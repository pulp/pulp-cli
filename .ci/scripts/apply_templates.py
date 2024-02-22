from pathlib import Path
import sys

import toml
from cookiecutter.main import cookiecutter

if __name__ == "__main__":
    sections = []
    output_dir = ".."

    if len(sys.argv) == 2:
        config = {
            "app_label": sys.argv[1],
            "glue": True,
            "docs": False,
            "translations": False,
        }
        sections.append("bootstrap")
        output_dir = "."
    else:
        with open("pyproject.toml") as fp:
            config = toml.load(fp)["tool"]["pulp_cli_template"]

    sections.append("ci")

    if config["docs"]:
        sections.append("docs")

    cutter_path = Path(__file__).parent.parent.parent / "cookiecutter"

    for section in sections:
        bootstrap = section == "bootstrap"
        print(f"Apply {section} template")
        cookiecutter(
            str(cutter_path / section),
            no_input=not bootstrap,
            extra_context=config,
            overwrite_if_exists=not bootstrap,
            output_dir=output_dir,
        )
