from typing import Iterable

import click
from pulp_glue.common.context import PulpRemoteContext
from pulp_glue.common.i18n import get_translation
from pulp_glue.file.context import PulpFileACSContext, PulpFileRemoteContext

from pulpcore.cli.common.generic import (
    PulpCLIContext,
    acs_lookup_option,
    create_command,
    destroy_command,
    href_option,
    list_command,
    name_option,
    pass_entity_context,
    pass_pulp_context,
    pulp_group,
    resource_option,
    role_command,
    show_command,
    update_command,
)

translation = get_translation(__name__)
_ = translation.gettext


path_option = click.option(
    "--path", "paths", multiple=True, help=_("path to add to ACS; can be specified multiple times.")
)


@pulp_group()
@click.option(
    "-t",
    "--type",
    "acs_type",
    type=click.Choice(["file"], case_sensitive=False),
    default="file",
)
@pass_pulp_context
@click.pass_context
def acs(ctx: click.Context, pulp_ctx: PulpCLIContext, acs_type: str) -> None:
    if acs_type == "file":
        ctx.obj = PulpFileACSContext(pulp_ctx)
    else:
        raise NotImplementedError()


@acs.group()
def path() -> None:
    """Manage paths for an ACS."""
    pass


@path.command()
@name_option
@href_option
@acs_lookup_option
@path_option
@pass_entity_context
def add(acs_ctx: PulpFileACSContext, paths: Iterable[str]) -> None:
    """Add path(s) to an existing ACS."""
    paths = set(paths)
    existing_paths = set(acs_ctx.entity["paths"])

    for path in paths:
        if path in existing_paths:
            raise click.ClickException(_("ACS already has path '{}'.").format(path))

    if existing_paths != {""}:
        paths = set.union(existing_paths, paths)
    acs_ctx.update(body={"paths": list(paths)})


@path.command()
@name_option
@href_option
@acs_lookup_option
@path_option
@pass_entity_context
def remove(acs_ctx: PulpFileACSContext, paths: Iterable[str]) -> None:
    """Remove path(s) from an existing ACS."""
    paths = set(paths)
    existing_paths = set(acs_ctx.entity["paths"])

    if paths - existing_paths:
        missing_paths = paths - existing_paths
        raise click.ClickException(_("ACS does not have path(s): {}.").format(missing_paths))

    paths = existing_paths - paths
    acs_ctx.update(body={"paths": list(paths)})


remote_option = resource_option(
    "--remote",
    default_plugin="file",
    default_type="file",
    context_table={"file:file": PulpFileRemoteContext},
    href_pattern=PulpRemoteContext.HREF_PATTERN,
    help=_("Remote to attach to ACS in the form '[[<plugin>:]<resource_type>:]<name>' or by href."),
)
lookup_options = [href_option, name_option, acs_lookup_option]
update_options = [remote_option]
create_options = update_options + [click.option("--name", required=True), path_option]

acs.add_command(list_command())
acs.add_command(show_command(decorators=lookup_options))
acs.add_command(create_command(decorators=create_options))
acs.add_command(update_command(decorators=lookup_options + update_options))
acs.add_command(destroy_command(decorators=lookup_options))
acs.add_command(role_command(decorators=lookup_options))


@acs.command()
@pass_entity_context
@pass_pulp_context
@href_option
@name_option
@acs_lookup_option
def refresh(pulp_ctx: PulpCLIContext, acs_ctx: PulpFileACSContext) -> None:
    acs_ctx.refresh()
