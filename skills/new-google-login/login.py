"""Google Chrome Login Helper for the Antigravity Token-Refresh-Service.

TWO MODES:
  1. standalone (--attach NOT set):
       Startet Chrome selbst, loggt via AppleScript + Vision-Gate ein.
       Gedacht für manuelles Testen / interaktiven Gebrauch.

  2. attach (--attach set):
       Chrome läuft BEREITS (gestartet von nodriver/chrome_login.py auf --port).
       Verbindet sich direkt per CDP (requests + WebSocket) und tippt Email/Passwort
       ohne AppleScript oder Vision-Gate — weil nodriver-Chrome kein sichtbares
       macOS-Fenster ist das AppleScript ansprechen könnte.
       Öffnet accounts.google.com/ServiceLogin, tippt Email → Next → Passwort → Next.
       Gibt exit code 0 bei Erfolg, 1 bei Fehler.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path


# ── Brain log ─────────────────────────────────────────────────────────────────


def log_to_brain(msg: str):
    """Schreibt in stdout (wird von chrome_login.py als log.error/debug erfasst)
    und in eine lokale Logdatei zur Diagnose."""
    print(f"[BRAIN LOG] {msg}", flush=True)
    try:
        log_file = (
            Path.home()
            / ".config"
            / "openAntigravity-auth-Token-Refresh-Service"
            / "login_helper.log"
        )
        with open(log_file, "a") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")
    except Exception:
        pass


# ── CDP helpers ────────────────────────────────────────────────────────────────


def _cdp_get_targets(port: int) -> list:
    """Fragt den Chrome CDP-Endpoint nach allen offenen Tabs/Targets."""
    import urllib.request

    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=5) as r:
            return json.loads(r.read())
    except Exception as e:
        log_to_brain(f"CDP /json failed: {e}")
        return []


def _cdp_get_browser_ws_url(port: int) -> str | None:
    """Liest die Browser-WebSocket-URL aus /json/version.

    Warum das nötig ist:
    Manche Chrome-Starts liefern zunächst keinen page-target in /json,
    aber immer ein browser-level websocket. Darüber können wir per
    Target.createTarget selbst einen leeren Tab erzeugen.
    """
    import urllib.request

    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/json/version", timeout=5
        ) as r:
            data = json.loads(r.read())
            return data.get("webSocketDebuggerUrl")
    except Exception as e:
        log_to_brain(f"CDP /json/version failed: {e}")
        return None


def _cdp_send(ws_url: str, method: str, params: dict | None = None) -> dict:
    """Sendet einen CDP-Befehl per WebSocket und wartet auf die Antwort.
    Verwendet websocket-client falls vorhanden, sonst websockets (asyncio).
    Fallback: subprocess mit node -e (immer verfügbar wenn node da ist).
    """
    params = params or {}
    import json as _json

    # Versuch 1: websocket-client (sync, kein asyncio nötig)
    try:
        import websocket  # websocket-client package

        # Chrome rejects the default websocket-client Origin header on DevTools
        # connections from attach mode, so we suppress Origin entirely.
        ws = websocket.create_connection(ws_url, timeout=10, suppress_origin=True)
        cmd_id = 1
        ws.send(_json.dumps({"id": cmd_id, "method": method, "params": params}))
        # Lese Antworten bis unsere id auftaucht
        for _ in range(20):
            raw = ws.recv()
            msg = _json.loads(raw)
            if msg.get("id") == cmd_id:
                ws.close()
                return msg.get("result", {})
        ws.close()
        return {}
    except ImportError:
        pass
    except Exception as e:
        log_to_brain(f"websocket-client send failed ({method}): {e}")
        return {}


def _cdp_navigate(ws_url: str, url: str):
    _cdp_send(ws_url, "Page.navigate", {"url": url})
    time.sleep(2.0)  # Warte auf Seitenlade


def _cdp_eval(ws_url: str, expr: str) -> str | None:
    """Führt JavaScript im Tab aus und gibt den Stringwert zurück."""
    result = _cdp_send(
        ws_url,
        "Runtime.evaluate",
        {
            "expression": expr,
            "returnByValue": True,
            "awaitPromise": False,
        },
    )
    try:
        return result.get("result", {}).get("value")
    except Exception:
        return None


def _cdp_type(ws_url: str, text: str):
    """Tippt Text Zeichen für Zeichen via CDP Input.dispatchKeyEvent.
    Deutlich zuverlässiger als clipboard-paste bei Google-Formularen."""
    for ch in text:
        _cdp_send(
            ws_url,
            "Input.dispatchKeyEvent",
            {
                "type": "keyDown",
                "text": ch,
                "key": ch,
            },
        )
        _cdp_send(
            ws_url,
            "Input.dispatchKeyEvent",
            {
                "type": "keyUp",
                "text": ch,
                "key": ch,
            },
        )
        time.sleep(0.04)  # Kleines Delay gegen Bot-Erkennung


def _cdp_press_enter(ws_url: str):
    """Schickt Enter-Taste per CDP."""
    _cdp_send(
        ws_url,
        "Input.dispatchKeyEvent",
        {
            "type": "keyDown",
            "key": "Enter",
            "code": "Enter",
            "nativeVirtualKeyCode": 13,
        },
    )
    _cdp_send(
        ws_url,
        "Input.dispatchKeyEvent",
        {"type": "keyUp", "key": "Enter", "code": "Enter", "nativeVirtualKeyCode": 13},
    )
    time.sleep(2.0)


def _cdp_click_selector(ws_url: str, selector: str):
    """Klickt ein Element per CDP (JavaScript querySelector + click)."""
    _cdp_eval(ws_url, f"document.querySelector({json.dumps(selector)})?.click()")
    time.sleep(1.5)


def _find_page_ws_url(port: int, timeout: float = 15.0) -> str | None:
    """Findet die WebSocket-URL des ersten sichtbaren Page-Targets auf dem CDP-Port.
    Wartet bis zu `timeout` Sekunden bis Chrome bereit ist."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        targets = _cdp_get_targets(port)
        for t in targets:
            if t.get("type") == "page":
                return t.get("webSocketDebuggerUrl")

        # Wenn Chrome noch keinen page-target bereitgestellt hat, erzeugen wir
        # selbst einen leeren Tab über den Browser-Target-WebSocket.
        browser_ws = _cdp_get_browser_ws_url(port)
        if browser_ws:
            try:
                _cdp_send(browser_ws, "Target.createTarget", {"url": "about:blank"})
            except Exception as e:
                log_to_brain(f"Target.createTarget failed: {e}")

        time.sleep(0.5)
    return None


# ── Attach mode: reines CDP-Login ─────────────────────────────────────────────


def cdp_login(email: str, password: str, port: int) -> bool:
    """Loggt einen Google-Account per reinem CDP ein.

    Erwartet einen BEREITS laufenden Chrome-Prozess auf `port`.
    Kein AppleScript, kein Vision-Gate — direkte CDP-Steuerung.

    Flow:
      1. Ersten Page-Tab via /json finden
      2. Zu accounts.google.com/ServiceLogin navigieren
      3. Email eingeben + Next
      4. Passwort eingeben + Next
      5. Prüfen ob URL von accounts.google.com weggegangen ist (= Erfolg)
    """
    log_to_brain(f"CDP login starting for {email} on port {port}")

    # Schritt 1: WebSocket URL des Page-Tabs holen
    ws_url = _find_page_ws_url(port, timeout=20.0)
    if not ws_url:
        log_to_brain(f"ERROR: No page target found on CDP port {port}")
        return False
    log_to_brain(f"CDP page target: {ws_url[:80]}...")

    # Schritt 2: Zu Google Login navigieren
    # Wir öffnen direkt die Email-Eingabe-URL von Google
    login_url = "https://accounts.google.com/ServiceLogin?hl=en"
    log_to_brain(f"Navigating to {login_url}")
    _cdp_navigate(ws_url, login_url)
    time.sleep(3.0)

    # Schritt 3: Email-Feld suchen und füllen
    # Google verwendet '#identifierId' für das Email-Input
    log_to_brain(f"Typing email: {email}")
    _cdp_click_selector(ws_url, "#identifierId")
    time.sleep(0.5)
    _cdp_type(ws_url, email)
    time.sleep(0.5)

    # Schritt 4: Next-Button klicken (id=identifierNext)
    log_to_brain("Clicking Next after email")
    _cdp_click_selector(ws_url, "#identifierNext")
    time.sleep(3.5)  # Warte auf Passwort-Seite

    # Schritt 5: Passwort-Feld suchen (name="Passwd" oder type="password")
    log_to_brain("Typing password")
    # Versuche verschiedene Selektoren — Google ändert diese gelegentlich
    for sel in ['input[type="password"]', '[name="Passwd"]', "#password input"]:
        val = _cdp_eval(ws_url, f"!!document.querySelector({json.dumps(sel)})")
        if val:
            _cdp_click_selector(ws_url, sel)
            time.sleep(0.3)
            _cdp_type(ws_url, password)
            break
    else:
        log_to_brain("ERROR: Password field not found")
        return False

    # Schritt 6: Next nach Passwort (id=passwordNext)
    log_to_brain("Clicking Next after password")
    _cdp_click_selector(ws_url, "#passwordNext")
    time.sleep(4.0)

    # Schritt 7: Prüfen ob Login erfolgreich war
    # Erfolg = URL ist NICHT mehr auf accounts.google.com/ServiceLogin
    current_url = _cdp_eval(ws_url, "window.location.href") or ""
    log_to_brain(f"Post-login URL: {current_url[:100]}")

    if (
        "ServiceLogin" not in current_url
        and "accounts.google.com/signin" not in current_url
    ):
        log_to_brain(f"✅ CDP login SUCCESS for {email}")
        return True
    else:
        log_to_brain(f"❌ CDP login FAILED - still on login page: {current_url[:100]}")
        return False


# ── Standalone mode: AppleScript + Vision-Gate ────────────────────────────────


def run_applescript(script: str) -> bool:
    try:
        subprocess.run(["osascript", "-e", script], check=True)
        return True
    except subprocess.CalledProcessError as e:
        log_to_brain(f"AppleScript Error: {e}")
        return False


def vision_gate(step_name: str, expected: str) -> str:
    screenshot_path = f"/tmp/vision_{step_name.replace(' ', '_')}.png"
    subprocess.run(["screencapture", "-x", screenshot_path])

    prompt = (
        f"Du siehst einen Screenshot nach der Aktion: {step_name}. "
        f"Erwartetes Ergebnis: {expected}. "
        f"Prüfe genau: Ist das erwartete Ergebnis eingetreten? "
        f"Antworte mit: PROCEED wenn OK, STOP wenn Fehler, RETRY wenn nötig."
    )
    log_to_brain(f"Requesting Vision Gate for {step_name}...")
    try:
        cmd = [
            "opencode",
            "run",
            f"Image: {screenshot_path}. {prompt}",
            "--model",
            "nvidia/meta/llama-3.2-11b-vision-instruct",
            "--format",
            "json",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        out = res.stdout.upper()
        if "PROCEED" in out:
            log_to_brain(f"Vision Check PROCEED: {step_name}")
            return "PROCEED"
        elif "RETRY" in out:
            log_to_brain(f"Vision Check RETRY: {step_name}")
            return "RETRY"
        else:
            log_to_brain(f"Vision Check STOP/FAILED: {step_name}. Output: {out[:100]}")
            return "STOP"
    except Exception as e:
        log_to_brain(f"Vision CLI Failed: {e}")
        return "STOP"


def perform_vision_step(
    step_name: str, action_script: str, expected: str, retries: int = 3
):
    for attempt in range(retries):
        log_to_brain(f"Executing Action: {step_name} (Attempt {attempt + 1})")
        if action_script:
            run_applescript(action_script)
            time.sleep(2.0)
        status = vision_gate(step_name, expected)
        if status == "PROCEED":
            return True
        elif status == "STOP":
            log_to_brain(f"ABORTING flow at {step_name} due to STOP signal.")
            sys.exit(1)
    log_to_brain(f"ABORTING flow at {step_name} due to max retries.")
    sys.exit(1)


def standalone_chrome_login_vision_gated(
    email: str, password: str, port: int, profile_dir: str
):
    """Standalone-Modus: startet Chrome selbst und loggt via AppleScript+Vision ein."""
    log_to_brain(f"Starting STANDALONE VISION GATED Chrome login for {email}")

    chrome_cmd = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        f"--user-data-dir={profile_dir}",
        f"--remote-debugging-port={port}",
        "--disable-search-engine-choice-screen",
        "--no-default-browser-check",
        "--no-first-run",
        "--disable-popup-blocking",
        "about:blank",
    ]
    subprocess.Popen(chrome_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(3.0)

    perform_vision_step(
        "Activate Chrome",
        'tell application "Google Chrome" to activate',
        "Chrome is the active window, showing a blank page (about:blank)",
    )
    perform_vision_step(
        "Focus URL Bar",
        'tell application "System Events" to keystroke "l" using command down',
        "The URL address bar is focused/highlighted",
    )
    perform_vision_step(
        "Tab to Profile Icon",
        'tell application "System Events" to key code 48',
        "The Profile icon in the Chrome toolbar is focused/highlighted",
    )
    perform_vision_step(
        "Open Profile Dropdown",
        'tell application "System Events" to keystroke " "',
        "The Profile dropdown menu is open and visible",
    )
    perform_vision_step(
        "Tab to Sign In Button",
        'tell application "System Events" to key code 48',
        "The 'Sign in' (Anmelden) or 'Turn on sync' button is focused",
    )
    perform_vision_step(
        "Click Sign In Button",
        'tell application "System Events" to keystroke " "',
        "The Google Login page (accounts.google.com) is fully loaded",
    )
    perform_vision_step(
        "Type Email",
        f'tell application "System Events" to keystroke "{email}"',
        f"The email field contains '{email}'",
    )
    perform_vision_step(
        "Submit Email",
        'tell application "System Events" to key code 36',
        "The password input field is now visible and focused",
    )
    perform_vision_step(
        "Type Password",
        f'tell application "System Events" to keystroke "{password}"',
        "The password field contains characters (dots/asterisks)",
    )
    perform_vision_step(
        "Submit Password",
        'tell application "System Events" to key code 36',
        "The login was successful and we are redirected, or a Sync prompt is shown",
    )
    log_to_brain("✅ Vision-Gated Login Flow Completed Successfully")


# ── Entrypoint ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Google Chrome Login Helper")
    parser.add_argument("--email", required=True, help="Google account email")
    parser.add_argument("--password", required=True, help="Google account password")
    parser.add_argument("--port", type=int, default=7654, help="Chrome CDP port")
    parser.add_argument("--profile-dir", required=True, help="Chrome user-data-dir")
    parser.add_argument(
        "--attach",
        action="store_true",
        help="Attach to already-running Chrome via CDP (no AppleScript, no Vision-Gate). "
        "Used by the Token-Refresh-Service when nodriver has already launched Chrome.",
    )
    args = parser.parse_args()

    if args.attach:
        # ── CDP Mode: nodriver hat Chrome bereits gestartet ──
        # Kein AppleScript, kein Vision-Gate, direktes CDP-Login
        ok = cdp_login(args.email, args.password, args.port)
        sys.exit(0 if ok else 1)
    else:
        # ── Standalone Mode: Chrome selbst starten + Vision-Gate ──
        standalone_chrome_login_vision_gated(
            args.email, args.password, args.port, args.profile_dir
        )
        sys.exit(0)
