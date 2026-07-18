import click

from pulp_glue.common.context import PulpRemoteContext, PulpRepositoryContext
from pulp_glue.common.i18n import get_translation
from pulp_glue.hugging_face.context import (
    PulpHuggingFaceDistributionContext,
    PulpHuggingFaceRemoteContext,
    PulpHuggingFaceRepositoryContext,
)

from pulp_cli.generic import (
    common_distribution_create_options,
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
    resource_option,
    show_command,
    type_option,
    update_command,
)

translation = get_translation(__package__)
_ = translation.gettext


remote_option = resource_option(
    "--remote",
    default_plugin="hugging_face",
    default_type="hugging-face",
    context_table={"hugging_face:hugging-face": PulpHuggingFaceRemoteContext},
    href_pattern=PulpRemoteContext.HREF_PATTERN,
    help=_(
        "Hugging Face remote to use for pull-through caching."
        " Specified as '[[<plugin>:]<type>:]<name>' or as href."
        " Pass an empty string to detach the remote."
    ),
)
repository_option = resource_option(
    "--repository",
    default_plugin="hugging_face",
    default_type="hugging-face",
    context_table={"hugging_face:hugging-face": PulpHuggingFaceRepositoryContext},
    href_pattern=PulpRepositoryContext.HREF_PATTERN,
    help=_(
        "Hugging Face repository whose latest version is served."
        " Specified as '[[<plugin>:]<type>:]<name>' or as href."
        " Pass an empty string to detach the repository."
    ),
)


@pulp_group()
@type_option(choices={"hugging-face": PulpHuggingFaceDistributionContext})
def distribution() -> None:
    pass


lookup_options = [href_option, name_option, distribution_lookup_option]
nested_lookup_options = [distribution_lookup_option]
update_options = [
    remote_option,
    repository_option,
    pulp_labels_option,
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
