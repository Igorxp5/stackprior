import json
import os
from flask import request, jsonify
from subprocess import check_output

from api.configurer import UpstreamDirective

app = None
configurer = None
nginx_container = None

PATH_NGINX = '../../nginx/nginx.conf'
PATH_MQUEUE = '../../nginx/mqueue.json'

def get_pid(name):
    ugly_data = nginx_container.exec_run(["pidof",name])[1]
    data = ugly_data.decode()
    pids = map(int,data.split())
    return min(list((pids)))

def restart_nginx():
    pid = get_pid('nginx')
    nginx_container.exec_run(f"kill -HUP {pid}")


def get_strategy(server):
    # TODO make the weights verification
    for caracter in server:
        if caracter == ':':
            return 'round-robin'
    
    return 'dns'


def get_priorities(path):
    with open(path, "r") as archive:
        priorities = archive.read()
        return json.loads(priorities)


def set_priority(path, endpoint, priority):
    priorities = get_priorities(path)

    with open(path, "w") as archive:
        priorities[endpoint] = priority
        archive.write(json.dumps(priorities, indent=4))

def del_priority(path, endpoint):
    priorities = get_priorities(path)

    with open(path, "w") as archive:
        del priorities[endpoint]
        archive.write(json.dumps(priorities, indent=4))


def making_get(upstream):
    dic={}
    dic['name']=upstream.name

    servers = upstream.get_all_servers()
    dic['servers']= servers 

    endpoint = configurer.get_endpoint(upstream.name)
    dic['endpoint'] = endpoint

    strategy = get_strategy(servers[0])
    dic['strategy'] = strategy

    
    priorities = get_priorities(PATH_MQUEUE)
    priority = priorities[endpoint]
    dic['priority'] = priority

    return dic


def services(nginx_container_, configurer_, app_):
    global configurer, nginx_container, app
    configurer = configurer_
    nginx_container = nginx_container_
    app = app_

    return _services

def _services(service=None):

    if request.method == "POST":
        return create()

    if request.method == "DELETE":
        return delete(service)

    if request.method == "GET" and service:
        return get(service)

    if request.method == "GET" and service == None:
        return index()

    return f'Services: {service}'


def create():
    
    # TODO retornar os erros
    service = request.json
    name, endpoint, priority , strategy, servers = service['name'], service['endpoint'], service['priority'], service['strategy'], service['servers']

    #Name of service can't be the same
    if configurer.get_upstream(name):
        return {"error:" : "The name of upstream is already in use"}, 400

    #Endpoint can't be the same
    for e in get_priorities(PATH_MQUEUE):
        if e == endpoint:
            return {"error:" : "Endpoint already exists"}, 400

    configurer.set_resolver('127.0.0.1', valid='30s')
    upstream = UpstreamDirective(name)
    if strategy == 'priority':
        #three parameters in add_server, server, port and weigth
        for server in servers:
            ip_port = str(server["ip"])+":"+str(server["port"])
            upstream.add_server(ip_port , weigth=priority)

    if strategy == 'dns':
        #one parameter in add_server, server
        for server in servers:
            upstream.add_server(server["ip"])


    if strategy == 'round-robin':
        #two parameters in add_server, server and port
        for server in servers:
            ip_port = str(server["ip"])+":"+str(server["port"])
            upstream.add_server(ip_port)


    configurer.add_upstream(upstream)
    configurer.add_route(endpoint, upstream.name)

    configurer.save(PATH_NGINX)
    set_priority(PATH_MQUEUE, endpoint, priority)

    restart_nginx()

    return {"sucess" : "service created"}, 201

def delete(service):
    
    if not configurer.get_upstream(service):
        return {"error:" : "This service doesn't exist"}, 400
    else:
        endpoint = configurer.get_endpoint(service)

        #delete priority
        del_priority(PATH_MQUEUE, endpoint)

        configurer.remove_upstream(service)

        configurer.save(PATH_NGINX)
        restart_nginx()

        # delete location 
        configurer.remove_route(endpoint)
        restart_nginx()
        return {"sucess" : "service deleted"}, 200


def index():
    upstreams = configurer.get_all_upstreams()
    data = []
    for upstream in upstreams:
        dic = making_get(upstream)
        data.append(dic)
    return  {'data': data}


def get(service):
    upstream = configurer.get_upstream(service)
    if upstream:
        dic = making_get(upstream)
    else:
        return {"error" : "This service doesn't found"}, 404
    
    return dic




