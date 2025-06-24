# How to Create a Pulp CLI Plugin

This guide shows you how to create a Pulp CLI plugin using the provided bootstrap templates.
Instead of manually creating all the required files, the bootstrap process will automatically generate the correct structure and files for you.

## Overview

Pulp CLI plugin extend the functionality of the Pulp CLI by adding custom commands and features.
The `pulp-cli` project includes templates that make it easy to bootstrap a new plugin with the correct structure and configuration.

## Prerequisites

Before you begin, ensure you have the following installed:

```bash
pip install cookiecutter click pyyaml tomlkit
```

## Bootstrap a New Pulp CLI Plugin

### Using the Bootstrap Template

Navigate to the directory where you want to create your new plugin and run:

```bash
# Clone the pulp-cli repository if you don't have it already
git clone https://github.com/pulp/pulp-cli.git

# Run the bootstrap script
pulp-cli/cookiecutter/apply_templates.py --bootstrap
```

### Answer the Prompts

You will be prompted for several values during the bootstrap process.
The most important is **app_label**, which by convention (when applicable) should match the Pulp server component your plugin targets (for example, use `file` for `pulp-file`).
This value determines the import paths and command names for your plugin.
You will also see additional prompts for options such as glue integration, documentation, translations, version, repository URL, and CI configuration.
Answer these as appropriate for your project.

### Key Files and Directories

The bootstrap process creates several important directories and files:

- `pulpcore/cli/my-plugin/__init__.py`: Main entry point where you define command groups.
  See below for more details
- `pulp-glue-my-plugin/pulp_glue/my-plugin/context.py`: API context class for interacting with Pulp.
  See below for more details
- `pyproject.toml`: Project metadata, dependencies, and build configuration.
  This file contains essential project information including author details, licensing information, version numbers, package dependencies, and build system configuration.
  You'll need to customize the author name, email, project description, license type to match your plugin's specific requirements.
- `CHANGES/`: Directory for changelog fragments (.feature, .bugfix, etc. files).
  See the [changelog update guide] for more details.
- `.github/workflows/`: This directory contains GitHub Actions workflow configurations for automated testing and continuous integration.
  These files are pre-configured and do not require modification when initially setting up your plugin development environment.
  The CI workflows will automatically run tests and validation checks on your plugin code when you push changes to your repository.

## Customizing Your Plugin

### Create API Context Classes

Edit `pulp-glue-my-plugin/pulp_glue/my_plugin/context.py` to define context classes that handle API interactions:

```python
import typing as t

from pulp_glue.common.context import (
    PulpEntityContext,
    PluginRequirement
) 


class PulpMyResourceContext():
    """Context for working with my custom resource."""

    ID_PREFIX = "my_resource"
    NEEDS_PLUGINS = [PluginRequirement("my_plugin", specifier=">=0.0.1")]

    def example_action(self, data: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
        """Execute an example action with specific data.

    Args:
        data: The data dictionary to send to the API

    Returns:
        The action result
    """
        response = self.call(
            operation="example_action",
            body=data,
        )
        return response
```

### Add Subcommands to the CLI

Edit `pulpcore/cli/my_plugin/__init__.py` to define your command groups and add functionality:

```python
import typing as t
import click
from pulp_cli.generic import pulp_group
from pulp_glue.common.i18n import get_translation

# Import your command plugins
from pulpcore.cli.my_plugin.my_resource import my_resource

translation = get_translation(__package__)
_ = translation.gettext

__version__ = "0.1.0"  # Matches version in pyproject.toml


@pulp_group(name="my_plugin")
def my_plugin_group() -> None:
    """My plugin commands."""
    pass


def mount(main: click.Group, **kwargs: t.Any) -> None:
    # Add your command groups here
    my_plugin_group.add_command(my_resource)
    main.add_command(my_plugin_group)
```

### Create Plugin Commands

Create a new file for your resource, e.g., `pulpcore/cli/my_plugin/my_resource.py`:

```python
import click
from pulp_cli.common.context import pass_pulp_context
from pulp_glue.common.context import PulpContext
from pulp_glue.my_plugin.context import PulpMyResourceContext
from pulp_cli.common.generic import pass_entity_context


@click.group()
@pass_pulp_context
@click.pass_context 
def my_resource(ctx: click.Context, pulp_ctx: PulpContext, /) -> None:
    """My custom commands."""
    ctx.obj = PulpMyResourceContext(pulp_ctx)


@my_resource.command()
@click.option("--data", required=True, help="Data for the example action")
@pass_entity_context
@pass_pulp_context
def my_command(pulp_ctx: PulpContext, my_resource_ctx: PulpMyResourceContext, /, data: str):
    """Calling example action."""
    result = my_resource_ctx.example_action({"data": data})
    pulp_ctx.output_result(result)
```

## Development Workflow

### Install Your plugin in Development Mode

For installation instructions, see [here][installation].

### Test Your Commands

After installation, you can test your commands:

```bash
pulp my-plugin my-resource my-command --data "example"
```

Consider [writing tests] for your commands as soon as you implement them.

## Update Templates

If you need to update the project structure with new template changes:

```bash
cd pulp-cli-my-plugin
../pulp-cli/cookiecutter/apply_templates.py
```

[changelog update guide]: site:pulpcore/docs/dev/guides/git/#changelog-update
[installation]: site:pulp-cli/docs/user/guides/installation#from-a-source-checkout
[writing tests]: site:pulp-cli/docs/dev/guides/contributing/#testing