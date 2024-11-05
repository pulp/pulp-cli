import typing as t


class AuthProviderBase:
    """
    Base class for auth providers.

    This abstract base class will analyze the authentication proposals of the openapi specs.
    Different authentication schemes can be implemented in subclasses.
    """

    def can_complete_http_basic(self) -> bool:
        return False

    def can_complete_mutualTLS(self) -> bool:
        return False

    def can_complete_oauth2_client_credentials(self, scopes: list[str]) -> bool:
        return False

    def can_complete_scheme(self, scheme: dict[str, t.Any], scopes: list[str]) -> bool:
        if scheme["type"] == "http":
            if scheme["scheme"] == "basic":
                return self.can_complete_http_basic()
        elif scheme["type"] == "mutualTLS":
            return self.can_complete_mutualTLS()
        elif scheme["type"] == "oauth2":
            for flow_name, flow in scheme["flows"].items():
                if flow_name == "clientCredentials" and self.can_complete_oauth2_client_credentials(
                    flow["scopes"]
                ):
                    return True
        return False

    def can_complete(
        self, proposal: dict[str, list[str]], security_schemes: dict[str, dict[str, t.Any]]
    ) -> bool:
        for name, scopes in proposal.items():
            scheme = security_schemes.get(name)
            if scheme is None or not self.can_complete_scheme(scheme, scopes):
                return False
        # This covers the case where `[]` allows for no auth at all.
        return True

    async def auth_success_hook(
        self, proposal: dict[str, list[str]], security_schemes: dict[str, dict[str, t.Any]]
    ) -> None:
        pass

    async def auth_failure_hook(
        self, proposal: dict[str, list[str]], security_schemes: dict[str, dict[str, t.Any]]
    ) -> None:
        pass

    async def http_basic_credentials(self) -> tuple[bytes, bytes]:
        raise NotImplementedError()

    async def oauth2_client_credentials(self) -> tuple[bytes, bytes]:
        raise NotImplementedError()

    def tls_credentials(self) -> tuple[str, str | None]:
        raise NotImplementedError()


class BasicAuthProvider(AuthProviderBase):
    """
    AuthProvider providing basic auth with fixed `username`, `password`.
    """

    def __init__(self, username: t.AnyStr, password: t.AnyStr):
        super().__init__()
        self.username: bytes = username.encode("latin1") if isinstance(username, str) else username
        self.password: bytes = password.encode("latin1") if isinstance(password, str) else password

    def can_complete_http_basic(self) -> bool:
        return True

    async def http_basic_credentials(self) -> tuple[bytes, bytes]:
        return self.username, self.password


class GlueAuthProvider(AuthProviderBase):
    """
    AuthProvider allowing to be used with prepared credentials.
    """

    def __init__(
        self,
        *,
        username: t.AnyStr | None = None,
        password: t.AnyStr | None = None,
        client_id: t.AnyStr | None = None,
        client_secret: t.AnyStr | None = None,
        cert: str | None = None,
        key: str | None = None,
    ):
        super().__init__()
        self.username: bytes | None = None
        self.password: bytes | None = None
        self.client_id: bytes | None = None
        self.client_secret: bytes | None = None
        self.cert: str | None = cert
        self.key: str | None = key

        if username is not None:
            assert password is not None
            self.username = username.encode("latin1") if isinstance(username, str) else username
            self.password = password.encode("latin1") if isinstance(password, str) else password
        if client_id is not None:
            assert client_secret is not None
            self.client_id = client_id.encode("latin1") if isinstance(client_id, str) else client_id
            self.client_secret = (
                client_secret.encode("latin1") if isinstance(client_secret, str) else client_secret
            )

        if cert is None and key is not None:
            raise RuntimeError("Key can only be used together with a cert.")

    def can_complete_http_basic(self) -> bool:
        return self.username is not None

    def can_complete_oauth2_client_credentials(self, scopes: list[str]) -> bool:
        return self.client_id is not None

    def can_complete_mutualTLS(self) -> bool:
        return self.cert is not None

    async def http_basic_credentials(self) -> tuple[bytes, bytes]:
        assert self.username is not None
        assert self.password is not None
        return self.username, self.password

    async def oauth2_client_credentials(self) -> tuple[bytes, bytes]:
        assert self.client_id is not None
        assert self.client_secret is not None
        return self.client_id, self.client_secret

    def tls_credentials(self) -> tuple[str, str | None]:
        assert self.cert is not None
        return (self.cert, self.key)
