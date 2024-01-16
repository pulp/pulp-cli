import re
import typing as t

import click
from pulp_glue.common.context import (
    EntityDefinition,
    PulpGenericRepositoryContext,
    PulpRepositoryContext,
    PulpRepositoryVersionContext,
)
from pulp_glue.common.i18n import get_translation

from pulpcore.cli.common.generic import (
    PulpCLIContext,
    list_command,
    name_filter_options,
    pass_pulp_context,
    pulp_group,
    pulp_option,
    resource_option,
    version_command,
)

translation = get_translation(__package__)
_ = translation.gettext


def _version_list_callback(
    ctx: click.Context, param: click.Parameter, value: t.Iterable[t.Tuple[str, int]]
) -> t.Iterable[PulpRepositoryVersionContext]:
    result = []
    pulp_ctx = ctx.find_object(PulpCLIContext)
    assert pulp_ctx is not None
    for item in value:
        pulp_href: t.Optional[str] = None
        entity: t.Optional[EntityDefinition] = None

        if item[0].startswith("/"):
            pattern = rf"^{pulp_ctx.api_path}{PulpRepositoryContext.HREF_PATTERN}"
            match = re.match(pattern, item[0])
            if match is None:
                raise click.ClickException(
                    _("'{value}' is not a valid href for {option_name}.").format(
                        value=value, option_name=param.name
                    )
                )
            match_groups = match.groupdict(default="")
            plugin = match_groups.get("plugin", "")
            resource_type = match_groups.get("resource_type", "")
            pulp_href = item[0]
        else:
            plugin, resource_type, identifier = item[0].split(":", maxsplit=2)
            if not identifier:
                raise click.ClickException(_("Repositories must be specified with plugin and type"))
            entity = {"name": identifier}
        context_class = PulpRepositoryContext.TYPE_REGISTRY.get(plugin + ":" + resource_type)
        if context_class is None:
            raise click.ClickException(
                _(
                    "The type '{plugin}:{resource_type}' "
                    "is not valid for the {option_name} option."
                ).format(plugin=plugin, resource_type=resource_type, option_name=param.name)
            )
        repository_ctx: PulpRepositoryContext = context_class(
            pulp_ctx, pulp_href=pulp_href, entity=entity
        )

        entity_ctx = repository_ctx.get_version_context(number=item[1])
        result.append(entity_ctx)

    return result


@pulp_group()
@pass_pulp_context
@click.pass_context
def repository(ctx: click.Context, pulp_ctx: PulpCLIContext) -> None:
    """
    Perform actions on all repositories.

    Please look for the plugin specific repository commands for more detailed actions.
    i.e. 'pulp file repository <...>'
    """
    ctx.obj = PulpRepositoryContext(pulp_ctx)


filter_options = name_filter_options

repository.add_command(list_command(decorators=filter_options))
repository.add_command(version_command(decorators=[], list_only=True))


@repository.command()
@resource_option(
    "--repository",
    "repositories",
    context_table=PulpRepositoryContext.TYPE_REGISTRY,
    multiple=True,
    href_pattern=PulpRepositoryContext.HREF_PATTERN,
    help=_(
        "Repository in the form '[[<plugin>:]<resource_type>:]<name>' or by href."
        " Can be called multiple times."
    ),
)
@pulp_option(
    "--all",
    "all_repositories",
    is_flag=True,
    show_default=True,
    default=False,
    help=_("Select all repositories."),
)
@pulp_option(
    "--keep-version",
    "keep_versions",
    type=tuple([str, int]),
    help=_(
        "Repository version specified as '<repo_name_or_href> <version_number>' to keep unaffected."
        " Can be specified multiple times."
    ),
    callback=_version_list_callback,
    multiple=True,
    required=False,
)
@pass_pulp_context
def reclaim(
    pulp_ctx: PulpCLIContext,
    repositories: t.Iterable[str],
    all_repositories: bool,
    keep_versions: t.Iterable[str],
) -> None:
    if not (repositories or all_repositories):
        raise click.UsageError(_("Either --repository or --all must be specified."))
    elif repositories and all_repositories:
        raise click.UsageError(_("Only one of --repository or --all can be specified."))

    if all_repositories:
        repositories = ["*"]

    PulpGenericRepositoryContext(pulp_ctx=pulp_ctx).reclaim(
        repo_hrefs=list(repositories), repo_versions_keeplist=list(keep_versions)
    )
