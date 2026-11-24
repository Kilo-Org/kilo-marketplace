#!/usr/bin/env python3
"""Submit an AI/ML API asynchronous job and wait for its result. Standard library only.

  job.py submit video    --body '{"model": "...", "prompt": "..."}' [--download out.mp4]
  job.py submit music    --body @request.json
  job.py submit stt      --body '{"model": "...", "url": "https://.../audio.mp3"}'
  job.py submit response --body '{"model": "...", "input": "..."}'      # sent with background: true
  job.py poll   video <id>

Options: --sandbox (free test run), --interval SECONDS, --timeout SECONDS, --no-wait.
Reads the key from AIMLAPI_API_KEY and never prints it.
Exit codes: 0 completed (or incomplete with partial output), 1 job failed, 2 still running (timeout, or polls kept
failing), 3 HTTP error, 4 completed but the download failed.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.aimlapi.com"
# A named User-Agent shows which requests come from these skills; it is not needed for access.
CLIENT = "aimlapi-skills/1.0.5 job.py"

KINDS = {
    #          submit path              poll URL builder                                  default interval
    "video": ("/v2/video/generations", lambda i: f"/v2/video/generations?id={urllib.parse.quote(i)}", 15),
    "music": ("/v2/generate/audio", lambda i: f"/v2/generate/audio?id={urllib.parse.quote(i)}", 10),
    "stt": ("/v1/stt/create", lambda i: f"/v1/stt/{urllib.parse.quote(i)}", 5),
    "response": ("/v1/responses", lambda i: f"/v1/responses/{urllib.parse.quote(i)}", 5),
}
PENDING = {"queued", "pending", "waiting", "active", "generating", "processing", "in_progress"}
SUCCESS = {"completed", "succeeded"}


TRANSIENT = {429, 500, 502, 503, 504}


class Transient(Exception):
    """A poll that failed in a way worth asking again (rate limit, gateway, network)."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None  # an API call never follows a redirect: the key must not travel to another host


_OPENER = urllib.request.build_opener(_NoRedirect)


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def call(method: str, path: str, body: dict | None, sandbox: bool, transient_ok: bool = False) -> tuple[dict, dict]:
    key = os.environ.get("AIMLAPI_API_KEY")
    if not key:
        sys.exit("AIMLAPI_API_KEY is not set. Create a key at https://aimlapi.com/app/keys and set it in your environment.")
    headers = {
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
        "User-Agent": CLIENT,
        "x-aimlapi-client": CLIENT,
    }
    if sandbox:
        headers["X-AIMLAPI-Sandbox"] = "1"
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(API + path, data=data, method=method, headers=headers)
    try:
        with _OPENER.open(req, timeout=120) as resp:
            return json.load(resp), dict(resp.headers)
    except urllib.error.HTTPError as err:
        if transient_ok and err.code in TRANSIENT:
            raise Transient(f"HTTP {err.code}") from err
        text = err.read().decode("utf-8", "replace")[:2000]
        log(f"{method} {path} -> HTTP {err.code}")
        if err.headers.get("Retry-After"):
            log(f"Retry-After: {err.headers['Retry-After']}")
        print(text)
        sys.exit(3)
    except (urllib.error.URLError, TimeoutError, ConnectionError) as err:
        if transient_ok:
            raise Transient(str(getattr(err, "reason", err))) from err
        log(f"{method} {path} failed: {getattr(err, 'reason', err)}")
        sys.exit(3)


def download(url: str, target: str) -> bool:
    """Save a result file. No API key: result links are public or signed."""
    req = urllib.request.Request(url, headers={"User-Agent": CLIENT})
    try:
        with urllib.request.urlopen(req, timeout=600) as resp, open(target, "wb") as f:
            while chunk := resp.read(1 << 20):
                f.write(chunk)
        return True
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as err:
        log(f"download failed ({getattr(err, 'code', None) or getattr(err, 'reason', err)}): {url}")
        return False


def job_id(answer: dict) -> str:
    for key in ("id", "generation_id"):
        if answer.get(key):
            return str(answer[key])
    print(json.dumps(answer, indent=2))
    sys.exit("The submit answer has no id: see the body above.")


def result_url(answer: dict) -> str | None:
    for path in (("video", "url"), ("audio_file", "url"), ("audio", "url")):
        node = answer
        for key in path:
            node = node.get(key) if isinstance(node, dict) else None
        if isinstance(node, str):
            return node
    return None


def wait(kind: str, ident: str, a) -> int:
    _, build, default_interval = KINDS[kind]
    interval = a.interval or default_interval
    deadline = time.monotonic() + a.timeout
    failed = 0
    while True:
        try:
            answer, headers = call("GET", build(ident), None, a.sandbox, transient_ok=True)
            failed = 0
        except Transient as err:
            failed += 1
            if failed >= 10 or time.monotonic() > deadline:
                log(f"{failed} polls in a row failed ({err}). The job keeps running: poll again with `job.py poll {kind} {ident}`.")
                return 2
            log(f"{kind} {ident}: poll failed ({err}), asking again")
            time.sleep(min(60, interval * failed))
            continue
        status = str(answer.get("status", "")).lower()
        log(f"{kind} {ident}: {status or 'no status'}")
        if status in SUCCESS or status == "incomplete":
            print(json.dumps(answer, indent=2))
            if status == "incomplete":
                reason = (answer.get("incomplete_details") or {}).get("reason", "unknown")
                log(f"stopped early ({reason}); the partial output is above")
            url = result_url(answer)
            if url and a.download:
                if not download(url, a.download):
                    log("the job completed (and was charged); only the download failed. Fetch the URL above again soon: result links expire.")
                    return 4
                log(f"saved {a.download}")
            elif url:
                log(f"result: {url}")
            if headers.get("x-aimlapi-sandbox") == "true":
                log("note: sandbox answer, nothing was charged")
            return 0
        if status and status not in PENDING:
            print(json.dumps(answer, indent=2))
            log(f"job ended with status {status}: see error in the body above")
            return 1
        if time.monotonic() > deadline:
            log(f"still {status} after {a.timeout}s. The job keeps running: poll again with `job.py poll {kind} {ident}`.")
            return 2
        time.sleep(interval)


def load_body(text: str) -> dict:
    if text.startswith("@"):
        with open(text[1:], encoding="utf-8") as f:
            return json.load(f)
    return json.loads(text)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("submit", "poll"):
        s = sub.add_parser(name)
        s.add_argument("kind", choices=sorted(KINDS))
        if name == "submit":
            s.add_argument("--body", required=True, help="JSON request body, or @file.json")
            s.add_argument("--no-wait", action="store_true")
        else:
            s.add_argument("id")
        s.add_argument("--sandbox", action="store_true", help="free test run: live response format, no charge")
        s.add_argument("--interval", type=float)
        s.add_argument("--timeout", type=float, default=1800)
        s.add_argument("--download", help="save the result file here")
    a = p.parse_args()

    if a.cmd == "poll":
        sys.exit(wait(a.kind, a.id, a))

    body = load_body(a.body)
    if a.kind == "response":
        body["background"] = True
    path = KINDS[a.kind][0]
    answer, _ = call("POST", path, body, a.sandbox)
    ident = job_id(answer)
    log(f"submitted {a.kind} {ident}")
    if a.no_wait:
        print(json.dumps(answer, indent=2))
        return
    sys.exit(wait(a.kind, ident, a))


if __name__ == "__main__":
    main()
