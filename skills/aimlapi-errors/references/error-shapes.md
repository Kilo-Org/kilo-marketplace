# Error body shapes

Observed on api.aimlapi.com. Source: https://docs.aimlapi.com/errors-and-messages/general-info.md

Most errors are `application/problem+json`:

```json
{
  "title": "Unauthorized",
  "status": 401,
  "message": "This request requires a valid API key. You can create a new API key on the Billing page: https://aimlapi.com/app/keys",
  "instance": "/v1/chat/completions",
  "requestId": "OQtn2ADiWhg5KEqO5pryE",
  "timestamp": "2026-11-12T15:15:59.630Z",
  "error": { "name": "UnauthorizedException", "message": "…" }
}
```

A request that fails validation lists every bad field in `error.details`:

```json
{
  "title": "Bad Request",
  "status": 400,
  "message": "Validation failed. Please check your request fields and values (including required params, allowed formats, and incompatible options) and try again.",
  "error": {
    "name": "PublicApiValidationException",
    "type": "invalid_request_error",
    "details": [{ "path": "lyrics", "reason": "String must contain at least 10 character(s)", "code": "too_small" }]
  }
}
```

Fix each `path` with its `reason`; the top-level `message` alone does not say which field is wrong.

Some errors that come from a model provider use the OpenAI shape: `{"error": {"message": "…", "type": "…", "code": "…"}}`. A machine-readable code, when there is one, is in top-level `code` or in `error.code`. Parse defensively:

## Parse defensively

One helper for every shape above:

```python
def error_text(body: dict) -> str:
    err = body.get("error") if isinstance(body.get("error"), dict) else {}
    details = "; ".join(f"{d.get('path')}: {d.get('reason')}" for d in err.get("details") or [] if isinstance(d, dict))
    text = body.get("message") or err.get("message") or str(body)
    return f"{text} ({details})" if details else text

def error_code(body: dict) -> str | None:
    err = body.get("error") if isinstance(body.get("error"), dict) else {}
    return body.get("code") or err.get("code")
```
