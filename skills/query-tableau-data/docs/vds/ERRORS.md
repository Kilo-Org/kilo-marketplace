# Error Codes

VDS returns standard `HTTP` status codes and _Tableau-specific_ error codes in the response body.

| HTTP Status | Tableau Code | Condition | Details |
|-------------|--------------|-----------|---------|
| 400 | `400000` | Bad request | The content of the request body is invalid. Check for missing or incomplete JSON. |
| 400 | `400800` | Invalid formula for calculation | Invalid custom calculation syntax. |
| 400 | `400802` | Invalid API request | The incoming request isn't valid per the OpenAPI specification. |
| 400 | `400803` | Validation failed | The incoming request isn't valid per the validation rules. |
| 400 | `400804` | Response too large | The response value exceeds the limit. You must apply a filter in your request. |
| 401 | `401001` | Login error | The login failed for the given user. |
| 401 | `401002` | Invalid authorization credentials | The provided auth token is formatted incorrectly. |
| 403 | `403157` | Feature disabled | The feature is disabled. |
| 403 | `403800` | API access permission denied | The user doesn't have API Access granted on the given data source. |
| 404 | `404934` | Unknown field | The requested field doesn't exist. |
| 404 | `404950` | API endpoint not found | The request endpoint doesn't exist. |
| 408 | `408000` | Request timeout | The request timed out. |
| 409 | `409000` | User already on site | HTTP status conflict. |
| 429 | `429000` | Too many requests | Too many requests in the allotted amount of time. |
| 500 | `500000` | Internal server error | The request could not be completed. |
| 500 | `500810` | VDS empty table response | The underlying data engine returned empty data value response. |
| 500 | `500811` | VDS missing table | The underlying data engine returned empty metadata associated with response. |
| 500 | `500812` | Error while processing an error | Internal processing error. |
| 501 | `501000` | Not implemented | Can't find response from upstream server. |
| 503 | `503800` | VDS unavailable | The underlying data engine is unavailable. |
| 503 | `503801` | VDS discovery error | The upstream service can't be found. |
| 504 | `504000` | Gateway timeout | The upstream service response timed out. |

---

### Related Documentation

- [QUERY_DATASOURCE.md](../api/QUERY_DATASOURCE.md) — error handling in the query endpoint
- [STREAMING.md](./STREAMING.md) — in-stream error events during SSE responses
- [LIMITATIONS.md](./LIMITATIONS.md) — rate limits (`429`) and version constraints
