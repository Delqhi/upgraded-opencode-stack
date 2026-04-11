---
name: sin-bridge
description: "OpenSIN Bridge + Vision Gate: The ONLY authorized browser automation interface for surveys, profiles, and web forms. Enforces mandatory screenshot + Gemini Vision verification after EVERY SINGLE web action. Zero blind clicks. Zero autorun."
license: Apache-2.0
compatibility: opencode
metadata:
  audience: all-agents
  workflow: browser-automation-with-vision-gate
  trigger: bridge, sin-bridge, prolific, survey, web-automation, browser-automation, vision-gate, screenshot-check
  version: v5.0.0-vision-gate
  priority: "-7.0"
---

# SIN-Bridge Skill v5.0 — Vision Gate Edition

> **PRIORITY -7.0 — ABSOLUTE OBERSTE REGEL IM GESAMTEN OPENSIN-ÖKOSYSTEM**
> Kein Agent darf jemals wieder eine einzige Web-Aktion ausführen ohne visuelle Verifikation durch das Vision-Modell.

---

## 1. WAS IST DIE OPENSIN-BRIDGE?

Die OpenSIN-Bridge ist eine Chrome Extension + HF MCP Server Architektur:

```
+------------------------+         +------------------------------+
|  Chrome Extension      |  WS     |  HF MCP Server               |
|  (Thin Client)         | <-----> |  (openjerro-opensin-bridge)   |
|                        |         |                               |
|  - DOM Extractor       |         |  - JSON-RPC Tool Interface    |
|  - Action Executor     |         |  - Accessibility Tree         |
|  - Shadow DOM Piercer  |         |  - Screenshot Capture         |
|  - Human Entropy       |         |  - Anti-Detection Logic       |
+------------------------+         +------------------------------+
         |                                    |
         v                                    v
    [Real Browser]                     [AI Agent via MCP]
```

**Bridge URL:** `https://openjerro-opensin-bridge-mcp.hf.space`
**Extension Path:** `/Users/jeremy/dev/OpenSIN-Bridge/extension`

---

## 2. VISION GATE — DAS HERZSTÜCK (PFLICHT BEI JEDER AKTION)

### 2.1 Das Problem (warum Vision Gate existiert)

Agenten haben blind drauflosgeklickt:
- Surveys gestartet aber nie Fragen beantwortet
- Modals bestätigt ohne zu lesen was drinsteht
- Tabs geöffnet und Endlosschleifen gestartet
- "Ich dachte es hat funktioniert" ohne Screenshot-Beweis

**Ein LLM SIEHT NICHT was auf dem Bildschirm passiert. Es RÄT. Raten ist VERBOTEN.**

### 2.2 Die Lösung: Screenshot + Vision-Check nach JEDER Aktion

```
SCHRITT 1: Aktion ausführen (URL, Klick, Tastendruck, Scroll, was auch immer)
SCHRITT 2: SOFORT Screenshot des GESAMTEN Bildschirms machen
SCHRITT 3: Screenshot an Vision-Modell senden mit Kontext-Prompt
SCHRITT 4: Vision-Modell-Antwort LESEN und VERSTEHEN
SCHRITT 5: NUR bei "PROCEED" → nächste Aktion erlaubt
           Bei "STOP" oder "RETRY" → Situation analysieren
```

### 2.3 Vision-Modell Spezifikation

**Primär:** `google/antigravity-gemini-3-flash` via OpenCode CLI
**Fallback:** `look-screen` CLI mit 6-Model Gemini REST API Chain

### 2.4 Vision-Prompt Template (PFLICHT bei jedem Check)

```
Du siehst einen Screenshot eines Browsers nach der Aktion: [BESCHREIBUNG DER AKTION].
Erwartetes Ergebnis: [WAS HÄTTE PASSIEREN SOLLEN].

Prüfe GENAU:
1. Ist das erwartete Ergebnis eingetreten? (JA/NEIN mit Begründung)
2. Gibt es Fehler, Warnungen, Captchas oder Popups? (JA/NEIN, wenn JA: welche?)
3. Ist die Seite vollständig geladen? (JA/NEIN)
4. Was zeigt der Bildschirm GENAU? (Beschreibe alle sichtbaren Elemente)
5. Was ist der empfohlene nächste Schritt? (Konkret)

Antworte mit: PROCEED wenn alles OK ist, STOP wenn etwas falsch ist, RETRY wenn die Aktion wiederholt werden sollte.
```

---

## 3. BRIDGE-WORKFLOW (EXAKTER ABLAUF — KEINE ABKÜRZUNGEN)

### 3.1 Vor dem Start: Health Check

```python
import urllib.request, json

# PFLICHT: Bridge Health prüfen BEVOR irgendwas passiert
health = json.loads(
    urllib.request.urlopen(
        "https://openjerro-opensin-bridge-mcp.hf.space/health",
        timeout=15
    ).read()
)
assert health.get("extensionConnected") is True, "Extension NICHT verbunden! STOP!"
```

### 3.2 Der 10-Schritt Vision-Gate-Workflow

```
 1. Bridge Health prüfen → extension_connected: true?
     ↓ FAIL? → Extension installieren (siehe §7)
 2. Tab navigieren: navigate → URL
 3. ★ VISION-GATE: take_screenshot → Vision-Check → PROCEED?
 4. DOM analysieren: get_accessibility_tree oder get_html
 5. ★ VISION-GATE: take_screenshot → Vision-Check → PROCEED?
 6. Element interagieren: click_element / type_text / select_option
 7. ★ VISION-GATE: take_screenshot → Vision-Check → PROCEED?
 8. Ergebnis prüfen: get_text / get_html
 9. ★ VISION-GATE: take_screenshot → Vision-Check → PROCEED?
10. Nächster Schritt NUR bei PROCEED vom Vision-Modell
```

**Jedes ★ ist ein PFLICHT-Checkpoint. Wer einen überspringt: SOFORTIGER PERMANENTER BAN.**

### 3.3 Python-Implementierung des Vision-Gate-Loops

```python
import subprocess, json, base64, urllib.request

# ============================================================================
# CONSTANTS — Bridge + Vision Konfiguration
# ============================================================================
BRIDGE_MCP_URL = "https://openjerro-opensin-bridge-mcp.hf.space/mcp"
BRIDGE_HEALTH_URL = "https://openjerro-opensin-bridge-mcp.hf.space/health"
MAX_STEPS = 40           # Absolute Obergrenze für Aktionen
MAX_RETRIES = 3          # Max aufeinanderfolgende RETRYs bevor STOP
MAX_NO_PROGRESS = 5      # Max Aktionen ohne sichtbaren Fortschritt

# ============================================================================
# VISION GATE — Das Herzstück
# ============================================================================
def vision_check(screenshot_base64: str, action_description: str, expected_result: str) -> str:
    """
    Sendet einen Screenshot an das Vision-Modell und gibt PROCEED/STOP/RETRY zurück.
    
    WHY: Ein LLM sieht nicht was auf dem Bildschirm passiert. 
         Ohne Vision-Check rät der Agent blind — und das ist VERBOTEN.
    
    CONSEQUENCES: Ohne diesen Check darf KEINE weitere Web-Aktion stattfinden.
    """
    prompt = f"""Du siehst einen Screenshot eines Browsers nach der Aktion: {action_description}.
Erwartetes Ergebnis: {expected_result}.

Prüfe GENAU:
1. Ist das erwartete Ergebnis eingetreten? (JA/NEIN mit Begründung)
2. Gibt es Fehler, Warnungen, Captchas oder Popups? (JA/NEIN, wenn JA: welche?)
3. Ist die Seite vollständig geladen? (JA/NEIN)
4. Was zeigt der Bildschirm GENAU? (Beschreibe alle sichtbaren Elemente)
5. Was ist der empfohlene nächste Schritt? (Konkret)

Antworte mit: PROCEED wenn alles OK ist, STOP wenn etwas falsch ist, RETRY wenn die Aktion wiederholt werden sollte."""
    
    # Vision-Modell aufrufen via opencode CLI (EINZIG ERLAUBTER WEG)
    result = subprocess.run(
        ["opencode", "run", prompt, "--format", "json"],
        capture_output=True, text=True, timeout=60,
    )
    
    parts = []
    for line in result.stdout.splitlines():
        try:
            ev = json.loads(line)
            if ev.get("type") == "text":
                parts.append(ev.get("part", {}).get("text", ""))
        except json.JSONDecodeError:
            pass
    
    response = "".join(parts).strip().upper()
    
    # Extraktion des Verdikts
    if "PROCEED" in response:
        return "PROCEED"
    elif "RETRY" in response:
        return "RETRY"
    else:
        return "STOP"


def vision_gate(screenshot_b64: str, action: str, expected: str, 
                step_number: int, retry_count: int) -> tuple[str, int]:
    """
    Führt den vollständigen Vision-Gate-Check durch.
    
    Returns: (verdict, updated_retry_count)
    
    WHY: Zentrale Funktion die den Vision-Gate-Loop steuert.
    CONSEQUENCES: Bei STOP muss der gesamte Workflow anhalten.
    """
    verdict = vision_check(screenshot_b64, action, expected)
    
    if verdict == "RETRY":
        retry_count += 1
        if retry_count >= MAX_RETRIES:
            print(f"[VISION-GATE] ❌ {MAX_RETRIES}x RETRY → FORCE STOP (Step {step_number})")
            return "STOP", retry_count
        print(f"[VISION-GATE] 🔄 RETRY #{retry_count} (Step {step_number})")
        return "RETRY", retry_count
    elif verdict == "STOP":
        print(f"[VISION-GATE] ❌ STOP bei Step {step_number}")
        return "STOP", 0
    else:
        print(f"[VISION-GATE] ✅ PROCEED (Step {step_number})")
        return "PROCEED", 0
```

---

## 4. BRIDGE MCP TOOLS (VERFÜGBARE WERKZEUGE)

### 4.1 Navigation

| Tool | Beschreibung | Vision-Gate danach? |
|------|-------------|---------------------|
| `navigate` | URL öffnen | **JA — PFLICHT** |
| `go_back` | Browser zurück | **JA — PFLICHT** |
| `go_forward` | Browser vorwärts | **JA — PFLICHT** |
| `reload` | Seite neu laden | **JA — PFLICHT** |

### 4.2 DOM-Interaktion

| Tool | Beschreibung | Vision-Gate danach? |
|------|-------------|---------------------|
| `click_element` | CSS-Selektor klicken | **JA — PFLICHT** |
| `type_text` | Text in Element eingeben | **JA — PFLICHT** |
| `select_option` | Dropdown-Option wählen | **JA — PFLICHT** |
| `get_text` | Text auslesen | Nein (read-only) |
| `get_html` | HTML auslesen | Nein (read-only) |
| `get_accessibility_tree` | DOM-Baum auslesen | Nein (read-only) |

### 4.3 Screenshots & Beobachtung

| Tool | Beschreibung | Vision-Gate danach? |
|------|-------------|---------------------|
| `take_screenshot` | Screenshot machen | Nein (IST der Gate-Input) |
| `tabs_list` | Tabs auflisten | Nein (read-only) |
| `tabs_activate` | Tab wechseln | **JA — PFLICHT** |

### 4.4 Tab-Management

| Tool | Beschreibung | Vision-Gate danach? |
|------|-------------|---------------------|
| `tabs_create` | Neuen Tab öffnen | **JA — PFLICHT** |
| `tabs_close` | Tab schließen | **JA — PFLICHT** |
| `tabs_update` | Tab aktualisieren | **JA — PFLICHT** |

**REGEL:** Alles was den Bildschirm VERÄNDERT braucht Vision-Gate. Alles was nur LIEST nicht.

---

## 5. ANTI-ENDLOSSCHLEIFEN-REGELN

```python
# ============================================================================
# ANTI-ENDLOSSCHLEIFEN-SCHUTZ
# ============================================================================
# 1. Nach 3 aufeinanderfolgenden RETRY → SOFORT STOPPEN
# 2. Nach 5 Aktionen ohne sichtbaren Fortschritt → SOFORT STOPPEN  
# 3. Nach MAX_STEPS (40) Gesamtaktionen → SOFORT STOPPEN
# 4. Bei jedem STOP: Screenshot + Kontext loggen, Issue erstellen
# ============================================================================

class VisionGateController:
    """
    Controller der den Vision-Gate-Loop steuert und Endlosschleifen verhindert.
    
    WHY: Ohne diesen Controller laufen Agenten in Endlosschleifen.
    CONSEQUENCES: Controller-Verletzung = SOFORTIGER PERMANENTER BAN.
    """
    
    def __init__(self):
        self.total_steps = 0
        self.consecutive_retries = 0
        self.no_progress_count = 0
        self.last_screenshot_hash = None
    
    def should_continue(self) -> bool:
        """Prüft ob der Agent weitermachen darf."""
        if self.total_steps >= MAX_STEPS:
            print(f"[GATE] ❌ MAX_STEPS ({MAX_STEPS}) erreicht → STOP")
            return False
        if self.consecutive_retries >= MAX_RETRIES:
            print(f"[GATE] ❌ {MAX_RETRIES}x RETRY → STOP")
            return False
        if self.no_progress_count >= MAX_NO_PROGRESS:
            print(f"[GATE] ❌ {MAX_NO_PROGRESS} Aktionen ohne Fortschritt → STOP")
            return False
        return True
    
    def record_step(self, verdict: str, screenshot_hash: str):
        """Zeichnet einen Schritt auf und aktualisiert Zähler."""
        self.total_steps += 1
        
        if verdict == "RETRY":
            self.consecutive_retries += 1
        else:
            self.consecutive_retries = 0
        
        # Fortschritts-Erkennung via Screenshot-Hash
        if screenshot_hash == self.last_screenshot_hash:
            self.no_progress_count += 1
        else:
            self.no_progress_count = 0
            self.last_screenshot_hash = screenshot_hash
```

---

## 6. VISION-CHECK METHODEN (4 WEGE)

### Methode A: Via webauto-nodriver-mcp observe_screen (BEVORZUGT wenn MCP aktiv)

```
1. observe_screen(include_dom="true")  → liefert Screenshot + DOM
2. Screenshot an Vision-Modell senden
3. Ergebnis auswerten
```

### Methode B: Via screencapture + look-screen CLI

```bash
# Screenshot machen
screencapture -x /tmp/opensin_vision_gate_step_XX.png

# Vision-Analyse anfordern
look-screen --screenshot /tmp/opensin_vision_gate_step_XX.png \
  --describe \
  --prompt "KONTEXT: Ich habe gerade [AKTION] ausgeführt. ..."
```

### Methode C: Via OpenSIN-Bridge take_screenshot (BEVORZUGT für Survey/Profil)

```python
# Bridge-Screenshot holen
screenshot_result = bridge_call("take_screenshot", {})
screenshot_b64 = screenshot_result.get("screenshot", "")

# An Vision-Modell senden
verdict = vision_check(screenshot_b64, "Klick auf 'Next'", "Nächste Frage erscheint")
```

### Methode D: Via multimodal-looker Subagent

```python
# task(subagent_type="multimodal-looker", prompt="Analysiere: ...")
```

---

## 7. EXTENSION INSTALLATION (WENN NICHT VERBUNDEN)

### 7.1 Schnell-Check

```python
import urllib.request, json

def is_bridge_connected() -> bool:
    """Prüft ob die Bridge-Extension verbunden ist."""
    try:
        health = json.loads(
            urllib.request.urlopen(
                "https://openjerro-opensin-bridge-mcp.hf.space/health",
                timeout=10
            ).read()
        )
        return health.get("extensionConnected") is True
    except Exception:
        return False
```

### 7.2 Keyboard-Installation (7 Schritte)

Siehe: `references/install-extension-via-keyboard.md`

**Schnell-Zusammenfassung:**
1. CMD+LEERTASTE (Spotlight öffnen)
2. "chrome" + ENTER (Chrome öffnen)
3. TAB 4x + ENTER (Adressleiste)
4. TAB 3x + LEERTASTE (Extensions-Bereich)
5. TAB 10x + ENTER (Developer Mode aktivieren)
6. TAB 2x + ENTER ("Entpackte Erweiterung laden" Button)
7. Extension-Ordner auswählen: `/Users/jeremy/dev/OpenSIN-Bridge/extension`

### 7.3 Auto-Install via AppleScript

```python
async def install_opensin_bridge_extension():
    """
    Installiert die OpenSIN Bridge Extension via macOS AppleScript.
    WHY: Wenn Extension nicht installiert, funktioniert kein Bridge-Tool.
    CONSEQUENCES: Ändert Chrome-Konfiguration dauerhaft.
    """
    extension_path = "/Users/jeremy/dev/OpenSIN-Bridge/extension"
    script = f'''
    tell application "System Events"
        key down command
        key down space
        key up space
        key up command
        delay 0.5
        keystroke "chrome"
        delay 0.3
        key code 36
        delay 2
        repeat 4 times
            key code 48
            delay 0.1
        end repeat
        key code 36
        delay 0.5
        repeat 3 times
            key code 48
            delay 0.1
        end repeat
        keystroke " "
        delay 0.5
        repeat 10 times
            key code 48
            delay 0.1
        end repeat
        key code 36
        delay 0.5
        repeat 2 times
            key code 48
            delay 0.1
        end repeat
        key code 36
        delay 1
        keystroke "{extension_path}"
        key code 36
        delay 1
    end tell
    '''
    import subprocess
    result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
    return result.returncode == 0
```

---

## 8. STEALTH FEATURES (ANTI-DETECTION)

Die Bridge hat eingebaute Anti-Detection-Funktionen:

| Feature | Beschreibung |
|---------|-------------|
| **Human Entropy** | Gaussian noise auf Klick-Koordinaten und Timing |
| **Shadow DOM Piercing** | Rekursive Traversierung von shadowRoot-Grenzen |
| **Deterministic Primitives** | Bekannte UI-Elemente werden mit harten Regeln behandelt, nicht AI-Raten |
| **Self-Healing Loops** | Wenn ein Klick keine DOM-Änderung erzeugt, feuern Fallback-Strategien |
| **Native Messaging Host** | CSP-Restrictions umgehen via stdio |

---

## 9. KONSEQUENZEN (ABSOLUT, KEINE DISKUSSION)

| Verstoß | Konsequenz |
|---------|------------|
| Web-Aktion ohne Screenshot danach | **SOFORTIGER PERMANENTER BAN** |
| Screenshot ohne Vision-Modell-Check | **SOFORTIGER PERMANENTER BAN** |
| Vision-Modell sagt STOP, Agent macht trotzdem weiter | **SOFORTIGER PERMANENTER BAN** |
| Autorun (mehrere Aktionen ohne Vision-Gate dazwischen) | **SOFORTIGER PERMANENTER BAN** |
| Survey/Profil-Arbeit ohne OpenSIN-Bridge | **SOFORTIGER PERMANENTER BAN** |
| "Ich dachte es hat funktioniert" ohne Screenshot-Beweis | **SOFORTIGER PERMANENTER BAN** |
| Endlosschleife ohne Vision-basierte Abbruch-Logik | **SOFORTIGER PERMANENTER BAN** |
| Direktes nodriver/CDP für Survey-Arbeit statt Bridge | **SOFORTIGER PERMANENTER BAN** |

---

## 10. WANN DIESEN SKILL NUTZEN

| Trigger | Aktion |
|---------|--------|
| "Prolific Profil ausfüllen" | Bridge + Vision Gate Workflow starten |
| "Survey ausfüllen" | Bridge + Vision Gate Workflow starten |
| "Web-Formular automatisieren" | Bridge + Vision Gate Workflow starten |
| "Browser-Automation mit Screenshots" | Bridge + Vision Gate Workflow starten |
| "sin-bridge" | Diesen Skill laden |
| "bridge health check" | §7.1 Health Check ausführen |
| "extension installieren" | §7.2/7.3 Extension Installation |

---

## 11. ZUSAMMENFASSUNG IN EINEM SATZ

**KEIN EINZIGER KLICK, KEIN EINZIGER TASTENDRUCK, KEINE EINZIGE URL, KEINE EINZIGE WEB-AKTION OHNE DASS `antigravity-gemini-3-flash` VORHER EINEN SCREENSHOT DES GESAMTEN BILDSCHIRMS ANALYSIERT UND MIT "PROCEED" BESTÄTIGT HAT. PUNKT. KEINE AUSNAHMEN. NIEMALS.**

---

## 12. RESSOURCEN

- [OpenSIN-Bridge Repo](https://github.com/OpenSIN-AI/OpenSIN-Bridge)
- [Bridge HF Space](https://openjerro-opensin-bridge-mcp.hf.space)
- [Vision Gate Mandate in AGENTS.md](~/.config/opencode/AGENTS.md) — Zeile 1
- [Gemini Vision API](https://ai.google.dev/gemini-api/docs/vision)
- Extension Path: `/Users/jeremy/dev/OpenSIN-Bridge/extension`
