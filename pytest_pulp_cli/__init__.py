# type: ignore

import os
import pathlib
import subprocess

import gnupg
import pytest
import requests
import toml


def pytest_collect_file(file_path, parent):
    if file_path.suffix == ".sh" and file_path.name.startswith("test_"):
        return ScriptFile.from_parent(parent, path=file_path)


class ScriptFile(pytest.File):
    # To make pytest.Function happy
    obj = None

    def collect(self):
        # Extract the name between "test_" and ".sh".
        name = self.path.name[5:][:-3]
        yield ScriptItem.from_parent(self, name=name, path=self.path)


# HACK: Inherit from `pytest.Function` to be able to use the fixtures
class ScriptItem(pytest.Function):
    def __init__(self, path, **kwargs):
        super().__init__(callobj=self._runscript, **kwargs)
        self.path = path
        self.add_marker("script")
        if path.parts[-3] == "scripts":
            self.add_marker(path.parts[-2])

    def _runscript(self, pulp_cli_env, tmp_path, pulp_container_log):
        run = subprocess.run([self.path], cwd=tmp_path)
        if run.returncode == 23:
            pytest.skip("Skipped as requested by the script.")
        if run.returncode != 0:
            raise ScriptError(f"Script returned with exit code {run.returncode}.")

    def reportinfo(self):
        return self.path, 0, f"test script: {self.name}"

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
    settings = toml.load("tests/cli.toml")
    if os.environ.get("PULP_API_ROOT"):
        for key in settings:
            settings[key]["api_root"] = os.environ["PULP_API_ROOT"]
    settings_path = tmp_path_factory.mktemp("config", numbered=False)
    (settings_path / "pulp").mkdir(parents=True)
    with open(settings_path / "pulp" / "cli.toml", "w") as settings_file:
        toml.dump(settings, settings_file)
    yield settings_path, settings


@pytest.fixture(scope="session")
def pulp_cli_gnupghome(tmp_path_factory):
    """
    This fixture will setup a GPG home directory once per session only.
    """
    gnupghome = tmp_path_factory.mktemp("gnupghome")
    gpg = gnupg.GPG(gnupghome=str(gnupghome))

    key_file = pathlib.Path(__file__).parent / "GPG-PRIVATE-KEY-pulp-qe"
    if key_file.exists():
        private_key_data = key_file.read_text()
    else:
        private_key_url = (
            "https://github.com/pulp/pulp-fixtures/raw/master/common/GPG-PRIVATE-KEY-pulp-qe"
        )
        private_key_data = requests.get(private_key_url).text
        key_file.write_text(private_key_data)

    import_result = gpg.import_keys(private_key_data)
    gpg.trust_keys(import_result.fingerprints[0], "TRUST_ULTIMATE")
    return gnupghome


@pytest.fixture
def pulp_cli_env(pulp_cli_settings, pulp_cli_vars, pulp_cli_gnupghome, monkeypatch):
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
    monkeypatch.setenv("GNUPGHOME", str(pulp_cli_gnupghome))

    for key, value in pulp_cli_vars.items():
        monkeypatch.setenv(key, value)

    yield settings


if "PULP_LOGGING" in os.environ:

    @pytest.fixture(scope="session")
    def pulp_container_log_stream():
        with subprocess.Popen(
            [os.environ["PULP_LOGGING"], "logs", "-f", "--tail", "0", "pulp-ephemeral"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        ) as proc:
            os.set_blocking(proc.stdout.fileno(), False)
            yield proc.stdout
            proc.kill()

    @pytest.fixture
    def pulp_container_log(pulp_container_log_stream):
        # Flush logs before starting the test
        pulp_container_log_stream.read()
        yield
        logs = pulp_container_log_stream.read()
        if logs is not None:
            print(logs.decode())

else:

    @pytest.fixture
    def pulp_container_log():
        yield
