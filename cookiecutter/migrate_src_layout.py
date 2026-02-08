#!/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pyyaml>=6.0.3,<6.1",
#     "tomlkit>=0.13.3,<0.14",
# ]
# ///


import typing as t
import sys
from pathlib import Path

import tomlkit


def main() -> None:
    pyproject_file = Path("pyproject.toml")
    try:
        pyproject_toml: t.Any = tomlkit.loads(pyproject_file.read_text())
        config = pyproject_toml["tool"]["pulp_cli_template"]
    except (FileNotFoundError, KeyError):
        raise RuntimeError("This does not look like a pulp cli repository.")

    if config.get("src_layout") is True:
        print("Apparently this repository has been migrated already.")
        sys.exit()

    if config["glue"] is True:
        if config["app_label"] == "":
            glue_dir = Path("pulp-glue")
        else:
            glue_dir = Path("pulp-glue-" + config["app_label"])
        assert glue_dir.is_dir()
        print("Moving glue parts.")
        glue_src_dir = glue_dir / "src"
        glue_src_dir.mkdir(exist_ok=True)
        glue_namespace_dir = glue_dir / "pulp_glue"
        glue_namespace_dir.rename(glue_src_dir / "pulp_glue")

    print("Moving cli parts to src.")
    cli_src_dir = Path("src")
    cli_src_dir.mkdir(exist_ok=True)

    cli_namespace_dir = Path("pulpcore")
    cli_namespace_dir.rename(cli_src_dir / "pulpcore")

    if config["app_label"] == "":
        cli_base_dir = Path("pulp_cli")
        cli_base_dir.rename(cli_src_dir / "pulp_cli")
        pytest_plugin_dir = Path("pytest_pulp_cli")
        pytest_plugin_dir.rename(cli_src_dir / "pytest_pulp_cli")

    config["src_layout"] = True
    pyproject_file.write_text(tomlkit.dumps(pyproject_toml))
    print("Please reapply the cookiecutter ci templates now.")


if __name__ == "__main__":
    main()
