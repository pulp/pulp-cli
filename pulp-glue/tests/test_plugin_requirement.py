import pytest

from pulp_glue.common.context import PluginRequirement, PulpContext
from pulp_glue.common.exceptions import PulpException

pytestmark = pytest.mark.glue


def test_has_plugin(mock_pulp_ctx: PulpContext) -> None:
    assert mock_pulp_ctx.has_plugin(PluginRequirement("core"))
    assert mock_pulp_ctx.has_plugin(PluginRequirement("core", specifier=">=3.50"))
    assert not mock_pulp_ctx.has_plugin(PluginRequirement("core", specifier=">=3.50,<3.60"))
    assert not mock_pulp_ctx.has_plugin(PluginRequirement("core", specifier=">=3.50,<3.60"))
    assert mock_pulp_ctx.has_plugin(
        PluginRequirement("core", specifier=">=3.50,<3.60", inverted=True)
    )

    assert not mock_pulp_ctx.has_plugin(PluginRequirement("elephant"))
    assert not mock_pulp_ctx.has_plugin(PluginRequirement("elephant", specifier=">=0.0.0"))
    assert mock_pulp_ctx.has_plugin(
        PluginRequirement("elephant", specifier=">=0.0.0", inverted=True)
    )


def test_needs_plugin(mock_pulp_ctx: PulpContext) -> None:
    mock_pulp_ctx.needs_plugin(PluginRequirement("core"))
    mock_pulp_ctx.needs_plugin(PluginRequirement("elephant", feature="zoo"))
    with pytest.raises(PulpException, match=r"elephant.*zoo"):
        mock_pulp_ctx.has_plugin(PluginRequirement("core"))
