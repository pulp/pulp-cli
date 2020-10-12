# -*- coding: utf-8 -*-

# copyright (c) 2020, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

import json
import os
import uuid
import requests
from urllib.parse import urlencode, urljoin
import urllib3


class OpenAPI:
    def __init__(
        self,
        base_url,
        doc_path,
        username=None,
        password=None,
        validate_certs=True,
        refresh_cache=False,
    ):
        if not validate_certs:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        self.base_url = base_url
        self.doc_path = doc_path

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self._session = requests.session()
        if username and password:
            self._session.auth = (username, password)
        elif username:
            raise Exception("Password is required if username is set.")
        elif password:
            raise Exception("Username is required if password is set.")
        self._session.headers.update(headers)
        self._session.verify = validate_certs

        self.load_api(refresh_cache=refresh_cache)

    def load_api(self, refresh_cache=False):
        # TODO: Find a way to invalidate caches on upstream change
        xdg_cache_home = os.environ.get("XDG_CACHE_HOME") or "~/.cache"
        apidoc_cache = os.path.join(
            os.path.expanduser(xdg_cache_home),
            "squeezer",
            self.base_url.replace(":", "_").replace("/", "_"),
            "api.json",
        )
        try:
            if refresh_cache:
                raise IOError()
            with open(apidoc_cache) as f:
                data = f.read()
            self._parse_api(data)
        except Exception:
            # Try again with a freshly downloaded version
            data = self._download_api()
            self._parse_api(data)
            # Write to cache as it seems to be valid
            os.makedirs(os.path.dirname(apidoc_cache), exist_ok=True)
            with open(apidoc_cache, "wb") as f:
                f.write(data)

    def _parse_api(self, data):
        self.api_spec = json.loads(data)
        if self.api_spec.get("openapi", "").startswith("3."):
            self.openapi_version = 3
        else:
            raise NotImplementedError("Unknown schema version")
        self.operations = {
            method_entry["operationId"]: (method, path)
            for path, path_entry in self.api_spec["paths"].items()
            for method, method_entry in path_entry.items()
            if method in {"get", "put", "post", "delete", "options", "head", "patch", "trace"}
        }

    def _download_api(self):
        r = self._session.get(urljoin(self.base_url, self.doc_path))
        r.raise_for_status()
        return r.content

    def extract_params(self, param_type, path_spec, method_spec, params):
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
        result = {}
        for name in list(params.keys()):
            if name in param_spec:
                param_spec.pop(name)
                result[name] = params.pop(name)
        remaining_required = [
            item["name"] for item in param_spec.values() if item.get("required", False)
        ]
        if any(remaining_required):
            raise Exception(
                "Required parameters [{0}] missing for {1}.".format(
                    ", ".join(remaining_required), param_type
                )
            )
        return result

    def render_body(self, path_spec, method_spec, headers, body=None, uploads=None):
        if not (body or uploads):
            return None
        content_types = list(method_spec["requestBody"]["content"].keys())
        if uploads:
            body = body or {}
            if any(
                (content_type.startswith("multipart/form-data") for content_type in content_types)
            ):
                boundary = uuid.uuid4().hex
                part_boundary = b"--" + str.encode(boundary)

                form = []
                for key, value in body.items():
                    b_key = str.encode(key)
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
                raise Exception("No suitable content type for file upload specified.")
        else:
            if any((content_type.startswith("application/json") for content_type in content_types)):
                data = json.dumps(body)
                headers["Content-Type"] = "application/json"
            elif any(
                (
                    content_type.startswith("application/x-www-form-urlencoded")
                    for content_type in content_types
                )
            ):
                data = urlencode(body)
                headers["Content-Type"] = "application/x-www-form-urlencoded"
            else:
                raise Exception("No suitable content type for file upload specified.")
        headers["Content-Length"] = str(len(data))
        return data

    def parse_response(self, method_spec, response):
        if response.status_code == 204:
            return "{}"

        try:
            response_spec = method_spec["responses"][str(response.status_code)]
        except KeyError:
            # Fallback 201 -> 200
            response_spec = method_spec["responses"][str(100 * int(response.status_code / 100))]
        if "application/json" in response_spec["content"]:
            return response.json()
        return None

    def call(self, operation_id, parameters=None, body=None, uploads=None):
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
            raise Exception(
                "Parameter [{names}] not available for {operation_id}.".format(
                    names=", ".join(parameters.keys()), operation_id=operation_id
                )
            )
        url = urljoin(self.base_url, path)
        if query_string:
            url += "?" + query_string

        data = self.render_body(path_spec, method_spec, headers, body, uploads)

        response = self._session.request(method, url, data=data, headers=headers)
        response.raise_for_status()
        return self.parse_response(method_spec, response)
