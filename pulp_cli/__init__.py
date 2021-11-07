from types import ModuleType
from typing import Any, Dict

import click
import pkg_resources


def main() -> Any:
    ##############################################################################
    # Load plugins
    # https://packaging.python.org/guides/creating-and-discovering-plugins/#using-package-metadata
    discovered_plugins: Dict[str, ModuleType] = {
        entry_point.name: entry_point.load()
        for entry_point in pkg_resources.iter_entry_points("pulp_cli.plugins")
    }
    _main: click.Group = discovered_plugins["common"].main
    for plugin in discovered_plugins.values():
        if hasattr(plugin, "mount"):
            plugin.mount(_main, discovered_plugins=discovered_plugins)
    return _main()
