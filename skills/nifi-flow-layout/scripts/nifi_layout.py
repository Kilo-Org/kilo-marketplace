#!/usr/bin/env python3
"""Audit and beautify Apache NiFi canvas layouts.

The script intentionally changes only visual/maintenance metadata:
positions, comments, connection bends, labelIndex, and empty connection names.
It does not edit processor business properties.
"""
from __future__ import annotations

import argparse
import collections
import contextlib
import dataclasses
import json
import math
import os
import re
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests

# Match NiFi frontend CanvasConstants from apache/nifi.  These are not guessed:
# PROCESSOR=350x130, PORT=240x48, PROCESS_GROUP=384x176, FUNNEL=48x48.
# Connection labels are always 240px wide and their height depends on rows.
SIZE = {
    "PROCESSOR": (350.0, 130.0),
    "PROCESS_GROUP": (384.0, 176.0),
    "INPUT_PORT": (240.0, 48.0),
    "OUTPUT_PORT": (240.0, 48.0),
    "FUNNEL": (48.0, 48.0),
}
CONNECTION_LABEL_WIDTH = 240.0
CONNECTION_ROW_HEIGHT = 19.0
CONNECTION_BACKPRESSURE_HEIGHT = 3.0
# Fallback for old call sites; real connection labels use connection_label_size().
LABEL = (CONNECTION_LABEL_WIDTH, CONNECTION_ROW_HEIGHT * 2 + CONNECTION_BACKPRESSURE_HEIGHT)
PAD = 14.0
MAIN_X = {"PROCESSOR": 160.0, "PROCESS_GROUP": 144.0, "INPUT_PORT": 215.0, "OUTPUT_PORT": 215.0, "FUNNEL": 240.0}
MAIN_GAP = {
    ("PROCESS_GROUP", "PROCESS_GROUP"): 36.0,
    ("PROCESSOR", "PROCESS_GROUP"): 36.0,
    ("PROCESS_GROUP", "PROCESSOR"): 20.0,
    ("PROCESSOR", "PROCESSOR"): 20.0,
    # Port-to-processor/processor-to-port gaps should be symmetrical: the queue
    # label has enough air, but the link stays short and readable.
    ("INPUT_PORT", "PROCESSOR"): 8.0,
    # Same visual rule as input -> processor, but output ports need a bit more
    # room because the success label is often taller than it looks in REST data.
    ("PROCESSOR", "OUTPUT_PORT"): 18.0,
    ("PROCESS_GROUP", "OUTPUT_PORT"): 30.0,
    ("INPUT_PORT", "PROCESS_GROUP"): 36.0,
}
ERROR_COLUMN_GAP = 1320.0
BUS_GAP = 300.0
LANE_GAP = 80.0
LABEL_CLEARANCE = 24.0  # canvas-space equivalent of ~12px visual clearance at current NiFi zoom
COMPONENT_CLEARANCE = 18.0
LINE_SPACING = 48.0  # canvas-space equivalent of ~32px visual line spacing
PREFERRED_LANE_SPACING = 64.0  # compact target: enough air without huge empty corridors
# Outside same-column return buses may be visually compact, but their queue label
# is centered on the lane bend.  Keep the lane far enough from the component edge
# so the label itself has clearance; otherwise a 64px lane can still put the
# 240px-wide "Name/Queued" label over the processor/card.
OUTER_LABEL_LANE_GAP = CONNECTION_LABEL_WIDTH / 2.0 + LABEL_CLEARANCE
SIDE_BASE_GAP = 800.0
SIDE_FANIN_GAP = 80.0
SIDE_MAX_GAP = 1460.0

@dataclasses.dataclass
class Rect:
    x: float
    y: float
    w: float
    h: float

    @property
    def left(self) -> float: return self.x
    @property
    def right(self) -> float: return self.x + self.w
    @property
    def top(self) -> float: return self.y
    @property
    def bottom(self) -> float: return self.y + self.h
    @property
    def cx(self) -> float: return self.x + self.w / 2
    @property
    def cy(self) -> float: return self.y + self.h / 2

    def inflate(self, p: float) -> "Rect":
        return Rect(self.x - p, self.y - p, self.w + 2*p, self.h + 2*p)

    def intersects(self, other: "Rect") -> bool:
        return not (self.right <= other.left or self.left >= other.right or self.bottom <= other.top or self.top >= other.bottom)

    def as_dict(self) -> Dict[str, float]:
        return {"x": round(self.x, 3), "y": round(self.y, 3), "w": round(self.w, 3), "h": round(self.h, 3)}

@dataclasses.dataclass
class Node:
    id: str
    kind: str
    name: str
    x: float
    y: float
    comments: str = ""
    revision: int = 0
    raw: Dict[str, Any] = dataclasses.field(default_factory=dict)

    def size(self) -> Tuple[float, float]:
        return SIZE.get(self.kind, SIZE["PROCESSOR"])

    def rect(self) -> Rect:
        w, h = self.size()
        return Rect(self.x, self.y, w, h)

    def with_pos(self, x: float, y: float) -> "Node":
        return dataclasses.replace(self, x=x, y=y)

@dataclasses.dataclass
class Conn:
    id: str
    source_id: str
    dest_id: str
    source_type: str
    dest_type: str
    source_group_id: Optional[str]
    dest_group_id: Optional[str]
    source_name: str
    dest_name: str
    relationships: Tuple[str, ...]
    name: str = ""
    bends: List[Dict[str, float]] = dataclasses.field(default_factory=list)
    label_index: int = 0
    revision: int = 0
    raw: Dict[str, Any] = dataclasses.field(default_factory=dict)

class NiFi:
    def __init__(self, base_url: str, cert: Optional[Tuple[str, str]], token: Optional[str], verify: bool):
        self.base_url = base_url.rstrip("/")
        self.s = requests.Session()
        self.s.verify = verify
        if cert: self.s.cert = cert
        if token: self.s.headers.update({"Authorization": f"Bearer {token}"})
        if not verify:
            requests.packages.urllib3.disable_warnings()  # type: ignore[attr-defined]

    def req(self, method: str, path: str, **kw: Any) -> Any:
        last = None
        for i in range(8):
            try:
                r = self.s.request(method, self.base_url + "/" + path.lstrip("/"), timeout=60, **kw)
                if r.ok:
                    return r.json() if r.content else {}
                last = f"{method} {path} -> {r.status_code}\n{r.text[:2000]}"
                if 400 <= r.status_code < 500:
                    raise RuntimeError(last)
            except Exception as e:  # pragma: no cover - diagnostic retry
                last = repr(e)
                if isinstance(e, RuntimeError) and "-> 4" in str(e):
                    raise
            time.sleep(0.2 + i * 0.2)
        raise RuntimeError(last)

    def flow(self, group_id: str) -> Dict[str, Any]:
        return self.req("GET", f"flow/process-groups/{group_id}")["processGroupFlow"]["flow"]

    def snapshot(self, group_id: str) -> Dict[str, Any]:
        return self.req("GET", f"flow/process-groups/{group_id}")

    def component_state(self, typ: str, cid: str) -> Optional[str]:
        endpoint = self._component_endpoint(typ, cid)
        if not endpoint:
            return None
        try:
            return self.req("GET", endpoint)["component"].get("state")
        except Exception:
            return None

    def queue_count(self, connection_id: str) -> int:
        cur = self.req("GET", f"connections/{connection_id}")
        snap = ((cur.get("status") or {}).get("aggregateSnapshot") or {})
        for key in ("flowFilesQueued", "queuedCount"):
            value = snap.get(key)
            if value is None:
                continue
            if isinstance(value, int):
                return value
            try:
                return int(str(value).replace(",", "").strip())
            except ValueError:
                pass
        queued = snap.get("queued")
        if isinstance(queued, str):
            m = re.match(r"\s*([0-9,]+)\s*/", queued)
            if m:
                return int(m.group(1).replace(",", ""))
        return 0

    def update_processor(self, node: Node, name: Optional[str], comments: Optional[str], x: Optional[float], y: Optional[float]) -> None:
        cur = self.req("GET", f"processors/{node.id}")
        comp: Dict[str, Any] = {"id": node.id}
        if name is not None: comp["name"] = name
        if x is not None and y is not None: comp["position"] = {"x": x, "y": y}
        if comments is not None:
            cfg = dict(cur["component"].get("config") or {})
            cfg["comments"] = comments
            comp["config"] = cfg
        self.req("PUT", f"processors/{node.id}", json={"revision": {"version": cur["revision"]["version"]}, "component": comp})

    def update_process_group(self, node: Node, name: Optional[str], comments: Optional[str], x: Optional[float], y: Optional[float]) -> None:
        cur = self.req("GET", f"process-groups/{node.id}")
        comp: Dict[str, Any] = {"id": node.id}
        if name is not None: comp["name"] = name
        if comments is not None: comp["comments"] = comments
        if x is not None and y is not None: comp["position"] = {"x": x, "y": y}
        self.req("PUT", f"process-groups/{node.id}", json={"revision": {"version": cur["revision"]["version"]}, "component": comp})

    def update_port(self, kind: str, node: Node, name: Optional[str], comments: Optional[str], x: Optional[float], y: Optional[float]) -> None:
        endpoint = "input-ports" if kind == "INPUT_PORT" else "output-ports"
        cur = self.req("GET", f"{endpoint}/{node.id}")
        comp: Dict[str, Any] = {"id": node.id}
        if name is not None: comp["name"] = name
        if comments is not None: comp["comments"] = comments
        if x is not None and y is not None: comp["position"] = {"x": x, "y": y}
        self.req("PUT", f"{endpoint}/{node.id}", json={"revision": {"version": cur["revision"]["version"]}, "component": comp})


    def _component_endpoint(self, typ: str, cid: str) -> Optional[str]:
        if typ == "PROCESSOR": return f"processors/{cid}"
        if typ == "INPUT_PORT": return f"input-ports/{cid}"
        if typ == "OUTPUT_PORT": return f"output-ports/{cid}"
        return None

    def _stop_component_if_running(self, typ: str, cid: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        endpoint = self._component_endpoint(typ, cid)
        if not endpoint:
            return None, None
        cur = self.req("GET", endpoint)
        state = cur["component"].get("state")
        if state == "RUNNING":
            try:
                self.req("PUT", f"{endpoint}/run-status", json={"revision": {"version": cur["revision"]["version"]}, "state": "STOPPED"})
            except Exception:
                # NiFi can close the TLS connection while accepting a run-status
                # change. Verify the actual state before deciding the stop failed;
                # otherwise a later exception can leave a processor stopped.
                cur = self.req("GET", endpoint)
                if cur["component"].get("state") != "STOPPED":
                    raise
            for _ in range(80):
                time.sleep(0.1)
                cur = self.req("GET", endpoint)
                if cur["component"].get("state") == "STOPPED":
                    break
            return endpoint, cur
        return None, None

    def _restart_component(self, endpoint: Optional[str]) -> None:
        if not endpoint:
            return
        cur = self.req("GET", endpoint)
        self.req("PUT", f"{endpoint}/run-status", json={"revision": {"version": cur["revision"]["version"]}, "state": "RUNNING"})

    def _put_connection(self, conn: Conn, bends: List[Dict[str, float]], label_index: int, clear_name: bool = True) -> None:
        cur = self.req("GET", f"connections/{conn.id}")
        # NiFi expects the existing source/destination/relationships to remain present.
        comp: Dict[str, Any] = dict(cur["component"])
        comp["id"] = conn.id
        comp["bends"] = bends
        comp["labelIndex"] = label_index
        if clear_name:
            comp["name"] = ""
        self.req("PUT", f"connections/{conn.id}", json={"revision": {"version": cur["revision"]["version"]}, "component": comp})

    def update_connection(self, conn: Conn, bends: List[Dict[str, float]], label_index: int, clear_name: bool = True) -> Dict[str, Any]:
        """Update a connection without stopping processors unless NiFi requires it.

        The safe default is state-preserving: first try the pure revision update.
        If this NiFi instance rejects connection geometry while endpoints are running,
        stop only the endpoints for this connection, only when its queue is empty, and
        restore exactly the endpoints that were running before the retry.
        """
        before = {
            "source_state": self.component_state(conn.source_type, conn.source_id),
            "destination_state": self.component_state(conn.dest_type, conn.dest_id),
            "queue_count": self.queue_count(conn.id),
            "stopped_for_retry": [],
        }
        try:
            self._put_connection(conn, bends, label_index, clear_name=clear_name)
            before["mode"] = "state_preserving"
            return before
        except Exception as first_error:
            if before["queue_count"]:
                raise RuntimeError(f"connection {conn.id} update rejected and queue is not empty ({before['queue_count']}): {first_error}") from first_error
            stopped: List[Optional[str]] = []
            src_ep, _ = self._stop_component_if_running(conn.source_type, conn.source_id)
            dst_ep, _ = self._stop_component_if_running(conn.dest_type, conn.dest_id)
            stopped.extend([src_ep, dst_ep])
            before["stopped_for_retry"] = [x for x in stopped if x]
            try:
                self._put_connection(conn, bends, label_index, clear_name=clear_name)
                before["mode"] = "stopped_empty_queue_retry"
                return before
            finally:
                # Restart destination first, then source. If one side was already stopped it is ignored.
                for ep in reversed([x for x in stopped if x]):
                    self._restart_component(ep)


@contextlib.contextmanager
def p12_cert_pair(p12_path: Optional[str], passphrase: Optional[str]) -> Iterable[Optional[Tuple[str, str]]]:
    if not p12_path:
        yield None
        return
    try:
        from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat, pkcs12
    except ImportError as e:
        raise RuntimeError("cryptography package is required for --p12 auth") from e
    data = Path(p12_path).read_bytes()
    password_bytes = passphrase.encode() if passphrase else None
    key, cert, _cas = pkcs12.load_key_and_certificates(data, password_bytes)
    if key is None or cert is None:
        raise RuntimeError("--p12 did not contain both a private key and a client certificate")
    cert_file = tempfile.NamedTemporaryFile(suffix=".crt", delete=False)
    key_file = tempfile.NamedTemporaryFile(suffix=".key", delete=False)
    try:
        cert_file.write(cert.public_bytes(Encoding.PEM)); cert_file.close(); os.chmod(cert_file.name, 0o600)
        key_file.write(key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())); key_file.close(); os.chmod(key_file.name, 0o600)
        yield (cert_file.name, key_file.name)
    finally:
        for f in (cert_file.name, key_file.name):
            try: os.unlink(f)
            except OSError: pass

def node_from(entity: Dict[str, Any], kind: str) -> Node:
    c = entity["component"]
    comments = c.get("comments") or (c.get("config") or {}).get("comments") or ""
    return Node(c["id"], kind, c.get("name") or "", c["position"]["x"], c["position"]["y"], comments, entity.get("revision", {}).get("version", 0), entity)

def conn_from(entity: Dict[str, Any]) -> Conn:
    c = entity["component"]
    rel = tuple(c.get("selectedRelationships") or c.get("relationships") or [])
    return Conn(c["id"], c["source"]["id"], c["destination"]["id"], c["source"]["type"], c["destination"]["type"], c.get("sourceGroupId") or c["source"].get("groupId"), c.get("destinationGroupId") or c["destination"].get("groupId"), c["source"].get("name", ""), c["destination"].get("name", ""), rel, c.get("name") or "", list(c.get("bends") or []), int(c.get("labelIndex") or 0), entity.get("revision", {}).get("version", 0), entity)

def parse_group(flow: Dict[str, Any]) -> Tuple[Dict[str, Node], List[Conn]]:
    nodes: Dict[str, Node] = {}
    for key, kind in [("processors", "PROCESSOR"), ("processGroups", "PROCESS_GROUP"), ("inputPorts", "INPUT_PORT"), ("outputPorts", "OUTPUT_PORT"), ("funnels", "FUNNEL")]:
        for e in flow.get(key, []) or []:
            n = node_from(e, kind)
            nodes[n.id] = n
    conns = [conn_from(e) for e in flow.get("connections", []) or []]
    return nodes, conns

def visual_id(conn: Conn, endpoint: str, current_group: str, nodes: Dict[str, Node]) -> str:
    if endpoint == "source":
        eid, gid = conn.source_id, conn.source_group_id
    else:
        eid, gid = conn.dest_id, conn.dest_group_id
    if eid in nodes:
        return eid
    if gid and gid != current_group and gid in nodes:
        return gid
    return eid

def is_errorish(node: Node) -> bool:
    text = f"{node.name} {node.comments}".lower()
    return any(s in text for s in ["ошиб", "error", "failure", "dead-letter", "лог ошибки", "логирует ошиб"])

def strip_number(name: str) -> str:
    return re.sub(r"^\s*\d+(?:\.\d+)*\s+", "", name).strip()

def comment_for(node: Node) -> str:
    if node.comments.strip():
        return node.comments.strip()
    n = strip_number(node.name) or node.kind
    if node.kind == "INPUT_PORT":
        return f"Вход в этот блок. Получает FlowFile от предыдущего шага и передает его дальше без скрытой бизнес-логики."
    if node.kind == "OUTPUT_PORT":
        return f"Выход из этого блока. Передает FlowFile следующему этапу после успешного завершения текущей логики."
    if node.kind == "PROCESS_GROUP":
        return f"Группа объединяет шаги «{n}», чтобы этот участок потока можно было читать и сопровождать отдельно."
    if is_errorish(node):
        return f"Фиксирует ошибочный сценарий для шага «{n}», чтобы сбой был виден в логах и не терялся в очередях."
    return f"Выполняет шаг «{n}» в общем сценарии. Комментарий нужен, чтобы было понятно, зачем объект стоит в потоке."

def classify_main(nodes: Dict[str, Node]) -> Tuple[List[Node], List[Node]]:
    if not nodes:
        return [], []
    xs = sorted(n.x for n in nodes.values())
    base_x = xs[min(len(xs)//2, len(xs)-1)]
    # Main lane is the visually left/central lane; far-right processors are side handlers.
    side: List[Node] = []
    main: List[Node] = []
    for n in nodes.values():
        if n.kind == "PROCESSOR" and n.x > base_x + 430:
            side.append(n)
        else:
            main.append(n)
    main.sort(key=lambda n: (n.y, n.x))
    side.sort(key=lambda n: (n.y, n.x))
    return main, side

def target_layout(nodes: Dict[str, Node], conns: Optional[List[Conn]] = None) -> Dict[str, Tuple[float, float]]:
    main, side = classify_main(nodes)
    result: Dict[str, Tuple[float, float]] = {}
    if not main:
        return result
    # Final output ports are visual sinks.  Keep them after the last main
    # processor/process group even if their previous y-position was slightly
    # above it.  Otherwise a later layout pass can put the output port between
    # two groups and force an ugly side loop for the real final connection.
    if conns:
        incoming: Dict[str, int] = collections.defaultdict(int)
        outgoing: Dict[str, int] = collections.defaultdict(int)
        for c in conns:
            incoming[c.dest_id] += 1
            outgoing[c.source_id] += 1

        def main_order(n: Node) -> Tuple[int, float, float]:
            is_final_output = n.kind == "OUTPUT_PORT" and incoming.get(n.id, 0) > 0 and outgoing.get(n.id, 0) == 0
            return (1 if is_final_output else 0, n.y, n.x)

        main.sort(key=main_order)
    y = 0.0
    prev: Optional[Node] = None
    for i, n in enumerate(main):
        x = MAIN_X.get(n.kind, 160.0)
        if i == 0:
            y = 0.0
        elif prev is not None:
            ph = SIZE.get(prev.kind, SIZE["PROCESSOR"])[1]
            gap = MAIN_GAP.get((prev.kind, n.kind), 8.0)
            y = result[prev.id][1] + ph + LABEL[1] + gap
        result[n.id] = (x, y)
        prev = n
    if side:
        side_incoming: Dict[str, int] = collections.defaultdict(int)
        if conns:
            for c in conns:
                if c.dest_id in {s.id for s in side}:
                    side_incoming[c.dest_id] += 1
        max_fanin = max(side_incoming.values(), default=1)
        # A one-off log processor should stay near the main route. Dense fan-in needs
        # a wider corridor for labels and separate lanes, but not every side column does.
        dynamic_gap = min(SIDE_MAX_GAP, SIDE_BASE_GAP + max(0, max_fanin - 1) * SIDE_FANIN_GAP)
        side_x = MAIN_X["PROCESSOR"] + dynamic_gap
        # Put side handlers beside the nearest main step by original y. This keeps error routes horizontal.
        main_by_y = sorted(main, key=lambda n: n.y)
        used: Dict[float, int] = collections.defaultdict(int)
        for s in side:
            nearest = min(main_by_y, key=lambda m: abs(m.y - s.y)) if main_by_y else s
            sy = result.get(nearest.id, (nearest.x, nearest.y))[1]
            offset = used[sy] * 150.0
            used[sy] += 1
            result[s.id] = (side_x, sy + offset)
    return result

def with_targets(nodes: Dict[str, Node], targets: Dict[str, Tuple[float, float]]) -> Dict[str, Node]:
    return {i: (n.with_pos(*targets[i]) if i in targets else n) for i, n in nodes.items()}

def rects(nodes: Dict[str, Node], exclude: Iterable[str] = ()) -> List[Tuple[str, Rect]]:
    ex = set(exclude)
    return [(i, n.rect().inflate(PAD)) for i, n in nodes.items() if i not in ex]

def rects_actual(nodes: Dict[str, Node], exclude: Iterable[str] = ()) -> List[Tuple[str, Rect]]:
    ex = set(exclude)
    return [(i, n.rect()) for i, n in nodes.items() if i not in ex]

def segment_rect(a: Tuple[float, float], b: Tuple[float, float], thick: float = 2.0) -> Rect:
    x1, y1 = a; x2, y2 = b
    return Rect(min(x1, x2)-thick, min(y1, y2)-thick, abs(x1-x2)+2*thick, abs(y1-y2)+2*thick)

def orthogonal_segment(a: Tuple[float, float], b: Tuple[float, float]) -> Optional[Tuple[str, float, float, float]]:
    """Normalize an orthogonal segment for line-overlap diagnostics."""
    x1, y1 = a; x2, y2 = b
    if abs(x1 - x2) < 1.0 and abs(y1 - y2) >= 1.0:
        return ("v", round((x1 + x2) / 2.0, 1), min(y1, y2), max(y1, y2))
    if abs(y1 - y2) < 1.0 and abs(x1 - x2) >= 1.0:
        return ("h", round((y1 + y2) / 2.0, 1), min(x1, x2), max(x1, x2))
    return None

def segment_overlap_amount(a: Tuple[str, float, float, float], b: Tuple[str, float, float, float]) -> float:
    """Return overlap length for collinear segments; zero means no visual stacking."""
    if a[0] != b[0] or abs(a[1] - b[1]) > 2.0:
        return 0.0
    lo = max(a[2], b[2])
    hi = min(a[3], b[3])
    return max(0.0, hi - lo)

def segment_parallel_overlap(a: Tuple[str, float, float, float], b: Tuple[str, float, float, float]) -> float:
    """Return shared span for same-orientation segments, even on different lanes."""
    if a[0] != b[0]:
        return 0.0
    lo = max(a[2], b[2])
    hi = min(a[3], b[3])
    return max(0.0, hi - lo)

def perpendicular_cross_point(
    a: Tuple[str, float, float, float],
    b: Tuple[str, float, float, float],
    margin: float = 3.0,
) -> Optional[Tuple[float, float]]:
    """Return the X/T crossing point between orthogonal segments, away from endpoints."""
    if a[0] == b[0]:
        return None
    v, h = (a, b) if a[0] == "v" else (b, a)
    x, y = v[1], h[1]
    if h[2] + margin < x < h[3] - margin and v[2] + margin < y < v[3] - margin:
        return (x, y)
    return None

def distinct_route_segment_pair(ca: str, ia: int, cb: str, ib: int) -> bool:
    """Return True when two route segments should be compared as separate wires.

    Adjacent segments of the same connection meet at a bend by design.  But
    non-adjacent segments of the same connection can still create the same
    visual defects as two different connections: a U-turn with parallel lanes
    too close, a loop crossing itself, or a short line sitting on top of a
    previous part of the route.
    """
    return ca != cb or abs(ia - ib) > 1

def route_points(src: Node, dst: Node, bends: List[Dict[str, float]]) -> List[Tuple[float, float]]:
    sr, dr = src.rect(), dst.rect()
    # Endpoint choice follows the dominant direction of the first/last segment.
    if bends:
        first = bends[0]; last = bends[-1]
        if first["x"] > sr.right: start = (sr.right, first["y"])
        elif first["x"] < sr.left: start = (sr.left, first["y"])
        elif first["y"] > sr.bottom: start = (first["x"], sr.bottom)
        elif first["y"] < sr.top: start = (first["x"], sr.top)
        else: start = (sr.cx, sr.bottom if first["y"] >= sr.cy else sr.top)
        if last["x"] > dr.right: end = (dr.right, last["y"])
        elif last["x"] < dr.left: end = (dr.left, last["y"])
        elif last["y"] < dr.top: end = (last["x"], dr.top)
        elif last["y"] > dr.bottom: end = (last["x"], dr.bottom)
        else: end = (dr.cx, dr.bottom)
    else:
        if abs(sr.cx - dr.cx) < abs(sr.cy - dr.cy):
            start = (sr.cx, sr.bottom if dr.cy >= sr.cy else sr.top)
            end = (dr.cx, dr.top if dr.cy >= sr.cy else dr.bottom)
        else:
            start = (sr.right if dr.cx >= sr.cx else sr.left, sr.cy)
            end = (dr.left if dr.cx >= sr.cx else dr.right, dr.cy)
    return [start] + [(p["x"], p["y"]) for p in bends] + [end]

def terminal_is_group_port(typ: str, group_id: Optional[str], current_group: str) -> bool:
    """Mirror NiFi ConnectionRenderer.isGroup(): a port inside another PG is rendered as a group endpoint."""
    return typ in ("INPUT_PORT", "OUTPUT_PORT") and bool(group_id) and group_id != current_group

def connection_label_size(conn: Conn, current_group: str) -> Tuple[float, float]:
    """Return the real NiFi connection label size for route scoring.

    NiFi places the label at a bend point, not at the middle of the segment.
    Height is rows*19+3: optional From, optional To, optional relationship Name, mandatory Queued.
    """
    rows = 1  # Queued is always shown.
    if terminal_is_group_port(conn.source_type, conn.source_group_id, current_group):
        rows += 1
    if terminal_is_group_port(conn.dest_type, conn.dest_group_id, current_group):
        rows += 1
    if conn.relationships:
        rows += 1
    return CONNECTION_LABEL_WIDTH, rows * CONNECTION_ROW_HEIGHT + CONNECTION_BACKPRESSURE_HEIGHT

def label_rect(points: List[Tuple[float, float]], label_index: int, size: Tuple[float, float], bends: Optional[List[Dict[str, float]]] = None) -> Rect:
    if len(points) < 2:
        return Rect(0, 0, *size)
    # NiFi behavior: with bends, labelIndex points to a bend and the label is centered there.
    # Without bends, the label is centered between calculated start/end.
    if bends:
        idx = max(0, min(label_index, len(bends)-1))
        mx, my = bends[idx]["x"], bends[idx]["y"]
    else:
        a, b = points[0], points[-1]
        mx, my = (a[0]+b[0])/2, (a[1]+b[1])/2
    return Rect(mx - size[0]/2, my - size[1]/2, size[0], size[1])

def best_label_index(src: Node, dst: Node, bends: List[Dict[str, float]], nodes: Dict[str, Node], label_size: Tuple[float, float]) -> int:
    """Place the NiFi connection label on the safest visible bend point.

    A common mistake is to score segment midpoints. NiFi does not do that when bends exist: it centers the
    label directly on bends[labelIndex]. We therefore create enough bend candidates and score the actual label box.
    """
    pts = route_points(src, dst, bends)
    if not bends:
        return 0
    scored: List[Tuple[int, float, int]] = []
    for i, bend in enumerate(bends):
        lr = label_rect(pts, i, label_size, bends)
        collisions = 0
        for oid, r in rects_actual(nodes, exclude=[]):
            if lr.intersects(r):
                collisions += 1000
        # Prefer labels on long open lanes and avoid first/last bends too close to component edges.
        nearest_component = min(
            (abs(bend["x"] - r.cx) + abs(bend["y"] - r.cy) for oid, r in rects(nodes, exclude=[])),
            default=9999.0,
        )
        edge_penalty = 25.0 if i in (0, len(bends) - 1) and len(bends) > 1 else 0.0
        scored.append((collisions, edge_penalty - min(nearest_component, 300.0) / 100.0, i))
    scored.sort(key=lambda x: (x[0], x[1], x[2]))
    return scored[0][2]

def best_label_index_avoiding(
    src: Node,
    dst: Node,
    bends: List[Dict[str, float]],
    nodes: Dict[str, Node],
    label_size: Tuple[float, float],
    occupied: List[Rect],
    segment_obstacles: Optional[List[Tuple[str, int, Tuple[str, float, float, float]]]] = None,
    own_connection_id: str = "",
) -> int:
    """Pick a label bend that avoids components, labels, and other route lines.

    NiFi labels are not annotations floating above the canvas; visually they are
    solid blocks.  A route crossing another connection's queued/name label is as
    bad as crossing a processor, so global segment obstacles are part of the
    label scoring.
    """
    if not bends:
        return 0
    pts = route_points(src, dst, bends)
    scored: List[Tuple[int, int, float, int]] = []
    for i, bend in enumerate(bends):
        lr = label_rect(pts, i, label_size, bends)
        hard_collisions = 0
        collisions = 0
        for oid, r in rects_actual(nodes, exclude=[]):
            if lr.intersects(r):
                hard_collisions += 1
        for other in occupied:
            if lr.inflate(18.0).intersects(other.inflate(18.0)):
                hard_collisions += 1
        for cid, _seg_i, seg in segment_obstacles or []:
            if cid == own_connection_id:
                continue
            if seg[0] == "v":
                sr = Rect(seg[1] - 3.0, seg[2], 6.0, seg[3] - seg[2])
            else:
                sr = Rect(seg[2], seg[1] - 3.0, seg[3] - seg[2], 6.0)
            if lr.inflate(LABEL_CLEARANCE).intersects(sr):
                collisions += 90
        # Prefer labels near the source side, not on a shared target bus.  The
        # last bends often sit directly next to target fan-in lanes.
        edge_penalty = 10.0 if i == 0 and len(bends) > 1 else 0.0
        target_bus_penalty = 18.0 if i >= len(bends) - 2 and len(bends) > 2 else 0.0
        scored.append((hard_collisions, collisions, edge_penalty + target_bus_penalty, i))
    scored.sort(key=lambda x: (x[0], x[1], x[2], x[3]))
    return scored[0][3]

def route_cost(src: Node, dst: Node, bends: List[Dict[str, float]], label_index: int, nodes: Dict[str, Node], label_size: Tuple[float, float]) -> Tuple[int, float]:
    if label_index < 0:
        label_index = best_label_index(src, dst, bends, nodes, label_size)
    pts = route_points(src, dst, bends)
    collisions = 0
    for i in range(len(pts)-1):
        if abs(pts[i+1][0] - pts[i][0]) > 1.0 and abs(pts[i+1][1] - pts[i][1]) > 1.0:
            # A diagonal segment usually means the first/last bend was placed on
            # the wrong side of the component. It often hides the arrowhead under
            # a processor, so treat it almost as badly as a real collision.
            collisions += 80
        sr = segment_rect(pts[i], pts[i+1], 3.0)
        for oid, r in rects(nodes, exclude=[src.id, dst.id]):
            if sr.intersects(r):
                collisions += 100
        # A line that is technically outside but flush against a block still
        # reads as “the connection is under/inside the block” in NiFi. Penalize
        # near touches so the scorer prefers another side/lane.
        touch_probe = segment_rect(pts[i], pts[i+1], COMPONENT_CLEARANCE)
        for oid, r in rects_actual(nodes, exclude=[src.id, dst.id]):
            if touch_probe.intersects(r):
                collisions += 20
    lr = label_rect(pts, label_index, label_size, bends)
    # Labels must not sit on any component, including their own source/destination.
    # NiFi renders labels as solid boxes, so touching endpoints still looks like overlap.
    for oid, r in rects(nodes, exclude=[]):
        if lr.intersects(r):
            collisions += 50
    length = sum(abs(pts[i+1][0]-pts[i][0]) + abs(pts[i+1][1]-pts[i][1]) for i in range(len(pts)-1))
    bends_penalty = len(bends) * 20.0
    return collisions, length + bends_penalty

def candidate_routes(src: Node, dst: Node, lane: int = 0) -> List[Tuple[List[Dict[str, float]], int]]:
    sr, dr = src.rect(), dst.rect()
    candidates: List[Tuple[List[Dict[str, float]], int]] = []
    # Direct route. Good for main vertical chain.
    candidates.append(([], -1))
    # Right-side route. Used only if it wins by geometry; no forced giant loops.
    bus_x = max(sr.right, dr.right) + BUS_GAP + lane * LANE_GAP
    y1, y2 = sr.cy, dr.cy
    candidates.append(([{"x": bus_x, "y": y1}, {"x": bus_x, "y": y2}, {"x": dr.left - 60, "y": y2}], -1))
    # Nearest-side local route. This is the normal choice for a branch to a
    # processor on the right: short horizontal, local vertical lane, short entry.
    if sr.cx < dr.cx:
        local_x = max(sr.right + 60.0 + lane * 40.0, dr.left - 90.0 - lane * 40.0)
        local_x = min(local_x, dr.left - 55.0)
    else:
        local_x = min(sr.left - 60.0 - lane * 40.0, dr.right + 90.0 + lane * 40.0)
        local_x = max(local_x, dr.right + 55.0)
    candidates.append(([{"x": local_x, "y": sr.cy}, {"x": local_x, "y": dr.cy}], -1))
    # Left-side route, useful for output ports and crowded targets.
    left_x = min(sr.left, dr.left) - 180 - lane * LANE_GAP
    low_y = max(sr.bottom, dr.bottom) + 70 + lane * 36
    candidates.append(([{"x": left_x, "y": sr.cy}, {"x": left_x, "y": low_y}, {"x": dr.left - 40, "y": low_y}, {"x": dr.left - 40, "y": dr.cy}], -1))
    # Simple doglegs.
    mid_y = (sr.cy + dr.cy) / 2
    candidates.append(([{"x": sr.cx, "y": mid_y}, {"x": dr.cx, "y": mid_y}], -1))
    mid_x = (sr.cx + dr.cx) / 2
    candidates.append(([{"x": mid_x, "y": sr.cy}, {"x": mid_x, "y": dr.cy}], -1))
    return candidates

def choose_route(src: Node, dst: Node, nodes: Dict[str, Node], label_size: Tuple[float, float], lane: int = 0) -> Tuple[List[Dict[str, float]], int]:
    scored = []
    for bends, li in candidate_routes(src, dst, lane):
        chosen_li = best_label_index(src, dst, bends, nodes, label_size) if li < 0 else li
        scored.append((route_cost(src, dst, bends, chosen_li, nodes, label_size), bends, chosen_li))
    scored.sort(key=lambda x: (x[0][0], x[0][1]))
    return scored[0][1], scored[0][2]

def old_bottom_output_route(src: Node, dst: Node, lane: int, total: int = 1) -> List[Dict[str, float]]:
    sr, dr = src.rect(), dst.rect()
    entry_x, entry_y = edge_slot(dr, "bottom", lane, total)
    source_x, _ = source_exit_point(src, "bottom", lane, total)
    lane_y = max(sr.bottom, dr.bottom) + 68.0 + lane * 46.0
    if sr.cx > dr.cx + 400.0:
        return [{"x": source_x, "y": lane_y}, {"x": entry_x, "y": lane_y}, {"x": entry_x, "y": entry_y}]
    if sr.cx > dr.cx + 120.0:
        lane_x = max(sr.right, dr.right) + 120.0 + lane * LANE_GAP
    else:
        lane_x = min(sr.left, dr.left) - 160.0 - lane * LANE_GAP
    return [{"x": lane_x, "y": sr.cy}, {"x": lane_x, "y": lane_y}, {"x": entry_x, "y": lane_y}, {"x": entry_x, "y": entry_y}]

def side_processor_to_output_route(src: Node, dst: Node, lane: int, total: int = 1) -> List[Dict[str, float]]:
    """Route a side processor into an output port without cutting through the main corridor.

    Common NiFi layout: main lane on the left, log/error processor on the right,
    output port below the main lane.  The readable route leaves the side processor
    from bottom/right, travels below nearby blocks, and enters the output port
    from the right/bottom.  This avoids the old center dogleg where the connection
    label sat under another processor or covered the arrowhead.
    """
    sr, dr = src.rect(), dst.rect()
    total = max(1, total)
    # Prefer the output centerline when it is already below the side processor.
    # This removes the tiny extra vertical dogleg next to the output port.
    lane_y = dr.cy if dr.cy >= sr.bottom + 38.0 else max(sr.bottom, dr.bottom) + 76.0 + lane * 44.0
    # Use a right-side local drop if the source is to the right of the output.
    # The first bend must be OUTSIDE the source rectangle. If it is inside the
    # processor width, NiFi draws a diagonal from the bottom center and it looks
    # as if the connection goes under the block.
    if sr.cx > dr.cx + 160.0:
        # Prefer a compact bottom/right return: down from the handler, then
        # straight into the output port from the right.  The first bend shares
        # the source center x, so NiFi draws a clean vertical exit instead of a
        # diagonal segment hidden by the processor.
        label_lane_y = lane_y
        entry_x = dr.right + 48.0
        if abs(label_lane_y - dr.cy) < 1.0:
            return [
                {"x": sr.cx, "y": dr.cy},
                {"x": entry_x, "y": dr.cy},
            ]
        return [
            {"x": sr.cx, "y": label_lane_y},
            {"x": entry_x, "y": label_lane_y},
            {"x": entry_x, "y": dr.cy},
        ]
    # Symmetric fallback when the side processor is left of the output.
    label_lane_y = lane_y
    entry_x = dr.left - 48.0
    if abs(label_lane_y - dr.cy) < 1.0:
        return [
            {"x": sr.cx, "y": dr.cy},
            {"x": entry_x, "y": dr.cy},
        ]
    return [
        {"x": sr.cx, "y": label_lane_y},
        {"x": entry_x, "y": label_lane_y},
        {"x": entry_x, "y": dr.cy},
    ]

def route_to_output(src: Node, dst: Node, nodes: Dict[str, Node], label_size: Tuple[float, float], lane: int, total: int = 1) -> Tuple[List[Dict[str, float]], int]:
    sr, dr = src.rect(), dst.rect()
    if sr.cx > dr.cx + 300.0:
        # A side/error handler returning to a bottom output port is clearer when
        # it leaves from the outside and comes back below the blocks. Scoring by
        # length alone used to choose a shorter left-side route whose vertical
        # segment sat between queue labels and looked like a hidden crossing.
        bends = side_processor_to_output_route(src, dst, lane, total)
        return bends, best_label_index(src, dst, bends, nodes, label_size)
    # Output ports are small, so a long bottom loop often looks worse than a
    # short side entry. Try both: shortest local side route and bottom-finish
    # route, then keep the one that does not cross intermediate processors.
    side = branch_target_side(src, dst)
    candidates: List[List[Dict[str, float]]] = []
    side_bends, _ = route_to_side(src, dst, label_size, lane, total, side, nodes)
    candidates.append(side_bends)
    candidates.append(old_bottom_output_route(src, dst, lane, total))
    # Prefer this for log/error side processors returning to a bottom output.
    # It prevents center-corridor lines from touching blocks or hiding arrowheads.
    candidates.append(side_processor_to_output_route(src, dst, lane, total))
    # If the output is left/right of the source, also try direct side entry on that side.
    if abs(sr.cy - dr.cy) < 160.0:
        candidates.append([])
    scored: List[Tuple[Tuple[int, float], List[Dict[str, float]], int]] = []
    for bends in candidates:
        li = best_label_index(src, dst, bends, nodes, label_size) if bends else 0
        scored.append((route_cost(src, dst, bends, li, nodes, label_size), bends, li))
    scored.sort(key=lambda x: (x[0][0], x[0][1]))
    return scored[0][1], scored[0][2]

def branch_target_side(src: Node, dst: Node) -> str:
    """Choose the target side that makes the branch shortest and least surprising.

    This is deliberately global, not “always enter the left side”.  NiFi components can be
    entered from any side; the readable choice depends on where the source sits.
    """
    sr, dr = src.rect(), dst.rect()
    if sr.right <= dr.left:
        return "left"
    if dr.right <= sr.left:
        return "right"
    if sr.bottom <= dr.top:
        return "top"
    if dr.bottom <= sr.top:
        return "bottom"
    dx = dr.cx - sr.cx
    dy = dr.cy - sr.cy
    if abs(dx) >= abs(dy):
        return "left" if dx >= 0 else "right"
    return "top" if dy >= 0 else "bottom"


def dense_fanin_target_side(src: Node, dst: Node) -> str:
    """Pick different target sides when many branches enter one processor.

    A single processor edge cannot show 6-10 arrowheads clearly; NiFi's 130px
    height makes the slots too close.  Split dense fan-in by source position:
    above sources enter from the top, below sources enter from the bottom, and
    only same-row sources use the nearest side.
    """
    sr, dr = src.rect(), dst.rect()
    if abs(sr.cx - dr.cx) > 260.0:
        # Split a crowded side processor across both vertical edges.  A 130px
        # processor cannot show many arrowheads on one side; using left for
        # upper sources and right for lower sources creates two readable combs.
        if sr.cx < dr.cx:
            return "left" if sr.cy <= dr.cy else "right"
        return "right" if sr.cy <= dr.cy else "left"
    return "top" if sr.cy < dr.cy else "bottom"

def edge_slot(rect: Rect, side: str, lane: int, total: int) -> Tuple[float, float]:
    """Return a distinct anchor point on the chosen target edge.

    Multiple incoming connections to the same object must not collapse into the same
    arrowhead.  Slots are ordered by source position, so top sources usually enter upper
    target slots and lines do not cross each other.
    """
    total = max(1, total)
    lane = max(0, min(lane, total - 1))
    if side in ("left", "right"):
        margin_top = 26.0
        margin_bottom = 18.0
        usable = max(1.0, rect.h - margin_top - margin_bottom)
        y = rect.top + margin_top + usable * (lane + 1) / (total + 1)
        x = rect.left - 48.0 if side == "left" else rect.right + 48.0
        return x, y
    margin_left = 30.0
    margin_right = 30.0
    usable = max(1.0, rect.w - margin_left - margin_right)
    x = rect.left + margin_left + usable * (lane + 1) / (total + 1)
    y = rect.top - 48.0 if side == "top" else rect.bottom + 48.0
    return x, y

def source_exit_point(src: Node, side: str, lane: int, total: int) -> Tuple[float, float]:
    """Spread exits too, so a processor with several branches does not create one thick line."""
    sr = src.rect()
    total = max(1, total)
    lane = max(0, min(lane, total - 1))
    if side == "left":
        # Target is to the left, so leave source through its left side.
        margin_top, margin_bottom = 26.0, 18.0
        y = sr.top + margin_top + max(1.0, sr.h - margin_top - margin_bottom) * (lane + 1) / (total + 1)
        return sr.left - 48.0, y
    if side == "right":
        margin_top, margin_bottom = 26.0, 18.0
        y = sr.top + margin_top + max(1.0, sr.h - margin_top - margin_bottom) * (lane + 1) / (total + 1)
        return sr.right + 48.0, y
    if side == "top":
        margin_left, margin_right = 30.0, 30.0
        x = sr.left + margin_left + max(1.0, sr.w - margin_left - margin_right) * (lane + 1) / (total + 1)
        return x, sr.top - 48.0
    margin_left, margin_right = 30.0, 30.0
    x = sr.left + margin_left + max(1.0, sr.w - margin_left - margin_right) * (lane + 1) / (total + 1)
    return x, sr.bottom + 48.0

def spread_coord(a: float, b: float, lane: int, total: int, min_gap: float = 60.0) -> float:
    """Pick a lane coordinate between two edges; fall back outside if the corridor is narrow."""
    lo, hi = min(a, b), max(a, b)
    if hi - lo >= min_gap * 2:
        return lo + (hi - lo) * (lane + 1) / (max(1, total) + 1)
    # No real corridor: create parallel outside lanes instead of stacking one line.
    mid = (a + b) / 2.0
    return mid + (lane - (max(1, total) - 1) / 2.0) * 44.0


def find_clear_horizontal_lane(
    nodes: Optional[Dict[str, Node]],
    x1: float,
    x2: float,
    preferred_y: float,
    y_min: float,
    y_max: float,
    exclude: Iterable[str],
    step: float = 8.0,
) -> float:
    """Find a horizontal lane that does not run through components.

    Handler-return routes often need to cross from a side processor back to the
    main lane.  A fixed y-coordinate can cut through an intermediate processor,
    so scan the vertical gap and choose the closest clear lane to the preferred
    position.
    """
    if nodes is None or y_max <= y_min:
        return preferred_y
    lo, hi = min(x1, x2), max(x1, x2)
    candidates = [preferred_y]
    y = y_min
    while y <= y_max:
        candidates.append(y)
        y += step
    candidates = sorted(set(round(c, 3) for c in candidates if y_min <= c <= y_max), key=lambda yy: abs(yy - preferred_y))
    for yy in candidates:
        probe = segment_rect((lo, yy), (hi, yy), 6.0)
        blocked = False
        for oid, r in rects(nodes, exclude=exclude):
            if probe.intersects(r):
                blocked = True
                break
        if not blocked:
            return yy
    return preferred_y

def route_to_side(
    src: Node,
    dst: Node,
    label_size: Tuple[float, float],
    lane: int = 0,
    total: int = 1,
    target_side: Optional[str] = None,
    nodes: Optional[Dict[str, Node]] = None,
) -> Tuple[List[Dict[str, float]], int]:
    sr, dr = src.rect(), dst.rect()
    side = target_side or branch_target_side(src, dst)
    if total <= 1 and side in ("left", "right"):
        # A single local branch does not need an artificial dogleg. Without bends,
        # NiFi centers the label on the straight segment; this is shorter and cleaner.
        if abs(sr.cy - dr.cy) < max(70.0, label_size[1] + 30.0):
            return [], 0
    entry_x, entry_y = edge_slot(dr, side, lane, total)
    # Source exits toward the open corridor, not blindly from the opposite side
    # of the target.  For example, a left-lane processor that enters a target
    # through the target's right edge must still leave through its own right edge.
    if side in ("left", "right"):
        source_side = "right" if sr.cx < dr.cx else "left"
    else:
        source_side = {"top": "bottom", "bottom": "top"}[side]
    # For dense fan-in we sometimes enter the target from top/bottom even when
    # sources are in the left main lane.  In that geometry the clean route is to
    # leave the source sideways into the corridor, then go vertically into the
    # target edge slot; exiting from source bottom/top would cut through the next
    # main processor.
    if side in ("top", "bottom") and abs(sr.cx - dr.cx) > 260.0:
        lateral_side = "right" if sr.cx < dr.cx else "left"
        exit_x, exit_y = source_exit_point(src, lateral_side, lane, total)
        # Keep the vertical drop/rise close to the target, not in the main lane.
        lane_x = entry_x
        return [
            {"x": exit_x, "y": exit_y},
            {"x": lane_x, "y": exit_y},
            {"x": lane_x, "y": entry_y},
        ], -1
    exit_x, exit_y = source_exit_point(src, source_side, lane, total)

    if side in ("left", "right"):
        # Special case: a right-column handler returns to a lower main-lane
        # processor (or symmetric left-column return). If we exit through the
        # side facing the main lane, the return line often reuses the same short
        # segment as incoming failure routes and becomes a bundled fan-in/fan-out.
        # Drop from the bottom first, then enter the lower target from its side.
        if side == "right" and sr.cx > dr.cx + 240.0 and dr.top > sr.bottom + 35.0:
            # A right-column handler returning to a lower main-lane processor
            # should not drop straight down from the handler centerline: if
            # another right-column processor sits below it, NiFi draws the first
            # vertical segment through that processor.  Leave from the handler's
            # left edge, travel in the open middle corridor, then enter the
            # lower main-lane target from the right.  This fixes the visual
            # "line over processor" defect seen in PUIG 30.30/30.70 side
            # handlers without sending the return through main queue labels.
            right_entry_x, right_entry_y = edge_slot(dr, "right", lane, total)
            exit_x, exit_y = source_exit_point(src, "left", lane, total)
            min_corridor_x = dr.right + label_size[0] + 120.0 + lane * 56.0
            max_corridor_x = sr.left - label_size[0] - 120.0 - lane * 24.0
            if max_corridor_x >= min_corridor_x + 40.0:
                corridor_x = spread_coord(min_corridor_x, max_corridor_x, lane, total, min_gap=50.0)
            else:
                corridor_x = max(dr.right + 300.0 + lane * 64.0, right_entry_x + 220.0 + lane * 64.0)
            return [
                {"x": exit_x, "y": exit_y},
                {"x": corridor_x, "y": exit_y},
                {"x": corridor_x, "y": right_entry_y},
                {"x": right_entry_x, "y": right_entry_y},
            ], -1
        # Horizontal branch: source -> unique vertical lane -> unique target slot.
        label_half = label_size[0] / 2.0
        if side == "left":
            # Normal left-edge fan-in from a left main lane uses the corridor
            # between source and target. If the source is on the other side, go
            # around the target's outside instead of crossing the processor.
            if sr.cx < dr.cx:
                # Reserve a label pocket next to the source and move the shared
                # vertical bus far enough to the right so it does not pass
                # through that label.
                label_x = sr.right + label_half + 32.0
                safe_left = sr.right + label_size[0] + 110.0 + lane * 16.0
                safe_right = dr.left - label_half - 34.0
                lane_x = spread_coord(safe_left, safe_right, lane, total, min_gap=40.0)
                lane_x = min(lane_x, dr.left - 54.0)
                lane_x = max(lane_x, safe_left) if sr.right < dr.left else lane_x
            else:
                lane_x = dr.left - label_half - 70.0 - lane * LANE_GAP
                label_x = sr.left - label_half - 32.0
        else:
            if sr.cx < dr.cx:
                lane_x = dr.right + label_half + 70.0 + lane * LANE_GAP
                label_x = sr.right + label_half + 32.0
            else:
                label_x = sr.left - label_half - 32.0
                safe_left = dr.right + label_half + 34.0
                safe_right = sr.left - label_size[0] - 110.0 - lane * 16.0
                lane_x = spread_coord(safe_left, safe_right, lane, total, min_gap=40.0)
                lane_x = max(lane_x, dr.right + 54.0)
                lane_x = min(lane_x, safe_right) if dr.right < sr.left else lane_x
        bends = [
            {"x": exit_x, "y": exit_y},
            {"x": label_x, "y": exit_y},
            {"x": lane_x, "y": exit_y},
            {"x": lane_x, "y": entry_y},
            {"x": entry_x, "y": entry_y},
        ]
        return bends, 1

    # Vertical branch: source -> unique horizontal lane -> unique target slot.
    if side == "top":
        lane_y = spread_coord(sr.bottom + 58.0, dr.top - 58.0, lane, total, min_gap=100.0)
        lane_y = min(lane_y, dr.top - 54.0)
        lane_y = max(lane_y, sr.bottom + 54.0) if sr.bottom < dr.top else lane_y
    else:
        lane_y = spread_coord(dr.bottom + 58.0, sr.top - 58.0, lane, total, min_gap=100.0)
        lane_y = max(lane_y, dr.bottom + 54.0)
        lane_y = min(lane_y, sr.top - 54.0) if dr.bottom < sr.top else lane_y
    bends = [
        {"x": exit_x, "y": exit_y},
        {"x": exit_x, "y": lane_y},
        {"x": entry_x, "y": lane_y},
        {"x": entry_x, "y": entry_y},
    ]
    return bends, -1


def route_has_component_hit(src: Node, dst: Node, bends: List[Dict[str, float]], nodes: Dict[str, Node], clearance: float = 3.0) -> bool:
    """Return True when a candidate route visibly crosses another component.

    This is used before selecting an alternate target side.  A side may look
    better geometrically, but if any segment crosses a processor/port/group, the
    route must use another side instead of producing a hidden line under a block.
    """
    pts = route_points(src, dst, bends)
    for i in range(len(pts) - 1):
        seg = segment_rect(pts[i], pts[i + 1], clearance)
        for oid, r in rects_actual(nodes, exclude=[src.id, dst.id]):
            if seg.intersects(r.inflate(2.0)):
                return True
    return False


def clear_same_column_route(src: Node, dst: Node, nodes: Dict[str, Node]) -> bool:
    """Return True for a short/medium vertical side-chain route with no blocker.

    In NiFi, two right-column error handlers stacked vertically are usually most
    readable as a direct vertical connection.  A scored dogleg can accidentally
    run down the side of the handler below it, creating the visible "line over
    processor" defect.
    """
    sr, dr = src.rect(), dst.rect()
    if abs(sr.cx - dr.cx) > 80.0:
        return False
    y1, y2 = (sr.bottom, dr.top) if sr.cy <= dr.cy else (dr.bottom, sr.top)
    if y2 < y1:
        return False
    if y2 - y1 < 28.0:
        return False
    x = (sr.cx + dr.cx) / 2.0
    probe = segment_rect((x, y1), (x, y2), 8.0)
    for oid, r in rects_actual(nodes, exclude=[src.id, dst.id]):
        if probe.intersects(r.inflate(4.0)):
            return False
    return True

def same_column_blocked(src: Node, dst: Node, nodes: Dict[str, Node]) -> bool:
    """Return True when a direct same-column route would cross an intermediate component."""
    sr, dr = src.rect(), dst.rect()
    if abs(sr.cx - dr.cx) > 100.0:
        return False
    y1, y2 = (sr.bottom, dr.top) if sr.cy <= dr.cy else (dr.bottom, sr.top)
    if y2 <= y1:
        return False
    probe = segment_rect(((sr.cx + dr.cx) / 2.0, y1), ((sr.cx + dr.cx) / 2.0, y2), COMPONENT_CLEARANCE)
    for oid, r in rects_actual(nodes, exclude=[src.id, dst.id]):
        if probe.intersects(r.inflate(2.0)):
            return True
    return False

def same_column_around_route(src: Node, dst: Node, nodes: Dict[str, Node], lane: int = 0, total: int = 1) -> Tuple[List[Dict[str, float]], int]:
    """Route same-column blocked chains outside their column instead of through central buses.

    If two right-column handlers have another right-column handler between them,
    routing around the left side sends the line into dense main/side fan-in
    corridors.  The readable shape goes around the outside of that column.
    """
    sr, dr = src.rect(), dst.rect()
    side = "right" if sr.cx >= MAIN_X["PROCESSOR"] + 700.0 else "left"
    exit_x, exit_y = source_exit_point(src, side, lane, total)
    entry_x, entry_y = edge_slot(dr, side, lane, total)
    blockers = [
        n.rect()
        for n in nodes.values()
        if n.id not in (src.id, dst.id)
        and min(sr.cy, dr.cy) - 80.0 <= n.rect().cy <= max(sr.cy, dr.cy) + 80.0
        and abs(n.rect().cx - sr.cx) < 220.0
    ]
    if side == "right":
        component_edge = max([sr.right, dr.right] + [r.right for r in blockers])
        anchor_edge = max(entry_x, exit_x)
        lane_x = max(
            component_edge + OUTER_LABEL_LANE_GAP,
            anchor_edge + PREFERRED_LANE_SPACING + lane * PREFERRED_LANE_SPACING,
        )
    else:
        component_edge = min([sr.left, dr.left] + [r.left for r in blockers])
        anchor_edge = min(entry_x, exit_x)
        lane_x = min(
            component_edge - OUTER_LABEL_LANE_GAP,
            anchor_edge - PREFERRED_LANE_SPACING - lane * PREFERRED_LANE_SPACING,
        )
    bends = [
        {"x": exit_x, "y": exit_y},
        {"x": lane_x, "y": exit_y},
        {"x": lane_x, "y": entry_y},
        {"x": entry_x, "y": entry_y},
    ]
    return bends, 1


def label_clearance_rect(seg: Tuple[str, float, float, float]) -> Rect:
    if seg[0] == "v":
        return Rect(seg[1] - 3.0, seg[2], 6.0, seg[3] - seg[2])
    return Rect(seg[2], seg[1] - 3.0, seg[3] - seg[2], 6.0)


def nudge_segment_coordinate(
    bends: List[Dict[str, float]],
    pts: List[Tuple[float, float]],
    segment_index: int,
    orientation: str,
    new_coord: float,
) -> bool:
    """Move a whole collinear run by changing its bend coordinates.

    A route may represent one straight lane as several adjacent segments because
    extra bends were inserted for label anchors.  Moving only one segment in that
    run creates diagonal neighbors.  Instead, expand to the full same-orientation
    run and move every bend that belongs to it.
    """
    if not bends:
        return False
    run_start = segment_index
    run_end = segment_index
    while run_start > 0:
        prev = orthogonal_segment(pts[run_start - 1], pts[run_start])
        if not prev or prev[0] != orientation:
            break
        run_start -= 1
    while run_end + 1 < len(pts) - 1:
        nxt = orthogonal_segment(pts[run_end + 1], pts[run_end + 2])
        if not nxt or nxt[0] != orientation:
            break
        run_end += 1
    key = "x" if orientation == "v" else "y"
    changed = False
    # Segment run [run_start..run_end] uses route points [run_start..run_end+1].
    # Route point 0 is source perimeter and len(pts)-1 is destination perimeter;
    # route point i maps to bends[i-1] for internal points.
    for point_i in range(run_start, run_end + 2):
        bend_i = point_i - 1
        if 0 <= bend_i < len(bends):
            if abs(bends[bend_i][key] - new_coord) > 0.1:
                bends[bend_i] = dict(bends[bend_i])
                bends[bend_i][key] = new_coord
                changed = True
    return changed


def nudge_routes_away_from_labels(
    group_id: str,
    nodes: Dict[str, Node],
    conns: List[Conn],
    routed: Dict[str, Tuple[List[Dict[str, float]], int]],
) -> None:
    """Create small route offsets so lines keep a visible gap from queued labels.

    The earlier pass packed labels, but a neighboring route can still skim the
    label border by a few pixels.  This pass treats every label inflated by the
    conservative canvas-space clearance as an obstacle and nudges the offending segment coordinate to
    the nearest side of that inflated label.  It only edits existing bends and is
    intentionally conservative: if a route has no bends, it leaves the main spine
    untouched.
    """
    for _ in range(4):
        labels: List[Tuple[str, Rect]] = []
        for c in conns:
            sid = visual_id(c, "source", group_id, nodes)
            did = visual_id(c, "dest", group_id, nodes)
            if sid not in nodes or did not in nodes:
                continue
            bends, li = routed.get(c.id, ([], 0))
            pts = route_points(nodes[sid], nodes[did], bends)
            labels.append((c.id, label_rect(pts, li, connection_label_size(c, group_id), bends)))
        changed_any = False
        for c in conns:
            sid = visual_id(c, "source", group_id, nodes)
            did = visual_id(c, "dest", group_id, nodes)
            if sid not in nodes or did not in nodes:
                continue
            bends, li = routed.get(c.id, ([], 0))
            if not bends:
                continue
            bends = [dict(b) for b in bends]
            pts = route_points(nodes[sid], nodes[did], bends)
            for seg_i in range(len(pts) - 1):
                norm = orthogonal_segment(pts[seg_i], pts[seg_i + 1])
                if not norm or (norm[3] - norm[2]) <= 12.0:
                    continue
                seg_rect = label_clearance_rect(norm)
                for lid, lr in labels:
                    if lid == c.id:
                        continue
                    inflated = lr.inflate(LABEL_CLEARANCE)
                    if not seg_rect.intersects(inflated):
                        continue
                    if norm[0] == "v":
                        left = inflated.left - 4.0
                        right = inflated.right + 4.0
                        new_coord = left if abs(norm[1] - left) <= abs(norm[1] - right) else right
                    else:
                        above = inflated.top - 4.0
                        below = inflated.bottom + 4.0
                        new_coord = above if abs(norm[1] - above) <= abs(norm[1] - below) else below
                    if nudge_segment_coordinate(bends, pts, seg_i, norm[0], new_coord):
                        changed_any = True
                        routed[c.id] = (bends, li)
                        pts = route_points(nodes[sid], nodes[did], bends)
                    break
        if not changed_any:
            return

def collect_route_segments(
    group_id: str,
    nodes: Dict[str, Node],
    conns: List[Conn],
    routed: Dict[str, Tuple[List[Dict[str, float]], int]],
    min_len: float = 12.0,
) -> List[Tuple[str, int, Tuple[str, float, float, float]]]:
    segments: List[Tuple[str, int, Tuple[str, float, float, float]]] = []
    for c in conns:
        sid = visual_id(c, "source", group_id, nodes)
        did = visual_id(c, "dest", group_id, nodes)
        if sid not in nodes or did not in nodes:
            continue
        bends, _li = routed.get(c.id, ([], 0))
        pts = route_points(nodes[sid], nodes[did], bends)
        for i in range(len(pts) - 1):
            norm = orthogonal_segment(pts[i], pts[i + 1])
            if norm and (norm[3] - norm[2]) > min_len:
                segments.append((c.id, i, norm))
    return segments

def route_component_or_diagonal_hit(
    group_id: str,
    nodes: Dict[str, Node],
    conn: Conn,
    bends: List[Dict[str, float]],
    clearance: float = 6.0,
) -> bool:
    sid = visual_id(conn, "source", group_id, nodes)
    did = visual_id(conn, "dest", group_id, nodes)
    if sid not in nodes or did not in nodes:
        return False
    pts = route_points(nodes[sid], nodes[did], bends)
    for i in range(len(pts) - 1):
        if abs(pts[i + 1][0] - pts[i][0]) > 1.0 and abs(pts[i + 1][1] - pts[i][1]) > 1.0:
            return True
        seg = segment_rect(pts[i], pts[i + 1], clearance)
        for oid, r in rects_actual(nodes, exclude=[sid, did]):
            if seg.intersects(r.inflate(2.0)):
                return True
    return False

def nudge_routes_for_line_clearance(
    group_id: str,
    nodes: Dict[str, Node],
    conns: List[Conn],
    routed: Dict[str, Tuple[List[Dict[str, float]], int]],
) -> None:
    """Widen dense route corridors and eliminate line-to-line X/T crossings.

    The first clearance pass only reported close parallel lanes.  Real NiFi
    review showed that lanes 1-2 grid cells apart still read as one thick wire,
    and a vertical bus crossing a horizontal branch creates an ambiguous
    unconnected T/X.  This pass edits existing bends only, nudging the whole
    collinear run to keep orthogonal routes and avoid diagonal artifacts.
    """
    conn_by_id = {c.id: c for c in conns}

    def try_move(cid: str, seg_i: int, orientation: str, options: List[float]) -> bool:
        conn = conn_by_id.get(cid)
        if not conn:
            return False
        sid = visual_id(conn, "source", group_id, nodes)
        did = visual_id(conn, "dest", group_id, nodes)
        if sid not in nodes or did not in nodes:
            return False
        bends, li = routed.get(cid, ([], 0))
        if not bends:
            return False
        pts = route_points(nodes[sid], nodes[did], bends)
        current = orthogonal_segment(pts[seg_i], pts[seg_i + 1])
        if not current or current[0] != orientation:
            return False
        scored: List[Tuple[float, List[Dict[str, float]]]] = []
        for new_coord in options:
            trial = [dict(b) for b in bends]
            if not nudge_segment_coordinate(trial, pts, seg_i, orientation, new_coord):
                continue
            if route_component_or_diagonal_hit(group_id, nodes, conn, trial, clearance=COMPONENT_CLEARANCE):
                continue
            trial_pts = route_points(nodes[sid], nodes[did], trial)
            length = sum(abs(trial_pts[i + 1][0] - trial_pts[i][0]) + abs(trial_pts[i + 1][1] - trial_pts[i][1]) for i in range(len(trial_pts) - 1))
            scored.append((abs(new_coord - current[1]) + length / 10000.0, trial))
        if not scored:
            return False
        scored.sort(key=lambda item: item[0])
        routed[cid] = (scored[0][1], li)
        return True

    for _ in range(16):
        segs = collect_route_segments(group_id, nodes, conns, routed, min_len=18.0)
        changed = False
        for i in range(len(segs)):
            ca, ia, sa = segs[i]
            for j in range(i + 1, len(segs)):
                cb, ib, sb = segs[j]
                if not distinct_route_segment_pair(ca, ia, cb, ib):
                    continue
                cross = perpendicular_cross_point(sa, sb)
                if cross:
                    v_id, v_i, v_seg = (ca, ia, sa) if sa[0] == "v" else (cb, ib, sb)
                    h_id, h_i, h_seg = (ca, ia, sa) if sa[0] == "h" else (cb, ib, sb)
                    # First try moving the vertical bus outside the horizontal
                    # branch.  If that bus is constrained by endpoints, move the
                    # horizontal branch outside the vertical bus span.
                    if try_move(v_id, v_i, "v", [h_seg[2] - LINE_SPACING, h_seg[3] + LINE_SPACING]) or try_move(h_id, h_i, "h", [v_seg[2] - LINE_SPACING, v_seg[3] + LINE_SPACING]):
                        changed = True
                        break
                parallel = segment_parallel_overlap(sa, sb)
                if sa[0] == sb[0] and parallel > 35.0:
                    distance = abs(sa[1] - sb[1])
                    if distance < LINE_SPACING:
                        # Nudge the later connection away from the earlier
                        # lane. Exact overlaps get both left/right candidates.
                        if sa[0] == "v":
                            sign = -1.0 if sb[1] <= sa[1] else 1.0
                        else:
                            sign = -1.0 if sb[1] <= sa[1] else 1.0
                        target = sa[1] + sign * LINE_SPACING
                        options = [target, sa[1] - LINE_SPACING, sa[1] + LINE_SPACING]
                        if try_move(cb, ib, sb[0], options) or try_move(ca, ia, sa[0], [sb[1] - LINE_SPACING, sb[1] + LINE_SPACING]):
                            changed = True
                            break
            if changed:
                break
        if not changed:
            return

def far_side_entry_is_clear(src: Node, dst: Node, nodes: Dict[str, Node], side: str, label_size: Tuple[float, float], total: int) -> bool:
    """Check the real candidate path before choosing a far-side fan-in entry.

    Dense fan-in often benefits from sending lower sources to the target's right
    edge, but only if the whole candidate route is clear.  This prevents the
    common failure where a lower side-handler sits under the error processor and
    the far-side horizontal segment crosses that handler or its label corridor.
    """
    if side not in ("left", "right"):
        return True
    bends, _li = route_to_side(src, dst, label_size, 0, max(1, total), side, nodes)
    return not route_has_component_hit(src, dst, bends, nodes, clearance=6.0)

def route_connections(group_id: str, nodes: Dict[str, Node], conns: List[Conn]) -> Dict[str, Tuple[List[Dict[str, float]], int]]:
    routed: Dict[str, Tuple[List[Dict[str, float]], int]] = {}
    # Pre-rank fan-in groups before routing.  This is the key to avoiding visual line
    # stacking: connections going into the same target side receive ordered edge slots
    # and ordered bus lanes instead of all sharing the target center.
    branch_groups: Dict[Tuple[str, str], List[str]] = collections.defaultdict(list)
    branch_rank: Dict[str, Tuple[int, int, str]] = {}
    output_groups: Dict[str, List[str]] = collections.defaultdict(list)
    output_rank: Dict[str, Tuple[int, int]] = {}
    branch_candidates: List[Tuple[Conn, str, str]] = []
    branch_counts: Dict[str, int] = collections.defaultdict(int)
    for c in conns:
        sid = visual_id(c, "source", group_id, nodes)
        did = visual_id(c, "dest", group_id, nodes)
        if sid not in nodes or did not in nodes:
            continue
        src, dst = nodes[sid], nodes[did]
        aligned_main = abs(src.rect().cx - dst.rect().cx) < 70 and src.rect().bottom <= dst.rect().top
        if dst.kind == "OUTPUT_PORT":
            output_groups[dst.id].append(c.id)
        if dst.kind == "PROCESSOR" and not aligned_main:
            horizontal_gap = abs(dst.rect().cx - src.rect().cx) > 280
            vertical_gap = abs(dst.rect().cy - src.rect().cy) > 220
            if horizontal_gap or vertical_gap:
                branch_candidates.append((c, sid, did))
                branch_counts[did] += 1
    for c, sid, did in branch_candidates:
        src, dst = nodes[sid], nodes[did]
        side = branch_target_side(src, dst)
        if abs(src.rect().cx - dst.rect().cx) < 180.0 and abs(src.rect().cy - dst.rect().cy) > 220.0:
            # Same-lane loopbacks (for example "log successful task" back to
            # "claim next task") must not use a vertical centerline through all
            # intermediate processors and queue labels.  Route them as a side
            # loop so the return arrow visibly travels outside the main spine.
            side = "left"
        if branch_counts[did] >= 5 and src.rect().cx < dst.rect().cx:
            # Dense fan-in into a right-column handler cannot put every arrow on
            # the left edge: the slots are only ~15-20 px apart and the browser
            # shows them as one thick merged wire.  Split upper sources into the
            # target top edge and keep same/lower sources in the left corridor.
            # Do not use the far right edge by default: if a second handler sits
            # below the target, the far-right vertical bus runs through that
            # processor (exactly the PUIG 30.70.90 -> 30.70.110 defect).
            if src.rect().cy < dst.rect().top - 60.0:
                side = "top"
            else:
                side = "left"
        branch_groups[(dst.id, side)].append(c.id)
    conn_by_id = {c.id: c for c in conns}
    for (dst_id, side), ids in branch_groups.items():
        if side in ("left", "right"):
            ids.sort(key=lambda cid: (nodes[visual_id(conn_by_id[cid], "source", group_id, nodes)].rect().cy, cid))
        else:
            ids.sort(key=lambda cid: (nodes[visual_id(conn_by_id[cid], "source", group_id, nodes)].rect().cx, cid))
        for i, cid in enumerate(ids):
            branch_rank[cid] = (i, len(ids), side)
    for dst_id, ids in output_groups.items():
        # For output ports, sort by source Y first so stacked branches keep their
        # visible order and receive different bottom slots.
        ids.sort(key=lambda cid: (nodes[visual_id(conn_by_id[cid], "source", group_id, nodes)].rect().cy, cid))
        for i, cid in enumerate(ids):
            output_rank[cid] = (i, len(ids))
    for c in conns:
        sid = visual_id(c, "source", group_id, nodes)
        did = visual_id(c, "dest", group_id, nodes)
        if sid not in nodes or did not in nodes:
            routed[c.id] = ([], 0)
            continue
        src, dst = nodes[sid], nodes[did]
        label_size = connection_label_size(c, group_id)
        if clear_same_column_route(src, dst, nodes):
            routed[c.id] = ([], 0)
            continue
        if src.kind == "PROCESSOR" and dst.kind == "PROCESSOR" and same_column_blocked(src, dst, nodes):
            bends, li = same_column_around_route(src, dst, nodes, 0, 1)
            if li < 0:
                li = best_label_index(src, dst, bends, nodes, label_size)
            routed[c.id] = (bends, li)
            continue
        if dst.kind == "OUTPUT_PORT":
            # The normal main-chain finish is a short vertical connection.
            # Side lanes are only for secondary branches into the same output port.
            aligned = abs(src.rect().cx - dst.rect().cx) < 70 and src.rect().bottom <= dst.rect().top
            blocked_below = any(
                n.id not in (src.id, dst.id)
                and abs(n.rect().cx - src.rect().cx) < 120
                and n.rect().top > src.rect().bottom
                and n.rect().bottom < dst.rect().top
                for n in nodes.values()
            )
            if aligned and not blocked_below:
                routed[c.id] = ([], 0)
            else:
                lane, total = output_rank.get(c.id, (0, 1))
                bends, li = route_to_output(src, dst, nodes, label_size, lane, total)
                if li < 0:
                    li = best_label_index(src, dst, bends, nodes, label_size)
                routed[c.id] = (bends, li)
            continue
        if c.id in branch_rank:
            lane, total, side = branch_rank[c.id]
            bends, li = route_to_side(src, dst, label_size, lane, total, side, nodes)
            if li < 0:
                li = best_label_index(src, dst, bends, nodes, label_size)
            routed[c.id] = (bends, li)
            continue
        # Main lane rule: if the next component is directly below on the same centerline,
        # keep the connection straight. This is the visual style the user expects in NiFi:
        # block → queue label → block, without side doglegs for normal success flow.
        aligned_main = abs(src.rect().cx - dst.rect().cx) < 70 and src.rect().bottom <= dst.rect().top
        blocker = any(
            n.id not in (src.id, dst.id)
            and abs(n.rect().cx - src.rect().cx) < 130
            and n.rect().top > src.rect().bottom
            and n.rect().bottom < dst.rect().top
            for n in nodes.values()
        )
        if aligned_main and not blocker:
            routed[c.id] = ([], 0)
            continue
        bends, li = choose_route(src, dst, nodes, label_size, 0)
        routed[c.id] = (bends, li)
    # Second pass: NiFi labels are solid boxes, and local route scoring cannot see labels
    # or route lines that will be placed by other connections. Pack labelIndex values so
    # queue labels do not overlap labels or sit underneath another route segment.
    all_route_segments: List[Tuple[str, int, Tuple[str, float, float, float]]] = []
    for c in conns:
        sid = visual_id(c, "source", group_id, nodes)
        did = visual_id(c, "dest", group_id, nodes)
        if sid not in nodes or did not in nodes:
            continue
        bends, _li = routed.get(c.id, ([], 0))
        pts = route_points(nodes[sid], nodes[did], bends)
        for i in range(len(pts) - 1):
            norm = orthogonal_segment(pts[i], pts[i + 1])
            if norm and (norm[3] - norm[2]) > 12.0:
                all_route_segments.append((c.id, i, norm))
    occupied_labels: List[Rect] = []
    for c in sorted(conns, key=lambda cc: (nodes.get(visual_id(cc, "source", group_id, nodes), Node("", "PROCESSOR", "", 0, 0)).y, cc.id)):
        sid = visual_id(c, "source", group_id, nodes)
        did = visual_id(c, "dest", group_id, nodes)
        if sid not in nodes or did not in nodes:
            continue
        bends, li = routed.get(c.id, ([], 0))
        label_size = connection_label_size(c, group_id)
        if bends:
            li = best_label_index_avoiding(nodes[sid], nodes[did], bends, nodes, label_size, occupied_labels, all_route_segments, c.id)
            if nodes[sid].rect().cx > nodes[did].rect().cx + 300.0 and nodes[did].rect().cy < nodes[sid].rect().cy - 220.0 and len(bends) >= 2:
                # Right-column handler returning to the top of the main loop:
                # place the label on the side-column bend, not the center bus,
                # so it does not collide with labels of incoming error routes.
                # But never force that bend if the current group already placed
                # another queue label there; in dense fetch loops the forced
                # side bend created overlapping queued boxes.
                forced = 1
                forced_rect = label_rect(route_points(nodes[sid], nodes[did], bends), forced, label_size, bends)
                forced_hits = any(forced_rect.inflate(18.0).intersects(other.inflate(18.0)) for other in occupied_labels)
                forced_hits = forced_hits or any(forced_rect.intersects(r) for _oid, r in rects_actual(nodes, exclude=[]))
                if not forced_hits:
                    li = forced
                else:
                    # Pick another bend that has no hard label/component
                    # collision.  Prefer later bends for long loopbacks because
                    # the first two bends are usually in the side-column bundle.
                    fallback: List[Tuple[int, int]] = []
                    pts = route_points(nodes[sid], nodes[did], bends)
                    for idx in range(len(bends)):
                        rr = label_rect(pts, idx, label_size, bends)
                        hard = sum(1 for other in occupied_labels if rr.inflate(18.0).intersects(other.inflate(18.0)))
                        hard += sum(1 for _oid, comp_rect in rects_actual(nodes, exclude=[]) if rr.intersects(comp_rect))
                        fallback.append((hard, idx))
                    fallback.sort(key=lambda item: (item[0], 0 if item[1] >= 2 else 1, item[1]))
                    if fallback and fallback[0][0] == 0:
                        li = fallback[0][1]
            routed[c.id] = (bends, li)
        pts = route_points(nodes[sid], nodes[did], bends)
        occupied_labels.append(label_rect(pts, li, label_size, bends))
    nudge_routes_away_from_labels(group_id, nodes, conns, routed)
    nudge_routes_for_line_clearance(group_id, nodes, conns, routed)
    nudge_routes_away_from_labels(group_id, nodes, conns, routed)
    # Route nudging can move the bend that owns a connection label. Repack one
    # more time against the final widened lanes so labels do not end up on a new
    # bus or another queued box.
    final_segments = collect_route_segments(group_id, nodes, conns, routed)
    occupied_labels = []
    for c in sorted(conns, key=lambda cc: (nodes.get(visual_id(cc, "source", group_id, nodes), Node("", "PROCESSOR", "", 0, 0)).y, cc.id)):
        sid = visual_id(c, "source", group_id, nodes)
        did = visual_id(c, "dest", group_id, nodes)
        if sid not in nodes or did not in nodes:
            continue
        bends, li = routed.get(c.id, ([], 0))
        if bends:
            li = best_label_index_avoiding(nodes[sid], nodes[did], bends, nodes, connection_label_size(c, group_id), occupied_labels, final_segments, c.id)
            routed[c.id] = (bends, li)
        occupied_labels.append(label_rect(route_points(nodes[sid], nodes[did], bends), li, connection_label_size(c, group_id), bends))
    # The final repack can legitimately move a label to another bend after the
    # line-clearance pass.  Run one last path-vs-label nudge so a newly selected
    # label does not end up with a neighboring route skimming or crossing it.
    nudge_routes_away_from_labels(group_id, nodes, conns, routed)
    return routed

def audit_names_comments(nodes: Dict[str, Node], conns: List[Conn]) -> Dict[str, Any]:
    missing_comments = [(n.kind, n.id, n.name) for n in nodes.values() if n.kind != "FUNNEL" and not n.comments.strip()]
    named_connections = [(c.id, c.name) for c in conns if c.name]
    dot00 = [(n.kind, n.id, n.name) for n in nodes.values() if re.search(r"(^|\.)00(\D|$)", n.name)]
    return {"missing_comments": missing_comments, "named_connections": named_connections, "dot00_names": dot00}

def route_report(group_id: str, nodes: Dict[str, Node], conns: List[Conn], routes: Dict[str, Tuple[List[Dict[str, float]], int]]) -> List[Dict[str, Any]]:
    issues = []
    label_rects: List[Tuple[str, Rect]] = []
    all_segments: List[Tuple[str, int, Tuple[str, float, float, float]]] = []
    for c in conns:
        sid = visual_id(c, "source", group_id, nodes)
        did = visual_id(c, "dest", group_id, nodes)
        if sid not in nodes or did not in nodes:
            continue
        bends, li = routes.get(c.id, (c.bends, c.label_index))
        pts = route_points(nodes[sid], nodes[did], bends)
        for i in range(len(pts)-1):
            if abs(pts[i+1][0] - pts[i][0]) > 1.0 and abs(pts[i+1][1] - pts[i][1]) > 1.0:
                issues.append({"connection": c.id, "type": "diagonal_segment", "segment": i})
            seg = segment_rect(pts[i], pts[i+1], 3.0)
            hits = [oid for oid, r in rects(nodes, exclude=[sid, did]) if seg.intersects(r)]
            if hits:
                issues.append({"connection": c.id, "type": "segment_intersects_component", "segment": i, "hits": hits})
            norm = orthogonal_segment(pts[i], pts[i+1])
            if norm and (norm[3] - norm[2]) > 12.0:
                all_segments.append((c.id, i, norm))
        lr = label_rect(pts, li, connection_label_size(c, group_id), bends)
        hits = [oid for oid, r in rects_actual(nodes, exclude=[]) if lr.intersects(r)]
        if hits:
            issues.append({"connection": c.id, "type": "label_intersects_component", "hits": hits, "label": lr.as_dict()})
        for oid, other in label_rects:
            if lr.intersects(other):
                issues.append({"connection": c.id, "type": "label_intersects_label", "other": oid})
        label_rects.append((c.id, lr))
    # A route can visually run through another connection's queued/name box even
    # when it does not touch any processor.  This is a hard readability defect:
    # the operator sees wires crossing a label and cannot tell what is connected.
    for ca, ia, sa in all_segments:
        if sa[0] == "v":
            seg_rect = Rect(sa[1] - 3.0, sa[2], 6.0, sa[3] - sa[2])
        else:
            seg_rect = Rect(sa[2], sa[1] - 3.0, sa[3] - sa[2], 6.0)
        for lid, lr in label_rects:
            if lid == ca:
                continue
            if seg_rect.intersects(lr):
                issues.append({
                    "connection": ca,
                    "type": "segment_intersects_connection_label",
                    "segment": ia,
                    "label_connection": lid,
                })
            elif seg_rect.intersects(lr.inflate(LABEL_CLEARANCE)):
                issues.append({
                    "connection": ca,
                    "type": "segment_too_close_to_connection_label",
                    "segment": ia,
                    "label_connection": lid,
                    "required": LABEL_CLEARANCE,
                })
    for i in range(len(all_segments)):
        ca, ia, sa = all_segments[i]
        for j in range(i + 1, len(all_segments)):
            cb, ib, sb = all_segments[j]
            if not distinct_route_segment_pair(ca, ia, cb, ib):
                continue
            overlap = segment_overlap_amount(sa, sb)
            # Tiny shared endpoint touches are fine. Longer collinear overlap creates the
            # “one thick wire” problem the skill must prevent.
            if overlap > 20.0:
                issues.append({
                    "connection": ca,
                    "type": "segment_overlaps_segment",
                    "segment": ia,
                    "other_connection": cb,
                    "other_segment": ib,
                    "overlap": round(overlap, 1),
                    "orientation": sa[0],
                })
            cross = perpendicular_cross_point(sa, sb)
            if cross:
                issues.append({
                    "connection": ca,
                    "type": "segments_cross_segment",
                    "segment": ia,
                    "other_connection": cb,
                    "other_segment": ib,
                    "at": {"x": round(cross[0], 1), "y": round(cross[1], 1)},
                })
            # Even when two fan-in lines are not exactly collinear, lanes closer
            # than a grid cell read as one thick wire in the browser.  Report it
            # so the algorithm can widen the corridor instead of hiding the issue.
            if sa[0] == sb[0] and 0.0 < abs(sa[1] - sb[1]) < LINE_SPACING:
                near_lo = max(sa[2], sb[2])
                near_hi = min(sa[3], sb[3])
                if near_hi - near_lo > 35.0:
                    issues.append({
                        "connection": ca,
                        "type": "parallel_segments_too_close",
                        "segment": ia,
                        "other_connection": cb,
                        "other_segment": ib,
                        "overlap": round(near_hi - near_lo, 1),
                        "distance": round(abs(sa[1] - sb[1]), 1),
                        "required": LINE_SPACING,
                        "orientation": sa[0],
                    })
    return issues

def backup(api: NiFi, group_id: str, backup_dir: Path) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    out = backup_dir / f"nifi-flow-{group_id}-{time.strftime('%Y%m%d-%H%M%S')}.json"
    out.write_text(json.dumps(api.snapshot(group_id), ensure_ascii=False, indent=2), encoding="utf-8")
    return out

def iter_groups(api: NiFi, root_id: str, recursive: bool, order: str = "api", include_root: bool = True) -> Iterable[Tuple[str, Dict[str, Any]]]:
    flow = api.flow(root_id)
    if include_root:
        yield root_id, flow
    if recursive:
        children = list(flow.get("processGroups", []) or [])
        if order == "top-down":
            children.sort(key=lambda pg: (
                (pg.get("component") or {}).get("position", {}).get("y", 0.0),
                (pg.get("component") or {}).get("position", {}).get("x", 0.0),
                (pg.get("component") or {}).get("name", ""),
            ))
        for pg in children:
            yield from iter_groups(api, pg["component"]["id"], recursive=True, order=order, include_root=True)

def apply_group(api: NiFi, group_id: str, flow: Dict[str, Any], mode: str, rename: bool = False) -> Dict[str, Any]:
    nodes, conns = parse_group(flow)
    before = audit_names_comments(nodes, conns)
    targets = target_layout(nodes, conns)
    next_nodes = with_targets(nodes, targets)
    routes = route_connections(group_id, next_nodes, conns)
    issues = route_report(group_id, next_nodes, conns, routes)
    planned = {
        "group_id": group_id,
        "node_moves": [],
        "connection_routes": [],
        "before_audit": before,
        "route_issues": issues,
        "processor_states_before": {},
        "processor_states_after": {},
        "state_preservation_issues": [],
    }
    if mode == "apply":
        for n in nodes.values():
            if n.kind in ("PROCESSOR", "INPUT_PORT", "OUTPUT_PORT"):
                planned["processor_states_before"][n.id] = api.component_state(n.kind, n.id)

    for nid, n in nodes.items():
        x, y = targets.get(nid, (n.x, n.y))
        new_comment = comment_for(n)
        new_name = n.name
        if rename and n.kind in ("PROCESSOR", "PROCESS_GROUP") and re.search(r"(^|\.)00(\D|$)", n.name):
            new_name = re.sub(r"(^|\.)00(?=\D|$)", lambda m: "10" if m.group(1) == "" else m.group(1) + "10", n.name)
        changed = abs(n.x-x) > 0.1 or abs(n.y-y) > 0.1 or new_comment != n.comments or new_name != n.name
        if changed:
            planned["node_moves"].append({"id": nid, "kind": n.kind, "name": n.name, "to_name": new_name, "from": {"x": n.x, "y": n.y}, "to": {"x": x, "y": y}, "comment_changed": new_comment != n.comments})
            if mode == "apply":
                if n.kind == "PROCESSOR":
                    api.update_processor(n, new_name if new_name != n.name else None, new_comment if new_comment != n.comments else None, x, y)
                elif n.kind == "PROCESS_GROUP":
                    api.update_process_group(n, new_name if new_name != n.name else None, new_comment if new_comment != n.comments else None, x, y)
                elif n.kind in ("INPUT_PORT", "OUTPUT_PORT"):
                    api.update_port(n.kind, n, new_name if new_name != n.name else None, new_comment if new_comment != n.comments else None, x, y)

    for c in conns:
        bends, li = routes.get(c.id, ([], 0))
        need = c.name != "" or c.bends != bends or c.label_index != li
        if need:
            route_plan = {"id": c.id, "source": c.source_name, "dest": c.dest_name, "clear_name": bool(c.name), "bends": bends, "labelIndex": li}
            if mode == "apply":
                route_plan["update_safety"] = api.update_connection(c, bends, li, clear_name=True)
            planned["connection_routes"].append(route_plan)
    if mode == "apply":
        for n in nodes.values():
            if n.kind in ("PROCESSOR", "INPUT_PORT", "OUTPUT_PORT"):
                planned["processor_states_after"][n.id] = api.component_state(n.kind, n.id)
        for cid, before_state in planned["processor_states_before"].items():
            after_state = planned["processor_states_after"].get(cid)
            if after_state != before_state:
                planned["state_preservation_issues"].append({"component": cid, "before": before_state, "after": after_state})
    return planned

def cmd_self_test() -> None:
    a = Rect(0, 0, 10, 10); b = Rect(9, 9, 5, 5); c = Rect(11, 11, 5, 5)
    assert a.intersects(b)
    assert not a.intersects(c)
    src = Node("a", "PROCESSOR", "A", 0, 0)
    dst = Node("b", "PROCESSOR", "B", 0, 220)
    nodes = {"a": src, "b": dst, "x": Node("x", "PROCESSOR", "X", 420, 0)}
    bends, li = choose_route(src, dst, nodes, LABEL)
    assert isinstance(bends, list) and isinstance(li, int)
    assert not re.search(r"(^|\.)00(\D|$)", "30.10 Test")
    assert re.search(r"(^|\.)00(\D|$)", "30.00 Test")
    flow = {
        "processGroups": [
            {"component": {"id": "lower", "name": "lower", "position": {"x": 0, "y": 200}}},
            {"component": {"id": "upper", "name": "upper", "position": {"x": 0, "y": 10}}},
        ]
    }
    class FakeApi:
        def flow(self, gid: str) -> Dict[str, Any]:
            return flow if gid == "root" else {"processGroups": []}
    ordered = [gid for gid, _ in iter_groups(FakeApi(), "root", True, order="top-down")]
    assert ordered[:3] == ["root", "upper", "lower"]
    c1 = Conn("c1", "a", "b", "PROCESSOR", "PROCESSOR", None, None, "a", "b", ("success",), name="should clear")
    assert audit_names_comments({"a": src, "b": dst}, [c1])["named_connections"]
    label = label_rect(route_points(src, dst, []), 0, connection_label_size(c1, "root"), [])
    assert label.w == CONNECTION_LABEL_WIDTH and label.h >= 41
    assert perpendicular_cross_point(("v", 50, 0, 100), ("h", 40, 0, 100)) == (50, 40)
    assert perpendicular_cross_point(("v", 50, 0, 100), ("h", 0, 0, 100)) is None
    assert segment_parallel_overlap(("v", 10, 0, 100), ("v", 40, 50, 150)) == 50
    assert not distinct_route_segment_pair("same", 1, "same", 2)
    assert distinct_route_segment_pair("same", 1, "same", 3)
    compact_side = same_column_around_route(
        Node("rs1", "PROCESSOR", "RS1", 1200, 0),
        Node("rs2", "PROCESSOR", "RS2", 1200, 420),
        {"mid": Node("mid", "PROCESSOR", "MID", 1200, 210)},
    )[0]
    assert compact_side[1]["x"] - (1200 + SIZE["PROCESSOR"][0]) <= OUTER_LABEL_LANE_GAP + 10.0
    left = Node("left", "PROCESSOR", "Left", 0, 0)
    right = Node("right", "PROCESSOR", "Right", 700, 0)
    top = Node("top", "PROCESSOR", "Top", 320, -260)
    bottom = Node("bottom", "PROCESSOR", "Bottom", 320, 260)
    cross_nodes = {n.id: n for n in (left, right, top, bottom)}
    horizontal = Conn("h", "left", "right", "PROCESSOR", "PROCESSOR", None, None, "left", "right", ("success",))
    vertical = Conn("v", "top", "bottom", "PROCESSOR", "PROCESSOR", None, None, "top", "bottom", ("success",))
    cross_routes = {
        "h": ([{"x": 300.0, "y": left.rect().cy}, {"x": 400.0, "y": right.rect().cy}], 0),
        "v": ([{"x": top.rect().cx, "y": -40.0}, {"x": bottom.rect().cx, "y": 240.0}], 0),
    }
    before = route_report("root", cross_nodes, [horizontal, vertical], cross_routes)
    assert any(i["type"] == "segments_cross_segment" for i in before)
    print("self-test ok")

def main() -> None:
    p = argparse.ArgumentParser(description="Audit/dry-run/apply NiFi visual layout rules")
    p.add_argument("--base-url", help="NiFi API base URL, e.g. https://nifi.example.com/nifi-api")
    p.add_argument("--group-id", help="Root process group id")
    p.add_argument("--cert", help="Client certificate PEM")
    p.add_argument("--key", help="Client key PEM")
    p.add_argument("--p12", help="Client PKCS#12 certificate")
    p.add_argument("--p12-pass-file", help="File containing the PKCS#12 passphrase")
    p.add_argument("--p12-pass-env", help="Environment variable containing the PKCS#12 passphrase")
    p.add_argument("--token", help="Bearer token")
    p.add_argument("--verify", help="Use system TLS validation (true) or the specified CA bundle path (default: true)")
    p.add_argument("--insecure", action="store_true", help="Explicitly disable TLS certificate validation (unsafe)")
    p.add_argument("--mode", choices=["audit", "dry-run", "apply", "self-test"], default="audit")
    p.add_argument("--recursive", action="store_true", help="Process nested groups too")
    p.add_argument("--single-group", action="store_true", help="Process only --group-id even if --recursive is also present")
    p.add_argument("--group-order", choices=["api", "top-down"], default="api", help="Recursive child order")
    p.add_argument("--backup-dir", default="./nifi-layout-backups")
    p.add_argument("--report-dir", help="Directory for default JSON reports")
    p.add_argument("--screenshots-dir", help="Reserved by wrappers/visual gate; recorded in the report")
    p.add_argument("--visual-gate", action="store_true", help="Require callers to run Playwright visual check; recorded in report")
    p.add_argument("--rename", action="store_true", help="Allow safe numbering cleanup such as .00 -> .10")
    p.add_argument("--report", help="Write JSON report to this file")
    args = p.parse_args()
    if args.mode == "self-test":
        cmd_self_test(); return
    if not args.base_url or not args.group_id:
        p.error("--base-url and --group-id are required unless --mode self-test")
    if args.insecure and args.verify:
        p.error("--insecure cannot be combined with --verify")
    if args.insecure:
        verify: Any = False
    elif args.verify is None or str(args.verify).lower() in ("1", "true", "yes"):
        verify = True
    elif str(args.verify).lower() in ("0", "false", "no"):
        p.error("TLS verification can only be disabled with the explicit --insecure flag")
    else:
        verify = args.verify
    cert = (args.cert, args.key) if args.cert and args.key else None
    p12_pass = None
    if args.p12_pass_file:
        p12_pass = Path(args.p12_pass_file).read_text(encoding="utf-8").strip("\r\n")
    if args.p12_pass_env:
        p12_pass = os.environ.get(args.p12_pass_env, "")
    with p12_cert_pair(args.p12, p12_pass) as p12_cert:
        api = NiFi(args.base_url, cert or p12_cert, args.token, verify)
        backup_path = backup(api, args.group_id, Path(args.backup_dir)) if args.mode in ("dry-run", "apply") else None
        all_reports = []
        recursive = bool(args.recursive and not args.single_group)
        for gid, flow in iter_groups(api, args.group_id, recursive, order=args.group_order):
            all_reports.append(apply_group(api, gid, flow, args.mode, rename=args.rename))
        report = {
            "mode": args.mode,
            "root_group_id": args.group_id,
            "recursive": recursive,
            "group_order": args.group_order,
            "visual_gate": args.visual_gate,
            "screenshots_dir": args.screenshots_dir,
            "backup": str(backup_path) if backup_path else None,
            "groups": all_reports,
        }
        text = json.dumps(report, ensure_ascii=False, indent=2)
        report_path = args.report
        if not report_path and args.report_dir:
            Path(args.report_dir).mkdir(parents=True, exist_ok=True)
            report_path = str(Path(args.report_dir) / f"nifi-layout-{args.mode}-{args.group_id}-{time.strftime('%Y%m%d-%H%M%S')}.json")
        if report_path:
            Path(report_path).parent.mkdir(parents=True, exist_ok=True)
            Path(report_path).write_text(text, encoding="utf-8")
        print(text)

if __name__ == "__main__":
    main()
