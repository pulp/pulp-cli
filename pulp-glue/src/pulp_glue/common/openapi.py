import asyncio
import json
import logging
import os
import ssl
import typing as t
import warnings
from base64 import b64encode
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import cached_property
from io import BufferedReader
from urllib.parse import urlencode, urljoin

import requests
import urllib3
from multidict import CIMultiDict, CIMultiDictProxy, MutableMultiMapping

from pulp_glue.common import __version__
from pulp_glue.common.authentication import AuthProviderBase
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
    headers: MutableMultiMapping[str] | CIMultiDict[str] | t.MutableMapping[str, str]
    params: dict[str, str] | None = None
    data: dict[str, t.Any] | str | None = None
    files: dict[str, tuple[str, UploadType, str]] | None = None
    security: list[dict[str, list[str]]] | None = None


@dataclass
class _Response:
    status_code: int
    headers: MutableMultiMapping[str] | CIMultiDictProxy[str] | t.MutableMapping[str, str]
    body: bytes


class OpenAPI:
    """
    The abstraction Layer to interact with a server providing an openapi v3 specification.

    Parameters:
        base_url: The base URL inlcuding the HTTP scheme, hostname and optional subpaths of the
            served api.
        doc_path: Path of the json api doc schema relative to the `base_url`.
        headers: Dictionary of additional request headers.
        auth_provider: Object that can be questioned for credentials according to the api spec.
        cert: Client certificate used for auth.
        key: Matching key for `cert` if not already included.
        verify_ssl: Whether to check server TLS certificates agains a CA.
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
                "validate_certs is deprecated; use verify_ssl instead.",
                DeprecationWarning,
            )
            verify_ssl = validate_certs
        if safe_calls_only is not None:
            warnings.warn(
                "safe_calls_only is deprecated; use dry_run instead.",
                DeprecationWarning,
            )
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

        self._headers.update(
            {
                "User-Agent": user_agent or f"Pulp-glue openapi parser ({__version__})",
                "Accept": "application/json",
            }
        )
        if cid:
            self._headers["Correlation-Id"] = cid

        self._setup_session()

        self._oauth2_lock = asyncio.Lock()
        self._oauth2_token: str | None = None
        self._oauth2_expires: datetime = datetime.now()

        self.load_api(refresh_cache=refresh_cache)

    def _setup_session(self) -> None:
        # This is specific requests library.

        if self._verify_ssl is False:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        self._session: requests.Session = requests.session()
        # Don't redirect, because carrying auth accross redirects is unsafe.
        self._session.max_redirects = 0
        self._session.headers.update(self._headers)
        session_settings = self._session.merge_environment_settings(
            self._base_url, {}, None, self._verify_ssl, None
        )
        self._session.verify = session_settings["verify"]
        self._session.proxies = session_settings["proxies"]

        if self._auth_provider is not None and self._auth_provider.can_complete_mutualTLS():
            cert, key = self._auth_provider.tls_credentials()
            if key is not None:
                self._session.cert = (cert, key)
            else:
                self._session.cert = cert

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
            if self._auth_provider is not None and self._auth_provider.can_complete_mutualTLS():
                _ssl_context.load_cert_chain(*self._auth_provider.tls_credentials())
        return _ssl_context

    def load_api(self, refresh_cache: bool = False) -> None:
        # TODO: Find a way to invalidate caches on upstream change
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
            with open(apidoc_cache, "rb") as f:
                data: bytes = f.read()
            self._parse_api(data)
        except Exception:
            # Try again with a freshly downloaded version
            data = self._download_api()
            self._parse_api(data)
            # Write to cache as it seems to be valid
            os.makedirs(os.path.dirname(apidoc_cache), exist_ok=True)
            with open(apidoc_cache, "bw") as f:
                f.write(data)

    def _parse_api(self, data: bytes) -> None:
        self.api_spec: dict[str, t.Any] = json.loads(data)
        if self.api_spec.get("openapi", "").startswith("3."):
            self.openapi_version: int = 3
        else:
            raise OpenAPIError(_("Unknown schema version"))
        self.operations: dict[str, t.Any] = {
            method_entry["operationId"]: (method, path)
            for path, path_entry in self.api_spec.get("paths", {}).items()
            for method, method_entry in path_entry.items()
            if method in {"get", "put", "post", "delete", "options", "head", "patch", "trace"}
        }

    def _download_api(self) -> bytes:
        try:
            response: requests.Response = self._session.get(urljoin(self._base_url, self._doc_path))
        except requests.RequestException as e:
            raise OpenAPIError(str(e))
        response.raise_for_status()
        if "Correlation-Id" in response.headers:
            self._set_correlation_id(response.headers["Correlation-Id"])
        return response.content

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
            # Do it for requests too...
            self._session.headers["Correlation-Id"] = correlation_id

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
                                # If available, use the filename.
                                files[key] = (
                                    getattr(value, "name", key).split("/")[-1],
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
                2,
                "\n".join([f"  {key}=={value}" for key, value in request.params.items()]),
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

    def _select_proposal(
        self,
        request: _Request,
    ) -> dict[str, list[str]] | None:
        proposal = None
        if (
            request.security
            and "Authorization" not in request.headers
            and "Authorization" not in self._session.headers
            and self._auth_provider is not None
        ):
            security_schemes: dict[str, dict[str, t.Any]] = self.api_spec["components"][
                "securitySchemes"
            ]
            try:
                proposal = next(
                    (
                        p
                        for p in request.security
                        if self._auth_provider.can_complete(p, security_schemes)
                    )
                )
            except StopIteration:
                raise OpenAPIError(_("No suitable auth scheme found."))
        return proposal

    async def _authenticate_request(
        self,
        request: _Request,
        proposal: dict[str, list[str]],
    ) -> bool:
        assert self._auth_provider is not None

        may_retry = False
        security_schemes = self.api_spec["components"]["securitySchemes"]
        for scheme_name, scopes in proposal.items():
            scheme = security_schemes[scheme_name]
            if scheme["type"] == "http":
                if scheme["scheme"] == "basic":
                    username, password = await self._auth_provider.http_basic_credentials()
                    secret = b64encode(username + b":" + password)
                    # TODO Should we add, amend or replace the existing auth header?
                    request.headers["Authorization"] = f"Basic {secret.decode()}"
                else:
                    raise NotImplementedError("Auth scheme: http " + scheme["scheme"])
            elif scheme["type"] == "oauth2":
                flow = scheme["flows"].get("clientCredentials")
                if flow is None:
                    raise NotImplementedError("OAuth2: Only client credential flow is available.")
                # Allow retry if the token was taken from cache.
                may_retry = not await self._fetch_oauth2_token(flow)
                request.headers["Authorization"] = f"Bearer {self._oauth2_token}"
            elif scheme["type"] == "mutualTLS":
                # At this point, we assume the cert has already been loaded into the sslcontext.
                pass
            else:
                raise NotImplementedError("Auth type: " + scheme["type"])
        return may_retry

    async def _fetch_oauth2_token(self, flow: dict[str, t.Any]) -> bool:
        assert self._auth_provider is not None

        new_token = False
        async with self._oauth2_lock:
            now = datetime.now()
            if self._oauth2_token is None or self._oauth2_expires < now:
                # Get or refresh token.
                client_id, client_secret = await self._auth_provider.oauth2_client_credentials()
                secret = b64encode(client_id + b":" + client_secret)
                data: dict[str, t.Any] = {"grant_type": "client_credentials"}
                scopes = flow.get("scopes")
                if scopes:
                    data["scopes"] = " ".join(scopes)
                request = _Request(
                    operation_id="",
                    method="post",
                    url=flow["tokenUrl"],
                    headers={"Authorization": f"Basic {secret.decode()}"},
                    data=data,
                )
                response = self._send_request(request)
                if response.status_code < 200 or response.status_code >= 300:
                    raise OpenAPIError("Failed to fetch OAuth2 token")
                result = json.loads(response.body)
                self._oauth2_token = result["access_token"]
                self._oauth2_expires = now + timedelta(seconds=result["expires_in"])
                new_token = True
        return new_token

    def _send_request(
        self,
        request: _Request,
    ) -> _Response:
        # This function uses requests to translate the _Request into a _Response.
        try:
            r = self._session.request(
                request.method,
                request.url,
                params=request.params,
                headers=request.headers,
                data=request.data,
                files=request.files,
            )
            response = _Response(status_code=r.status_code, headers=r.headers, body=r.content)
        except requests.TooManyRedirects as e:
            assert e.response is not None
            raise OpenAPIError(
                _(
                    "Received redirect to '{new_url} from {old_url}'."
                    " Please check your configuration."
                ).format(
                    new_url=e.response.headers["location"],
                    old_url=request.url,
                )
            )
        except requests.RequestException as e:
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
        if "Correlation-Id" in response.headers:
            self._set_correlation_id(response.headers["Correlation-Id"])
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

        rel_url = path
        for name, value in self._extract_params("path", path_spec, method_spec, parameters).items():
            rel_url = path.replace("{" + name + "}", value)

        query_params = self._extract_params("query", path_spec, method_spec, parameters)

        if any(parameters):
            raise OpenAPIError(
                _("Parameter [{names}] not available for {operation_id}.").format(
                    names=", ".join(parameters.keys()), operation_id=operation_id
                )
            )
        url = urljoin(self._base_url, rel_url)

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

        may_retry = False
        if proposal := self._select_proposal(request):
            assert len(proposal) == 1, "More complex security proposals are not implemented."
            may_retry = asyncio.run(self._authenticate_request(request, proposal))

        response = self._send_request(request)

        if proposal is not None:
            assert self._auth_provider is not None
            if may_retry and response.status_code == 401:
                self._oauth2_token = None
                asyncio.run(self._authenticate_request(request, proposal))
                response = self._send_request(request)

            if response.status_code >= 200 and response.status_code < 300:
                asyncio.run(
                    self._auth_provider.auth_success_hook(
                        proposal, self.api_spec["components"]["securitySchemes"]
                    )
                )
            elif response.status_code == 401:
                asyncio.run(
                    self._auth_provider.auth_failure_hook(
                        proposal, self.api_spec["components"]["securitySchemes"]
                    )
                )

        self._log_response(response)
        return self._parse_response(method_spec, response)
