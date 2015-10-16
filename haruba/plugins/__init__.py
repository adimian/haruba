import imp
import importlib
import pkgutil
import sys


class PluginManager(object):
    def __init__(self, plugin_dir, active_plugins=None):
        self._available_plugins = []
        self.plugin_dir = plugin_dir
        self.active_plugins = []
        if active_plugins:
            for plugin in active_plugins:
                self.activate_plugin(plugin)

    @property
    def available_plugins(self):
        if not self._available_plugins:
            modules = pkgutil.iter_modules(path=[self.plugin_dir])
            self._available_plugins = [module for _, module, _ in modules]
        return self._available_plugins

    def load_plugin(self, plugin):
        if plugin in self.available_plugins:
            module = sys.modules.get(plugin)
            if not module:
                sys.path.append(self.plugin_dir)
                module = importlib.import_module(plugin)
            if not hasattr(module, "init_plugin"):
                raise ImportError("Plug-in must have an 'init_plugin' method")
            return module
        raise ImportError("No module named %s" % plugin)

    def activate_plugin(self, plugin):
        if isinstance(plugin, (list, tuple)):
            for sub in plugin:
                self.activate_plugin(sub)
        self.active_plugins.append(plugin)

    def start_active_plugins(self):
        for plugin in self.active_plugins:
            self.load_plugin(plugin).init_plugin()
