#!/bin/env python3

import tomllib
from pathlib import Path

import yaml

from cookiecutter.main import cookiecutter

if __name__ == "__main__":
    sections = []
    overwrite = True

    with open("pyproject.toml", "rb") as fp:
        pyproject_toml = tomllib.load(fp)

    config = pyproject_toml["tool"]["pulp_cli_template"]
    config.setdefault("main_package", config["app_label"])

    # CI
    sections.append("ci")
    config["current_version"] = pyproject_toml["project"]["version"]
    with open(".github/workflows/test.yml") as fp:
        config["test_matrix"] = yaml.safe_load(fp)["jobs"]["test"]["strategy"]["matrix"]

    # Docs
    if config["docs"]:
        sections.append("docs")

    cutter_path = Path(__file__).parent

    for section in sections:
        print(f"Apply {section} template")
        cookiecutter(
            str(cutter_path / section),
            no_input=True,
            extra_context=config,
            overwrite_if_exists=overwrite,
            output_dir="..",
        )
