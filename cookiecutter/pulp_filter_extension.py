import shlex
import typing as t

from jinja2 import Environment
from jinja2.ext import Extension


def _assert_key(key: t.Any) -> str:
    assert isinstance(key, str)
    assert key.isidentifier()
    return key


def _quote(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def to_toml_value(value: t.Any) -> str:
    if isinstance(value, str):
        return '"' + value + '"'
    elif value is True:
        return "true"
    elif value is False:
        return "false"
    elif isinstance(value, int):
        return str(value)
    else:
        raise NotImplementedError("Not an atomic value.")


def to_camel(name: str) -> str:
    return name.title().replace("_", "")


def to_dash(name: str) -> str:
    return name.replace("_", "-")


def to_snake(name: str) -> str:
    return name.replace("-", "_")


def to_hour(name: str) -> int:
    """
    Turn a string into a pseudorandom integer between 0 and 24.
    """
    return sum((i * ord(c) for i, c in enumerate(name))) % 24


class PulpFilterExtension(Extension):
    def __init__(self, environment: Environment):
        super().__init__(environment)
        environment.filters["camel"] = to_camel
        environment.filters["caps"] = str.upper
        environment.filters["dash"] = to_dash
        environment.filters["snake"] = to_snake
        environment.filters["toml_value"] = to_toml_value
        environment.filters["shquote"] = shlex.quote
        environment.filters["hour"] = to_hour
