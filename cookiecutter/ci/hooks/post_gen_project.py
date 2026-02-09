import os
import shutil
import sys

import tomlkit

for base_path in [
    ".",
    "pulp-glue{{ cookiecutter.__app_label_suffix }}",
]:
    # Merge pyproject.toml.update into pyproject.toml
    with open(os.path.join(base_path, "pyproject.toml"), "r") as fp:
        pyproject_toml = tomlkit.load(fp)

    with open(os.path.join(base_path, "pyproject.toml.update"), "r") as fp:
        pyproject_toml_update = tomlkit.load(fp)

    # TODO How deep is your merge?
    # Is merging on the tool level appropriate?
    pyproject_toml["tool"].update(pyproject_toml_update["tool"])

    if "dependency-groups" in pyproject_toml_update:
        if "dependency-groups" not in pyproject_toml:
            pyproject_toml["dependency-groups"]=pyproject_toml_update["dependency-groups"]
        else:
            pyproject_toml["dependency-groups"].update(pyproject_toml_update["dependency-groups"])

    # Remove legacy tools.
    for tool in ["flake8", "black", "isort"]:
        pyproject_toml["tool"].pop(tool, None)

    with open(os.path.join(base_path, "pyproject.toml"), "w") as fp:
        tomlkit.dump(pyproject_toml, fp)

# Remove unwanted files

REMOVE_PATHS = [
    "pyproject.toml.update",
    ".bumpversion.cfg",
    ".flake8",
    {%- if not cookiecutter.glue %}
    "pulp-glue{{ cookiecutter.__app_label_suffix }}",
    "CHANGES/pulp-glue{{ cookiecutter.__app_label_suffix }}",
    {%- else %}
    "pulp-glue{{ cookiecutter.__app_label_suffix }}/pyproject.toml.update",
    {%- endif %}
    {%- if not cookiecutter.app_label or not cookiecutter.glue %}
    ".ci/scripts/check_cli_dependencies.py",
    {%- endif %}
    {%- if cookiecutter.app_label %}
    ".github/dependabot.yml",
    {%- endif %}
]

for path in REMOVE_PATHS:
    path = path.strip()
    if path and os.path.exists(path):
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.unlink(path)
