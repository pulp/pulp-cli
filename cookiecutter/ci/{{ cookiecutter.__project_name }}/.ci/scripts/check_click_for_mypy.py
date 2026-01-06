#!/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "packaging>=25.0,<25.1",
# ]
# ///

from importlib import metadata

from packaging.version import Version

if __name__ == "__main__":
    click_version = Version(metadata.version("click"))
    if click_version < Version("8.1.1"):
        print("🚧 Linting with mypy is currently only supported with click>=8.1.1. 🚧")
        print("🔧 Please run `pip install click>=8.1.1` first. 🔨")
        exit(1)
