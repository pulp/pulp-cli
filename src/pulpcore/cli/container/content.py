import gettext
import typing as t

import click

from pulp_glue.common.context import (
    EntityDefinition,
    PluginRequirement,
    PulpContentContext,
    PulpDistributionContext,
)
from pulp_glue.container.context import (
    PulpContainerBlobContext,
    PulpContainerDistributionContext,
    PulpContainerManifestContext,
    PulpContainerRepositoryContext,
    PulpContainerTagContext,
)

from pulp_cli.generic import (
    PulpCLIContext,
    content_filter_options,
    href_option,
    label_command,
    list_command,
    option_group,
    option_processor,
    pulp_group,
    pulp_option,
    resource_option,
    show_command,
    type_option,
)

_ = gettext.gettext


def _content_callback(ctx: click.Context, value: dict[str, t.Any]) -> None:
    if value:
        entity_ctx = ctx.find_object(PulpContentContext)
        assert entity_ctx is not None
        if isinstance(entity_ctx, PulpContainerTagContext) and len(value) != 2:
            raise click.UsageError(_("Both 'name' and 'digest' are needed to describe a tag."))
        entity_ctx.entity = value


def _repository_version_from_distribution(
    pulp_ctx: PulpCLIContext, distribution: EntityDefinition
) -> str:
    if repository_version := distribution.get("repository_version"):
        return t.cast(str, repository_version)

    repository_href = distribution.get("repository")
    if not repository_href:
        raise click.ClickException(
            _(
                "Distribution '{name}' is not associated with a repository or repository version."
            ).format(name=distribution.get("name", ""))
        )
    repo_ctx = PulpContainerRepositoryContext(pulp_ctx, pulp_href=repository_href)

    return t.cast(str, repo_ctx.entity["latest_version_href"])


def _process_distribution_filter(ctx: click.Context) -> None:
    if distribution := ctx.params.pop("distribution", None):
        if ctx.params.get("repository_version"):
            raise click.UsageError(
                _("Cannot use --distribution together with --repository-version.")
            )

        assert isinstance(distribution, PulpContainerDistributionContext)
        pulp_ctx = ctx.find_object(PulpCLIContext)
        assert pulp_ctx is not None
        ctx.params["repository_version"] = _repository_version_from_distribution(
            pulp_ctx, distribution.entity
        )


@pulp_group()
@type_option(
    choices={
        "blob": PulpContainerBlobContext,
        "manifest": PulpContainerManifestContext,
        "tag": PulpContainerTagContext,
    },
    default="tag",
)
def content() -> None:
    pass


distribution_filter_option = resource_option(
    "--distribution",
    default_plugin="container",
    default_type="container",
    context_table={
        "container:container": PulpContainerDistributionContext,
    },
    href_pattern=PulpDistributionContext.HREF_PATTERN,
    help=_(
        "Filter {entities} by the repository version served by this distribution (name or href)."
    ),
)


list_options = [
    pulp_option(
        "--media-type",
        allowed_with_contexts=(PulpContainerManifestContext, PulpContainerTagContext),
    ),
    pulp_option("--name", "name", allowed_with_contexts=(PulpContainerTagContext,)),
    pulp_option(
        "--name-in",
        "name__in",
        multiple=True,
        allowed_with_contexts=(PulpContainerTagContext,),
    ),
    pulp_option(
        "--digest",
        allowed_with_contexts=(
            PulpContainerManifestContext,
            PulpContainerBlobContext,
            PulpContainerTagContext,
        ),
    ),
    pulp_option(
        "--digest-in",
        "digest__in",
        multiple=True,
        allowed_with_contexts=(PulpContainerManifestContext, PulpContainerBlobContext),
    ),
    pulp_option(
        "--is-bootable",
        is_flag=True,
        default=None,
        allowed_with_contexts=(PulpContainerManifestContext,),
    ),
    pulp_option(
        "--is-flatpak",
        is_flag=True,
        default=None,
        allowed_with_contexts=(PulpContainerManifestContext,),
    ),
    *content_filter_options,
    distribution_filter_option,
    option_processor(callback=_process_distribution_filter),
]

lookup_options = [
    pulp_option(
        "--digest",
        help=_("Digest associated with {entity}"),
    ),
    pulp_option(
        "--name",
        help=_("Name of {entity}"),
        allowed_with_contexts=(PulpContainerTagContext,),
    ),
    href_option,
    option_group(
        "content",
        ["name", "digest"],
        callback=_content_callback,
        require_all=False,
        expose_value=False,
    ),
]

content.add_command(list_command(decorators=list_options))
content.add_command(show_command(decorators=lookup_options))
content.add_command(
    label_command(
        decorators=lookup_options,
        need_plugins=[PluginRequirement("core", specifier=">=3.73.2")],
    )
)
