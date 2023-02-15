import click
from pulp_glue.common.context import PluginRequirement, registered_repository_contexts
from pulp_glue.core.context import PulpPublicationContext

from pulpcore.cli.common.generic import (
    PulpCLIContext,
    list_command,
    pass_pulp_context,
    publication_filter_options,
    pulp_group,
    resource_option,
)

repository_option = resource_option(
    "--repository",
    context_table=registered_repository_contexts,
    needs_plugins=[PluginRequirement("core", min="3.20.0")],
)


@pulp_group()
@pass_pulp_context
@click.pass_context
def publication(ctx: click.Context, pulp_ctx: PulpCLIContext) -> None:
    """
    Perform actions on all publications.

    Please look for the plugin specific publication commands for more detailed actions.
    i.e. 'pulp file publication <...>'
    """
    ctx.obj = PulpPublicationContext(pulp_ctx)


publication.add_command(list_command(decorators=publication_filter_options + [repository_option]))
