"""Exception hierarchy for the query_tableau_data_py package."""

from typing import Any


class TableauError(Exception):
    """Base for all SDK errors.

    Carries the HTTP status code, raw response body, and parsed Tableau
    error fields so agents can reference official Tableau documentation.
    """

    def __init__(
        self,
        *,
        status_code: int | None = None,
        response_body: bytes = b"",
        response_headers: dict[str, str] | None = None,
        tableau_error_code: str | None = None,
        tableau_error_message: str | None = None,
        context: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        self.status_code = status_code
        self.response_body = response_body
        self.response_headers = response_headers or {}
        self.tableau_error_code = tableau_error_code
        self.tableau_error_message = tableau_error_message
        self.context = context or {}
        for key, value in kwargs.items():
            setattr(self, key, value)
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        parts = [self.__class__.__name__]
        if self.tableau_error_code:
            parts.append(f"[{self.tableau_error_code}]")
        if self.tableau_error_message:
            parts.append(f"{self.tableau_error_message}")
        return " ".join(parts)

    def __str__(self) -> str:
        return self._format_message()


class AuthenticationError(TableauError):
    """Sign-in failed, token expired, or credentials rejected."""


class CatalogUnavailableError(TableauError):
    """Both GraphQL Metadata API and REST API datasource discovery failed."""


class IntrospectionError(TableauError):
    """readMetadata or getDatasourceModel returned an unexpected or unparseable response."""


class DatasourceNotFoundError(TableauError):
    """The requested datasource LUID does not exist or is not accessible."""


class QueryExecutionError(TableauError):
    """VDS returned a pre-streaming or during-streaming error object."""


class RateLimitError(TableauError):
    """HTTP 429 or Tableau rate-limit response. Includes retry-after if available."""

    def __init__(
        self,
        *,
        status_code: int | None = None,
        response_body: bytes = b"",
        response_headers: dict[str, str] | None = None,
        tableau_error_code: str | None = None,
        tableau_error_message: str | None = None,
        context: dict[str, Any] | None = None,
        retry_after: int | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            status_code=status_code,
            response_body=response_body,
            response_headers=response_headers,
            tableau_error_code=tableau_error_code,
            tableau_error_message=tableau_error_message,
            context=context,
            **kwargs,
        )
        self.retry_after = retry_after


class ServerError(TableauError):
    """HTTP 5xx or unrecoverable server-side failure."""


class ViewQueryError(TableauError):
    """REST view data query failed (e.g. bad view ID, site not found, permission denied).

    Raised for non-2xx responses from the
    ``GET /api/{version}/sites/{site-id}/views/{view-id}/data`` endpoint
    that are not authentication, rate-limit, or server errors.
    """


class ValidationError(TableauError):
    """Request payload or response failed Pydantic validation.

    Wraps pydantic.ValidationError with additional HTTP context.
    """
