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

        params = command.params
        if params:
            if "--type" in params[0].opts:
                # iterate over commands with specific context types
                for context_type in params[0].type.choices:
                    yield args + ["--type", context_type]

                    for name, sub in command.commands.items():
                        yield from traverse_commands(sub, args + ["--type", context_type, name])


@pytest.fixture
def no_api(monkeypatch):
    @property
    def getter(self):
        pytest.fail("Invalid access to 'PulpContext.api'.", pytrace=False)

    monkeypatch.setattr("pulp_glue.common.context.PulpContext.api", getter)


@pytest.mark.help_page
def test_access_help(no_api, subtests):
    """Test, that all help screens are accessible without touching the api property."""
    runner = CliRunner()
    for args in traverse_commands(main, []):
        with subtests.test(msg=" ".join(args)):
            result = runner.invoke(main, args + ["--help"], catch_exceptions=False)

            if result.exit_code == 2:
                assert "not available in this context" in result.stdout
            else:
                assert result.exit_code == 0
                assert result.stdout.startswith("Usage:") or result.stdout.startswith(
                    "DeprecationWarning:"
                )
