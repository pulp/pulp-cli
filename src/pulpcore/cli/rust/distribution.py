import click

from pulp_glue.common.i18n import get_translation
from pulp_glue.rust.context import (
    PulpRustDistributionContext,
    PulpRustRemoteContext,
    PulpRustRepositoryContext,
)

from pulp_cli.generic import (
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
    pulp_group,
    pulp_labels_option,
    pulp_option,
    resource_option,
    show_command,
    type_option,
    update_command,
)

translation = get_translation(__package__)
_ = translation.gettext


repository_option = resource_option(
    "--repository",
    default_plugin="rust",
    default_type="rust",
    context_table={"rust:rust": PulpRustRepositoryContext},
    href_pattern=PulpRustRepositoryContext.HREF_PATTERN,
    help=_(
        "Repository to be used for auto-distributing."
        " Specified as '[[<plugin>:]<type>:]<name>' or as href."
    ),
)


@pulp_group()
@type_option(
    choices={"rust": PulpRustDistributionContext},
    default="rust",
)
def distribution() -> None:
    pass


lookup_options = [href_option, name_option, distribution_lookup_option]
nested_lookup_options = [distribution_lookup_option]
update_options = [
    repository_option,
    pulp_option(
        "--version",
        type=int,
        help=_(
            "The repository version number to distribute."
            " When unset, the latest version of the repository will be auto-distributed."
        ),
    ),
    resource_option(
        "--remote",
        default_plugin="rust",
        default_type="rust",
        context_table={"rust:rust": PulpRustRemoteContext},
        href_pattern=PulpRustRemoteContext.HREF_PATTERN,
        help=_(
            "Remote to use for pull-through caching."
            " Specified as '[[<plugin>:]<type>:]<name>' or as href."
        ),
    ),
    content_guard_option,
    pulp_labels_option,
    pulp_option(
        "--allow-uploads/--no-allow-uploads",
        is_flag=True,
        default=None,
        help=_("Allow publishing crates via ``cargo publish``."),
    ),
]
create_options = common_distribution_create_options + update_options

distribution.add_command(list_command(decorators=distribution_filter_options))
distribution.add_command(show_command(decorators=lookup_options))
distribution.add_command(create_command(decorators=create_options))
distribution.add_command(
    update_command(decorators=lookup_options + update_options + [click.option("--base-path")])
)
distribution.add_command(destroy_command(decorators=lookup_options))
distribution.add_command(label_command(decorators=nested_lookup_options))
