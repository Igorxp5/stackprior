import os
import subprocess
import contextlib
import time

MAIN_DIRECTORY = os.path.join(os.path.dirname(__file__), '../')


@contextlib.contextmanager
def start_project(env=None, **kwargs):
    inherited_env = os.environ.copy()
    if env:
        inherited_env.update(env)
    process = subprocess.Popen('docker-compose up', env=inherited_env,
                               shell=True, cwd=MAIN_DIRECTORY, **kwargs)
    print(f'Project running! PID: {process.pid}')
    try:
        yield process
    finally:
        terminate_process = subprocess.Popen('docker-compose down', 
                                             shell=True, cwd=MAIN_DIRECTORY)
        print('Waiting project stop to run...')
        terminate_process.wait()
