import typing as t

import pytest

from pulp_glue.common.context import PulpContext
from pulp_glue.common.openapi import BasicAuthProvider


class PulpTestContext(PulpContext):
    # TODO check if we can just make the base class ignore echo.
    def echo(*args, **kwargs) -> None:
        return


@pytest.fixture
def pulp_ctx(
    request: pytest.FixtureRequest, pulp_cli_settings: t.Dict[str, t.Dict[str, t.Any]]
) -> PulpContext:
    verbose = request.config.getoption("verbose")
    settings = pulp_cli_settings["cli"]
    return PulpTestContext(
        api_kwargs={
            "base_url": settings["base_url"],
            "auth_provider": (
                BasicAuthProvider(settings.get("username"), settings.get("password"))
                if "username" in settings
                else None
            ),
            "cert": settings.get("cert"),
            "key": settings.get("key"),
            "debug_callback": lambda i, s: i <= verbose and print(s),
        },
        api_root=settings.get("api_root", "pulp/"),
        background_tasks=False,
        timeout=settings.get("timeout", 120),
    )


@pytest.fixture
def fake_pulp_ctx(
    request: pytest.FixtureRequest, pulp_cli_settings: t.Dict[str, t.Dict[str, t.Any]]
) -> PulpContext:
    verbose = request.config.getoption("verbose")
    settings = pulp_cli_settings["cli"]
    return PulpTestContext(
        api_kwargs={
            "base_url": settings["base_url"],
            "auth_provider": (
                BasicAuthProvider(settings.get("username"), settings.get("password"))
                if "username" in settings
                else None
            ),
            "cert": settings.get("cert"),
            "key": settings.get("key"),
            "debug_callback": lambda i, s: i <= verbose and print(s),
        },
        api_root=settings.get("api_root", "pulp/"),
        background_tasks=False,
        timeout=settings.get("timeout", 120),
        fake_mode=True,
    )
