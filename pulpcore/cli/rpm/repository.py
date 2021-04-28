import gettext
from typing import Any, Dict, Optional, Union

import click

from pulpcore.cli.common.context import (
    PluginRequirement,
    PulpContext,
    PulpEntityContext,
    PulpRepositoryContext,
    pass_pulp_context,
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
    pulp_option,
    show_command,
    update_command,
    version_command,
)
from pulpcore.cli.rpm.common import CHECKSUM_CHOICES
from pulpcore.cli.rpm.context import PulpRpmRemoteContext, PulpRpmRepositoryContext

_ = gettext.gettext


def _remote_callback(
    ctx: click.Context, param: click.Parameter, value: Optional[str]
) -> Optional[Union[str, PulpEntityContext]]:
    # Pass None and "" verbatim
    if value:
        pulp_ctx: PulpContext = ctx.find_object(PulpContext)
        return PulpRpmRemoteContext(pulp_ctx, entity={"name": value})
    return value


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


lookup_options = [href_option, name_option]
update_options = [
    click.option("--description"),
    click.option("--retain-package-versions", type=int),
    click.option("--remote", callback=_remote_callback),
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
        needs_plugins=[PluginRequirement("rpm", "3.11.0.dev")],
        default=None,
    ),
    pulp_option("--retained-versions", needs_plugins=[PluginRequirement("core", "3.13.0.dev")]),
]
create_options = update_options + [click.option("--name", required=True)]

repository.add_command(list_command(decorators=[label_select_option]))
repository.add_command(show_command(decorators=lookup_options))
repository.add_command(create_command(decorators=create_options))
repository.add_command(update_command(decorators=lookup_options + update_options))
repository.add_command(destroy_command(decorators=lookup_options))
repository.add_command(version_command())
repository.add_command(label_command())


@repository.command()
@click.option("--name", required=True)
@click.option("--mirror/--no-mirror", default=None)
@click.option("--remote")
@pass_repository_context
@pass_pulp_context
def sync(
    pulp_ctx: PulpContext,
    repository_ctx: PulpRepositoryContext,
    name: str,
    remote: Optional[str],
    mirror: Optional[bool],
) -> None:
    repository = repository_ctx.find(name=name)
    repository_href = repository["pulp_href"]

    body: Dict[str, Any] = {}

    if mirror:
        body["mirror"] = mirror

    if remote:
        remote_href: str = PulpRpmRemoteContext(pulp_ctx).find(name=remote)["pulp_href"]
        body["remote"] = remote_href
    elif repository["remote"] is None:
        raise click.ClickException(
            f"Repository '{name}' does not have a default remote. Please specify with '--remote'."
        )

    repository_ctx.sync(
        href=repository_href,
        body=body,
    )
