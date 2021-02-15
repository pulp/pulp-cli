import gettext

import click

from pulpcore.cli.common.context import PulpContext, pass_pulp_context
from pulpcore.cli.common.generic import (
    create_command,
    destroy_command,
    href_option,
    label_command,
    label_select_option,
    list_command,
    name_option,
    show_command,
    update_command,
)
from pulpcore.cli.rpm.context import PulpRpmDistributionContext

_ = gettext.gettext


@click.group()
@click.option(
    "-t",
    "--type",
    "distribution_type",
    type=click.Choice(["rpm"], case_sensitive=False),
    default="rpm",
)
@pass_pulp_context
@click.pass_context
def distribution(ctx: click.Context, pulp_ctx: PulpContext, distribution_type: str) -> None:
    if distribution_type == "rpm":
        ctx.obj = PulpRpmDistributionContext(pulp_ctx)
    else:
        raise NotImplementedError()


lookup_options = [href_option, name_option]
create_options = [
    click.option("--name", required=True),
    click.option("--base-path", required=True),
    click.option("--publication"),
]
update_options = [
    click.option("--base-path"),
    click.option("--publication"),
]

distribution.add_command(list_command(decorators=[label_select_option]))
distribution.add_command(show_command(decorators=lookup_options))
distribution.add_command(create_command(decorators=create_options))
distribution.add_command(update_command(decorators=lookup_options + update_options))
distribution.add_command(destroy_command(decorators=lookup_options))
distribution.add_command(label_command())
