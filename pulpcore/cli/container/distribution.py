import gettext
from typing import Optional, Union, cast

import click

from pulpcore.cli.common.context import (
    EntityDefinition,
    PulpContext,
    PulpEntityContext,
    pass_entity_context,
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
    resource_option,
    show_command,
)
from pulpcore.cli.container.context import (
    PulpContainerDistributionContext,
    PulpContainerPushRepositoryContext,
    PulpContainerRepositoryContext,
)

_ = gettext.gettext


repository_option = resource_option(
    "--repository",
    default_plugin="container",
    default_type="container",
    context_table={
        "container:container": PulpContainerRepositoryContext,
        "container:push": PulpContainerPushRepositoryContext,
    },
)


@click.group()
@click.option(
    "-t",
    "--type",
    "distribution_type",
    type=click.Choice(["container"], case_sensitive=False),
    default="container",
)
@pass_pulp_context
@click.pass_context
def distribution(ctx: click.Context, pulp_ctx: PulpContext, distribution_type: str) -> None:
    if distribution_type == "container":
        ctx.obj = PulpContainerDistributionContext(pulp_ctx)
    else:
        raise NotImplementedError()


filter_options = [label_select_option, base_path_option, base_path_contains_option]
lookup_options = [href_option, name_option]
create_options = [
    click.option("--name", required=True),
    click.option("--base-path", required=True),
    repository_option,
    click.option(
        "--version", type=int, help=_("a repository version number, leave blank for latest")
    ),
]

distribution.add_command(list_command(decorators=filter_options))
distribution.add_command(show_command(decorators=lookup_options))
distribution.add_command(create_command(decorators=create_options))
distribution.add_command(destroy_command(decorators=lookup_options))
distribution.add_command(label_command())


@distribution.command()
@href_option
@name_option
@click.option("--base-path")
@repository_option
@click.option("--version", type=int, help=_("a repository version number, leave blank for latest"))
@pass_entity_context
@pass_pulp_context
def update(
    pulp_ctx: PulpContext,
    distribution_ctx: PulpContainerDistributionContext,
    base_path: Optional[str],
    repository: Optional[Union[str, PulpEntityContext]],
    version: Optional[int],
) -> None:
    distribution: EntityDefinition = distribution_ctx.entity
    href: str = distribution_ctx.pulp_href
    body: EntityDefinition = {}

    if base_path is not None:
        body["base_path"] = base_path
    if repository is not None:
        if repository == "":
            # unset repository or repository version
            if distribution["repository"]:
                body["repository"] = ""
            elif distribution["repository_version"]:
                body["repository_version"] = ""
        else:
            repository = cast(PulpEntityContext, repository)
            if version is not None:
                if distribution["repository"]:
                    distribution_ctx.update(href, body={"repository": ""}, non_blocking=True)
                body["repository_version"] = f"{repository.pulp_href}versions/{version}/"
            else:
                if distribution["repository_version"]:
                    distribution_ctx.update(
                        href, body={"repository_version": ""}, non_blocking=True
                    )
                body["repository"] = repository.pulp_href
    elif version is not None:
        # keep current repository, change version
        if distribution["repository"]:
            distribution_ctx.update(href, body={"repository": ""}, non_blocking=True)
            body["repository_version"] = f'{distribution["repository"]}versions/{version}/'
        elif distribution["repository_version"]:
            repository_href, _, _ = distribution["repository_version"].partition("versions")
            body["repository_version"] = f"{repository_href}versions/{version}/"
        else:
            raise click.ClickException(
                _(
                    "Distribution {distribution} doesn't have a repository set, "
                    "please specify the repository to use  with --repository"
                ).format(distribution=distribution["name"])
            )
    distribution_ctx.update(href, body=body)
