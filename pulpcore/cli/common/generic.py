from typing import Any

import click

from pulpcore.cli.common.context import (
    DEFAULT_LIMIT,
    PulpContext,
    PulpEntityContext,
    PulpRepositoryContext,
    PulpRepositoryVersionContext,
    pass_pulp_context,
    pass_entity_context,
    pass_repository_context,
    pass_repository_version_context,
)


##############################################################################
# Decorator common options


limit_option = click.option(
    "--limit", default=DEFAULT_LIMIT, type=int, help="Limit the number of entries to show."
)
offset_option = click.option(
    "--offset", default=0, type=int, help="Skip a number of entries to show."
)


##############################################################################
# Generic reusable commands


@click.command(name="list")
@limit_option
@offset_option
@pass_entity_context
@pass_pulp_context
def list_entities(
    pulp_ctx: PulpContext, entity_ctx: PulpEntityContext, limit: int, offset: int, **kwargs: Any
) -> None:
    """
    Show a list of entries
    """
    parameters = {k: v for k, v in kwargs.items() if v is not None}
    result = entity_ctx.list(limit=limit, offset=offset, parameters=parameters)
    pulp_ctx.output_result(result)


@click.command(name="show")
@click.option("--name", required=True, help="Name of the entry")
@pass_entity_context
@pass_pulp_context
def show_by_name(pulp_ctx: PulpContext, entity_ctx: PulpEntityContext, name: str) -> None:
    """Shows details of an entry"""
    href = entity_ctx.find(name=name)["pulp_href"]
    entity = entity_ctx.show(href)
    pulp_ctx.output_result(entity)


@click.command(name="show")
@click.option("--href", required=True, help="HREF of the entry")
@pass_entity_context
@pass_pulp_context
def show_by_href(pulp_ctx: PulpContext, entity_ctx: PulpEntityContext, href: str) -> None:
    """Shows details of an entry"""
    entity = entity_ctx.show(href)
    pulp_ctx.output_result(entity)


@click.command(name="show")
@click.option("--version", required=True, type=int)
@pass_repository_version_context
@pass_pulp_context
def show_version(
    pulp_ctx: PulpContext,
    repository_version_ctx: PulpRepositoryVersionContext,
    version: int,
) -> None:
    repo_href = repository_version_ctx.repository["pulp_href"]
    href = f"{repo_href}versions/{version}"
    result = repository_version_ctx.show(href)
    pulp_ctx.output_result(result)


@click.command(name="destroy")
@click.option("--name", required=True, help="Name of the entry to destroy")
@pass_entity_context
def destroy_by_name(entity_ctx: PulpEntityContext, name: str) -> None:
    """
    Destroy an entry
    """
    href = entity_ctx.find(name=name)["pulp_href"]
    entity_ctx.delete(href)


@click.command(name="destroy")
@click.option("--href", required=True, help="HREF of the entry to destroy")
@pass_entity_context
def destroy_by_href(entity_ctx: PulpEntityContext, href: str) -> None:
    """
    Destroy an entry
    """
    entity_ctx.delete(href)


@click.command(name="destroy")
@click.option("--version", required=True, type=int)
@pass_repository_version_context
def destroy_version(
    repository_version_ctx: PulpRepositoryVersionContext,
    version: int,
) -> None:
    repo_href = repository_version_ctx.repository["pulp_href"]
    href = f"{repo_href}versions/{version}/"
    repository_version_ctx.delete(href)


@click.command(name="repair")
@click.option("--version", required=True, type=int)
@pass_repository_version_context
@pass_pulp_context
def repair_version(
    pulp_ctx: PulpContext,
    repository_version_ctx: PulpRepositoryVersionContext,
    version: int,
) -> None:
    repo_href = repository_version_ctx.repository["pulp_href"]
    href = f"{repo_href}versions/{version}/"
    result = repository_version_ctx.repair(href)
    pulp_ctx.output_result(result)


# Generic repository_version command group
@click.group(name="version")
@click.option("--repository", required=True)
@pass_repository_context
@pass_pulp_context
@click.pass_context
def version_group(
    ctx: click.Context,
    pulp_ctx: PulpContext,
    repository_ctx: PulpRepositoryContext,
    repository: str,
) -> None:
    ctx.obj = repository_ctx.VERSION_CONTEXT(pulp_ctx)
    ctx.obj.repository = repository_ctx.find(name=repository)


version_group.add_command(list_entities)
version_group.add_command(show_version)
version_group.add_command(destroy_version)
version_group.add_command(repair_version)
