import typing as t
from datetime import datetime, timedelta

import requests


class OAuth2ClientCredentialsAuth(requests.auth.AuthBase):
    """
    This implements the OAuth2 ClientCredentials Grant authentication flow.
    https://datatracker.ietf.org/doc/html/rfc6749#section-4.4
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        token_url: str,
        scopes: t.Optional[t.List[str]] = None,
        verify_ssl: t.Optional[t.Union[str, bool]] = None,
    ):
        self._token_server_auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
        self._token_url = token_url
        self._scopes = scopes
        self._verify_ssl = verify_ssl

        self._access_token: t.Optional[str] = None
        self._expire_at: t.Optional[datetime] = None

    def __call__(self, request: requests.PreparedRequest) -> requests.PreparedRequest:
        if self._expire_at is None or self._expire_at < datetime.now():
            self._retrieve_token()

        assert self._access_token is not None

        request.headers["Authorization"] = f"Bearer {self._access_token}"

        # Call to untyped function "register_hook" in typed context
        request.register_hook("response", self._handle401)  # type: ignore[no-untyped-call]

        return request

    def _handle401(
        self,
        response: requests.Response,
        **kwargs: t.Any,
    ) -> requests.Response:
        if response.status_code != 401:
            return response

        # If we get this far, probably the token is not valid anymore.

        # Try to reach for a new token once.
        self._retrieve_token()

        assert self._access_token is not None

        # Consume content and release the original connection
        # to allow our new request to reuse the same one.
        response.content
        response.close()
        prepared_new_request = response.request.copy()

        prepared_new_request.headers["Authorization"] = f"Bearer {self._access_token}"

        # Avoid to enter into an infinity loop.
        # Call to untyped function "deregister_hook" in typed context
        prepared_new_request.deregister_hook(  # type: ignore[no-untyped-call]
            "response", self._handle401
        )

        # "Response" has no attribute "connection"
        new_response: requests.Response = response.connection.send(prepared_new_request, **kwargs)
        new_response.history.append(response)
        new_response.request = prepared_new_request

        return new_response

    def _retrieve_token(self) -> None:
        data = {
            "grant_type": "client_credentials",
        }

        if self._scopes:
            data["scope"] = " ".join(self._scopes)

        response: requests.Response = requests.post(
            self._token_url,
            data=data,
            auth=self._token_server_auth,
            verify=self._verify_ssl,
        )

        response.raise_for_status()

        token = response.json()
        self._expire_at = datetime.now() + timedelta(seconds=token["expires_in"])
        self._access_token = token["access_token"]
