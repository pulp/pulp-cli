import click
from pulpcore.cli.common.context import PulpContext, pass_pulp_context
from pulpcore.cli.common.generic import (
    list_entities,
    show_entity,
    destroy_entity,
    create_entity,
    update_entity,
    href_option,
    name_option,
    label_select_option,
    version_option,
)
from pulpcore.cli.container.context import (
    PulpContainerRepositoryContext,
    PulpContainerPushRepositoryContext,
    PulpContainerDistributionContext,
    PulpContainerContentGuardContext,
    PulpContainerNamespaceContext,
    PulpContainerRecursiveAddContext,
    PulpContainerRecursiveRemoveContext,
    PulpContainerTagContext,
    PulpContainerManifestContext,
    PulpContainerBlobContext,
    PulpContainerImageContext,
    PulpContainerSignatureContext,
)


@click.group()
@click.option(
    "-t",
    "--type",
    "repo_type",
    type=click.Choice(["container", "push"], case_sensitive=False),
    default="container",
)
@pass_pulp_context
@click.pass_context
def repository(ctx: click.Context, pulp_ctx: PulpContext, repo_type: str) -> None:
    if repo_type == "container":
        ctx.obj = PulpContainerRepositoryContext(pulp_ctx)
    elif repo_type == "push":
        ctx.obj = PulpContainerPushRepositoryContext(pulp_ctx)


repository.add_command(list_entities)
repository.add_command(show_entity)
repository.add_command(destroy_entity)
repository.add_command(create_entity)
repository.add_command(update_entity)


@repository.command()
@click.option("--remote", required=True, help="Remote to sync from")
@click.option(
    "--mirror",
    type=bool,
    default=None,
    help="Mirror mode: True to remove content not present in upstream, False for additive sync only",
)
@href_option
@name_option
@pass_pulp_context
@click.pass_context
def sync(
    ctx: click.Context,
    pulp_ctx: PulpContext,
    remote: str,
    mirror: bool,
    href: str,
    name: str,
) -> None:
    """
    Sync content from a remote repository.
    """
    entity_ctx = ctx.obj
    repository_href = entity_ctx.find(href=href, name=name)["pulp_href"]

    body: dict = {"remote": remote}
    if mirror is not None:
        body["mirror"] = mirror

    result = entity_ctx.sync(repository_href, body)
    pulp_ctx.output_result(result)