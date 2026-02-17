import typing as t
from functools import reduce

import click
import pytest
from click.testing import CliRunner

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


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    m = next(metafunc.definition.iter_markers("help_page"), None)
    if m is not None and "base_cmd" in m.kwargs:
        rel_main:click.Group = main
        base_cmd = m.kwargs["base_cmd"]
        for step in base_cmd:
            sub = rel_main.commands[step]
            assert isinstance(sub, click.Group)
            rel_main = sub
        metafunc.parametrize("args", traverse_commands(rel_main, base_cmd), ids=" ".join)


@pytest.fixture
def no_api(monkeypatch: pytest.MonkeyPatch) -> None:
    @property  # type: ignore
    def getter(self: t.Any) -> None:
        pytest.fail("Invalid access to 'PulpContext.api'.", pytrace=False)

    monkeypatch.setattr("pulp_glue.common.context.PulpContext.api", getter)


@pytest.mark.help_page(base_cmd=[])
def test_accessing_the_help_page_does_not_invoke_api(
    no_api: None,
    args: list[str],
) -> None:
    runner = CliRunner()
    result = runner.invoke(main, args + ["--help"], catch_exceptions=False)

    if result.exit_code == 2:
        assert (
            "not available in this context" in result.stdout
            or "not available in this context" in result.stderr
        )
    else:
        assert result.exit_code == 0
        assert result.stdout.startswith("Usage:") or result.stdout.startswith("DeprecationWarning:")


@pytest.mark.parametrize(
    "command,options",
    [
        pytest.param(
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
