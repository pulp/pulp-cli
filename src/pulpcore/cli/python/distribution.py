import typing as t

import click

from pulp_glue.common.context import (
    EntityDefinition,
    EntityFieldDefinition,
    PluginRequirement,
    PulpEntityContext,
)
from pulp_glue.common.i18n import get_translation
from pulp_glue.python.context import (
    PulpPythonDistributionContext,
    PulpPythonRemoteContext,
    PulpPythonRepositoryContext,
)

from pulp_cli.generic import (
    PulpCLIContext,
    common_distribution_create_options,
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
    pulp_option,
    resource_option,
    show_command,
)

translation = get_translation(__package__)
_ = translation.gettext


repository_option = resource_option(
    "--repository",
    default_plugin="python",
    default_type="python",
    context_table={"python:python": PulpPythonRepositoryContext},
    help=_(
        "Repository to be used for auto-distributing."
        " When used with --version, this will create repository_version instead."
        " When set, this will unset the 'publication'."
        " Specified as '[[<plugin>:]<type>:]<name>' or as href."
    ),
    href_pattern=PulpPythonRepositoryContext.HREF_PATTERN,
)


@pulp_group()
@click.option(
    "-t",
    "--type",
    "distribution_type",
    type=click.Choice(["python"], case_sensitive=False),
    default="python",
)
@pass_pulp_context
@click.pass_context
def distribution(ctx: click.Context, pulp_ctx: PulpCLIContext, /, distribution_type: str) -> None:
    if distribution_type == "python":
        ctx.obj = PulpPythonDistributionContext(pulp_ctx)
    else:
        raise NotImplementedError()


lookup_options = [href_option, name_option, distribution_lookup_option]
nested_lookup_options = [distribution_lookup_option]
update_options = [
    click.option(
        "--publication",
        help=_(
            "Publication to be served. This will unset the 'repository' and disable "
            "auto-distribute."
        ),
    ),
    repository_option,
    pulp_option(
        "--version",
        type=int,
        help=_("A repository version number, leave blank for latest."),
        needs_plugins=[PluginRequirement("python", specifier=">=3.21.0")],
    ),
    content_guard_option,
    pulp_option(
        "--allow-uploads/--block-uploads",
        needs_plugins=[PluginRequirement("python", specifier=">=3.4.0")],
        default=None,
    ),
    resource_option(
        "--remote",
        default_plugin="python",
        default_type="python",
        context_table={"python:python": PulpPythonRemoteContext},
        needs_plugins=[PluginRequirement("python", specifier=">=3.6.0")],
        href_pattern=PulpPythonRemoteContext.HREF_PATTERN,
    ),
    pulp_labels_option,
]
create_options = common_distribution_create_options + update_options

distribution.add_command(list_command(decorators=distribution_filter_options))
distribution.add_command(show_command(decorators=lookup_options))
distribution.add_command(create_command(decorators=create_options))
distribution.add_command(destroy_command(decorators=lookup_options))
distribution.add_command(label_command(decorators=nested_lookup_options))


def apply_decorators(decorators_list: list[t.Callable[..., t.Any]]) -> t.Callable[..., t.Any]:
    def decorator(func: t.Callable[..., t.Any]) -> t.Callable[..., t.Any]:
        for d in decorators_list:
            func = d(func)
        return func

    return decorator


@distribution.command()
@apply_decorators(lookup_options + update_options + [click.option("--base-path")])
@pass_entity_context
def update(
    distribution_ctx: PulpEntityContext,
    /,
    publication: str | None,
    repository: EntityFieldDefinition,
    version: int | None,
    content_guard: EntityFieldDefinition,
    allow_uploads: bool | None,
    remote: EntityFieldDefinition,
    pulp_labels: dict[str, str] | None,
    base_path: str | None,
) -> None:
    """
    Update a Python distribution.
    """
    assert isinstance(distribution_ctx, PulpPythonDistributionContext)

    dist_body: EntityDefinition = distribution_ctx.entity
    body: EntityDefinition = dict()

    if publication is not None:
        body["publication"] = publication
    if content_guard is not None:
        body["content_guard"] = content_guard
    if allow_uploads is not None:
        body["allow_uploads"] = allow_uploads
    if remote is not None:
        body["remote"] = remote
    if pulp_labels is not None:
        body["pulp_labels"] = pulp_labels
    if base_path is not None:
        body["base_path"] = base_path

    if repository is not None and isinstance(repository, PulpPythonRepositoryContext):
        repo = repository.entity
        if version is not None:
            if dist_body.get("repository"):
                distribution_ctx.update(body={"repository": ""}, non_blocking=True)
            body["repository_version"] = f"{repo['versions_href']}{version}/"
        else:
            if dist_body.get("repository_version"):
                distribution_ctx.update(body={"repository_version": ""}, non_blocking=True)
            body["repository"] = repo["pulp_href"]
    elif version is not None:
        if dist_body.get("repository"):
            distribution_ctx.update(body={"repository": ""}, non_blocking=True)
            body["repository_version"] = f"{dist_body['repository']}versions/{version}/"
        elif dist_body.get("repository_version"):
            repository_href = dist_body["repository_version"].partition("versions")[0]
            body["repository_version"] = f"{repository_href}versions/{version}/"
        else:
            raise click.ClickException(
                _(
                    "Distribution doesn't have a repository set, "
                    "please specify the repository to use with --repository"
                )
            )
    distribution_ctx.update(body=body)
