import os
import pytest
import subprocess


TEST_NAMES = [
    name[5:-3]
    for name in os.listdir("tests/scripts")
    if name.startswith("test_") and name.endswith(".sh")
]


@pytest.mark.parametrize("test_name", TEST_NAMES)
def test_script(test_name):
    run = subprocess.run([os.path.join("tests", "scripts", "test_" + test_name + ".sh")])
    assert run.returncode == 0
