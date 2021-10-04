import gettext
import json
import re
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
)

import click
import schema as s

from pulpcore.cli.common.context import (
    DEFAULT_LIMIT,
    EntityDefinition,
    EntityFieldDefinition,
    PluginRequirement,
    PulpContentContext,
    PulpContext,
    PulpEntityContext,
    PulpRepositoryContext,
    PulpRepositoryVersionContext,
    pass_content_context,
    pass_entity_context,
    pass_pulp_context,
    pass_repository_context,
    pass_repository_version_context,
)

_ = gettext.gettext

_F = TypeVar("_F")
_FC = TypeVar("_FC", Callable[..., Any], click.Command)


class PulpCommand(click.Command):
    def get_short_help_str(self, limit: int = 45) -> str:
        return self.short_help or ""

    def format_help_text(
        self, ctx: click.Context, formatter: click.formatting.HelpFormatter
    ) -> None:
        entity_ctx = ctx.find_object(PulpEntityContext)
        assert entity_ctx is not None
        if self.help is not None:
            self.help = self.help.format(entity=entity_ctx.ENTITY, entities=entity_ctx.ENTITIES)
        super().format_help_text(ctx, formatter)


class PulpOption(click.Option):
    def __init__(
        self,
        *args: Any,
        needs_plugins: Optional[List[PluginRequirement]] = None,
        **kwargs: Any,
    ):
        self.needs_plugins = needs_plugins
        super().__init__(*args, **kwargs)

    def process_value(self, ctx: click.Context, value: Any) -> Any:
        if value is not None and self.needs_plugins:
            pulp_ctx = ctx.find_object(PulpContext)
            assert pulp_ctx is not None
            for plugin_requirement in self.needs_plugins:
                if not plugin_requirement.feature:
                    plugin_requirement = PluginRequirement(
                        plugin_requirement.name,
                        plugin_requirement.min,
                        plugin_requirement.max,
                        feature=_("the {name} option").format(name=self.name),
                        inverted=plugin_requirement.inverted,
                    )

                pulp_ctx.needs_plugin(plugin_requirement)
        return super().process_value(ctx, value)

    def get_help_record(self, ctx: click.Context) -> Optional[Tuple[str, str]]:
        tmp = super().get_help_record(ctx)
        if tmp is None:
            return None
        synopsis, help_text = tmp
        entity_ctx = ctx.find_object(PulpEntityContext)
        assert entity_ctx is not None
        help_text = help_text.format(entity=entity_ctx.ENTITY, entities=entity_ctx.ENTITIES)
        return synopsis, help_text


class GroupOption(PulpOption):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.group: List[str] = kwargs.pop("group")
        assert self.group, "'group' parameter required"
        kwargs["help"] = (
            kwargs.get("help", "")
            + " "
            + _("Option is grouped with {option_list}.").format(option_list=", ".join(self.group))
        ).strip()
        super().__init__(*args, **kwargs)

    def handle_parse_result(
        self, ctx: click.Context, opts: Mapping[str, Any], args: List[Any]
    ) -> Any:
        assert self.name is not None
        all_options = self.group + [self.name]
        if all(x in opts for x in all_options):
            self.prompt = None
        else:
            raise click.UsageError(
                _("Illegal usage, please specify all options in the group: {option_list}").format(
                    option_list=", ".join(all_options)
                )
            )
        value = opts.get(self.name)
        if self.callback is not None:
            value = self.callback(ctx, self, {o: opts[o] for o in all_options})
        if self.expose_value:
            ctx.params[self.name] = value
        return value, args


##############################################################################
# Option callbacks


def _href_callback(
    ctx: click.Context, param: click.Parameter, value: Optional[str]
) -> Optional[str]:
    if value is not None:
        entity_ctx = ctx.find_object(PulpEntityContext)
        assert entity_ctx is not None
        entity_ctx.pulp_href = value
    return value


def _name_callback(
    ctx: click.Context, param: click.Parameter, value: Optional[str]
) -> Optional[str]:
    if value is not None:
        entity_ctx = ctx.find_object(PulpEntityContext)
        assert entity_ctx is not None
        entity_ctx.entity = {"name": value}
    return value


def _repository_href_callback(
    ctx: click.Context, param: click.Parameter, value: Optional[str]
) -> Optional[str]:
    if value is not None:
        repository_ctx = ctx.find_object(PulpRepositoryContext)
        assert repository_ctx is not None
        repository_ctx.pulp_href = value
    return value


def _repository_callback(
    ctx: click.Context, param: click.Parameter, value: Optional[str]
) -> Optional[str]:
    if value is not None:
        repository_ctx = ctx.find_object(PulpRepositoryContext)
        assert repository_ctx is not None
        repository_ctx.entity = {"name": value}
    return value


def _version_callback(
    ctx: click.Context, param: click.Parameter, value: Optional[int]
) -> Optional[int]:
    entity_ctx = ctx.find_object(PulpEntityContext)
    assert entity_ctx is not None
    repository_ctx = ctx.find_object(PulpRepositoryContext)
    assert repository_ctx is not None
    if value is not None:
        entity_ctx.pulp_href = f"{repository_ctx.entity['versions_href']}{value}/"
    else:
        entity_ctx.pulp_href = repository_ctx.entity["latest_version_href"]
    return value


def load_json_callback(
    ctx: click.Context,
    param: click.Parameter,
    value: Optional[str],
) -> Any:
    """Load JSON from input string or from file if string starts with @."""
    json_object: Any
    json_string: Union[str, bytes]

    # pass None and "" verbatim
    if not value:
        return value

    if value.startswith("@"):
        json_file = value[1:]
        try:
            with click.open_file(json_file, "rb") as fp:
                json_string = fp.read()
        except OSError:
            raise click.ClickException(
                _("Failed to load content from {json_file}").format(json_file=json_file)
            )
    else:
        json_string = value

    try:
        json_object = json.loads(json_string)
    except json.decoder.JSONDecodeError:
        raise click.ClickException(_("Failed to decode JSON"))
    else:
        return json_object


def create_content_json_callback(
    content_ctx: Type[PulpContentContext], schema: s.Schema = None
) -> Any:
    def _callback(
        ctx: click.Context, param: click.Parameter, value: Optional[str]
    ) -> Optional[List[PulpContentContext]]:
        new_value = load_json_callback(ctx, param, value)
        if new_value is not None:
            if schema is not None:
                try:
                    schema.validate(new_value)
                except s.SchemaError as e:
                    raise click.ClickException(
                        _("Validation of '{parameter}' failed: {error}").format(
                            parameter=param.name, error=str(e)
                        )
                    )
            pulp_ctx = ctx.find_object(PulpContext)
            assert pulp_ctx is not None
            return [content_ctx(pulp_ctx, entity=unit) for unit in new_value]
        return new_value

    return _callback


# based on https://stackoverflow.com/a/42865957/2002471
units = {"B": 1, "KB": 10 ** 3, "MB": 10 ** 6, "GB": 10 ** 9, "TB": 10 ** 12}


def parse_size_callback(ctx: click.Context, param: click.Parameter, value: str) -> int:
    size = value.strip().upper()
    match = re.match(r"^([0-9]+)\s*([KMGT]?B)?$", size)
    if not match:
        raise click.ClickException("Please pass in a valid size of form: [0-9] [K/M/G/T]B")
    number, unit = match.groups(default="B")
    return int(float(number) * units[unit])


##############################################################################
# Decorator common options


def pulp_option(*args: Any, **kwargs: Any) -> Callable[[_FC], _FC]:
    kwargs["cls"] = PulpOption
    return click.option(*args, **kwargs)


def resource_option(*args: Any, **kwargs: Any) -> Callable[[_FC], _FC]:
    default_plugin: Optional[str] = kwargs.pop("default_plugin", None)
    default_type: Optional[str] = kwargs.pop("default_type", None)
    lookup_key: str = kwargs.pop("lookup_key", "name")
    context_table: Dict[str, Type[PulpEntityContext]] = kwargs.pop("context_table")
    capabilities: Optional[List[str]] = kwargs.pop("capabilities", None)
    href_pattern: Optional[str] = kwargs.pop("href_pattern", None)

    def _option_callback(
        ctx: click.Context, param: click.Parameter, value: Optional[str]
    ) -> EntityFieldDefinition:
        # Pass None and "" verbatim
        if not value:
            return value

        pulp_href: Optional[str] = None
        entity: Optional[EntityDefinition] = None

        if value.startswith("/"):
            # An href was passed
            if href_pattern is None:
                raise click.ClickException(
                    _("The option {option_name} does not support href.").format(
                        option_name=param.name
                    )
                )
            match = re.match(href_pattern, value)
            if match is None:
                raise click.ClickException(
                    _("'{value}' is not a valid href for {option_name}.").format(
                        value=value, option_name=param.name
                    )
                )
            match_groups = match.groupdict(default="")
            plugin = match_groups.get("plugin", "")
            resource_type = match_groups.get("resource_type", "")
            pulp_href = value
        else:
            # A natural key identifier was passed
            split_value = value.split(":", maxsplit=2)
            while len(split_value) < 3:
                split_value.insert(0, "")
            plugin, resource_type, identifier = split_value
            entity = {lookup_key: identifier}

        if resource_type == "":
            if default_type is None:
                raise click.ClickException(
                    _("A resource type must be specified with the {option_name} option.").format(
                        option_name=param.name
                    )
                )
            resource_type = default_type
        if plugin == "":
            if default_plugin is None:
                raise click.ClickException(
                    _("A plugin must be specified with the {option_name} option.").format(
                        option_name=param.name
                    )
                )
            plugin = default_plugin

        context_class = context_table.get(plugin + ":" + resource_type)
        if context_class is None:
            raise click.ClickException(
                _(
                    "The type '{plugin}:{resource_type}' "
                    "is not valid for the {option_name} option."
                ).format(plugin=plugin, resource_type=resource_type, option_name=param.name)
            )
        pulp_ctx = ctx.find_object(PulpContext)
        assert pulp_ctx is not None
        entity_ctx: PulpEntityContext = context_class(pulp_ctx, pulp_href=pulp_href, entity=entity)

        if capabilities is not None:
            for capability in capabilities:
                if not entity_ctx.capable(capability):
                    raise click.ClickException(
                        _(
                            "The type '{plugin}:{resource_type}' "
                            "does not support the '{capability}' capability."
                        ).format(plugin=plugin, resource_type=resource_type, capability=capability)
                    )
        return entity_ctx

    def _multi_option_callback(
        ctx: click.Context, param: click.Parameter, value: Iterable[Optional[str]]
    ) -> Iterable[EntityFieldDefinition]:
        if value:
            return (_option_callback(ctx, param, item) for item in value)
        return tuple()

    if "cls" not in kwargs:
        kwargs["cls"] = PulpOption
    if kwargs.get("multiple"):
        kwargs["callback"] = _multi_option_callback
    else:
        kwargs["callback"] = _option_callback
    return click.option(*args, **kwargs)


limit_option = pulp_option(
    "--limit",
    default=DEFAULT_LIMIT,
    type=click.IntRange(1),
    help=_("Limit the number of {entities} to show."),
)
offset_option = pulp_option(
    "--offset",
    default=0,
    type=int,
    help=_("Skip a number of {entities} to show."),
)

href_option = pulp_option(
    "--href",
    help=_("HREF of the {entity}"),
    callback=_href_callback,
    expose_value=False,
)

name_option = pulp_option(
    "--name",
    help=_("Name of the {entity}"),
    callback=_name_callback,
    expose_value=False,
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

label_select_option = pulp_option(
    "--label-select",
    "pulp_label_select",
    help=_("Filter {entities} by a label search query."),
    type=str,
)

base_path_option = pulp_option(
    "--base-path",
    help=_("Base-path of the {entity}"),
    type=str,
)

base_path_contains_option = pulp_option(
    "--base-path-contains",
    "base_path__icontains",
    help=_("{entity} base-path contains search"),
    type=str,
)

content_in_option = pulp_option(
    "--content",
    "content__in",
    help=_("Search for {entities} with these content hrefs in them (JSON list)"),
    callback=load_json_callback,
)

chunk_size_option = pulp_option(
    "--chunk-size",
    help=_("Chunk size to break up {entity} into. Defaults to 1MB"),
    default="1MB",
    callback=parse_size_callback,
)

pulp_created_gte_option = pulp_option(
    "--created-after",
    "pulp_created__gte",
    help=_("Search for {entities} created at or after this ISO 8601 date"),
    type=str,
)

pulp_created_lte_option = pulp_option(
    "--created-before",
    "pulp_created__lte",
    help=_("Search for {entities} created at or before this ISO 8601 date"),
    type=str,
)

retained_versions_option = pulp_option(
    "--retain-repo-versions",
    needs_plugins=[PluginRequirement("core", "3.13.0.dev")],
    help=_("Number of repository versions to keep."),
)

publication_filter_options = [
    content_in_option,
    pulp_created_gte_option,
    pulp_created_lte_option,
    pulp_option("--repository-version", help=_("Search {entities} by repository version HREF")),
]

common_remote_create_options = [
    click.option("--name", required=True),
    click.option("--url", required=True),
    click.option("--ca-cert", help=_("a PEM encoded CA certificate")),
    click.option("--client-cert", help=_("a PEM encoded client certificate")),
    click.option("--client-key", help=_("a PEM encode private key")),
    click.option("--connect-timeout", type=float),
    click.option(
        "--download-concurrency", type=int, help=_("total number of simultaneous connections")
    ),
    click.option("--password"),
    click.option("--proxy-url"),
    click.option("--proxy-username"),
    click.option("--proxy-password"),
    click.option("--rate-limit", type=int, help=_("limit download rate in requests per second")),
    click.option("--sock-connect-timeout", type=float),
    click.option("--sock-read-timeout", type=float),
    click.option("--tls-validation", type=bool),
    click.option("--total-timeout", type=float),
    click.option("--username"),
]

common_remote_update_options = [
    click.option("--url"),
    click.option("--ca-cert", help=_("a PEM encoded CA certificate")),
    click.option("--client-cert", help=_("a PEM encoded client certificate")),
    click.option("--client-key", help=_("a PEM encode private key")),
    click.option("--connect-timeout", type=float),
    click.option(
        "--download-concurrency", type=int, help=_("total number of simultaneous connections")
    ),
    click.option("--password"),
    click.option("--proxy-url"),
    click.option("--proxy-username"),
    click.option("--proxy-password"),
    click.option("--rate-limit", type=int, help=_("limit download rate in requests per second")),
    click.option("--sock-connect-timeout", type=float),
    click.option("--sock-read-timeout", type=float),
    click.option("--tls-validation", type=bool),
    click.option("--total-timeout", type=float),
    click.option("--username"),
]

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
    need_plugins = kwargs.pop("need_plugins", [])

    @click.group(**kwargs)
    @pass_pulp_context
    def label_group(pulp_ctx: PulpContext) -> None:
        for item in need_plugins:
            pulp_ctx.needs_plugin(item)

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


def repository_content_command(**kwargs: Any) -> click.Group:
    """A factory that creates a repository content command group."""

    content_contexts = kwargs.pop("contexts", {})
    names = list(content_contexts.keys()) + ["all"]
    content_contexts.update({"all": PulpContentContext})

    def version_callback(
        ctx: click.Context, param: click.Parameter, value: Optional[int]
    ) -> PulpRepositoryVersionContext:
        repo_ctx = ctx.find_object(PulpRepositoryContext)
        assert repo_ctx is not None
        repo_ver_ctx = repo_ctx.get_version_context()
        repo_ver_ctx.pulp_href = (
            f"{repo_ctx.pulp_href}versions/{value}/"
            if value
            else repo_ctx.entity["latest_version_href"]
        )
        return repo_ver_ctx

    @click.command("list")
    @click.option("-t", "--type", "type", type=click.Choice(names), default=names[0])
    @limit_option
    @offset_option
    @repository_option
    @click.option("--version", type=int, callback=version_callback)
    @pass_pulp_context
    def content_list(
        pulp_ctx: PulpContext,
        version: PulpRepositoryVersionContext,
        offset: Optional[int],
        limit: Optional[int],
        type: Optional[str],
        **params: Any,
    ) -> None:
        parameters = {k: v for k, v in params.items() if v is not None}
        parameters.update({"repository_version": version.pulp_href})
        result = content_contexts[type](pulp_ctx).list(
            limit=limit, offset=offset, parameters=parameters
        )
        pulp_ctx.output_result(result)

    @click.command("add")
    @repository_option
    @click.option("--base-version", type=int, callback=version_callback)
    @pass_content_context
    def content_add(
        content_ctx: PulpContentContext,
        base_version: PulpRepositoryVersionContext,
    ) -> None:
        repo_ctx = base_version.repository_ctx
        repo_ctx.modify(
            repo_ctx.pulp_href,
            add_content=[content_ctx.pulp_href],
            base_version=base_version.pulp_href,
        )

    @click.command("remove")
    @click.option("--all", is_flag=True, help=_("Remove all content from repository version"))
    @repository_option
    @click.option("--base-version", type=int, callback=version_callback)
    @pass_content_context
    def content_remove(
        content_ctx: PulpContentContext,
        base_version: PulpRepositoryVersionContext,
        all: bool,
    ) -> None:
        repo_ctx = base_version.repository_ctx
        remove_content = ["*" if all else content_ctx.pulp_href]
        repo_ctx.modify(
            repo_ctx.pulp_href, remove_content=remove_content, base_version=base_version.pulp_href
        )

    @click.command("modify")
    @repository_option
    @click.option("--base-version", type=int, callback=version_callback)
    def content_modify(
        base_version: PulpRepositoryVersionContext,
        add_content: Optional[List[PulpContentContext]],
        remove_content: Optional[List[PulpContentContext]],
    ) -> None:
        repo_ctx = base_version.repository_ctx
        ac = [unit.pulp_href for unit in add_content] if add_content else None
        rc = [unit.pulp_href for unit in remove_content] if remove_content else None
        repo_ctx.modify(repo_ctx.pulp_href, ac, rc, base_version.pulp_href)

    command_decorators = {
        content_list: kwargs.pop("list_decorators", []),
        content_add: kwargs.pop("add_decorators", []),
        content_remove: kwargs.pop("remove_decorators", []),
        content_modify: kwargs.pop("modify_decorators", []),
    }
    if not kwargs.get("name"):
        kwargs["name"] = "content"

    @click.group(**kwargs)
    @pass_pulp_context
    @click.pass_context
    def content_group(ctx: click.Context, pulp_ctx: PulpContext) -> None:
        ctx.obj = PulpContentContext(pulp_ctx)

    for command, options in command_decorators.items():
        for option in options:
            command = option(command)
        content_group.add_command(command)

    return content_group
