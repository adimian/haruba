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


def test_nonexisting_plugin_manager():
    plugin_dir = os.path.join(ROOT_DIR, "data", "mock_plugin")
    pm = PluginManager(plugin_dir)
    with pytest.raises(ImportError) as excinfo:
        pm.load_plugin('doesnt_exist')
    assert str(excinfo.value) == "No module named doesnt_exist"


def test_plugins_list():
    plugin_dir = os.path.join(ROOT_DIR, "data", "mock_plugin")
    pm = PluginManager(plugin_dir, ["mock_plugin", ])
    assert pm.active_plugins == ["mock_plugin"]


def test_add_list_active_plugin():
    plugin_dir = os.path.join(ROOT_DIR, "data", "mock_plugin")
    pm = PluginManager(plugin_dir)
    pm.activate_plugin(["mock_plugin", "broken_plugin"])
    print(pm.active_plugins)
    assert pm.active_plugins == ["mock_plugin", "broken_plugin"]


def test_add_str_active_plugin():
    plugin_dir = os.path.join(ROOT_DIR, "data", "mock_plugin")
    pm = PluginManager(plugin_dir)
    pm.activate_plugin("mock_plugin")
    assert pm.active_plugins == ["mock_plugin"]


def test_add_active_plugin():
    plugin_dir = os.path.join(ROOT_DIR, "data", "mock_plugin")
    pm = PluginManager(plugin_dir, ["mock_plugin", ])
    pm.start_active_plugins()
