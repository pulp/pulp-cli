# copyright (c) 2020, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

import gettext
import json
import os
import uuid
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlencode, urljoin

import requests
import urllib3

_ = gettext.gettext

SAFE_METHODS = ["GET", "HEAD", "OPTIONS"]


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
    ):
        if not validate_certs:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        self.debug_callback: Callable[[int, str], Any] = debug_callback or (lambda i, x: None)
        self.base_url: str = base_url
        self.doc_path: str = doc_path
        self.safe_calls_only: bool = safe_calls_only

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self._session: requests.Session = requests.session()
        if username and password:
            if cert or key:
                raise OpenAPIError("Cannot use both username/password and cert auth.")
            self._session.auth = (username, password)
        elif username:
            raise OpenAPIError("Password is required if username is set.")
        elif password:
            raise OpenAPIError("Username is required if password is set.")
        elif cert and key:
            self._session.cert = (cert, key)
        elif cert:
            self._session.cert = cert
        elif key:
            raise OpenAPIError("Cert is required if key is set.")
        self._session.headers.update(headers)
        self._session.verify = validate_certs
        self._session.max_redirects = 0

        self.load_api(refresh_cache=refresh_cache)

    def load_api(self, refresh_cache: bool = False) -> None:
        # TODO: Find a way to invalidate caches on upstream change
        xdg_cache_home: str = os.environ.get("XDG_CACHE_HOME") or "~/.cache"
        apidoc_cache: str = os.path.join(
            os.path.expanduser(xdg_cache_home),
            "squeezer",
            self.base_url.replace(":", "_").replace("/", "_"),
            "api.json",
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
            raise OpenAPIError("Unknown schema version")
        self.operations: Dict[str, Any] = {
            method_entry["operationId"]: (method, path)
            for path, path_entry in self.api_spec["paths"].items()
            for method, method_entry in path_entry.items()
            if method in {"get", "put", "post", "delete", "options", "head", "patch", "trace"}
        }

    def _download_api(self) -> bytes:
        try:
            r: requests.Response = self._session.get(urljoin(self.base_url, self.doc_path))
        except requests.exceptions.ConnectionError as e:
            raise OpenAPIError(str(e))
        r.raise_for_status()
        return r.content

    def extract_params(
        self,
        param_type: str,
        path_spec: Dict[str, Any],
        method_spec: Dict[str, Any],
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
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
        result: Dict[str, Any] = {}
        for name in list(params.keys()):
            if name in param_spec:
                param_spec.pop(name)
                result[name] = params.pop(name)
        remaining_required = [
            item["name"] for item in param_spec.values() if item.get("required", False)
        ]
        if any(remaining_required):
            raise OpenAPIError(
                "Required parameters [{0}] missing for {1}.".format(
                    ", ".join(remaining_required), param_type
                )
            )
        return result

    def render_body(
        self,
        path_spec: Dict[str, Any],
        method_spec: Dict[str, Any],
        headers: Dict[str, str],
        body: Optional[Dict[str, Any]] = None,
        uploads: Optional[Dict[str, bytes]] = None,
    ) -> Optional[bytes]:
        if not (body or uploads):
            return None
        content_types: List[str] = list(method_spec["requestBody"]["content"].keys())
        if uploads:
            body = body or {}
            if any(
                (content_type.startswith("multipart/form-data") for content_type in content_types)
            ):
                boundary: str = uuid.uuid4().hex
                part_boundary: bytes = b"--" + str.encode(boundary)

                form: List[bytes] = []
                for key, value in body.items():
                    b_key: bytes = str.encode(key)
                    form.extend(
                        [
                            part_boundary,
                            b'Content-Disposition: form-data; name="%s"' % b_key,
                            b"",
                            str.encode(value),
                        ]
                    )
                for key, file_data in uploads.items():
                    b_key = str.encode(key)
                    form.extend(
                        [
                            part_boundary,
                            b'Content-Disposition: file; name="%s"; filename="%s"' % (b_key, b_key),
                            b"Content-Type: application/octet-stream",
                            b"",
                            file_data,
                        ]
                    )
                form.append(part_boundary + b"--")
                data = b"\r\n".join(form)
                headers["Content-Type"] = "multipart/form-data; boundary={boundary}".format(
                    boundary=boundary
                )
            else:
                raise OpenAPIError("No suitable content type for file upload specified.")
        elif body:
            if any((content_type.startswith("application/json") for content_type in content_types)):
                data = str.encode(json.dumps(body))
                headers["Content-Type"] = "application/json"
            elif any(
                (
                    content_type.startswith("application/x-www-form-urlencoded")
                    for content_type in content_types
                )
            ):
                data = str.encode(urlencode(body))
                headers["Content-Type"] = "application/x-www-form-urlencoded"
            else:
                raise OpenAPIError("No suitable content type for request specified.")
        headers["Content-Length"] = str(len(data))
        return data

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
        uploads: Optional[Dict[str, bytes]] = None,
    ) -> Any:
        method, path = self.operations[operation_id]
        path_spec = self.api_spec["paths"][path]
        method_spec = path_spec[method]

        if parameters is None:
            parameters = {}
        else:
            parameters = parameters.copy()

        if any(self.extract_params("cookie", path_spec, method_spec, parameters)):
            raise NotImplementedError("Cookie parameters are not implemented.")

        headers = self.extract_params("header", path_spec, method_spec, parameters)

        for name, value in self.extract_params("path", path_spec, method_spec, parameters).items():
            path = path.replace("{" + name + "}", value)

        query_string = urlencode(
            self.extract_params("query", path_spec, method_spec, parameters), doseq=True
        )

        if any(parameters):
            raise OpenAPIError(
                "Parameter [{names}] not available for {operation_id}.".format(
                    names=", ".join(parameters.keys()), operation_id=operation_id
                )
            )
        url = urljoin(self.base_url, path)
        if query_string:
            url += "?" + query_string

        data: Optional[bytes] = self.render_body(path_spec, method_spec, headers, body, uploads)

        self.debug_callback(1, f"{method} {url}")
        for key, value in headers.items():
            self.debug_callback(2, f"  {key}: {value}")
        if data:
            self.debug_callback(2, f"{data!r}")
        if self.safe_calls_only and method.upper() not in SAFE_METHODS:
            raise OpenAPIError("Call aborted due to safe mode")
        try:
            response: requests.Response = self._session.request(
                method, url, data=data, headers=headers
            )
        except requests.ConnectionError as e:
            raise OpenAPIError(str(e))
        except requests.exceptions.TooManyRedirects as e:
            raise OpenAPIError(
                _("Received redirect to '{url}'. Please check your CLI configuration.").format(
                    url=e.response.headers["location"]
                )
            )
        self.debug_callback(1, f"Response: {response.status_code}")
        if response.text:
            self.debug_callback(3, f"{response.text}")
        response.raise_for_status()
        return self.parse_response(method_spec, response)
