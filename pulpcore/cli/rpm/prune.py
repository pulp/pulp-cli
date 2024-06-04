import gettext
import typing as t

import click
from pulp_glue.common.context import PulpException
from pulp_glue.rpm.context import PulpRpmPruneContext, PulpRpmRepositoryContext

from pulpcore.cli.common.generic import (
    PulpCLIContext,
    pass_pulp_context,
    pulp_command,
    resource_option,
)

_ = gettext.gettext

multi_repository_option = resource_option(
    "--repository",
    "repositories",
    default_plugin="rpm",
    default_type="rpm",
    context_table={"rpm:rpm": PulpRpmRepositoryContext},
    multiple=True,
    href_pattern=PulpRpmRepositoryContext.HREF_PATTERN,
    help=_(
        "RPM Repository to prune, in the form 'rpm:rpm:<name>' or by href."
        " Can be called multiple times."
    ),
)


@pulp_command()
@multi_repository_option
@click.option(
    "--all-repositories",
    type=bool,
    is_flag=True,
    show_default=True,
    default=False,
    help=_("Prune *all* repositories accessible to the invoking user."),
)
@click.option(
    "--keep-days",
    type=int,
    default=14,
    help=_("Prune packages that were added to the specified repositories more than N days ago."),
)
@click.option(
    "--dry-run",
    type=bool,
    is_flag=True,
    show_default=True,
    default=False,
    help=_("Evaluate the prune-status of the specified repositories but DO NOT make any changes."),
)
@pass_pulp_context
def prune_packages(
    pulp_ctx: PulpCLIContext,
    repositories: t.Iterable[PulpRpmRepositoryContext],
    all_repositories: t.Optional[bool],
    keep_days: t.Optional[int],
    dry_run: t.Optional[bool],
) -> None:
    """
    Prune older Packages from the current-version of a repository/repositories.

    Repositories can be specified by repeated --repository arguments.

    "All" repositories can be specified by --all-repositories.

    At least one repository, or --all-repositories, must be specified.

    You may not specify --all-repositories *and* one or more specific repositories.
    """
    prune_ctx = PulpRpmPruneContext(pulp_ctx)
    if not (all_repositories or repositories):
        raise PulpException(
            _("at least one --repository, or --all-repositories, must be specified")
        )
    elif all_repositories and repositories:
        raise PulpException(
            _("cannot specify --all-repositories and --repository at the same time")
        )

    repos_list: t.List[t.Union[str, PulpRpmRepositoryContext]] = (
        ["*"] if all_repositories else list(repositories)
    )

    result = prune_ctx.prune_packages(repos_list, keep_days, dry_run)
    pulp_ctx.output_result(result)
