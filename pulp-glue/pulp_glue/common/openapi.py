# copyright (c) 2020, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

import base64
import datetime
import json
import os
import typing as t
from collections import defaultdict
from contextlib import suppress
from io import BufferedReader
from urllib.parse import urljoin

import requests
import urllib3

from pulp_glue.common import __version__
from pulp_glue.common.i18n import get_translation

translation = get_translation(__package__)
_ = translation.gettext

UploadType = t.Union[bytes, t.IO[bytes]]

SAFE_METHODS = ["GET", "HEAD", "OPTIONS"]
ISO_DATE_FORMAT = "%Y-%m-%d"
ISO_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


class OpenAPIError(Exception):
    """Base Exception for errors related to using the openapi spec."""

    pass


class OpenAPIValidationError(OpenAPIError):
    """Exception raised for failed client side validation of parameters or request bodies."""

    pass


class UnsafeCallError(OpenAPIError):
    """Exception raised for POST, PUT, PATCH or DELETE calls with `safe_calls_only=True`."""

    pass


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
        validate_certs: Whether to check server TLS certificates agains a CA.
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
        headers: t.Optional[t.Dict[str, str]] = None,
        auth_provider: t.Optional[AuthProviderBase] = None,
        cert: t.Optional[str] = None,
        key: t.Optional[str] = None,
        validate_certs: bool = True,
        refresh_cache: bool = False,
        safe_calls_only: bool = False,
        debug_callback: t.Optional[t.Callable[[int, str], t.Any]] = None,
        user_agent: t.Optional[str] = None,
        cid: t.Optional[str] = None,
    ):
        if not validate_certs:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        self.debug_callback: t.Callable[[int, str], t.Any] = debug_callback or (lambda i, x: None)
        self.base_url: str = base_url
        self.doc_path: str = doc_path
        self.safe_calls_only: bool = safe_calls_only
        self.auth_provider = auth_provider

        self._session: requests.Session = requests.session()
        if self.auth_provider:
            if cert or key:
                raise OpenAPIError(_("Cannot use both 'auth' and 'cert'."))
        else:
            if cert and key:
                self._session.cert = (cert, key)
            elif cert:
                self._session.cert = cert
            elif key:
                raise OpenAPIError(_("Cert is required if key is set."))
        self._session.headers.update(
            {
                "User-Agent": user_agent or f"Pulp-glue openapi parser ({__version__})",
                "Accept": "application/json",
            }
        )
        if cid:
            self._session.headers["Correlation-Id"] = cid
        if headers:
            self._session.headers.update(headers)
        self._session.max_redirects = 0

        verify: t.Optional[t.Union[bool, str]] = validate_certs and os.environ.get(
            "PULP_CA_BUNDLE", True
        )
        session_settings = self._session.merge_environment_settings(
            base_url, {}, None, verify, None
        )
        self._session.verify = session_settings["verify"]
        self._session.proxies = session_settings["proxies"]

        self.load_api(refresh_cache=refresh_cache)

    def load_api(self, refresh_cache: bool = False) -> None:
        # TODO: Find a way to invalidate caches on upstream change
        xdg_cache_home: str = os.environ.get("XDG_CACHE_HOME") or "~/.cache"
        apidoc_cache: str = os.path.join(
            os.path.expanduser(xdg_cache_home),
            "squeezer",
            (self.base_url + "_" + self.doc_path).replace(":", "_").replace("/", "_") + "api.json",
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
            response: requests.Response = self._session.get(urljoin(self.base_url, self.doc_path))
        except requests.RequestException as e:
            raise OpenAPIError(str(e))
        response.raise_for_status()
        if "Correlation-ID" in response.headers:
            self._set_correlation_id(response.headers["Correlation-ID"])
        return response.content

    def _set_correlation_id(self, correlation_id: str) -> None:
        if "Correlation-ID" in self._session.headers:
            if self._session.headers["Correlation-ID"] != correlation_id:
                raise OpenAPIError(
                    _("Correlation ID returned from server did not match. {} != {}").format(
                        self._session.headers["Correlation-ID"], correlation_id
                    )
                )
        else:
            self._session.headers["Correlation-ID"] = correlation_id

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

    def extract_params(
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
                if param_schema:
                    param = self.validate_schema(param_schema, name, param)

                if isinstance(param, t.List):
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

    def validate_schema(self, schema: t.Any, name: str, value: t.Any) -> t.Any:
        # Look if the schema is provided by reference
        schema_ref = schema.get("$ref")
        if schema_ref:
            if not schema_ref.startswith("#/components/schemas/"):
                raise OpenAPIError(_("Api spec is invalid."))
            # len("#/components/schemas/") == 21
            schema_name = schema_ref[21:]
            schema = self.api_spec["components"]["schemas"][schema_name]

        if value is None and schema.get("nullable", False):
            return None

        schema_type = schema.get("type")
        allOf = schema.get("allOf")
        anyOf = schema.get("anyOf")
        oneOf = schema.get("oneOf")
        not_schema = schema.get("not")
        if allOf:
            old_value = value
            value = self.validate_schema(allOf[0], name, value)
            for sub_schema in allOf[1:]:
                # TODO check if it is possible to combine non object types.
                value.update(self.validate_schema(sub_schema, name, old_value))
        elif anyOf:
            for sub_schema in anyOf:
                with suppress(OpenAPIValidationError):
                    value = self.validate_schema(sub_schema, name, value)
                    break
            else:
                raise OpenAPIValidationError(
                    _("No schema in anyOf validated for {name}.").format(name=name)
                )
        elif oneOf:
            old_value = value
            found_valid = False
            for sub_schema in anyOf:
                with suppress(OpenAPIValidationError):
                    value = self.validate_schema(sub_schema, name, old_value)
                    if found_valid:
                        raise OpenAPIValidationError(
                            _("Multiple schemas in oneOf validated for {name}.").format(name=name)
                        )
                    found_valid = True
            if not found_valid:
                raise OpenAPIValidationError(
                    _("No schema in oneOf validated for {name}.").format(name=name)
                )
        elif not_schema:
            try:
                self.validate_schema(not_schema, name, value)
            except OpenAPIValidationError:
                pass
            else:
                raise OpenAPIValidationError(
                    _("Forbidden schema for {name} validated.").format(name=name)
                )
        elif schema_type is None:
            # Schema type is not specified.
            # JSONField
            pass
        elif schema_type == "object":
            # Serializer
            value = self.validate_object(schema, name, value)
        elif schema_type == "array":
            # ListField
            value = self.validate_array(schema, name, value)
        elif schema_type == "string":
            # CharField
            # TextField
            # DateTimeField etc.
            # ChoiceField
            # FielField (binary data)
            value = self.validate_string(schema, name, value)
        elif schema_type == "integer":
            # IntegerField
            value = self.validate_integer(schema, name, value)
        elif schema_type == "number":
            # FloatField
            value = self.validate_number(schema, name, value)
        elif schema_type == "boolean":
            # BooleanField
            if not isinstance(value, bool):
                raise OpenAPIValidationError(
                    _("'{name}' is expected to be a boolean.").format(name=name)
                )
        # TODO: Add more types here.
        else:
            raise OpenAPIError(
                _("Type `{schema_type}` is not implemented yet.").format(schema_type=schema_type)
            )
        return value

    def validate_object(self, schema: t.Any, name: str, value: t.Any) -> t.Dict[str, t.Any]:
        if not isinstance(value, t.Dict):
            raise OpenAPIValidationError(
                _("'{name}' is expected to be an object.").format(name=name)
            )
        properties = schema.get("properties", {})
        additional_properties = schema.get("additionalProperties")
        if properties or additional_properties is not None:
            value = value.copy()
            for property_name, property_value in value.items():
                property_schema = properties.get(property_name, additional_properties)
                if not property_schema:
                    raise OpenAPIValidationError(
                        _("Unexpected property '{property_name}' for '{name}' provided.").format(
                            name=name, property_name=property_name
                        )
                    )
                value[property_name] = self.validate_schema(
                    property_schema, property_name, property_value
                )
        if "required" in schema:
            missing_properties = set(schema["required"]) - set(value.keys())
            if missing_properties:
                raise OpenAPIValidationError(
                    _("Required properties(s) '{missing_properties}' of '{name}' missing.").format(
                        name=name, missing_properties=missing_properties
                    )
                )
        return value

    def validate_array(self, schema: t.Any, name: str, value: t.Any) -> t.List[t.Any]:
        if not isinstance(value, t.List):
            raise OpenAPIValidationError(_("'{name}' is expected to be a list.").format(name=name))
        item_schema = schema["items"]
        return [self.validate_schema(item_schema, name, item) for item in value]

    def validate_string(self, schema: t.Any, name: str, value: t.Any) -> t.Union[str, UploadType]:
        enum = schema.get("enum")
        if enum:
            if value not in enum:
                raise OpenAPIValidationError(
                    _("'{name}' is not one of the valid choices.").format(name=name)
                )
        schema_format = schema.get("format")
        if schema_format == "date":
            if not isinstance(value, datetime.date):
                raise OpenAPIValidationError(
                    _("'{name}' is expected to be a date.").format(name=name)
                )
            return value.strftime(ISO_DATE_FORMAT)
        elif schema_format == "date-time":
            if not isinstance(value, datetime.datetime):
                raise OpenAPIValidationError(
                    _("'{name}' is expected to be a datetime.").format(name=name)
                )
            return value.strftime(ISO_DATETIME_FORMAT)
        elif schema_format == "bytes":
            if not isinstance(value, bytes):
                raise OpenAPIValidationError(
                    _("'{name}' is expected to be bytes.").format(name=name)
                )
            return base64.b64encode(value)
        elif schema_format == "binary":
            if not isinstance(value, (bytes, BufferedReader)):
                raise OpenAPIValidationError(
                    _("'{name}' is expected to be binary.").format(name=name)
                )
            return value
        else:
            if not isinstance(value, str):
                raise OpenAPIValidationError(
                    _("'{name}' is expected to be a string.").format(name=name)
                )
            return value

    def validate_integer(self, schema: t.Any, name: str, value: t.Any) -> int:
        if not isinstance(value, int):
            raise OpenAPIValidationError(
                _("'{name}' is expected to be an integer.").format(name=name)
            )
        minimum = schema.get("minimum")
        if minimum is not None and value < minimum:
            raise OpenAPIValidationError(
                _("'{name}' is violating the minimum constraint").format(name=name)
            )
        maximum = schema.get("maximum")
        if maximum is not None and value > maximum:
            raise OpenAPIValidationError(
                _("'{name}' is violating the maximum constraint").format(name=name)
            )
        return value

    def validate_number(self, schema: t.Any, name: str, value: t.Any) -> float:
        # https://swagger.io/specification/#data-types describes float and double.
        # Python does not distinguish them.
        if not isinstance(value, float):
            raise OpenAPIValidationError(
                _("'{name}' is expected to be a number.").format(name=name)
            )
        return value

    def render_request_body(
        self,
        method_spec: t.Dict[str, t.Any],
        body: t.Optional[t.Dict[str, t.Any]] = None,
        validate_body: bool = True,
    ) -> t.Tuple[
        t.Optional[str],
        t.Optional[t.Dict[str, t.Any]],
        t.Optional[t.Dict[str, t.Any]],
        t.Optional[t.List[t.Tuple[str, t.Tuple[str, UploadType, str]]]],
    ]:
        content_types: t.List[str] = []
        try:
            request_body_spec = method_spec["requestBody"]
        except KeyError:
            if body is not None:
                raise OpenAPIError(_("This operation does not expect a request body."))
            return None, None, None, None
        else:
            body_required = request_body_spec.get("required", False)
            if body is None and not body_required:
                # shortcut
                return None, None, None, None
            content_types = list(request_body_spec["content"].keys())
        assert body is not None

        content_type: t.Optional[str] = None
        data: t.Optional[t.Dict[str, t.Any]] = None
        json: t.Optional[t.Dict[str, t.Any]] = None
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
                        body = self.validate_schema(
                            request_body_spec["content"][content_type]["schema"],
                            "body",
                            body,
                        )
                    except OpenAPIValidationError as e:
                        errors.append(f"{content_type}: {e}")
                        # Try the next content-type
                        continue

                if content_type.startswith("application/json"):
                    json = body
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
                raise OpenAPIError(
                    _("Validation failed for '{operation_id}':\n  ").format(
                        operation_id=method_spec["operationId"]
                    )
                    + "\n  ".join(errors)
                )
            else:
                raise OpenAPIError(_("No valid content type found."))

        return content_type, data, json, files

    def render_request(
        self,
        path_spec: t.Dict[str, t.Any],
        method: str,
        url: str,
        params: t.Dict[str, t.Any],
        headers: t.Dict[str, str],
        body: t.Optional[t.Dict[str, t.Any]] = None,
        validate_body: bool = True,
    ) -> requests.PreparedRequest:
        method_spec = path_spec[method]
        content_type, data, json, files = self.render_request_body(method_spec, body, validate_body)
        security: t.List[t.Dict[str, t.List[str]]] = method_spec.get(
            "security", self.api_spec.get("security", {})
        )
        if security and self.auth_provider:
            if "Authorization" in self._session.headers:
                # Bad idea, but you wanted it that way.
                auth = None
            else:
                auth = self.auth_provider(security, self.api_spec["components"]["securitySchemes"])
        else:
            # No auth required? Don't provide it.
            # No auth_provider available? Hope for the best (should do the trick for cert auth).
            auth = None
        request = self._session.prepare_request(
            requests.Request(
                method,
                url,
                auth=auth,
                params=params,
                headers=headers,
                data=data,
                json=json,
                files=files,
            )
        )
        if content_type:
            assert request.headers["content-type"].startswith(
                content_type
            ), f"{request.headers['content-type']} != {content_type}"
        return request

    def parse_response(self, method_spec: t.Dict[str, t.Any], response: requests.Response) -> t.Any:
        if response.status_code == 204:
            return "{}"

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
        if "application/json" in response_spec["content"]:
            return response.json()
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

        if any(self.extract_params("cookie", path_spec, method_spec, parameters)):
            raise NotImplementedError(_("Cookie parameters are not implemented."))

        headers = self.extract_params("header", path_spec, method_spec, parameters)

        for name, value in self.extract_params("path", path_spec, method_spec, parameters).items():
            path = path.replace("{" + name + "}", value)

        query_params = self.extract_params("query", path_spec, method_spec, parameters)

        if any(parameters):
            raise OpenAPIError(
                _("Parameter [{names}] not available for {operation_id}.").format(
                    names=", ".join(parameters.keys()), operation_id=operation_id
                )
            )
        url = urljoin(self.base_url, path)

        request: requests.PreparedRequest = self.render_request(
            path_spec,
            method,
            url,
            query_params,
            headers,
            body,
            validate_body=validate_body,
        )

        self.debug_callback(1, f"{operation_id} : {method} {request.url}")
        for key, value in request.headers.items():
            self.debug_callback(2, f"  {key}: {value}")
        if request.body is not None:
            self.debug_callback(3, f"{request.body!r}")
        if self.safe_calls_only and method.upper() not in SAFE_METHODS:
            raise UnsafeCallError(_("Call aborted due to safe mode"))
        try:
            response: requests.Response = self._session.send(request)
        except requests.TooManyRedirects as e:
            assert e.response is not None
            raise OpenAPIError(
                _("Received redirect to '{url}'. Please check your CLI configuration.").format(
                    url=e.response.headers["location"]
                )
            )
        except requests.RequestException as e:
            raise OpenAPIError(str(e))
        self.debug_callback(
            1, _("Response: {status_code}").format(status_code=response.status_code)
        )
        for key, value in response.headers.items():
            self.debug_callback(2, f"  {key}: {value}")
        if response.text:
            self.debug_callback(3, f"{response.text}")
        if "Correlation-ID" in response.headers:
            self._set_correlation_id(response.headers["Correlation-ID"])
        response.raise_for_status()
        return self.parse_response(method_spec, response)
