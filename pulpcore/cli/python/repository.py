import typing as t

import click
import schema as s
from pulp_glue.common.context import (
    EntityFieldDefinition,
    PluginRequirement,
    PulpRemoteContext,
    PulpRepositoryContext,
)
from pulp_glue.common.i18n import get_translation
from pulp_glue.python.context import (
    PulpPythonContentContext,
    PulpPythonRemoteContext,
    PulpPythonRepositoryContext,
)

from pulp_cli.generic import (
    GroupOption,
    PulpCLIContext,
    create_command,
    create_content_json_callback,
    destroy_command,
    href_option,
    json_callback,
    label_command,
    label_select_option,
    list_command,
    load_file_wrapper,
    name_option,
    pass_pulp_context,
    pass_repository_context,
    pulp_group,
    pulp_labels_option,
    pulp_option,
    repository_content_command,
    repository_href_option,
    repository_lookup_option,
    resource_option,
    retained_versions_option,
    show_command,
    update_command,
    version_command,
)
from pulpcore.cli.core.generic import task_command

translation = get_translation(__package__)
_ = translation.gettext


remote_option = resource_option(
    "--remote",
    default_plugin="python",
    default_type="python",
    context_table={"python:python": PulpPythonRemoteContext},
    href_pattern=PulpRemoteContext.HREF_PATTERN,
    help=_(
        "Remote used for synching in the form '[[<plugin>:]<resource_type>:]<name>' or by href."
    ),
)


def _content_callback(ctx: click.Context, param: click.Parameter, value: t.Any) -> t.Any:
    if value:
        pulp_ctx = ctx.find_object(PulpCLIContext)
        assert pulp_ctx is not None
        ctx.obj = PulpPythonContentContext(pulp_ctx, entity=value)
    return value


CONTENT_LIST_SCHEMA = s.Schema([{"sha256": str, "filename": s.And(str, len)}])


@load_file_wrapper
def _content_list_callback(
    ctx: click.Context, param: click.Parameter, value: t.Optional[str]
) -> t.Any:
    if value is None:
        return None

    result = json_callback(ctx, param, value)
    try:
        return CONTENT_LIST_SCHEMA.validate(result)
    except s.SchemaError as e:
        raise click.ClickException(
            _("Validation of '{parameter}' failed: {error}").format(
                parameter=param.name, error=str(e)
            )
        )


@pulp_group()
@click.option(
    "-t",
    "--type",
    "repo_type",
    type=click.Choice(["python"], case_sensitive=False),
    default="python",
)
@pass_pulp_context
@click.pass_context
def repository(ctx: click.Context, pulp_ctx: PulpCLIContext, /, repo_type: str) -> None:
    if repo_type == "python":
        ctx.obj = PulpPythonRepositoryContext(pulp_ctx)
    else:
        raise NotImplementedError()


lookup_options = [href_option, name_option, repository_lookup_option]
nested_lookup_options = [repository_href_option, repository_lookup_option]
update_options = [
    click.option("--description"),
    remote_option,
    pulp_option(
        "--autopublish/--no-autopublish",
        needs_plugins=[PluginRequirement("python", specifier=">=3.3.0")],
        default=None,
    ),
    retained_versions_option,
    pulp_labels_option,
]
create_options = update_options + [click.option("--name", required=True)]
package_options = [
    click.option("--sha256", cls=GroupOption, expose_value=False, group=["filename"]),
    click.option(
        "--filename",
        callback=_content_callback,
        expose_value=False,
        cls=GroupOption,
        group=["sha256"],
        help=_("Filename of the python package."),
    ),
]
content_json_callback = create_content_json_callback(
    PulpPythonContentContext, schema=CONTENT_LIST_SCHEMA
)
modify_options = [
    click.option(
        "--add-content",
        callback=content_json_callback,
        help=_(
            """JSON string with a list of objects to add to the repository.
    Each object must contain the following keys: "sha256", "filename".
    The argument prefixed with the '@' can be the path to a JSON file with a list of objects."""
        ),
    ),
    click.option(
        "--remove-content",
        callback=content_json_callback,
        help=_(
            """JSON string with a list of objects to remove from the repository.
    Each object must contain the following keys: "sha256", "filename".
    The argument prefixed with the '@' can be the path to a JSON file with a list of objects."""
        ),
    ),
]

repository.add_command(list_command(decorators=[label_select_option]))
repository.add_command(show_command(decorators=lookup_options))
repository.add_command(create_command(decorators=create_options))
repository.add_command(update_command(decorators=lookup_options + update_options))
repository.add_command(destroy_command(decorators=lookup_options))
repository.add_command(task_command(decorators=nested_lookup_options))
repository.add_command(version_command(decorators=nested_lookup_options))
repository.add_command(label_command(decorators=nested_lookup_options))
repository.add_command(
    repository_content_command(
        contexts={"package": PulpPythonContentContext},
        add_decorators=package_options,
        remove_decorators=package_options,
        modify_decorators=modify_options,
        base_default_plugin="python",
        base_default_type="python",
    )
)


@repository.command()
@name_option
@href_option
@repository_lookup_option
@remote_option
@pass_repository_context
def sync(
    repository_ctx: PulpRepositoryContext,
    /,
    remote: EntityFieldDefinition,
) -> None:
    """
    Sync the repository from a remote source.
    If remote is not specified sync will try to use the default remote associated with
    the repository
    """
    repository = repository_ctx.entity
    body: t.Dict[str, t.Any] = {}

    if remote:
        body["remote"] = remote
    elif repository["remote"] is None:
        raise click.ClickException(
            _(
                "Repository '{name}' does not have a default remote. "
                "Please specify with '--remote'."
            ).format(name=repository["name"])
        )

    repository_ctx.sync(body=body)
