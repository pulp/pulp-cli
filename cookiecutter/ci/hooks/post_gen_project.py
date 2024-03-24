# flake8: noqa

import os
import shutil
import sys

import tomlkit

# Merge pyproject.toml.update into pyproject.toml
with open("pyproject.toml", "r") as fp:
    pyproject_toml = tomlkit.load(fp)

with open("pyproject.toml.update", "r") as fp:
    pyproject_toml_update = tomlkit.load(fp)

# TODO How deep is your merge?
# Is merging on the tool level appropriate?
pyproject_toml["tool"].update(pyproject_toml_update["tool"])

with open("pyproject.toml", "w") as fp:
    tomlkit.dump(pyproject_toml, fp)

# Remove unwanted files

REMOVE_PATHS = [
    "pyproject.toml.update",
    ".bumpversion.cfg",
    {% if not cookiecutter.glue -%}
    "pulp-glue{{ cookiecutter.__app_label_suffix }}",
    "CHANGES/pulp-glue{{ cookiecutter.__app_label_suffix }}",
    {%- endif %}
]

for path in REMOVE_PATHS:
    path = path.strip()
    if path and os.path.exists(path):
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.unlink(path)
