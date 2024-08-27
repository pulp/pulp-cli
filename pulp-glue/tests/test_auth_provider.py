import pytest

from pulp_glue.common.openapi import AuthProviderBase, OpenAPIError

pytestmark = pytest.mark.glue


SECURITY_SCHEMES = {
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


def test_auth_provider_select_mechanism(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(AuthProviderBase, "basic_auth", lambda *args: "BASIC")
    monkeypatch.setattr(
        AuthProviderBase,
        "oauth2_client_credentials_auth",
        lambda *args: "OAUTH2_CLIENT_CREDENTIALS",
    )

    # Error if no auth scheme is available.
    with pytest.raises(OpenAPIError):
        AuthProviderBase()([], SECURITY_SCHEMES)

    # Error if a nonexisting mechanism is proposed.
    with pytest.raises(KeyError):
        AuthProviderBase()([{"foo": []}], SECURITY_SCHEMES)

    # Succeed without mechanism for an empty proposal.
    assert AuthProviderBase()([{}], SECURITY_SCHEMES) is None

    # Try select a not implemented auth.
    with pytest.raises(OpenAPIError):
        AuthProviderBase()([{"A": []}], SECURITY_SCHEMES)

    # Ignore proposals with multiple mechanisms.
    with pytest.raises(OpenAPIError):
        AuthProviderBase()([{"B": [], "C": []}], SECURITY_SCHEMES)

    # Select Basic auth alone and from multiple.
    assert AuthProviderBase()([{"B": []}], SECURITY_SCHEMES) == "BASIC"
    assert AuthProviderBase()([{"A": []}, {"B": []}], SECURITY_SCHEMES) == "BASIC"

    # Select oauth2 client credentials alone and over basic auth if scopes match.
    assert AuthProviderBase()([{"D": []}], SECURITY_SCHEMES) == "OAUTH2_CLIENT_CREDENTIALS"
    assert (
        AuthProviderBase()([{"B": []}, {"D": []}], SECURITY_SCHEMES) == "OAUTH2_CLIENT_CREDENTIALS"
    )
    assert (
        AuthProviderBase()([{"B": []}, {"D": ["read:pets"]}], SECURITY_SCHEMES)
        == "OAUTH2_CLIENT_CREDENTIALS"
    )
    assert AuthProviderBase()([{"B": []}, {"D": ["read:cattle"]}], SECURITY_SCHEMES) == "BASIC"
