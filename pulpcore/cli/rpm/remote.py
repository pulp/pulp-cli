import click
from pulp_glue.common.i18n import get_translation
from pulp_glue.rpm.context import PulpRpmRemoteContext, PulpUlnRemoteContext

from pulpcore.cli.common.generic import (
    PulpCLIContext,
    create_command,
    destroy_command,
    href_option,
    label_command,
    list_command,
    load_string_callback,
    name_option,
    pass_pulp_context,
    pulp_group,
    pulp_option,
    remote_filter_options,
    remote_lookup_option,
    role_command,
    show_command,
    update_command,
)

translation = get_translation(__package__)
_ = translation.gettext


def _uln_url_callback(ctx: click.Context, param: click.Parameter, value: str) -> str:
    if type(ctx.obj) is PulpUlnRemoteContext and (value and not value.startswith("uln://")):
        raise click.ClickException("Invalid url format. Please enter correct uln channel.")

    return value


@pulp_group()
@click.option(
    "-t",
    "--type",
    "remote_type",
    type=click.Choice(["rpm", "uln"], case_sensitive=False),
    default="rpm",
)
@pass_pulp_context
@click.pass_context
def remote(ctx: click.Context, pulp_ctx: PulpCLIContext, remote_type: str) -> None:
    if remote_type == "rpm":
        ctx.obj = PulpRpmRemoteContext(pulp_ctx)
    elif remote_type == "uln":
        ctx.obj = PulpUlnRemoteContext(pulp_ctx)
    else:
        raise NotImplementedError()


lookup_options = [href_option, name_option, remote_lookup_option]
nested_lookup_options = [remote_lookup_option]

rpm_remote_options = [
    click.option(
        "--ca-cert",
        help=_("a PEM encoded CA certificate or @file containing same"),
        callback=load_string_callback,
    ),
    click.option(
        "--client-cert",
        help=_("a PEM encoded client certificate or @file containing same"),
        callback=load_string_callback,
    ),
    click.option(
        "--client-key",
        help=_("a PEM encode private key or @file containing same"),
        callback=load_string_callback,
    ),
    click.option("--connect-timeout", type=float),
    click.option(
        "--download-concurrency", type=int, help=_("total number of simultaneous connections")
    ),
    click.option(
        "--password",
        help=_(
            "The password to authenticate to the remote (can contain leading and trailing spaces)."
        ),
    ),
    click.option(
        "--policy", type=click.Choice(["immediate", "on_demand", "streamed"], case_sensitive=False)
    ),
    click.option("--proxy-url"),
    click.option("--proxy-username"),
    click.option(
        "--proxy-password",
        help=_(
            "The password to authenticate to the proxy (can contain leading and trailing spaces)."
        ),
    ),
    click.option("--rate-limit", type=int, help=_("limit download rate in requests per second")),
    pulp_option("--sles-auth-token", allowed_with_contexts=(PulpRpmRemoteContext,)),
    click.option("--sock-connect-timeout", type=float),
    click.option("--sock-read-timeout", type=float),
    click.option("--tls-validation", type=bool),
    click.option("--total-timeout", type=float),
    click.option("--username"),
]

rpm_remote_create_options = [
    click.option("--name", required=True),
    click.option(
        "--url",
        help=_(
            "For remote_type:uln, Use the ULN channel name starting with uln://. "
            "For remote_type:rpm, use url with http/https."
        ),
        required=True,
        callback=_uln_url_callback,
    ),
    pulp_option(
        "--uln-server-base-url",
        default="https://linux-update.oracle.com/",
        help=_("ULN Server base URL, default is 'https://linux-update.oracle.com/'"),
        allowed_with_contexts=(PulpUlnRemoteContext,),
    ),
]

rpm_remote_update_options = [
    click.option(
        "--url",
        help=_(
            "For remote_type:uln, Use the ULN channel name starting with uln://. "
            "For remote_type:rpm, use url with http/https."
        ),
        callback=_uln_url_callback,
    ),
    pulp_option(
        "--uln-server-base-url",
        help=_("ULN Server base URL."),
        allowed_with_contexts=(PulpUlnRemoteContext,),
    ),
]

remote.add_command(list_command(decorators=remote_filter_options))
remote.add_command(show_command(decorators=lookup_options))
remote.add_command(create_command(decorators=rpm_remote_create_options + rpm_remote_options))
remote.add_command(
    update_command(decorators=lookup_options + rpm_remote_update_options + rpm_remote_options)
)
remote.add_command(destroy_command(decorators=lookup_options))
remote.add_command(label_command(decorators=nested_lookup_options))
remote.add_command(role_command(decorators=lookup_options))
