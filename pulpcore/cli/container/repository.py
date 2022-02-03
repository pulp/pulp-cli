import re
from typing import Any, Dict

import click

from pulpcore.cli.common.context import (
    EntityFieldDefinition,
    PulpEntityContext,
    PulpRemoteContext,
    PulpRepositoryContext,
    pass_repository_context,
)
from pulpcore.cli.common.generic import (
    create_command,
    destroy_command,
    href_option,
    label_command,
    label_select_option,
    list_command,
    name_option,
    pulp_group,
    repository_href_option,
    repository_option,
    resource_option,
    retained_versions_option,
    show_command,
    type_option,
    update_command,
    version_command,
)
from pulpcore.cli.common.i18n import get_translation
from pulpcore.cli.container.context import (
    PulpContainerBaseRepositoryContext,
    PulpContainerPushRepositoryContext,
    PulpContainerRemoteContext,
    PulpContainerRepositoryContext,
)
from pulpcore.cli.core.generic import task_command

translation = get_translation(__name__)
_ = translation.gettext
VALID_TAG_REGEX = r"^[A-Za-z0-9][A-Za-z0-9._-]*$"


def _tag_callback(ctx: click.Context, param: click.Parameter, value: str) -> str:
    if len(value) == 0:
        raise click.ClickException("Please pass a non empty tag name.")
    if re.match(VALID_TAG_REGEX, value) is None:
        raise click.ClickException("Please pass a valid tag.")

    return value


remote_option = resource_option(
    "--remote",
    default_plugin="container",
    default_type="container",
    context_table={"container:container": PulpContainerRemoteContext},
    href_pattern=PulpRemoteContext.HREF_PATTERN,
    help=_(
        "Remote used for synching in the form '[[<plugin>:]<resource_type>:]<name>' or by href."
    ),
)


@pulp_group()
@type_option(
    choices={
        "container": PulpContainerRepositoryContext,
        "push": PulpContainerPushRepositoryContext,
    },
    default="container",
)
def repository() -> None:
    pass


lookup_options = [href_option, name_option]
nested_lookup_options = [repository_href_option, repository_option]
update_options = [
    click.option("--description"),
    remote_option,
    retained_versions_option,
]
create_options = update_options + [click.option("--name", required=True)]
container_context = (PulpContainerRepositoryContext,)

repository.add_command(list_command(decorators=[label_select_option]))
repository.add_command(show_command(decorators=lookup_options))
repository.add_command(
    create_command(decorators=create_options, allowed_with_contexts=container_context)
)
repository.add_command(
    update_command(
        decorators=lookup_options + update_options, allowed_with_contexts=container_context
    )
)
repository.add_command(
    destroy_command(decorators=lookup_options, allowed_with_contexts=container_context)
)
repository.add_command(task_command(decorators=nested_lookup_options))
repository.add_command(version_command(decorators=nested_lookup_options))
repository.add_command(label_command(decorators=nested_lookup_options))


@repository.command(allowed_with_contexts=container_context)
@name_option
@href_option
@remote_option
@pass_repository_context
def sync(
    repository_ctx: PulpRepositoryContext,
    remote: EntityFieldDefinition,
) -> None:
    if not repository_ctx.capable("sync"):
        raise click.ClickException(_("Repository type does not support sync."))

    repository = repository_ctx.entity
    repository_href = repository_ctx.pulp_href

    body: Dict[str, Any] = {}

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


@repository.command(name="tag")
@name_option
@href_option
@click.option("--tag", help=_("Name to tag an image with"), required=True, callback=_tag_callback)
@click.option("--digest", help=_("SHA256 digest of the Manifest file"), required=True)
@pass_repository_context
def add_tag(
    repository_ctx: PulpContainerBaseRepositoryContext,
    digest: str,
    tag: str,
) -> None:
    digest = digest.strip()
    if not digest.startswith("sha256:"):
        digest = f"sha256:{digest}"
    if len(digest) != 71:  # len("sha256:") + 64
        raise click.ClickException("Improper SHA256, please provide a valid 64 digit digest.")

    repository_ctx.tag(tag, digest)


@repository.command(name="untag")
@name_option
@href_option
@click.option("--tag", help=_("Name of tag to remove"), required=True, callback=_tag_callback)
@pass_repository_context
def remove_tag(repository_ctx: PulpContainerBaseRepositoryContext, tag: str) -> None:
    repository_ctx.untag(tag)
