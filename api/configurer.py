import re
import shlex
import itertools

from collections.abc import Iterable


GROUP_REGEX = r'(\S+) ?(.*?) ?\{([^\{\}]*)\}'
PARAMETER_REGEX = r'(\S+?)( (.+))?;'


class ParserError(Exception):
    pass


class Group:
    GROUP_CASTERS = {}

    def __init__(self, type_, properties=None, parameters=None, subgroups=None):
        assert isinstance(type_, str), 'type must be string'
        assert not properties or isinstance(properties, Iterable), 'properties must be iterable'
        assert not parameters or isinstance(parameters, Iterable), 'parameters must be iterable'
        assert not subgroups or isinstance(subgroups, Iterable), 'subgroups must be iterable'
        assert not parameters or all(isinstance(p, Parameter) for p in parameters), \
            'expecting Parameters object in parameters'
        assert not subgroups or all(isinstance(p, Group) for p in subgroups), \
            'expecting Group object in subgroups'

        self.type = type_
        self._properties = list(properties) if properties else []
        self._parameters = list(parameters) if parameters else []
        self._subgroups = list(subgroups) if subgroups else []

    def __str__(self):
        header = ' '.join(itertools.chain((self.type,), self._properties))
        subgroups_content = [str(g).replace('\n', '\n\t') for g in self._subgroups] 
        content = '\n\t'.join(itertools.chain([f'{p};' for p in self._parameters], subgroups_content))
        content = '\t' + content if content else ''
        return f'{header} {{\n{content}\n}}'
    
    def __repr__(self):
        return f'{self.__class__.__name__}({repr(self.type)}, ...)'

    def add_properties(self, *properties):
        self._properties.extend(properties)
    
    def get_properties(self):
        return self._properties
    
    def add_parameter(self, name, *args, **kwargs):
        parameter = Parameter(name, *args, **kwargs)
        self._parameters.append(parameter)
        return parameter

    def get_parameters(self):
        return self._parameters
    
    def get_parameter(self, name, *args, **kwargs):
        for p in self._parameters:
            
            if p.name == name and all(a in p.args for a in args) \
                and all(k in p.kwargs and p.kwargs[k] == v for k, v in kwargs.items()):
                return p
    
    def remove_parameter(self, name):
        parameter = self.get_parameter(name)
        assert parameter, f'parameter "{name}" does not exist'
        self._parameters.remove(parameter)
        return parameter

    def add_subgroup(self, group):
        self._subgroups.append(group)

    def get_subgroups(self):
        return self._subgroups
    
    @staticmethod
    def cast(group):
        raise NotImplementedError
    
    @staticmethod
    def group_caster(directive):
        def wrapper(cls):
            Group.GROUP_CASTERS[directive] = cls
            return cls
        return wrapper
    
    @staticmethod
    def parse_group(raw_content):
        try:
            groups, child_groups = Group._parse_group(raw_content)
            parsed_groups = []
            for position, group in groups.items():
                if group.type in Group.GROUP_CASTERS:
                    group = Group.GROUP_CASTERS[group.type].cast(group)
                if group not in child_groups:
                    parsed_groups.append(group)
            return parsed_groups
        except Exception as e:
            raise ParserError(e)

    @staticmethod
    def _parse_group(raw_content):
        groups = {}
        
        raw_groups = re.finditer(GROUP_REGEX, raw_content)
        for match_group in raw_groups:
            start, end = match_group.start(), match_group.end()
            raw_content = raw_content[:start] + ' ' * len(match_group.group()) + raw_content[end:]
            type_, properties, content = match_group.groups()
            properties = properties.split(' ')
            parameters = []
            raw_parameters = re.finditer(PARAMETER_REGEX, content)
            for match_parameter in raw_parameters:
                name, _, args = match_parameter.groups()
                args = re.split(r'\s', args)
                kwargs = {}
                for arg in args:
                    key, sep, value = arg.partition('=')
                    if sep:
                      kwargs[key] = value
                      args.remove(arg)  
                parameters.append(Parameter(name, *args, **kwargs))
            group = Group(type_, properties, parameters)
            groups[(start, end)] = group
        
        if not groups:
            return {}, []

        parent_groups, child_groups = Group._parse_group(raw_content)
        if parent_groups:
            for (start, end), group in groups.items():
                elegible_parents = [(s, e, p) for (s, e), p in parent_groups.items() if start > s and end < e]
                if elegible_parents:
                    parent = min(elegible_parents, key=lambda p: p[1] - p[0])
                    parent[2].add_subgroup(group)
                    child_groups.append(group)

            groups.update(parent_groups)

        return groups, child_groups


class Parameter:
    def __init__(self, name, *args, **kwargs):
        assert isinstance(name, str), 'name must be string'
        assert not re.search(r'\s', name), 'parameter name must not have whitespace'
        assert all(isinstance(k, str) for k, v in kwargs.items()), \
            'key-value parameters must be string'
        assert all(not re.search(r'\s', k) for k in kwargs), 'key-value parameters must not have whitespace'
        
        self.name = name
        self.args = args
        self.kwargs = kwargs
    
    def __str__(self):
        kwargs = (f"{k}={shlex.quote(str(v)) if v is not None else ''}" for k, v in self.kwargs.items())
        return ' '.join(map(str, itertools.chain((self.name,), self.args, kwargs)))

    def __repr__(self):
        args = ', '.join(map(repr, self.args))
        kwargs = ','.join(f'{k}={repr(v)}' for k, v in self.kwargs.items())
        return f"{self.__class__.__name__}({repr(self.name)}, {', '.join((args, kwargs))})"

class NGinxConfig:
    def __init__(self, groups=None, server_name=None, server_port=80):
        self._groups = groups or []
        self._groups = {g.type: g  for g in groups}
        self._http_directive = self._groups.get('http', None)
        if not self._http_directive:
            self._http_directive = HttpDirective(server_name, server_port)
            self._groups['http'] = self._http_directive
        self._groups['events'] = Group('events')

    def __repr__(self):
        return f'{self.__class__.__name__}(...)'

    def set_resolver(self, host, *args, **kwargs):
        return self._http_directive.set_resolver(host, *args, **kwargs)

    def add_upstream(self, upstream):
        return self._http_directive.add_upstream(upstream)

    def get_all_upstreams(self):
        return self._http_directive.get_all_upstreams()

    def get_upstream(self, name):
        return self._http_directive.get_upstream(name)
    
    def remove_upstream(self, name):
        return self._http_directive.remove_upstream(name)
    
    def get_endpoint(self, name_upstream):
        return self._http_directive.get_endpoint(name_upstream).rstrip('/')
    
    def get_sub_endpoint(self, name_upstream):
        return self._http_directive.get_sub_endpoint(name_upstream).rstrip('/')
        
    def add_route(self, endpoint, upstream_name, *args, sub_endpoint=None):
        return self._http_directive.add_route(self._normalize_route(endpoint), upstream_name, *args, sub_endpoint=sub_endpoint)
    
    def remove_route(self, endpoint):
        return self._http_directive.remove_route(self._normalize_route(endpoint))
    
    def update_route(self, endpoint, upstream_name, *args, sub_endpoint=None):
        return self._http_directive.update_route(self._normalize_route(endpoint), upstream_name, *args, sub_endpoint=sub_endpoint)
    
    def save(self, filepath):
        with open(filepath, 'w') as file:
            file.write('\n\n'.join(str(g) for g in self._groups.values()))
    
    def _normalize_route(self, endpoint):
        return endpoint.rstrip('/') + '/'

    @staticmethod
    def from_config_file(config_file):
        with open(config_file, 'r') as file:
            config = NGinxConfig(Group.parse_group(file.read()))
        return config

@Group.group_caster('http')
class HttpDirective(Group):
    def __init__(self, server_name=None, server_port=80):
        super().__init__('http')
        self._resolver = None
        self._upstreams = {}
        self._server_directive = ServerDirective(server_name=server_name, port=server_port)
        self.add_subgroup(self._server_directive)
    
    def set_resolver(self, host, *args, **kwargs):
        if self._resolver:
            self.remove_parameter('resolver')
        self._resolver = self.add_parameter('resolver', host, *args, **kwargs)

    def add_upstream(self, upstream):
        assert isinstance(upstream, UpstreamDirective), 'expecting UpstreamDirective object'
        self._upstreams[upstream.name] = upstream
        self.add_subgroup(upstream)
    
    def remove_upstream(self, name):
        upstream = next((g for g in self._subgroups if isinstance(g, UpstreamDirective) and  g.name == name), None)
        assert upstream, 'upstream {name} does not exist'
        self._subgroups.remove(upstream)

    #in progress
    def get_all_upstreams(self):
        upstreams = [g for g in self._subgroups if isinstance(g, UpstreamDirective)]
        return upstreams

    def get_upstream(self, name):
        upstreams = self.get_all_upstreams()
        upstream = None
        for i in upstreams:
            if i.name == name:
                upstream = i
        return upstream
        
    def get_endpoint(self, name_upstream):
        endpoints = self._server_directive.get_endpoints()
        endpoint = None
        for e, (endpoint_upstream, sub_endpoint) in endpoints.items():
            if endpoint_upstream == name_upstream:
                endpoint = e
        return endpoint
    
    def get_sub_endpoint(self, name_upstream):
        endpoints = self._server_directive.get_endpoints()
        sub_endpoint = None
        for e, (endpoint_upstream, sub_endpoint) in endpoints.items():
            if endpoint_upstream == name_upstream:
                sub_endpoint = sub_endpoint
        return sub_endpoint

    #serve pra nada
    def get_location(self, endpoint):
        locations = self._server_directive.get_locations()
        location = None
        for l in locations:
            if l.endpoint == endpoint:
                location = l
        return location


    def get_endpoints(self):
        return self._server_directive.get_endpoints()

    def add_route(self, endpoint, upstream_name, *args, sub_endpoint=None):
        return self._server_directive.add_route(endpoint, upstream_name, *args, sub_endpoint=sub_endpoint)
    
    def remove_route(self, endpoint):
        return self._server_directive.remove_route(endpoint)
    
    def update_route(self, endpoint, upstream_name, *args, sub_endpoint=None):
        return self._server_directive.update_route(endpoint, upstream_name, *args, sub_endpoint=sub_endpoint)
    
    @staticmethod
    def cast(group):
        group.__class__ = HttpDirective
        group._resolver = group.get_parameter('resolver')
        group._upstreams = {g._properties[0]: g for g in group._subgroups if g.type == 'upstream'}
        group._server_directive = next((g for g in group._subgroups if g.type == 'server'), None)
        if not group._server_directive:
            group._server_directive = ServerDirective()
            group.add_subgroup(group._server_directive)
        return group

@Group.group_caster('upstream')
class UpstreamDirective(Group):
    def __init__(self, name):
        self._name = name
        super().__init__('upstream', (name,))
    
    @property
    def name(self):
        return self._name
    
    @name.setter
    def name(self, name):
        self.name = name
        self._properties[0] = name
    
    def add_server(self, host, *args, **kwargs):
        assert not self.get_server(host), 'there is already a server with that host'
        return self.add_parameter('server', host, *args, **kwargs)
    
    def remove_server(self, host):
        server_parameter = self.get_server(host)
        assert server_parameter, 'server does not exist'
        self._parameters.remove(server_parameter)
        return server_parameter

    def get_server(self, host):
        return next((p for p in self._parameters if p.args[0] == host), None)

    def get_all_servers(self):
        return [(p.args, p.kwargs) for p in self._parameters]

        
    @staticmethod
    def cast(group):
        group.__class__ = UpstreamDirective
        group._name = group._properties[0]
        return group


@Group.group_caster('server')
class ServerDirective(Group):
    def __init__(self, routes=None, server_name=None, port=80):
        assert not routes or isinstance(routes, Iterable), 'routes must be iterable'
        assert not routes or all(isinstance(r, ServerRoute) for r in routes), \
            'expecting ServerRoute object in routes'
        assert isinstance(port, int), 'port must be integer'

        super().__init__('server', subgroups=routes)
        
        self.add_parameter('listen', port)
        
        if server_name:
            self.add_parameter('server_name', server_name)

    def get_endpoints(self):
        server_routes = self._subgroups
        endpoints = {}
        for server_route in server_routes:
            if server_route.endpoint:
                endpoints[server_route.endpoint] = server_route.upstream_name, server_route.sub_endpoint 
        if '/' in endpoints:
            del endpoints['/']
        return endpoints
    
    def get_locations(self):
        location = self._subgroups
        return location

    def add_route(self, endpoint, upstream_name, *args, sub_endpoint=None, https=False):
        server_route = ServerRoute(endpoint, upstream_name, sub_endpoint, args, https)
        self.add_subgroup(server_route)
        return server_route
    
    def remove_route(self, endpoint):
        server_route = next((g for g in self._subgroups if g._properties[0] == endpoint), None)
        assert server_route, 'endpoint does not exist'
        self._subgroups.remove(server_route)
        return server_route
    
    def update_route(self, endpoint, upstream_name, *args, sub_endpoint=None, https=False):
        self.remove_route(endpoint)
        return self.add_route(endpoint, upstream_name, sub_endpoint, *args, https)
    
    @staticmethod
    def cast(group):
        group.__class__ = ServerDirective
        return group


@Group.group_caster('location')
class ServerRoute(Group):
    def __init__(self, endpoint, upstream_name=None, sub_endpoint=None, parameters=None, https=False):
        assert endpoint, 'endpoint cannot be empty string or None'

        super().__init__('location', (endpoint,), parameters)

        self._endpoint = endpoint.strip('/')
        self._sub_endpoint = sub_endpoint.strip('/') if sub_endpoint else ''
        self._upstream_name = upstream_name
        self._https = https 
        
        if upstream_name:
            https_flag = 's' if https else ''
            
            sub_endpoint = f'{self.sub_endpoint}/' if self._sub_endpoint else '/'
            proxy_redirect = f'{self.endpoint}{sub_endpoint}'

            self.add_parameter('set', '$upstream', upstream_name)
            self.add_parameter('proxy_pass', f'http{https_flag}://{upstream_name}{sub_endpoint}')
            self.add_parameter('proxy_redirect', '/', proxy_redirect)
            self.add_parameter('proxy_redirect', 'default')
            self.add_parameter('proxy_set_header', 'Upgrade $http_upgrade')
            self.add_parameter('proxy_set_header', 'Connection "upgrade"')
            self.add_parameter('proxy_set_header', 'Host $host')

    @property
    def endpoint(self):
        return f'/{self._endpoint}'
    
    @property
    def sub_endpoint(self):
        return f'/{self._sub_endpoint}'

    @property
    def upstream_name(self):
        return self._upstream_name

    @property
    def https(self):
        return self._https
    
    @staticmethod
    def cast(group):
        set_upstream_parameter = group.get_parameter('set', '$upstream')
        upstream_name = set_upstream_parameter and set_upstream_parameter.args[1]
        proxy_pass_parameter = group.get_parameter('proxy_pass')
        https = proxy_pass_parameter and proxy_pass_parameter.args[0].startswith('https')
        proxy_redirect_parameter = group.get_parameter('proxy_redirect', '/')
        route = re.search(r'https?\:\/\/(.+?)/(.+)', proxy_pass_parameter.args[0])
        endpoint, sub_endpoint = route.groups()
        
        group.__class__ = ServerRoute
        group._endpoint = endpoint
        group._sub_endpoint = sub_endpoint.strip('/')
        group._upstream_name = upstream_name 
        group._https = https
        return group



if __name__ == "__main__":
    pass
    # config = NGinxConfig()
    # config.set_resolver('127.0.0.1', valid='30s')
    # upstream = UpstreamDirective('lets-chat')
    # upstream.add_server('lets-chat-1:8080')
    # upstream.add_server('lets-chat-2:8080')
    # upstream.add_server('lets-chat-3:8080')
    # config.add_upstream(upstream)
    # location = config.add_route('/', None)
    # location.add_parameter('deny', 'all')

    #config.save('./nginx.conf')

