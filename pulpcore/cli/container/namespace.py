import click
from pulp_glue.common.i18n import get_translation
from pulp_glue.container.context import PulpContainerNamespaceContext

from pulpcore.cli.common.generic import (
    PulpCLIContext,
    create_command,
    destroy_command,
    href_option,
    list_command,
    name_option,
    pass_pulp_context,
    pulp_group,
    resource_lookup_option,
    role_command,
    show_command,
)

translation = get_translation(__package__)
_ = translation.gettext


namespace_lookup_option = resource_lookup_option(
    "--namespace",
    context_class=PulpContainerNamespaceContext,
)


@pulp_group()
@click.option(
    "-t",
    "--type",
    "namespace_type",
    type=click.Choice(["container"], case_sensitive=False),
    default="container",
)
@pass_pulp_context
@click.pass_context
def namespace(ctx: click.Context, pulp_ctx: PulpCLIContext, namespace_type: str) -> None:
    if namespace_type == "container":
        ctx.obj = PulpContainerNamespaceContext(pulp_ctx)
    else:
        raise NotImplementedError()


lookup_options = [href_option, name_option, namespace_lookup_option]
create_options = [
    click.option("--name", required=True),
]

namespace.add_command(list_command())
namespace.add_command(show_command(decorators=lookup_options))
namespace.add_command(create_command(decorators=create_options))
namespace.add_command(destroy_command(decorators=lookup_options))
namespace.add_command(role_command(decorators=lookup_options))
