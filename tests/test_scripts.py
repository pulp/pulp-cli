import os
import subprocess

import pytest

TEST_NAMES = [
    name[5:-3]
    for name in os.listdir("tests/scripts")
    if name.startswith("test_") and name.endswith(".sh")
]


@pytest.mark.parametrize("test_name", TEST_NAMES)
def test_script(test_name, cli_env, tmp_path):
    run = subprocess.run(
        [os.path.realpath(os.path.join("tests", "scripts", "test_" + test_name + ".sh"))],
        cwd=tmp_path,
    )
    if run.returncode == 3:
        pytest.skip("Skipped as requested by the script.")
    assert run.returncode == 0
