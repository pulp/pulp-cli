import asyncio
import typing as t

import pytest

from pulp_glue.common.authentication import (
    AuthProviderBase,
    BasicAuthProvider,
    GlueAuthProvider,
)

pytestmark = pytest.mark.glue


SECURITY_SCHEMES: dict[str, dict[str, t.Any]] = {
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
    "E": {"type": "mutualTLS"},
}


class TestBasicAuthProvider:
    @pytest.fixture(scope="class")
    def provider(self) -> AuthProviderBase:
        return BasicAuthProvider(username="user1", password="password1")

    def test_can_complete_basic(self, provider: AuthProviderBase) -> None:
        assert provider.can_complete_http_basic()

    def test_provides_username_and_password(self, provider: AuthProviderBase) -> None:
        assert asyncio.run(provider.http_basic_credentials()) == (
            b"user1",
            b"password1",
        )

    def test_cannot_complete_mutualTLS(self, provider: AuthProviderBase) -> None:
        assert not provider.can_complete_mutualTLS()

    def test_can_complete_basic_proposal(self, provider: AuthProviderBase) -> None:
        assert provider.can_complete({"B": []}, security_schemes=SECURITY_SCHEMES)

    def test_cannot_complete_bearer_proposal(self, provider: AuthProviderBase) -> None:
        assert not provider.can_complete({"A": []}, security_schemes=SECURITY_SCHEMES)

    def test_cannot_complete_combined_proposal(self, provider: AuthProviderBase) -> None:
        assert not provider.can_complete({"A": [], "B": []}, security_schemes=SECURITY_SCHEMES)


class TestGlueAuthProvider:
    def test_empty_provider_cannot_complete(self) -> None:
        provider = GlueAuthProvider()
        assert provider.can_complete_http_basic() is False
        assert provider.can_complete_oauth2_client_credentials([]) is False
        assert provider.can_complete_mutualTLS() is False

    def test_username_needs_password(self) -> None:
        with pytest.raises(AssertionError):
            GlueAuthProvider(username="user1")

    def test_can_complete_basic_auth_and_provide_credentials(self) -> None:
        provider = GlueAuthProvider(username="user1", password="secret1")
        assert provider.can_complete_http_basic() is True
        assert asyncio.run(provider.http_basic_credentials()) == (b"user1", b"secret1")

    def test_client_id_needs_client_secret(self) -> None:
        with pytest.raises(AssertionError):
            GlueAuthProvider(client_id="client1")

    def test_can_complete_oauth2_client_credentials_and_provide_them(self) -> None:
        provider = GlueAuthProvider(client_id="client1", client_secret="secret1")
        assert provider.can_complete_oauth2_client_credentials([]) is True
        assert asyncio.run(provider.oauth2_client_credentials()) == (
            b"client1",
            b"secret1",
        )

    def test_can_complete_mutualTLS_and_provide_cert(self) -> None:
        provider = GlueAuthProvider(cert="FAKECERTIFICATE")
        assert provider.can_complete_mutualTLS() is True
        assert provider.tls_credentials() == ("FAKECERTIFICATE", None)
