## Architecture

The Pulp CLI architecture is described in this section.

### Plugin System

The Pulp CLI is designed with a plugin structure. Plugins can either live in the pulp-cli package or be shipped independently.
By convention, all parts of the CLI are packages in the open namespace `pulpcore.cli`.
A plugin can register itself with the main app by specifying its main module as a `pulp_cli.plugins` entrypoint in `setup.py`.

```python
entry_points={
    "pulp_cli.plugins": [
        "myplugin=pulpcore.cli.myplugin",
    ],
}
```

The plugin should then attach subcommands to the `pulpcore.cli.common.main` command by providing a `mount` method in the main module.

```python
from pulpcore.cli.common.generic import pulp_command

@pulp_command()
def my_command():
    pass


def mount(main: click.Group, **kwargs: Any) -> None:
    main.add_command(my_command)
```

### Pulp Glue

Pulp CLI provides the `pulp-glue` library as an abstraction layer that let's you perform high level operations in pulp.
Its goal is to abstract interacting with the rest api by parsing the api docs and waiting on tasks and task groups.
It is shipped as a separate python package to allow broad use across multiple projects, such as `pulp-squeezer` and `pulpcore`.
To this end, `pulp-glue` is the go to place for all known version dependent Pulp API subtleties and their corresponding fixes (see Version dependent codepaths below).

#### Contexts

In `click`, every subcommand is accompanied by a `click.Context`, and objects can be attached to them.
In this CLI we attach a [`PulpCLIContext`][pulpcore.cli.common.generic.PulpCLIContext] to the main command, which inherits from `pulp-glue`'s [`PulpContext`][pulp_glue.common.context.PulpContext].
This context handles the communication to the pulp server through its `api` property.

Further we encourage the handling of communication with certain endpoints by subclassing the [`PulpEntityContext`][pulp_glue.common.context.PulpEntityContext] or some of the resource-specific children, such as [PulpRepositoryContext][pulp_glue.common.context.PulpRepositoryContext].
Some examples of this can be found under `pulp_glue/{plugin-name}/context.py`.

By attaching them to the contexts of certain command groups, they are accessible to commands via the `pass_entity_context` decorator.
Those entity contexts should provide a common interface to the layer of `click` commands that define the user interaction.

```python
@pulp_group()
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

#### Version dependent code paths

Each Pulp CLI release is designed to support multiple Pulp server versions and the CLI itself is versioned independently of any version of the Pulp server components.
It is supposed to be able to communicate with different combinations of server component versions at the same time.
Because of this, it might be necessary to guard certain features and workarounds by checking against the available server plugin version.

As a rule of thumb, all necessary workarounds should be implemented in the corresponding `Context` objects.
To facilitate diverting code paths depending on plugin versions, the `PulpContext` provides the `needs_plugin` and `has_plugin` methods, both of which accept a [`PluginRequirement`][pulp_glue.common.context.PluginRequirement] object to describe dependencies on server components.

While `has_plugin` will evaluate immediately, `needs_plugin` can be seen as a deferred assertion.
It will raise an error, once the first access to the server is attempted.

```python
class MyEntityContext(PulpEntityContext):
    def show(self, href):
        if self.pulp_ctx.has_plugin(PluginRequirement("my_content", specifier=">=1.2.3", inverted=True)):
            # Versioned workaroud
            # see bug-tracker/12345678
            return lookup_my_content_legacy(href)
        return super().show(href)


@main.command()
@pass_pulp_context
@click.pass_context
def my_command(ctx, pulp_ctx):
    pulp_ctx.needs_plugin(PluginRequirement("my_content", specifier=">=1.0.0"))
    ctx.obj = MyEntityContext(pulp_ctx)
```

To declare version restrictions on *options*, the [`preprocess_entity`][pulp_glue.common.context.PulpEntityContext.preprocess_entity] method can be used to check if a given option is present in the request body and conditionally apply the requirements to the context.

In the following example, a guard is added because `my_option` was introduced to `MyPluginRepository` in version 3.24.0 of `"my_plugin"`:

```python
class PulpMyPluginRepositoryContext(PulpRepositoryContext):
    ...

    def preprocess_entity(self, body, partial) -> EntityDefinition:
        body = super().preprocess_entity(body, partial=partial)
        if "my_option" in body:
            self.pulp_ctx.needs_plugin(
                PluginRequirement("my_plugin", specifier=">=3.24.0", feature=_("my feature"))
            )
        return body
```

### Generics

For certain often repeated patterns like listing all entities of a particular kind,
we provide generic commands that use the underlying context objects.
The following example shows the use of the [`show_command`][pulpcore.cli.common.generic.show_command] generic.

```python
from pulpcore.cli.common.generic import name_option, show_command,

lookup_params = [name_option]
my_command.add_command(show_command(decorators=lookup_params))
```

To add options to these subcommands, pass a list of [`PulpOption`][pulpcore.cli.common.generic.PulpOption] objects to the `decorators` argument.
Preferably these are created using the [`pulp_option`][pulpcore.cli.common.generic.pulp_option] factory.

```python
from pulpcore.cli.common.generic import list_command,

filter_params = [
    pulp_option("--name"),
    pulp_option("--name-contains", "name__contains"),
]
my_command.add_command(list_command(decorators=filter_params))
```
