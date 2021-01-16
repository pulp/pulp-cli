from typing import Any, Callable, List, Optional

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
# Reusable conditions


def _truthy(ctx: click.Context) -> bool:
    return True


def _has_number(ctx: click.Context) -> bool:
    return ctx.params.get("number") is not None


def _has_no_number(ctx: click.Context) -> bool:
    return ctx.params.get("number") is None


##############################################################################
# Custom command classes to conditionally present subcommands


class CondMixin:
    def __init__(
        self, condition: Optional[Callable[[click.Context], bool]] = None, *args: Any, **kwargs: Any
    ) -> None:
        if condition is None:
            condition = _truthy
        self.condition: Callable[[click.Context], bool] = condition
        super().__init__(*args, **kwargs)


class CondCommand(CondMixin, click.Command):
    pass


class CondGroup(CondMixin, click.Group):
    def list_commands(self, ctx: click.Context) -> List[str]:
        return sorted(
            [
                name
                for name, command in self.commands.items()
                if not isinstance(command, CondMixin) or command.condition(ctx)
            ]
        )

    def get_command(self, ctx: click.Context, name: str) -> Optional[click.Command]:
        command = super().get_command(ctx, name)
        if isinstance(command, CondMixin) and not command.condition(ctx):
            return None
        return command

    # TODO: Add proper Type
    def command(self, *args: Any, **kwargs: Any) -> Any:
        if "condition" in kwargs and "cls" not in kwargs:
            kwargs["cls"] = CondCommand
        return super().command(*args, **kwargs)


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


def list_command(**kwargs: Any) -> click.Command:
    """A factory that creates a list command."""

    if "condition" in kwargs and "cls" not in kwargs:
        kwargs["cls"] = CondCommand
    if "name" not in kwargs:
        kwargs["name"] = "list"
    extra_options = kwargs.pop("extra_options", [])

    @click.command(**kwargs)
    @limit_option
    @offset_option
    @pass_entity_context
    @pass_pulp_context
    def callback(
        pulp_ctx: PulpContext, entity_ctx: PulpEntityContext, limit: int, offset: int, **kwargs: Any
    ) -> None:
        """
        Show a list of entries
        """
        parameters = {k: v for k, v in kwargs.items() if v is not None}
        result = entity_ctx.list(limit=limit, offset=offset, parameters=parameters)
        pulp_ctx.output_result(result)

    for option in extra_options:
        # Decorate callback with extra options
        callback = option(callback)
    return callback


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


def show_command(**kwargs: Any) -> click.Command:
    """A factory that creates a show command."""

    if "condition" in kwargs and "cls" not in kwargs:
        kwargs["cls"] = CondCommand
    if "name" not in kwargs:
        kwargs["name"] = "show"

    @click.command(**kwargs)
    @pass_entity_context
    @pass_pulp_context
    def callback(pulp_ctx: PulpContext, entity_ctx: PulpEntityContext) -> None:
        """
        Shows details of an entry
        """
        assert entity_ctx.entity is not None

        entity = entity_ctx.show(entity_ctx.entity["pulp_href"])
        pulp_ctx.output_result(entity)

    return callback


@click.command(name="show")
@pass_entity_context
@pass_pulp_context
def show_entity(pulp_ctx: PulpContext, entity_ctx: PulpEntityContext) -> None:
    """Shows details of an entry"""
    assert entity_ctx.entity is not None

    entity = entity_ctx.show(entity_ctx.entity["pulp_href"])
    pulp_ctx.output_result(entity)


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


def destroy_command(**kwargs: Any) -> click.Command:
    """A factory that creates a destroy command."""

    if "condition" in kwargs and "cls" not in kwargs:
        kwargs["cls"] = CondCommand
    if "name" not in kwargs:
        kwargs["name"] = "destroy"

    @click.command(**kwargs)
    @pass_entity_context
    def callback(entity_ctx: PulpEntityContext) -> None:
        """
        Destroy an entry
        """
        assert entity_ctx.entity is not None

        entity_ctx.delete(entity_ctx.entity["pulp_href"])

    return callback


@click.command(name="destroy")
@pass_entity_context
def destroy_entity(entity_ctx: PulpEntityContext) -> None:
    """
    Destroy an entry
    """
    assert entity_ctx.entity is not None

    entity_ctx.delete(entity_ctx.entity["pulp_href"])


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


def version_command(**kwargs: Any) -> click.Command:
    """A factory that creates a version command group."""

    if "cls" not in kwargs:
        kwargs["cls"] = CondGroup
    if "name" not in kwargs:
        kwargs["name"] = "version"

    @click.group(**kwargs)
    @click.option("--number", type=int, is_eager=True)
    @pass_repository_context
    @pass_pulp_context
    @click.pass_context
    def callback(
        ctx: click.Context,
        pulp_ctx: PulpContext,
        repository_ctx: PulpRepositoryContext,
        number: int,
    ) -> None:
        assert repository_ctx.entity is not None

        ctx.obj = repository_ctx.VERSION_CONTEXT(pulp_ctx)

        if number is not None:
            repo_href = repository_ctx.entity["pulp_href"]
            ctx.obj.entity = {"pulp_href": f"{repo_href}versions/{number}/"}

    callback.add_command(list_command(condition=_has_no_number))
    callback.add_command(show_command(condition=_has_number))
    callback.add_command(destroy_command(condition=_has_number))

    @callback.command(condition=_has_number)
    @pass_repository_version_context
    @pass_pulp_context
    def repair(
        pulp_ctx: PulpContext,
        repository_version_ctx: PulpRepositoryVersionContext,
    ) -> None:
        assert repository_version_ctx.entity is not None

        href = repository_version_ctx.entity["pulp_href"]
        result = repository_version_ctx.repair(href)
        pulp_ctx.output_result(result)

    return callback


# Generic repository_version command group
@click.group(name="version")
@pass_repository_context
@pass_pulp_context
@click.pass_context
def version_group(
    ctx: click.Context,
    pulp_ctx: PulpContext,
    repository_ctx: PulpRepositoryContext,
) -> None:
    assert repository_ctx.entity is not None

    ctx.obj = repository_ctx.VERSION_CONTEXT(pulp_ctx)
    ctx.obj.repository = repository_ctx.entity


version_group.add_command(list_entities)
version_group.add_command(show_version)
version_group.add_command(destroy_version)
version_group.add_command(repair_version)
