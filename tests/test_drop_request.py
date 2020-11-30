import os
import time
import random
import requests
import subprocess


from threading import Thread
from queue import Queue

from util import start_project


def test_drop_request():
    env = {'DB_USER': 'mongo', 'DB_PASS': 'mongo', 
           'MEMORY_THRESHOLD': '50', 'CPU_THRESHOLD': '50'}
    with start_project(env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) as process:
        print('Waiting 30 seconds to the platform be available...')
        time.sleep(30)

        def _request(responses):
            response = None
            try:
                response = requests.get('http://localhost/products', timeout=5)
            except Exception:
                print('Something wrong happened during the request!')
            else:
                responses.put(response)
        
        responses_queue = Queue()
        threads = []
        
        print('Sending 10 requests...')
        for _ in range(10):
            thread = Thread(target=_request, args=(responses_queue,))
            threads.append(thread)
            thread.start()
        
        print('Waiting for requests response...')
        for thread in threads:
            thread.join()
        
        i = 0
        responses = []
        while not responses_queue.empty():
            response = responses_queue.get()
            print(f'{i} - {response}')
            responses.append(response)
            i += 1

        assert any(response.status_code == 200 for response in responses), 'Some request should be answered'
        assert any(response.status_code == 503 for response in responses), 'Some request should be droped'
