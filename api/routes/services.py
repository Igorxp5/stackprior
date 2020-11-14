configurer = None
nginx_container = None

def services(nginx_container_, configurer_):
    global configurer, docker_client
    configurer = configurer_
    nginx_container = nginx_container_

    return _services

def _services(service=None):
    return f'Services: {service}'
