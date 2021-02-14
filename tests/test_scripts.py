import subprocess
from pathlib import Path

import pytest

TEST_SCRIPTS = [
    pytest.param(
        path.resolve(),
        id=("" if path.parent.name == "scripts" else path.parent.name + ".") + path.stem,
        marks=[] if path.parent.name == "scripts" else getattr(pytest.mark, path.parent.name),
    )
    for path in Path("tests/scripts").glob("**/test_*.sh")
]


@pytest.mark.script
@pytest.mark.parametrize("script", TEST_SCRIPTS)
def test_script(script, pulp_cli_env, tmp_path):
    run = subprocess.run([script], cwd=tmp_path)
    if run.returncode == 3:
        pytest.skip("Skipped as requested by the script.")
    assert run.returncode == 0
