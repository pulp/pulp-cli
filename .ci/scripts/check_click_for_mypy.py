#!/bin/env python3

from importlib.metadata import version

from packaging.version import parse

click_version = version("click")

if parse(click_version) < parse("8.1.1") or parse(click_version) >= parse("8.2"):
    print("🚧 Linting with mypy is currently only supported with click~=8.1.1. 🚧")
    print("🔧 Please run `pip install click~=8.1.1` first. 🔨")
    exit(1)
