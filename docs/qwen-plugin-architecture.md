# opencode-qwen-auth Plugin — Architektur & Troubleshooting

## Übersicht

`opencode-qwen-auth` ist das Multi-Account Auth-Plugin für den Qwen-Provider in OpenCode. Es verwaltet Token-Rotation, Health-Tracking und automatische Account-Auswahl via Hybrid-Strategie.

**Version:** 0.3.4  
**Installationspfad (Source):** `/Users/jeremy/dev/upgraded-opencode-stack/local-plugins/opencode-qwen-auth/`  
**Installationspfad (Runtime):** `/Users/jeremy/.config/opencode/local-plugins/opencode-qwen-auth/`  
**Konfigurationsdatei:** `/Users/jeremy/.config/opencode/qwen-auth-accounts.json`  
**Datenbank (OpenCode Core):** `/Users/jeremy/.local/share/opencode/opencode.db` (Tabellen: `account`, `account_state`, `control_account`)

---

## 🚨 KRITISCHE REGEL: NIEMALS qwen-auth-accounts.json MIT PYTHON ÜBERSCHREIBEN!

**Lesson Learned (2026-04-15):** Qwen verwendet **Refresh Token Rotation** — bei jedem erfolgreichen Refresh gibt Qwen einen NEUEN Refresh Token zurück und der ALTE wird sofort ungültig. Wenn ein Python-Skript die Datei überschreibt, während das Plugin den Token gerade rotiert hat, geht der NEUE Token verloren und der ALTE ist bereits gesperrt → **Account ist tot!**

**Regeln:**
1. **NIEMALS** `qwen-auth-accounts.json` mit Python/externen Skripten überschreiben, während OpenCode läuft
2. **NUR** `/connect` in OpenCode verwenden, um neue Accounts hinzuzufügen
3. **NUR** manuelle Edits, wenn OpenCode GESTOPPT ist
4. Nach jedem `/connect` SOFORT das `email`-Feld setzen (siehe unten)

---

## 🚨 KRITISCHE REGEL: EMAIL-FELD NACH /CONNECT SETZEN!

**Problem:** Das Plugin hat KEIN `email`-Feld im Account-Schema. Wenn mehrere Accounts mit verschiedenen Google-Emails existieren, kann man sie nicht unterscheiden. Rate-Limits pro Account funktionieren zwar (über accountIndex), aber man weiß nicht, welcher Account zu welcher Email gehört.

**Lösung:** Nach JEDEM `/connect` MUSS das `email`-Feld manuell in `qwen-auth-accounts.json` gesetzt werden!

**Schritt-für-Schritt:**
1. `/connect` in OpenCode ausführen → neuen Account hinzufügen
2. OpenCode STOPPEN
3. `qwen-auth-accounts.json` öffnen
4. Beim NEUEN Account (letzter in der Liste) das Feld `"email"` hinzufügen:
   ```json
   {
     "refreshToken": "...",
     "accessToken": "...",
     "email": "kundenservice@zukunftsorientierte-energie.info",
     ...
   }
   ```
5. Datei speichern
6. OpenCode neu starten

**WICHTIG:** Das `email`-Feld wird vom Spread-Operator (`...current, ...account`) in `mergeAccounts()` und `updateAccount()` automatisch erhalten — es geht also NICHT verloren bei Plugin-Schreibvorgängen. ABER: Bei Refresh-Token-Rotation erstellt `ensureStorage()` einen NEUEN Account ohne Email → dann muss die Email neu gesetzt werden.

**Bekannte Google-Accounts für Qwen:**
| Email | Zweck | Chrome-Profil |
|-------|-------|---------------|
| `zukunftsorientierte.energie@gmail.com` | Privat | Default |
| `info@zukunftsorientierte-energie.de` | Workspace/Business | Geschäftlich |
| `kundenservice@zukunftsorientierte-energie.info` | Kundenservice | Default |
| `Token-Refresh-Service-1774475475@zukunftsorientierte-energie.de` | Primary Token-Refresh-Service | Default |

---

## 🚨 REFRESH TOKEN ROTATION — WIE QWEN OAUTH WIRKLICH FUNKTIONIERT

**Qwen OAuth Flow (Device Flow RFC 8628):**

1. **Device Code anfordern:** `POST https://chat.qwen.ai/api/v1/oauth2/device/code`
   - Client-ID: `f0304373b74a44d2b584a3fb70ca9e56`
   - PKCE: Code Challenge + Verifier
   - Response: `device_code`, `user_code`, `verification_uri`, `expires_in=900` (15 Min)

2. **Benutzer autorisieren:** Browser öffnet `https://chat.qwen.ai/authorize?user_code=XXX`
   - User klickt "Bestätigen" mit seinem Google-Account
   - Erfolgsmeldung: "Authentifizierung erfolgreich"

3. **Token abholen:** `POST https://chat.qwen.ai/api/v1/oauth2/token`
   - `grant_type=urn:ietf:params:oauth:grant-type:device_code`
   - `code_verifier=` (PKCE-Verifier vom Schritt 1)
   - Response: `access_token` (86 chars), `refresh_token` (86 chars), `expires_in=21600` (6 Std)

4. **Token Refresh:** `POST https://chat.qwen.ai/api/v1/oauth2/token`
   - `grant_type=refresh_token`
   - ⚠️ **ROTATION:** Qwen gibt einen NEUEN `refresh_token` zurück und der ALTE wird sofort ungültig!
   - Neue `expires_in=21600` (6 Std)

5. **API-Call:** `POST https://portal.qwen.ai/v1/chat/completions`
   - `Authorization: Bearer {access_token}`
   - Model: `qwen3-coder-plus`

**Endpoints:**
| Zweck | URL |
|-------|-----|
| Device Code | `https://chat.qwen.ai/api/v1/oauth2/device/code` |
| Token (alle) | `https://chat.qwen.ai/api/v1/oauth2/token` |
| Autorisierung | `https://chat.qwen.ai/authorize` |
| Chat API | `https://portal.qwen.ai/v1/chat/completions` |
| ~~Passport~~ | `passport.qwen.ai` ❌ **EXISTIERT NICHT** (NXDOMAIN) |

**Quota:** Jeder Qwen-Account hat ~1000 Requests/Tag kostenlos. Bei Überschreitung: `insufficient_quota` Fehler.

---

## 🚨 KNOWN ISSUE: PLUGIN VERLIERT ROTATED REFRESH TOKENS

**Was passiert:** Wenn das Plugin einen Token erfolgreich refreshed, bekommt es einen NEUEN `refresh_token` vom Server. Das Plugin speichert den neuen Token via `updateAccount()` + `saveAccounts()`. ABER: Wenn währenddessen ein anderer Prozess (Python-Skript, anderes opencode-Fenster) die Datei überschreibt, geht der neue Token verloren → der alte ist bereits gesperrt → Account ist tot.

**Workaround:** Nach `/connect` IMMER OpenCode neu starten und die Accounts in Ruhe lassen. Keine externen Skripte auf die Datei loslassen!

---

## Architektur

### Dateistruktur

```
opencode-qwen-auth/
├── dist/
│   ├── index.js                    # Plugin Entry Point
│   └── src/
│       ├── plugin.js               # Main Plugin Logic
│       ├── plugin/
│       │   ├── account.js          # 🔑 Kern-Datei: Account-Storage & Rotation
│       │   ├── auth.js              # Auth-Flow
│       │   ├── rotation.js          # Hybrid-Rotation-Algorithmus
│       │   ├── token.js             # Token-Management
│       │   ├── logger.js            # Logging
│       │   ├── types.js             # TypeScript Types
│       │   └── config/              # Plugin-Konfiguration
│       │       ├── index.js
│       │       ├── schema.js
│       │       └── loader.js
│       ├── qwen/
│       │   └── oauth.js             # Qwen OAuth Flow
│       ├── cli/
│       │   └── install.js           # CLI Install Helper
│       └── transform/               # Request/Response Transformation
│           ├── index.js
│           ├── request.js
│           ├── response.js
│           └── sse.js
├── package.json
├── README.md
└── LICENSE
```

### Datenfluss

```
opencode CLI startet
  → Plugin lädt qwen-auth-accounts.json via loadAccounts()
  → normalizeStorage() filtert ungültige Accounts
  → Bei API-Call: selectAccount() wählt besten Account (Hybrid-Strategie)
  → Bei Erfolg: recordSuccess() → consecutiveFailures = 0
  → Bei Fehlschlag: recordFailure() → consecutiveFailures + 1
  → Bei Rate-Limit: markRateLimited() → rateLimitResetAt gesetzt
  → Bei Save: saveAccounts() → mergeAccounts() + normalizeStorage() → atomic write
```

---

## 🔑 Kernfunktionen in account.js

### `normalizeStorage(storage)` — Der Filter

**Was es tut:** Filtert die Account-Liste und setzt activeIndex auf einen gültigen Wert.

**PATCH V2 (2026-04-15):** Erweiterte Filter-Logik die drei Bedingungen prüft:

```javascript
// PATCH V2: Erweiterte Filterung
function normalizeStorage(storage) {
    const MAX_CONSECUTIVE_FAILURES = 20;
    const now = Date.now();
    const accounts = storage.accounts.filter((account) => {
        if (!account?.refreshToken) return false;
        if ((account.health?.consecutiveFailures ?? 0) > MAX_CONSECUTIVE_FAILURES) return false;
        const hasExpiredToken = !account.accessToken && (!account.expires || account.expires < now);
        const hasHighFailures = (account.health?.failureCount ?? 0) > 50;
        if (hasExpiredToken && hasHighFailures) return false;
        return true;
    });
    // ... rest
}
```

**Warum V2 statt V1:**
- V1 filterte nur `consecutiveFailures > 20` — aber Accounts mit `consecutiveFailures=0` und totem Refresh Token wurden nicht gefiltert
- V2 filtert zusätzlich: Accounts ohne AccessToken UND mit >50 totalen Fehlern → die sind mit Sicherheit tot (expired refresh token)
- Grace Period: Ein Account ohne AccessToken aber mit wenigen Fehlern bekommt eine Chance (vielleicht war es nur ein temporärer Netzwerkfehler)

### `mergeAccounts(existing, incoming)` — Der Merge-Algorithmus

**Was es tut:** Merged zwei Account-Listen anhand des `refreshToken` als Schlüssel.

**Kritisch:** Diese Funktion **fügt nur hinzu oder aktualisiert** — sie **löscht niemals** Accounts! Wenn ein Account in der existierenden Liste ist, bleibt er für immer.

**Daher:** Der `normalizeStorage()`-Patch ist die EINZIGE Möglichkeit, tote Accounts automatisch zu entfernen.

### `saveAccounts(storage)` — Atomic Write

**Ablauf:**
1. File-Lock via `proper-lockfile` (Stale: 10s, 5 Retries)
2. Existierende Datei laden via `loadAccounts()`
3. Merge: `mergeAccounts(existing, storage)`
4. Atomic Write: `.tmp` → `rename()` → `chmod(0o600)`

**WICHTIG:** `saveAccounts()` ruft IMMER `mergeAccounts()` auf! Das bedeutet:
- Selbst wenn wir die JSON-Datei manuell bereinigen, wird beim nächsten `saveAccounts()` der existierende State gelesen und gemerged
- **ABER:** Da `normalizeStorage()` am Ende aufgerufen wird, werden tote Accounts nach dem Merge automatisch herausgefiltert (nach unserem Patch)

### `selectAccount(storage, strategy, now, options)` — Account-Auswahl

**Strategien:**
- `"hybrid"` (Default): Kombiniert Health-Score und Token-Verbrauch. Nutzt `selectHybridAccount()` mit `pidOffset` für Multi-Process-Verteilung.
- `"round-robin"`: Startet beim nächsten Account nach `activeIndex`.
- `"sequential"`: Nimmt den aktuellen `activeIndex`.

**Hybrid-Algorithmus:** Bewertet jeden Account nach:
1. `healthScore` (Erfolgsrate minus Strafe für consecutive failures)
2. `tokens` (Token-Verbrauchs-Zähler)
3. `isRateLimited` (ob rateLimitResetAt in der Zukunft liegt)
4. `pidOffset` (Multi-Process-Rotation via PID)

### Health-Tracking

**Pro Account:**
- `successCount`: Anzahl erfolgreicher API-Calls
- `failureCount`: Anzahl fehlgeschlagener API-Calls
- `consecutiveFailures`: Aufeinanderfolgende Fehler (wird bei Erfolg auf 0 zurückgesetzt)
- `lastSuccess` / `lastFailure`: Timestamps

**Health-Score Berechnung:**
```javascript
successRate = successCount / (successCount + failureCount)
recencyPenalty = min(consecutiveFailures * 0.15, 0.5)
healthScore = max(0, successRate - recencyPenalty)
```

---

## ⚠️ Bekannte Probleme & Lösungen

### Problem 1: Tote Accounts sammeln sich endlos an

**Symptom:** `qwen-auth-accounts.json` hat 50+ Accounts, davon >20 mit `consecutiveFailures > 100`.

**Ursache:** `mergeAccounts()` löscht nie. `normalizeStorage()` filterte ursprünglich nicht nach Health.

**Lösung:** Patch in `normalizeStorage()` (siehe oben). Account mit `consecutiveFailures > 20` werden automatisch entfernt.

> ⚠️ **DER PYTHON-CLEANUP SCRIPT IST NUR NOCH ALS NOTFALL-INTERNET BACKUP NÖTIG!** Mit dem V2 Patch in `normalizeStorage()` werden tote Accounts automatisch nach jedem `saveAccounts()` Aufruf entfernt. Der Patch filtert: (1) kein refreshToken, (2) consecutiveFailures > 20, (3) Zombie-Accounts (expired + failureCount > 50). Manueller Eingriff sollte nur nötig sein wenn der Patch aus Versehen deaktiviert wurde.

**Manuelle Bereinigung (NUR NOCH NOTFALL):**
```python
# NUR wenn normalizeStorage() Patch fehlt oder deaktiviert ist!
import json, os, tempfile, shutil
p = '/Users/jeremy/.config/opencode/qwen-auth-accounts.json'
d = json.load(open(p))
# Filter: cf<=20 UND NICHT (expired + fc>50)
now = int(time.time() * 1000)
good = [a for a in d['accounts']
        if (a.get('health',{}).get('consecutiveFailures',0) <= 20
            and not (not a.get('accessToken')
                     and a.get('expires',0) < now
                     and a.get('health',{}).get('failureCount',0) > 50))]
best = max(range(len(good)), key=lambda i: good[i].get('health',{}).get('successCount',0) if good[i].get('health',{}).get('consecutiveFailures',0)==0 else -1)
with tempfile.NamedTemporaryFile('w',delete=False,dir=os.path.dirname(p)) as tmp:
    json.dump({'version':1,'accounts':good,'activeIndex':best}, tmp, indent=2)
shutil.move(tmp.name, p)
```

### Problem 2: Config-Überschreibung durch Plugin

**Symptom:** Manuelle Änderungen an `qwen-auth-accounts.json` werden nach dem nächsten `opencode`-Aufruf überschrieben.

**Ursache:** `saveAccounts()` ruft `mergeAccounts()` auf, welches den alten State mit dem neuen merged.

**Lösung:** Der `normalizeStorage()`-Patch stellt sicher, dass tote Accounts nach jedem Save automatisch entfernt werden.

### Problem 3: `opencode.json` Schema-Fehler

**Symptom:** `Error: Configuration is invalid — Unrecognized key: "hooks"`

**Ursache:** `hooks` ist KEIN gültiges Feld im OpenCode-Config-Schema. Es wird nicht unterstützt.

**Lösung:** `hooks` NIE in `opencode.json` eintragen. PCPM-Hooks werden projekt-lokal verwaltet (`.opencode/pcpm-config.json`), nicht in der globalen Config.

### Problem 4: MCP Schema-Fehler

**Symptom:** `Error: Invalid input mcp.sin-neural-bus`

**Ursache:** `description` ist kein gültiges Feld im MCP-Schema, und Command-Array muss einen Interpreter enthalten.

**Lösung:**
```json
// FALSCH:
"command": ["/Users/jeremy/.local/bin/opensin-neural-bus-mcp"],
"description": "..."  // ← NICHT ERLAUBT

// RICHTIG:
"command": ["node", "/Users/jeremy/.local/bin/opensin-neural-bus-mcp"]
// Kein "description"-Feld!
```

---

## 📊 OpenCode Datenbank (opencode.db)

**Pfad:** `/Users/jeremy/.local/share/opencode/opencode.db` (SQLite)

**Relevante Tabellen:**

| Tabelle | Zweck |
|---------|-------|
| `account` | Speichert Email, URL, access_token, refresh_token, token_expiry |
| `account_state` | Referenziert aktiven Account (active_account_id) |
| `control_account` | Ähnlich wie account, aber mit `active`-Flag |

**WICHTIG:** Die Qwen-Plugin-Accounts werden **NICHT** in `opencode.db` gespeichert! Sie liegen ausschließlich in `qwen-auth-accounts.json`. Die DB-Tabellen sind für andere Provider (Google/Antigravity, OpenAI etc.).

**Verifizierung:**
```sql
SELECT DISTINCT url FROM account;  -- Zeigt keine qwen.ai URLs
SELECT COUNT(*) FROM account WHERE url LIKE '%qwen%';  -- = 0
```

---

## 🔧 Wartungs-Skripte

### qwen_account_monitor.py

**Pfad:** `/Users/jeremy/dev/OpenSIN-documentation/scripts/qwen_account_monitor.py`

**Funktion:** Überwacht Account-Health, entfernt automatisch Accounts mit cons>20, rotiert zu gesündestem Account.

### Qwen Healer (Bash inline)

```bash
python3 -c "
import json, os, tempfile, shutil
p = '/Users/jeremy/.config/opencode/qwen-auth-accounts.json'
d = json.load(open(p))
good = [a for a in d['accounts'] if a.get('health',{}).get('consecutiveFailures',0) <= 20]
best = max(range(len(good)), key=lambda i: good[i].get('health',{}).get('successCount',0) if good[i].get('health',{}).get('consecutiveFailures',0)==0 else -1)
with tempfile.NamedTemporaryFile('w',delete=False,dir=os.path.dirname(p)) as tmp:
    json.dump({'version':1,'accounts':good,'activeIndex':best}, tmp, indent=2)
    shutil.move(tmp.name, p)
print(f'HEALED: {len(good)} accounts, activeIndex={best}')
"
```

---

## 📋 Quarantäne-Datei

**Pfad:** `/Users/jeremy/.config/opencode/qwen-auth-accounts.quarantined.json`

Enthält alle entfernten Accounts (mit >20 consecutive failures). Kann bei Bedarf manuell wiederhergestellt werden, indem Accounts zurück in die Hauptdatei kopiert werden.

---

## 🗺️ Provider-Konfiguration in opencode.json

```json
"qwen": {
  "npm": "@ai-sdk/openai-compatible",
  "name": "Qwen Code",
  "options": {
    "baseURL": "https://portal.qwen.ai/v1"
  },
  "models": {
    "coder-model": {
      "name": "Qwen 3.6 Plus",
      "limit": { "context": 1048576, "output": 65536 },
      "modalities": { "input": ["text"], "output": ["text"] }
    },
    "vision-model": {
      "name": "Qwen 3.6 Vision Plus",
      "limit": { "context": 131072, "output": 32768 },
      "attachment": true,
      "modalities": { "input": ["text", "image"], "output": ["text"] }
    }
  }
}
```

**WICHTIG:** Kein `apiKey` im Provider! Das Plugin (`opencode-qwen-auth`) injiziert den Token automatisch via Request-Transformation (`transform/request.js`).

---

## 🚨 Grundregeln für die Arbeit mit diesem Plugin

1. **NIEMALS** `qwen-auth-accounts.json` mit Python/externen Skripten überschreiben, während OpenCode läuft (Refresh Token Rotation!)
2. **NIEMALS** `hooks` in `opencode.json` eintragen (wird nicht unterstützt)
3. **NIEMALS** `description` in MCP-Einträgen verwenden (ungültiges Schema-Feld)
4. **IMMER** den `normalizeStorage()`-Patch beibehalten bei Plugin-Updates
5. **IMMER** nach Plugin-Updates die dist/account.js prüfen, ob der Patch noch existiert
6. **IMMER** `node` als Interpreter in MCP-Commands angeben
7. **IMMER** nach `/connect` das `email`-Feld manuell setzen (siehe oben)
8. **IMMER** nach `/connect` OpenCode neu starten
9. **NIEMALS** mehrere Prozesse gleichzeitig auf `qwen-auth-accounts.json` zugreifen lassen
10. **BEI QUOTA-EXCEEDED:** Einfach den nächsten Account über `/connect` hinzufügen (andere Email) → Plugin rotiert automatisch

---

## 📊 Account-Diagnostik (Schnell-Check)

```bash
# Alle Accounts mit Status anzeigen
python3 -c "
import json
with open('/Users/jeremy/.config/opencode/qwen-auth-accounts.json') as f:
    d = json.load(f)
for i, a in enumerate(d.get('accounts',[])):
    h = a.get('health',{})
    email = a.get('email', '⚠️ KEINE EMAIL')
    cf = h.get('consecutiveFailures', 0)
    print(f'  [{i}] email={email} | cf={cf} | sc={h.get(\"successCount\",0)} | AT_len={len(a.get(\"accessToken\",\"\"))}')
print(f'Gesamt: {len(d.get(\"accounts\",[]))} Accounts')
"
```

```bash
# Refresh Token Test (VORSICHT: rotiert den Token!)
curl -sS -X POST "https://chat.qwen.ai/api/v1/oauth2/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
  -d "client_id=f0304373b74a44d2b584a3fb70ca9e56&grant_type=refresh_token&refresh_token=HIER_DEN_RT_EINSETZEN"
```
