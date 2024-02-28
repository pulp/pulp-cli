import sys
import typing as t
from types import ModuleType

import click

if sys.version_info >= (3, 10):
    from importlib.metadata import entry_points
else:
    from importlib_metadata import entry_points

__version__ = "0.24.0.dev"
_main: t.Optional[click.Group] = None


def load_plugins() -> click.Group:
    global _main

    ##############################################################################
    # Load plugins
    # https://packaging.python.org/guides/creating-and-discovering-plugins/#using-package-metadata
    discovered_plugins: t.Dict[str, ModuleType] = {
        entry_point.name: entry_point.load()
        for entry_point in entry_points(group="pulp_cli.plugins")
    }
    _main = discovered_plugins["common"].main
    assert isinstance(_main, click.Group)
    for plugin in discovered_plugins.values():
        if hasattr(plugin, "mount"):
            plugin.mount(_main, discovered_plugins=discovered_plugins)
    return _main


def main() -> t.Any:
    if _main is None:
        load_plugins()
        assert _main is not None
    return _main()
