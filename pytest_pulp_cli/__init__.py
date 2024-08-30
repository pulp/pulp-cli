import os
import pathlib
import subprocess
import typing as t

import gnupg
import pytest
import requests
import toml

if t.TYPE_CHECKING:
    from _pytest._code.code import ExceptionInfo, TerminalRepr


def pytest_collect_file(
    file_path: pathlib.Path, parent: pytest.Collector
) -> t.Optional[pytest.Collector]:
    if file_path.suffix == ".sh" and file_path.name.startswith("test_"):
        return ScriptFile.from_parent(parent, path=file_path)
    return None


class ScriptFile(pytest.File):
    # To make pytest.Function happy
    obj = None

    def collect(self) -> t.Iterable[t.Union[pytest.Item, pytest.Collector]]:
        # Extract the name between "test_" and ".sh".
        name = self.path.name[5:][:-3]
        yield ScriptItem.from_parent(self, name=name, path=self.path)


# HACK: Inherit from `pytest.Function` to be able to use the fixtures
class ScriptItem(pytest.Function):
    def __init__(self, path: pathlib.Path, **kwargs: t.Any):
        super().__init__(callobj=self._runscript, **kwargs)
        self.path = path
        self.add_marker("script")
        if path.parts[-3] == "scripts":
            self.add_marker(path.parts[-2])

    def _runscript(
        self, pulp_cli_env: t.Dict[str, t.Any], tmp_path: pathlib.Path, pulp_container_log: None
    ) -> None:
        run = subprocess.run([self.path], cwd=tmp_path)
        if run.returncode == 23:
            pytest.skip("Skipped as requested by the script.")
        if run.returncode != 0:
            raise ScriptError(f"Script returned with exit code {run.returncode}.")

    def reportinfo(self) -> t.Tuple[pathlib.Path, int, str]:
        return self.path, 0, f"test script: {self.name}"

    def repr_failure(
        self,
        excinfo: "ExceptionInfo[BaseException]",
        # older versions of python do not have typing.Literal ...
        style: t.Optional[
            't.Literal["long", "short", "line", "no", "native", "value", "auto"]'
        ] = None,
    ) -> t.Union[str, "TerminalRepr"]:
        if isinstance(excinfo.value, ScriptError):
            return str(excinfo.value)
        # Weird, that the subclass Function does not like the parameter "style".
        return super().repr_failure(excinfo)


class ScriptError(Exception):
    """Custom exception to mark script execution failure."""


@pytest.fixture
def pulp_cli_vars() -> t.Dict[str, str]:
    """
    This fixture will return a dictionary that is used by `pulp_cli_env` to setup the environment.
    To inject more environment variables, it can overwritten.
    It will be initialized with "PULP_FIXTURE_URL".
    """
    PULP_FIXTURES_URL = os.environ.get("PULP_FIXTURES_URL", "https://fixtures.pulpproject.org")

    return {"PULP_FIXTURES_URL": PULP_FIXTURES_URL}


@pytest.fixture(scope="session")
def pulp_cli_settings() -> t.Dict[str, t.Dict[str, t.Any]]:
    """
    This fixture will setup the config file once per session only.
    It is most likely not useful to be included standalone.
    The `pulp_cli_env` fixture, however depends on it and sets $XDG_CONFIG_HOME up accordingly.
    """
    pulp_cli_test_tmpdir = pathlib.Path(os.environ.get("PULP_CLI_TEST_TMPDIR", "."))
    settings = {"cli": toml.load(os.environ.get("PULP_CLI_CONFIG", "tests/cli.toml"))["cli"]}
    if os.environ.get("PULP_HTTPS"):
        settings["cli"]["base_url"] = settings["cli"]["base_url"].replace("http://", "https://")
        client_cert_path = pulp_cli_test_tmpdir / "settings" / "certs" / "client.pem"
        client_key_path = pulp_cli_test_tmpdir / "settings" / "certs" / "client.key"
        if client_cert_path.exists():
            settings["cli"].pop("username", None)
            settings["cli"].pop("password", None)
            settings["cli"]["cert"] = str(client_cert_path)
            if client_key_path.exists():
                settings["cli"]["key"] = str(client_key_path)

    if os.environ.get("PULP_API_ROOT"):
        settings["cli"]["api_root"] = os.environ["PULP_API_ROOT"]

    settings["cli-noauth"] = {
        k: v for k, v in settings["cli"].items() if k not in {"username", "password", "cert", "key"}
    }
    return settings


@pytest.fixture(scope="session")
def pulp_cli_settings_path(
    tmp_path_factory: pytest.TempPathFactory, pulp_cli_settings: t.Dict[str, t.Dict[str, t.Any]]
) -> pathlib.Path:
    settings_path = tmp_path_factory.mktemp("config", numbered=False)
    (settings_path / "pulp").mkdir(parents=True)
    with open(settings_path / "pulp" / "cli.toml", "w") as settings_file:
        toml.dump(pulp_cli_settings, settings_file)
    return settings_path


@pytest.fixture(scope="session")
def pulp_cli_gnupghome(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    """
    This fixture will setup a GPG home directory once per session only.
    """
    gnupghome = tmp_path_factory.mktemp("gnupghome")
    gpg = gnupg.GPG(gnupghome=str(gnupghome))

    key_file = pathlib.Path(__file__).parent / "GPG-PRIVATE-KEY-fixture-signing"
    if key_file.exists():
        private_key_data = key_file.read_text()
    else:
        private_key_url = "https://github.com/pulp/pulp-fixtures/raw/master/common/GPG-PRIVATE-KEY-fixture-signing"  # noqa: E501
        private_key_data = requests.get(private_key_url).text
        key_file.write_text(private_key_data)

    import_result = gpg.import_keys(private_key_data)
    gpg.trust_keys(import_result.fingerprints[0], "TRUST_ULTIMATE")
    return gnupghome


@pytest.fixture
def pulp_cli_env(
    pulp_cli_settings: t.Dict[str, t.Dict[str, t.Any]],
    pulp_cli_settings_path: pathlib.Path,
    pulp_cli_vars: t.Dict[str, str],
    pulp_cli_gnupghome: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    This fixture will set up the environment for cli commands by:

    * creating a tmp_dir
    * placing the config there
    * pointing XDG_CONFIG_HOME accordingly
    * supplying other useful environment vars
    """
    monkeypatch.setenv("XDG_CONFIG_HOME", str(pulp_cli_settings_path))
    monkeypatch.setenv("PULP_BASE_URL", pulp_cli_settings["cli"]["base_url"])
    monkeypatch.setenv("VERIFY_SSL", str(pulp_cli_settings["cli"].get("verify_ssl", True)).lower())
    monkeypatch.setenv("GNUPGHOME", str(pulp_cli_gnupghome))

    for key, value in pulp_cli_vars.items():
        monkeypatch.setenv(key, value)

    return None


if "PULP_LOGGING" in os.environ:

    @pytest.fixture(scope="session")
    def pulp_container_log_stream() -> t.Iterator[t.IO[bytes]]:
        with subprocess.Popen(
            [os.environ["PULP_LOGGING"], "logs", "-f", "--tail", "0", "pulp-ephemeral"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        ) as proc:
            assert proc.stdout is not None
            os.set_blocking(proc.stdout.fileno(), False)
            yield proc.stdout
            proc.kill()

    @pytest.fixture
    def pulp_container_log(pulp_container_log_stream: t.IO[bytes]) -> t.Iterator[None]:
        # Flush logs before starting the test
        pulp_container_log_stream.read()
        yield
        logs = pulp_container_log_stream.read()
        if logs is not None:
            print(logs.decode())

else:

    @pytest.fixture
    def pulp_container_log() -> t.Iterator[None]:
        yield
