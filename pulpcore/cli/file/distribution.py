from typing import Optional

import click

from pulpcore.cli.common.context import PulpContext, pass_entity_context, pass_pulp_context
from pulpcore.cli.common.generic import (
    destroy_command,
    href_option,
    label_command,
    label_select_option,
    list_command,
    name_option,
    show_command,
)
from pulpcore.cli.file.context import PulpFileDistributionContext


@click.group()
@click.option(
    "-t",
    "--type",
    "distribution_type",
    type=click.Choice(["file"], case_sensitive=False),
    default="file",
)
@pass_pulp_context
@click.pass_context
def distribution(ctx: click.Context, pulp_ctx: PulpContext, distribution_type: str) -> None:
    if distribution_type == "file":
        ctx.obj = PulpFileDistributionContext(pulp_ctx)
    else:
        raise NotImplementedError()


lookup_options = [href_option, name_option]

distribution.add_command(list_command(decorators=[label_select_option]))
distribution.add_command(show_command(decorators=lookup_options))
distribution.add_command(destroy_command(decorators=lookup_options))
distribution.add_command(label_command())


@distribution.command()
@click.option("--name", required=True)
@click.option("--base-path", required=True)
@click.option("--publication")
@pass_entity_context
@pass_pulp_context
def create(
    pulp_ctx: PulpContext,
    distribution_ctx: PulpFileDistributionContext,
    name: str,
    base_path: str,
    publication: Optional[str],
) -> None:
    body = {"name": name, "base_path": base_path}
    if publication:
        body["publication"] = publication
    result = distribution_ctx.create(body=body)
    distribution = distribution_ctx.show(result["created_resources"][0])
    pulp_ctx.output_result(distribution)


@distribution.command()
@name_option
@href_option
@click.option("--base-path")
@click.option("--publication")
@pass_entity_context
@pass_pulp_context
def update(
    pulp_ctx: PulpContext,
    distribution_ctx: PulpFileDistributionContext,
    base_path: Optional[str],
    publication: Optional[str],
) -> None:
    distribution = distribution_ctx.entity
    distribution_href = distribution_ctx.pulp_href

    if (base_path is not None) and (base_path != distribution["base_path"]):
        distribution["base_path"] = base_path

    if publication is not None:
        distribution["publication"] = None if publication == "" else publication

    distribution_ctx.update(distribution_href, body=distribution)
