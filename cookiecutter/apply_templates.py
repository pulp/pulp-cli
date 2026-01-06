#!/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "click>=8.3.1,<8.4",
#     "cookiecutter>=2.6.0,<2.7",
#     "pyyaml>=6.0.3,<6.1",
#     "tomlkit>=0.13.3,<0.14",
# ]
# ///


import os
from pathlib import Path
import tomllib

import click
import yaml

from cookiecutter.main import cookiecutter


@click.option("--bootstrap/--no-bootstrap")
@click.option("--force/--no-force")
@click.command()
def main(bootstrap: bool, force: bool) -> None:
    cutter_path = Path(__file__).parent

    if bootstrap:
        print("Bootstrap new CLI plugin.")
        proj_dir = cookiecutter(
            str(cutter_path / "bootstrap"),
            no_input=False,
            overwrite_if_exists=force,
            output_dir=".",
        )
        print(f"New plugin repository created in {proj_dir}.")
        os.chdir(proj_dir)

    try:
        with open("pyproject.toml", "rb") as fp:
            pyproject_toml = tomllib.load(fp)
        config = pyproject_toml["tool"]["pulp_cli_template"]
    except (FileNotFoundError, KeyError):
        raise click.ClickException("This does not look like a pulp cli repository.")

    config.setdefault("main_package", config["app_label"])
    config["current_version"] = pyproject_toml["project"]["version"]

    sections = []

    # Select cookiecutter sections to apply.
    # CI
    sections.append("ci")
    with open(".github/workflows/test.yml") as fp:
        config["test_matrix"] = yaml.safe_load(fp)["jobs"]["test"]["strategy"]["matrix"]

    # Docs
    if config["docs"]:
        sections.append("docs")

    # Update with selected sections.
    for section in sections:
        print(f"Apply {section} template")
        cookiecutter(
            str(cutter_path / section),
            no_input=True,
            extra_context=config,
            overwrite_if_exists=True,
            output_dir="..",
        )


if __name__ == "__main__":
    main()
