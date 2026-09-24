import click

from pulp_glue.common.i18n import get_translation
from pulp_glue.rust.context import PulpRustContentContext

from pulp_cli.generic import (
    content_filter_options,
    href_option,
    list_command,
    pulp_group,
    show_command,
    type_option,
)

translation = get_translation(__package__)
_ = translation.gettext


@pulp_group()
@type_option(
    choices={"rust": PulpRustContentContext},
    default="rust",
)
def content() -> None:
    pass


lookup_options = [
    href_option,
]

content.add_command(
    list_command(
        decorators=[
            click.option("--name"),
            click.option("--version"),
            *content_filter_options,
        ]
    )
)
content.add_command(show_command(decorators=lookup_options))
