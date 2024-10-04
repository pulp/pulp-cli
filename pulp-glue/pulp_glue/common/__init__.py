import sys
import typing as t

if sys.version_info >= (3, 10):
    from importlib.metadata import entry_points
else:
    from importlib_metadata import entry_points

__version__ = "0.30.0.dev"

# Keep track to prevent loading plugins twice
loaded_plugins: t.Set[str] = set()


def load_plugins(enabled_plugins: t.Optional[t.List[str]] = None) -> None:
    """
    Load glue plugins that provide a `pulp_glue.plugins` entrypoint.
    This may be needed when you rely on the `TYPE_REGISTRY` attributes but cannot load the modules
    explicitely.

    Parameters:
        enabled_plugins: Optional list of plugins to consider for loading.
    """
    for entry_point in entry_points(group="pulp_glue.plugins"):
        name = entry_point.name
        if (
            enabled_plugins is None or entry_point.name in enabled_plugins
        ) and entry_point.name not in loaded_plugins:
            plugin = entry_point.load()
            if hasattr(plugin, "mount"):
                plugin.mount()
            loaded_plugins.add(name)
