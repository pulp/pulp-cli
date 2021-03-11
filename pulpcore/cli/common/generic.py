import gettext
import json
from typing import Any, Optional, Tuple, Union

import click

from pulpcore.cli.common.context import (
    DEFAULT_LIMIT,
    EntityDefinition,
    PulpContext,
    PulpEntityContext,
    PulpRepositoryContext,
    PulpRepositoryVersionContext,
    pass_entity_context,
    pass_pulp_context,
    pass_repository_context,
    pass_repository_version_context,
)

_ = gettext.gettext


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


def _href_callback(
    ctx: click.Context, param: click.Parameter, value: Optional[str]
) -> Optional[str]:
    if value is not None:
        entity_ctx: PulpEntityContext = ctx.find_object(PulpEntityContext)
        entity_ctx.pulp_href = value
    return value


def _name_callback(
    ctx: click.Context, param: click.Parameter, value: Optional[str]
) -> Optional[str]:
    if value is not None:
        entity_ctx: PulpEntityContext = ctx.find_object(PulpEntityContext)
        entity_ctx.entity = {"name": value}
    return value


def _repository_href_callback(
    ctx: click.Context, param: click.Parameter, value: Optional[str]
) -> Optional[str]:
    if value is not None:
        repository_ctx: PulpRepositoryContext = ctx.find_object(PulpRepositoryContext)
        repository_ctx.pulp_href = value
    return value


def _repository_callback(
    ctx: click.Context, param: click.Parameter, value: Optional[str]
) -> Optional[str]:
    if value is not None:
        repository_ctx: PulpRepositoryContext = ctx.find_object(PulpRepositoryContext)
        repository_ctx.entity = {"name": value}
    return value


def _version_callback(
    ctx: click.Context, param: click.Parameter, value: Optional[int]
) -> Optional[int]:
    entity_ctx: PulpEntityContext = ctx.find_object(PulpEntityContext)
    repository_ctx: PulpRepositoryContext = ctx.find_object(PulpRepositoryContext)
    if value is not None:
        entity_ctx.pulp_href = repository_ctx.entity["versions_href"] + str(value)
    else:
        entity_ctx.pulp_href = repository_ctx.entity["latest_version_href"]
    return value


def load_json_callback(
    ctx: click.Context,
    param: click.Parameter,
    value: str,
) -> Any:
    """Load JSON from input string or from file if string starts with @."""
    json_object: Any
    json_string: Union[str, bytes]

    if value is None:
        return None

    if value.startswith("@"):
        json_file = value[1:]
        try:
            with click.open_file(json_file, "rb") as fp:
                json_string = fp.read()
        except OSError:
            raise click.ClickException(f"Failed to load content from {json_file}")
    else:
        json_string = value

    try:
        json_object = json.loads(json_string)
    except json.decoder.JSONDecodeError:
        raise click.ClickException("Failed to decode JSON")
    else:
        return json_object


##############################################################################
# Decorator common options


limit_option = click.option(
    "--limit",
    default=DEFAULT_LIMIT,
    type=int,
    help=_("Limit the number of {entities} to show."),
    cls=PulpOption,
)
offset_option = click.option(
    "--offset",
    default=0,
    type=int,
    help=_("Skip a number of {entities} to show."),
    cls=PulpOption,
)

href_option = click.option(
    "--href",
    help=_("HREF of the {entity}"),
    callback=_href_callback,
    expose_value=False,
    cls=PulpOption,
)

name_option = click.option(
    "--name",
    help=_("Name of the {entity}"),
    callback=_name_callback,
    expose_value=False,
    cls=PulpOption,
)

repository_href_option = click.option(
    "--repository-href",
    help=_("HREF of the repository"),
    callback=_repository_href_callback,
    expose_value=False,
)

repository_option = click.option(
    "--repository",
    help=_("Name of the repository"),
    callback=_repository_callback,
    expose_value=False,
)

version_option = click.option(
    "--version",
    help=_("Repository version number"),
    type=int,
    callback=_version_callback,
    expose_value=False,
)

label_select_option = click.option(
    "--label-select",
    "pulp_label_select",
    help=_("Filter {entities} by a label search query."),
    type=str,
    cls=PulpOption,
)

base_path_option = click.option(
    "--base-path",
    help=_("Base-path of the {entity}"),
    type=str,
    cls=PulpOption,
)

base_path_contains_option = click.option(
    "--base-path-contains",
    "base_path__icontains",
    help=_("{entity} base-path contains search"),
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
    if "help" not in kwargs:
        kwargs["help"] = _("Show the list of optionally filtered {entities}.")
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
    if "help" not in kwargs:
        kwargs["help"] = _("Show details of a {entity}.")
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


def create_command(**kwargs: Any) -> click.Command:
    """A factory that creates a create command."""

    if "cls" not in kwargs:
        kwargs["cls"] = PulpCommand
    if "name" not in kwargs:
        kwargs["name"] = "create"
    if "help" not in kwargs:
        kwargs["help"] = _("Create a {entity}.")
    decorators = kwargs.pop("decorators", [])

    @click.command(**kwargs)
    @pass_entity_context
    @pass_pulp_context
    def callback(pulp_ctx: PulpContext, entity_ctx: PulpEntityContext, **kwargs: Any) -> None:
        """
        Create a {entity}.
        """
        body: EntityDefinition = entity_ctx.preprocess_body(kwargs)
        result = entity_ctx.create(body=body)
        if "created_resources" in result:
            entity_ctx.pulp_href = result["created_resources"][0]
            result = entity_ctx.entity
        pulp_ctx.output_result(result)

    for option in decorators:
        # Decorate callback
        callback = option(callback)
    return callback


def update_command(**kwargs: Any) -> click.Command:
    """A factory that creates an update command."""

    if "cls" not in kwargs:
        kwargs["cls"] = PulpCommand
    if "name" not in kwargs:
        kwargs["name"] = "update"
    if "help" not in kwargs:
        kwargs["help"] = _("Update a {entity}.")
    decorators = kwargs.pop("decorators", [])

    @click.command(**kwargs)
    @pass_entity_context
    @pass_pulp_context
    def callback(pulp_ctx: PulpContext, entity_ctx: PulpEntityContext, **kwargs: Any) -> None:
        """
        Update a {entity}.
        """
        body: EntityDefinition = entity_ctx.preprocess_body(kwargs)
        entity_ctx.update(href=entity_ctx.pulp_href, body=body)

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
    if "help" not in kwargs:
        kwargs["help"] = _("Destroy a {entity}.")
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
    decorators = kwargs.pop("decorators", [repository_href_option, repository_option])

    @click.group(**kwargs)
    @pass_repository_context
    @click.pass_context
    def callback(
        ctx: click.Context,
        repository_ctx: PulpRepositoryContext,
    ) -> None:
        ctx.obj = repository_ctx.get_version_context()

    callback.add_command(list_command(decorators=decorators))
    callback.add_command(show_command(decorators=decorators + [version_option]))
    callback.add_command(destroy_command(decorators=decorators + [version_option]))

    @callback.command()
    @repository_option
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

    @click.command(name="set", help=_("Add or update a label"))
    @click.option("--key", required=True, help=_("Key of the label"))
    @click.option("--value", required=True, help=_("Value of the label"))
    @pass_entity_context
    def label_set(entity_ctx: PulpEntityContext, key: str, value: str) -> None:
        """Add or update a label"""
        href = entity_ctx.entity["pulp_href"]
        entity_ctx.set_label(href, key, value)

    @click.command(name="unset", help=_("Remove a label with a given key"))
    @click.option("--key", required=True, help=_("Key of the label"))
    @pass_entity_context
    def label_unset(entity_ctx: PulpEntityContext, key: str) -> None:
        """Remove a label with a given key"""
        href = entity_ctx.entity["pulp_href"]
        entity_ctx.unset_label(href, key)

    @click.command(name="show", help=_("Show the value for a particular label key"))
    @click.option("--key", required=True, help=_("Key of the label"))
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
