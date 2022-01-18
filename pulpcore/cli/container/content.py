import gettext
from typing import Any

import click

from pulpcore.cli.common.context import PulpContext, PulpEntityContext, pass_pulp_context
from pulpcore.cli.common.generic import (
    GroupOption,
    href_option,
    list_command,
    pulp_group,
    pulp_option,
    show_command,
)
from pulpcore.cli.container.context import (
    PulpContainerBlobContext,
    PulpContainerManifestContext,
    PulpContainerTagContext,
)

_ = gettext.gettext


def _content_callback(ctx: click.Context, param: click.Parameter, value: Any) -> None:
    if value is not None:
        entity_ctx = ctx.find_object(PulpEntityContext)
        assert entity_ctx is not None
        if isinstance(entity_ctx, PulpContainerTagContext):
            entity_ctx.entity = value
        else:
            entity_ctx.entity = {"digest": value}


@pulp_group()
@click.option(
    "-t",
    "--type",
    "content_type",
    type=click.Choice(["blob", "manifest", "tag"], case_sensitive=False),
    default="tag",
)
@pass_pulp_context
@click.pass_context
def content(ctx: click.Context, pulp_ctx: PulpContext, content_type: str) -> None:
    if content_type == "manifest":
        ctx.obj = PulpContainerManifestContext(pulp_ctx)
    elif content_type == "tag":
        ctx.obj = PulpContainerTagContext(pulp_ctx)
    elif content_type == "blob":
        ctx.obj = PulpContainerBlobContext(pulp_ctx)
    else:
        raise NotImplementedError()


list_options = [
    pulp_option("--media-type"),
    pulp_option("--names", "name__in", allowed_with_contexts=(PulpContainerTagContext,)),
]

show_options = [
    pulp_option(
        "--digest",
        expose_value=False,
        help=_("Digest associated with {entity}"),
        callback=_content_callback,
        allowed_with_contexts=(PulpContainerBlobContext, PulpContainerManifestContext),
    ),
    click.option(
        "--digest",
        expose_value=False,
        help=_("Digest associated with {entity}"),
        callback=_content_callback,
        allowed_with_contexts=(PulpContainerTagContext,),
        group=[
            "name",
        ],
        cls=GroupOption,
    ),
    click.option(
        "--name",
        expose_value=False,
        help=_("Name of {entity}"),
        allowed_with_contexts=(PulpContainerTagContext,),
        group=[
            "digest",
        ],
        cls=GroupOption,
    ),
    href_option,
]

content.add_command(list_command(decorators=list_options))
content.add_command(show_command(decorators=show_options))
