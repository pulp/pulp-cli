from typing import IO, Any, Optional, Union

import click

from pulpcore.cli.ansible.context import (
    PulpAnsibleCollectionVersionContext,
    PulpAnsibleCollectionVersionSignatureContext,
    PulpAnsibleRepositoryContext,
    PulpAnsibleRoleContext,
)
from pulpcore.cli.common.context import (
    PulpContext,
    PulpEntityContext,
    PulpRepositoryContext,
    pass_entity_context,
    pass_pulp_context,
)
from pulpcore.cli.common.generic import (
    GroupOption,
    href_option,
    list_command,
    parse_size_callback,
    pulp_group,
    pulp_option,
    resource_option,
    show_command,
)
from pulpcore.cli.common.i18n import get_translation
from pulpcore.cli.core.context import PulpArtifactContext

translation = get_translation(__name__)
_ = translation.gettext


collection_context = (PulpAnsibleCollectionVersionContext,)
role_context = (PulpAnsibleRoleContext,)
content_context = (PulpAnsibleRoleContext, PulpAnsibleCollectionVersionContext)
signature_context = (PulpAnsibleCollectionVersionSignatureContext,)


def _content_callback(ctx: click.Context, param: click.Parameter, value: Any) -> Any:
    if value:
        entity_ctx = ctx.find_object(PulpEntityContext)
        assert entity_ctx is not None
        entity_ctx.entity = value
    return value


repository_option = resource_option(
    "--repository",
    default_plugin="ansible",
    default_type="ansible",
    context_table={
        "ansible:ansible": PulpAnsibleRepositoryContext,
    },
    href_pattern=PulpRepositoryContext.HREF_PATTERN,
    allowed_with_contexts=signature_context,
    help=_(
        "Repository to upload into in the form '[[<plugin>:]<resource_type>:]<name>' or by href."
    ),
)


@pulp_group()
@click.option(
    "-t",
    "--type",
    "content_type",
    type=click.Choice(["collection-version", "role", "signature"], case_sensitive=False),
    default="collection-version",
)
@pass_pulp_context
@click.pass_context
def content(ctx: click.Context, pulp_ctx: PulpContext, content_type: str) -> None:
    if content_type == "collection-version":
        ctx.obj = PulpAnsibleCollectionVersionContext(pulp_ctx)
    elif content_type == "role":
        ctx.obj = PulpAnsibleRoleContext(pulp_ctx)
    elif content_type == "signature":
        ctx.obj = PulpAnsibleCollectionVersionSignatureContext(pulp_ctx)
    else:
        raise NotImplementedError()


list_options = [
    pulp_option("--name", help=_("Name of {entity}"), allowed_with_contexts=content_context),
    pulp_option(
        "--namespace", help=_("Namespace of {entity}"), allowed_with_contexts=content_context
    ),
    pulp_option("--version", help=_("Version of {entity}"), allowed_with_contexts=content_context),
    pulp_option(
        "--latest",
        "is_highest",
        is_flag=True,
        default=None,
        help=_("Only show highest version of collection version"),
        allowed_with_contexts=collection_context,
    ),
    pulp_option(
        "--tags",
        help=_("Comma separated list of tags that must all match"),
        allowed_with_contexts=collection_context,
    ),
    pulp_option(
        "--pubkey-fingerprint",
        help=_("Public key fingerprint of the {entity}"),
        allowed_with_contexts=signature_context,
    ),
    pulp_option(
        "--collection",
        "signed_collection",
        help=_("Collection of {entity}"),
        allowed_with_contexts=signature_context,
    ),
    pulp_option(
        "--signing-service",
        help=_("Signing service used to create {entity}"),
        allowed_with_contexts=signature_context,
    ),
]

fields_options = [
    pulp_option("--fields", help=_("String list of fields to include in the result")),
    pulp_option(
        "--exclude-fields",
        default="files,manifest,docs_blob",
        help=_("String list of fields to exclude from result"),
    ),
]

lookup_options = [
    click.option(
        "--name",
        help=_("Name of {entity}"),
        group=["namespace", "version"],
        expose_value=False,
        allowed_with_contexts=(PulpAnsibleRoleContext, PulpAnsibleCollectionVersionContext),
        cls=GroupOption,
        callback=_content_callback,
    ),
    click.option(
        "--namespace",
        help=_("Namespace of {entity}"),
        group=["name", "version"],
        expose_value=False,
        allowed_with_contexts=(PulpAnsibleRoleContext, PulpAnsibleCollectionVersionContext),
        cls=GroupOption,
    ),
    click.option(
        "--version",
        help=_("Version of {entity}"),
        group=["namespace", "name"],
        expose_value=False,
        allowed_with_contexts=(PulpAnsibleRoleContext, PulpAnsibleCollectionVersionContext),
        cls=GroupOption,
    ),
    click.option(
        "--pubkey-fingerprint",
        help=_("Public key fingerprint of the {entity}"),
        group=["collection"],
        expose_value=False,
        allowed_with_contexts=signature_context,
        callback=_content_callback,
        cls=GroupOption,
    ),
    click.option(
        "--collection",
        "signed_collection",
        help=_("Collection of {entity}"),
        group=["pubkey_fingerprint"],
        expose_value=False,
        allowed_with_contexts=signature_context,
        cls=GroupOption,
    ),
    href_option,
]

content.add_command(list_command(decorators=list_options + fields_options))
content.add_command(show_command(decorators=lookup_options))


@content.command()
@click.option("--file", type=click.File("rb"), required=True)
@repository_option
@pulp_option(
    "--chunk-size",
    help=_("Chunk size to break up {entity} into. Defaults to 1MB"),
    default="1MB",
    callback=parse_size_callback,
    allowed_with_contexts=role_context,
)
@pulp_option(
    "--name", help=_("Name of {entity}"), allowed_with_contexts=role_context, required=True
)
@pulp_option(
    "--namespace",
    help=_("Namespace of {entity}"),
    allowed_with_contexts=role_context,
    required=True,
)
@pulp_option(
    "--version",
    help=_("Version of {entity}"),
    allowed_with_contexts=role_context,
    required=True,
)
@pulp_option(
    "--collection",
    help=_("Collection for this {entity}"),
    allowed_with_contexts=signature_context,
    required=True,
)
@pass_entity_context
@pass_pulp_context
def upload(
    pulp_ctx: PulpContext,
    content_ctx: Union[
        PulpAnsibleRoleContext,
        PulpAnsibleCollectionVersionContext,
        PulpAnsibleCollectionVersionSignatureContext,
    ],
    file: IO[bytes],
    **kwargs: Any,
) -> None:
    if isinstance(content_ctx, PulpAnsibleRoleContext):
        chunk_size = kwargs.pop("chunk_size")
        artifact_href = PulpArtifactContext(pulp_ctx).upload(file, chunk_size)
        body = {"artifact": artifact_href}
        body.update(kwargs)
        result = content_ctx.create(body=body)
        pulp_ctx.output_result(result)
    elif isinstance(content_ctx, PulpAnsibleCollectionVersionSignatureContext):
        body = {"signed_collection": kwargs["collection"]}
        repository: Optional[PulpRepositoryContext] = kwargs["repository"]
        if repository:
            body["repository"] = repository.pulp_href
        uploads = {"file": file.read()}
        pulp_ctx.output_result(content_ctx.create(body=body, uploads=uploads))
    elif isinstance(content_ctx, PulpAnsibleCollectionVersionContext):
        result = content_ctx.upload(file=file)
        pulp_ctx.output_result(result)
    else:
        raise NotImplementedError()
