import os
import subprocess

import pytest
import toml


def pytest_collect_file(parent, path):
    if path.ext == ".sh" and path.purebasename.startswith("test_"):
        return ScriptFile.from_parent(parent, fspath=path)


class ScriptFile(pytest.File):
    # To make pytest.Function happy
    obj = None

    def collect(self):
        name = self.fspath.purebasename[5:]
        yield ScriptItem.from_parent(self, name=name, path=self.fspath)


# HACK: Inherit from `pytest.Function` to be able to use the fixtures
class ScriptItem(pytest.Function):
    def __init__(self, path, **kwargs):
        super().__init__(callobj=self._runscript, **kwargs)
        self.path = path
        self.add_marker("script")
        if path.parts()[-3].basename == "scripts":
            self.add_marker(path.parts()[-2].basename)

    def _runscript(self, pulp_cli_env, tmp_path):
        run = subprocess.run([self.path], cwd=tmp_path)
        if run.returncode == 3:
            pytest.skip("Skipped as requested by the script.")
        if run.returncode != 0:
            raise ScriptError(f"Script returned with exit code {run.returncode}.")

    def reportinfo(self):
        return self.fspath, 0, f"test script: {self.name}"

    def repr_failure(self, excinfo):
        if isinstance(excinfo.value, ScriptError):
            return str(excinfo.value)
        return super().repr_failure(excinfo)


class ScriptError(Exception):
    """Custom exception to mark script execution failure."""


@pytest.fixture
def pulp_cli_vars():
    """
    This fixture will return a dictionary that is used by `pulp_cli_env` to setup the environment.
    To inject more environment variables, it can overwritten.
    It will be initialized with "PULP_FIXTURE_URL".
    """
    PULP_FIXTURES_URL = os.environ.get("PULP_FIXTURES_URL", "https://fixtures.pulpproject.org")

    return {"PULP_FIXTURES_URL": PULP_FIXTURES_URL}


@pytest.fixture(scope="session")
def pulp_cli_settings(tmp_path_factory):
    """
    This fixture will setup the config file once per session only.
    It is most likely not useful to be included standalone.
    The `pulp_cli_env` fixture, however depends on it and sets $XDG_CONFIG_HOME up accordingly.
    """
    settings = toml.load("tests/settings.toml")
    settings_path = tmp_path_factory.mktemp("config", numbered=False)
    (settings_path / "pulp").mkdir(parents=True)
    with open(settings_path / "pulp" / "settings.toml", "w") as settings_file:
        toml.dump(settings, settings_file)
    yield settings_path, settings


@pytest.fixture
def pulp_cli_env(pulp_cli_settings, pulp_cli_vars, monkeypatch):
    """
    This fixture will set up the environment for cli commands by:

    * creating a tmp_dir
    * placing the config there
    * pointing XDG_CONFIG_HOME accordingly
    * supplying other useful environment vars
    """
    settings_path, settings = pulp_cli_settings
    monkeypatch.setenv("XDG_CONFIG_HOME", str(settings_path))
    monkeypatch.setenv("PULP_BASE_URL", settings["cli"]["base_url"])
    monkeypatch.setenv("VERIFY_SSL", str(settings["cli"].get("verify_ssl", True)).lower())

    for key, value in pulp_cli_vars.items():
        monkeypatch.setenv(key, value)

    yield settings
