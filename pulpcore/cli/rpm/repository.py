import gettext
from typing import Any, Dict, Iterable, Optional

import click
import schema as s

from pulpcore.cli.common.context import (
    EntityFieldDefinition,
    PluginRequirement,
    PulpContext,
    PulpEntityContext,
    PulpRemoteContext,
    PulpRepositoryContext,
    pass_pulp_context,
    pass_repository_context,
)
from pulpcore.cli.common.generic import (
    create_command,
    create_content_json_callback,
    destroy_command,
    href_option,
    label_command,
    label_select_option,
    list_command,
    name_option,
    pulp_option,
    repository_content_command,
    repository_href_option,
    repository_option,
    resource_option,
    retained_versions_option,
    show_command,
    update_command,
    version_command,
)
from pulpcore.cli.core.generic import task_command
from pulpcore.cli.rpm.common import CHECKSUM_CHOICES
from pulpcore.cli.rpm.context import (
    PulpRpmPackageContext,
    PulpRpmRemoteContext,
    PulpRpmRepositoryContext,
)

_ = gettext.gettext


SKIP_TYPES = ["srpm"]
remote_option = resource_option(
    "--remote",
    default_plugin="rpm",
    default_type="rpm",
    context_table={"rpm:rpm": PulpRpmRemoteContext},
    href_pattern=PulpRemoteContext.HREF_PATTERN,
    help=_(
        "Remote used for synching in the form '[[<plugin>:]<resource_type>:]<name>' or by href."
    ),
)


def _content_callback(ctx: click.Context, param: click.Parameter, value: Any) -> Any:
    if value:
        pulp_ctx = ctx.find_object(PulpContext)
        assert pulp_ctx is not None
        ctx.obj = PulpRpmPackageContext(pulp_ctx, pulp_href=value)
    return value


CONTENT_LIST_SCHEMA = s.Schema([{"pulp_href": str}])


@click.group()
@click.option(
    "-t",
    "--type",
    "repo_type",
    type=click.Choice(["rpm"], case_sensitive=False),
    default="rpm",
)
@pass_pulp_context
@click.pass_context
def repository(ctx: click.Context, pulp_ctx: PulpContext, repo_type: str) -> None:
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
lookup_options = [href_option, name_option]
nested_lookup_options = [repository_href_option, repository_option]
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
@remote_option
@click.option("--mirror/--no-mirror", default=None)
@click.option(
    "--skip-type", "skip_types", multiple=True, type=click.Choice(SKIP_TYPES, case_sensitive=False)
)
@pass_repository_context
def sync(
    repository_ctx: PulpRepositoryContext,
    remote: EntityFieldDefinition,
    mirror: Optional[bool],
    skip_types: Iterable[str],
) -> None:
    repository = repository_ctx.entity
    repository_href = repository_ctx.pulp_href

    body: Dict[str, Any] = {}

    if mirror:
        body["mirror"] = mirror
    if skip_types:
        body["skip_types"] = skip_types

    if isinstance(remote, PulpEntityContext):
        body["remote"] = remote.pulp_href
    elif repository["remote"] is None:
        raise click.ClickException(
            _(
                "Repository '{name}' does not have a default remote. "
                "Please specify with '--remote'."
            ).format(name=repository["name"])
        )

    repository_ctx.sync(
        href=repository_href,
        body=body,
    )
