import json
import os
import typing as t

import pytest

from pulp_glue.common.context import PulpContext
from pulp_glue.common.openapi import BasicAuthProvider, OpenAPI

FAKE_OPENAPI_SPEC = json.dumps(
    {
        "openapi": "3.0.3",
        "info": {"x-pulp-app-versions": {"core": "3.75.0"}},
        "paths": {},
    }
)


@pytest.fixture
def pulp_ctx(
    request: pytest.FixtureRequest, pulp_cli_settings: t.Dict[str, t.Dict[str, t.Any]]
) -> PulpContext:
    if not any((mark.name == "live" for mark in request.node.iter_markers())):
        pytest.fail("This fixture can only be used in live (integration) tests.")

    if os.environ.get("PULP_OAUTH2", "").lower() == "true":
        pytest.skip("Pulp-glue in isolation does not support OAuth2 atm.")
    verbose = request.config.getoption("verbose")
    settings = pulp_cli_settings["cli"].copy()
    settings["debug_callback"] = lambda i, s: i <= verbose and print(s)
    return PulpContext.from_config(settings)


@pytest.fixture
def mock_pulp_ctx(
    request: pytest.FixtureRequest,
    monkeypatch: pytest.MonkeyPatch,
) -> PulpContext:
    monkeypatch.setattr(
        OpenAPI, "load_api", lambda self, refresh_cache: self._parse_api(FAKE_OPENAPI_SPEC)
    )
    monkeypatch.setattr(
        OpenAPI,
        "_send_request",
        lambda *args, **kwags: pytest.fail("Invalid use of pulp_ctx fixture in a non live test."),
    )

    verbose = request.config.getoption("verbose")
    settings: t.Dict[str, t.Any] = {"base_url": "nowhere"}
    settings["debug_callback"] = lambda i, s: i <= verbose and print(s)
    return PulpContext.from_config(settings)


@pytest.fixture
def fake_pulp_ctx(
    request: pytest.FixtureRequest, pulp_cli_settings: t.Dict[str, t.Dict[str, t.Any]]
) -> PulpContext:
    if not any((mark.name == "live" for mark in request.node.iter_markers())):
        pytest.fail("This fixture can only be used in live (integration) tests.")

    if os.environ.get("PULP_OAUTH2", "").lower() == "true":
        pytest.skip("Pulp-glue in isolation does not support OAuth2 atm.")
    verbose = request.config.getoption("verbose")
    settings = pulp_cli_settings["cli"]
    if "username" in settings:
        username = settings.get("username")
        assert isinstance(username, str)
        password = settings.get("password")
        assert isinstance(password, str)
        auth_provider = BasicAuthProvider(username, password)
    else:
        auth_provider = None
    return PulpContext(
        api_kwargs={
            "base_url": settings["base_url"],
            "auth_provider": auth_provider,
            "cert": settings.get("cert"),
            "key": settings.get("key"),
            "debug_callback": lambda i, s: i <= verbose and print(s),
        },
        api_root=settings.get("api_root", "pulp/"),
        background_tasks=False,
        timeout=settings.get("timeout", 120),
        fake_mode=True,
    )
