import os
import sys
import shutil

REMOVE_PATHS = [
    {% if not cookiecutter.glue -%} "pulp-glue{{ cookiecutter.__app_label_suffix }}", {%- endif %}
]

for path in REMOVE_PATHS:
    path = path.strip()
    if path and os.path.exists(path):
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.unlink(path)
