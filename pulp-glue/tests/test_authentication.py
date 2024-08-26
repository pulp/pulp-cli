import typing as t

import pytest

from pulp_glue.common.authentication import OAuth2ClientCredentialsAuth

pytestmark = pytest.mark.glue


def test_sending_no_scope_when_empty(monkeypatch: pytest.MonkeyPatch) -> None:

    class OAuth2MockResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"expires_in": 1, "access_token": "aaa"}

    def _requests_post_mocked(url: str, data: t.Dict[str, t.Any]):
        assert "scope" not in data
        return OAuth2MockResponse()

    monkeypatch.setattr("requests.post", _requests_post_mocked)

    OAuth2ClientCredentialsAuth(token_url="", client_id="", client_secret="").retrieve_token()

    OAuth2ClientCredentialsAuth(
        token_url="", client_id="", client_secret="", scopes=[]
    ).retrieve_token()
