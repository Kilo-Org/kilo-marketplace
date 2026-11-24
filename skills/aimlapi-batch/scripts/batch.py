#!/usr/bin/env python3
"""Run an AI/ML API batch from a JSONL file. Standard library only.

  batch.py check   requests.jsonl                 # validate locally, no network
  batch.py run     requests.jsonl [--out DIR]     # check, upload, create, wait, download results;
                                                  # safe to re-run: resumes the batch it created
  batch.py upload  requests.jsonl                 # print the file id
  batch.py create  <input_file_id>                # print the batch
  batch.py status  <batch_id>
  batch.py results <batch_id> [--out DIR]         # download output and error files
  batch.py cancel  <batch_id>

Reads the key from AIMLAPI_API_KEY and never prints it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import time
import urllib.error
import urllib.request
import uuid

API = "https://api.aimlapi.com"
# A named User-Agent shows which requests come from these skills; it is not needed for access.
CLIENT = "aimlapi-skills/1.0.5 batch.py"
ENDPOINT = "/v1/chat/completions"
SINGLE_REQUEST_MAX = 50 * 1024 * 1024   # above this, use the parts upload
PART_SIZE = 8 * 1024 * 1024              # every part but the last must be at least 5 MiB
LINE_MAX = 1024 * 1024
TERMINAL = {"completed", "failed", "expired", "cancelled"}
ALLOWED_FIELDS = {
    "model", "messages", "max_tokens", "max_completion_tokens", "temperature", "top_p", "stop", "seed",
    "frequency_penalty", "presence_penalty", "response_format", "tools", "tool_choice", "parallel_tool_calls",
    "user", "stream", "n",
}


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def key() -> str:
    value = os.environ.get("AIMLAPI_API_KEY")
    if not value:
        sys.exit("AIMLAPI_API_KEY is not set.")
    return value


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None  # surface 3xx as HTTPError so we can follow it without the API key


_OPENER = urllib.request.build_opener(_NoRedirect)
TRANSIENT = {429, 500, 502, 503, 504}


class Transient(Exception):
    """A poll that failed in a way worth asking again (rate limit, gateway, network)."""


def request(method: str, path: str, *, body: bytes | None = None, content_type: str | None = None,
            raw: bool = False, extra: dict | None = None, transient_ok: bool = False):
    headers = {"Authorization": f"Bearer {key()}", "User-Agent": CLIENT, "x-aimlapi-client": CLIENT, **(extra or {})}
    if content_type:
        headers["Content-Type"] = content_type
    req = urllib.request.Request(API + path, data=body, method=method, headers=headers)
    try:
        with _OPENER.open(req, timeout=300) as resp:
            data = resp.read()
            return data if raw else json.loads(data)
    except urllib.error.HTTPError as err:
        if err.code in (301, 302, 303, 307, 308) and err.headers.get("Location"):
            # File content redirects to a short-lived signed link. Fetch it WITHOUT the
            # Authorization header: a signed link refuses a request that carries two credentials.
            signed = urllib.request.Request(err.headers["Location"], headers={"User-Agent": CLIENT})
            with urllib.request.urlopen(signed, timeout=600) as resp:
                data = resp.read()
                return data if raw else json.loads(data)
        if transient_ok and err.code in TRANSIENT:
            raise Transient(f"HTTP {err.code}") from err
        log(f"{method} {path} -> HTTP {err.code}")
        if err.headers.get("Retry-After"):
            log(f"Retry-After: {err.headers['Retry-After']}")
        print(err.read().decode("utf-8", "replace")[:3000])
        sys.exit(3)
    except (urllib.error.URLError, TimeoutError, ConnectionError) as err:
        if transient_ok:
            raise Transient(str(getattr(err, "reason", err))) from err
        log(f"{method} {path} failed: {getattr(err, 'reason', err)}")
        sys.exit(3)


def post_json(path: str, payload: dict):
    return request("POST", path, body=json.dumps(payload).encode(), content_type="application/json")


def check(path: str) -> dict:
    """Catch the mistakes the API would refuse, before uploading."""
    ids, models, problems, count = set(), set(), [], 0
    with open(path, "rb") as f:
        for n, raw in enumerate(f, 1):
            if not raw.strip():
                continue
            count += 1
            if len(raw) > LINE_MAX:
                problems.append(f"line {n}: longer than 1 MiB")
                continue
            try:
                line = json.loads(raw)
            except json.JSONDecodeError as err:
                problems.append(f"line {n}: not JSON ({err.msg})")
                continue
            cid = line.get("custom_id")
            if not isinstance(cid, str) or not 1 <= len(cid) <= 512:
                problems.append(f"line {n}: custom_id must be a string of 1-512 characters")
            elif cid in ids:
                problems.append(f"line {n}: duplicate custom_id {cid!r}")
            ids.add(cid)
            if line.get("method") != "POST" or line.get("url") != ENDPOINT:
                problems.append(f'line {n}: needs "method": "POST" and "url": "{ENDPOINT}"')
            body = line.get("body") or {}
            models.add(body.get("model"))
            if "max_tokens" not in body and "max_completion_tokens" not in body:
                problems.append(f"line {n}: body needs max_tokens or max_completion_tokens")
            if body.get("stream"):
                problems.append(f"line {n}: stream may only be false in a batch")
            if body.get("n", 1) != 1:
                problems.append(f"line {n}: n may only be 1 in a batch")
            unknown = sorted(set(body) - ALLOWED_FIELDS)
            if unknown:
                problems.append(f"line {n}: fields a batch does not take: {', '.join(unknown)}")
    if len(models) > 1:
        problems.append(f"one model per file; found {sorted(m for m in models if m)}")
    if count == 0:
        problems.append("the file has no requests")
    return {"lines": count, "model": next(iter(models), None), "problems": problems}


def upload(path: str) -> str:
    size = os.path.getsize(path)
    name = os.path.basename(path)
    if size <= SINGLE_REQUEST_MAX:
        boundary = uuid.uuid4().hex
        with open(path, "rb") as f:
            content = f.read()
        body = (
            f'--{boundary}\r\nContent-Disposition: form-data; name="purpose"\r\n\r\nbatch\r\n'
            f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{name}"\r\n'
            "Content-Type: application/jsonl\r\n\r\n"
        ).encode() + content + f"\r\n--{boundary}--\r\n".encode()
        answer = request("POST", "/v1/files", body=body, content_type=f"multipart/form-data; boundary={boundary}")
        return answer["id"]

    # Large file: parts go straight to storage through signed URLs, not through the API.
    upload_obj = post_json("/v1/uploads", {"filename": name, "purpose": "batch", "bytes": size, "mime_type": "application/jsonl"})
    parts = []
    with open(path, "rb") as f:
        for number in range(1, math.ceil(size / PART_SIZE) + 1):
            chunk = f.read(PART_SIZE)
            part = post_json(f"/v1/uploads/{upload_obj['id']}/parts", {"part_number": number})
            put = urllib.request.Request(part["url"], data=chunk, method="PUT")
            with urllib.request.urlopen(put, timeout=600) as resp:
                etag = resp.headers["ETag"]
            parts.append({"part_number": number, "etag": etag})
            log(f"part {number} uploaded")
    done = post_json(f"/v1/uploads/{upload_obj['id']}/complete", {"parts": parts})
    if not done.get("file"):
        sys.exit(f"upload did not complete: {json.dumps(done)}")
    return done["file"]["id"]


def create(file_id: str, webhook_url: str | None = None, key: str | None = None) -> dict:
    payload = {"input_file_id": file_id, "endpoint": ENDPOINT, "completion_window": "24h"}
    if webhook_url:
        payload["webhook_url"] = webhook_url
    # A repeat with the same key returns the batch the first request created instead of a new one.
    return request("POST", "/v1/batches", body=json.dumps(payload).encode(), content_type="application/json",
                   extra={"Idempotency-Key": key or f"aimlapi-skills-{file_id}"})


def digest(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def state_path(path: str) -> str:
    return f"{path}.aimlapi-batch.json"


def save_state(path: str, state: dict) -> None:
    tmp = state_path(path) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, state_path(path))


def run(path: str, out: str, interval: float, webhook_url: str | None = None,
        upload_fn=None, create_fn=None, wait_fn=None, results_fn=None) -> dict:
    """Upload, create, wait and download, at most once per file content.

    Progress is kept in <file>.aimlapi-batch.json. A re-run with the same content resumes the
    batch it created instead of creating and paying for a second one. The Idempotency-Key comes
    from the content too, so a crash between create and saving the id still returns the same batch.
    """
    upload_fn, create_fn = upload_fn or upload, create_fn or create
    wait_fn, results_fn = wait_fn or wait, results_fn or results
    sha = digest(path)
    state = {}
    if os.path.exists(state_path(path)):
        with open(state_path(path), encoding="utf-8") as f:
            state = json.load(f)
        if state.get("sha256") != sha:
            sys.exit(f"{path} changed since batch {state.get('batch_id') or '(none)'} was started from it. "
                     f"To start a new batch on purpose, delete {state_path(path)}.")
    state["sha256"] = sha
    if state.get("batch_id"):
        log(f"resuming {state['batch_id']} (from {state_path(path)}); nothing new is created")
    else:
        if not state.get("file_id"):
            state["file_id"] = upload_fn(path)
            save_state(path, state)
            log(f"uploaded {state['file_id']}")
        batch = create_fn(state["file_id"], webhook_url, f"aimlapi-skills-{sha[:48]}")
        state["batch_id"] = batch["id"]
        save_state(path, state)
        log(f"created {batch['id']}")
    batch = wait_fn(state["batch_id"], interval)
    results_fn(batch, out)
    return batch


def wait(batch_id: str, interval: float, misses: int = 10) -> dict:
    failed = 0
    while True:
        try:
            batch = request("GET", f"/v1/batches/{batch_id}", transient_ok=True)
            failed = 0
        except Transient as err:
            failed += 1
            if failed >= misses:
                log(f"{batch_id}: {failed} polls in a row failed ({err}). The batch keeps running: run the same `batch.py run` command again to resume it.")
                sys.exit(3)
            log(f"{batch_id}: poll failed ({err}), asking again")
            time.sleep(min(60, interval * failed))
            continue
        counts = batch.get("request_counts") or {}
        log(f"{batch_id}: {batch['status']} {counts.get('completed', 0)}/{counts.get('total', '?')} done, {counts.get('failed', 0)} failed")
        if batch["status"] in TERMINAL:
            return batch
        time.sleep(interval)


def results(batch: dict, out: str) -> None:
    os.makedirs(out, exist_ok=True)
    for field in ("output_file_id", "error_file_id"):
        file_id = batch.get(field)
        if file_id:
            target = os.path.join(out, f"{batch['id']}.{field.split('_')[0]}.jsonl")
            with open(target, "wb") as f:
                f.write(request("GET", f"/v1/files/{file_id}/content", raw=True))
            log(f"saved {target}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("cmd", choices=("check", "run", "upload", "create", "status", "results", "cancel"))
    p.add_argument("target")
    p.add_argument("--out", default="batch-results")
    p.add_argument("--interval", type=float, default=60)
    p.add_argument("--webhook-url", help="also send a signed batch.* event to this https URL when the batch ends")
    a = p.parse_args()

    if a.cmd in ("check", "run", "upload"):
        report = check(a.target)
        for problem in report["problems"]:
            log(problem)
        if report["problems"]:
            sys.exit(f"{len(report['problems'])} problem(s); nothing was uploaded")
        log(f"{report['lines']} requests for {report['model']}")
        if a.cmd == "check":
            return
        if a.cmd == "upload":
            print(upload(a.target))
            return
        print(json.dumps(run(a.target, a.out, a.interval, a.webhook_url), indent=2))
    elif a.cmd == "create":
        print(json.dumps(create(a.target, a.webhook_url), indent=2))
    elif a.cmd == "status":
        print(json.dumps(request("GET", f"/v1/batches/{a.target}"), indent=2))
    elif a.cmd == "results":
        results(request("GET", f"/v1/batches/{a.target}"), a.out)
    elif a.cmd == "cancel":
        print(json.dumps(request("POST", f"/v1/batches/{a.target}/cancel"), indent=2))


if __name__ == "__main__":
    main()
