# OpenSIN Bridge — Browser Automation Skill

> **Die wichtigste Entwicklung der OpenSIN-AI Organisation.**
> Eine Chrome Extension mit 39 MCP Tools, die Antigravity und Claude Code in ALLEN Kategorien schlägt.

## Architektur

```
AI Agent (via opencode CLI)
        │
        ▼ (WebSocket)
HF MCP Server (immer online)
  wss://openjerro-opensin-bridge-mcp.hf.space
        │
        ▼ (WebSocket)
OpenSIN Bridge v2.6.0 (Chrome Extension)
        │
        ▼ (Chrome APIs)
Chrome Browser (deine Sessions, deine Cookies)
```

## Quick Start

### 1. Extension laden (einmalig)
```bash
# Repo clonen
git clone https://github.com/OpenSIN-AI/OpenSIN-backend.git
cd OpenSIN-backend/services/sin-chrome-extension

# In Chrome laden:
# 1. chrome://extensions/ öffnen
# 2. Entwicklermodus aktivieren
# 3. "Entpackte Erweiterung laden" → extension/ Ordner
```

### 2. MCP Server nutzen (immer online)
Der HF MCP Server läuft bereits und ist immer erreichbar:
- **URL:** https://huggingface.co/spaces/OpenJerro/opensin-bridge-mcp
- **Health:** https://openjerro-opensin-bridge-mcp.hf.space/health
- **WebSocket:** `wss://openjerro-opensin-bridge-mcp.hf.space`

## Verfügbare Tools (39)

### Tab Management (5)
- `tabs_list` — Alle Tabs auflisten
- `tabs_create` — Neuen Tab öffnen
- `tabs_update` — Tab aktualisieren
- `tabs_close` — Tab schließen
- `tabs_activate` — Tab aktivieren

### Navigation (4)
- `navigate` — Zu URL navigieren
- `go_back` — Zurück
- `go_forward` — Vorwärts
- `reload` — Seite neu laden

### DOM Interaction (8)
- `click_element` — Element klicken (React-kompatibel)
- `type_text` — Text eingeben
- `get_text` — Textinhalt lesen
- `get_html` — HTML lesen
- `get_attribute` — Attribut lesen
- `wait_for_element` — Auf Element warten
- `execute_script` — JavaScript ausführen (CSP-safe)
- `inject_css` — CSS injizieren

### Page Info (3)
- `get_page_info` — Title, URL, readyState
- `get_all_links` — Alle Links extrahieren
- `get_all_inputs` — Alle Formularfelder extrahieren

### Screenshot & Video (5)
- `screenshot` — Screenshot machen
- `screenshot_full` — Vollständiger Screenshot
- `start_recording` — Videoaufnahme starten
- `stop_recording` — Videoaufnahme stoppen
- `recording_status` — Aufnahmestatus prüfen

### Cookies (4)
- `get_cookies` — Cookies lesen
- `set_cookie` — Cookie setzen
- `delete_cookie` — Cookie löschen
- `clear_cookies` — Alle Cookies löschen

### Storage (3)
- `storage_get` — Local Storage lesen
- `storage_set` — Local Storage schreiben
- `storage_clear` — Local Storage löschen

### Network (2)
- `get_network_requests` — Request-Log lesen
- `block_url` — URL blockieren

### Stealth Mode (2)
- `enable_stealth` — Anti-Detection aktivieren
- `stealth_status` — Stealth-Status prüfen

### Prolific (1)
- `extract_prolific_studies` — Verfügbare Studies extrahieren

### System (3)
- `health` — Extension-Status prüfen
- `list_tools` — Alle Tools auflisten
- `offscreen_status` — Offscreen-Dokument-Status

## Beispiele

### Study auf Prolific finden und öffnen
```python
import asyncio, websockets, json

async def find_study():
    async with websockets.connect('wss://openjerro-opensin-bridge-mcp.hf.space/agent') as ws:
        # Navigate to Prolific
        await ws.send(json.dumps({
            'method': 'navigate',
            'params': {'url': 'https://app.prolific.com/studies'},
            'id': 1
        }))
        await asyncio.sleep(15)  # Wait for React SPA
        
        # Extract studies
        await ws.send(json.dumps({
            'method': 'extract_prolific_studies',
            'id': 2
        }))
        resp = await ws.recv()
        result = json.loads(resp)
        print(f"Studies: {result}")

asyncio.run(find_study())
```

### Stealth Mode aktivieren
```python
await ws.send(json.dumps({
    'method': 'enable_stealth',
    'id': 3
}))
```

### Screenshot machen
```python
await ws.send(json.dumps({
    'method': 'screenshot',
    'id': 4
}))
```

## Prolific Worker

Der **A2A-SIN-Worker-Prolific** läuft 24/7 und prüft automatisch alle 5 Minuten auf verfügbare Studies:

```bash
# Worker starten
cd /Users/jeremy/dev/A2A-SIN-Worker-Prolific
python3 src/worker.py

# Production Mode (navigiert zu Plattformen)
TEST_MODE=false python3 src/worker.py
```

## Vergleich: OpenSIN Bridge vs Claude Code

| Feature | Claude Code | OpenSIN Bridge v2.6.0 |
|---------|-------------|----------------------|
| Tools | ~5 | **39** |
| Video Recording | ❌ | ✅ |
| Stealth Mode | ❌ | ✅ |
| Cookie CRUD | ❌ | ✅ |
| Network Logging | ❌ | ✅ |
| URL Blocking | ❌ | ✅ |
| Offscreen Processing | ❌ | ✅ |
| 24/7 Worker | ❌ | ✅ |
| Open Source | ❌ | ✅ |
| Local Privacy | ❌ (Cloud Relay) | ✅ (Unix Socket) |

## Wichtige Hinweise

1. **CSP-Safe execute_script**: Alle Script-Injections nutzen den `code` Parameter, nicht `func`. Das umgeht Chrome's CSP `unsafe-eval` Restriction.

2. **Single Tab Mode**: Der Worker öffnet niemals neue Tabs für dieselbe Plattform. Er reused existierende Tabs, um Ban-Risiken zu minimieren.

3. **Safe Mode**: Standardmäßig läuft der Worker im `TEST_MODE=true`, der keine Navigation zu Plattformen durchführt. Für Production: `TEST_MODE=false`.

4. **Session Detection**: Der Worker erkennt automatisch abgelaufene Sessions (Login-Redirects) und wartet auf manuelles Einloggen, statt zu crashen.

## Links

- 📦 **Repo:** https://github.com/OpenSIN-AI/OpenSIN-backend/tree/main/services/sin-chrome-extension
- 🤖 **Worker:** https://github.com/OpenSIN-AI/A2A-SIN-Worker-Prolific
- 🌐 **HF MCP Server:** https://huggingface.co/spaces/OpenJerro/opensin-bridge-mcp
- 📖 **Dokumentation:** https://opensin.ai/docs/bridges/opensin-bridge-overview
- 📝 **Blog Post:** https://github.com/OpenSIN-AI/OpenSIN-Marketing-Release-Strategie/blob/main/blog-posts/21-opensin-bridge-vs-claude-code.md
