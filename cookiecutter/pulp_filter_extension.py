import shlex
import typing as t

from jinja2 import Environment
from jinja2.ext import Extension


def _assert_key(key: t.Any) -> str:
    assert isinstance(key, str)
    assert key.isidentifier()
    return key


def to_nice_yaml(data: t.Any, level: int = 0, embed_in: str = "") -> str:
    """Filter for Jinja 2 templates to render human readable YAML."""
    # Don't even believe this is complete!
    # Yes, I have checked pyyaml and ruamel.
    # Should I call this markup language "jaml" or "yson"?

    nl = False
    if isinstance(data, str):
        result = f'"{data}"'
    elif data is True:
        result = "true"
    elif data is False:
        result = "false"
    elif isinstance(data, int):
        result = f"{data}"
    elif isinstance(data, list):
        if len(data):
            nl = embed_in == "dict"
            result = ("\n" + "  " * level).join(
                ("-" + to_nice_yaml(item, level + 1, "list") for item in data)
            )
        else:
            result = "[]"
    elif isinstance(data, dict):
        if len(data):
            nl = embed_in == "dict"
            result = ("\n" + "  " * level).join(
                (
                    f"{_assert_key(key)}:" + to_nice_yaml(value, level + 1, "dict")
                    for key, value in sorted(data.items())
                )
            )
        else:
            result = "{}"
    else:
        raise NotImplementedError("YAML sucks!")
    if nl:
        return "\n" + "  " * level + result
    elif embed_in:
        return " " + result
    else:
        return result


def to_camel(name: str) -> str:
    return name.title().replace("_", "")


def to_dash(name: str) -> str:
    return name.replace("_", "-")


def to_snake(name: str) -> str:
    return name.replace("-", "_")


class PulpFilterExtension(Extension):
    def __init__(self, environment: Environment):
        super().__init__(environment)
        environment.filters["camel"] = to_camel
        environment.filters["caps"] = str.upper
        environment.filters["dash"] = to_dash
        environment.filters["snake"] = to_snake
        environment.filters["to_nice_yaml"] = to_nice_yaml
        environment.filters["shquote"] = shlex.quote


try:
    import pytest
except ImportError:
    pass
else:

    @pytest.mark.parametrize(
        "value,level,embed_in,out",
        [
            ([], 0, "", "[]"),
            ({}, 0, "", "{}"),
            ("test", 0, "", '"test"'),
            ({}, 1, "dict", " {}"),
            ([], 1, "list", " []"),
            ({}, 1, "list", " {}"),
            ([], 1, "dict", " []"),
            ([{}], 0, "", "- {}"),
            ([[[]]], 0, "", "- - []"),
            (
                {"a": [], "b": "test", "c": [True, False]},
                2,
                "list",
                """ a: []
    b: "test"
    c:
      - true
      - false""",
            ),
            ({"b": 1, "a": 0}, 0, "", "a: 0\nb: 1"),
        ],
    )
    def test_to_nice_yaml(value, level, embed_in, out):
        assert to_nice_yaml(value, level, embed_in) == out
