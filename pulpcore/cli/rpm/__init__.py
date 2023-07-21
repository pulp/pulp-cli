from typing import Any

import click
from pulp_glue.common.i18n import get_translation
from pulp_glue.rpm.context import PulpRpmACSContext, PulpRpmRemoteContext, PulpUlnRemoteContext

from pulpcore.cli.common.acs import acs_command
from pulpcore.cli.common.generic import pulp_group
from pulpcore.cli.rpm.comps import comps_upload
from pulpcore.cli.rpm.content import content
from pulpcore.cli.rpm.distribution import distribution
from pulpcore.cli.rpm.publication import publication
from pulpcore.cli.rpm.remote import remote
from pulpcore.cli.rpm.repository import repository

translation = get_translation(__name__)
_ = translation.gettext


@pulp_group()
def rpm() -> None:
    pass


def mount(main: click.Group, **kwargs: Any) -> None:
    rpm.add_command(repository)
    rpm.add_command(remote)
    rpm.add_command(publication)
    rpm.add_command(distribution)
    rpm.add_command(content)
    rpm.add_command(
        acs_command(
            acs_contexts={"rpm": PulpRpmACSContext},
            remote_context_table={"rpm:rpm": PulpRpmRemoteContext, "rpm:uln": PulpUlnRemoteContext},
        )
    )
    rpm.add_command(comps_upload)
    main.add_command(rpm)
