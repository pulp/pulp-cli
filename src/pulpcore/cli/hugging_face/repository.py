import click

from pulp_glue.common.i18n import get_translation
from pulp_glue.hugging_face.context import PulpHuggingFaceRepositoryContext

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
    retained_versions_option,
    show_command,
    type_option,
    update_command,
    version_command,
)

translation = get_translation(__package__)
_ = translation.gettext


@pulp_group()
@type_option(choices={"hugging-face": PulpHuggingFaceRepositoryContext})
def repository() -> None:
    pass


lookup_options = [href_option, name_option, repository_lookup_option]
nested_lookup_options = [repository_href_option, repository_lookup_option]
update_options = [
    click.option("--description"),
    retained_versions_option,
    pulp_labels_option,
]
create_options = update_options + [click.option("--name", required=True)]

repository.add_command(
    list_command(
        decorators=[
            label_select_option,
            click.option("--name-contains", "name__contains"),
        ]
    )
)
repository.add_command(show_command(decorators=lookup_options))
repository.add_command(create_command(decorators=create_options))
repository.add_command(update_command(decorators=lookup_options + update_options))
repository.add_command(destroy_command(decorators=lookup_options))
repository.add_command(version_command(decorators=nested_lookup_options))
repository.add_command(label_command(decorators=nested_lookup_options))
