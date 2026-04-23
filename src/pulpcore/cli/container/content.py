import gettext
import typing as t

import click

from pulp_glue.common.context import PluginRequirement, PulpContentContext
from pulp_glue.container.context import (
    PulpContainerBlobContext,
    PulpContainerManifestContext,
    PulpContainerTagContext,
)

from pulp_cli.generic import (
    content_filter_options,
    href_option,
    label_command,
    list_command,
    option_group,
    pulp_group,
    pulp_option,
    show_command,
    type_option,
)

_ = gettext.gettext


def _content_callback(ctx: click.Context, value: dict[str, t.Any]) -> None:
    if value:
        entity_ctx = ctx.find_object(PulpContentContext)
        assert entity_ctx is not None
        if isinstance(entity_ctx, PulpContainerTagContext) and len(value) != 2:
            raise click.UsageError(_("Both 'name' and 'digest' are needed to describe a tag."))
        entity_ctx.entity = value


@pulp_group()
@type_option(
    choices={
        "blob": PulpContainerBlobContext,
        "manifest": PulpContainerManifestContext,
        "tag": PulpContainerTagContext,
    },
    default="tag",
)
def content() -> None:
    pass


list_options = [
    pulp_option(
        "--media-type",
        allowed_with_contexts=(PulpContainerManifestContext, PulpContainerTagContext),
    ),
    pulp_option("--name", "name", allowed_with_contexts=(PulpContainerTagContext,)),
    pulp_option(
        "--name-in",
        "name__in",
        multiple=True,
        allowed_with_contexts=(PulpContainerTagContext,),
    ),
    pulp_option(
        "--digest",
        allowed_with_contexts=(
            PulpContainerManifestContext,
            PulpContainerBlobContext,
            PulpContainerTagContext,
        ),
    ),
    pulp_option(
        "--digest-in",
        "digest__in",
        multiple=True,
        allowed_with_contexts=(PulpContainerManifestContext, PulpContainerBlobContext),
    ),
    pulp_option(
        "--is-bootable",
        is_flag=True,
        default=None,
        allowed_with_contexts=(PulpContainerManifestContext,),
    ),
    pulp_option(
        "--is-flatpak",
        is_flag=True,
        default=None,
        allowed_with_contexts=(PulpContainerManifestContext,),
    ),
    *content_filter_options,
]

lookup_options = [
    pulp_option(
        "--digest",
        help=_("Digest associated with {entity}"),
    ),
    pulp_option(
        "--name",
        help=_("Name of {entity}"),
        allowed_with_contexts=(PulpContainerTagContext,),
    ),
    href_option,
    option_group(
        "content",
        ["name", "digest"],
        callback=_content_callback,
        require_all=False,
        expose_value=False,
    ),
]

content.add_command(list_command(decorators=list_options))
content.add_command(show_command(decorators=lookup_options))
content.add_command(
    label_command(
        decorators=lookup_options,
        need_plugins=[PluginRequirement("core", specifier=">=3.73.2")],
    )
)
