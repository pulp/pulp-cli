import datetime
import json
import re
import typing as t
from functools import lru_cache, wraps

import click
import schema as s
import yaml
from pulp_glue.common.context import (
    DATETIME_FORMATS,
    DEFAULT_LIMIT,
    EntityDefinition,
    EntityFieldDefinition,
    PluginRequirement,
    PulpACSContext,
    PulpContentContext,
    PulpContentGuardContext,
    PulpContext,
    PulpDistributionContext,
    PulpEntityContext,
    PulpException,
    PulpNoWait,
    PulpRemoteContext,
    PulpRepositoryContext,
    PulpRepositoryVersionContext,
)
from pulp_glue.common.i18n import get_translation

try:
    from pygments import highlight
    from pygments.formatters import Terminal256Formatter
    from pygments.lexers import JsonLexer, YamlLexer
except ImportError:
    PYGMENTS = False
else:
    PYGMENTS = True
    PYGMENTS_STYLE = "solarized-dark"

translation = get_translation(__name__)
_ = translation.gettext


_AnyCallable = t.Callable[..., t.Any]
FC = t.TypeVar("FC", bound=t.Union[_AnyCallable, click.Command])


class IncompatibleContext(click.UsageError):
    pass


class ClickNoWait(click.ClickException):
    exit_code = 0

    def show(self, file: t.Optional[t.IO[str]] = None) -> None:
        """
        Format the message into file or STDERR.
        Overwritten from base class to not print "Error: ".
        """
        if file is None:
            file = click.get_text_stream("stderr")
        click.echo(self.format_message(), file=file)


class PulpJSONEncoder(json.JSONEncoder):
    def default(self, obj: t.Any) -> t.Any:
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        else:
            return super().default(obj)


class PulpCLIContext(PulpContext):
    """
    Subclass of the Context that overwrites the CLI specifics.
    """

    def __init__(
        self,
        api_root: str,
        api_kwargs: t.Dict[str, t.Any],
        background_tasks: bool,
        timeout: int,
        format: str,
        domain: str = "default",
    ) -> None:
        super().__init__(
            api_root=api_root,
            api_kwargs=api_kwargs,
            background_tasks=background_tasks,
            timeout=timeout,
            domain=domain,
        )
        self.format = format

    def echo(self, message: str, nl: bool = True, err: bool = False) -> None:
        click.echo(message, nl=nl, err=err)

    def prompt(self, text: str, hide_input: bool = False) -> t.Any:
        return click.prompt(text, hide_input=hide_input)

    def output_result(self, result: t.Any) -> None:
        """
        Dump the provided result to the console using the selected renderer
        """
        if self.format == "json":
            output = json.dumps(result, cls=PulpJSONEncoder, indent=(2 if self.isatty else None))
            if PYGMENTS and self.isatty:
                output = highlight(output, JsonLexer(), Terminal256Formatter(style=PYGMENTS_STYLE))
            self.echo(output)
        elif self.format == "yaml":
            output = yaml.dump(result)
            if PYGMENTS and self.isatty:
                output = highlight(output, YamlLexer(), Terminal256Formatter(style=PYGMENTS_STYLE))
            self.echo(output)
        elif self.format == "none":
            pass
        else:
            raise NotImplementedError(
                _("Format '{format}' not implemented.").format(format=self.format)
            )


##############################################################################
# Decorator to access certain contexts


pass_pulp_context = click.make_pass_decorator(PulpCLIContext)
pass_entity_context = click.make_pass_decorator(PulpEntityContext)
pass_acs_context = click.make_pass_decorator(PulpACSContext)
pass_content_context = click.make_pass_decorator(PulpContentContext)
pass_repository_context = click.make_pass_decorator(PulpRepositoryContext)
pass_repository_version_context = click.make_pass_decorator(PulpRepositoryVersionContext)


##############################################################################
# Custom types for parameters


def int_or_empty(value: str) -> t.Union[str, int]:
    if value == "":
        return ""
    else:
        return int(value)


int_or_empty.__name__ = "int or empty"


def float_or_empty(value: str) -> t.Union[str, float]:
    if value == "":
        return ""
    else:
        return float(value)


float_or_empty.__name__ = "float or empty"


##############################################################################
# Custom classes for commands and parameters


class PulpCommand(click.Command):
    def __init__(
        self,
        *args: t.Any,
        allowed_with_contexts: t.Optional[t.Tuple[t.Type[PulpEntityContext]]] = None,
        needs_plugins: t.Optional[t.List[PluginRequirement]] = None,
        **kwargs: t.Any,
    ):
        self.allowed_with_contexts = allowed_with_contexts
        self.needs_plugins = needs_plugins
        super().__init__(*args, **kwargs)

    def invoke(self, ctx: click.Context) -> t.Any:
        try:
            if self.needs_plugins:
                pulp_ctx = ctx.find_object(PulpCLIContext)
                assert pulp_ctx is not None
                for plugin_requirement in self.needs_plugins:
                    pulp_ctx.needs_plugin(plugin_requirement)
            return super().invoke(ctx)
        except PulpException as e:
            raise click.ClickException(str(e))
        except PulpNoWait as e:
            raise ClickNoWait(str(e))

    def get_short_help_str(self, limit: int = 45) -> str:
        return self.short_help or ""

    def format_help_text(
        self, ctx: click.Context, formatter: click.formatting.HelpFormatter
    ) -> None:
        if self.help is not None:
            entity_ctx = ctx.find_object(PulpEntityContext)
            if entity_ctx is not None:
                self.help = self.help.format(entity=entity_ctx.ENTITY, entities=entity_ctx.ENTITIES)
        super().format_help_text(ctx, formatter)

    def get_params(self, ctx: click.Context) -> t.List[click.Parameter]:
        params = super().get_params(ctx)
        new_params: t.List[click.Parameter] = []
        for param in params:
            if isinstance(param, PulpOption):
                if param.allowed_with_contexts is not None:
                    if not isinstance(ctx.obj, param.allowed_with_contexts):
                        continue
            new_params.append(param)
        return new_params


class PulpGroup(PulpCommand, click.Group):
    command_class = PulpCommand
    group_class = type

    def get_command(self, ctx: click.Context, cmd_name: str) -> t.Optional[click.Command]:
        # Overwriting this removes the command from the help message and from being callable
        cmd = super().get_command(ctx, cmd_name)
        if isinstance(cmd, (PulpCommand, PulpGroup)):
            if cmd.allowed_with_contexts is not None:
                if not isinstance(ctx.obj, cmd.allowed_with_contexts):
                    raise IncompatibleContext(
                        _("The subcommand '{name}' is not available in this context.").format(
                            name=cmd.name
                        )
                    )
        return cmd

    def list_commands(self, ctx: click.Context) -> t.List[str]:
        commands_filtered_by_context = []

        for name, cmd in self.commands.items():
            if isinstance(cmd, (PulpCommand, PulpGroup)):
                if cmd.allowed_with_contexts is None or isinstance(
                    ctx.obj, cmd.allowed_with_contexts
                ):
                    commands_filtered_by_context.append(name)

        return sorted(commands_filtered_by_context)


def pulp_command(
    name: t.Optional[str] = None, **kwargs: t.Any
) -> t.Callable[[_AnyCallable], PulpCommand]:
    return click.command(name=name, cls=PulpCommand, **kwargs)


def pulp_group(
    name: t.Optional[str] = None, **kwargs: t.Any
) -> t.Callable[[_AnyCallable], PulpGroup]:
    return click.group(name=name, cls=PulpGroup, **kwargs)


class PulpOption(click.Option):
    def __init__(
        self,
        *args: t.Any,
        needs_plugins: t.Optional[t.List[PluginRequirement]] = None,
        allowed_with_contexts: t.Optional[t.Tuple[t.Type[PulpEntityContext]]] = None,
        **kwargs: t.Any,
    ):
        self.needs_plugins = needs_plugins
        self.allowed_with_contexts = allowed_with_contexts
        super().__init__(*args, **kwargs)

    def process_value(self, ctx: click.Context, value: t.Any) -> t.Any:
        if self.needs_plugins and value is not None and value != ():
            pulp_ctx = ctx.find_object(PulpCLIContext)
            assert pulp_ctx is not None
            for plugin_requirement in self.needs_plugins:
                if not plugin_requirement.feature:
                    plugin_requirement = PluginRequirement(
                        plugin_requirement.name,
                        specifier=plugin_requirement.specifier,
                        feature=_("the {name} option").format(name=self.name),
                        inverted=plugin_requirement.inverted,
                    )

                pulp_ctx.needs_plugin(plugin_requirement)
        return super().process_value(ctx, value)

    def get_help_record(self, ctx: click.Context) -> t.Optional[t.Tuple[str, str]]:
        tmp = super().get_help_record(ctx)
        if tmp is None:
            return None
        synopsis, help_text = tmp
        entity_ctx = ctx.find_object(PulpEntityContext)
        if entity_ctx is not None:
            help_text = help_text.format(entity=entity_ctx.ENTITY, entities=entity_ctx.ENTITIES)
        return synopsis, help_text


class GroupOption(PulpOption):
    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
        self.group: t.List[str] = kwargs.pop("group")
        assert self.group, "'group' parameter required"
        kwargs["help"] = (
            kwargs.get("help", "")
            + " "
            + _("Option is grouped with {option_list}.").format(option_list=", ".join(self.group))
        ).strip()
        super().__init__(*args, **kwargs)

    def handle_parse_result(
        self, ctx: click.Context, opts: t.Mapping[str, t.Any], args: t.List[t.Any]
    ) -> t.Any:
        assert self.name is not None
        all_options = self.group + [self.name]
        options_present = [x for x in all_options if x in opts]
        num_options = len(options_present)
        if num_options != len(all_options) and (num_options != 0 or self.required):
            raise click.UsageError(
                _("Illegal usage, please specify all options in the group: {option_list}").format(
                    option_list=", ".join(all_options)
                )
            )
        self.prompt = None
        value = opts.get(self.name)
        if self.callback is not None and num_options != 0:
            value = self.callback(ctx, self, {o: opts[o] for o in options_present})
        if self.expose_value:
            ctx.params[self.name] = value
        return value, args


##############################################################################
# Option callbacks


@lru_cache(typed=True)
def lookup_callback(
    attribute: str, context_class: t.Type[PulpEntityContext] = PulpEntityContext
) -> t.Callable[[click.Context, click.Parameter, t.Optional[str]], t.Optional[str]]:
    def _callback(
        ctx: click.Context, param: click.Parameter, value: t.Optional[str]
    ) -> t.Optional[str]:
        if value is not None:
            if value == "":
                value = "null"
            entity_ctx = ctx.find_object(context_class)
            assert entity_ctx is not None
            entity_ctx.entity = {attribute: value}
        return value

    return _callback


def href_callback(
    context_class: t.Type[PulpEntityContext] = PulpEntityContext,
) -> t.Callable[[click.Context, click.Parameter, t.Optional[str]], t.Optional[str]]:
    def _href_callback(
        ctx: click.Context, param: click.Parameter, value: t.Optional[str]
    ) -> t.Optional[str]:
        if value is not None:
            entity_ctx = ctx.find_object(context_class)
            assert entity_ctx is not None
            entity_ctx.pulp_href = value
        return value

    return _href_callback


def _version_callback(
    ctx: click.Context, param: click.Parameter, value: t.Optional[int]
) -> t.Optional[int]:
    entity_ctx = ctx.find_object(PulpEntityContext)
    assert entity_ctx is not None
    repository_ctx = ctx.find_object(PulpRepositoryContext)
    assert repository_ctx is not None
    if value is not None:
        entity_ctx.pulp_href = f"{repository_ctx.entity['versions_href']}{value}/"
    else:
        entity_ctx.pulp_href = repository_ctx.entity["latest_version_href"]
    return value


def load_file_wrapper(handler: t.Callable[[click.Context, click.Parameter, str], t.Any]) -> t.Any:
    """A wrapper that used for chaining or decorating callbacks that manipulate with input data."""

    @wraps(handler)
    def _load_file_or_string_wrapper(
        ctx: click.Context, param: click.Parameter, value: t.Optional[str]
    ) -> t.Any:
        """Load the string from input, or from file if the value starts with @."""
        if not value:
            return value

        if value.startswith("@"):
            the_file = value[1:]
            try:
                with click.open_file(the_file, "r") as fp:
                    the_content = fp.read()
            except OSError:
                raise click.ClickException(
                    _("Failed to load content from {file}").format(file=the_file)
                )
        else:
            the_content = value

        return handler(ctx, param, the_content)

    return _load_file_or_string_wrapper


load_string_callback = load_file_wrapper(lambda c, p, x: x)


def json_callback(ctx: click.Context, param: click.Parameter, value: t.Optional[str]) -> t.Any:
    if value is None:
        return None

    try:
        json_object = json.loads(value)
    except json.decoder.JSONDecodeError:
        raise click.ClickException(_("Failed to decode JSON"))
    else:
        return json_object


load_json_callback = load_file_wrapper(json_callback)


def load_labels_callback(
    ctx: click.Context, param: click.Parameter, value: t.Optional[str]
) -> t.Optional[t.Dict[str, str]]:
    if value is None:
        return value

    value = load_json_callback(ctx, param, value)
    if isinstance(value, dict) and all(
        (isinstance(key, str) and isinstance(val, str) for key, val in value.items())
    ):
        return value
    raise click.ClickException(_("Labels must be provided as a dictionary of strings."))


def create_content_json_callback(
    context_class: t.Optional[t.Type[PulpContentContext]] = None, schema: s.Schema = None
) -> t.Any:
    @load_file_wrapper
    def _callback(
        ctx: click.Context, param: click.Parameter, value: str
    ) -> t.Optional[t.List[PulpContentContext]]:
        ctx_class = context_class
        new_value = json_callback(ctx, param, value)
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
            pulp_ctx = ctx.find_object(PulpCLIContext)
            assert pulp_ctx is not None
            if ctx_class is None:
                context = ctx.find_object(PulpContentContext)
                assert context is not None
                ctx_class = type(context)
            return [ctx_class(pulp_ctx, entity=unit) for unit in new_value]
        return new_value

    return _callback


# based on https://stackoverflow.com/a/42865957/2002471
units = {"B": 1, "KB": 10**3, "MB": 10**6, "GB": 10**9, "TB": 10**12}


def parse_size_callback(ctx: click.Context, param: click.Parameter, value: str) -> int:
    size = value.strip().upper()
    match = re.match(r"^([0-9]+)\s*([KMGT]?B)?$", size)
    if not match:
        raise click.ClickException("Please pass in a valid size of form: [0-9] [K/M/G/T]B")
    number, unit = match.groups(default="B")
    return int(float(number) * units[unit])


def null_callback(
    ctx: click.Context, param: click.Parameter, value: t.Optional[str]
) -> t.Optional[str]:
    if value == "":
        return "null"
    return value


##############################################################################
# Decorator common options


def pulp_option(*args: t.Any, **kwargs: t.Any) -> t.Callable[[FC], FC]:
    kwargs["cls"] = PulpOption
    return click.option(*args, **kwargs)


domain_pattern = r"(?P<pulp_domain>[-a-zA-Z0-9_]+)"


def resource_lookup_option(*args: t.Any, **kwargs: t.Any) -> t.Callable[[FC], FC]:
    lookup_key: str = kwargs.pop("lookup_key", "name")
    context_class: t.Type[PulpEntityContext] = kwargs.pop("context_class")

    def _option_callback(
        ctx: click.Context, param: click.Parameter, value: t.Optional[str]
    ) -> EntityFieldDefinition:
        # Pass None and "" verbatim
        if not value:
            return value

        pulp_ctx = ctx.find_object(PulpCLIContext)
        assert pulp_ctx is not None

        entity_ctx = ctx.find_object(context_class)
        assert entity_ctx is not None

        if value.startswith("/"):
            # The HREF of a resource was passed
            href_pattern = entity_ctx.HREF_PATTERN
            if pulp_ctx.domain_enabled:
                pattern = rf"^{pulp_ctx._api_root}{domain_pattern}/api/v3/{href_pattern}"
            else:
                pattern = rf"^{pulp_ctx.api_path}{href_pattern}"
            match = re.match(pattern, value)
            if match:
                entity_ctx.pulp_href = value
            else:
                raise click.ClickException(
                    _("'{value}' is not a valid href for {option_name}.").format(
                        value=value, option_name=param.name
                    )
                )
        else:
            # The named identity of a resource was passed
            entity_ctx.entity = {lookup_key: value}

        return entity_ctx

    if "cls" not in kwargs:
        kwargs["cls"] = PulpOption
    kwargs["callback"] = _option_callback

    kwargs["expose_value"] = False

    if "help" not in kwargs:
        kwargs["help"] = _(
            "A resource to look for identified by <{lookup_key}> or by <href>."
        ).format(lookup_key=lookup_key)

    return click.option(*args, **kwargs)


def resource_option(*args: t.Any, **kwargs: t.Any) -> t.Callable[[FC], FC]:
    default_plugin: t.Optional[str] = kwargs.pop("default_plugin", None)
    default_type: t.Optional[str] = kwargs.pop("default_type", None)
    lookup_key: str = kwargs.pop("lookup_key", "name")
    context_table: t.Dict[str, t.Type[PulpEntityContext]] = kwargs.pop("context_table")
    capabilities: t.Optional[t.List[str]] = kwargs.pop("capabilities", None)
    href_pattern: t.Optional[str] = kwargs.pop("href_pattern", None)
    parent_resource_lookup: t.Optional[t.Tuple[str, t.Type[PulpEntityContext]]] = kwargs.pop(
        "parent_resource_lookup", None
    )

    def _option_callback(
        ctx: click.Context, param: click.Parameter, value: t.Optional[str]
    ) -> EntityFieldDefinition:
        # Pass None and "" verbatim
        if not value:
            return value

        pulp_href: t.Optional[str] = None
        entity: t.Optional[EntityDefinition] = None

        pulp_ctx = ctx.find_object(PulpCLIContext)
        assert pulp_ctx is not None

        if value.startswith("/"):
            # An href was passed
            if href_pattern is None:
                raise click.ClickException(
                    _("The option {option_name} does not support href.").format(
                        option_name=param.name
                    )
                )
            if pulp_ctx.domain_enabled:
                pattern = rf"^{pulp_ctx._api_root}{domain_pattern}/api/v3/{href_pattern}"
            else:
                pattern = rf"^{pulp_ctx.api_path}{href_pattern}"
            match = re.match(pattern, value)
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

        if parent_resource_lookup:
            parent_lookup_key, parent_context_type = parent_resource_lookup
            parent_ctx = ctx.find_object(parent_context_type)
            assert parent_ctx is not None
            parent_ctx.entity = {parent_lookup_key: entity_ctx}

        return entity_ctx

    def _multi_option_callback(
        ctx: click.Context, param: click.Parameter, value: t.Iterable[t.Optional[str]]
    ) -> t.Iterable[EntityFieldDefinition]:
        if value:
            return (_option_callback(ctx, param, item) for item in value)
        return tuple()

    if "cls" not in kwargs:
        kwargs["cls"] = PulpOption
    if kwargs.get("multiple"):
        kwargs["callback"] = _multi_option_callback
    else:
        kwargs["callback"] = _option_callback

    if "help" not in kwargs:
        kwargs["help"] = _(
            "Referenced resource, in the form {plugin_form}{type_form}<name> or by href. "
            "{plugin_default}{type_default}"
        ).format(
            plugin_form=_("[<plugin>:]") if default_plugin else _("<plugin>:"),
            type_form=_("[<resource_type>:]") if default_type else _("<resource_type>:"),
            plugin_default=_("'<plugin>' defaults to {plugin}. ").format(plugin=default_plugin)
            if default_plugin
            else "",
            type_default=_("'<resource_type>' defaults to {type}. ").format(type=default_type)
            if default_type
            else "",
        )

    return click.option(*args, **kwargs)


def type_option(*args: t.Any, **kwargs: t.Any) -> t.Callable[[FC], FC]:
    choices: t.Dict[str, t.Type[PulpEntityContext]] = kwargs.pop("choices")
    assert choices and isinstance(choices, dict)
    type_names = list(choices.keys())
    case_sensitive = kwargs.pop("case_sensitive", False)
    defaults = {
        "cls": PulpOption,
        "default": type_names[0],
        "is_eager": True,
        "expose_value": False,
    }

    def _type_callback(ctx: click.Context, param: click.Parameter, value: t.Optional[str]) -> str:
        pulp_ctx = ctx.find_object(PulpCLIContext)
        assert pulp_ctx
        if value is not None:
            cls = choices[value]
            assert issubclass(cls, PulpEntityContext)
            ctx.obj = cls(pulp_ctx)
            return value
        raise NotImplementedError()

    for k, v in defaults.items():
        if k not in kwargs:
            kwargs[k] = v
    if not args:
        args = ("-t", "--type", "entity_type")
    kwargs["callback"] = _type_callback
    kwargs["type"] = click.types.Choice(type_names, case_sensitive=case_sensitive)
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

ordering_option = pulp_option(
    "--ordering",
    multiple=True,
    required=False,
    help=_("A field that will be used to order the results. Can be specified multiple times."),
)

field_option = pulp_option(
    "--field",
    "fields",
    multiple=True,
    required=False,
    help=_("A field that is to be selected from a result. Can be specified multiple times."),
)

exclude_field_option = pulp_option(
    "--exclude-field",
    "exclude_fields",
    multiple=True,
    required=False,
    help=_("A field that is to be excluded from a result. Can be specified multiple times."),
)

href_option = pulp_option(
    "--href",
    help=_("HREF of the {entity}"),
    callback=href_callback(),
    expose_value=False,
)

name_option = pulp_option(
    "--name",
    help=_("Name of the {entity}"),
    callback=lookup_callback("name"),
    expose_value=False,
)

name_filter_option = pulp_option(
    "--name",
    help=_("Filter {entity} by exact name"),
)

name_contains_option = pulp_option(
    "--name-contains",
    "name__contains",
    help=_("Filter {entity} results where name contains value"),
)

name_icontains_option = pulp_option(
    "--name-icontains",
    "name__icontains",
    help=_("Filter {entity} results where name contains value, case insensitive"),
)

name_in_option = pulp_option(
    "--name-in",
    "name__in",
    multiple=True,
    help=_("Filter {entity} by name. Can be specified multiple times"),
)

repository_href_option = click.option(
    "--repository-href",
    help=_("HREF of the repository"),
    callback=href_callback(PulpRepositoryContext),
    expose_value=False,
)

repository_option = click.option(
    "--repository",
    help=_("Name of the repository"),
    callback=lookup_callback("name", PulpRepositoryContext),
    expose_value=False,
)

repository_lookup_option = resource_lookup_option(
    "--repository",
    context_class=PulpRepositoryContext,
)
remote_lookup_option = resource_lookup_option(
    "--remote",
    context_class=PulpRemoteContext,
)
distribution_lookup_option = resource_lookup_option(
    "--distribution",
    context_class=PulpDistributionContext,
)
acs_lookup_option = resource_lookup_option(
    "--acs",
    context_class=PulpACSContext,
)

content_guard_option = resource_option(
    "--content-guard",
    context_table=PulpContentGuardContext.TYPE_REGISTRY,
    href_pattern=PulpContentGuardContext.HREF_PATTERN,
    help=_(
        "Content Guard used to protect the distribution."
        " Specified as '<plugin>:<type>:<name>' or as href."
    ),
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
    help=_(
        "Search for {entities} with these content hrefs in them (JSON list or "
        "@file containing a JSON list)"
    ),
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
    help=_("Search for {entities} created at or after this date"),
    type=click.DateTime(formats=DATETIME_FORMATS),
)

pulp_created_lte_option = pulp_option(
    "--created-before",
    "pulp_created__lte",
    help=_("Search for {entities} created at or before this date"),
    type=click.DateTime(formats=DATETIME_FORMATS),
)

pulp_last_updated_gte_option = pulp_option(
    "--updated-after",
    "pulp_last_updated__gte",
    help=_("Search for {entities} last updated at or after this date"),
    type=click.DateTime(formats=DATETIME_FORMATS),
)

pulp_last_updated_lte_option = pulp_option(
    "--updated-before",
    "pulp_last_updated__lte",
    help=_("Search for {entities} last updated at or before this date"),
    type=click.DateTime(formats=DATETIME_FORMATS),
)

retained_versions_option = pulp_option(
    "--retain-repo-versions",
    needs_plugins=[PluginRequirement("core", specifier=">=3.13.0")],
    help=_("Number of repository versions to keep."),
    type=int,
)

pulp_labels_option = pulp_option(
    "--labels",
    "pulp_labels",
    help=_(
        "JSON dictionary of labels to set on {entity} (or " "@file containing a JSON dictionary)"
    ),
    callback=load_labels_callback,
)

name_filter_options = [
    name_filter_option,
    name_contains_option,
    name_icontains_option,
    name_in_option,
]

remote_filter_options = name_filter_options + [
    label_select_option,
    pulp_last_updated_gte_option,
    pulp_last_updated_lte_option,
]

distribution_filter_options = name_filter_options + [
    label_select_option,
    base_path_option,
    base_path_contains_option,
]

common_distribution_create_options = [
    click.option("--name", required=True),
    click.option("--base-path", required=True),
]

publication_filter_options = [
    content_in_option,
    pulp_created_gte_option,
    pulp_created_lte_option,
    pulp_option("--repository-version", help=_("Search {entities} by repository version HREF")),
]


common_remote_create_options = [
    click.option("--name", required=True),
    click.option("--url", required=True),
    click.option(
        "--ca-cert",
        help=_("a PEM encoded CA certificate or @file containing same"),
        callback=load_string_callback,
    ),
    click.option(
        "--client-cert",
        help=_("a PEM encoded client certificate or @file containing same"),
        callback=load_string_callback,
    ),
    click.option(
        "--client-key",
        help=_("a PEM encode private key or @file containing same"),
        callback=load_string_callback,
    ),
    click.option("--connect-timeout", type=float),
    click.option(
        "--download-concurrency", type=int, help=_("total number of simultaneous connections")
    ),
    click.option(
        "--password",
        help=_(
            "The password to authenticate to the remote (can contain leading and trailing spaces)."
        ),
    ),
    click.option("--proxy-url"),
    click.option("--proxy-username"),
    click.option(
        "--proxy-password",
        help=_(
            "The password to authenticate to the proxy (can contain leading and trailing spaces)."
        ),
    ),
    click.option("--rate-limit", type=int, help=_("limit download rate in requests per second")),
    click.option("--sock-connect-timeout", type=float),
    click.option("--sock-read-timeout", type=float),
    click.option("--tls-validation", type=bool),
    click.option("--total-timeout", type=float),
    click.option("--username"),
    click.option(
        "--max-retries",
        type=int,
        help=_("maximum number of retry attemts after a download failure"),
    ),
    pulp_labels_option,
]


common_remote_update_options = [
    click.option("--url"),
    click.option(
        "--ca-cert",
        help=_("a PEM encoded CA certificate or @file containing same"),
        callback=load_string_callback,
    ),
    click.option(
        "--client-cert",
        help=_("a PEM encoded client certificate or @file containing same"),
        callback=load_string_callback,
    ),
    click.option(
        "--client-key",
        help=_("a PEM encode private key or @file containing same"),
        callback=load_string_callback,
    ),
    click.option("--connect-timeout", type=float_or_empty),
    click.option(
        "--download-concurrency",
        type=int_or_empty,
        help=_("total number of simultaneous connections"),
    ),
    click.option(
        "--password",
        help=_(
            "The password to authenticate to the remote (can contain leading and trailing spaces)."
        ),
    ),
    click.option("--proxy-url"),
    click.option("--proxy-username"),
    click.option(
        "--proxy-password",
        help=_(
            "The password to authenticate to the proxy (can contain leading and trailing spaces)."
        ),
    ),
    click.option(
        "--rate-limit", type=int_or_empty, help=_("limit download rate in requests per second")
    ),
    click.option("--sock-connect-timeout", type=float_or_empty),
    click.option("--sock-read-timeout", type=float_or_empty),
    click.option("--tls-validation", type=bool),
    click.option("--total-timeout", type=float_or_empty),
    click.option("--username"),
    click.option(
        "--max-retries",
        type=int_or_empty,
        help=_("maximum number of retry attemts after a download failure"),
    ),
    pulp_labels_option,
]

##############################################################################
# Generic reusable commands


def list_command(**kwargs: t.Any) -> click.Command:
    """A factory that creates a list command."""

    kwargs.setdefault("name", "list")
    kwargs.setdefault("help", _("Show the list of optionally filtered {entities}."))
    decorators = kwargs.pop("decorators", [])

    # This is a mypy bug getting confused with positional args
    # https://github.com/python/mypy/issues/15037
    @pulp_command(**kwargs)  # type: ignore [arg-type]
    @limit_option
    @offset_option
    @ordering_option
    @field_option
    @exclude_field_option
    @pass_entity_context
    @pass_pulp_context
    def callback(
        pulp_ctx: PulpCLIContext,
        entity_ctx: PulpEntityContext,
        limit: int,
        offset: int,
        **kwargs: t.Any,
    ) -> None:
        """
        Show the list of optionally filtered {entities}.
        """
        if "ordering" in kwargs:
            # Workaround for missing ordering filter
            if not kwargs["ordering"]:
                kwargs["ordering"] = None
        result = entity_ctx.list(limit=limit, offset=offset, parameters=kwargs)
        pulp_ctx.output_result(result)

    for option in decorators:
        # Decorate callback
        callback = option(callback)
    return callback


def show_command(**kwargs: t.Any) -> click.Command:
    """A factory that creates a show command."""

    if "name" not in kwargs:
        kwargs["name"] = "show"
    if "help" not in kwargs:
        kwargs["help"] = _("Show details of a {entity}.")
    decorators = kwargs.pop("decorators", [])

    @pulp_command(**kwargs)
    @pass_entity_context
    @pass_pulp_context
    def callback(pulp_ctx: PulpCLIContext, entity_ctx: PulpEntityContext) -> None:
        """
        Show details of a {entity}.
        """
        pulp_ctx.output_result(entity_ctx.entity)

    for option in decorators:
        # Decorate callback
        callback = option(callback)
    return callback


def create_command(**kwargs: t.Any) -> click.Command:
    """A factory that creates a create command."""

    if "name" not in kwargs:
        kwargs["name"] = "create"
    if "help" not in kwargs:
        kwargs["help"] = _("Create a {entity}.")
    decorators = kwargs.pop("decorators", [])

    # This is a mypy bug getting confused with positional args
    # https://github.com/python/mypy/issues/15037
    @pulp_command(**kwargs)  # type: ignore [arg-type]
    @pass_entity_context
    @pass_pulp_context
    def callback(pulp_ctx: PulpCLIContext, entity_ctx: PulpEntityContext, **kwargs: t.Any) -> None:
        """
        Create a {entity}.
        """
        result = entity_ctx.create(body=kwargs)
        if "created_resources" in result:
            entity_ctx.pulp_href = result["created_resources"][0]
            result = entity_ctx.entity
        pulp_ctx.output_result(result)

    for option in decorators:
        # Decorate callback
        callback = option(callback)
    return callback


def update_command(**kwargs: t.Any) -> click.Command:
    """A factory that creates an update command."""

    if "name" not in kwargs:
        kwargs["name"] = "update"
    if "help" not in kwargs:
        kwargs["help"] = _("Update a {entity}.")
    decorators = kwargs.pop("decorators", [])

    # This is a mypy bug getting confused with positional args
    # https://github.com/python/mypy/issues/15037
    @pulp_command(**kwargs)  # type: ignore [arg-type]
    @pass_entity_context
    @pass_pulp_context
    def callback(pulp_ctx: PulpCLIContext, entity_ctx: PulpEntityContext, **kwargs: t.Any) -> None:
        """
        Update a {entity}.
        """
        entity_ctx.update(body=kwargs)

    for option in decorators:
        # Decorate callback
        callback = option(callback)
    return callback


def destroy_command(**kwargs: t.Any) -> click.Command:
    """A factory that creates a destroy command."""

    kwargs.setdefault("name", "destroy")
    kwargs.setdefault("help", _("Destroy a {entity}."))
    decorators = kwargs.pop("decorators", [])

    @pulp_command(**kwargs)
    @pass_entity_context
    def callback(entity_ctx: PulpEntityContext) -> None:
        """
        Destroy a {entity}.
        """
        entity_ctx.delete()

    for option in decorators:
        # Decorate callback
        callback = option(callback)
    return callback


def version_command(**kwargs: t.Any) -> click.Command:
    """A factory that creates a repository version command group."""

    kwargs.setdefault("name", "version")
    decorators = kwargs.pop("decorators", [repository_href_option, repository_option])
    list_only = kwargs.pop("list_only", False)

    @pulp_group(**kwargs)
    @pass_repository_context
    @click.pass_context
    def callback(
        ctx: click.Context,
        repository_ctx: PulpRepositoryContext,
    ) -> None:
        ctx.obj = repository_ctx.get_version_context()

    callback.add_command(list_command(decorators=decorators + [content_in_option]))

    if not list_only:
        callback.add_command(show_command(decorators=decorators + [version_option]))
        callback.add_command(destroy_command(decorators=decorators + [version_option]))

        @callback.command()
        @repository_option
        @version_option
        @pass_repository_version_context
        @pass_pulp_context
        def repair(
            pulp_ctx: PulpCLIContext,
            repository_version_ctx: PulpRepositoryVersionContext,
        ) -> None:
            result = repository_version_ctx.repair()
            pulp_ctx.output_result(result)

    return callback


def label_command(**kwargs: t.Any) -> click.Command:
    """A factory that creates a label command group."""

    kwargs.setdefault("name", "label")
    decorators = kwargs.pop("decorators", [name_option, href_option])
    need_plugins = kwargs.pop("need_plugins", [])

    @pulp_group(**kwargs)
    @pass_pulp_context
    def label_group(pulp_ctx: PulpCLIContext) -> None:
        for item in need_plugins:
            pulp_ctx.needs_plugin(item)

    @pulp_command(name="set", help=_("Add or update a label"))
    @click.option("--key", required=True, help=_("Key of the label"))
    @click.option("--value", required=True, help=_("Value of the label"))
    @pass_entity_context
    def label_set(entity_ctx: PulpEntityContext, key: str, value: str) -> None:
        """Add or update a label"""
        entity_ctx.set_label(key, value)

    @pulp_command(name="unset", help=_("Remove a label with a given key"))
    @click.option("--key", required=True, help=_("Key of the label"))
    @pass_entity_context
    def label_unset(entity_ctx: PulpEntityContext, key: str) -> None:
        """Remove a label with a given key"""
        entity_ctx.unset_label(key)

    @pulp_command(name="show", help=_("Show the value for a particular label key"))
    @click.option("--key", required=True, help=_("Key of the label"))
    @pass_entity_context
    def label_show(entity_ctx: PulpEntityContext, key: str) -> None:
        """Show the value for a particular label key"""
        click.echo(entity_ctx.show_label(key))

    for subcmd in [label_set, label_unset, label_show]:
        for decorator in decorators:
            subcmd = decorator(subcmd)
        label_group.add_command(subcmd)

    return label_group


def role_command(**kwargs: t.Any) -> click.Command:
    """A factory that creates a (object) role command group."""

    kwargs.setdefault("name", "role")
    kwargs.setdefault("help", _("Manage object roles."))
    decorators = kwargs.pop("decorators", [name_option, href_option])

    @pulp_group(**kwargs)
    def role_group() -> None:
        pass

    @pulp_command(help=_("List my permissions on this object."))
    @pass_entity_context
    @pass_pulp_context
    def my_permissions(pulp_ctx: PulpCLIContext, entity_ctx: PulpEntityContext) -> None:
        result = entity_ctx.my_permissions()
        pulp_ctx.output_result(result)

    @pulp_command(name="list", help=_("List assigned object roles."))
    @pass_entity_context
    @pass_pulp_context
    def role_list(pulp_ctx: PulpCLIContext, entity_ctx: PulpEntityContext) -> None:
        result = entity_ctx.list_roles()
        pulp_ctx.output_result(result)

    @pulp_command(name="add", help=_("Add assigned object roles."))
    @click.option("--role")
    @click.option("--user", "users", multiple=True)
    @click.option("--group", "groups", multiple=True)
    @pass_entity_context
    @pass_pulp_context
    def role_add(
        pulp_ctx: PulpCLIContext,
        entity_ctx: PulpEntityContext,
        role: str,
        users: t.List[str],
        groups: t.List[str],
    ) -> None:
        result = entity_ctx.add_role(role, users, groups)
        pulp_ctx.output_result(result)

    @pulp_command(name="remove", help=_("Remove assigned object roles."))
    @click.option("--role")
    @click.option("--user", "users", multiple=True)
    @click.option("--group", "groups", multiple=True)
    @pass_entity_context
    @pass_pulp_context
    def role_remove(
        pulp_ctx: PulpCLIContext,
        entity_ctx: PulpEntityContext,
        role: str,
        users: t.List[str],
        groups: t.List[str],
    ) -> None:
        result = entity_ctx.remove_role(role, users, groups)
        pulp_ctx.output_result(result)

    for subcmd in [my_permissions, role_list, role_add, role_remove]:
        for decorator in decorators:
            subcmd = decorator(subcmd)
        role_group.add_command(subcmd)

    return role_group


def repository_content_command(**kwargs: t.Any) -> click.Group:
    """A factory that creates a repository content command group."""

    content_contexts = kwargs.pop("contexts", {})

    def version_callback(
        ctx: click.Context, param: click.Parameter, value: t.Optional[int]
    ) -> PulpRepositoryVersionContext:
        repo_ctx = ctx.find_object(PulpRepositoryContext)
        assert repo_ctx is not None
        repo_ver_ctx = repo_ctx.get_version_context()
        repo_ver_ctx.pulp_href = (
            f"{repo_ctx.pulp_href}versions/{value}/"
            if value is not None
            else repo_ctx.entity["latest_version_href"]
        )
        return repo_ver_ctx

    # This is a mypy bug getting confused with positional args
    # https://github.com/python/mypy/issues/15037
    @pulp_command("list")  # type: ignore [arg-type]
    @click.option("--all-types", is_flag=True)
    @limit_option
    @offset_option
    @repository_option
    @click.option("--version", type=int, callback=version_callback)
    @pass_pulp_context
    @pass_content_context
    def content_list(
        content_ctx: PulpContentContext,
        pulp_ctx: PulpCLIContext,
        version: PulpRepositoryVersionContext,
        offset: int,
        limit: int,
        all_types: bool,
        **params: t.Any,
    ) -> None:
        parameters = {k: v for k, v in params.items() if v is not None}
        parameters.update({"repository_version": version.pulp_href})
        content_ctx = PulpContentContext(pulp_ctx) if all_types else content_ctx
        result = content_ctx.list(limit=limit, offset=offset, parameters=parameters)
        pulp_ctx.output_result(result)

    @pulp_command("add")
    @repository_option
    @click.option("--base-version", type=int, callback=version_callback)
    @pass_content_context
    def content_add(
        content_ctx: PulpContentContext,
        base_version: PulpRepositoryVersionContext,
    ) -> None:
        repo_ctx = base_version.repository_ctx
        repo_ctx.modify(add_content=[content_ctx.pulp_href], base_version=base_version.pulp_href)

    @pulp_command("remove")
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
        repo_ctx.modify(remove_content=remove_content, base_version=base_version.pulp_href)

    @pulp_command("modify")
    @repository_option
    @click.option("--base-version", type=int, callback=version_callback)
    def content_modify(
        base_version: PulpRepositoryVersionContext,
        add_content: t.Optional[t.List[PulpContentContext]],
        remove_content: t.Optional[t.List[PulpContentContext]],
    ) -> None:
        repo_ctx = base_version.repository_ctx
        ac = [unit.pulp_href for unit in add_content] if add_content else None
        rc = [unit.pulp_href for unit in remove_content] if remove_content else None
        repo_ctx.modify(add_content=ac, remove_content=rc, base_version=base_version.pulp_href)

    command_decorators: t.Dict[click.Command, t.Optional[t.List[t.Callable[[FC], FC]]]] = {
        content_list: kwargs.pop("list_decorators", []),
        content_add: kwargs.pop("add_decorators", None),
        content_remove: kwargs.pop("remove_decorators", None),
        content_modify: kwargs.pop("modify_decorators", None),
    }
    kwargs.setdefault("name", "content")

    @pulp_group(**kwargs)
    @type_option(choices=content_contexts)
    def content_group() -> None:
        pass

    for command, options in command_decorators.items():
        if options is not None:
            for option in options:
                command = option(command)
            content_group.add_command(command)

    return content_group
