from pathlib import Path

import toml
from cookiecutter.main import cookiecutter

if __name__ == "__main__":
    sections = []
    overwrite = True

    with open("pyproject.toml") as fp:
        config = toml.load(fp)["tool"]["pulp_cli_template"]

    sections.append("ci")

    if config["docs"]:
        sections.append("docs")

    cutter_path = Path(__file__).parent.parent.parent / "cookiecutter"

    for section in sections:
        print(f"Apply {section} template")
        cookiecutter(
            str(cutter_path / section),
            no_input=True,
            extra_context=config,
            overwrite_if_exists=overwrite,
            output_dir="..",
        )
