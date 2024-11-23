import typing as t

from pulp_glue.common.i18n import get_translation

translation = get_translation(__package__)
_ = translation.gettext


class PulpException(Exception):
    """The base exception `pulp-glue` will emit on expected error paths."""


class PulpEntityNotFound(PulpException):
    """Exception to signify that an entity was not found."""


class PulpHTTPError(PulpException):
    """Exception to indicate HTTP error responses."""

    def __init__(self, msg: str, status_code: int, operation_id: t.Optional[str] = None) -> None:
        super().__init__(msg)
        self.status_code = status_code
        self.operation_id = operation_id


class PulpAuthenticationFailed(PulpHTTPError):
    """Exception to signal a failed authentication."""

    def __init__(self, operation_id: str) -> None:
        super().__init__(
            _("Authentication failed for {operation_id}.").format(operation_id=operation_id),
            401,
            operation_id,
        )


class PulpNotAutorized(PulpHTTPError):
    """Exception to signal an action was not autorized."""

    def __init__(self, operation_id: str) -> None:
        super().__init__(
            _("Operation {operation_id} is not authorized.").format(operation_id=operation_id),
            403,
            operation_id,
        )


class PulpNoWait(Exception):
    """Exception to indicate that a task continues running in the background."""


class NotImplementedFake(NotImplementedError, PulpException):
    """Exception to indicat that a call without a fake version was attempted in fake_mode."""


class OpenAPIError(PulpException):
    """Base Exception for errors related to using the openapi spec."""


class ValidationError(OpenAPIError):
    """Exception raised for failed client side validation of parameters or request bodies."""


class UnsafeCallError(OpenAPIError):
    """Exception raised for POST, PUT, PATCH or DELETE calls with `safe_calls_only=True`."""
