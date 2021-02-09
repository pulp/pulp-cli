import os

import pytest
import toml

# Constants used in tests
PULP_FIXTURES_URL = os.environ.get("PULP_FIXTURES_URL", "https://fixtures.pulpproject.org")

ENV_CONSTANTS = {
    "PULP_FIXTURES_URL": PULP_FIXTURES_URL,
    "FILE_REMOTE_URL": PULP_FIXTURES_URL + "/file/PULP_MANIFEST",
    "CONTAINER_REMOTE_URL": "https://registry-1.docker.io",
    "CONTAINER_IMAGE": "hello-world",
    "RPM_REMOTE_URL": PULP_FIXTURES_URL + "/rpm-unsigned",
    "ANSIBLE_COLLECTION_REMOTE_URL": "https://galaxy.ansible.com/",
    "ANSIBLE_ROLE_REMOTE_URL": "https://galaxy.ansible.com/api/v1/roles/?namespace__name=elastic",
}


@pytest.fixture
def cli_env(tmp_path, monkeypatch):
    """
    This fixture will set up the environment for cli commands by:

    * creating a tmp_dir
    * placing the config there
    * pointing XDG_CONFIG_HOME accordingly
    * supplying other useful environment vars
    """
    settings = toml.load("tests/settings.toml")
    settings_path = tmp_path / "config" / "pulp"
    settings_path.mkdir(parents=True)
    with open(settings_path / "settings.toml", "w") as settings_file:
        toml.dump(settings, settings_file)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("PULP_BASE_URL", settings["cli"]["base_url"])
    monkeypatch.setenv("VERIFY_SSL", str(settings["cli"].get("verify_ssl", True)).lower())

    for key, value in ENV_CONSTANTS.items():
        monkeypatch.setenv(key, value)

    yield settings
