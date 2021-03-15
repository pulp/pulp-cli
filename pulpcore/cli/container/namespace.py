import gettext

import click

from pulpcore.cli.common.context import PulpContext, pass_pulp_context
from pulpcore.cli.common.generic import (
    create_command,
    destroy_command,
    href_option,
    list_command,
    name_option,
    show_command,
)
from pulpcore.cli.container.context import PulpContainerNamespaceContext

_ = gettext.gettext


@click.group()
@click.option(
    "-t",
    "--type",
    "namespace_type",
    type=click.Choice(["container"], case_sensitive=False),
    default="container",
)
@pass_pulp_context
@click.pass_context
def namespace(ctx: click.Context, pulp_ctx: PulpContext, namespace_type: str) -> None:
    if namespace_type == "container":
        ctx.obj = PulpContainerNamespaceContext(pulp_ctx)
    else:
        raise NotImplementedError()


lookup_options = [href_option, name_option]
create_options = [
    click.option("--name", required=True),
]

namespace.add_command(list_command())
namespace.add_command(show_command(decorators=lookup_options))
namespace.add_command(create_command(decorators=create_options))
namespace.add_command(destroy_command(decorators=lookup_options))
