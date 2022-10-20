from typing import Dict, Optional

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
    show_command,
)
from pulpcore.cli.common.i18n import get_translation

translation = get_translation(__name__)
_ = translation.gettext


repository_option = resource_option(
    "--repository",
    default_plugin="ansible",
    default_type="ansible",
    context_table={"ansible:ansible": PulpAnsibleRepositoryContext},
)


@pulp_group()
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


lookup_options = [href_option, name_option]
create_options = [
    click.option("--name", required=True),
    click.option(
        "--base-path",
        required=True,
        help=_("the base (relative) path component of the published url."),
    ),
    repository_option,
    click.option(
        "--version", type=int, help=_("a repository version number, leave blank for latest")
    ),
    pulp_labels_option,
]
distribution.add_command(list_command(decorators=distribution_filter_options))
distribution.add_command(show_command(decorators=lookup_options))
distribution.add_command(destroy_command(decorators=lookup_options))
distribution.add_command(create_command(decorators=create_options))
distribution.add_command(
    label_command(
        need_plugins=[
            PluginRequirement("ansible", "0.8.0"),
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
@pulp_labels_option
@pass_entity_context
def update(
    distribution_ctx: PulpAnsibleDistributionContext,
    base_path: Optional[str],
    repository: EntityFieldDefinition,
    version: Optional[int],
    pulp_labels: Optional[Dict[str, str]],
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
    if pulp_labels is not None:
        body["pulp_labels"] = pulp_labels
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
                _(
                    "Distribution {name} doesn't have a repository set, "
                    "please specify the repository to use  with --repository"
                ).format(name=name)
            )
    distribution_ctx.update(href, body=body)
