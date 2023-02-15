from typing import Any, Dict, Iterable, Optional

import click
import schema as s
from pulp_glue.common.context import (
    EntityFieldDefinition,
    PluginRequirement,
    PulpRemoteContext,
    PulpRepositoryContext,
)
from pulp_glue.common.i18n import get_translation
from pulp_glue.rpm.context import (
    PulpRpmPackageContext,
    PulpRpmRemoteContext,
    PulpRpmRepositoryContext,
    PulpUlnRemoteContext,
)

from pulpcore.cli.common.generic import (
    PulpCLIContext,
    create_command,
    create_content_json_callback,
    destroy_command,
    href_option,
    label_command,
    label_select_option,
    list_command,
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
from pulpcore.cli.rpm.common import CHECKSUM_CHOICES

translation = get_translation(__name__)
_ = translation.gettext

SKIP_TYPES = ["srpm", "treeinfo"]
SYNC_TYPES = ["additive", "mirror_complete", "mirror_content_only"]
remote_option = resource_option(
    "--remote",
    default_plugin="rpm",
    default_type="rpm",
    context_table={"rpm:rpm": PulpRpmRemoteContext, "rpm:uln": PulpUlnRemoteContext},
    href_pattern=PulpRemoteContext.HREF_PATTERN,
    help=_(
        "Remote used for synching in the form '[[<plugin>:]<resource_type>:]<name>' or by href."
    ),
)


def _content_callback(ctx: click.Context, param: click.Parameter, value: Any) -> Any:
    if value:
        pulp_ctx = ctx.find_object(PulpCLIContext)
        assert pulp_ctx is not None
        ctx.obj = PulpRpmPackageContext(pulp_ctx, pulp_href=value)
    return value


CONTENT_LIST_SCHEMA = s.Schema([{"pulp_href": str}])


@pulp_group()
@click.option(
    "-t",
    "--type",
    "repo_type",
    type=click.Choice(["rpm"], case_sensitive=False),
    default="rpm",
)
@pass_pulp_context
@click.pass_context
def repository(ctx: click.Context, pulp_ctx: PulpCLIContext, repo_type: str) -> None:
    if repo_type == "rpm":
        ctx.obj = PulpRpmRepositoryContext(pulp_ctx)
    else:
        raise NotImplementedError()


package_options = [
    click.option(
        "--package-href",
        callback=_content_callback,
        expose_value=False,
        help=_("Href of the rpm package to use"),
    )
]
lookup_options = [href_option, name_option, repository_lookup_option]
nested_lookup_options = [repository_href_option, repository_lookup_option]
content_json_callback = create_content_json_callback(
    PulpRpmPackageContext, schema=CONTENT_LIST_SCHEMA
)
modify_options = [
    click.option(
        "--add-content",
        callback=content_json_callback,
        help=_(
            """JSON string with a list of objects to add to the repository.
    Each object must contain the following keys: "pulp_href".
    The argument prefixed with the '@' can be the path to a JSON file with a list of objects."""
        ),
    ),
    click.option(
        "--remove-content",
        callback=content_json_callback,
        help=_(
            """JSON string with a list of objects to remove from the repository.
    Each object must contain the following keys: "pulp_href".
    The argument prefixed with the '@' can be the path to a JSON file with a list of objects."""
        ),
    ),
]
update_options = [
    click.option("--description"),
    click.option("--retain-package-versions", type=int),
    remote_option,
    click.option(
        "--metadata-checksum-type", type=click.Choice(CHECKSUM_CHOICES, case_sensitive=False)
    ),
    click.option(
        "--package-checksum-type", type=click.Choice(CHECKSUM_CHOICES, case_sensitive=False)
    ),
    click.option("--gpgcheck", type=click.Choice(("0", "1"))),
    click.option("--repo-gpgcheck", type=click.Choice(("0", "1"))),
    click.option("--sqlite-metadata/--no-sqlite-metadata", default=None),
    pulp_option(
        "--autopublish/--no-autopublish",
        needs_plugins=[PluginRequirement("rpm", "3.12.0")],
        default=None,
    ),
    retained_versions_option,
    pulp_labels_option,
]
create_options = update_options + [click.option("--name", required=True)]

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
        contexts={"package": PulpRpmPackageContext},
        add_decorators=package_options,
        remove_decorators=package_options,
        modify_decorators=modify_options,
    )
)


@repository.command()
@name_option
@href_option
@repository_lookup_option
@remote_option
@click.option(
    "--mirror/--no-mirror",
    default=None,
    help="""
    DEPRECATED: If True, sync_policy will default to 'mirror_complete' instead
    of 'additive'.
    """,
)
@pulp_option(
    "--optimize/--no-optimize",
    default=None,
    help="Whether or not to optimize sync.",
    needs_plugins=[PluginRequirement("rpm", min="3.3.0")],
)
@click.option(
    "--skip-type",
    "skip_types",
    multiple=True,
    type=click.Choice(SKIP_TYPES, case_sensitive=False),
    help="Content type to skip during sync.",
)
@pulp_option(
    "--sync-policy",
    "sync_policy",
    type=click.Choice(SYNC_TYPES, case_sensitive=False),
    help="""
    Modifies how the sync is performed. 'mirror_complete' will clone the original metadata
    and create an automatic publication from it, but comes with some limitations and does
    not work for certain repositories. 'mirror_content_only' will change the repository
    contents to match the remote but the metadata will be regenerated and will not be
    bit-for-bit identical. 'additive' will retain the existing contents of the repository
    and add the contents of the repository being synced.
    """,
    needs_plugins=[PluginRequirement("rpm", "3.16.0")],
)
@pass_repository_context
def sync(
    repository_ctx: PulpRepositoryContext,
    remote: EntityFieldDefinition,
    mirror: Optional[bool],
    optimize: Optional[bool],
    skip_types: Optional[Iterable[str]],
    sync_policy: Optional[str],
) -> None:
    """
    Sync the repository from a remote source.
    If remote is not specified sync will try to use the default remote associated with
    the repository
    """
    repo = repository_ctx.entity
    body: Dict[str, Any] = {}

    if mirror:
        body["mirror"] = mirror
    if optimize:
        body["optimize"] = optimize
    if skip_types:
        body["skip_types"] = skip_types
    if sync_policy:
        body["sync_policy"] = sync_policy

    if remote:
        body["remote"] = remote
    elif repo["remote"] is None:
        raise click.ClickException(
            _(
                "Repository '{name}' does not have a default remote. "
                "Please specify with '--remote'."
            ).format(name=repo["name"])
        )
    repository_ctx.sync(body=body)
