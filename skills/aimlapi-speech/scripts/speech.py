#!/usr/bin/env python3
"""Text-to-speech and speech-to-text on AI/ML API. Standard library only.

  speech.py tts  --body '{"model": "...", "text": "..."}' --out speech.mp3
  speech.py tts  --body @request.json --out speech.mp3
  speech.py stt  --model <id> --url https://.../meeting.mp3 [--body '{"language": "en"}']
  speech.py stt  --model <id> --file meeting.mp3 [--field audio|file] [--out answer.json]
  speech.py poll <generation_id> [--out answer.json]

tts sends POST /v1/tts and saves the audio: from the `audio.url` of a JSON answer, or the binary body that comes
with `"stream": true` (some models default to it). stt submits POST /v1/stt/create (JSON with `url`, or a
multipart upload of a local file), then polls GET /v1/stt/<generation_id> and prints the transcript.

Options: --sandbox (free test run), --interval SECONDS, --timeout SECONDS, --no-wait, --json (print the whole answer).
Reads the key from AIMLAPI_API_KEY and never prints it. API calls never follow redirects; audio downloads carry no key.
Exit codes: 0 done, 1 the job failed (status "error"), 2 still running (timeout, or polls kept failing),
3 HTTP or network error, 4 the audio was generated (and charged) but could not be saved.
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

API = "https://api.aimlapi.com"
# A named User-Agent shows which requests come from these skills; it is not needed for access.
CLIENT = "aimlapi-skills/1.0.5 speech.py"

PENDING = {"queued", "pending", "waiting", "active", "generating", "processing", "in_progress"}
SUCCESS = {"completed", "succeeded"}
TRANSIENT = {429, 500, 502, 503, 504}
FILE_FIELDS = ("audio", "file")


class Transient(Exception):
    """A poll that failed in a way worth asking again (rate limit, gateway, network)."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None  # an API call never follows a redirect: the key must not travel to another host


_OPENER = urllib.request.build_opener(_NoRedirect)


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


# ---------------------------------------------------------------- pure helpers (unit-tested)


def load_body(text: str | None) -> dict:
    if not text:
        return {}
    if text.startswith("@"):
        with open(text[1:], encoding="utf-8") as f:
            body = json.load(f)
    else:
        body = json.loads(text)
    if not isinstance(body, dict):
        raise ValueError("--body must be a JSON object")
    return body


def form_value(value) -> str:
    """A multipart field is text: booleans as true/false, objects and arrays as JSON."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return value
    return json.dumps(value)


def multipart(fields: dict, file_field: str, filename: str, content: bytes, content_type: str | None = None,
              boundary: str | None = None) -> tuple[bytes, str]:
    """Build a multipart/form-data body. Returns (body, Content-Type header value)."""
    boundary = boundary or "aimlapi-" + uuid.uuid4().hex
    safe_name = os.path.basename(filename).replace('"', "_").replace("\r", "_").replace("\n", "_") or "audio"
    ctype = content_type or mimetypes.guess_type(safe_name)[0] or "application/octet-stream"
    out = bytearray()
    for name, value in fields.items():
        out += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n".encode()
        out += form_value(value).encode() + b"\r\n"
    out += (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"{file_field}\"; filename=\"{safe_name}\"\r\n"
        f"Content-Type: {ctype}\r\n\r\n"
    ).encode()
    out += content + b"\r\n"
    out += f"--{boundary}--\r\n".encode()
    return bytes(out), f"multipart/form-data; boundary={boundary}"


def audio_source(answer: dict) -> tuple[str, str] | None:
    """Where the audio of a JSON TTS answer is: ("url", link) or ("base64", data). The live answer is
    {"audio": {"url": ...}}; the published schema shows "audio" as a plain URL string, so accept both."""
    audio = answer.get("audio")
    if isinstance(audio, str) and audio:
        return ("url", audio)
    if isinstance(audio, dict):
        if isinstance(audio.get("url"), str) and audio["url"]:
            return ("url", audio["url"])
        if isinstance(audio.get("base64"), str) and audio["base64"]:
            return ("base64", audio["base64"])
    return None


def sniff_format(head: bytes) -> str | None:
    """The audio container from the first bytes. A binary TTS answer is labelled audio/wav whatever it holds."""
    if head[:4] == b"RIFF" and head[8:12] == b"WAVE":
        return "wav"
    if head[:3] == b"ID3" or (len(head) > 1 and head[0] == 0xFF and head[1] & 0xE0 == 0xE0 and head[1] & 0x06):
        return "mp3"
    if head[:4] == b"OggS":
        return "ogg"
    if head[:4] == b"fLaC":
        return "flac"
    if len(head) > 1 and head[0] == 0xFF and head[1] & 0xF6 == 0xF0:
        return "aac"
    return None


def transcript_text(result) -> str | None:
    """The transcript in the `result` of a finished STT poll. Most models answer {"text": ...}; Deepgram models
    answer their own document, whose transcript is results.channels[0].alternatives[0].transcript."""
    if isinstance(result, str):
        return result
    if not isinstance(result, dict):
        return None
    if isinstance(result.get("text"), str):
        return result["text"]
    channels = (result.get("results") or {}).get("channels") if isinstance(result.get("results"), dict) else None
    if isinstance(channels, dict):
        channels = [channels]
    if isinstance(channels, list) and channels and isinstance(channels[0], dict):
        alternatives = channels[0].get("alternatives") or []
        if alternatives and isinstance(alternatives[0], dict) and isinstance(alternatives[0].get("transcript"), str):
            return alternatives[0]["transcript"]
    return None


def file_field_from_schema(doc: dict) -> str | None:
    """Which multipart field a model takes its audio file in ("audio" or "file"), from its OpenAPI document."""
    for path in (doc.get("paths") or {}).values():
        for op in path.values() if isinstance(path, dict) else []:
            content = ((op or {}).get("requestBody") or {}).get("content") or {}
            for media in content.values():
                props = (media.get("schema") or {}).get("properties") or {}
                for name in FILE_FIELDS:
                    if (props.get(name) or {}).get("format") == "binary":
                        return name
    return None


def poll_path(generation_id: str) -> str:
    ident = urllib.parse.quote(generation_id, safe="")
    return f"/v1/stt/{ident}"


# ---------------------------------------------------------------- network


def _key() -> str:
    key = os.environ.get("AIMLAPI_API_KEY")
    if not key:
        sys.exit("AIMLAPI_API_KEY is not set. Create a key at https://aimlapi.com/app/keys or run the aimlapi-setup skill.")
    return key


def call(method: str, path: str, data: bytes | None, content_type: str | None, sandbox: bool,
         timeout: float = 120, transient_ok: bool = False, accept: str = "application/json"):
    """One API call. Returns the open response (caller reads it). Exits 3 on an HTTP or network error."""
    headers = {
        "Authorization": f"Bearer {_key()}",
        "Accept": accept,
        "User-Agent": CLIENT,
        "x-aimlapi-client": CLIENT,
    }
    if sandbox:
        headers["X-AIMLAPI-Sandbox"] = "1"
    if content_type:
        headers["Content-Type"] = content_type
    req = urllib.request.Request(API + path, data=data, method=method, headers=headers)
    try:
        return _OPENER.open(req, timeout=timeout)
    except urllib.error.HTTPError as err:
        if transient_ok and err.code in TRANSIENT:
            raise Transient(f"HTTP {err.code}") from err
        log(f"{method} {path} -> HTTP {err.code}")
        if 300 <= err.code < 400:
            log("redirect not followed: an API call never sends the key to another address")
        if err.headers.get("Retry-After"):
            log(f"Retry-After: {err.headers['Retry-After']}")
        print(err.read().decode("utf-8", "replace")[:2000])
        sys.exit(3)
    except (urllib.error.URLError, TimeoutError, ConnectionError) as err:
        if transient_ok:
            raise Transient(str(getattr(err, "reason", err))) from err
        log(f"{method} {path} failed: {getattr(err, 'reason', err)}")
        sys.exit(3)


def call_json(method: str, path: str, body: dict | None, sandbox: bool, **kw) -> tuple[dict, dict]:
    data = json.dumps(body).encode() if body is not None else None
    with call(method, path, data, "application/json" if body is not None else None, sandbox, **kw) as resp:
        return json.load(resp), dict(resp.headers)


def download(url: str, target: str) -> bool:
    """Save an audio file. No API key: result links are public or signed."""
    if not url.startswith(("https://", "http://")):
        log(f"not an http(s) link, not downloaded: {url[:100]}")
        return False
    req = urllib.request.Request(url, headers={"User-Agent": CLIENT})
    try:
        with urllib.request.urlopen(req, timeout=600) as resp, open(target, "wb") as f:
            while chunk := resp.read(1 << 20):
                f.write(chunk)
        return True
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as err:
        log(f"download failed ({getattr(err, 'code', None) or getattr(err, 'reason', err)}): {url}")
        return False


def schema_field(model: str) -> str | None:
    """Read the model's request schema from the public catalogue (no key) and find its file field."""
    model = model.removeprefix("sandbox/")
    try:
        query = urllib.parse.urlencode({"id": model})
        req = urllib.request.Request(f"{API}/v1/models?{query}", headers={"User-Agent": CLIENT, "Accept": "application/json"})
        with _OPENER.open(req, timeout=60) as resp:
            data = json.load(resp).get("data") or []
        docs = (data[0].get("info") or {}).get("docsJson") if data else None
        if not docs or urllib.parse.urlparse(docs).hostname != urllib.parse.urlparse(API).hostname:
            return None
        req = urllib.request.Request(docs, headers={"User-Agent": CLIENT, "Accept": "application/json"})
        with _OPENER.open(req, timeout=60) as resp:
            return file_field_from_schema(json.load(resp))
    except (urllib.error.URLError, TimeoutError, ConnectionError, ValueError, KeyError, IndexError):
        return None


# ---------------------------------------------------------------- commands


def cmd_tts(a) -> int:
    body = load_body(a.body)
    if body.get("stream") is True and a.sandbox:
        log("note: sandbox mode does not cover stream: true; expect 400 sandbox_unsupported")
    resp = call("POST", "/v1/tts", json.dumps(body).encode(), "application/json", a.sandbox,
                timeout=a.timeout, accept="application/json, audio/*")
    with resp:
        ctype = (resp.headers.get("Content-Type") or "").lower()
        sandbox_answer = resp.headers.get("x-aimlapi-sandbox") == "true"
        if "json" not in ctype:
            # Binary audio: the body is the file. It arrives labelled audio/wav; the bytes follow the format asked for.
            try:
                with open(a.out, "wb") as f:
                    head = resp.read(1 << 16)
                    f.write(head)
                    while chunk := resp.read(1 << 20):
                        f.write(chunk)
            except (OSError, urllib.error.URLError, TimeoutError, ConnectionError) as err:
                log(f"audio stream broke or could not be written ({err}); the request was charged. Check GET /v2/logs.")
                return 4
            fmt = sniff_format(head)
            log(f"saved {a.out} (binary answer, Content-Type {ctype or 'none'}, looks like {fmt or 'unknown format'})")
            ext = os.path.splitext(a.out)[1].lstrip(".").lower()
            if fmt and ext and ext != fmt and not (fmt == "ogg" and ext in {"opus", "oga"}):
                log(f"warning: the file name ends in .{ext} but the bytes look like {fmt}")
            log("cost: a binary answer carries none; read it from GET /v2/logs")
            return 0
        answer = json.load(resp)
    print(json.dumps(answer, indent=2))
    source = audio_source(answer)
    if source is None:
        log("the answer has no audio: see the body above")
        return 1
    kind, value = source
    if kind == "url":
        if not download(value, a.out):
            log("the speech was generated (and charged); only the download failed. Fetch the URL above again soon: links expire.")
            return 4
    else:
        try:
            with open(a.out, "wb") as f:
                f.write(base64.b64decode(value))
        except (OSError, ValueError) as err:
            log(f"could not save the audio: {err}")
            return 4
    usage = (answer.get("meta") or {}).get("usage") or {}
    log(f"saved {a.out}" + (f"; cost {usage.get('usd_spent')} USD" if "usd_spent" in usage else ""))
    if sandbox_answer:
        log("note: sandbox answer, a placeholder file; nothing was charged")
    return 0


def submit_stt(a) -> str:
    extra = load_body(a.body)
    extra.pop("model", None)
    if a.url:
        body = {"model": a.model, "url": a.url, **extra}
        answer, _ = call_json("POST", "/v1/stt/create", body, a.sandbox)
    else:
        field = a.field or schema_field(a.model)
        if not field:
            field = "audio"
            log("could not read the model's schema; sending the file as `audio` (OpenAI models take `file`: pass --field file)")
        numbers = [k for k, v in extra.items() if isinstance(v, (int, float)) and not isinstance(v, bool)]
        if numbers:
            log(f"note: a multipart upload sends every field as text, and numbers ({', '.join(numbers)}) may be refused;"
                " if so, send the audio by --url")
        try:
            with open(a.file, "rb") as f:
                content = f.read()
        except OSError as err:
            sys.exit(f"cannot read {a.file}: {err}")
        data, ctype = multipart({"model": a.model, **extra}, field, a.file, content)
        with call("POST", "/v1/stt/create", data, ctype, a.sandbox, timeout=600) as resp:
            answer = json.load(resp)
    ident = answer.get("generation_id") or answer.get("id")
    if not ident:
        print(json.dumps(answer, indent=2))
        sys.exit("The submit answer has no generation_id: see the body above.")
    return str(ident)


def wait_stt(ident: str, a) -> int:
    deadline = time.monotonic() + a.timeout
    failed = 0
    while True:
        try:
            answer, headers = call_json("GET", poll_path(ident), None, a.sandbox, timeout=60, transient_ok=True)
            failed = 0
        except Transient as err:
            failed += 1
            if failed >= 10 or time.monotonic() > deadline:
                log(f"{failed} polls in a row failed ({err}). The job keeps running: poll again with `speech.py poll {ident}`.")
                return 2
            log(f"stt {ident}: poll failed ({err}), asking again")
            time.sleep(min(60, a.interval * failed))
            continue
        status = str(answer.get("status", "")).lower()
        log(f"stt {ident}: {status or 'no status'}")
        if status in SUCCESS:
            if a.out:
                with open(a.out, "w", encoding="utf-8") as f:
                    json.dump(answer, f, indent=2, ensure_ascii=False)
                log(f"saved {a.out}")
            text = transcript_text(answer.get("result"))
            if a.json or text is None:
                print(json.dumps(answer, indent=2, ensure_ascii=False))
                if text is None:
                    log("no transcript in the usual place (result.text or Deepgram's results.channels); see the answer above")
            else:
                print(text)
            if headers.get("x-aimlapi-sandbox") == "true":
                log("note: sandbox answer, a fixed transcript; nothing was charged")
            return 0
        if status and status not in PENDING:
            print(json.dumps(answer, indent=2, ensure_ascii=False))
            log(f"job ended with status {status}: see error in the body above")
            return 1
        if time.monotonic() > deadline:
            log(f"still {status} after {a.timeout}s. The job keeps running: poll again with `speech.py poll {ident}`.")
            return 2
        time.sleep(a.interval)


def cmd_stt(a) -> int:
    if bool(a.url) == bool(a.file):
        sys.exit("give exactly one of --url or --file")
    ident = submit_stt(a)
    log(f"submitted stt {ident}")
    if a.no_wait:
        print(json.dumps({"generation_id": ident}))
        return 0
    return wait_stt(ident, a)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("tts", help="text to speech: POST /v1/tts, save the audio")
    t.add_argument("--body", required=True, help="JSON request body, or @file.json")
    t.add_argument("--out", required=True, help="save the audio here")
    t.add_argument("--timeout", type=float, default=900, help="seconds to wait for the answer (default 900)")

    s = sub.add_parser("stt", help="speech to text: submit, poll, print the transcript")
    s.add_argument("--model", required=True)
    s.add_argument("--url", help="public URL of the audio")
    s.add_argument("--file", help="local audio file to upload")
    s.add_argument("--field", choices=FILE_FIELDS, help="multipart field for --file (default: read from the model's schema)")
    s.add_argument("--body", help="more request fields as JSON, or @file.json")
    s.add_argument("--no-wait", action="store_true")

    q = sub.add_parser("poll", help="poll an STT job you submitted earlier")
    q.add_argument("id")

    for x in (s, q):
        x.add_argument("--interval", type=float, default=5)
        x.add_argument("--timeout", type=float, default=1800, help="seconds to keep polling (default 1800)")
        x.add_argument("--out", help="save the final answer (JSON) here")
        x.add_argument("--json", action="store_true", help="print the whole final answer instead of the transcript")
    for x in (t, s, q):
        x.add_argument("--sandbox", action="store_true", help="free test run: live answer format, no charge")
    a = p.parse_args()

    try:
        if a.cmd == "tts":
            sys.exit(cmd_tts(a))
        if a.cmd == "stt":
            sys.exit(cmd_stt(a))
        sys.exit(wait_stt(a.id, a))
    except (ValueError, OSError) as err:
        sys.exit(f"bad input: {err}")


if __name__ == "__main__":
    main()
