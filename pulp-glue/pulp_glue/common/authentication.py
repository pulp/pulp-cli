import json
import typing as t
from datetime import datetime, timedelta
from pathlib import Path

import click
import requests


class OAuth2Auth(requests.auth.AuthBase):

    def __init__(self, *args: t.List[t.Any], **kwargs: t.Dict[t.Any, t.Any]):
        self.client_id = kwargs.get("username")
        self.client_secret = kwargs.get("password")
        self.flow: t.Dict[t.Any, t.Any] = kwargs["flow"]
        self.token_url = self.flow["flows"]["clientCredentials"]["tokenUrl"]
        self.scope = [*self.flow["flows"]["clientCredentials"]["scopes"]][0]
        self.token: t.Dict[t.Any, t.Any] = {}

    def __call__(self, request: requests.PreparedRequest) -> requests.PreparedRequest:
        self.retrieve_local_token()

        access_token = self.token.get("access_token")
        request.headers["Authorization"] = f"Bearer {access_token}"

        request.register_hook("response", self.handle401)  # type: ignore

        return request

    def handle401(
        self, response: requests.Response, **kwargs: t.Dict[t.Any, t.Any]
    ) -> requests.Response:
        if response.status_code != 401:
            return response

        self.retrieve_local_token()
        if self.is_token_expired():
            self.retrieve_token()

        response.content
        prep = response.request.copy()

        access_token = self.token.get("access_token")
        prep.headers["Authorization"] = f"Bearer {access_token}"

        _response: requests.Response = response.connection.send(prep, **kwargs)  # type: ignore
        _response.history.append(response)
        _response.request = prep

        return _response

    def is_token_expired(self) -> bool:
        if self.token:
            issued_at = datetime.fromisoformat(self.token["issued_at"])
            expires_in = timedelta(seconds=self.token["expires_in"])
            token_timedelta = issued_at + expires_in - timedelta(seconds=5)

            if token_timedelta >= datetime.now():
                return False

        return True

    def store_local_token(self) -> None:
        TOKEN_LOCATION = Path(click.utils.get_app_dir("pulp"), "token.json")
        with Path(TOKEN_LOCATION).open("w") as token_file:
            token = json.dumps(self.token)
            token_file.write(token)

    def retrieve_local_token(self) -> None:
        token_file = Path(click.utils.get_app_dir("pulp"), "token.json")
        if token_file.exists():
            with token_file.open("r") as tf:
                token_json = tf.read()
                self.token = json.loads(token_json)

    def retrieve_token(self) -> None:
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": self.scope,
            "grant_type": "client_credentials",
        }

        response: requests.Response = requests.post(self.token_url, data=data)

        self.token = response.json() if response.status_code == 200 else None
        self.token["issued_at"] = datetime.now().isoformat()
        self.store_local_token()
