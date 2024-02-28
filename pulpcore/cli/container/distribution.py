import typing as t

import click
from pulp_glue.common.context import (
    EntityDefinition,
    EntityFieldDefinition,
    PulpEntityContext,
    PulpRepositoryContext,
)
from pulp_glue.common.i18n import get_translation
from pulp_glue.container.context import (
    PulpContainerDistributionContext,
    PulpContainerPushRepositoryContext,
    PulpContainerRepositoryContext,
)

from pulpcore.cli.common.generic import (
    PulpCLIContext,
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
    role_command,
    show_command,
)

translation = get_translation(__package__)
_ = translation.gettext


repository_option = resource_option(
    "--repository",
    default_plugin="container",
    default_type="container",
    context_table={
        "container:container": PulpContainerRepositoryContext,
        "container:push": PulpContainerPushRepositoryContext,
    },
    href_pattern=PulpRepositoryContext.HREF_PATTERN,
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
def distribution(ctx: click.Context, pulp_ctx: PulpCLIContext, distribution_type: str) -> None:
    if distribution_type == "container":
        ctx.obj = PulpContainerDistributionContext(pulp_ctx)
    else:
        raise NotImplementedError()


lookup_options = [href_option, name_option, distribution_lookup_option]
nested_lookup_options = [distribution_lookup_option]
create_options = [
    click.option("--name", required=True),
    click.option("--base-path", required=True),
    repository_option,
    content_guard_option,
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
distribution.add_command(label_command(decorators=nested_lookup_options))


@distribution.command()
@href_option
@name_option
@distribution_lookup_option
@click.option("--base-path")
@repository_option
@content_guard_option
@click.option("--version", type=int, help=_("a repository version number, leave blank for latest"))
@click.option("--private/--public", default=None)
@pulp_labels_option
@pass_entity_context
def update(
    distribution_ctx: PulpEntityContext,
    base_path: t.Optional[str],
    repository: t.Optional[t.Union[str, PulpEntityContext]],
    content_guard: EntityFieldDefinition,
    version: t.Optional[int],
    private: t.Optional[bool],
    pulp_labels: t.Optional[t.Dict[str, str]],
) -> None:
    assert isinstance(distribution_ctx, PulpContainerDistributionContext)

    distribution: EntityDefinition = distribution_ctx.entity
    body: EntityDefinition = {}

    if private is not None:
        body["private"] = private
    if base_path is not None:
        body["base_path"] = base_path
    if pulp_labels is not None:
        body["pulp_labels"] = pulp_labels
    if content_guard is not None:
        body["content_guard"] = content_guard
    if repository is not None:
        if repository == "":
            # unset repository or repository version
            if distribution["repository"]:
                body["repository"] = ""
            elif distribution["repository_version"]:
                body["repository_version"] = ""
        else:
            repository = t.cast(PulpEntityContext, repository)
            if version is not None:
                if distribution["repository"]:
                    distribution_ctx.update(body={"repository": ""}, non_blocking=True)
                body["repository_version"] = f"{repository.pulp_href}versions/{version}/"
            else:
                if distribution["repository_version"]:
                    distribution_ctx.update(body={"repository_version": ""}, non_blocking=True)
                body["repository"] = repository.pulp_href
    elif version is not None:
        # keep current repository, change version
        if distribution["repository"]:
            distribution_ctx.update(body={"repository": ""}, non_blocking=True)
            body["repository_version"] = f'{distribution["repository"]}versions/{version}/'
        elif distribution["repository_version"]:
            # 'dummy' vars are to get us around a mypy/1.2 complaint about '_'
            repository_href, dummy, dummy = distribution["repository_version"].partition("versions")
            body["repository_version"] = f"{repository_href}versions/{version}/"
        else:
            raise click.ClickException(
                _(
                    "Distribution {distribution} doesn't have a repository set, "
                    "please specify the repository to use  with --repository"
                ).format(distribution=distribution["name"])
            )
    distribution_ctx.update(body=body)
