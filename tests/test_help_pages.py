import typing as t
from functools import reduce

import click
import pytest
from click.testing import CliRunner
from pytest_subtests.plugin import SubTests

from pulp_cli import load_plugins, main

load_plugins()


def traverse_commands(command: click.Command, args: t.List[str]) -> t.Iterator[t.List[str]]:
    yield args

    if isinstance(command, click.Group):
        for name, sub in command.commands.items():
            yield from traverse_commands(sub, args + [name])

        params = command.params
        if params:
            if "--type" in params[0].opts:
                # iterate over commands with specific context types
                assert isinstance(params[0].type, click.Choice)
                for context_type in params[0].type.choices:
                    yield args + ["--type", context_type]

                    for name, sub in command.commands.items():
                        yield from traverse_commands(sub, args + ["--type", context_type, name])


@pytest.fixture
def no_api(monkeypatch: pytest.MonkeyPatch) -> None:
    @property  # type: ignore
    def getter(self: t.Any) -> None:
        pytest.fail("Invalid access to 'PulpContext.api'.", pytrace=False)

    monkeypatch.setattr("pulp_glue.common.context.PulpContext.api", getter)


@pytest.mark.help_page
def test_access_help(no_api: None, subtests: SubTests) -> None:
    """Test, that all help screens are accessible without touching the api property."""
    runner = CliRunner()
    for args in traverse_commands(main, []):
        with subtests.test(msg=" ".join(args)):
            result = runner.invoke(main, args + ["--help"], catch_exceptions=False)

            if result.exit_code == 2:
                assert (
                    "not available in this context" in result.stdout
                    or "not available in this context" in result.stderr
                )
            else:
                assert result.exit_code == 0
                assert result.stdout.startswith("Usage:") or result.stdout.startswith(
                    "DeprecationWarning:"
                )


@pytest.mark.parametrize(
    "command,options",
    [
        (
            [
                "file",
                "repository",
                "show",
            ],
            [
                "--repository",
                "dummy",
            ],
        ),
        pytest.param(
            [
                "file",
                "repository",
                "version",
                "show",
            ],
            [
                "--repository",
                "dummy",
                "--version",
                "42",
            ],
        ),
    ],
)
def test_deferred_context(
    monkeypatch: pytest.MonkeyPatch,
    no_api: None,
    command: t.List[str],
    options: t.List[str],
) -> None:
    monkeypatch.setattr(
        reduce(
            lambda com, sub: com.commands[sub] if isinstance(com, click.Group) else pytest.fail(),
            command,
            t.cast(click.Command, main),
        ),
        "callback",
        lambda: None,
    )
    runner = CliRunner()
    result = runner.invoke(main, command + options)
    assert result.exit_code == 0
