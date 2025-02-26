#!/bin/env python3

import tomllib
from pathlib import Path

from packaging.requirements import Requirement

if __name__ == "__main__":
    base_path = Path(__file__).parent.parent.parent
    glue_path = "pulp-glue{{ cookiecutter.__app_label_suffix }}"
    with (base_path / "pyproject.toml").open("rb") as fp:
        cli_pyproject = tomllib.load(fp)

    cli_dependency = next(
        (
            Requirement(r)
            for r in cli_pyproject["project"]["dependencies"]
            if r.startswith("pulp-cli")
        )
    )

    with (base_path / glue_path / "pyproject.toml").open("rb") as fp:
        glue_pyproject = tomllib.load(fp)

    glue_dependency = next(
        (
            Requirement(r)
            for r in glue_pyproject["project"]["dependencies"]
            if r.startswith("pulp-glue")
        )
    )

    if cli_dependency.specifier != glue_dependency.specifier:
        print("🪢 CLI and GLUE dependencies mismatch:")
        print(" ", cli_dependency)
        print(" ", glue_dependency)
        exit(1)
