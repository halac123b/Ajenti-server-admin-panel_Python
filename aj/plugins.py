import os
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