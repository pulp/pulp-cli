import gettext
from typing import Iterable

import click

from pulpcore.cli.common.context import (
    PluginRequirement,
    PulpContext,
    PulpRemoteContext,
    pass_entity_context,
    pass_pulp_context,
)
from pulpcore.cli.common.generic import (
    create_command,
    destroy_command,
    href_option,
    list_command,
    name_option,
    resource_option,
    show_command,
    update_command,
)
from pulpcore.cli.rpm.context import PulpRpmACSContext, PulpRpmRemoteContext

_ = gettext.gettext


path_option = click.option(
    "--path", "paths", multiple=True, help=_("path to add to ACS; can be specified multiple times.")
)


@click.group()
@click.option(
    "-t",
    "--type",
    "acs_type",
    type=click.Choice(["rpm"], case_sensitive=False),
    default="rpm",
)
@pass_pulp_context
@click.pass_context
def acs(ctx: click.Context, pulp_ctx: PulpContext, acs_type: str) -> None:
    pulp_ctx.needs_plugin(PluginRequirement("rpm", "3.16.0.dev"))
    if acs_type == "rpm":
        ctx.obj = PulpRpmACSContext(pulp_ctx)
    else:
        raise NotImplementedError()


@acs.group()
def path() -> None:
    """Manage paths for an ACS."""
    pass


@path.command()
@name_option
@href_option
@path_option
@pass_entity_context
def add(acs_ctx: PulpRpmACSContext, paths: Iterable[str]) -> None:
    """Add path(s) to an existing ACS."""
    paths = set(paths)
    href = acs_ctx.entity["pulp_href"]
    existing_paths = set(acs_ctx.show(href)["paths"])

    for path in paths:
        if path in existing_paths:
            raise click.ClickException(_("ACS already has path '{}'.").format(path))

    if existing_paths != {""}:
        paths = set.union(existing_paths, paths)
    acs_ctx.update(href, body={"paths": list(paths)})


@path.command()
@name_option
@href_option
@path_option
@pass_entity_context
def remove(acs_ctx: PulpRpmACSContext, paths: Iterable[str]) -> None:
    """Remove path(s) from an existing ACS."""
    paths = set(paths)
    href = acs_ctx.entity["pulp_href"]
    existing_paths = set(acs_ctx.show(href)["paths"])

    if paths - existing_paths:
        missing_paths = paths - existing_paths
        raise click.ClickException(_("ACS does not have path(s): {}.").format(missing_paths))

    paths = existing_paths - paths
    acs_ctx.update(href, body={"paths": list(paths)})


remote_option = resource_option(
    "--remote",
    default_plugin="rpm",
    default_type="rpm",
    context_table={"rpm:rpm": PulpRpmRemoteContext},
    href_pattern=PulpRemoteContext.HREF_PATTERN,
    help=_("Remote to attach to ACS in the form '[[<plugin>:]<resource_type>:]<name>' or by href."),
)
path_option = click.option(
    "--path",
    "paths",
    multiple=True,
)
lookup_options = [href_option, name_option]
update_options = [remote_option]
create_options = update_options + [click.option("--name", required=True), path_option]

acs.add_command(list_command())
acs.add_command(show_command(decorators=lookup_options))
acs.add_command(create_command(decorators=create_options))
acs.add_command(update_command(decorators=lookup_options + update_options))
acs.add_command(destroy_command(decorators=lookup_options))


@acs.command()
@pass_entity_context
@pass_pulp_context
@href_option
@name_option
def refresh(pulp_ctx: PulpContext, acs_ctx: PulpRpmACSContext) -> None:
    acs_ctx.refresh(acs_ctx.pulp_href)
