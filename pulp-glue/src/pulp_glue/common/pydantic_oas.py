import typing as t

import pydantic
import pydantic.alias_generators
from pydantic_core import PydanticCustomError


def to_alias(value: str) -> str:
    return pydantic.alias_generators.to_camel(value.rstrip("_"))


class OASBase(pydantic.BaseModel, alias_generator=to_alias, extra="forbid"):
    pass


class ExtensibleOASBase(OASBase, extra="allow"):
    @pydantic.model_validator(mode="after")
    def _check_extensions(self) -> "t.Self":
        if self.__pydantic_extra__ is not None:
            invalid_keys = [
                key for key in self.__pydantic_extra__.keys() if not key.startswith("x-")
            ]
            if invalid_keys:
                raise PydanticCustomError(
                    "invalid_extensions",
                    "Extra inputs are only permitted as '^x-' extensions. {invalid_keys}",
                    {"invalid_keys": invalid_keys},
                )

        return self


OperationName = t.Literal[
    "get",
    "put",
    "post",
    "patch",
    "delete",
    "options",
    "head",
    "trace",
]


class Reference(OASBase):
    ref: t.Annotated[str, pydantic.Field(alias="$ref")]
    summary: str | None = None
    description: str | None = None


class OAuthFlow(OASBase):
    refresh_url: str | None = None
    scopes: dict[str, str]


class OAuthFlowToken(OAuthFlow):
    token_url: str


class OAuthFlowAuthorization(OAuthFlow):
    authorization_url: str


class OAuthFlowAuthorizationCode(OAuthFlow):
    authorization_url: str
    token_url: str


class OAuthFlows(OASBase):
    implicit: OAuthFlowAuthorization | None = None
    password: OAuthFlowToken | None = None
    client_credentials: OAuthFlowToken | None = None
    authorization_code: OAuthFlowAuthorizationCode | None = None


class SecuritySchemeBase(OASBase):
    type_: str
    description: str | None = None


class SecuritySchemeApiKey(SecuritySchemeBase):
    type_: t.Literal["apiKey"]
    name: str
    in_: t.Literal["query", "header", "cookie"]


class SecuritySchemeHttp(SecuritySchemeBase):
    type_: t.Literal["http"]
    scheme: str
    bearer_format: str | None = None


class SecuritySchemeMutualTLS(SecuritySchemeBase):
    type_: t.Literal["mutualTLS"]


class SecuritySchemeOAuth2(SecuritySchemeBase):
    type_: t.Literal["oauth2"]
    flows: OAuthFlows


class SecuritySchemeOpenIdConnect(SecuritySchemeBase):
    type_: t.Literal["openIdConnect"]
    open_id_connect_url: str


SecurityScheme = t.Annotated[
    SecuritySchemeApiKey
    | SecuritySchemeHttp
    | SecuritySchemeMutualTLS
    | SecuritySchemeOAuth2
    | SecuritySchemeOpenIdConnect,
    pydantic.Field(discriminator="type_"),
]


class Contact(ExtensibleOASBase):
    name: str | None = None
    url: str | None = None
    email: str | None = None


class License(ExtensibleOASBase):
    name: str
    identifier: str | None = None
    url: str | None = None


class Info(ExtensibleOASBase):
    title: str
    summary: str | None = None
    description: str | None = None
    terms_of_service: str | None = None
    contact: Contact | None = None
    license: License | None = None
    version: str


class ServerVariable(ExtensibleOASBase):
    enum: list[str] | None = None
    default: str
    description: str | None = None


class Server(ExtensibleOASBase):
    url: str
    description: str | None = None
    variables: dict[str, ServerVariable] | None = None


class ExternalDocumentation(ExtensibleOASBase):
    url: str
    description: str | None = None


class Example(ExtensibleOASBase):
    summary: str | None = None
    description: str | None = None
    value: t.Any = None
    external_value: str | None = None


SecurityRequirements = list[dict[str, list[str]]]


class Discriminator(ExtensibleOASBase):
    property_name: str
    mapping: dict[str, str] | None = None


class XML(ExtensibleOASBase):
    name: str | None = None
    namespace: str | None = None
    prefix: str | None = None
    attribute: bool = False
    wrapped: bool = False


class Schema(OASBase, extra="allow"):
    discriminator: Discriminator | None = None
    xml: XML | None = None
    external_docs: ExternalDocumentation | None = None
    example: t.Any = None


class Link(ExtensibleOASBase):
    operation_ref: str | None = None
    operation_id: str | None = None
    parameters: dict[str, t.Any] | None = None
    request_body: t.Any = None
    description: str | None = None
    server: Server | None = None


class Tag(ExtensibleOASBase):
    name: str
    description: str | None = None
    external_docs: ExternalDocumentation | None = None


class Encoding(ExtensibleOASBase):
    content_type: str | None = None
    headers: dict[str, t.Union["Header", Reference]] | None = None
    # TODO These only apply to RFC6570
    style: (
        t.Literal[
            "simple",
            "form",
            "matrix",
            "label",
            "spaceDelimited",
            "pipeDelimited",
            "deepObject",
        ]
        | None
    ) = None
    explode: t.Annotated[bool, pydantic.Field(default_factory=lambda data: data["style"] == "form")]
    allow_reserved: bool = False


class MediaType(ExtensibleOASBase):
    schema_: Schema
    example: t.Any = None
    examples: dict[str, Example | Reference] | None = None
    encoding: dict[str, Encoding] = {}


class HeaderBase(ExtensibleOASBase):
    description: str | None = None
    required: bool | None = False
    deprecated: bool = False


class ContentHeader(HeaderBase):
    content: dict[str, MediaType]


class SchemaHeader(HeaderBase):
    schema_: Schema | Reference
    style: t.Literal["simple"] = "simple"
    explide: bool = False
    example: t.Any = None
    examples: dict[str, Example | Reference] | None = None


Header = ContentHeader | SchemaHeader


class ParameterBase(ExtensibleOASBase):
    name: str
    in_: t.Literal["query", "header", "path", "cookie"]
    description: str | None = None
    required: bool | None = False
    deprecated: bool = False
    allow_empty_value: bool = False

    @pydantic.model_validator(mode="after")
    def _path_required(self) -> "t.Self":
        if self.in_ == "path":
            assert self.required
        return self


class ContentParameter(ParameterBase):
    content: dict[str, MediaType]


class SchemaParameter(ParameterBase):
    schema_: Schema
    style: t.Annotated[
        t.Literal[
            "simple",
            "form",
            "matrix",
            "label",
            "spaceDelimited",
            "pipeDelimited",
            "deepObject",
        ],
        pydantic.Field(
            default_factory=lambda data: (
                "simple" if data.get("in_") in ["header", "path"] else "form"
            )
        ),
    ]
    explode: t.Annotated[bool, pydantic.Field(default_factory=lambda data: data["style"] == "form")]
    allowed_reserved: bool = False
    example: t.Any = None
    examples: dict[str, Example | Reference] | None = None


Parameter = ContentParameter | SchemaParameter


class RequestBody(ExtensibleOASBase):
    description: str | None = None
    content: dict[str, MediaType]
    required: bool = False


class Response(ExtensibleOASBase):
    description: str
    headers: dict[str, Header | Reference] | None = None
    content: dict[str, MediaType] | None = None
    links: dict[str, Link | Reference] | None = None


Responses = dict[str, Response | Reference]  # TODO key linting ??


Callback = dict[str, "PathItem"]


class Operation(ExtensibleOASBase):
    tags: list[str] | None = None
    summary: str | None = None
    description: str | None = None
    external_docs: ExternalDocumentation | None = None
    operation_id: str
    parameters: list[Parameter | Reference] = []
    request_body: RequestBody | Reference | None = None
    responses: Responses | None = None
    callbacks: dict[str, Callback | Reference] | None = None
    deprecated: bool = False
    security: SecurityRequirements | None = None
    servers: list[Server] | None = None


class PathItem(ExtensibleOASBase):
    # TODO $ref
    get: Operation | None = None
    put: Operation | None = None
    post: Operation | None = None
    patch: Operation | None = None
    delete: Operation | None = None
    options: Operation | None = None
    head: Operation | None = None
    trace: Operation | None = None
    servers: list[Server] | None = None
    parameters: list[Parameter | Reference] = []


class Components(ExtensibleOASBase):
    schemas: dict[str, Schema] | None = {}
    responses: dict[str, Response | Reference] | None = None
    parameters: dict[str, Parameter | Reference] = {}
    examples: dict[str, Example | Reference] | None = None
    request_bodies: dict[str, RequestBody | Reference] | None = None
    headers: dict[str, Header | Reference] | None = None
    security_schemes: dict[str, SecurityScheme | Reference] = {}
    links: dict[str, Link | Reference] | None = None
    callbacks: dict[str, Callback | Reference] | None = None
    path_items: dict[str, PathItem] | None = None


class OpenAPISpec(ExtensibleOASBase):
    openapi: str
    info: Info
    json_schema_dialect: str | None = None
    servers: list[Server] | None = None
    # In the specification there is a Paths Object,
    # probably because paths as keys can get extra validation.
    paths: dict[str, PathItem] = {}
    webhooks: dict[str, PathItem] | None = None
    components: Components | None = None
    security: SecurityRequirements | None = None
    tags: list[Tag] | None = None
    external_docs: ExternalDocumentation | None = None
