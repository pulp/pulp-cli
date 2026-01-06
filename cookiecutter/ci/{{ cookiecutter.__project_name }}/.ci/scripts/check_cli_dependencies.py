#!/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "packaging>=25.0,<25.1",
# ]
# ///

import typing as t
from pathlib import Path

import tomllib
from packaging.requirements import Requirement

GLUE_DIR = "pulp-glue{{ cookiecutter.__app_label_suffix }}"


def dependencies(path: Path) -> t.Iterator[Requirement]:
    with (path / "pyproject.toml").open("rb") as fp:
        pyproject = tomllib.load(fp)

    return (Requirement(r) for r in pyproject["project"]["dependencies"])


if __name__ == "__main__":
    base_path = Path(__file__).parent.parent.parent
    glue_path = base_path / GLUE_DIR

    cli_dependency = next((r for r in dependencies(base_path) if r.name == "pulp-cli"))
    glue_dependency = next((r for r in dependencies(glue_path) if r.name == "pulp-glue"))

    if cli_dependency.specifier != glue_dependency.specifier:
        print("🪢 CLI and GLUE dependencies mismatch:")
        print(" ", cli_dependency)
        print(" ", glue_dependency)
        exit(1)
