import gettext
from typing import IO, Any, Optional, Union

import click

from pulpcore.cli.ansible.context import PulpAnsibleCollectionVersionContext, PulpAnsibleRoleContext
from pulpcore.cli.common.context import PulpContext, pass_entity_context, pass_pulp_context
from pulpcore.cli.common.generic import (
    GroupOption,
    chunk_size_option,
    href_option,
    list_command,
    pulp_option,
    show_command,
)
from pulpcore.cli.core.context import PulpArtifactContext

_ = gettext.gettext


def _content_callback(ctx: click.Context, param: click.Parameter, value: Any) -> Any:
    if value:
        ctx.obj.entity = value  # The context should be already set based on the type option
    return value


@click.group()
@click.option(
    "-t",
    "--type",
    "content_type",
    type=click.Choice(["collection-version", "role"], case_sensitive=False),
    default="collection-version",
)
@pass_pulp_context
@click.pass_context
def content(ctx: click.Context, pulp_ctx: PulpContext, content_type: str) -> None:
    if content_type == "collection-version":
        ctx.obj = PulpAnsibleCollectionVersionContext(pulp_ctx)
    elif content_type == "role":
        ctx.obj = PulpAnsibleRoleContext(pulp_ctx)
    else:
        raise NotImplementedError()


list_options = [
    pulp_option("--name", help=_("Name of {entity}")),
    pulp_option("--namespace", help=_("Namespace of {entity}")),
    pulp_option("--version", help=_("Version of {entity}")),
    pulp_option(
        "--only-highest",
        "is_highest",
        is_flag=True,
        default=None,
        help=_(
            "Only show highest version of collection version (only works for collection versions)"
        ),
    ),
    pulp_option(
        "--tags",
        help=_(
            "Comma separated list of tags that must all match (only works for collection-versions)"
        ),
    ),
]

fields_options = [
    pulp_option("--fields", help=_("String list of fields to include in the result")),
    pulp_option(
        "--exclude-fields",
        default="files,manifest,docs_blob",
        help=_("String list of fields to exclude from result"),
    ),
]

lookup_options = [
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

content.add_command(list_command(decorators=list_options + fields_options))
content.add_command(show_command(decorators=lookup_options))


@content.command()
@click.option("--file", type=click.File("rb"), required=True)
@chunk_size_option
@pulp_option("--name", help=_("Name of {entity}, only required for Roles"))
@pulp_option("--namespace", help=_("Namespace of {entity}, only required for Roles"))
@pulp_option("--version", help=_("Version of {entity}, only required for Roles"))
@pass_entity_context
@pass_pulp_context
def upload(
    pulp_ctx: PulpContext,
    content_ctx: Union[PulpAnsibleRoleContext, PulpAnsibleCollectionVersionContext],
    file: IO[bytes],
    chunk_size: int,
    name: Optional[str],
    namespace: Optional[str],
    version: Optional[str],
) -> None:

    if isinstance(content_ctx, PulpAnsibleRoleContext):
        # Check that name, namespace, and version are supplied for Role upload
        if not all((name, namespace, version)):
            raise click.ClickException(
                "Please specify name, namespace, and version when uploading a Role"
            )
        artifact_href = PulpArtifactContext(pulp_ctx).upload(file, chunk_size)
        body = {"artifact": artifact_href, "name": name, "namespace": namespace, "version": version}
        result = content_ctx.create(body=body)
        pulp_ctx.output_result(result)
    else:
        # Collection upload uses name, namespace, and version for extra validation
        body = {"expected_name": name, "expected_namespace": namespace, "expected_version": version}
        result = content_ctx.upload(file=file, body=body)
        pulp_ctx.output_result(result)
