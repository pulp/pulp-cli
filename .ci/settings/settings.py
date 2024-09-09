import os

ALLOWED_EXPORT_PATHS = ["/tmp"]
ANALYTICS = False
ALLOWED_CONTENT_CHECKSUMS = ["sha1", "sha256", "sha512"]

if os.environ.get("PULP_HTTPS", "false").lower() == "true":
    AUTHENTICATION_BACKENDS = "@merge django.contrib.auth.backends.RemoteUserBackend"
    MIDDLEWARE = "@merge django.contrib.auth.middleware.RemoteUserMiddleware"
    REST_FRAMEWORK__DEFAULT_AUTHENTICATION_CLASSES = (
        "@merge pulpcore.app.authentication.PulpRemoteUserAuthentication"
    )
    REMOTE_USER_ENVIRON_NAME = "HTTP_REMOTEUSER"

if os.environ.get("PULP_OAUTH2", "false").lower() == "true":
    assert os.environ.get("PULP_HTTPS", "false").lower() == "true"

    def PulpCliFakeOauth2Authentication(*args, **kwargs):
        # We need to lazy load this.
        # Otherwise views may be instanciated, before this configuration is merged.

        from django.contrib.auth import authenticate
        from drf_spectacular.extensions import OpenApiAuthenticationExtension
        from rest_framework.authentication import BaseAuthentication

        class _PulpCliFakeOauth2Authentication(BaseAuthentication):
            def authenticate(self, request):
                auth_header = request.META.get("HTTP_AUTHORIZATION")
                if auth_header == "Bearer DEADBEEF":
                    return authenticate(request, remote_user="admin"), None
                else:
                    return None

            def authenticate_header(self, request):
                return 'Bearer realm="Pulp"'

        class PulpCliFakeOauth2AuthenticationScheme(OpenApiAuthenticationExtension):
            target_class = _PulpCliFakeOauth2Authentication
            name = "PulpCliFakeOauth2"

            def get_security_definition(self, auto_schema):
                return {
                    "type": "oauth2",
                    "flows": {
                        "clientCredentials": {
                            "tokenUrl": "https://localhost:8080/oauth2token/",
                            "scopes": {"api.console": "grant_access_to_pulp"},
                        },
                    },
                }

        return _PulpCliFakeOauth2Authentication(*args, **kwargs)

    PULP_CLI_FAKE_OAUTH2_AUTHENTICATION = PulpCliFakeOauth2Authentication

    REST_FRAMEWORK__DEFAULT_AUTHENTICATION_CLASSES = (
        "@merge pulpcore.app.settings.PULP_CLI_FAKE_OAUTH2_AUTHENTICATION"
    )
