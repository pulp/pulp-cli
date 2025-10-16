import typing as t
from urllib.parse import urljoin

import pytest

pytest_plugins = ("pytest_pulp_cli",)


@pytest.fixture
def pulp_cli_vars(pulp_cli_vars: t.Dict[str, str]) -> t.Dict[str, str]:
    PULP_FIXTURES_URL = pulp_cli_vars["PULP_FIXTURES_URL"]
    result = {}
    result.update(pulp_cli_vars)
    result.update(
        {
            "FILE_REMOTE_URL": urljoin(PULP_FIXTURES_URL, "/file/PULP_MANIFEST"),
            "FILE_REMOTE2_URL": urljoin(PULP_FIXTURES_URL, "/file2/PULP_MANIFEST"),
            "FILE_LARGE_REMOTE_URL": urljoin(PULP_FIXTURES_URL, "/file-perf/PULP_MANIFEST"),
            "CONTAINER_REMOTE_URL": "https://quay.io",
            "CONTAINER_IMAGE": "libpod/alpine",
            "RPM_REMOTE_URL": urljoin(PULP_FIXTURES_URL, "/rpm-unsigned"),
            "RPM_WEAK_DEPS_URL": urljoin(PULP_FIXTURES_URL, "/rpm-richnweak-deps"),
            "RPM_MODULES_REMOTE_URL": urljoin(PULP_FIXTURES_URL, "/rpm-with-modules"),
            "ANSIBLE_COLLECTION_REMOTE_URL": "https://galaxy.ansible.com/",
            "ANSIBLE_ROLE_REMOTE_URL": "https://galaxy.ansible.com/api/v1/roles/?owner__username=elastic",  # noqa
            "PYTHON_REMOTE_URL": PULP_FIXTURES_URL + "/python-pypi/",
            "ULN_REMOTE_URL": "uln://ovm2_2.1.1_i386_patch",
        }
    )
    return result
