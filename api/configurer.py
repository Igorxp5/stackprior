import re
import shlex
import itertools

from collections.abc import Iterable


UPSTREAM_REGEX = r'upstream (.+) \{([\S\s]*?)\}'


class NGinxConfigurer:
    def __init__(self):
        self._upstreams = {}
        self._routes = {}
        self._other_configs = ''
    
    def add_upstream(self, name, upstream):
        assert name not in self._upstreams, f'{name} upstream already exists'
        self._upstreams[name] = None
        self.update_upstream(name, upstream)

    def get_upstream(self, name):
        assert name in self._upstreams, f'{name} upstream does not exist'
        return self._upstreams[name]
    
    def update_upstream(self, name, upstream):
        assert name in self._upstreams, f'{name} upstream does not exist'
        assert isinstance(upstream, NGinxConfigurer.Upstream), \
                'upstream must be a Upstream object'
        self._upstreams[name] = upstream

    @staticmethod
    def from_config_file(config_file):
        return NGinxConfigurer()
    
    @staticmethod
    def parse_config(raw_config):
        upstreams = {}
        for match in re.findall(UPSTREAM_REGEX, raw_config):
            upstream = NGinxConfigurer.parse_upstream(match.group(0))
            upstreams[upstream.name] = upstream
        return upstreams

    @staticmethod
    def parse_upstream(upstream_raw):
        match = re.match(UPSTREAM_REGEX, upstream_raw)
        assert match, 'This is not a NGinx upstream'
        name = match.group(1)
        upstream = NGinxConfigurer.Upstream(name)
        parameters = {}
        for parameter in match.group(2).split(';'):
            parameter = parameter.strip()
            if parameter:
                key, sep, value = parameter.partition('=')
                value = value if sep else None
                parameters[key] = value

    class Group:
        def __init__(self, type_, properties=None, parameters=None, subgroups=None):
            assert isinstance(type_, str), 'type must be string'
            assert not properties or isinstance(properties, Iterable), 'properties must be iterable'
            assert not parameters or isinstance(parameters, Iterable), 'parameters must be iterable'
            assert not subgroups or isinstance(subgroups, Iterable), 'subgroups must be iterable'
            assert not parameters or all(isinstance(p, NGinxConfigurer.Parameter) for p in parameters), \
                'expecting Parameters object in parameters'
            assert not subgroups or all(isinstance(p, NGinxConfigurer.Group) for p in subgroups), \
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
        
        def add_parameter(self, name, *args, **kwargs):
            self._parameters.append(NGinxConfigurer.Parameter(name, *args, **kwargs))

        def get_parameters(self):
            return self._parameters
        
        def add_properties(self, *properties):
            self._properties.extend(properties)
        
        def get_properties(self):
            return self._properties

    class Parameter:
        def __init__(self, name, *args, **kwargs):
            assert isinstance(name, str), 'name must be string'
            assert all(isinstance(a, str) for a in args), 'all parameters must be string'
            assert all(not re.search(r'\s', a) for a in args), 'parameters without value must not have whitespace'
            assert all(isinstance(k, str) for k, v in kwargs.items()), \
                'key-value parameters must be string'
            assert all(not re.search(r'\s', k) for k in kwargs), 'key-value parameters must not have whitespace'
            
            self.name = name
            self.args = args
            self.kwargs = kwargs
        
        def __str__(self):
            kwargs = (f"{k}={shlex.quote(str(v)) if v else ''}" for k, v in self.kwargs.items())
            return ' '.join(itertools.chain((self.name,), self.args, kwargs))

        def __repr__(self):
            args = ', '.join(map(repr, self.args))
            kwargs = ','.join(f'{k}={repr(v)}' for k, v in self.kwargs.items())
            return f"{self.__class__.__name__}({repr(self.name)}, {', '.join((args, kwargs))})"
    
    class Upstream(Group):
        def __init__(self, name):
            super().__init__('upstream', (name,))
        
        def add_server(self, name, *args, **kwargs):
            assert not self.get_server(name), 'there is already a server with that name'
            return self.add_parameter('server', name, *args, **kwargs)
        
        def remove_server(self, name):
            server_parameter = self.get_server(name)
            assert server_parameter, 'server does not exist'
            self._parameters.remove(server_parameter)

        def get_server(self, name):
            return next((p for p in self._parameters if p.args[0] == name), None)

if __name__ == "__main__":
    upstream = NGinxConfigurer.Upstream('dynamics')
    upstream.add_server('backend1.example.com', weight=5)
    print(upstream)
