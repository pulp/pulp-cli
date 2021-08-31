# Contributing

There are many ways to contribute to this project, and all are welcome.

## Pulp CLI feedback & thank you

If you take the time to evaluate, test, or build your own CLI commands, please complete [this survey](https://forms.gle/ca1nxVVkNivEeE5m8), and we will gladly ship you some SWAG!

## Doc contributions

If you see something wrong with the docs, we welcome [documentation PRs](https://github.com/pulp/pulp-cli).

If you are using the Pulp CLI and have written end-to-end steps for Pulp workflows, we would greatly appreciate if you would contribute docs to the relevant [plugins](https://docs.pulpproject.org/pulpcore/plugins/index.html).


## Code conventions

If you are interested in contributing code, note that we have some styling and formatting conventions:

`pulp-cli` comes with python type annotations and black code formatting.
To run the auto-formatting features, execute `make black`.
Please run `make lint` before committing changes to check for compliance.
Also please follow [The seven rules of a great Git commit message](https://chris.beams.io/posts/git-commit/).
For each new feature, we require corresponding tests.

## Pulp CLI Architecture

If you are interested in extending, patching, or contributing new Pulp CLI features, you can find information about the Pulp CLI architecture in this section.  

### Plugin system

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

### Contexts

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

### Version dependent code paths

Each Pulp CLI release is designed to support multiple Pulp server versions and the CLI itself is versioned independently of any version of the Pulp server components.
It is supposed to be able to communicate with different combinations of server component versions at the same time.
Because of this, it might be necessary to guard certain features and workarounds by checking against the available server plugin version.
As a rule of thumb, all necessary workarounds should be implemented in the corresponding `Context` objects to provide a consistent interface to the command callbacks.
To facilitate diverting code paths depending on plugin versions, the `PulpContext` provides the `needs_plugin` and `has_plugin` methods.
While `has_plugin` will evaluete immediately, `needs_plugin` can be seen as a deferred assertion.
It will raise an error, once the first access to the server is attempted.

```python
class MyEntityContext(PulpEntityContext):
    def show(self, href):
        if self.pulp_ctx.has_plugin(PluginRequirement("my_content", min="1.2.3", inverted=True)):
            # Versioned workaroud
            # see bug-tracker/12345678
            return lookup_my_content_legacy(href)
        return super().show(href)


@main.command()
@pass_pulp_context
@click.pass_context
def my_command(ctx, pulp_ctx):
    pulp_ctx.needs_plugin(PluginRequirement("my_content", min="1.0.0"))
    ctx.obj = MyEntityContext(pulp_ctx)
```

The named tuple `PluginRequirement` is used to describe dependence on server components.
It needs the `name` of the plugin and accepts optionally an inclusive `min` version,
an exclusive `max` version, and an `inverted` flag for exclusion of a version range.

Additionally, the `PulpOption` provides the `needs_plugins` keyword argument.
It accepts a list of `PluginRequirements` to error when used.

### Generics

For certain often repeated patterns like listing all entities of a particular kind,
we provide generic commands that use the underlying context objects.

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

## Global help accessibility

In order to be able to access every (sub-)commands help page,
it is necessary that no code outside of the final performing command callback accesses the `api` property of the `PulpContext`.
There are some facilities that perform lazy loading to help with that requirement.
Those include:
  - `PulpContext.api`: When accessed, the `api.json` file for the addressed server will be read or downloaded and processed.
    Scheduled version checks will be reevaluated.
  - `PulpContext.needs_version`: This function can be used at any time to declear that an operation needs a plugin in a version range.
    The actual check will be performed, once `api` was accessed for the first time, or immediately afterwards.
  - `PulpEntityContext.entity`: This property can be used to collect lookup attributes for entities by assigining dicts to it.
    On read access, the entity lookup will be performed though the `api` property.
  - `PulpEntityContext.pulp_href`: This property can be used to specify an entity by its URI.
    It will be fetched from the server only at read access.

## Testing

Tests are shell scripts in `tests/scripts` with names like `test_*.sh`.
They should should focus on the cli operation and are not a replacement for pulp integration tests;
i.e. make sure the cli translates to the right api calls, but do not care about pulp internals.

## Running Tests

In order to run tests, a running instance of pulp with all necessary plugins installed must be
configured in `tests/cli.toml`.

To run tests:

```
make test                           # all tests
pytest -m pulp_file                 # tests for pulp_file
pytest -m pulp_file -k test_remote  # run tests/scripts/pulp_file/test_remote.sh
```
