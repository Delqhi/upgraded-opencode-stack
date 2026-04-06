#!/usr/bin/env python3
"""
CDP Browser Logger - Enterprise Deep Debug Skill
=================================================
Captures EVERYTHING from a Chrome browser session via Chrome DevTools Protocol:
console, network, screenshots, screencast video, performance, errors, DOM, coverage.

All captured data is uploaded to GitLab LogCenter (no local disk bloat).

Usage:
  cdp_browser_logger.py start   --project <name> [--port 9334] [--fps 2] [--quality 80]
  cdp_browser_logger.py stop
  cdp_browser_logger.py capture-screenshot --project <name> [--port 9334] [--name <n>]
  cdp_browser_logger.py capture-har        --project <name> [--port 9334]
  cdp_browser_logger.py dump-console       --project <name> [--port 9334]
  cdp_browser_logger.py dump-coverage      --project <name> [--port 9334]
  cdp_browser_logger.py dump-perf          --project <name> [--port 9334]

Requires: Chrome running with --remote-debugging-port=9334
"""

import argparse
import base64
import datetime
import json
import os
import signal
import socket
import struct
import sys
import threading
import time
import hashlib
import urllib.request
import urllib.error

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

VERSION = "1.0.0"
DEFAULT_CDP_PORT = 9334
PID_FILE = "/tmp/cdp_browser_logger.pid"
STATE_FILE = "/tmp/cdp_browser_logger_state.json"


def _ts():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ts_short():
    return datetime.datetime.now().strftime("%Y%m%d-%H%M%S")


class WebSocketClient:
    """Minimal RFC 6455 WebSocket client (no external deps)."""

    def __init__(self, url: str):
        self.url = url
        self.sock: socket.socket | None = None
        self._msg_id = 0
        self._lock = threading.Lock()

    def connect(self):
        from urllib.parse import urlparse

        parsed = urlparse(self.url)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or 80
        path = parsed.path or "/"

        self.sock = socket.create_connection((host, port), timeout=10)
        key = base64.b64encode(os.urandom(16)).decode()
        handshake = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            f"Upgrade: websocket\r\n"
            f"Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            f"Sec-WebSocket-Version: 13\r\n\r\n"
        )
        self.sock.sendall(handshake.encode())
        resp = b""
        while b"\r\n\r\n" not in resp:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise ConnectionError("WebSocket handshake failed")
            resp += chunk
        if b"101" not in resp.split(b"\r\n")[0]:
            raise ConnectionError(f"WebSocket upgrade rejected: {resp[:200]}")

    def send(self, data: str) -> None:
        if not self.sock:
            raise ConnectionError("Not connected")
        payload = data.encode("utf-8")
        frame = bytearray()
        frame.append(0x81)
        mask_key = os.urandom(4)
        plen = len(payload)
        if plen <= 125:
            frame.append(0x80 | plen)
        elif plen <= 65535:
            frame.append(0x80 | 126)
            frame.extend(struct.pack("!H", plen))
        else:
            frame.append(0x80 | 127)
            frame.extend(struct.pack("!Q", plen))
        frame.extend(mask_key)
        masked = bytearray(b ^ mask_key[i % 4] for i, b in enumerate(payload))
        frame.extend(masked)
        with self._lock:
            self.sock.sendall(frame)

    def recv(self, timeout: float = 30.0) -> str:
        if not self.sock:
            raise ConnectionError("Not connected")
        self.sock.settimeout(timeout)
        try:
            header = self._recv_exact(2)
        except (socket.timeout, TimeoutError):
            return ""
        opcode = header[0] & 0x0F
        masked = bool(header[1] & 0x80)
        plen = header[1] & 0x7F
        if plen == 126:
            plen = struct.unpack("!H", self._recv_exact(2))[0]
        elif plen == 127:
            plen = struct.unpack("!Q", self._recv_exact(8))[0]
        if masked:
            mask_key = self._recv_exact(4)
        payload = self._recv_exact(plen)
        if masked:
            payload = bytearray(b ^ mask_key[i % 4] for i, b in enumerate(payload))
        if opcode == 0x08:
            raise ConnectionError("WebSocket closed by server")
        if opcode == 0x09:
            self._send_pong(payload)
            return self.recv(timeout)
        return payload.decode("utf-8", errors="replace")

    def _recv_exact(self, n: int) -> bytes:
        buf = bytearray()
        while len(buf) < n:
            chunk = self.sock.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("Connection closed")
            buf.extend(chunk)
        return bytes(buf)

    def _send_pong(self, payload: bytes):
        frame = bytearray([0x8A, len(payload)])
        frame.extend(payload)
        with self._lock:
            self.sock.sendall(frame)

    def call(
        self, method: str, params: dict | None = None, timeout: float = 30.0
    ) -> dict:
        self._msg_id += 1
        msg_id = self._msg_id
        msg = {"id": msg_id, "method": method}
        if params:
            msg["params"] = params
        self.send(json.dumps(msg))
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            raw = self.recv(timeout=min(5.0, deadline - time.monotonic()))
            if not raw:
                continue
            try:
                resp = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if resp.get("id") == msg_id:
                if "error" in resp:
                    raise RuntimeError(f"CDP error: {resp['error']}")
                return resp.get("result", {})
        raise TimeoutError(f"CDP call {method} timed out")

    def close(self):
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None


def get_ws_url(port: int = DEFAULT_CDP_PORT) -> str:
    url = f"http://127.0.0.1:{port}/json/version"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read())
            return data.get("webSocketDebuggerUrl", "")
    except Exception:
        pass
    url2 = f"http://127.0.0.1:{port}/json"
    try:
        with urllib.request.urlopen(url2, timeout=5) as resp:
            pages = json.loads(resp.read())
            for p in pages:
                if p.get("type") == "page":
                    return p.get("webSocketDebuggerUrl", "")
    except Exception:
        pass
    raise ConnectionError(f"Cannot find CDP WebSocket on port {port}")


class CDPCapture:
    """Full CDP session capture: console, network, screenshots, screencast, perf, errors."""

    def __init__(self, ws: WebSocketClient, project_name: str):
        self.ws = ws
        self.project_name = project_name
        self.console_log: list[dict] = []
        self.network_log: list[dict] = []
        self.exceptions: list[dict] = []
        self.performance_metrics: list[dict] = []
        self.security_events: list[dict] = []
        self.screencast_frames: list[bytes] = []
        self.coverage_js: list = []
        self.coverage_css: list = []
        self._running = False
        self._listener_thread: threading.Thread | None = None
        self._session_start = _ts()
        self._frame_count = 0

    def enable_domains(self):
        for domain in [
            ("Runtime.enable", None),
            ("Console.enable", None),
            (
                "Network.enable",
                {"maxTotalBufferSize": 50_000_000, "maxResourceBufferSize": 10_000_000},
            ),
            ("Page.enable", None),
            ("Performance.enable", {"timeDomain": "timeTicks"}),
            ("Security.enable", None),
            ("DOM.enable", None),
            ("Log.enable", None),
        ]:
            method, params = domain
            try:
                self.ws.call(method, params)
            except Exception as e:
                print(f"[cdp] Warning: {method} failed: {e}")

    def start_js_coverage(self):
        try:
            self.ws.call("Profiler.enable")
            self.ws.call(
                "Profiler.startPreciseCoverage", {"callCount": True, "detailed": True}
            )
            print("[cdp] JS coverage started")
        except Exception as e:
            print(f"[cdp] JS coverage failed: {e}")

    def start_css_coverage(self):
        try:
            self.ws.call("CSS.enable")
            self.ws.call("CSS.startRuleUsageTracking")
            print("[cdp] CSS coverage started")
        except Exception as e:
            print(f"[cdp] CSS coverage failed: {e}")

    def start_screencast(self, fps: int = 2, quality: int = 60):
        try:
            self.ws.call(
                "Page.startScreencast",
                {
                    "format": "jpeg",
                    "quality": quality,
                    "maxWidth": 1920,
                    "maxHeight": 1080,
                    "everyNthFrame": max(1, 60 // fps),
                },
            )
            print(f"[cdp] Screencast started (target ~{fps} fps, quality={quality})")
        except Exception as e:
            print(f"[cdp] Screencast failed: {e}")

    def capture_screenshot(self) -> bytes:
        result = self.ws.call(
            "Page.captureScreenshot",
            {
                "format": "png",
                "quality": 100,
                "fromSurface": True,
            },
        )
        return base64.b64decode(result.get("data", ""))

    def get_performance_metrics(self) -> dict:
        result = self.ws.call("Performance.getMetrics")
        metrics = {}
        for m in result.get("metrics", []):
            metrics[m["name"]] = m["value"]
        return metrics

    def get_dom_counters(self) -> dict:
        try:
            result = self.ws.call("Memory.getDOMCounters")
            return result
        except Exception:
            return {}

    def stop_js_coverage(self) -> list:
        try:
            result = self.ws.call("Profiler.takePreciseCoverage")
            self.ws.call("Profiler.stopPreciseCoverage")
            return result.get("result", [])
        except Exception:
            return []

    def stop_css_coverage(self) -> list:
        try:
            result = self.ws.call("CSS.stopRuleUsageTracking")
            return result.get("ruleUsage", [])
        except Exception:
            return []

    def start_event_listener(self):
        self._running = True
        self._listener_thread = threading.Thread(target=self._event_loop, daemon=True)
        self._listener_thread.start()

    def stop_event_listener(self):
        self._running = False
        if self._listener_thread:
            self._listener_thread.join(timeout=5)

    def _event_loop(self):
        while self._running:
            try:
                raw = self.ws.recv(timeout=2.0)
                if not raw:
                    continue
                msg = json.loads(raw)
                self._handle_event(msg)
            except (ConnectionError, json.JSONDecodeError):
                if self._running:
                    time.sleep(0.5)
            except Exception:
                if self._running:
                    time.sleep(0.5)

    def _handle_event(self, msg: dict):
        method = msg.get("method", "")
        params = msg.get("params", {})
        ts = _ts()

        if method == "Runtime.consoleAPICalled":
            entry = {
                "timestamp": ts,
                "type": params.get("type", "log"),
                "args": [_serialize_remote_obj(a) for a in params.get("args", [])],
                "stackTrace": _extract_stack(params.get("stackTrace")),
                "url": params.get("context", ""),
            }
            self.console_log.append(entry)

        elif method == "Runtime.exceptionThrown":
            detail = params.get("exceptionDetails", {})
            entry = {
                "timestamp": ts,
                "text": detail.get("text", ""),
                "exception": _serialize_remote_obj(detail.get("exception", {})),
                "stackTrace": _extract_stack(detail.get("stackTrace")),
                "lineNumber": detail.get("lineNumber", 0),
                "columnNumber": detail.get("columnNumber", 0),
                "url": detail.get("url", ""),
            }
            self.exceptions.append(entry)

        elif method == "Log.entryAdded":
            log_entry = params.get("entry", {})
            entry = {
                "timestamp": ts,
                "level": log_entry.get("level", ""),
                "source": log_entry.get("source", ""),
                "text": log_entry.get("text", ""),
                "url": log_entry.get("url", ""),
                "lineNumber": log_entry.get("lineNumber", 0),
            }
            self.console_log.append(entry)

        elif method == "Network.requestWillBeSent":
            req = params.get("request", {})
            entry = {
                "timestamp": ts,
                "requestId": params.get("requestId", ""),
                "type": "request",
                "method": req.get("method", ""),
                "url": req.get("url", ""),
                "headers": req.get("headers", {}),
                "postData": (req.get("postData", "") or "")[:2000],
                "initiator_type": params.get("initiator", {}).get("type", ""),
            }
            self.network_log.append(entry)

        elif method == "Network.responseReceived":
            resp = params.get("response", {})
            entry = {
                "timestamp": ts,
                "requestId": params.get("requestId", ""),
                "type": "response",
                "status": resp.get("status", 0),
                "statusText": resp.get("statusText", ""),
                "url": resp.get("url", ""),
                "headers": resp.get("headers", {}),
                "mimeType": resp.get("mimeType", ""),
                "timing": resp.get("timing", {}),
            }
            self.network_log.append(entry)

        elif method == "Network.loadingFailed":
            entry = {
                "timestamp": ts,
                "requestId": params.get("requestId", ""),
                "type": "failed",
                "errorText": params.get("errorText", ""),
                "canceled": params.get("canceled", False),
                "blockedReason": params.get("blockedReason", ""),
            }
            self.network_log.append(entry)

        elif method == "Security.securityStateChanged":
            entry = {
                "timestamp": ts,
                "securityState": params.get("securityState", ""),
                "summary": params.get("summary", ""),
            }
            self.security_events.append(entry)

        elif method == "Page.screencastFrame":
            frame_data = base64.b64decode(params.get("data", ""))
            self.screencast_frames.append(frame_data)
            self._frame_count += 1
            session_id = params.get("sessionId")
            if session_id is not None:
                try:
                    self.ws.call("Page.screencastFrameAck", {"sessionId": session_id})
                except Exception:
                    pass

    def build_session_report(self) -> dict:
        perf = {}
        try:
            perf = self.get_performance_metrics()
        except Exception:
            pass

        return {
            "session_start": self._session_start,
            "session_end": _ts(),
            "project": self.project_name,
            "summary": {
                "console_entries": len(self.console_log),
                "network_entries": len(self.network_log),
                "exceptions": len(self.exceptions),
                "screencast_frames": self._frame_count,
                "security_events": len(self.security_events),
            },
            "console": self.console_log[-500:],
            "exceptions": self.exceptions,
            "network": self.network_log[-1000:],
            "security": self.security_events,
            "performance": perf,
        }

    def upload_to_logcenter(self, report: dict | None = None):
        try:
            from gitlab_logcenter import get_logcenter
        except ImportError:
            print("[cdp] WARNING: gitlab_logcenter not importable, saving locally")
            self._save_local(report)
            return

        lc = get_logcenter(self.project_name)
        ts = _ts_short()

        if report is None:
            report = self.build_session_report()

        report_bytes = json.dumps(report, indent=2, default=str).encode("utf-8")
        lc.upload_bytes(
            report_bytes,
            f"cdp_session_{ts}.json",
            category="browser",
            tags=["cdp", "session"],
            description=f"CDP browser session capture {ts}",
        )
        print(f"[cdp] Session report uploaded ({len(report_bytes)} bytes)")

        console_bytes = json.dumps(self.console_log, indent=2, default=str).encode(
            "utf-8"
        )
        if len(console_bytes) > 100:
            lc.upload_bytes(
                console_bytes,
                f"console_{ts}.json",
                category="browser",
                tags=["cdp", "console"],
                description=f"Console log {ts}",
            )

        net_bytes = json.dumps(self.network_log, indent=2, default=str).encode("utf-8")
        if len(net_bytes) > 100:
            lc.upload_bytes(
                net_bytes,
                f"network_{ts}.json",
                category="browser",
                tags=["cdp", "network"],
                description=f"Network log {ts}",
            )

        if self.exceptions:
            exc_bytes = json.dumps(self.exceptions, indent=2, default=str).encode(
                "utf-8"
            )
            lc.upload_bytes(
                exc_bytes,
                f"exceptions_{ts}.json",
                category="browser",
                tags=["cdp", "exceptions"],
                description=f"JS exceptions {ts}",
            )

        if self.screencast_frames:
            self._upload_screencast_video(lc, ts)

    def _upload_screencast_video(self, lc, ts: str):
        if not self.screencast_frames:
            return
        frame_count = len(self.screencast_frames)
        print(f"[cdp] Uploading {frame_count} screencast frames...")
        for i, frame in enumerate(self.screencast_frames):
            if i % 10 == 0:
                lc.upload_bytes(
                    frame,
                    f"screencast_{ts}_frame{i:05d}.jpg",
                    category="video",
                    tags=["cdp", "screencast", f"frame_{i}"],
                    description=f"Screencast frame {i}/{frame_count}",
                )

        manifest = {
            "type": "screencast",
            "timestamp": ts,
            "total_frames": frame_count,
            "uploaded_frames": len(range(0, frame_count, 10)),
            "sample_rate": "every 10th frame",
        }
        lc.upload_bytes(
            json.dumps(manifest, indent=2).encode(),
            f"screencast_{ts}_manifest.json",
            category="video",
            tags=["cdp", "screencast", "manifest"],
        )
        print(f"[cdp] Screencast uploaded ({frame_count} frames, every 10th saved)")

    def _save_local(self, report: dict | None = None):
        ts = _ts_short()
        out_dir = f"/tmp/cdp_capture_{ts}"
        os.makedirs(out_dir, exist_ok=True)
        if report is None:
            report = self.build_session_report()
        with open(f"{out_dir}/session_report.json", "w") as f:
            json.dump(report, f, indent=2, default=str)
        with open(f"{out_dir}/console.json", "w") as f:
            json.dump(self.console_log, f, indent=2, default=str)
        with open(f"{out_dir}/network.json", "w") as f:
            json.dump(self.network_log, f, indent=2, default=str)
        if self.exceptions:
            with open(f"{out_dir}/exceptions.json", "w") as f:
                json.dump(self.exceptions, f, indent=2, default=str)
        for i, frame in enumerate(self.screencast_frames[:100]):
            with open(f"{out_dir}/frame_{i:05d}.jpg", "wb") as f:
                f.write(frame)
        print(f"[cdp] Saved locally to {out_dir}/")


def _serialize_remote_obj(obj: dict) -> str:
    if not obj:
        return ""
    if "value" in obj:
        return str(obj["value"])
    if "description" in obj:
        return obj["description"]
    if "unserializableValue" in obj:
        return obj["unserializableValue"]
    return str(obj.get("type", "unknown"))


def _extract_stack(st: dict | None) -> list[str]:
    if not st:
        return []
    frames = []
    for f in st.get("callFrames", [])[:20]:
        frames.append(
            f"{f.get('functionName', '(anonymous)')} "
            f"at {f.get('url', '')}:{f.get('lineNumber', 0)}:{f.get('columnNumber', 0)}"
        )
    return frames


def cmd_start(args):
    ws_url = get_ws_url(args.port)
    print(f"[cdp] Connecting to {ws_url}")
    ws = WebSocketClient(ws_url)
    ws.connect()
    print("[cdp] Connected")

    capture = CDPCapture(ws, args.project)
    capture.enable_domains()
    capture.start_js_coverage()
    capture.start_css_coverage()
    capture.start_screencast(fps=args.fps, quality=args.quality)
    capture.start_event_listener()

    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))
    with open(STATE_FILE, "w") as f:
        json.dump(
            {
                "project": args.project,
                "port": args.port,
                "started": _ts(),
                "pid": os.getpid(),
            },
            f,
        )

    print(f"[cdp] Capturing... (PID={os.getpid()}, Ctrl+C to stop & upload)")

    def _shutdown(signum=None, frame=None):
        print("\n[cdp] Stopping capture...")
        try:
            capture.stop_event_listener()
        except Exception:
            pass
        try:
            capture.ws.call("Page.stopScreencast")
        except Exception:
            pass
        capture.coverage_js = capture.stop_js_coverage()
        capture.coverage_css = capture.stop_css_coverage()
        report = capture.build_session_report()
        report["js_coverage_entries"] = len(capture.coverage_js)
        report["css_coverage_entries"] = len(capture.coverage_css)
        capture.upload_to_logcenter(report)
        ws.close()
        for f_path in (PID_FILE, STATE_FILE):
            try:
                os.unlink(f_path)
            except Exception:
                pass
        print("[cdp] Done.")
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    while True:
        time.sleep(60)
        perf = capture.get_performance_metrics()
        capture.performance_metrics.append({"timestamp": _ts(), **perf})
        stats = (
            f"console={len(capture.console_log)} "
            f"network={len(capture.network_log)} "
            f"errors={len(capture.exceptions)} "
            f"frames={capture._frame_count}"
        )
        print(f"[cdp] {_ts()} | {stats}")


def cmd_stop(args):
    if os.path.isfile(PID_FILE):
        with open(PID_FILE, "r") as f:
            pid = int(f.read().strip())
        print(f"[cdp] Sending SIGTERM to PID {pid}")
        try:
            os.kill(pid, signal.SIGTERM)
            print("[cdp] Stop signal sent")
        except ProcessLookupError:
            print("[cdp] Process not found, cleaning up")
            os.unlink(PID_FILE)
    else:
        print("[cdp] No running capture found")


def cmd_screenshot(args):
    ws_url = get_ws_url(args.port)
    ws = WebSocketClient(ws_url)
    ws.connect()
    capture = CDPCapture(ws, args.project)
    png = capture.capture_screenshot()
    name = args.name or f"screenshot_{_ts_short()}"
    local_path = f"/tmp/{name}.png"
    with open(local_path, "wb") as f:
        f.write(png)
    print(f"[cdp] Screenshot saved: {local_path} ({len(png)} bytes)")
    try:
        from gitlab_logcenter import get_logcenter

        lc = get_logcenter(args.project)
        lc.upload_file(
            local_path,
            category="screenshots",
            tags=["cdp", "screenshot"],
            description=f"Screenshot {name}",
        )
        print(f"[cdp] Uploaded to logcenter")
    except Exception as e:
        print(f"[cdp] LogCenter upload failed: {e}")
    ws.close()


def cmd_har(args):
    ws_url = get_ws_url(args.port)
    ws = WebSocketClient(ws_url)
    ws.connect()
    capture = CDPCapture(ws, args.project)
    capture.enable_domains()
    capture.start_event_listener()
    print(f"[cdp] Capturing network for {args.duration}s...")
    time.sleep(args.duration)
    capture.stop_event_listener()
    report = {
        "network": capture.network_log,
        "captured_at": _ts(),
        "duration_sec": args.duration,
    }
    try:
        from gitlab_logcenter import get_logcenter

        lc = get_logcenter(args.project)
        lc.upload_bytes(
            json.dumps(report, indent=2, default=str).encode(),
            f"har_capture_{_ts_short()}.json",
            category="browser",
            tags=["cdp", "network", "har"],
        )
        print(f"[cdp] HAR uploaded ({len(capture.network_log)} entries)")
    except Exception as e:
        local = f"/tmp/har_capture_{_ts_short()}.json"
        with open(local, "w") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"[cdp] Saved locally: {local} (upload failed: {e})")
    ws.close()


def cmd_console(args):
    ws_url = get_ws_url(args.port)
    ws = WebSocketClient(ws_url)
    ws.connect()
    capture = CDPCapture(ws, args.project)
    capture.enable_domains()
    capture.start_event_listener()
    print(f"[cdp] Capturing console for {args.duration}s...")
    time.sleep(args.duration)
    capture.stop_event_listener()
    try:
        from gitlab_logcenter import get_logcenter

        lc = get_logcenter(args.project)
        lc.upload_bytes(
            json.dumps(capture.console_log, indent=2, default=str).encode(),
            f"console_dump_{_ts_short()}.json",
            category="browser",
            tags=["cdp", "console"],
        )
        print(f"[cdp] Console uploaded ({len(capture.console_log)} entries)")
    except Exception as e:
        for entry in capture.console_log:
            print(json.dumps(entry, default=str))
        print(f"[cdp] LogCenter unavailable: {e}")
    ws.close()


def cmd_coverage(args):
    ws_url = get_ws_url(args.port)
    ws = WebSocketClient(ws_url)
    ws.connect()
    capture = CDPCapture(ws, args.project)
    capture.enable_domains()
    capture.start_js_coverage()
    capture.start_css_coverage()
    print(f"[cdp] Collecting coverage for {args.duration}s...")
    time.sleep(args.duration)
    js_cov = capture.stop_js_coverage()
    css_cov = capture.stop_css_coverage()
    report = {
        "timestamp": _ts(),
        "js_coverage": {"entries": len(js_cov), "data": js_cov[:100]},
        "css_coverage": {"entries": len(css_cov), "data": css_cov[:100]},
    }
    try:
        from gitlab_logcenter import get_logcenter

        lc = get_logcenter(args.project)
        lc.upload_bytes(
            json.dumps(report, indent=2, default=str).encode(),
            f"coverage_{_ts_short()}.json",
            category="reports",
            tags=["cdp", "coverage"],
        )
        print(f"[cdp] Coverage uploaded (JS={len(js_cov)}, CSS={len(css_cov)})")
    except Exception as e:
        local = f"/tmp/coverage_{_ts_short()}.json"
        with open(local, "w") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"[cdp] Saved locally: {local}")
    ws.close()


def cmd_perf(args):
    ws_url = get_ws_url(args.port)
    ws = WebSocketClient(ws_url)
    ws.connect()
    capture = CDPCapture(ws, args.project)
    capture.enable_domains()
    samples = []
    for i in range(args.samples):
        m = capture.get_performance_metrics()
        dom = capture.get_dom_counters()
        samples.append({"timestamp": _ts(), "metrics": m, "dom": dom})
        if i < args.samples - 1:
            time.sleep(args.interval)
    report = {"samples": samples, "count": len(samples)}
    try:
        from gitlab_logcenter import get_logcenter

        lc = get_logcenter(args.project)
        lc.upload_bytes(
            json.dumps(report, indent=2, default=str).encode(),
            f"perf_{_ts_short()}.json",
            category="reports",
            tags=["cdp", "performance"],
        )
        print(f"[cdp] Performance uploaded ({len(samples)} samples)")
    except Exception as e:
        print(json.dumps(report, indent=2, default=str))
    ws.close()


def main():
    parser = argparse.ArgumentParser(
        prog="cdp_browser_logger", description="Chrome CDP full-session browser capture"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_start = sub.add_parser("start", help="Start continuous capture")
    p_start.add_argument("--project", required=True)
    p_start.add_argument("--port", type=int, default=DEFAULT_CDP_PORT)
    p_start.add_argument("--fps", type=int, default=2)
    p_start.add_argument("--quality", type=int, default=60)
    p_start.set_defaults(func=cmd_start)

    p_stop = sub.add_parser("stop", help="Stop running capture")
    p_stop.set_defaults(func=cmd_stop)

    p_ss = sub.add_parser("capture-screenshot", help="Take one screenshot")
    p_ss.add_argument("--project", required=True)
    p_ss.add_argument("--port", type=int, default=DEFAULT_CDP_PORT)
    p_ss.add_argument("--name", default="")
    p_ss.set_defaults(func=cmd_screenshot)

    p_har = sub.add_parser("capture-har", help="Capture network traffic")
    p_har.add_argument("--project", required=True)
    p_har.add_argument("--port", type=int, default=DEFAULT_CDP_PORT)
    p_har.add_argument("--duration", type=int, default=30)
    p_har.set_defaults(func=cmd_har)

    p_con = sub.add_parser("dump-console", help="Capture console output")
    p_con.add_argument("--project", required=True)
    p_con.add_argument("--port", type=int, default=DEFAULT_CDP_PORT)
    p_con.add_argument("--duration", type=int, default=30)
    p_con.set_defaults(func=cmd_console)

    p_cov = sub.add_parser("dump-coverage", help="Capture JS/CSS coverage")
    p_cov.add_argument("--project", required=True)
    p_cov.add_argument("--port", type=int, default=DEFAULT_CDP_PORT)
    p_cov.add_argument("--duration", type=int, default=10)
    p_cov.set_defaults(func=cmd_coverage)

    p_perf = sub.add_parser("dump-perf", help="Capture performance metrics")
    p_perf.add_argument("--project", required=True)
    p_perf.add_argument("--port", type=int, default=DEFAULT_CDP_PORT)
    p_perf.add_argument("--samples", type=int, default=10)
    p_perf.add_argument("--interval", type=float, default=2.0)
    p_perf.set_defaults(func=cmd_perf)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
