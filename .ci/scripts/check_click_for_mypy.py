#!/bin/env python3

import sys

import click
from packaging.version import parse

if parse(click.__version__) < parse("8.1.1") or parse(click.__version__) >= parse("8.2"):
    print("🚧 Linting with mypy is currently only supported with click~=8.1.1. 🚧")
    print("🔧 Please run `pip install click~=8.1.1` first. 🔨")
    sys.exit(1)
