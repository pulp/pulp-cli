# copyright (c) 2020, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

import json
import os
import typing as t
from collections import defaultdict
from dataclasses import dataclass
from io import BufferedReader
from urllib.parse import urlencode, urljoin

import requests
import urllib3
from multidict import CIMultiDict, MutableMultiMapping

from pulp_glue.common import __version__
from pulp_glue.common.exceptions import (
    OpenAPIError,
    PulpAuthenticationFailed,
    PulpException,
    PulpHTTPError,
    PulpNotAutorized,
    UnsafeCallError,
    ValidationError,
)
from pulp_glue.common.i18n import get_translation
from pulp_glue.common.schema import encode_json, encode_param, validate

translation = get_translation(__package__)
_ = translation.gettext

UploadType = t.Union[bytes, t.IO[bytes]]

SAFE_METHODS = ["GET", "HEAD", "OPTIONS"]


@dataclass
class _Response:
    status_code: int
    headers: t.Union[MutableMultiMapping[str], t.MutableMapping[str, str]]
    body: bytes


class AuthProviderBase:
    """
    Base class for auth providers.

    This abstract base class will analyze the authentication proposals of the openapi specs.
    Different authentication schemes should be implemented by subclasses.
    Returned auth objects need to be compatible with `requests.auth.AuthBase`.
    """

    def basic_auth(self, scopes: t.List[str]) -> t.Optional[requests.auth.AuthBase]:
        """Implement this to provide means of http basic auth."""
        return None

    def http_auth(
        self, security_scheme: t.Dict[str, t.Any], scopes: t.List[str]
    ) -> t.Optional[requests.auth.AuthBase]:
        """Select a suitable http auth scheme or return None."""
        # https://www.iana.org/assignments/http-authschemes/http-authschemes.xhtml
        if security_scheme["scheme"] == "basic":
            result = self.basic_auth(scopes)
            if result:
                return result
        return None

    def oauth2_client_credentials_auth(
        self, flow: t.Any, scopes: t.List[str]
    ) -> t.Optional[requests.auth.AuthBase]:
        """Implement this to provide other authentication methods."""
        return None

    def oauth2_auth(
        self, security_scheme: t.Dict[str, t.Any], scopes: t.List[str]
    ) -> t.Optional[requests.auth.AuthBase]:
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
        security: t.List[t.Dict[str, t.List[str]]],
        security_schemes: t.Dict[str, t.Dict[str, t.Any]],
    ) -> t.Optional[requests.auth.AuthBase]:

        # Reorder the proposals by their type to prioritize properly.
        # Select only single mechanism proposals on the way.
        proposed_schemes: t.Dict[str, t.Dict[str, t.List[str]]] = defaultdict(dict)
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
        self.auth = requests.auth.HTTPBasicAuth(username, password)

    def basic_auth(self, scopes: t.List[str]) -> t.Optional[requests.auth.AuthBase]:
        return self.auth


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
        verify: Whether to check server TLS certificates agains a CA (requests semantic).
        refresh_cache: Whether to fetch the api doc regardless.
        safe_calls_only: Flag to disallow issuing POST, PUT, PATCH or DELETE calls.
        debug_callback: Callback that will be called with strings useful for logging or debugging.
        user_agent: String to use in the User-Agent header.
        cid: Correlation ID to send with all requests.
    """

    def __init__(
        self,
        base_url: str,
        doc_path: str,
        headers: t.Optional[CIMultiDict[str]] = None,
        auth_provider: t.Optional[AuthProviderBase] = None,
        cert: t.Optional[str] = None,
        key: t.Optional[str] = None,
        verify: t.Optional[t.Union[bool, str]] = True,
        refresh_cache: bool = False,
        safe_calls_only: bool = False,
        debug_callback: t.Optional[t.Callable[[int, str], t.Any]] = None,
        user_agent: t.Optional[str] = None,
        cid: t.Optional[str] = None,
    ):
        self._debug_callback: t.Callable[[int, str], t.Any] = debug_callback or (lambda i, x: None)
        self._base_url: str = base_url
        self._doc_path: str = doc_path
        self._safe_calls_only: bool = safe_calls_only
        self._headers = CIMultiDict(headers or {})
        self._verify = verify
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

        self._setup_session()

        self.load_api(refresh_cache=refresh_cache)

    def _setup_session(self) -> None:
        # This is specific requests library.

        if self._verify is False:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        self._session: requests.Session = requests.session()
        # Don't redirect, because carrying auth accross redirects is unsafe.
        self._session.max_redirects = 0
        self._session.headers.update(self._headers)
        if self._auth_provider:
            if self._cert or self._key:
                raise OpenAPIError(_("Cannot use both 'auth' and 'cert'."))
        else:
            if self._cert and self._key:
                self._session.cert = (self._cert, self._key)
            elif self._cert:
                self._session.cert = self._cert
            elif self._key:
                raise OpenAPIError(_("Cert is required if key is set."))
        session_settings = self._session.merge_environment_settings(
            self._base_url, {}, None, self._verify, None
        )
        self._session.verify = session_settings["verify"]
        self._session.proxies = session_settings["proxies"]

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def cid(self) -> t.Optional[str]:
        return self._headers.get("Correlation-Id")

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
                raise IOError()
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
        self.api_spec: t.Dict[str, t.Any] = json.loads(data)
        if self.api_spec.get("openapi", "").startswith("3."):
            self.openapi_version: int = 3
        else:
            raise OpenAPIError(_("Unknown schema version"))
        self.operations: t.Dict[str, t.Any] = {
            method_entry["operationId"]: (method, path)
            for path, path_entry in self.api_spec["paths"].items()
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
    ) -> t.Dict[str, t.Any]:
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
        path_spec: t.Dict[str, t.Any],
        method_spec: t.Dict[str, t.Any],
        params: t.Dict[str, t.Any],
    ) -> t.Dict[str, t.Any]:
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
        result: t.Dict[str, t.Any] = {}
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
        method_spec: t.Dict[str, t.Any],
        body: t.Optional[t.Dict[str, t.Any]] = None,
        validate_body: bool = True,
    ) -> t.Tuple[
        t.Optional[str],
        t.Optional[t.Union[t.Dict[str, t.Any], str]],
        t.Optional[t.List[t.Tuple[str, t.Tuple[str, UploadType, str]]]],
    ]:
        content_types: t.List[str] = []
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

        content_type: t.Optional[str] = None
        data: t.Optional[t.Union[t.Dict[str, t.Any], str]] = None
        files: t.Optional[t.List[t.Tuple[str, t.Tuple[str, UploadType, str]]]] = None

        candidate_content_types = [
            "multipart/form-data",
        ]
        if not any((isinstance(value, (bytes, BufferedReader)) for value in body.values())):
            candidate_content_types = [
                "application/json",
                "application/x-www-form-urlencoded",
            ] + candidate_content_types
        errors: t.List[str] = []
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
                    uploads: t.Dict[str, t.Tuple[str, UploadType, str]] = {}
                    data = {}
                    # Extract and prepare the files to upload
                    if body:
                        for key, value in body.items():
                            if isinstance(value, (bytes, BufferedReader)):
                                uploads[key] = (
                                    getattr(value, "name", key),
                                    value,
                                    "application/octet-stream",
                                )
                            else:
                                data[key] = value
                    if uploads:
                        files = [(key, upload_data) for key, upload_data in uploads.items()]
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

    def _send_request(
        self,
        path_spec: t.Dict[str, t.Any],
        method: str,
        url: str,
        params: t.Dict[str, t.Any],
        headers: t.Dict[str, str],
        body: t.Optional[t.Dict[str, t.Any]] = None,
        validate_body: bool = True,
    ) -> _Response:
        method_spec = path_spec[method]
        content_type, data, files = self._render_request_body(method_spec, body, validate_body)
        security: t.Optional[t.List[t.Dict[str, t.List[str]]]] = method_spec.get(
            "security", self.api_spec.get("security")
        )
        if security and self._auth_provider:
            if "Authorization" in self._session.headers:
                # Bad idea, but you wanted it that way.
                auth = None
            else:
                auth = self._auth_provider(security, self.api_spec["components"]["securitySchemes"])
        else:
            # No auth required? Don't provide it.
            # No auth_provider available? Hope for the best (should do the trick for cert auth).
            auth = None
        # For we encode the json on our side.
        # Somehow this does not work properly for multipart...
        if content_type is not None and content_type.startswith("application/json"):
            headers["content-type"] = content_type
        request = self._session.prepare_request(
            requests.Request(
                method,
                url,
                auth=auth,
                params=params,
                headers=headers,
                data=data,
                files=files,
            )
        )
        if content_type:
            assert request.headers["content-type"].startswith(
                content_type
            ), f"{request.headers['content-type']} != {content_type}"
        for key, value in request.headers.items():
            self._debug_callback(2, f"  {key}: {value}")
        if request.body is not None:
            self._debug_callback(3, f"{request.body!r}")
        if self._safe_calls_only and method.upper() not in SAFE_METHODS:
            raise UnsafeCallError(_("Call aborted due to safe mode"))
        try:
            response = self._session.send(request)
        except requests.TooManyRedirects as e:
            assert e.response is not None
            raise OpenAPIError(
                _("Received redirect to '{url}'. Please check your CLI configuration.").format(
                    url=e.response.headers["location"]
                )
            )
        except requests.RequestException as e:
            raise OpenAPIError(str(e))
        self._debug_callback(
            1, _("Response: {status_code}").format(status_code=response.status_code)
        )
        for key, value in response.headers.items():
            self._debug_callback(2, f"  {key}: {value}")
        if response.text:
            self._debug_callback(3, f"{response.text}")
        if "Correlation-Id" in response.headers:
            self._set_correlation_id(response.headers["Correlation-Id"])
        if response.status_code == 401:
            raise PulpAuthenticationFailed(method_spec["operationId"])
        if response.status_code == 403:
            raise PulpNotAutorized(method_spec["operationId"])
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            if e.response is not None:
                raise PulpHTTPError(str(e.response.text), e.response.status_code)
            else:
                raise PulpException(str(e))
        return _Response(
            status_code=response.status_code, headers=response.headers, body=response.content
        )

    def _parse_response(self, method_spec: t.Dict[str, t.Any], response: _Response) -> t.Any:
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
        parameters: t.Optional[t.Dict[str, t.Any]] = None,
        body: t.Optional[t.Dict[str, t.Any]] = None,
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
            OpenAPIValidationError: on failed input validation (no request was sent to the server).
            requests.HTTPError: on failures related to the HTTP call made.
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

        if query_params:
            qs = urlencode(query_params)
            self._debug_callback(1, f"{operation_id} : {method} {url}?{qs}")
        else:
            self._debug_callback(1, f"{operation_id} : {method} {url}")
        self._debug_callback(
            2, "\n".join([f"  {key}=={value}" for key, value in query_params.items()])
        )

        response = self._send_request(
            path_spec,
            method,
            url,
            query_params,
            headers,
            body,
            validate_body=validate_body,
        )

        return self._parse_response(method_spec, response)
