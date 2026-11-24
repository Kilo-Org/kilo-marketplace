# Retry helpers

Both retry only answers that came back quickly and say nothing ran: `429`, `500`, `502`, `503`. A `504` or a client timeout may mean the request is still running: see SKILL.md § Do not pay twice.

**A `200` can carry an error.** When a non-streaming answer takes longer than 60 seconds, the API sends a space every 15 seconds to keep the connection open, and the first space fixes the status at `200`. If the provider fails after that, the body is `{"error": {...}}` (after leading spaces, which JSON parsers skip) and there are no cost headers. So check the body, not only the status: `read_result` / `readResult` below do. Such a late error is not retried automatically: the request ran for over a minute, so let the caller decide.

## Python

```python
import os
import random
import time
import requests

RETRYABLE = {429, 500, 502, 503}  # not 504: the request may still be running


class AimlapiError(Exception):
    def __init__(self, status, body, request_id):
        err = body.get("error") if isinstance(body, dict) else None
        message = (err or {}).get("message") if isinstance(err, dict) else None
        super().__init__(f"AI/ML API {status} ({request_id}): {message or (body.get('message') if isinstance(body, dict) else body)}")
        self.status, self.body, self.request_id = status, body, request_id


def post_with_retry(url, *, headers, json, attempts=4, timeout=900):
    for attempt in range(attempts):
        resp = requests.post(url, headers=headers, json=json, timeout=timeout)
        if resp.status_code not in RETRYABLE or attempt == attempts - 1:
            return resp
        retry_after = resp.headers.get("Retry-After")
        delay = float(retry_after) if retry_after and retry_after.isdigit() else min(60, 2 ** attempt) + random.random()
        time.sleep(delay)


def read_result(resp):
    """The parsed body, or AimlapiError for an error status or a 200 that carries an error."""
    try:
        body = resp.json()
    except ValueError:
        body = resp.text
    if not resp.ok or (isinstance(body, dict) and isinstance(body.get("error"), dict)):
        raise AimlapiError(resp.status_code, body, resp.headers.get("x-request-id"))
    return body
```

Usage:

```python
resp = post_with_retry(
    "https://api.aimlapi.com/v1/chat/completions",
    headers={"Authorization": f"Bearer {os.environ['AIMLAPI_API_KEY']}", "X-Client-Request-Id": "order-8f21c4"},
    json={"model": "openai/gpt-4o-mini", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 50},
)
answer = read_result(resp)
```

## TypeScript

Node 18+ (`fetch` built in).

```ts
const RETRYABLE = new Set([429, 500, 502, 503]); // not 504: the request may still be running
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

export async function postWithRetry(
  url: string,
  body: unknown,
  { attempts = 4, timeoutMs = 900_000, clientRequestId }: { attempts?: number; timeoutMs?: number; clientRequestId?: string } = {},
): Promise<Response> {
  const headers: Record<string, string> = {
    Authorization: `Bearer ${process.env.AIMLAPI_API_KEY}`,
    "Content-Type": "application/json",
  };
  if (clientRequestId) headers["X-Client-Request-Id"] = clientRequestId;

  for (let attempt = 0; ; attempt++) {
    const resp = await fetch(url, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(timeoutMs),
    });
    if (!RETRYABLE.has(resp.status) || attempt === attempts - 1) return resp;

    const retryAfter = Number(resp.headers.get("retry-after"));
    const delay = Number.isFinite(retryAfter) && retryAfter > 0
      ? retryAfter * 1000
      : Math.min(60_000, 2 ** attempt * 1000) + Math.random() * 1000;
    await sleep(delay);
  }
}

/** The parsed body; throws for an error status or a 200 that carries an error. */
export async function readResult(resp: Response): Promise<any> {
  const text = await resp.text();
  let body: any = text;
  try {
    body = JSON.parse(text);
  } catch {
    // not JSON: keep the text
  }
  const err = body?.error && typeof body.error === "object" ? body.error : undefined;
  if (!resp.ok || err) {
    const details = (err?.details ?? []).map((d: { path?: string; reason?: string }) => `${d.path}: ${d.reason}`).join("; ");
    const message = err?.message ?? body?.message ?? text;
    throw new Error(`AI/ML API ${resp.status} (${resp.headers.get("x-request-id")}): ${message}${details ? ` (${details})` : ""}`);
  }
  return body;
}
```

Usage:

```ts
const resp = await postWithRetry("https://api.aimlapi.com/v1/chat/completions", {
  model: "openai/gpt-4o-mini",
  messages: [{ role: "user", content: "Hi" }],
  max_tokens: 50,
}, { clientRequestId: "order-8f21c4" });

const answer = await readResult(resp);
```
