import click

from pulp_glue.common.context import (
    PulpRemoteContext,
)
from pulp_glue.common.i18n import get_translation
from pulp_glue.rust.context import (
    PulpRustRemoteContext,
    PulpRustRepositoryContext,
)

from pulp_cli.generic import (
    create_command,
    destroy_command,
    href_option,
    label_command,
    label_select_option,
    list_command,
    name_option,
    pulp_group,
    pulp_labels_option,
    repository_href_option,
    repository_lookup_option,
    resource_option,
    retained_versions_option,
    show_command,
    type_option,
    update_command,
    version_command,
)
from pulpcore.cli.core.generic import task_command

translation = get_translation(__package__)
_ = translation.gettext


remote_option = resource_option(
    "--remote",
    default_plugin="rust",
    default_type="rust",
    context_table={"rust:rust": PulpRustRemoteContext},
    href_pattern=PulpRemoteContext.HREF_PATTERN,
    help=_("Remote used for syncing in the form '[[<plugin>:]<resource_type>:]<name>' or by href."),
)


@pulp_group()
@type_option(
    choices={"rust": PulpRustRepositoryContext},
    default="rust",
)
def repository() -> None:
    pass


lookup_options = [href_option, name_option, repository_lookup_option]
nested_lookup_options = [repository_href_option, repository_lookup_option]
update_options = [
    click.option("--description"),
    remote_option,
    retained_versions_option,
    pulp_labels_option,
]
create_options = update_options + [click.option("--name", required=True)]

repository.add_command(
    list_command(
        decorators=[label_select_option, click.option("--name-startswith", "name__startswith")]
    )
)
repository.add_command(show_command(decorators=lookup_options))
repository.add_command(create_command(decorators=create_options))
repository.add_command(update_command(decorators=lookup_options + update_options))
repository.add_command(destroy_command(decorators=lookup_options))
repository.add_command(task_command(decorators=nested_lookup_options))
repository.add_command(version_command(decorators=nested_lookup_options))
repository.add_command(label_command(decorators=nested_lookup_options))
