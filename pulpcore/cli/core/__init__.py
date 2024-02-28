import typing as t

import click

from pulpcore.cli.core.access_policy import access_policy
from pulpcore.cli.core.artifact import artifact
from pulpcore.cli.core.content import content
from pulpcore.cli.core.content_guard import content_guard
from pulpcore.cli.core.distribution import distribution
from pulpcore.cli.core.domain import domain
from pulpcore.cli.core.export import export
from pulpcore.cli.core.exporter import exporter
from pulpcore.cli.core.group import group
from pulpcore.cli.core.importer import importer
from pulpcore.cli.core.orphan import orphan
from pulpcore.cli.core.publication import publication
from pulpcore.cli.core.remote import remote
from pulpcore.cli.core.repository import repository
from pulpcore.cli.core.role import role
from pulpcore.cli.core.show import show
from pulpcore.cli.core.signing_service import signing_service
from pulpcore.cli.core.status import status
from pulpcore.cli.core.task import task
from pulpcore.cli.core.task_group import task_group
from pulpcore.cli.core.upload import upload
from pulpcore.cli.core.upstream_pulp import upstream_pulp
from pulpcore.cli.core.user import user
from pulpcore.cli.core.worker import worker


def mount(main: click.Group, **kwargs: t.Any) -> None:
    main.add_command(access_policy)
    main.add_command(artifact)
    main.add_command(content)
    main.add_command(domain)
    main.add_command(export)
    main.add_command(exporter)
    main.add_command(group)
    main.add_command(content_guard)
    main.add_command(distribution)
    main.add_command(importer)
    main.add_command(orphan)
    main.add_command(publication)
    main.add_command(remote)
    main.add_command(repository)
    main.add_command(role)
    main.add_command(show)
    main.add_command(signing_service)
    main.add_command(status)
    main.add_command(task)
    main.add_command(task_group)
    main.add_command(upload)
    main.add_command(upstream_pulp)
    main.add_command(user)
    main.add_command(worker)

    _orig_get_command = main.get_command

    def patched_get_command(ctx: click.Context, cmd_name: str) -> t.Optional[click.Command]:
        if cmd_name == "domains":
            click.echo("Please use 'domain' instead of 'domains'.", err=True)
            cmd_name = "domain"
        return _orig_get_command(ctx, cmd_name)

    main.get_command = patched_get_command  # type: ignore[method-assign]
