from typing import Optional

import click

from pulpcore.cli.ansible.context import (
    PulpAnsibleDistributionContext,
    PulpAnsibleRepositoryContext,
)
from pulpcore.cli.common.context import (
    EntityDefinition,
    PulpContext,
    pass_entity_context,
    pass_pulp_context,
)
from pulpcore.cli.common.generic import destroy_by_name, list_entities, show_by_name


@click.group()
@click.option(
    "-t",
    "--type",
    "distribution_type",
    type=click.Choice(["ansible"], case_sensitive=False),
    default="ansible",
)
@pass_pulp_context
@click.pass_context
def distribution(ctx: click.Context, pulp_ctx: PulpContext, distribution_type: str) -> None:
    if distribution_type == "ansible":
        ctx.obj = PulpAnsibleDistributionContext(pulp_ctx)
    else:
        raise NotImplementedError()


distribution.add_command(list_entities)
distribution.add_command(show_by_name)
distribution.add_command(destroy_by_name)


# TODO Add content_guard option
@distribution.command()
@click.option("--name", required=True)
@click.option("--base-path", required=True)
@click.option("--repository", help="name of repository")
@click.option("--version", type=int, help="version of repository, leave blank for always latest")
@pass_entity_context
@pass_pulp_context
def create(
    pulp_ctx: PulpContext,
    distribution_ctx: PulpAnsibleDistributionContext,
    name: str,
    base_path: str,
    repository: Optional[str],
    version: Optional[int],
) -> None:
    """Creates a distribution at base-path for repository's content to be discovered at"""
    body: EntityDefinition = {"name": name, "base_path": base_path}
    repo: EntityDefinition = PulpAnsibleRepositoryContext(pulp_ctx).find(name=repository)
    if version is not None and not repository:
        click.ClickException("You must set --repository when using version")
    elif version is not None:
        body["repository_version"] = f'{repo["versions_href"]}{version}/'
    elif repository:
        body["repository"] = repo["pulp_href"]
    result = distribution_ctx.create(body=body)
    pulp_ctx.output_result(result)


@distribution.command()
@click.option("--name", required=True)
@click.option("--base-path", help="new base_path")
@click.option("--repository", type=str, default=None, help="new repository to be served")
@click.option(
    "--version",
    type=int,
    default=None,
    help="version of new repository to be served, leave blank for always latest",
)
@pass_entity_context
@pass_pulp_context
def update(
    pulp_ctx: PulpContext,
    distribution_ctx: PulpAnsibleDistributionContext,
    name: str,
    base_path: Optional[str],
    repository: Optional[str],
    version: Optional[int],
) -> None:
    """
    To remove repository or repository_version fields set --repository to ""
    """
    dist_body: EntityDefinition = distribution_ctx.find(name=name)
    href: str = dist_body["pulp_href"]
    body: EntityDefinition = dict()

    if base_path:
        body["base_path"] = base_path
    if repository is not None:
        if repository == "":
            # unset repository or repository version
            if dist_body["repository"]:
                body["repository"] = ""
            elif dist_body["repository_version"]:
                body["repository_version"] = ""
        else:
            repo = PulpAnsibleRepositoryContext(pulp_ctx).find(name=repository)
            if version is not None:
                if dist_body["repository"]:
                    distribution_ctx.update(href, body={"repository": ""}, non_blocking=True)
                body["repository_version"] = f'{repo["versions_href"]}{version}/'
            else:
                if dist_body["repository_version"]:
                    distribution_ctx.update(
                        href, body={"repository_version": ""}, non_blocking=True
                    )
                body["repository"] = repo["pulp_href"]
    elif version is not None:
        # keep current repository, change version
        if dist_body["repository"]:
            distribution_ctx.update(href, body={"repository": ""}, non_blocking=True)
            body["repository_version"] = f'{dist_body["repository"]}versions/{version}/'
        elif dist_body["repository_version"]:
            repository_href, _, _ = dist_body["repository_version"].partition("versions")
            body["repository_version"] = f"{repository_href}versions/{version}/"
        else:
            raise click.ClickException(
                f"Distribution {name} doesn't have a repository set, "
                f"please specify the repository to use  with --repository"
            )
    distribution_ctx.update(href, body=body)
