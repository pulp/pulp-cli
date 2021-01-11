from pulpcore.cli.common import main

from pulpcore.cli.core.artifact import artifact
from pulpcore.cli.core.export import export
from pulpcore.cli.core.exporter import exporter
from pulpcore.cli.core.group import group
from pulpcore.cli.core.importer import importer
from pulpcore.cli.core.orphans import orphans
from pulpcore.cli.core.status import status
from pulpcore.cli.core.task import task
from pulpcore.cli.core.user import user
from pulpcore.cli.core.show import show


# Register commands with cli
main.add_command(status)
main.add_command(show)
main.add_command(user)
main.add_command(group)
main.add_command(artifact)
main.add_command(orphans)
main.add_command(task)
main.add_command(exporter)
main.add_command(export)
main.add_command(importer)
