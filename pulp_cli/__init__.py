from types import ModuleType
from typing import Any, Dict, Optional

import click
import pkg_resources

__version__ = "0.19.5"
_main: Optional[click.Group] = None


def load_plugins() -> click.Group:
    global _main

    ##############################################################################
    # Load plugins
    # https://packaging.python.org/guides/creating-and-discovering-plugins/#using-package-metadata
    discovered_plugins: Dict[str, ModuleType] = {
        entry_point.name: entry_point.load()
        for entry_point in pkg_resources.iter_entry_points("pulp_cli.plugins")
    }
    _main = discovered_plugins["common"].main
    assert isinstance(_main, click.Group)
    for plugin in discovered_plugins.values():
        if hasattr(plugin, "mount"):
            plugin.mount(_main, discovered_plugins=discovered_plugins)
    return _main


def main() -> Any:
    if _main is None:
        load_plugins()
        assert _main is not None
    return _main()
