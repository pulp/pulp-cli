import typing as t
from copy import deepcopy

import pytest
from pulp_glue.common.context import PulpContext


@pytest.mark.glue
def test_api_quirks_idempotent(
    pulp_cli_settings: t.Tuple[t.Any, t.Dict[str, t.Dict[str, t.Any]]]
) -> None:
    """
    Test, that the applied api quirks can be applied twice without failing.

    This can let us hope they will not fail once the api is fixed upstream.
    """
    settings = pulp_cli_settings[1]["cli"]
    pulp_ctx = PulpContext(
        api_kwargs={"base_url": settings["base_url"]},
        api_root=settings.get("api_root", "pulp/"),
        background_tasks=False,
        timeout=settings.get("timeout", 120),
    )
    patched_once_api = deepcopy(pulp_ctx.api.api_spec)
    # Patch a second time
    pulp_ctx._patch_api_spec()
    assert pulp_ctx.api.api_spec == patched_once_api
