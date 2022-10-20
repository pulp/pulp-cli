from typing import Dict, Optional, Union, cast

import click

from pulpcore.cli.common.context import (
    EntityDefinition,
    PulpContext,
    PulpEntityContext,
    pass_entity_context,
    pass_pulp_context,
)
from pulpcore.cli.common.generic import (
    create_command,
    destroy_command,
    distribution_filter_options,
    href_option,
    label_command,
    list_command,
    name_option,
    pulp_group,
    pulp_labels_option,
    resource_option,
    role_command,
    show_command,
)
from pulpcore.cli.common.i18n import get_translation
from pulpcore.cli.container.context import (
    PulpContainerDistributionContext,
    PulpContainerPushRepositoryContext,
    PulpContainerRepositoryContext,
)

translation = get_translation(__name__)
_ = translation.gettext


repository_option = resource_option(
    "--repository",
    default_plugin="container",
    default_type="container",
    context_table={
        "container:container": PulpContainerRepositoryContext,
        "container:push": PulpContainerPushRepositoryContext,
    },
)


@pulp_group()
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


lookup_options = [href_option, name_option]
create_options = [
    click.option("--name", required=True),
    click.option("--base-path", required=True),
    repository_option,
    click.option(
        "--version", type=int, help=_("a repository version number, leave blank for latest")
    ),
    click.option("--private/--public", default=None),
    pulp_labels_option,
]

distribution.add_command(list_command(decorators=distribution_filter_options))
distribution.add_command(show_command(decorators=lookup_options))
distribution.add_command(create_command(decorators=create_options))
distribution.add_command(destroy_command(decorators=lookup_options))
distribution.add_command(role_command(decorators=lookup_options))
distribution.add_command(label_command())


@distribution.command()
@href_option
@name_option
@click.option("--base-path")
@repository_option
@click.option("--version", type=int, help=_("a repository version number, leave blank for latest"))
@click.option("--private/--public", default=None)
@pulp_labels_option
@pass_entity_context
def update(
    distribution_ctx: PulpContainerDistributionContext,
    base_path: Optional[str],
    repository: Optional[Union[str, PulpEntityContext]],
    version: Optional[int],
    private: Optional[bool],
    pulp_labels: Optional[Dict[str, str]],
) -> None:
    distribution: EntityDefinition = distribution_ctx.entity
    href: str = distribution_ctx.pulp_href
    body: EntityDefinition = {}

    if private is not None:
        body["private"] = private
    if base_path is not None:
        body["base_path"] = base_path
    if pulp_labels is not None:
        body["pulp_labels"] = pulp_labels
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
