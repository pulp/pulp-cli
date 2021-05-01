from typing import Optional, Union

import click

from pulpcore.cli.common.context import (
    PluginRequirement,
    PulpContext,
    PulpEntityContext,
    pass_pulp_context,
)
from pulpcore.cli.common.generic import (
    base_path_contains_option,
    base_path_option,
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
)
from pulpcore.cli.python.context import PulpPythonDistributionContext, PulpPythonRepositoryContext


def _repository_callback(
    ctx: click.Context, param: click.Parameter, value: Optional[str]
) -> Optional[Union[str, PulpEntityContext]]:
    if value:
        pulp_ctx: PulpContext = ctx.find_object(PulpContext)
        return PulpPythonRepositoryContext(pulp_ctx, entity={"name": value})
    return value


@click.group()
@click.option(
    "-t",
    "--type",
    "distribution_type",
    type=click.Choice(["python"], case_sensitive=False),
    default="python",
)
@pass_pulp_context
@click.pass_context
def distribution(ctx: click.Context, pulp_ctx: PulpContext, distribution_type: str) -> None:
    if distribution_type == "python":
        ctx.obj = PulpPythonDistributionContext(pulp_ctx)
    else:
        raise NotImplementedError()


filter_options = [label_select_option, base_path_option, base_path_contains_option]
lookup_options = [href_option, name_option]
create_options = [
    click.option("--name", required=True),
    click.option("--base-path", required=True),
    click.option("--publication"),
    pulp_option(
        "--repository",
        callback=_repository_callback,
        needs_plugins=[PluginRequirement("python", "3.3.0.dev")],
    ),
]
update_options = [
    click.option("--base-path"),
    click.option("--publication"),
    pulp_option(
        "--repository",
        callback=_repository_callback,
        needs_plugins=[PluginRequirement("python", "3.3.0.dev")],
    ),
]

distribution.add_command(list_command(decorators=filter_options))
distribution.add_command(show_command(decorators=lookup_options))
distribution.add_command(destroy_command(decorators=lookup_options))
distribution.add_command(create_command(decorators=create_options))
distribution.add_command(update_command(decorators=lookup_options + update_options))
distribution.add_command(label_command())
