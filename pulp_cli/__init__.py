import typing as t
from types import ModuleType

import click
import pkg_resources

__version__ = "0.22.0.dev"


##############################################################################
# Load plugins
# https://packaging.python.org/guides/creating-and-discovering-plugins/#using-package-metadata
discovered_plugins: t.Dict[str, ModuleType] = {
    entry_point.name: entry_point.load()
    for entry_point in pkg_resources.iter_entry_points("pulp_cli.plugins")
}

main: click.Group = t.cast(click.Group, discovered_plugins["common"].main)

for plugin in discovered_plugins.values():
    if hasattr(plugin, "mount"):
        plugin.mount(main, discovered_plugins=discovered_plugins)
