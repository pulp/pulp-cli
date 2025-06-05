# Supported Authentication Methods

Pulp-CLI support some authentication methods to authenticate against a Pulp instance.
Some very simple and common, like HTTP Basic Auth, and some more complex like OAuth2.

## OAuth2 ClientCredentials grant

!!! warning

    This is an experimental feature. The support of it could change without any major warning.

    For more information, see [RFC6749 section 4.4].

Using this method the pulp-cli can request a token from an Identity Provider using a pair of 
credentials (client_id/client_secret). The token is then sent through using the `Authorization` header.
The issuer URL and the scope of token must be specified by the Pulp server through the OpenAPI scheme definition.

[RFC6749 section 4.4]: https://datatracker.ietf.org/doc/html/rfc6749#section-4.4
