from pulpcore.cli.common import main
from pulpcore.cli.container.repository import repository
from pulpcore.cli.container.repository_version import version
from pulpcore.cli.container.remote import remote

# from pulpcore.cli.container.distribution import distribution


@main.group()
def container() -> None:
    pass


container.add_command(repository)
repository.add_command(version)
container.add_command(remote)
# container.add_command(distribution)
