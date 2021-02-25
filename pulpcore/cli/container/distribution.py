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
    list_command,
    name_option,
    show_command,
)
from pulpcore.cli.container.context import (
    PulpContainerDistributionContext,
    PulpContainerPushRepositoryContext,
    PulpContainerRepositoryContext,
)

_ = gettext.gettext


def _repository_callback(
    ctx: click.Context, param: click.Parameter, value: Optional[str]
) -> Union[None, str, PulpEntityContext]:
    # Pass None and "" verbatim
    if value:
        pulp_ctx: PulpContext = ctx.find_object(PulpContext)
        entity_ctx = ctx.find_object(PulpEntityContext)
        if entity_ctx.meta.get("repository_type") == "container":
            return PulpContainerRepositoryContext(pulp_ctx, entity={"name": value})
        elif entity_ctx.meta.get("repository_type") == "push":
            return PulpContainerPushRepositoryContext(pulp_ctx, entity={"name": value})
        else:
            raise NotImplementedError()
    return value


def _repository_type_callback(
    ctx: click.Context, param: click.Parameter, value: Optional[str]
) -> Optional[str]:
    entity_ctx = ctx.find_object(PulpEntityContext)
    entity_ctx.meta["repository_type"] = value
    return value


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


filter_options = [base_path_option, base_path_contains_option]
lookup_options = [href_option, name_option]
create_options = [
    click.option("--name", required=True),
    click.option("--base-path", required=True),
    click.option("--repository", callback=_repository_callback),
    click.option(
        "--version", type=int, help=_("a repository version number, leave blank for latest")
    ),
    click.option(
        "-t",
        "--repository-type",
        "repository_type",
        type=click.Choice(["container", "push"], case_sensitive=False),
        default="container",
        is_eager=True,
        expose_value=False,
        callback=_repository_type_callback,
    ),
]

distribution.add_command(list_command(decorators=filter_options))
distribution.add_command(show_command(decorators=lookup_options))
distribution.add_command(create_command(decorators=create_options))
distribution.add_command(destroy_command(decorators=lookup_options))


@distribution.command()
@href_option
@name_option
@click.option("--base-path")
@click.option("--repository", callback=_repository_callback)
@click.option("--version", type=int, help=_("a repository version number, leave blank for latest"))
@click.option(
    "-t",
    "--repository-type",
    "repository_type",
    type=click.Choice(["container", "push"], case_sensitive=False),
    default="container",
    is_eager=True,
    expose_value=False,
    callback=_repository_type_callback,
)
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
