import typing as t

import click
from pulp_glue.ansible.context import PulpAnsibleDistributionContext, PulpAnsibleRepositoryContext
from pulp_glue.common.context import (
    EntityDefinition,
    EntityFieldDefinition,
    PluginRequirement,
    PulpContext,
    PulpEntityContext,
)
from pulp_glue.common.i18n import get_translation

from pulpcore.cli.common.generic import (
    content_guard_option,
    create_command,
    destroy_command,
    distribution_filter_options,
    distribution_lookup_option,
    href_option,
    label_command,
    list_command,
    name_option,
    pass_entity_context,
    pass_pulp_context,
    pulp_group,
    pulp_labels_option,
    resource_option,
    show_command,
)

translation = get_translation(__package__)
_ = translation.gettext


repository_option = resource_option(
    "--repository",
    default_plugin="ansible",
    default_type="ansible",
    context_table={"ansible:ansible": PulpAnsibleRepositoryContext},
    href_pattern=PulpAnsibleRepositoryContext.HREF_PATTERN,
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


lookup_options = [href_option, name_option, distribution_lookup_option]
nested_lookup_options = [distribution_lookup_option]
create_options = [
    click.option("--name", required=True),
    click.option(
        "--base-path",
        required=True,
        help=_("the base (relative) path component of the published url."),
    ),
    repository_option,
    content_guard_option,
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
        decorators=nested_lookup_options,
        need_plugins=[
            PluginRequirement("ansible", specifier=">=0.8.0"),
        ],
    )
)


@distribution.command()
@name_option
@href_option
@distribution_lookup_option
@click.option("--base-path", help=_("new base_path"))
@repository_option
@content_guard_option
@click.option(
    "--version",
    type=int,
    default=None,
    help=_("version of new repository to be served, leave blank for always latest"),
)
@pulp_labels_option
@pass_entity_context
def update(
    distribution_ctx: PulpEntityContext,
    base_path: t.Optional[str],
    repository: EntityFieldDefinition,
    content_guard: EntityFieldDefinition,
    version: t.Optional[int],
    pulp_labels: t.Optional[t.Dict[str, str]],
) -> None:
    """
    To remove repository or repository_version fields set --repository to ""
    """
    assert isinstance(distribution_ctx, PulpAnsibleDistributionContext)

    dist_body: EntityDefinition = distribution_ctx.entity
    name: str = dist_body["name"]
    body: EntityDefinition = dict()

    if base_path:
        body["base_path"] = base_path
    if pulp_labels is not None:
        body["pulp_labels"] = pulp_labels
    if content_guard is not None:
        body["content_guard"] = content_guard
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
                    distribution_ctx.update(body={"repository": ""}, non_blocking=True)
                body["repository_version"] = f'{repo["versions_href"]}{version}/'
            else:
                if dist_body["repository_version"]:
                    distribution_ctx.update(body={"repository_version": ""}, non_blocking=True)
                body["repository"] = repo["pulp_href"]
    elif version is not None:
        # keep current repository, change version
        if dist_body["repository"]:
            distribution_ctx.update(body={"repository": ""}, non_blocking=True)
            body["repository_version"] = f'{dist_body["repository"]}versions/{version}/'
        elif dist_body["repository_version"]:
            # 'dummy' vars are to get us around a mypy/1.2 complaint about '_'
            repository_href, dummy, dummy = dist_body["repository_version"].partition("versions")
            body["repository_version"] = f"{repository_href}versions/{version}/"
        else:
            raise click.ClickException(
                _(
                    "Distribution {name} doesn't have a repository set, "
                    "please specify the repository to use  with --repository"
                ).format(name=name)
            )
    distribution_ctx.update(body=body)
