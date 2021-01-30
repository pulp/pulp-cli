# Pulp CLI Architecture

## Plugin system

The Pulp CLI is designed with a plugin structure. Plugins can either live in the pulp-cli package or be shipped independently.
By convention, all parts of the CLI are packages in the open namespace `pulpcore.cli`.
A plugin can register itself with the main app by specifying by specifying its main module as a `pulp_cli.plugins` entrypoint in `setup.py`.

```python
entry_points={
    "pulp_cli.plugins": [
        "myplugin=pulpcore.cli.myplugin",
    ],
}
```

The plugin can then attach subcommands to the `pulpcore.cli.common.main` command.

```python
from pulpcore.cli.common import main

@main.command()
def my_command():
    pass
```

## Contexts

In `click`, every subcommand is accompanied by a `click.Context`, and objects can be attached to them.
In this CLI we attach a `PulpContext` to the main command.
It acts as an abstraction layer that handles the communication to the pulp server through its `api` property.
Further we encourage the handling of communication with certain endpoints by subclassing the `PulpEntityContext`.
By attaching them to the contexts of certain command groups, they are accessible to commands via the `pass_entity_context` decorator.
Those entity contexts should provide a common interface to the layer of `click` commands that define the user interaction.

```python
@main.command()
@pass_pulp_context
@click.pass_context
def my_command(ctx, pulp_ctx):
    ctx.obj = MyEntityContext(pulp_ctx)


@my_command.command()
@pass_entity_context
def my_sub_command(entity_ctx):
    ... href = ...
    entity_ctx.destroy(href)
```

### Version dependent codepaths

Each pulp CLI release is designed to support multiple pulp server versions.
The entity contexts should be used to implement necessary server version-dependent workarounds.
To facilitate this, the `PulpContext` provides the `needs_plugin` and `has_plugin` methods.

```python
class MyEntityContext(PulpEntityContext):
    def show(self, href):
        if not self.pulp_ctx.has_plugin("pulp_my_content", min_version="1.2.3"):
            return lookup_my_content_legacy(href)
        else:
            return super().show(href)


@main.command()
@pass_pulp_context
@click.pass_context
def my_command(ctx, pulp_ctx):
    pulp_ctx.needs_plugin("pulp_my_content", min_version="1.0.0")
    ctx.obj = MyEntityContext(pulp_ctx)
```

## Generics

For certain often repeated patterns like listing all entities of a  particular kind, we provide generic commands that use the underlying context objects.

```python
from pulpcore.cli.common.generic import name_option, show_command,

lookup_params = [name_option]
my_command.add_command(show_command(decorators=lookup_params))
```

Some of these commands understand extra arguments.
They can be attached by passing a list of `click.Options` via the `decorators` argument.

```python
from pulpcore.cli.common.generic import list_command,

filter_params = [
    click.option("--name"),
    click.option("--name-contains", "name__contains"),
]
my_command.add_command(list_command(decorators=filter_params))
```
