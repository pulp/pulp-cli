import asyncio
import json
import logging
import os
import ssl
import typing as t
import warnings
from base64 import b64encode
from collections import defaultdict
from dataclasses import dataclass
from functools import cached_property
from io import BufferedReader
from urllib.parse import urlencode, urljoin

import aiofiles
import aiofiles.os
import aiohttp
import requests
from multidict import CIMultiDict, CIMultiDictProxy, MutableMultiMapping

from pulp_glue.common import __version__
from pulp_glue.common.exceptions import (
    OpenAPIError,
    PulpAuthenticationFailed,
    PulpHTTPError,
    PulpNotAutorized,
    UnsafeCallError,
    ValidationError,
)
from pulp_glue.common.i18n import get_translation
from pulp_glue.common.schema import encode_json, encode_param, validate

translation = get_translation(__package__)
_ = translation.gettext
_logger = logging.getLogger("pulp_glue.openapi")

UploadType = bytes | t.IO[bytes]

SAFE_METHODS = ["GET", "HEAD", "OPTIONS"]


@dataclass
class _Request:
    operation_id: str
    method: str
    url: str
    headers: MutableMultiMapping[str] | CIMultiDictProxy[str] | t.MutableMapping[str, str]
    params: dict[str, str] | None = None
    data: dict[str, t.Any] | str | None = None
    files: dict[str, tuple[str, UploadType, str]] | None = None
    security: list[dict[str, list[str]]] | None = None


@dataclass
class _Response:
    status_code: int
    headers: MutableMultiMapping[str] | CIMultiDictProxy[str] | t.MutableMapping[str, str]
    body: bytes


class AuthProviderBase:
    """
    Base class for auth providers.

    This abstract base class will analyze the authentication proposals of the openapi specs.
    Different authentication schemes should be implemented by subclasses.
    Returned auth objects need to be compatible with `requests.auth.AuthBase`.
    """

    def basic_auth(self, scopes: list[str]) -> requests.auth.AuthBase | None:
        """Implement this to provide means of http basic auth."""
        return None

    def http_auth(
        self, security_scheme: dict[str, t.Any], scopes: list[str]
    ) -> requests.auth.AuthBase | None:
        """Select a suitable http auth scheme or return None."""
        # https://www.iana.org/assignments/http-authschemes/http-authschemes.xhtml
        if security_scheme["scheme"] == "basic":
            result = self.basic_auth(scopes)
            if result:
                return result
        return None

    def oauth2_client_credentials_auth(
        self, flow: t.Any, scopes: list[str]
    ) -> requests.auth.AuthBase | None:
        """Implement this to provide other authentication methods."""
        return None

    def oauth2_auth(
        self, security_scheme: dict[str, t.Any], scopes: list[str]
    ) -> requests.auth.AuthBase | None:
        """Select a suitable oauth2 flow or return None."""
        # Check flows by preference.
        if "clientCredentials" in security_scheme["flows"]:
            flow = security_scheme["flows"]["clientCredentials"]
            # Select this flow only if it claims to provide all the necessary scopes.
            # This will allow subsequent auth proposals to be considered.
            if set(scopes) - set(flow["scopes"]):
                return None

            result = self.oauth2_client_credentials_auth(flow, scopes)
            if result:
                return result
        return None

    def __call__(
        self,
        security: list[dict[str, list[str]]],
        security_schemes: dict[str, dict[str, t.Any]],
    ) -> requests.auth.AuthBase | None:

        # Reorder the proposals by their type to prioritize properly.
        # Select only single mechanism proposals on the way.
        proposed_schemes: dict[str, dict[str, list[str]]] = defaultdict(dict)
        for proposal in security:
            if len(proposal) == 0:
                # Empty proposal: No authentication needed. Shortcut return.
                return None
            if len(proposal) == 1:
                name, scopes = list(proposal.items())[0]
                proposed_schemes[security_schemes[name]["type"]][name] = scopes
            # Ignore all proposals with more than one required auth mechanism.

        # Check for auth schemes by preference.
        if "oauth2" in proposed_schemes:
            for name, scopes in proposed_schemes["oauth2"].items():
                result = self.oauth2_auth(security_schemes[name], scopes)
                if result:
                    return result

        # if we get here, either no-oauth2, OR we couldn't find creds
        if "http" in proposed_schemes:
            for name, scopes in proposed_schemes["http"].items():
                result = self.http_auth(security_schemes[name], scopes)
                if result:
                    return result

        raise OpenAPIError(_("No suitable auth scheme found."))


class BasicAuthProvider(AuthProviderBase):
    """
    Implementation for AuthProviderBase providing basic auth with fixed `username`, `password`.
    """

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.auth = requests.auth.HTTPBasicAuth(username, password)

    def basic_auth(self, scopes: list[str]) -> requests.auth.AuthBase | None:
        return self.auth


class _Middleware:
    def __init__(
        self,
        openapi: "OpenAPI",
        security: t.Optional[t.List[t.Dict[str, t.List[str]]]],
    ):
        self._openapi = openapi
        # self.method_spec  may be more interesting...
        self._security = security

    async def __call__(
        self,
        request: aiohttp.ClientRequest,
        handler: aiohttp.ClientHandlerType,
    ) -> aiohttp.ClientResponse:
        if self._security:
            assert self._openapi._auth_provider is not None
            auth = self._openapi._auth_provider(
                self._security, self._openapi.api_spec["components"]["securitySchemes"]
            )
            if isinstance(auth, requests.auth.HTTPBasicAuth):
                username = (
                    auth.username.encode("latin1")
                    if isinstance(auth.username, str)
                    else auth.username
                )
                password = (
                    auth.password.encode("latin1")
                    if isinstance(auth.password, str)
                    else auth.password
                )
                secret = b64encode(username + b":" + password)
                request.headers["Authorization"] = "Basic " + secret.decode()
        response = await handler(request)

        if "Correlation-Id" in response.headers:
            self._openapi._set_correlation_id(response.headers["Correlation-Id"])
        return response


class OpenAPI:
    """
    The abstraction Layer to interact with a server providing an openapi v3 specification.

    Parameters:
        base_url: The base URL inlcuding the HTTP scheme, hostname and optional subpaths of the
            served api.
        doc_path: Path of the json api doc schema relative to the `base_url`.
        headers: Dictionary of additional request headers.
        auth_provider: Object that returns requests auth objects according to the api spec.
        cert: Client certificate used for auth.
        key: Matching key for `cert` if not already included.
        verify_ssl: Whether to check server TLS certificates agains a CA (requests semantic).
        refresh_cache: Whether to fetch the api doc regardless.
        dry_run: Flag to disallow issuing POST, PUT, PATCH or DELETE calls.
        debug_callback: Callback that will be called with strings useful for logging or debugging.
        user_agent: String to use in the User-Agent header.
        cid: Correlation ID to send with all requests.
        validate_certs: DEPRECATED use verify_ssl instead.
        safe_calls_only: DEPRECATED use dry_run instead.
    """

    def __init__(
        self,
        base_url: str,
        doc_path: str,
        headers: CIMultiDict[str] | CIMultiDictProxy[str] | None = None,
        auth_provider: AuthProviderBase | None = None,
        cert: str | None = None,
        key: str | None = None,
        verify_ssl: bool | str | None = True,
        refresh_cache: bool = False,
        dry_run: bool = False,
        debug_callback: t.Callable[[int, str], t.Any] | None = None,
        user_agent: str | None = None,
        cid: str | None = None,
        validate_certs: bool | None = None,
        safe_calls_only: bool | None = None,
    ):
        if validate_certs is not None:
            warnings.warn(
                "validate_certs is deprecated; use verify_ssl instead.", DeprecationWarning
            )
            verify_ssl = validate_certs
        if safe_calls_only is not None:
            warnings.warn("safe_calls_only is deprecated; use dry_run instead.", DeprecationWarning)
            dry_run = safe_calls_only
        if debug_callback is not None:
            warnings.warn(
                "debug_callback is deprecated; use logging with level DEBUG instead.",
                DeprecationWarning,
            )

        self._debug_callback: t.Callable[[int, str], t.Any] = debug_callback or (
            lambda lvl, msg: _logger.log(logging.DEBUG + 4 - lvl, msg)
        )
        self._base_url: str = base_url
        self._doc_path: str = doc_path
        self._dry_run: bool = dry_run
        self._headers = CIMultiDict(headers or {})
        self._verify_ssl = verify_ssl

        self._auth_provider = auth_provider
        self._cert = cert
        self._key = key

        self._headers.update(
            {
                "User-Agent": user_agent or f"Pulp-glue openapi parser ({__version__})",
                "Accept": "application/json",
            }
        )
        if cid:
            self._headers["Correlation-Id"] = cid

        self.load_api(refresh_cache=refresh_cache)

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def cid(self) -> str | None:
        return self._headers.get("Correlation-Id")

    @cached_property
    def ssl_context(self) -> t.Union[ssl.SSLContext, bool]:
        _ssl_context: t.Union[ssl.SSLContext, bool]
        if self._verify_ssl is False:
            _ssl_context = False
        else:
            if isinstance(self._verify_ssl, str):
                _ssl_context = ssl.create_default_context(cafile=self._verify_ssl)
            else:
                _ssl_context = ssl.create_default_context()
            if self._cert:
                _ssl_context.load_cert_chain(self._cert, self._key)
        return _ssl_context

    def load_api(self, refresh_cache: bool = False) -> None:
        asyncio.run(self._load_api(refresh_cache=refresh_cache))

    async def _load_api(self, refresh_cache: bool = False) -> None:
        # TODO: Find a way to invalidate caches on upstream change.
        xdg_cache_home: str = os.environ.get("XDG_CACHE_HOME") or "~/.cache"
        apidoc_cache: str = os.path.join(
            os.path.expanduser(xdg_cache_home),
            "squeezer",
            (self._base_url + "_" + self._doc_path).replace(":", "_").replace("/", "_")
            + "api.json",
        )
        try:
            if refresh_cache:
                # Fake that we did not find the cache.
                raise OSError()
            async with aiofiles.open(apidoc_cache, mode="rb") as f:
                data: bytes = await f.read()
            self._parse_api(data)
        except Exception:
            # Try again with a freshly downloaded version.
            data = await self._download_api()
            self._parse_api(data)
            # Write to cache as it seems to be valid.
            await aiofiles.os.makedirs(os.path.dirname(apidoc_cache), exist_ok=True)
            async with aiofiles.open(apidoc_cache, mode="bw") as f:
                await f.write(data)

    def _parse_api(self, data: bytes) -> None:
        self.api_spec: dict[str, t.Any] = json.loads(data)
        if self.api_spec.get("openapi", "").startswith("3."):
            self.openapi_version: int = 3
        else:
            raise OpenAPIError(_("Unknown schema version"))
        self.operations: dict[str, t.Any] = {
            method_entry["operationId"]: (method, path)
            for path, path_entry in self.api_spec["paths"].items()
            for method, method_entry in path_entry.items()
            if method in {"get", "put", "post", "delete", "options", "head", "patch", "trace"}
        }

    async def _download_api(self) -> bytes:
        response = await self._send_request(
            _Request(
                operation_id="",
                method="get",
                url=urljoin(self._base_url, self._doc_path),
                headers=self._headers,
            )
        )
        if response.status_code != 200:
            raise OpenAPIError(_("Failed to find api docs."))
        return response.body

    def _set_correlation_id(self, correlation_id: str) -> None:
        if "Correlation-Id" in self._headers:
            if self._headers["Correlation-Id"] != correlation_id:
                raise OpenAPIError(
                    _("Correlation ID returned from server did not match. {} != {}").format(
                        self._headers["Correlation-Id"], correlation_id
                    )
                )
        else:
            self._headers["Correlation-Id"] = correlation_id

    def param_spec(
        self, operation_id: str, param_type: str, required: bool = False
    ) -> dict[str, t.Any]:
        method, path = self.operations[operation_id]
        path_spec = self.api_spec["paths"][path]
        method_spec = path_spec[method]

        param_spec = {
            entry["name"]: entry
            for entry in path_spec.get("parameters", [])
            if entry["in"] == param_type
        }
        param_spec.update(
            {
                entry["name"]: entry
                for entry in method_spec.get("parameters", [])
                if entry["in"] == param_type
            }
        )
        if required:
            param_spec = {k: v for k, v in param_spec.items() if v.get("required", False)}
        return param_spec

    def _extract_params(
        self,
        param_in: str,
        path_spec: dict[str, t.Any],
        method_spec: dict[str, t.Any],
        params: dict[str, t.Any],
    ) -> dict[str, t.Any]:
        param_specs = {
            entry["name"]: entry
            for entry in path_spec.get("parameters", [])
            if entry["in"] == param_in
        }
        param_specs.update(
            {
                entry["name"]: entry
                for entry in method_spec.get("parameters", [])
                if entry["in"] == param_in
            }
        )
        result: dict[str, t.Any] = {}
        for name in list(params.keys()):
            if name in param_specs:
                param = params.pop(name)
                param_spec = param_specs.pop(name)
                param_schema = param_spec.get("schema")
                if param_schema is not None:
                    self.validate_schema(param_schema, name, param)

                param = encode_param(param)
                if isinstance(param, list):
                    if not param:
                        # Don't propagate an empty list here
                        continue
                    # Check if we need to implode the list
                    style = (
                        param_spec.get("style") or "form"
                        if param_in in ("query", "cookie")
                        else "simple"
                    )
                    explode: bool = param_spec.get("explode", style == "form")
                    if not explode:
                        # Not exploding means comma separated list
                        param = ",".join(param)
                result[name] = param
        remaining_required = [
            item["name"] for item in param_specs.values() if item.get("required", False)
        ]
        if any(remaining_required):
            raise RuntimeError(
                _("Required parameters [{required}] missing in {param_in}.").format(
                    required=", ".join(remaining_required), param_in=param_in
                )
            )
        return result

    def validate_schema(self, schema: t.Any, name: str, value: t.Any) -> None:
        validate(schema, name, value, self.api_spec["components"]["schemas"])

    def _render_request_body(
        self,
        method_spec: dict[str, t.Any],
        body: dict[str, t.Any] | None = None,
        validate_body: bool = True,
    ) -> tuple[
        str | None,
        dict[str, t.Any] | str | None,
        dict[str, tuple[str, UploadType, str]] | None,
    ]:
        content_types: list[str] = []
        try:
            request_body_spec = method_spec["requestBody"]
        except KeyError:
            if body is not None:
                raise OpenAPIError(_("This operation does not expect a request body."))
            return None, None, None
        else:
            body_required = request_body_spec.get("required", False)
            if body is None and not body_required:
                # shortcut
                return None, None, None
            content_types = list(request_body_spec["content"].keys())
        assert body is not None

        content_type: str | None = None
        data: dict[str, t.Any] | str | None = None
        files: dict[str, tuple[str, UploadType, str]] | None = None

        candidate_content_types = [
            "multipart/form-data",
        ]
        if not any((isinstance(value, (bytes, BufferedReader)) for value in body.values())):
            candidate_content_types = [
                "application/json",
                "application/x-www-form-urlencoded",
            ] + candidate_content_types
        errors: list[str] = []
        for candidate in candidate_content_types:
            content_type = next(
                (
                    content_type
                    for content_type in content_types
                    if content_type.startswith(candidate)
                ),
                None,
            )
            if content_type:
                if validate_body:
                    try:
                        self.validate_schema(
                            request_body_spec["content"][content_type]["schema"],
                            "body",
                            body,
                        )
                    except ValidationError as e:
                        errors.append(f"{content_type}: {e}")
                        # Try the next content-type
                        continue

                if content_type.startswith("application/json"):
                    data = encode_json(body)
                elif content_type.startswith("application/x-www-form-urlencoded"):
                    data = body
                elif content_type.startswith("multipart/form-data"):
                    data = {}
                    files = {}
                    # Extract and prepare the files to upload
                    if body:
                        for key, value in body.items():
                            if isinstance(value, (bytes, BufferedReader)):
                                files[key] = (
                                    getattr(value, "name", key),
                                    value,
                                    "application/octet-stream",
                                )
                            else:
                                data[key] = value
                break
        else:
            # No known content-type left
            if errors:
                raise ValidationError(
                    _("Validation failed for '{operation_id}':\n  ").format(
                        operation_id=method_spec["operationId"]
                    )
                    + "\n  ".join(errors)
                )
            else:
                raise ValidationError(_("No valid content type found."))

        return content_type, data, files

    def _render_request(
        self,
        path_spec: dict[str, t.Any],
        method: str,
        url: str,
        params: dict[str, t.Any],
        headers: dict[str, str],
        body: dict[str, t.Any] | None = None,
        validate_body: bool = True,
    ) -> _Request:
        method_spec = path_spec[method]
        _headers = CIMultiDict(self._headers)
        _headers.update(headers)

        security: list[dict[str, list[str]]] | None
        if self._auth_provider and "Authorization" not in self._headers:
            security = method_spec.get("security", self.api_spec.get("security"))
        else:
            # No auth required? Don't provide it.
            # No auth_provider available? Hope for the best (should do the trick for cert auth).
            # Authorization header present? You wanted it that way...
            security = None

        content_type, data, files = self._render_request_body(method_spec, body, validate_body)
        # For we encode the json on our side.
        # Somehow this does not work properly for multipart...
        if content_type is not None and content_type.startswith("application/json"):
            _headers["Content-Type"] = content_type

        return _Request(
            operation_id=method_spec["operationId"],
            method=method,
            url=url,
            headers=_headers,
            params=params,
            data=data,
            files=files,
            security=security,
        )

    def _log_request(self, request: _Request) -> None:
        if request.params:
            qs = urlencode(request.params)
            self._debug_callback(1, f"{request.operation_id} : {request.method} {request.url}?{qs}")
            self._debug_callback(
                2, "\n".join([f"  {key}=={value}" for key, value in request.params.items()])
            )
        else:
            self._debug_callback(1, f"{request.operation_id} : {request.method} {request.url}")
        for key, value in request.headers.items():
            self._debug_callback(2, f"  {key}: {value}")
        if request.data is not None:
            self._debug_callback(3, f"{request.data!r}")
        if request.files is not None:
            for key, (name, _dummy, content_type) in request.files.items():
                self._debug_callback(3, f"{key} <- {name} [{content_type}]")

    async def _send_request(
        self,
        request: _Request,
    ) -> _Response:
        # This function uses aiohttp to translate the _Request into a _Response.
        data: aiohttp.FormData | dict[str, t.Any] | str | None
        if request.files:
            assert isinstance(request.data, dict)
            data = aiohttp.FormData(default_to_multipart=True)
            for key, value in request.data.items():
                data.add_field(key, encode_param(value))
            for key, (name, value, content_type) in request.files.items():
                data.add_field(key, value, filename=name, content_type=content_type)
        else:
            data = request.data
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    request.method,
                    request.url,
                    params=request.params,
                    headers=request.headers,
                    data=data,
                    ssl=self.ssl_context,
                    max_redirects=0,
                    middlewares=[_Middleware(self, request.security)],
                ) as r:
                    response_body = await r.read()
                    response = _Response(
                        status_code=r.status, headers=r.headers, body=response_body
                    )
        except aiohttp.TooManyRedirects as e:
            # We could handle that in the middleware...
            assert e.history[-1] is not None
            raise OpenAPIError(
                _(
                    "Received redirect to '{new_url} from {old_url}'."
                    " Please check your configuration."
                ).format(
                    new_url=e.history[-1].headers["location"],
                    old_url=request.url,
                )
            )
        except aiohttp.ClientResponseError as e:
            raise OpenAPIError(str(e))

        return response

    def _log_response(self, response: _Response) -> None:
        self._debug_callback(
            1, _("Response: {status_code}").format(status_code=response.status_code)
        )
        for key, value in response.headers.items():
            self._debug_callback(2, f"  {key}: {value}")
        if response.body:
            self._debug_callback(3, f"{response.body!r}")

    def _parse_response(self, method_spec: dict[str, t.Any], response: _Response) -> t.Any:
        if response.status_code == 401:
            raise PulpAuthenticationFailed(method_spec["operationId"])
        elif response.status_code == 403:
            raise PulpNotAutorized(method_spec["operationId"])
        elif response.status_code >= 300:
            raise PulpHTTPError(response.body.decode(), response.status_code)

        if response.status_code == 204:
            return {}

        try:
            response_spec = method_spec["responses"][str(response.status_code)]
        except KeyError:
            # Fallback 201 -> 200
            try:
                response_spec = method_spec["responses"][str(100 * int(response.status_code / 100))]
            except KeyError:
                raise OpenAPIError(
                    _("Unexpected response '{code}' (expected '{expected}').").format(
                        code=response.status_code,
                        expected=(", ").join(method_spec["responses"].keys()),
                    )
                )
        content_type = response.headers.get("content-type")
        if content_type is not None and content_type.startswith("application/json"):
            assert content_type in response_spec["content"]
            return json.loads(response.body)
        return None

    def call(
        self,
        operation_id: str,
        parameters: dict[str, t.Any] | None = None,
        body: dict[str, t.Any] | None = None,
        validate_body: bool = True,
    ) -> t.Any:
        """
        Make a call to the server.

        Parameters:
            operation_id: ID of the operation in the openapi v3 specification.
            parameters: Arguments that are to be sent as headers, querystrings or part of the URI.
            body: Body payload for POST, PUT, PATCH calls.
            validate_body: Indicate whether the body should be validated.

        Returns:
            The JSON decoded server response if any.

        Raises:
            ValidationError: on failed input validation (no request was sent to the server).
            OpenAPIError: on failures related to the HTTP call made.
        """
        method, path = self.operations[operation_id]
        path_spec = self.api_spec["paths"][path]
        method_spec = path_spec[method]

        if parameters is None:
            parameters = {}
        else:
            parameters = parameters.copy()

        if any(self._extract_params("cookie", path_spec, method_spec, parameters)):
            raise NotImplementedError(_("Cookie parameters are not implemented."))

        headers = self._extract_params("header", path_spec, method_spec, parameters)

        for name, value in self._extract_params("path", path_spec, method_spec, parameters).items():
            path = path.replace("{" + name + "}", value)

        query_params = self._extract_params("query", path_spec, method_spec, parameters)

        if any(parameters):
            raise OpenAPIError(
                _("Parameter [{names}] not available for {operation_id}.").format(
                    names=", ".join(parameters.keys()), operation_id=operation_id
                )
            )
        url = urljoin(self._base_url, path)

        request = self._render_request(
            path_spec,
            method,
            url,
            query_params,
            headers,
            body,
            validate_body=validate_body,
        )
        self._log_request(request)

        if self._dry_run and request.method.upper() not in SAFE_METHODS:
            raise UnsafeCallError(_("Call aborted due to safe mode"))

        response = asyncio.run(self._send_request(request))

        self._log_response(response)
        return self._parse_response(method_spec, response)
