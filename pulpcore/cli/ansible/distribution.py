import gettext
from typing import Optional

import click

from pulpcore.cli.ansible.context import (
    PulpAnsibleDistributionContext,
    PulpAnsibleRepositoryContext,
)
from pulpcore.cli.common.context import (
    EntityDefinition,
    EntityFieldDefinition,
    PluginRequirement,
    PulpContext,
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
    show_command,
)

_ = gettext.gettext


def _repository_callback(
    ctx: click.Context, param: click.Parameter, value: Optional[str]
) -> EntityFieldDefinition:
    # Pass None and "" verbatim
    if value:
        pulp_ctx: PulpContext = ctx.find_object(PulpContext)
        return PulpAnsibleRepositoryContext(pulp_ctx, entity={"name": value})
    return value


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


filter_options = [label_select_option, base_path_option, base_path_contains_option]
lookup_options = [href_option, name_option]
create_options = [
    click.option("--name", required=True),
    click.option(
        "--base-path",
        required=True,
        help=_("the base (relative) path component of the published url."),
    ),
    click.option(
        "--repository",
        required=True,
        callback=_repository_callback,
        help=_("repository with content to distribute"),
    ),
    click.option(
        "--version", type=int, help=_("a repository version number, leave blank for latest")
    ),
]
distribution.add_command(list_command(decorators=filter_options))
distribution.add_command(show_command(decorators=lookup_options))
distribution.add_command(destroy_command(decorators=lookup_options))
distribution.add_command(create_command(decorators=create_options))
distribution.add_command(
    label_command(
        need_plugins=[
            PluginRequirement("core", "3.10.0"),
            PluginRequirement("ansible", "0.8.0.dev"),
        ]
    )
)


# TODO Add content_guard option
@distribution.command()
@name_option
@href_option
@click.option("--base-path", help=_("new base_path"))
@click.option("--repository", type=str, default=None, help=_("new repository to be served"))
@click.option(
    "--version",
    type=int,
    default=None,
    help=_("version of new repository to be served, leave blank for always latest"),
)
@pass_entity_context
def update(
    distribution_ctx: PulpAnsibleDistributionContext,
    base_path: Optional[str],
    repository: EntityFieldDefinition,
    version: Optional[int],
) -> None:
    """
    To remove repository or repository_version fields set --repository to ""
    """
    dist_body: EntityDefinition = distribution_ctx.entity
    href: str = dist_body["pulp_href"]
    name: str = dist_body["name"]
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
        elif isinstance(repository, PulpAnsibleRepositoryContext):
            repo = repository.entity
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
