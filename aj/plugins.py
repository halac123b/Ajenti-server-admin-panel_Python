import logging
import os

import yaml
from aj.util import public
import jadi

@public
@jadi.service
class PluginManager():
    """
    Handles plugin loading and unloading
    """
    __plugin_info = {}
    __crashes = {}

    def __init__(self, context):
        self.context = context
        self.load_order = []
    
    def get_crash(self, name):
        return self.__crashes.get(name, None)
    
    def __getitem__(self, name):
        return self.__plugin_info[name]
    
    def __iter__(self):
        return iter(self.load_order)
    
    def __len__(self):
        return len(self.__plugin_info)
    
    def get_content_path(self, name, path):
        path = path.replace('..', '').strip('/')
        return os.path.join(self[name]['path'], path)
    
    def get_loaded_plugins_list(self):
        for plugin in self:
            if self[plugin]['imported']:
                yield self[plugin]['info']['name']

    def load_all_from(self, providers):
        """
        Loads all plugins provided by given providers.

        :param providers:
        :type providers: list(:class:`PluginProvider`)
        """
        found = []
        for provider in providers:
            found += provider.provide()
        
        self.__plugin_info = {}
        for path in found:
            try:
                yml_info = yaml.load(open(os.path.join(path, 'plugin.yml')), Loader=yaml.SafeLoader)
            except yaml.constructor.ConstructorError:
                logging.error(f"Malformatted plugin.yml located at {path}, not loading plugin.")
                continue
            yml_info['resources'] = [
                ({'path': x} if isinstance(x, str) else x)
                for x in yml_info.get('resources', [])
            ]

            self.__plugin_info[yml_info['name']] = {
                'info': yml_info,
                'path': path,
                'imported': False,
            }

        logging.info(f'Discovered {len(self.__plugin_info):d} plugins')

        self.load_order = []
        to_load = list(self.__plugin_info.values())

        while True:
            delta = 0
            for plugin in to_load:
                for dep in plugin['info']['dependencies']:
                    if isinstance(dep, PluginDependency) and dep.plugin_name not in self.load_order:
                        break

@public
class PluginProvider():
    """
    A base class for plugin locator
    """
    def provide(self):
        """
        Should return a list of found plugin paths

        :returns: list(str)
        """
        raise NotImplementedError()

@public
class PluginLoadError(Exception):
    pass

@public
class Dependency(yaml.YAMLObject):
    yaml_loader = yaml.SafeLoader
    yaml_tag = u'!Dependency'

    class Unsatisfied(PluginLoadError):
        def __init__(self):
            PluginLoadError.__init__(self, None)
            self.dependency = None
        
        def reason(self):
            pass

        def describe(self):
            return 'Dependency unsatisfied'
        
        def __str__(self):
            return f'{self.dependency.__class__.__name__} ({self.reason()})'
        
    def build_exception(self):
        exception = self.Unsatisfied()
        exception.dependency = self
        return exception
    
    def check(self):
        if not self.is_satisfied():
            exception = self.build_exception()
            raise exception
    
    def is_satisfied(self):
        pass

    @property
    def value(self):
        return str(self)

@public
class PluginDependency(Dependency):
    pass