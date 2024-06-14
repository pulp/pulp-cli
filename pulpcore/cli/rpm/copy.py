import gettext
import typing as t

import click
from pulp_glue.rpm.context import PulpRpmCopyContext

from pulpcore.cli.common.generic import (
    PulpCLIContext,
    load_json_callback,
    pass_pulp_context,
    pulp_command,
)

_ = gettext.gettext


@pulp_command()
@click.option(
    "--config",
    callback=load_json_callback,
    help=_(
        """
        A JSON document describing sources, destinations, and content to be copied. It has the
        format `[{"source_repo_version": repo-version-href, "dest_repo": repo-href,
        "content": [content-href,...]},...]`

         The argument prefixed with an '@' is interpreted as the path to a JSON file.
        """
    ),
)
@click.option(
    "--dependency-solving",
    type=bool,
    is_flag=True,
    show_default=True,
    default=False,
    help=_("Copy dependencies of the explicitly-defined content being copied."),
)
@pass_pulp_context
def copy(
    pulp_ctx: PulpCLIContext,
    config: t.List[t.Dict[str, t.Any]],
    dependency_solving: t.Optional[bool],
) -> None:
    """ """
    copy_ctx = PulpRpmCopyContext(pulp_ctx)
    result = copy_ctx.copy(config, dependency_solving)
    pulp_ctx.output_result(result)
