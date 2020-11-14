import os
import docker

from flask import Flask
from pymongo import MongoClient 

from routes import services, metrics
from configurer import NGinxConfigurer

NGINX_CONTAINER_NAME = os.environ.get('NGINX_CONTAINER_NAME', 'nginx')
NGINX_CONFIG_FILE = os.environ.get('NGINX_CONFIG_FILE')
NGINX_CONFIG_FILE = os.path.join(os.getcwd(), NGINX_CONFIG_FILE)

HOST = os.environ.get('HOST', '0.0.0.0')
PORT = os.environ.get('PORT', '80')

DB_HOST = os.environ.get('DB_HOST', '127.0.0.1')
DB_PORT = os.environ.get('DB_PORT', '27017')
DB_USER = os.environ.get('DB_USER', 'mongo')
DB_PASS = os.environ.get('DB_PASS', 'mongo')
DB_NAME = os.environ.get('DB_NAME', 'stackprior-db')

DOCKER_UNIX_SOCKET = os.environ.get('DOCKER_UNIX_SOCKET', '/var/run/docker.sock')

assert NGINX_CONFIG_FILE and os.path.exists(NGINX_CONFIG_FILE), \
    'Set "NGINX_CONFIG_FILE" as valid Nginx config file'

assert DB_HOST and DB_USER and DB_PASS, \
    'Set "DB_HOST", "DB_USER" and "DB_PASS" environment variables'


mongo_client = MongoClient(f'mongodb://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/')
mongodb = mongo_client[DB_NAME]

configurer = NGinxConfigurer.from_config_file(NGINX_CONFIG_FILE)

docker_client = docker.DockerClient(base_url=f'unix://{DOCKER_UNIX_SOCKET}')

try:
    nginx_container = docker_client.containers.get(NGINX_CONTAINER_NAME)
except docker.errors.NotFound:
    raise RuntimeError('NGinx container is not available yet')

app = Flask(__name__)

# Routes
route_services = app.route('/services/<service>')(services(nginx_container, configurer))
app.route('/services/')(route_services)
app.route('/metrics/')(metrics(mongodb))


if __name__ == '__main__':
    app.run(host=HOST, port=PORT)
