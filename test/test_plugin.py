import os
import pytest
from haruba.plugins import PluginManager

ROOT_DIR = pytest.ROOT_DIR


def test_plugin_manager():
    plugin_dir = os.path.join(ROOT_DIR, "data", "mock_plugin")
    pm = PluginManager(plugin_dir)
    plugins = pm.available_plugins
    assert sorted(plugins) == sorted(['mock_plugin', 'broken_plugin'])
    module = pm.load_plugin('mock_plugin')
    assert module.init_plugin() == "mock plug-in initialized"


def test_broken_plugin_manager():
    plugin_dir = os.path.join(ROOT_DIR, "data", "mock_plugin")
    pm = PluginManager(plugin_dir)
    with pytest.raises(ImportError) as excinfo:
        pm.load_plugin('broken_plugin')
    assert str(excinfo.value) == "Plug-in must have an 'init_plugin' method"
