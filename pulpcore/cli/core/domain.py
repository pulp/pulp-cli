import click
from pulp_glue.common.context import PulpContext
from pulp_glue.common.i18n import get_translation
from pulp_glue.core.context import PulpDomainContext

from pulpcore.cli.common.generic import (
    create_command,
    destroy_command,
    href_option,
    list_command,
    load_json_callback,
    name_option,
    pass_pulp_context,
    pulp_group,
    role_command,
    show_command,
    update_command,
)

translation = get_translation(__package__)
_ = translation.gettext


# We need to override the default_map, because we may read a default value for the `--domain`
# option from the config file that will collide here.
@pulp_group(name="domain", context_settings={"default_map": {}})
@pass_pulp_context
@click.pass_context
def domain(ctx: click.Context, pulp_ctx: PulpContext) -> None:
    """
    Perform actions on domains.
    """
    ctx.obj = PulpDomainContext(pulp_ctx)


lookup_options = [href_option, name_option]
update_options = [
    click.option("--description"),
    click.option(
        "--storage-settings", callback=load_json_callback, help=_("Settings for storage backend")
    ),
    click.option(
        "--redirect/--no-redirect",
        "redirect_to_object_storage",
        default=True,
        help=_("Have content app redirect to object storage"),
    ),
    click.option(
        "--hide-distributions/--show-distributions",
        "hide_guarded_distributions",
        default=False,
        help=_("Hide guarded distributions in the content app"),
    ),
]
storage_classes = (
    "pulpcore.app.models.storage.FileSystem",
    "storages.backends.s3boto3.S3Boto3Storage",
    "storages.backends.azure_storage.AzureStorage",
)
create_options = update_options + [
    click.option("--name", required=True, help=_("Name of the domain")),
    click.option(
        "--storage-class",
        required=True,
        type=click.Choice(storage_classes, case_sensitive=False),
        help=_("Storage backend for domain"),
    ),
]

domain.add_command(list_command())
domain.add_command(show_command(decorators=lookup_options))
domain.add_command(create_command(decorators=create_options))
domain.add_command(update_command(decorators=update_options + lookup_options))
domain.add_command(destroy_command(decorators=lookup_options))
domain.add_command(role_command(decorators=lookup_options))
