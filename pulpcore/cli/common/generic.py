from typing import Any, Optional, Tuple

import click

from pulpcore.cli.common.context import (
    DEFAULT_LIMIT,
    PulpContext,
    PulpEntityContext,
    PulpRepositoryContext,
    PulpRepositoryVersionContext,
    pass_entity_context,
    pass_pulp_context,
    pass_repository_context,
    pass_repository_version_context,
)


class PulpCommand(click.Command):
    def get_short_help_str(self, limit: int = 45) -> str:
        return self.short_help or ""

    def format_help_text(
        self, ctx: click.Context, formatter: click.formatting.HelpFormatter
    ) -> None:
        entity_ctx: PulpEntityContext = ctx.find_object(PulpEntityContext)
        if self.help is not None:
            self.help = self.help.format(entity=entity_ctx.ENTITY, entities=entity_ctx.ENTITIES)
        super().format_help_text(ctx, formatter)


class PulpOption(click.Option):
    def get_help_record(self, ctx: click.Context) -> Tuple[str, str]:
        synopsis, help_text = super().get_help_record(ctx)
        entity_ctx: PulpEntityContext = ctx.find_object(PulpEntityContext)
        help_text = help_text.format(entity=entity_ctx.ENTITY, entities=entity_ctx.ENTITIES)
        return synopsis, help_text


##############################################################################
# Option callbacks


def _href_callback(ctx: click.Context, param: click.Parameter, value: str) -> str:
    if value is not None:
        entity_ctx: PulpEntityContext = ctx.find_object(PulpEntityContext)
        entity_ctx.pulp_href = value
    return value


def _name_callback(ctx: click.Context, param: click.Parameter, value: str) -> str:
    if value is not None:
        entity_ctx: PulpEntityContext = ctx.find_object(PulpEntityContext)
        entity_ctx.entity = {"name": value}
    return value


def _version_callback(ctx: click.Context, param: click.Parameter, value: int) -> int:
    entity_ctx: PulpEntityContext = ctx.find_object(PulpEntityContext)
    repository_ctx: PulpRepositoryContext = ctx.find_object(PulpRepositoryContext)
    if value is not None:
        entity_ctx.pulp_href = repository_ctx.entity["versions_href"] + str(value)
    else:
        entity_ctx.pulp_href = repository_ctx.entity["latest_version_href"]
    return value


##############################################################################
# Decorator common options


limit_option = click.option(
    "--limit",
    default=DEFAULT_LIMIT,
    type=int,
    help="Limit the number of {entities} to show.",
    cls=PulpOption,
)
offset_option = click.option(
    "--offset",
    default=0,
    type=int,
    help="Skip a number of {entities} to show.",
    cls=PulpOption,
)

href_option = click.option(
    "--href",
    help="HREF of the {entity}",
    callback=_href_callback,
    expose_value=False,
    cls=PulpOption,
)

name_option = click.option(
    "--name",
    help="Name of the {entity}",
    callback=_name_callback,
    expose_value=False,
    cls=PulpOption,
)

version_option = click.option(
    "--version",
    help="Repository version number",
    type=int,
    callback=_version_callback,
    expose_value=False,
)

label_select_option = click.option(
    "--label-select",
    "pulp_label_select",
    help="Filter {entities} by a label search query.",
    type=str,
    cls=PulpOption,
)

##############################################################################
# Generic reusable commands


def list_command(**kwargs: Any) -> click.Command:
    """A factory that creates a list command."""

    if "cls" not in kwargs:
        kwargs["cls"] = PulpCommand
    if "name" not in kwargs:
        kwargs["name"] = "list"
    decorators = kwargs.pop("decorators", [])

    @click.command(**kwargs)
    @limit_option
    @offset_option
    @pass_entity_context
    @pass_pulp_context
    def callback(
        pulp_ctx: PulpContext, entity_ctx: PulpEntityContext, limit: int, offset: int, **kwargs: Any
    ) -> None:
        """
        Show the list of optionally filtered {entities}.
        """
        parameters = {k: v for k, v in kwargs.items() if v is not None}
        result = entity_ctx.list(limit=limit, offset=offset, parameters=parameters)
        pulp_ctx.output_result(result)

    for option in decorators:
        # Decorate callback
        callback = option(callback)
    return callback


def show_command(**kwargs: Any) -> click.Command:
    """A factory that creates a show command."""

    if "cls" not in kwargs:
        kwargs["cls"] = PulpCommand
    if "name" not in kwargs:
        kwargs["name"] = "show"
    decorators = kwargs.pop("decorators", [])

    @click.command(**kwargs)
    @pass_entity_context
    @pass_pulp_context
    def callback(pulp_ctx: PulpContext, entity_ctx: PulpEntityContext) -> None:
        """
        Show details of a {entity}.
        """
        pulp_ctx.output_result(entity_ctx.entity)

    for option in decorators:
        # Decorate callback
        callback = option(callback)
    return callback


def destroy_command(**kwargs: Any) -> click.Command:
    """A factory that creates a destroy command."""

    if "cls" not in kwargs:
        kwargs["cls"] = PulpCommand
    if "name" not in kwargs:
        kwargs["name"] = "destroy"
    decorators = kwargs.pop("decorators", [])

    @click.command(**kwargs)
    @pass_entity_context
    def callback(entity_ctx: PulpEntityContext) -> None:
        """
        Destroy a {entity}.
        """
        entity_ctx.delete(entity_ctx.pulp_href)

    for option in decorators:
        # Decorate callback
        callback = option(callback)
    return callback


def version_command(**kwargs: Any) -> click.Command:
    """A factory that creates a repository version command group."""

    if "name" not in kwargs:
        kwargs["name"] = "version"
    decorators = kwargs.pop("decorators", [])

    @click.group(**kwargs)
    @click.option("--repository")
    @pass_repository_context
    @pass_pulp_context
    @click.pass_context
    def callback(
        ctx: click.Context,
        pulp_ctx: PulpContext,
        repository_ctx: PulpRepositoryContext,
        repository: Optional[str],
    ) -> None:
        ctx.obj = repository_ctx.get_version_context()
        if repository is not None:
            repository_ctx.entity = {"name": repository}

    for option in decorators:
        # Decorate callback
        callback = option(callback)

    callback.add_command(list_command())
    callback.add_command(show_command(decorators=[version_option]))
    callback.add_command(destroy_command(decorators=[version_option]))

    @callback.command()
    @version_option
    @pass_repository_version_context
    @pass_pulp_context
    def repair(
        pulp_ctx: PulpContext,
        repository_version_ctx: PulpRepositoryVersionContext,
    ) -> None:
        href = repository_version_ctx.pulp_href
        result = repository_version_ctx.repair(href)
        pulp_ctx.output_result(result)

    return callback


def label_command(**kwargs: Any) -> click.Command:
    """A factory that creates a label command group."""

    if "name" not in kwargs:
        kwargs["name"] = "label"
    decorators = kwargs.pop("decorators", [name_option, href_option])

    @click.group(**kwargs)
    def label_group() -> None:
        pass

    @click.command(name="set")
    @click.option("--key", required=True, help="Key of the label")
    @click.option("--value", required=True, help="Value of the label")
    @pass_entity_context
    def label_set(entity_ctx: PulpEntityContext, key: str, value: str) -> None:
        """Add or update a label"""
        href = entity_ctx.entity["pulp_href"]
        entity_ctx.set_label(href, key, value)

    @click.command(name="unset")
    @click.option("--key", required=True, help="Key of the label")
    @pass_entity_context
    def label_unset(entity_ctx: PulpEntityContext, key: str) -> None:
        """Remove a label with a given key"""
        href = entity_ctx.entity["pulp_href"]
        entity_ctx.unset_label(href, key)

    @click.command(name="show")
    @click.option("--key", required=True, help="Key of the label")
    @pass_entity_context
    def label_show(entity_ctx: PulpEntityContext, key: str) -> None:
        """Show the value for a particular label key"""
        href = entity_ctx.entity["pulp_href"]
        click.echo(entity_ctx.show_label(href, key))

    for subcmd in [label_set, label_unset, label_show]:
        for decorator in decorators:
            subcmd = decorator(subcmd)
        label_group.add_command(subcmd)

    return label_group


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
@pass_repository_context
@pass_pulp_context
def show_version(
    pulp_ctx: PulpContext,
    repository_ctx: PulpRepositoryContext,
    repository_version_ctx: PulpRepositoryVersionContext,
    version: int,
) -> None:
    repo_href = repository_ctx.pulp_href
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
@pass_repository_context
def destroy_version(
    repository_ctx: PulpRepositoryContext,
    repository_version_ctx: PulpRepositoryVersionContext,
    version: int,
) -> None:
    repo_href = repository_ctx.pulp_href
    href = f"{repo_href}versions/{version}/"
    repository_version_ctx.delete(href)


@click.command(name="repair")
@click.option("--version", required=True, type=int)
@pass_repository_version_context
@pass_repository_context
@pass_pulp_context
def repair_version(
    pulp_ctx: PulpContext,
    repository_ctx: PulpRepositoryContext,
    repository_version_ctx: PulpRepositoryVersionContext,
    version: int,
) -> None:
    repo_href = repository_ctx.pulp_href
    href = f"{repo_href}versions/{version}/"
    result = repository_version_ctx.repair(href)
    pulp_ctx.output_result(result)


# Generic repository_version command group
@click.group(name="version")
@click.option("--repository")
@pass_repository_context
@pass_pulp_context
@click.pass_context
def version_group(
    ctx: click.Context,
    pulp_ctx: PulpContext,
    repository_ctx: PulpRepositoryContext,
    repository: Optional[str],
) -> None:
    ctx.obj = repository_ctx.get_version_context()
    if repository is not None:
        repository_ctx.entity = {"name": repository}


version_group.add_command(list_entities)
version_group.add_command(show_version)
version_group.add_command(destroy_version)
version_group.add_command(repair_version)
