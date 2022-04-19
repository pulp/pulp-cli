# type: ignore

from unittest.mock import PropertyMock, patch

import click
import pytest
from click.testing import CliRunner

from pulp_cli import load_plugins

main = load_plugins()


def traverse_commands(command, args):
    yield args
    if isinstance(command, click.Group):
        for name, sub in command.commands.items():
            yield from traverse_commands(sub, args + [name])


@pytest.mark.help_page
@pytest.mark.parametrize("args", traverse_commands(main, []), ids=" ".join)
@patch("pulpcore.cli.common.context.PulpContext.api", new_callable=PropertyMock)
def test_access_help(_api, args):
    """Test, that all help screens are accessible without touching the api property."""
    runner = CliRunner()
    result = runner.invoke(main, args + ["--help"])
    assert result.exit_code == 0
    assert result.stdout.startswith("Usage:") or result.stdout.startswith("DeprecationWarning:")
    _api.assert_not_called()
