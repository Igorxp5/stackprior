import os
import json
import socket
import psutil
import logging
import argparse
import traceback
import socketserver

from queue import PriorityQueue, Empty
from threading import Thread, Event, Lock

from watchdog.observers import Observer
from watchdog.events import FileModifiedEvent

from dataclasses import dataclass, field
from typing import Any


LOG_FORMAT = '[%(threadName)s] %(asctime)s %(levelname)s: %(message)s'


@dataclass(order=True)
class PrioritizedItem:
    priority: int
    item: Any=field(compare=False)


class PoppablePriorityQueue(PriorityQueue):
    def __init__(self, maxsize=0):
        self._lock = Lock()
        super().__init__(maxsize)
    
    def put(self, *args, **kwargs):
        with self._lock:
            return PriorityQueue.put(self, *args, **kwargs)

    def get(self, *args, **kwargs):
        with self._lock:
            return PriorityQueue.get(self, *args, **kwargs)

    def pop(self, *args, **kwargs):
        with self._lock:
            return self.queue.pop(*args, **kwargs)


class ProxyConnection(Thread):
    IDLE_TIMEOUT = 1

    def __init__(self, forward_host, forward_port, stop_event, 
                 first_request_line, client_socket, address):
        self._address = address
        self._first_line = first_request_line
        self._client_socket = client_socket
        self._forward_host = forward_host
        self._forward_port = forward_port
        self._stop_event = stop_event
        super().__init__(daemon=True)

    def run(self):
        proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        try:
            self._client_socket.settimeout(ProxyConnection.IDLE_TIMEOUT)
            proxy_socket.settimeout(ProxyConnection.IDLE_TIMEOUT)
            logging.debug(f'Connecting to Forward Server...')
            proxy_socket.connect((self._forward_host, self._forward_port))
            logging.debug(f'Connected to Forward Server, forwaring request...')
            proxy_socket.sendall(self._first_line)
            client_ip, client_port = self._address 
            proxy_socket.sendall(b'X-Forwarded-For: ' + client_ip.encode('ascii') + b'\r\n')
            buffer_ = None
            while not self._stop_event.is_set() and (buffer_ is None or not buffer_):
                try:
                    buffer_ = self._client_socket.recv(4096)
                except socket.timeout:
                    pass
                else:
                    proxy_socket.sendall(buffer_)
                    try:
                        buffer_ = proxy_socket.recv(4096)
                    except socket.timeout:
                        pass
                    else:
                        self._client_socket.sendall(buffer_) 

        except socket.error:
            logging.warning(traceback.format_exc())
        except IOError:
            logging.debug(f'Connection to {self._address[0]} has closed')
        finally:
            proxy_socket.close()
            self._client_socket.close()


class RequestProxyManager(Thread):
    IDLE_TIMEOUT = 15

    def __init__(self, queue, stop_event, forward_host, 
                 forward_port, *args, **kwargs):
        self._queue = queue
        self._stop_event = stop_event
        self._forward_host = forward_host
        self._forward_port = forward_port
        super().__init__(name='RequestProxyManager', *args, **kwargs)
    
    def run(self):
        logging.info('RequestProxyManager is ready and waiting for requests...')
        while not self._stop_event.is_set():
            
            try:
                request = self._queue.get(timeout=RequestProxyManager.IDLE_TIMEOUT)
            except Empty:
                continue
            
            logging.debug(f'RequestProxyManager has received: {request.item}')
            ProxyConnection(self._forward_host, self._forward_port, 
                            self._stop_event, *request.item).start()
    
        logging.info('RequestProxyManager has been terminated')


class RequestHandler(Thread):
    HTTP_METHODS = {'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS',
                    'TRACE', 'PATCH'}
    IDLE_TIMEOUT = 20

    def __init__(self, client_socket, address, stop_event, queue,
                 memory_threshold, cpu_threshold, route_priorities=None, *args, **kwargs):
        self._queue = queue
        self._address = address
        self._stop_event = stop_event
        self._client_socket = client_socket
        self._route_priorities = route_priorities or dict()
        self._memory_threshold = memory_threshold
        self._cpu_threshold = cpu_threshold
        super().__init__(*args, **kwargs)
    
    def run(self):
        request_first_line = b''
        self._client_socket.settimeout(RequestHandler.IDLE_TIMEOUT)
        logging.info(f'Handling connection with {self._address[0]}')
        try:
            http_method = RequestHandler.read_until(self._client_socket, b' ')
            if http_method.decode() not in RequestHandler.HTTP_METHODS:
                logging.debug(f'Client {self._address[0]} has request ' \
                                f'an invalid HTTP method: {repr(http_method)}')
                self._respond_invalid_http_method()
                return self._client_socket.close()
            route = RequestHandler.read_until(self._client_socket, b' ')
            http_version = RequestHandler.read_until(self._client_socket, b'\r\n')
            first_line = http_method + b' ' + route + b' ' + http_version + b'\r\n'
            request = first_line, self._client_socket, self._address
            logging.info(f'Client {self._address[0]} has requested: {http_method} {route}')
            self._evaluate_and_put_request(route, request)
        except socket.timeout:
            logging.info(f'Client {self._address[0]} took a long time to send the request')
            self._respond_resquest_timeout()
            self._client_socket.close()
        except UnicodeDecodeError:
            self._respond_bad_request()
            self._client_socket.close()
        except Exception:
            logging.error(f'Something wrong happened during request reading!')
            logging.error(traceback.format_exc())
            self._client_socket.close()

    def _drop_request(self, request):
        client_socket = request[1]
        content = header + b'\r\n'
        content += b'Connection: close\r\n'
        content += b'Content-Length: 0\r\n\r\n'
        client_socket.sendall(content)
    
    def _evaluate_and_put_request(self, route, request):
        priority = self._route_priorities.get(route, float('inf'))
        if (psutil.cpu_percent() >= self._cpu_threshold 
            or psutil.virtual_memory().percent >= self._memory_threshold):
            last_request = self._queue.pop(-1)
            if last_request.priority > priority:
                prioritized, deprioritized = request, last_request
            else:
                prioritized, deprioritized = last_request, request
            self._drop_request(deprioritized)
        else:
            prioritized = request
        self._queue.put(PrioritizedItem(priority, prioritized))

    def _respond_invalid_http_method(self):
        self._http_no_body_response(b'HTTP/1.1 405 Method Not Allowed')

    def _respond_bad_request(self):
        self._http_no_body_response(b'HTTP/1.1 400 Bad Request')
    
    def _respond_resquest_timeout(self):
        self._http_no_body_response(b'HTTP/1.1 408 Request Timeout')
    
    def _http_no_body_response(self, header):
        content = header + b'\r\n'
        content += b'Connection: close\r\n'
        content += b'Content-Length: 0\r\n\r\n'
        self._client_socket.sendall(content)

    @staticmethod
    def read_until(socket_, char, include=False):
        read = b''
        buffer_ = None
        while buffer_ is None or buffer_:
            buffer_ = socket_.recv(len(char))
            if buffer_ == char or not buffer_:
                break
            read += buffer_
        if include:
            read += buffer_
        return read


class RoutePriorities:
    def __init__(self, config_file, stop_event):
        self._stop_event = stop_event
        self._config_file = config_file
        self._access_config_lock = Lock()
        self._config = None
        
        self._load_config_file()
        self._start_observe_file_changes()

    def get(self, key, default=None):
        with self._access_config_lock:
            return self._config.get(key, default)
    
    def _load_config_file(self):
        with self._access_config_lock:
            with open(self._config_file) as file:
                self._config = json.load(file)
        logging.info(f'Route priorities loaded!')
    
    def _start_observe_file_changes(self):
        observer = Observer()
        event_handler = ObserverEventHandler(self) 
        observer.schedule(event_handler, path=self._config_file)
        observer.start()
    
    class ObserverEventHandler(FileModifiedEvent):
        def __init__(self, route_priorities):
            self._route_priorities = route_priorities
            super().__init__()

        def on_modified(self, event):
            logging.info(f'Config files has modified, updating route priorities...')
            self._route_priorities._load_config_file()


def start_server(host, port, forward_host, forward_port, memory_threshold, cpu_threshold, 
                 route_priorities=None):
    stop_event = Event()
    queue = PoppablePriorityQueue()
    request_proxy = RequestProxyManager(queue, stop_event, forward_host, forward_port)
    request_proxy.start()

    try:
        logging.info('Starting server socket...')
        with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as server_socket:
            server_socket.bind((host, port))
            server_socket.listen()
            logging.info('Server is listening...')
            while True:
                client_socket, address = server_socket.accept()
                logging.info(f'Server has accepted a connection ({address[0]})')
                handler = RequestHandler(client_socket, address, stop_event, queue, memory_threshold, cpu_threshold, 
                                         route_priorities, name=f'RequestHandler({address[0]})')
                handler.start()
    except KeyboardInterrupt:
        logging.info('Stopping server, waiting for RequestProxyManager to finish...')
        stop_event.set()
        request_proxy.join()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('forward_host', help='Forward Server Host')
    parser.add_argument('forward_port', type=int, help='Forward Server port')
    parser.add_argument('host', nargs='?', default='0.0.0.0', help='Interface for HTTP server')
    parser.add_argument('port', nargs='?', default=80, type=int, help='HTTP Server port')
    
    parser.add_argument('-r', '--route-file', default=None, help='Route priorities JSON file')
    parser.add_argument('-l', '--log-level', default='DEBUG', choices=('INFO', 'DEBUG', 'WARNING', 'ERROR'), help='Logging level')
    parser.add_argument('-m', '--memory-threshold', default=80, type=float, help='Memory threshold to start dropping requests')
    parser.add_argument('-c', '--cpu-threshold', default=80, type=float, help='CPU threshold to start dropping requests')

    args = parser.parse_args()
    
    route_priorities = None

    if args.route_file:
        route_priorities = RoutePriorities(args.route_file)

    logging.basicConfig(level=getattr(logging, args.log_level, None), format=LOG_FORMAT)

    start_server(args.host, args.port, args.forward_host, args.forward_port, 
                 args.memory_threshold, args.cpu_threshold, route_priorities)
