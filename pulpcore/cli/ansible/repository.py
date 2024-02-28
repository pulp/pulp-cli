import typing as t

import click
import schema as s
from pulp_glue.ansible.context import (
    PulpAnsibleCollectionRemoteContext,
    PulpAnsibleCollectionVersionContext,
    PulpAnsibleRepositoryContext,
    PulpAnsibleRoleContext,
    PulpAnsibleRoleRemoteContext,
)
from pulp_glue.common.context import (
    EntityFieldDefinition,
    PluginRequirement,
    PulpRemoteContext,
    PulpRepositoryContext,
)
from pulp_glue.common.i18n import get_translation
from pulp_glue.core.context import PulpSigningServiceContext

from pulpcore.cli.common.generic import (
    GroupOption,
    PulpCLIContext,
    create_command,
    create_content_json_callback,
    destroy_command,
    href_option,
    label_command,
    label_select_option,
    list_command,
    load_json_callback,
    load_string_callback,
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
    default_plugin="ansible",
    default_type="collection",
    context_table={
        "ansible:collection": PulpAnsibleCollectionRemoteContext,
        "ansible:role": PulpAnsibleRoleRemoteContext,
    },
    href_pattern=PulpRemoteContext.HREF_PATTERN,
    help=_(
        "Remote used for synching in the form '[[<plugin>:]<resource_type>:]<name>' or by href."
    ),
)


CONTENT_LIST_SCHEMA = s.Schema(
    [{"name": s.And(str, len), "namespace": s.And(str, len), "version": s.And(str, len)}]
)


def _content_callback(ctx: click.Context, param: click.Parameter, value: t.Any) -> t.Any:
    if value:
        ctx.obj.entity = value  # The context is set by the type parameter on the content commands
    return value


def _signing_service_callback(ctx: click.Context, param: click.Parameter, value: t.Any) -> t.Any:
    if value:
        pulp_ctx = ctx.find_object(PulpCLIContext)
        assert pulp_ctx is not None
        value = PulpSigningServiceContext(pulp_ctx, entity={"name": value})
    return value


@pulp_group()
@click.option(
    "-t",
    "--type",
    "repo_type",
    type=click.Choice(["ansible"], case_sensitive=False),
    default="ansible",
)
@pass_pulp_context
@click.pass_context
def repository(ctx: click.Context, pulp_ctx: PulpCLIContext, repo_type: str) -> None:
    if repo_type == "ansible":
        ctx.obj = PulpAnsibleRepositoryContext(pulp_ctx)
    else:
        raise NotImplementedError()


lookup_options = [href_option, name_option, repository_lookup_option]
nested_lookup_options = [repository_href_option, repository_lookup_option]
update_options = [
    click.option("--description"),
    pulp_option(
        "--gpgkey",
        callback=load_string_callback,
        needs_plugins=[
            PluginRequirement(
                "ansible", specifier=">=0.15.0", feature="gpgkeys on ansible repositories"
            )
        ],
    ),
    remote_option,
    retained_versions_option,
    pulp_labels_option,
]
create_options = update_options + [click.option("--name", required=True)]
content_options = [
    click.option(
        "--name",
        help=_("Name of {entity}"),
        group=["namespace", "version"],
        expose_value=False,
        cls=GroupOption,
        callback=_content_callback,
    ),
    click.option(
        "--namespace",
        help=_("Namespace of {entity}"),
        group=["name", "version"],
        expose_value=False,
        cls=GroupOption,
    ),
    click.option(
        "--version",
        help=_("Version of {entity}"),
        group=["namespace", "name"],
        expose_value=False,
        cls=GroupOption,
    ),
    href_option,
]
content_json_callback = create_content_json_callback(schema=CONTENT_LIST_SCHEMA)
modify_options = [
    click.option(
        "--add-content",
        callback=content_json_callback,
        help=_(
            """JSON string with a list of objects to add to the repository.
    Each object must contain the following keys: "name", "namespace", "version".
    The argument prefixed with the '@' can be the path to a JSON file with a list of objects."""
        ),
    ),
    click.option(
        "--remove-content",
        callback=content_json_callback,
        help=_(
            """JSON string with a list of objects to remove from the repository.
    Each object must contain the following keys: "name", "namespace", "version".
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
        contexts={
            "collection-version": PulpAnsibleCollectionVersionContext,
            "role": PulpAnsibleRoleContext,
        },
        add_decorators=content_options,
        remove_decorators=content_options,
        modify_decorators=modify_options,
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
        name = repository["name"]
        raise click.ClickException(
            _(
                "Repository '{name}' does not have a default remote."
                " Please specify with '--remote'."
            ).format(name=name)
        )

    repository_ctx.sync(body=body)


@repository.command()
@name_option
@href_option
@repository_lookup_option
@click.option("--signing-service", required=True, callback=_signing_service_callback)
@click.option("--content-units", callback=load_json_callback)
@pass_repository_context
def sign(
    repository_ctx: PulpRepositoryContext,
    signing_service: PulpSigningServiceContext,
    content_units: t.Optional[t.List[str]],
) -> None:
    """Sign the collections in the repository using the signing service specified."""
    if content_units is None:
        content_units = ["*"]
    body = {"content_units": content_units, "signing_service": signing_service}
    parameters = {repository_ctx.HREF: repository_ctx.pulp_href}
    repository_ctx.call("sign", parameters=parameters, body=body)
