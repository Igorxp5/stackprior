import json
import os
from flask import request, jsonify
from subprocess import check_output

from api.configurer import UpstreamDirective

app = None
configurer = None
nginx_container = None

PATH_NGINX = None
PATH_MQUEUE = None


def restart_nginx():
    nginx_container.exec_run(f'nginx -s reload')


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
    dic['servers'] = []
    for server in servers:
        host, sep, port = server[0][0].partition(':')
        server_info = {'host': host}
        dic['strategy'] = 'dns'
        if port:
            server_info['port'] = int(port)
            dic['strategy'] = 'round-robin'
        if 'weight' in server[1]:
            server_info['weight'] = int(server[1]['weight'])
            dic['strategy'] = 'priority'
        dic['servers'].append(server_info)

    endpoint = configurer.get_endpoint(upstream.name)
    sub_endpoint = configurer.get_sub_endpoint(upstream.name)

    dic['endpoint'] = endpoint
    dic['sub-endpoint'] = sub_endpoint

    
    priorities = get_priorities(PATH_MQUEUE)
    priority = priorities[endpoint]
    dic['priority'] = priority

    return dic


def services(nginx_container_, configurer_, app_, nginx_config_file, mqueue_config_file):
    global configurer, nginx_container, app, PATH_NGINX, PATH_MQUEUE
    configurer = configurer_
    nginx_container = nginx_container_
    app = app_
    PATH_NGINX = nginx_config_file
    PATH_MQUEUE = mqueue_config_file

    return _services

def _services(service=None):

    if request.method == "POST":
        response, status_code = create()

    elif request.method == "DELETE":
        response, status_code = delete(service)

    elif request.method == "GET" and service:
        response, status_code = get(service)

    elif request.method == "GET" and not service:
        response, status_code = index()
    
    elif request.method == "PUT" and service:
        response, status_code = update(service)
    
    elif request.method == "OPTIONS":
        response, status_code = jsonify(), 200
    
    else:
        response, status_code = jsonify(error='invalid request'), 400

    response.headers.add('Access-Control-Allow-Credentials', 'true')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Headers', 'x-csrf-token')
    response.headers.add('Access-Control-Allow-Methods',
                        'GET, POST, OPTIONS, PUT, PATCH, DELETE')

    return response, status_code


def create():
    service = request.json
    name, endpoint, priority , strategy, servers = service['name'], service['endpoint'], service['priority'], service['strategy'], service['servers']
    sub_endpoint = service.get('sub-endpoint')

    #Name of service can't be the same
    if configurer.get_upstream(name):
        return jsonify(sucess='The name of upstream is already in use'), 400

    #Endpoint can't be the same
    for e in get_priorities(PATH_MQUEUE):
        if e == endpoint:
            return jsonify(error="Endpoint already exists"), 400

    configurer.set_resolver('127.0.0.11', valid='30s')
    upstream = UpstreamDirective(name)
    kwargs = {'max_fails': 15, 'fail_timeout': 600}
    
    if strategy == 'priority':
        kwargs['weight'] = 0
        #three parameters in add_server, server, port and weight
        for server in servers:
            kwargs['weight'] = server['weight']
            host_port = str(server["host"])+":"+str(server["port"])
            upstream.add_server(host_port, **kwargs)

    if strategy == 'dns':
        # one parameter in add_server, server
        for server in servers:
            upstream.add_server(server["host"], **kwargs)


    if strategy == 'round-robin':
        # two parameters in add_server, server and port
        for server in servers:
            host_port = str(server["host"])+":"+str(server["port"])
            upstream.add_server(host_port, **kwargs)


    configurer.add_upstream(upstream)
    configurer.add_route(endpoint, upstream.name, sub_endpoint=sub_endpoint)

    configurer.save(PATH_NGINX)
    set_priority(PATH_MQUEUE, endpoint, priority)

    restart_nginx()

    return jsonify(sucess='service created'), 201

def delete(service):
    
    if not configurer.get_upstream(service):
        return jsonify(error="This service doesn't exist"), 404
    else:
        endpoint = configurer.get_endpoint(service)

        del_priority(PATH_MQUEUE, endpoint)

        configurer.remove_upstream(service)
        configurer.remove_route(endpoint)

        configurer.save(PATH_NGINX)
        restart_nginx()
        return jsonify(sucess='service deleted'), 200


def index():
    upstreams = configurer.get_all_upstreams()
    data = []
    for upstream in upstreams:
        dic = making_get(upstream)
        data.append(dic)
    return  jsonify(data=data), 200


def get(service):
    upstream = configurer.get_upstream(service)
    if upstream:
        dic = making_get(upstream)
    else:
        return jsonify(error='This service doesn\'t exist'), 404
    
    return jsonify(**dic)


def update(service):

    update_data = request.json
    name, endpoint, priority , strategy, servers = update_data['name'], update_data['endpoint'], update_data['priority'], update_data['strategy'], update_data['servers']
    sub_endpoint = update_data.get('sub-endpoint')

    #DELETING

    if not configurer.get_upstream(service):
        return jsonify(error='This service doesn\'t exist'), 404
    else:
        old_endpoint = configurer.get_endpoint(service)

        del_priority(PATH_MQUEUE, old_endpoint)
        configurer.remove_upstream(service)
        configurer.remove_route(old_endpoint)
    

    #CHECKING
    
    #Name of service can't be the same
    if configurer.get_upstream(name):
        set_priority(PATH_MQUEUE, endpoint, priority)
        return jsonify(error='The name of upstream is already in use'), 400

    #Endpoint can't be the same
    for e in get_priorities(PATH_MQUEUE):
        if e == endpoint:
            set_priority(PATH_MQUEUE, endpoint, priority)
            return jsonify(error='Endpoint already exists'), 400


    #CREATING

    configurer.set_resolver('127.0.0.11', valid='30s')
    upstream = UpstreamDirective(name)
    kwargs = {'max_fails': 15, 'fail_timeout': 600}
    
    if strategy == 'priority':
        kwargs['weight'] = 0
        #three parameters in add_server, server, port and weight
        for server in servers:
            kwargs['weight'] = server['weight']
            host_port = str(server["host"])+":"+str(server["port"])
            upstream.add_server(host_port, **kwargs)

    if strategy == 'dns':
        # one parameter in add_server, server
        for server in servers:
            upstream.add_server(server["host"], **kwargs)


    if strategy == 'round-robin':
        # two parameters in add_server, server and port
        for server in servers:
            host_port = str(server["host"])+":"+str(server["port"])
            upstream.add_server(host_port, **kwargs)


    configurer.add_upstream(new_upstream)
    configurer.add_route(endpoint, new_upstream.name, sub_endpoint=sub_endpoint)

    configurer.save(PATH_NGINX)
    set_priority(PATH_MQUEUE, endpoint, priority)

    restart_nginx()

    return jsonify(success='service updated'), 200
