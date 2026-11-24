#!/usr/bin/env python3
"""Send one request to AI/ML API in sandbox mode and show what came back. Standard library only.

  try.py chat     '{"model": "openai/gpt-4o-mini", "messages": [{"role": "user", "content": "[sandbox:error=429] hi"}]}'
  try.py image    '{"model": "flux/schnell", "prompt": "a red cube"}'
  try.py embed    '{"model": "openai/text-embedding-3-small", "input": "hello"}'
  try.py messages '{"model": "anthropic/claude-haiku-5-5", "max_tokens": 50, "messages": [{"role": "user", "content": "hi"}]}'
  try.py <path>   '<json>'          # any other POST path, e.g. /v1/responses

The X-AIMLAPI-Sandbox: 1 header is always sent, so nothing is charged.
Reads the key from AIMLAPI_API_KEY and never prints it. Body may be @file.json.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

API = "https://api.aimlapi.com"
# A named User-Agent shows which requests come from these skills; it is not needed for access.
CLIENT = "aimlapi-skills/1.0.5 try.py"
PATHS = {
    "chat": "/v1/chat/completions",
    "responses": "/v1/responses",
    "messages": "/v1/messages",
    "image": "/v1/images/generations",
    "embed": "/v1/embeddings",
    "tts": "/v1/tts",
}
SHOW = ("x-aimlapi-sandbox", "x-inference-id", "x-aimlapi-usd-spent", "x-aimlapi-credits-used", "retry-after", "content-type")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None  # never send the key on to another host


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    target, raw = sys.argv[1], sys.argv[2]
    path = PATHS.get(target, target)
    if not path.startswith("/"):
        sys.exit(f"unknown target {target!r}; use one of {', '.join(PATHS)} or a path such as /v1/responses")
    if raw.startswith("@"):
        with open(raw[1:], encoding="utf-8") as f:
            raw = f.read()
    body = json.loads(raw)

    key = os.environ.get("AIMLAPI_API_KEY")
    if not key:
        sys.exit("AIMLAPI_API_KEY is not set.")
    req = urllib.request.Request(
        API + path,
        data=json.dumps(body).encode(),
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "X-AIMLAPI-Sandbox": "1",
            "User-Agent": CLIENT,
            "x-aimlapi-client": CLIENT,
        },
    )
    try:
        resp = urllib.request.build_opener(_NoRedirect).open(req, timeout=120)
        status, headers, text = resp.status, resp.headers, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as err:
        status, headers, text = err.code, err.headers, err.read().decode("utf-8", "replace")

    print(f"HTTP {status}")
    for name in SHOW:
        if headers.get(name) is not None:
            print(f"{name}: {headers.get(name)}")
    print()
    try:
        print(json.dumps(json.loads(text), indent=2)[:6000])
    except json.JSONDecodeError:
        print(text[:6000])
    return 0 if status < 400 else 1


if __name__ == "__main__":
    sys.exit(main())
