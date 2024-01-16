import typing as t

import click
from pulp_glue.common.context import PulpACSContext, PulpRemoteContext
from pulp_glue.common.i18n import get_translation

from pulpcore.cli.common.generic import (
    PulpCLIContext,
    acs_lookup_option,
    create_command,
    destroy_command,
    href_option,
    list_command,
    name_option,
    pass_acs_context,
    pass_pulp_context,
    pulp_group,
    resource_option,
    role_command,
    show_command,
    type_option,
    update_command,
)

translation = get_translation(__package__)
_ = translation.gettext


path_option = click.option(
    "--path", "paths", multiple=True, help=_("path to add to ACS; can be specified multiple times.")
)


def acs_command(
    acs_contexts: t.Dict[str, t.Type[PulpACSContext]],
    remote_context_table: t.Dict[str, t.Type[PulpRemoteContext]],
) -> click.Command:
    default_remote_plugin, default_remote_type = list(remote_context_table.keys())[0].split(":")

    @pulp_group()
    @type_option(choices=acs_contexts)
    def acs() -> None:
        pass

    @acs.group()
    def path() -> None:
        """Manage paths for an ACS."""
        pass

    @path.command()
    @name_option
    @href_option
    @acs_lookup_option
    @path_option
    @pass_acs_context
    def add(acs_ctx: PulpACSContext, paths: t.Iterable[str]) -> None:
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
    @pass_acs_context
    def remove(acs_ctx: PulpACSContext, paths: t.Iterable[str]) -> None:
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
        default_plugin=default_remote_plugin,
        default_type=default_remote_type,
        context_table=remote_context_table,
        href_pattern=PulpRemoteContext.HREF_PATTERN,
        help=_(
            "Remote to attach to ACS in the form '[[<plugin>:]<resource_type>:]<name>' or by href."
        ),
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
    @acs_lookup_option
    @href_option
    @name_option
    @pass_acs_context
    @pass_pulp_context
    def refresh(pulp_ctx: PulpCLIContext, acs_ctx: PulpACSContext) -> None:
        acs_ctx.refresh()

    return acs
