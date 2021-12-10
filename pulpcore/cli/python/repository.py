from typing import Any, Dict, Optional

import click

from pulpcore.cli.common.context import (
    EntityFieldDefinition,
    PluginRequirement,
    PulpContext,
    PulpEntityContext,
    PulpRemoteContext,
    PulpRepositoryContext,
    pass_pulp_context,
    pass_repository_context,
)
from pulpcore.cli.common.generic import (
    create_command,
    create_content_json_callback,
    destroy_command,
    href_option,
    label_command,
    label_select_option,
    list_command,
    name_option,
    pulp_option,
    repository_content_command,
    repository_href_option,
    repository_option,
    resource_option,
    retained_versions_option,
    show_command,
    update_command,
    version_command,
)
from pulpcore.cli.common.i18n import get_translation
from pulpcore.cli.core.generic import task_command
from pulpcore.cli.python.context import (
    PulpPythonContentContext,
    PulpPythonRemoteContext,
    PulpPythonRepositoryContext,
)

translation = get_translation(__name__)
_ = translation.gettext


remote_option = resource_option(
    "--remote",
    default_plugin="python",
    default_type="python",
    context_table={"python:python": PulpPythonRemoteContext},
    href_pattern=PulpRemoteContext.HREF_PATTERN,
    help=_(
        "Remote used for synching in the form '[[<plugin>:]<resource_type>:]<name>' or by href."
    ),
)


def _content_callback(
    ctx: click.Context, param: click.Parameter, value: Optional[str]
) -> Optional[str]:
    if value:
        pulp_ctx = ctx.find_object(PulpContext)
        assert pulp_ctx is not None
        ctx.obj = PulpPythonContentContext(pulp_ctx, entity={"filename": value})
    return value


@click.group()
@click.option(
    "-t",
    "--type",
    "repo_type",
    type=click.Choice(["python"], case_sensitive=False),
    default="python",
)
@pass_pulp_context
@click.pass_context
def repository(ctx: click.Context, pulp_ctx: PulpContext, repo_type: str) -> None:
    if repo_type == "python":
        ctx.obj = PulpPythonRepositoryContext(pulp_ctx)
    else:
        raise NotImplementedError()


lookup_options = [href_option, name_option]
nested_lookup_options = [repository_href_option, repository_option]
update_options = [
    click.option("--description"),
    remote_option,
    pulp_option(
        "--autopublish/--no-autopublish",
        needs_plugins=[PluginRequirement("python", "3.3.0.dev")],
        default=None,
    ),
    retained_versions_option,
]
create_options = update_options + [click.option("--name", required=True)]
package_option = click.option(
    "--filename",
    callback=_content_callback,
    expose_value=False,
    help=_("Filename of the python package"),
)
content_json_callback = create_content_json_callback(PulpPythonContentContext)
modify_options = [
    click.option(
        "--add-content",
        callback=content_json_callback,
        help=_(
            """JSON string with a list of objects to add to the repository.
    Each object should have the key: "filename"
    The argument prefixed with the '@' can be the path to a JSON file with a list of objects."""
        ),
    ),
    click.option(
        "--remove-content",
        callback=content_json_callback,
        help=_(
            """JSON string with a list of objects to remove from the repository.
    Each object should have the key: "filename"
    The argument prefixed with the '@' can be the path to a JSON file with a list of objects."""
        ),
    ),
]

repository.add_command(list_command(decorators=[label_select_option]))
repository.add_command(show_command(decorators=lookup_options))
repository.add_command(create_command(decorators=create_options))
repository.add_command(update_command(decorators=lookup_options + update_options))
repository.add_command(destroy_command(decorators=lookup_options))
repository.add_command(task_command(decorators=nested_lookup_options))
repository.add_command(version_command(decorators=nested_lookup_options))
repository.add_command(label_command(decorators=nested_lookup_options))
repository.add_command(
    repository_content_command(
        contexts={"package": PulpPythonContentContext},
        add_decorators=[package_option],
        remove_decorators=[package_option],
        modify_decorators=modify_options,
    )
)


@repository.command()
@name_option
@href_option
@remote_option
@pass_repository_context
def sync(
    repository_ctx: PulpRepositoryContext,
    remote: EntityFieldDefinition,
) -> None:
    repository = repository_ctx.entity
    repository_href = repository_ctx.pulp_href

    body: Dict[str, Any] = {}

    if isinstance(remote, PulpEntityContext):
        body["remote"] = remote.pulp_href
    elif repository["remote"] is None:
        raise click.ClickException(
            _(
                "Repository '{name}' does not have a default remote. "
                "Please specify with '--remote'."
            ).format(name=repository["name"])
        )

    repository_ctx.sync(
        href=repository_href,
        body=body,
    )


@repository.command(deprecated=True)
@name_option
@href_option
@click.option("--filename", required=True)
@click.option("--base-version", type=int)
@pass_repository_context
@pass_pulp_context
def add(
    pulp_ctx: PulpContext,
    repository_ctx: PulpRepositoryContext,
    filename: str,
    base_version: Optional[int],
) -> None:
    """Please use 'content add' instead."""
    repository_href = repository_ctx.pulp_href

    base_version_href: Optional[str]
    if base_version is not None:
        base_version_href = f"{repository_href}versions/{base_version}/"
    else:
        base_version_href = None

    content_href = PulpPythonContentContext(pulp_ctx, entity={"filename": filename}).pulp_href

    repository_ctx.modify(
        href=repository_href,
        add_content=[content_href],
        base_version=base_version_href,
    )


@repository.command(deprecated=True)
@name_option
@href_option
@click.option("--filename", required=True)
@click.option("--base-version", type=int)
@pass_repository_context
@pass_pulp_context
def remove(
    pulp_ctx: PulpContext,
    repository_ctx: PulpRepositoryContext,
    filename: str,
    base_version: Optional[int],
) -> None:
    """Please use 'content remove' instead."""
    repository_href = repository_ctx.pulp_href

    base_version_href: Optional[str]
    if base_version is not None:
        base_version_href = f"{repository_href}versions/{base_version}/"
    else:
        base_version_href = None

    content_href = PulpPythonContentContext(pulp_ctx, entity={"filename": filename}).pulp_href

    repository_ctx.modify(
        href=repository_href,
        remove_content=[content_href],
        base_version=base_version_href,
    )
