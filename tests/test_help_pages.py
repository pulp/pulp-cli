# type: ignore

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


@pytest.fixture
def no_api(monkeypatch):
    @property
    def getter(self):
        pytest.fail("Invalid access to 'PulpContext.api'.", pytrace=False)

    monkeypatch.setattr("pulpcore.cli.common.context.PulpContext.api", getter)


@pytest.mark.help_page
@pytest.mark.parametrize("args", traverse_commands(main, []), ids=" ".join)
def test_access_help(no_api, args):
    """Test, that all help screens are accessible without touching the api property."""
    runner = CliRunner()
    result = runner.invoke(main, args + ["--help"], catch_exceptions=False)
    assert result.exit_code == 0
    assert result.stdout.startswith("Usage:") or result.stdout.startswith("DeprecationWarning:")
