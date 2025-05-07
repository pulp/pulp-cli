# How to Create a Pulp CLI Module Similar to `pulp-cli-console`

This guide provides a comprehensive walkthrough for creating a Pulp CLI module similar to `pulp-cli-console`. It includes details on the required files, directory structure, and examples to help you build your own module.

---

## 1. Overview

A Pulp CLI module extends the functionality of the Pulp CLI by adding custom commands and features. For example, `pulp-cli-console` provides administrative tools for managing tasks, vulnerabilities, and performance monitoring.

---

## 2. Directory Structure

Here is the recommended directory structure for your module:

```plaintext
my-pulp-cli-module/
├── my_pulp_cli_module/
│   ├── __init__.py
│   ├── cli/
│   │   └── my_command/
│   │       ├── __init__.py  # Registers commands
│   │       └── task.py  # Example subcommand
│   └── glue/
│       ├── __init__.py
│       └── context.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_task.py
├── pyproject.toml
├── README.md
├── MANIFEST.in
└── requirements.txt
```

---

## 3. Key Files and Their Purpose

### 3.1 `pyproject.toml`

Defines the project metadata and dependencies. Example:

```toml
[build-system]
requires = ["setuptools>=42", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "my-pulp-cli-module"
version = "0.1.0"
description = "A custom Pulp CLI module"
readme = "README.md"
requires-python = ">=3.8"
dependencies = [
    "pulp-cli",
    "click"
]

[project.entry-points."pulp_cli.plugins"]
my_module = "my_pulp_cli_module.cli"
```

### 3.2 `cli/my_command/__init__.py`

Registers the CLI commands with the Pulp CLI.

```python
from my_pulp_cli_module.cli.my_command.task import attach_task_commands

def attach_my_commands(main):
    """Attach all subcommands to the main CLI group."""
    @main.group()
    def my_command():
        """My custom Pulp CLI commands."""
        pass

    attach_task_commands(my_command)
```

### 3.3 `cli/my_command/task.py`

This file provides an example of a subcommand under `my_command`. It demonstrates how to define and attach subcommands to the main CLI group.

```python
import click
from pulp_glue.common.context import PulpContext
from pulpcore.cli.common.generic import pass_pulp_context

def attach_task_commands(group: click.Group):
    """Attach example subcommands."""
    @group.group()
    @pass_pulp_context
    def task(ctx, pulp_ctx: PulpContext):
        """Example subcommand group."""
        pass

    @task.command()
    @click.option("--limit", type=int, help="Limit the number of items shown")
    @pass_pulp_context
    def list(pulp_ctx: PulpContext, limit: int):
        """Example list command."""
        items = pulp_ctx.list_items(limit=limit)  # Replace with actual logic
        click.echo(items)
```

### 3.4 `glue/context.py`

Provides a custom context for interacting with the Pulp API.

```python
from pulp_glue.common.context import PulpContext

class MyPulpContext(PulpContext):
    def list_tasks(self, limit):
        return self.call_api("/tasks", params={"limit": limit})
```

### 3.5 `tests/conftest.py`

Sets up test fixtures.

```python
import pytest
from my_pulp_cli_module.glue.context import MyPulpContext

@pytest.fixture
def pulp_context():
    return MyPulpContext(base_url="http://test-server", username="admin", password="password")
```

### 3.6 `tests/test_task.py`

Tests the task commands.

```python
from click.testing import CliRunner
from my_pulp_cli_module.cli.commands.task import list

def test_list_tasks(pulp_context):
    runner = CliRunner()
    result = runner.invoke(list, ["--limit", "10"], obj=pulp_context)
    assert result.exit_code == 0
    assert "tasks" in result.output
```

---

## 4. Development Workflow

### Step 1: Install Dependencies

```bash
pip install -e .
```

### Step 2: Run Tests

```bash
pytest
```

### Step 3: Test the CLI

```bash
pulp my-module task list --limit 10
```

---

## 5. Best Practices

1. **Follow PEP 8**: Ensure your code adheres to Python's style guide.
2. **Write Tests**: Cover all commands and edge cases.
3. **Use Click**: Leverage Click's features for robust CLI development.
4. **Document**: Provide clear documentation for users.

---

## 6. Example Usage

After installation, users can run:

```bash
pulp my-module task list --limit 10
```

---

By following this guide, you can create a fully functional Pulp CLI module that integrates seamlessly with the Pulp ecosystem.