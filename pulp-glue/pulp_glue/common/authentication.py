import click
import json
import requests

from typing import NoReturn
from datetime import datetime, timedelta
from pathlib import Path


class OAuth2Auth(requests.auth.AuthBase):

    def __init__(self, *args, **kwargs):
        self.client_id: str = kwargs.get("username")
        self.client_secret: str = kwargs.get("password")
        self.flow: list = kwargs.get("flow")
        self.token_url: str = self.flow["flows"]["clientCredentials"]["tokenUrl"]
        self.scope: str = [*self.flow["flows"]["clientCredentials"]["scopes"]][0]
        self.token: dict = {}

    def __call__(self, request: requests.PreparedRequest) -> requests.PreparedRequest:
        self.retrieve_local_token()

        access_token = self.token.get("access_token")
        request.headers["Authorization"] = f"Bearer {access_token}"

        request.register_hook("response", self.handle401)

        return request

    def handle401(self, request: requests.PreparedRequest, **kwargs) -> requests.PreparedRequest:
        if request.status_code != 401:
            return request

        self.retrieve_local_token()
        if self.is_token_expired():
            self.retrieve_token()

        request.content
        prep = request.request.copy()

        access_token = self.token.get('access_token')
        prep.headers["Authorization"] = f"Bearer {access_token}"

        _request = request.connection.send(prep, **kwargs)
        _request.history.append(request)
        _request.request = prep

        return _request

    def is_token_expired(self) -> bool:
        if self.token:
            issued_at = datetime.fromisoformat(self.token["issued_at"])
            expires_in = timedelta(seconds=self.token["expires_in"])
            token_timedelta = issued_at + expires_in - timedelta(seconds=5)

            if token_timedelta >= datetime.now():
                return False

        return True

    def store_local_token(self) -> NoReturn:
        TOKEN_LOCATION = (Path(click.utils.get_app_dir("pulp"), "token.json"))
        with Path(TOKEN_LOCATION).open("w") as token_file:
            token = json.dumps(self.token)
            token_file.write(token)

    def retrieve_local_token(self) -> NoReturn:
        TOKEN_LOCATION = (Path(click.utils.get_app_dir("pulp"), "token.json"))
        with Path(TOKEN_LOCATION).open("r") as token_file:
            token_json = token_file.read()
            self.token = json.loads(token_json)

    def retrieve_token(self) -> NoReturn:
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
