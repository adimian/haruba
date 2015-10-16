import imp
import importlib
import pkgutil
import sys


def is_plugin_list(candidate):
    if not isinstance(candidate, list):
        raise Exception("active plug-ins must be of type: list")


class PluginManager(object):
    def __init__(self, plugin_dir, active_plugins=None):
        self._available_plugins = []
        self.plugin_dir = plugin_dir
        self.active_plugins = []
        if active_plugins:
            is_plugin_list(active_plugins)
            self.active_plugins.extend(active_plugins)

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

    def activate_plugins(self, plugins):
        if isinstance(plugins, str):
            plugins = [plugins]
        is_plugin_list(plugins)
        self.active_plugins.extend(plugins)

    def load_active_plugins(self):
        for plugin in self.active_plugins:
            self.load_plugin(plugin).init_plugin()
