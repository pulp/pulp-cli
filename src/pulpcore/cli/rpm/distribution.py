import click

from pulp_glue.common.context import PluginRequirement
from pulp_glue.common.i18n import get_translation
from pulp_glue.rpm.context import PulpRpmDistributionContext, PulpRpmRepositoryContext

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
    role_command,
    show_command,
    type_option,
    update_command,
)

translation = get_translation(__package__)
_ = translation.gettext

repository_option = resource_option(
    "--repository",
    default_plugin="rpm",
    default_type="rpm",
    context_table={"rpm:rpm": PulpRpmRepositoryContext},
    help=_(
        "Repository to be used for auto-distributing."
        " When set, this will unset the 'publication'."
        " Specified as '[[<plugin>:]<type>:]<name>' or as href."
    ),
    href_pattern=PulpRpmRepositoryContext.HREF_PATTERN,
)


@pulp_group()
@type_option(choices={"rpm": PulpRpmDistributionContext})
def distribution() -> None:
    pass


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
    pulp_option(
        "--generate-repo-config/--no-generate-repo-config",
        default=None,
        help=_("Option specifying whether ``*.repo`` files will be generated and served."),
    ),
    repository_option,
    content_guard_option,
    pulp_labels_option,
    pulp_option(
        "--checkpoint/--not-checkpoint",
        is_flag=True,
        default=None,
        needs_plugins=[PluginRequirement("rpm", specifier=">=3.29.0")],
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
distribution.add_command(role_command(decorators=lookup_options))
