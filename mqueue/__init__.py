import os
import json
import time
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
    http_request: bool


class PoppablePriorityQueue(PriorityQueue):
    def __init__(self, maxsize=0):
        self._lock = Lock()
        super().__init__(maxsize)
    
    def put(self, *args, **kwargs):
        return PriorityQueue.put(self, *args, **kwargs)

    def get(self, *args, **kwargs):
        return PriorityQueue.get(self, *args, **kwargs)

    def pop(self, *args, **kwargs):
        return self.queue.pop(*args, **kwargs)


class ProxyConnection(Thread):
    IDLE_TIMEOUT = 0.5
    CHUNK_SIZE = 2048

    def __init__(self, forward_host, forward_port, stop_event, 
                 first_request_line, client_socket, address, http_request=True):
        self._address = address
        self._first_line = first_request_line
        self._client_socket = client_socket
        self._forward_host = forward_host
        self._forward_port = forward_port
        self._stop_event = stop_event
        self._http_request = http_request
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
            if self._http_request:
                proxy_socket.sendall(b'X-Forwarded-For: ' + client_ip.encode('ascii') + b'\r\n')
            buffer_ = None
            while not self._stop_event.is_set() and (buffer_ is None or not buffer_):
                buffer_ = b''
                while True:
                    try:
                        b = self._client_socket.recv(ProxyConnection.CHUNK_SIZE)
                        if b:
                            buffer_ += b
                        else:
                            break
                    except socket.timeout:
                        break
            
                if buffer_:
                    # logging.debug(f'Sending to server: {repr(buffer_)}')
                    proxy_socket.sendall(buffer_)
                    
                buffer_ = b''
                while True:
                    try:
                        b = proxy_socket.recv(ProxyConnection.CHUNK_SIZE)
                        if b:
                            buffer_ += b
                        else:
                            break
                    except socket.timeout:
                        break

                if buffer_:
                    # logging.debug(f'Sending to client: {repr(buffer_)}')
                    self._client_socket.sendall(buffer_)

        except socket.error:
            logging.warning(traceback.format_exc())
        except IOError:
            logging.debug(f'Connection to {self._address[0]} has closed')
        finally:
            proxy_socket.shutdown(socket.SHUT_RDWR)
            proxy_socket.close()
            self._client_socket.shutdown(socket.SHUT_RDWR)
            self._client_socket.close()


class RequestProxyManager(Thread):
    IDLE_TIMEOUT = 30

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
                            self._stop_event, *request.item, request.http_request).start()
    
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
            route = RequestHandler.read_until(self._client_socket, b' ')
            http_version = RequestHandler.read_until(self._client_socket, b'\r\n')
            if http_version.startswith(b'HTTP') and http_method.decode() not in RequestHandler.HTTP_METHODS:
                logging.debug(f'Client {self._address[0]} has request ' \
                                f'an invalid HTTP method: {repr(http_method)}')
                self._respond_invalid_http_method()
                self._client_socket.shutdown(socket.SHUT_RDWR)
                return self._client_socket.close()
            first_line = http_method + b' ' + route + b' ' + http_version + b'\r\n'
            request = first_line, self._client_socket, self._address
            if http_version.startswith(b'HTTP'):
                logging.info(f'Client {self._address[0]} has requested: {http_method} {route}')
            else:
                logging.info(f'Client {self._address[0]} is sending other type of message (non-HTTP)')
            self._evaluate_and_put_request(route.decode(), request)
        except socket.timeout:
            logging.info(f'Client {self._address[0]} took a long time to send the request')
            self._respond_resquest_timeout()
            self._client_socket.shutdown(socket.SHUT_RDWR)
            self._client_socket.close()
        except UnicodeDecodeError:
            self._respond_bad_request()
            self._client_socket.shutdown(socket.SHUT_RDWR)
            self._client_socket.close()
        except Exception:
            logging.error(f'Something wrong happened during request reading!')
            logging.error(traceback.format_exc())
            self._client_socket.shutdown(socket.SHUT_RDWR)
            self._client_socket.close()

    def _drop_request(self, request):
        client_socket = request[1]
        content = b'HTTP/1.1 503 Service Unavailable\r\n'
        content += b'Connection: close\r\n'
        content += b'Retry-after: \r\n'
        content += b'Content-Length: 0\r\n\r\n'
        client_socket.sendall(content)
        client_socket.shutdown(socket.SHUT_RDWR)
        client_socket.close()

    def _evaluate_and_put_request(self, route, request, http_request=True):
        if http_request:
            route, sep, subroute = route.strip('/').partition('/')
            priority = self._route_priorities.get(f'/{route}', float('inf'))
            prioritized, deprioritized = None, None
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent 
            logging.info(f'CPU Percent: {cpu_percent}\tMemory Percent: {memory_percent}')
            logging.info(f'CPU Threshold: {self._cpu_threshold}\tMemory Threshold: {self._memory_threshold}')
            if not self._queue.empty() and (cpu_percent >= self._cpu_threshold \
                or memory_percent >= self._memory_threshold):
                last_request = self._queue.pop(-1)
                if last_request.priority > priority:
                    prioritized, deprioritized = request, last_request
                else:
                    prioritized, deprioritized = last_request, request
            else:
                prioritized = request
            if prioritized is request:
                logging.info(f'Add request to the queue with priority: {priority}')
            elif deprioritized is request:
                logging.info(f'Server is overloaded dropping current request')
            else:
                logging.info(f'Server is overloaded dropping last request in the queue')

            if deprioritized:
                self._drop_request(deprioritized)
            self._queue.put(PrioritizedItem(priority, prioritized, http_request))

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
    def __init__(self, config_file):
        self._config_file = config_file
        self._access_config_lock = Lock()
        self._config = None
        
        self._load_config_file()
        self._start_observe_file_changes()

    def get(self, key, default=None):
        with self._access_config_lock:
            return self._config.get(key, default)
    
    def _load_config_file(self):
        time.sleep(5)  # the file content is not available when event is triggered
        logging.info(f'Reading route priorities config file...')
        config = self._config and self._config.copy() or None
        try:
            with open(self._config_file) as file:
                config = json.load(file)
        except json.decoder.JSONDecodeError:
            logging.error('Could not read new config file, keep the same priorities...')
        else:
            with self._access_config_lock:
                self._config = config
            logging.info(f'Route priorities loaded!')
    
    def _start_observe_file_changes(self):
        observer = Observer()
        event_handler = RoutePriorities.ObserverEventHandler(self, self._config_file)
        observer.schedule(event_handler, path=self._config_file)
        observer.start()
    
    class ObserverEventHandler(FileModifiedEvent):
        def __init__(self, route_priorities, src_path):
            self._route_priorities = route_priorities
            super().__init__(src_path)

        def dispatch(self, event):
            logging.info(f'FileSystemEvent: {event}...')
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
    parser.add_argument('-l', '--log-level', default='INFO', choices=('INFO', 'DEBUG', 'WARNING', 'ERROR'), help='Logging level')
    parser.add_argument('-m', '--memory-threshold', default=80, type=float, help='Memory threshold to start dropping requests')
    parser.add_argument('-c', '--cpu-threshold', default=80, type=float, help='CPU threshold to start dropping requests')

    args = parser.parse_args()
    
    route_priorities = None

    logging.basicConfig(level=getattr(logging, args.log_level, None), format=LOG_FORMAT)
    
    if args.route_file:
        route_priorities = RoutePriorities(args.route_file)

    start_server(args.host, args.port, args.forward_host, args.forward_port, 
                 args.memory_threshold, args.cpu_threshold, route_priorities)
