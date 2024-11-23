import typing as t

import pytest
from requests.auth import AuthBase

from pulp_glue.common.exceptions import OpenAPIError
from pulp_glue.common.openapi import AuthProviderBase

pytestmark = pytest.mark.glue


SECURITY_SCHEMES: t.Dict[str, dict[str, t.Any]] = {
    "A": {"type": "http", "scheme": "bearer"},
    "B": {"type": "http", "scheme": "basic"},
    "C": {
        "type": "oauth2",
        "flows": {
            "implicit": {
                "authorizationUrl": "https://example.com/api/oauth/dialog",
                "scopes": {
                    "write:pets": "modify pets in your account",
                    "read:pets": "read your pets",
                },
            },
            "authorizationCode": {
                "authorizationUrl": "https://example.com/api/oauth/dialog",
                "tokenUrl": "https://example.com/api/oauth/token",
                "scopes": {
                    "write:pets": "modify pets in your account",
                    "read:pets": "read your pets",
                },
            },
        },
    },
    "D": {
        "type": "oauth2",
        "flows": {
            "implicit": {
                "authorizationUrl": "https://example.com/api/oauth/dialog",
                "scopes": {
                    "write:pets": "modify pets in your account",
                    "read:pets": "read your pets",
                },
            },
            "clientCredentials": {
                "tokenUrl": "https://example.com/api/oauth/token",
                "scopes": {
                    "write:pets": "modify pets in your account",
                    "read:pets": "read your pets",
                },
            },
        },
    },
}


class MockBasicAuth(AuthBase):
    pass


class MockOAuth2CCAuth(AuthBase):
    pass


def test_auth_provider_select_mechanism(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(AuthProviderBase, "basic_auth", lambda *args: MockBasicAuth())
    monkeypatch.setattr(
        AuthProviderBase,
        "oauth2_client_credentials_auth",
        lambda *args: MockOAuth2CCAuth(),
    )
    provider = AuthProviderBase()

    # Error if no auth scheme is available.
    with pytest.raises(OpenAPIError):
        provider([], SECURITY_SCHEMES)

    # Error if a nonexisting mechanism is proposed.
    with pytest.raises(KeyError):
        provider([{"foo": []}], SECURITY_SCHEMES)

    # Succeed without mechanism for an empty proposal.
    assert provider([{}], SECURITY_SCHEMES) is None

    # Try select a not implemented auth.
    with pytest.raises(OpenAPIError):
        provider([{"A": []}], SECURITY_SCHEMES)

    # Ignore proposals with multiple mechanisms.
    with pytest.raises(OpenAPIError):
        provider([{"B": [], "C": []}], SECURITY_SCHEMES)

    # Select Basic auth alone and from multiple.
    assert isinstance(provider([{"B": []}], SECURITY_SCHEMES), MockBasicAuth)
    assert isinstance(provider([{"A": []}, {"B": []}], SECURITY_SCHEMES), MockBasicAuth)

    # Select oauth2 client credentials alone and over basic auth if scopes match.
    assert isinstance(provider([{"D": []}], SECURITY_SCHEMES), MockOAuth2CCAuth)
    assert isinstance(provider([{"B": []}, {"D": []}], SECURITY_SCHEMES), MockOAuth2CCAuth)
    assert isinstance(
        provider([{"B": []}, {"D": ["read:pets"]}], SECURITY_SCHEMES), MockOAuth2CCAuth
    )
    # Fall back to basic if scope does not match.
    assert isinstance(
        provider([{"B": []}, {"D": ["read:cattle"]}], SECURITY_SCHEMES), MockBasicAuth
    )
