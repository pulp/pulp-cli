# copyright (c) 2020, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

import base64
import datetime
import json
import os
from io import BufferedReader
from typing import IO, Any, Callable, Dict, List, Mapping, Optional, Tuple, Union
from urllib.parse import urljoin

import requests
import urllib3

from pulpcore.cli.common.i18n import get_translation

translation = get_translation(__name__)
_ = translation.gettext

UploadType = Union[bytes, IO[bytes]]
UploadsMap = Mapping[str, UploadType]

SAFE_METHODS = ["GET", "HEAD", "OPTIONS"]
ISO_DATE_FORMAT = "%Y-%m-%d"
ISO_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


class OpenAPIError(Exception):
    pass


class OpenAPI:
    def __init__(
        self,
        base_url: str,
        doc_path: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        cert: Optional[str] = None,
        key: Optional[str] = None,
        validate_certs: bool = True,
        refresh_cache: bool = False,
        safe_calls_only: bool = False,
        debug_callback: Optional[Callable[[int, str], Any]] = None,
        user_agent: Optional[str] = None,
        cid: Optional[str] = None,
    ):
        if not validate_certs:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        self.debug_callback: Callable[[int, str], Any] = debug_callback or (lambda i, x: None)
        self.base_url: str = base_url
        self.doc_path: str = doc_path
        self.safe_calls_only: bool = safe_calls_only

        self._session: requests.Session = requests.session()
        if username and password:
            if cert or key:
                raise OpenAPIError(_("Cannot use both username/password and cert auth."))
            self._session.auth = (username, password)
        elif username:
            raise OpenAPIError(_("Password is required if username is set."))
        elif password:
            raise OpenAPIError(_("Username is required if password is set."))
        elif cert and key:
            self._session.cert = (cert, key)
        elif cert:
            self._session.cert = cert
        elif key:
            raise OpenAPIError(_("Cert is required if key is set."))
        self._session.headers.update(
            {
                "User-Agent": user_agent or "Pulp-CLI openapi parser",
                "Accept": "application/json",
            }
        )
        if cid:
            self._session.headers["Correlation-Id"] = cid
        self._session.max_redirects = 0

        verify: Optional[Union[bool, str]] = (
            os.environ.get("PULP_CA_BUNDLE") if validate_certs is not False else False
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
        self.api_spec: Dict[str, Any] = json.loads(data)
        if self.api_spec.get("openapi", "").startswith("3."):
            self.openapi_version: int = 3
        else:
            raise OpenAPIError(_("Unknown schema version"))
        self.operations: Dict[str, Any] = {
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

    def extract_params(
        self,
        param_in: str,
        path_spec: Dict[str, Any],
        method_spec: Dict[str, Any],
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
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
        result: Dict[str, Any] = {}
        for name in list(params.keys()):
            if name in param_specs:
                param = params.pop(name)
                param_spec = param_specs.pop(name)
                param_schema = param_spec.get("schema")
                if param_schema:
                    param = self.validate_schema(param_schema, name, param)

                if isinstance(param, List):
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

    def validate_schema(self, schema: Any, name: str, value: Any) -> Any:
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

        schema_type = schema.get("type", "string")
        if schema_type == "object":
            value = self.validate_object(schema, name, value)
        elif schema_type == "array":
            value = self.validate_array(schema, name, value)
        elif schema_type == "string":
            value = self.validate_string(schema, name, value)
        elif schema_type == "integer":
            value = self.validate_integer(schema, name, value)
        elif schema_type == "number":
            value = self.validate_number(schema, name, value)
        elif schema_type == "boolean":
            if not isinstance(value, bool):
                raise OpenAPIError(_("'{name}' is expected to be a boolean.").format(name=name))
        # TODO: Add more types here.
        else:
            raise OpenAPIError(
                _("Type `{schema_type}` is not implemented yet.").format(schema_type=schema_type)
            )
        return value

    def validate_object(self, schema: Any, name: str, value: Any) -> Dict[str, Any]:
        if not isinstance(value, Dict):
            raise OpenAPIError(_("'{name}' is expected to be an object.").format(name=name))
        properties = schema.get("properties")
        if properties is not None:
            for property_name, property_value in value.items():
                property_schema = properties.get(property_name)
                if not property_schema:
                    raise OpenAPIError(
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
                raise OpenAPIError(
                    _("Required properties(s) '{missing_properties}' of '{name}' missing.").format(
                        name=name, missing_properties=missing_properties
                    )
                )
        return value

    def validate_array(self, schema: Any, name: str, value: Any) -> List[Any]:
        if not isinstance(value, List):
            raise OpenAPIError(_("'{name}' is expected to be a list.").format(name=name))
        item_schema = schema["items"]
        return [self.validate_schema(item_schema, name, item) for item in value]

    def validate_string(self, schema: Any, name: str, value: Any) -> Union[str, UploadType]:
        schema_format = schema.get("format")
        if schema_format == "date":
            if not isinstance(value, datetime.date):
                raise OpenAPIError(_("'{name}' is expected to be a date.").format(name=name))
            return value.strftime(ISO_DATE_FORMAT)
        elif schema_format == "date-time":
            if not isinstance(value, datetime.datetime):
                raise OpenAPIError(_("'{name}' is expected to be a datetime.").format(name=name))
            return value.strftime(ISO_DATETIME_FORMAT)
        elif schema_format == "bytes":
            if not isinstance(value, bytes):
                raise OpenAPIError(_("'{name}' is expected to be bytes.").format(name=name))
            return base64.b64encode(value)
        elif schema_format == "binary":
            if not isinstance(value, (bytes, BufferedReader)):
                raise OpenAPIError(_("'{name}' is expected to be binary.").format(name=name))
            return value
        else:
            if not isinstance(value, str):
                raise OpenAPIError(_("'{name}' is expected to be a string.").format(name=name))
            return value

    def validate_integer(self, schema: Any, name: str, value: Any) -> int:
        if not isinstance(value, int):
            raise OpenAPIError(_("'{name}' is expected to be an integer.").format(name=name))
        minimum = schema.get("minimum")
        if minimum is not None and value < minimum:
            raise OpenAPIError(_("'{name}' is violating the minimum constraint").format(name=name))
        maximum = schema.get("maximum")
        if maximum is not None and value > maximum:
            raise OpenAPIError(_("'{name}' is violating the maximum constraint").format(name=name))
        return value

    def validate_number(self, schema: Any, name: str, value: Any) -> float:
        # https://swagger.io/specification/#data-types describes float and double.
        # Python does not distinguish them.
        if not isinstance(value, float):
            raise OpenAPIError(_("'{name}' is expected to be an integer.").format(name=name))
        return value

    def render_request(
        self,
        path_spec: Dict[str, Any],
        method: str,
        url: str,
        params: Dict[str, Any],
        headers: Dict[str, str],
        body: Optional[Dict[str, Any]] = None,
        uploads: Optional[UploadsMap] = None,
        validate_body: bool = True,
    ) -> requests.PreparedRequest:
        method_spec = path_spec[method]
        try:
            content_types: List[str] = (
                list(method_spec["requestBody"]["content"].keys()) if body or uploads else []
            )
        except KeyError:
            raise OpenAPIError(_("This operation does not expect a request body."))

        content_type: Optional[str] = None
        data: Optional[Dict[str, Any]] = None
        json: Optional[Dict[str, Any]] = None
        files: Optional[List[Tuple[str, Tuple[str, UploadType, str]]]] = None

        if uploads:
            content_type = next(
                (
                    content_type
                    for content_type in content_types
                    if content_type.startswith("multipart/form-data")
                ),
                None,
            )
            if content_type:
                data = body
                files = [
                    (key, (key, file_data, "application/octet-stream"))
                    for key, file_data in uploads.items()
                ]
            else:
                raise OpenAPIError(_("No suitable content type for file upload specified."))
        elif body:
            content_type = next(
                (
                    content_type
                    for content_type in content_types
                    if content_type.startswith("application/json")
                ),
                None,
            )
            if content_type:
                json = body
            else:
                content_type = next(
                    (
                        content_type
                        for content_type in content_types
                        if content_type.startswith("application/x-www-form-urlencoded")
                    ),
                    None,
                )
                if content_type:
                    data = body
                else:
                    raise OpenAPIError(_("No suitable content type for request specified."))
        if content_type and validate_body:
            body = body or {}
            if uploads:
                # Add uploads for validation (CRAZY HACK)
                body.update(uploads)
            # This only works, because data or json will be the same object as body...
            body = self.validate_schema(
                method_spec["requestBody"]["content"][content_type]["schema"],
                "body",
                body,
            )
            assert isinstance(body, Dict)
            if uploads:
                # Remove uploads again
                for key in uploads:
                    body.pop(key)
        return self._session.prepare_request(
            requests.Request(
                method, url, params=params, headers=headers, data=data, json=json, files=files
            )
        )

    def parse_response(self, method_spec: Dict[str, Any], response: requests.Response) -> Any:
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
        parameters: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
        uploads: Optional[UploadsMap] = None,
        validate_body: bool = True,
    ) -> Any:
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
            uploads,
            validate_body=validate_body,
        )

        self.debug_callback(1, f"{operation_id} : {method} {request.url}")
        for key, value in request.headers.items():
            self.debug_callback(2, f"  {key}: {value}")
        if request.body is not None:
            self.debug_callback(3, f"{request.body!r}")
        if self.safe_calls_only and method.upper() not in SAFE_METHODS:
            raise OpenAPIError(_("Call aborted due to safe mode"))
        try:
            response: requests.Response = self._session.send(request)
        except requests.TooManyRedirects as e:
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
