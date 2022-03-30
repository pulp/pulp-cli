#!/bin/env python3

import sys

import click

if click.__version__.split(".")[0:2] != ["8", "0"]:
    print("🚧 Linting with mypy is currently only supported with click~=8.0.0. 🚧")
    print("🔧 Please run `pip install click~=8.0.0` first. 🔨")
    sys.exit(1)
