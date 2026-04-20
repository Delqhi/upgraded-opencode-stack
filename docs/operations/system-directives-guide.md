# System Directives — Konfiguration & Brain Sync Enforcer

> **EINFÜHRUNG:** System Directives sind `[SYSTEM DIRECTIVE: OH-MY-OPENCODE - TYPE]` Nachrichten die vom Oh-My-Opencode Plugin automatisch in Sessions injiziert werden. Dieser Guide zeigt wie man sie erweitert, überwacht und den neuen **Brain Sync Enforcer** nutzt.

---

## 1. Was sind System Directives?

System Directives sind spezielle System-Nachrichten die vom `oh-my-opencode-sin` Plugin erzeugt werden. Sie haben das Format:

```
[SYSTEM DIRECTIVE: OH-MY-OPENCODE - TYPE]
Nachrichtentext...
```

### Eingebaute Directive Types

| Type | Wann ausgelöst | Quelle |
|------|----------------|--------|
| `TODO CONTINUATION` | Agent wird idle, Todos sind offen | `todo-continuation-enforcer` Hook |
| `RALPH LOOP` | Ralph Loop Fortsetzung | `ralph-loop` Hook |
| `BOULDER CONTINUATION` | Boulder-Plan mit offenen Tasks | `boulder-continuation` Hook |
| `DELEGATION REQUIRED` | Aufgabe muss delegiert werden | `sisyphus-junior-notepad` Hook |
| `SINGLE TASK ONLY` | Nur eine Aufgabe bearbeiten | `sisyphus-junior-notepad` Hook |
| `WORK STOP BRAIN CHECK` | Arbeit stoppen, Brain-/Todo-State final prüfen | `brain-sync-enforcer` Hook |
| `COMPACTION CONTEXT` | Nach Context-Kompaktierung | `context-window-monitor` Hook |
| `CONTEXT WINDOW MONITOR` | Context-Fenster > 70% voll | `context-window-monitor` Hook |
| `PROMETHEUS READ-ONLY` | Prometheus Planner Modus | `start-work` Hook |

### Technische Architektur

```
session.idle Event
  → todo-continuation-enforcer Handler
    → prüft Todos via ctx.client.session.todo()
      → inkomplete Todos? → 2s Countdown Toast
        → injectContinuation()
          → ctx.client.session.promptAsync()
            → "[SYSTEM DIRECTIVE: OH-MY-OPENCODE - TODO CONTINUATION]"
              + Todo-Liste im Prompt
```

Die Directive-Funktionen liegen im gebündelten Plugin:
- **Source:** `local-plugins/oh-my-opencode-sin/dist/index.js`
- **Key Function:** `createSystemDirective(type)` → `[SYSTEM DIRECTIVE: OH-MY-OPENCODE - ${type}]`
- **Directive Types:** `SystemDirectiveTypes` Konstante

---

## 2. System Directive Watcher

Der **System Directive Watcher** ist ein eigenständiger Background-Prozess der Session-Nachrichten scannt und bei erkannten Directives automatisch Todos erstellt.

### Dateilocation

```
~/.config/opencode/scripts/system-directive-watcher.js
```

### Starten

```bash
# Vordergrund (einmalig):
bun run ~/.config/opencode/scripts/system-directive-watcher.js

# Als Daemon (persistent im Hintergrund):
bun run ~/.config/opencode/scripts/system-directive-watcher.js --daemon

# Mit Log-File Tailing (statt Polling):
bun run ~/.config/opencode/scripts/system-directive-watcher.js --log=/tmp/oh-my-opencode.log

# Custom Poll-Interval (in ms):
bun run ~/.config/opencode/scripts/system-directive-watcher.js --interval=5000
```

### Daemon Setup (Terminal/iTerm2)

```bash
# Daemon starten im Hintergrund:
bash /Users/jeremy/.config/opencode/scripts/launch-watcher.sh

# Status pruefen:
cat /tmp/opensin-directive-watcher.pid 2>/dev/null && echo "RUNNING" || echo "NOT_RUNNING"
cat /tmp/opencode-directive-watcher.out

# Daemon stoppen:
kill $(cat /tmp/opensin-directive-watcher.pid 2>/dev/null) 2>/dev/null
```

### LaunchAgent (Auto-Start beim Login)

LaunchAgent plist location:
```
~/Library/LaunchAgents/org.opencode.system-directive-watcher.plist
```

Plist Inhalt:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>org.opencode.system-directive-watcher</string>
  <key>ProgramArguments</key>
  <array>
    <string>/Users/jeremy/.config/opencode/scripts/launch-watcher.sh</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <false/>
  <key>StandardErrorPath</key>
  <string>/tmp/opencode-directive-watcher.err</string>
  <key>StandardOutPath</key>
  <string>/tmp/opencode-directive-watcher.out</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    <key>HOME</key>
    <string>/Users/jeremy</string>
  </dict>
  <key>Nice</key>
  <integer>10</integer>
</dict>
</plist>
```

```bash
# LaunchAgent laden (kanonischer Weg):
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/org.opencode.system-directive-watcher.plist

# Alternative: Direkt über den Wrapper starten:
bash /Users/jeremy/.config/opencode/scripts/launch-watcher.sh
```

### Global Installierte Pfade

Der Watcher ist global installiert fuer JEDES Projekt:
```
~/.config/opencode/scripts/system-directive-watcher.js  ← Haupt-Watcher
~/.config/opencode/scripts/launch-watcher.sh            ← Launch-Helper Script
~/Library/LaunchAgents/org.opencode.system-directive-watcher.plist  ← Auto-Start
```

### Token-Refresh-Service Safety

Der Antigravity-Token-Refresh-Service bleibt absichtlich manuell/aufrufgesteuert:

- `~/Library/LaunchAgents/com.antigravity.Token-Refresh-Service.plist`
- `RunAtLoad=false`
- `KeepAlive=false`

Er darf **nicht** vom Watcher oder irgendeinem Auto-Start-Pfad getriggert werden.

### Konfiguration

Die `DIRECTIVE_ACTIONS` Map im Script definiert welche Todos pro Directive erstellt werden:

```javascript
const DIRECTIVE_ACTIONS = {
  "TODO CONTINUATION": [
    { content: "Global Brain aktualisieren (.pcpm/ sync)", priority: "high" },
    { content: "Local Brain aktualisieren (project context)", priority: "high" },
    { content: "Todo-Liste pruefen und aktualisieren", priority: "medium" },
  ],
  "WORK STOP BRAIN CHECK": [
    { content: "Brain Sync final prüfen", priority: "high" },
    { content: "Todo-Status vor Stopp validieren", priority: "high" },
  ],
  "BRAIN SYNC ENFORCER": [
    { content: "Brain Sync: Global Brain + Local Brain", priority: "high" },
  ],
  // ... weitere Types
};
```

Neue Directive Types einfach als neuen Key hinzufügen.

### State Management

- State-File: `/tmp/opensin-directive-watcher-state.json`
- Speichert bereits verarbeitete Directives (keine Duplikate)
- Max 100 Einträge (automatisches Rotieren)

---

## 3. Brain Sync Enforcer & Extended Enforcement Checks

**Oh-My-Opencode Plugin** bietet einen `brain-sync-enforcer` Hook der vier kritische Checks durchsetzt:

### 3.1 Übersicht der Checks

| Check | Directive Type | Erfolgs-Phrase | Priorität | Wann ausgelöst |
|-------|----------------|----------------|-----------|----------------|
| **A) Brain Check** | `BRAIN SYNC ENFORCER` | `Brains updated` | HIGH | Agent idle, vor Stopp |
| **B) Code Check** | `CODE CHECK` | `Repositories updated` | HIGH | Nach Code-Arbeit |
| **C) Documentation Check** | `DOCUMENTATION CHECK` | `Docs updated` | HIGH | Vor Abschluss |
| **D) Organization Check** | `ORGANIZATION CHECK` | `Org updated` | HIGH | GitHub Hygiene |

Alle Checks arbeiten mit demselben Mechanismus:
1. Directive wird per `session.promptAsync()` injiziert
2. Agent MUSS mit exakter Erfolgs-Phrase antworten
3. Bei fehlender Antwort: Re-Injection alle 10s (max 5 Retries)
4. Erst nach Bestätigung: Arbeit freigegeben

### 3.2 Brain Check (A)

**Directive:** `[SYSTEM DIRECTIVE: OH-MY-OPENCODE - BRAIN SYNC ENFORCER]`

**Prüft:**
- Global Brain (`.pcpm/` + Hive Mind sync)
- Local Brain (`AGENTS.md` + Project-Pläne)

**Antwort:** `Brains updated`

**Patterns:**
```regex
/brains?\s+updated?/i
/brain\s+sync\s+(done|complete|finished|ok)/i
/ja.*brain/i
/yes.*brain/i
/global.*local.*brain/i
/pcpm.*sync/i
/hive\s+mind\s+updated?/i
```

---

### 3.3 Code Check (B)

**Directive:** `[SYSTEM DIRECTIVE: OH-MY-OPENCODE - CODE CHECK]`

**Prüft:**
1. Repositories aktualisiert
2. Alle Changes committed, gepusht, in `main` gemerged
3. Priority Lists & Issues aktualisiert/erstellt

**Antwort:** `Repositories updated`

**Patterns:**
```regex
/repositories?\s+updated/i
/repo.*updated/i
/all.*(commit|push|merge|main).*done/i
/code.*complete/i
```

---

### 3.4 Documentation Check (C)

**Directive:** `[SYSTEM DIRECTIVE: OH-MY-OPENCODE - DOCUMENTATION CHECK]`

**Prüft:**
- README.md Updates
- API Documentation Changes
- Architecture Decision Records (ADRs)
- User Guides & Inline Comments
- Changelog Einträge

**Antwort:** `Docs updated`

**Patterns:**
```regex
/docs?\s+updated/i
/documentation.*complete/i
/readme.*update/i
/all.*docs.*done/i
```

---

### 3.5 Organization & Project Management Check (D)

**Directive:** `[SYSTEM DIRECTIVE: OH-MY-OPENCODE - ORGANIZATION CHECK]`

**Prüft Enterprise-GitHub-Hygiene:**
1. **Issue & PR Management:** Issues korrekt gelabelt, Milestones zugewiesen, PRs mit Issues verlinkt (z.B. "Resolves #ID"), PR-Beschreibungen vollständig
2. **Traceability:** Commits, PR-Diskussionen, Review-Kommentare enthalten Issue-ID Querverweise
3. **Backlog & Technical Debt:** Edge-Cases, Bugs, Tech-D Debt als GitHub Issues mit Priorität erfasst
4. **Stakeholder Alignment:** Kommentare auf Issues/PRs, @mentions, Changelogs aktualisiert
5. **Compliance & Documentation:** Architektur-Entscheidungen in PR-Kommentaren, Issues oder Docs festgehalten

**Antwort:** `Org updated`

**Patterns:**
```regex
/org\s+updated/i
/organization.*complete/i
/github.*hygiene.*done/i
/all.*issues?.*label/i
/all.*prs?.*complete/i
/project.*management.*done/i
```

---

## 4. Integration in Oh-My-Opencode (Plugin Hook)

### Hook-Registrierung

In `local-plugins/oh-my-opencode-sin/src/hooks/index.ts`:

```typescript
export { createBrainSyncEnforcer } from "./brain-sync-enforcer";
```

### Hook-Erstellung

In `local-plugins/oh-my-opencode-sin/src/create-hooks.ts`:

```typescript
const brainSyncEnforcer = isHookEnabled("brain-sync-enforcer")
  ? safeHook("brain-sync-enforcer", () => createBrainSyncEnforcer(ctx, {
      retryIntervalMs: 10000,
      maxRetries: 5,
      enabledChecks: ["brain", "code", "docs", "org"], // Alle 4 Checks
    }))
  : null;
```

**Optionen:**
- `retryIntervalMs`: Re-Injection Intervall (default: 10000ms)
- `maxRetries`: Maximale Versuche (default: 5)
- `enabledChecks`: Array der aktiven Checks (`["brain"]` für nur Brain Check)

### Deaktivierung

In `~/.config/opencode/oh-my-openagent.json`:

```json
{
  "disabled_hooks": ["brain-sync-enforcer"]
}
```

---

## 5. Standalone Betrieb

Falls keine Plugin-Integration möglich:

```bash
# Einfacher Test
bun run scripts/brain-sync-enforcer.js --session=ses_abc123
```

Der Script nutzt dieselbe Logik wie der Hook, aber ohne OpenCode Context.

---

## 6. System Directive Watcher — Neue Checks

Der Watcher (`scripts/system-directive-watcher.js`) erstellt automatisch Todos für alle 4 Checks:

```javascript
const DIRECTIVE_ACTIONS = {
  "BRAIN SYNC ENFORCER": [
    { content: "Brain Sync: Global Brain + Local Brain", priority: "high" },
  ],
  "CODE CHECK": [
    { content: "Code-Check: Repositories updated + pushed + merged", priority: "high" },
    { content: "Issues/Priorities aktualisiert", priority: "medium" },
  ],
  "DOCUMENTATION CHECK": [
    { content: "Dokumentation reviewen: README, ADRs, Changelog", priority: "high" },
    { content: "Fehlende Docs erstellen", priority: "medium" },
  ],
  "ORGANIZATION CHECK": [
    { content: "GitHub-Hygiene: Issues labeln, PRs verlinken", priority: "high" },
    { content: "Traceability: Commit-Messages mit Issue-ID", priority: "high" },
    { content: "Backlog/Technical Debt als Issues erfassen", priority: "medium" },
    { content: "Stakeholder-Kommentare/@mentions pruefen", priority: "medium" },
  ],
  // ... bestehende Types
};
```

---

## 7. Agent-Anleitung: So bestehst du die Checks

### Brain Check (A)
1. `node global-brain/src/cli.js sync` (Global Brain)
2. `AGENTS.md` aktualisieren (Local Brain)
3. Antwort: `Brains updated`

### Code Check (B)
1.Repo(s) updaten, committen, pushen
2. PR erstellen, in `main` mergen
3. Priority Lists & Issues anpassen
4. Antwort: `Repositories updated`

### Documentation Check (C)
1.README/API-Docs/ADRs überprüfen
2.Fehlende Docs erstellen/updaten
3. Changelog ergänzen
4. Antwort: `Docs updated`

### Organization Check (D)
1.Issues labeln & Milestones zuweisen
2.PRs mit Issues verlinken ("Resolves #123")
3.Commit-Messages mit Issue-ID
4.Backlog/Tech-Debt als Issues erfassen
5.Stakeholder @mentions setzen
6.Antwort: `Org updated`

**WICHTIG:** Genau diese Phrase verwenden — keine Abwandlungen!

---

## 8. Troubleshooting

| Problem | Lösung |
|---------|--------|
| Check wird nicht ausgelöst | Hook-Aktivierung prüfen: `isHookEnabled("brain-sync-enforcer")` |
| Agent antwortet mit falscher Phrase | Retry-Loop → nach 5 Versuchen Eskalation |
| Zuviele Retries | `maxRetries` erhöhen oder Issue melden |
| Nur bestimmte Checks aktivieren | `enabledChecks: ["brain", "code"]` im Hook |
| State-Problem | State-File löschen: `rm /tmp/opensin-brain-sync-state.json` |
| Watcher erkennt keine Directives | Session-Verzeichnis prüfen: `~/.local/share/opencode/messages/` |

---

## 9. Dateien-Übersicht

| Datei | Zweck |
|-------|------|
| `scripts/brain-sync-enforcer.js` | Hook + Standalone Script (4 Checks) |
| `scripts/system-directive-watcher.js` | Background Watcher für alle Directives |
| `docs/operations/system-directives-guide.md` | Diese Dokumentation |
| `/tmp/opensin-brain-sync-state.json` | Check-Status pro Session |
| `/tmp/opensin-directive-watcher-state.json` | Watcher-State (processed Directives) |

---

## 10. Erweiterung: Eigene Checks hinzufügen

### 1. CHECKS Map erweitern

```javascript
// In brain-sync-enforcer.js
const CHECKS = {
  // ... bestehende Checks
  
  myCustomCheck: {
    directiveType: "MY CUSTOM CHECK",
    prompt: `[SYSTEM DIRECTIVE: OH-MY-OPENCODE - MY CUSTOM CHECK]

Prüfe ob...`,
    confirmationPatterns: [
      /my\s+custom\s+confirmed/i,
      /custom\s+check\s+done/i,
    ],
    successPhrase: "Custom check done",
  },
};
```

### 2. In Watcher eintragen

```javascript
// In system-directive-watcher.js
const DIRECTIVE_ACTIONS = {
  "MY CUSTOM CHECK": [
    { content: "Custom Check Todo 1", priority: "high" },
  ],
  // ...
};
```

### 3. Hook-Option anpassen

```typescript
createBrainSyncEnforcer(ctx, {
  enabledChecks: ["brain", "code", "docs", "org", "myCustomCheck"]
})
```

Für native Integration als Hook im Plugin:

```
local-plugins/oh-my-opencode-sin/
└── src/
    └── hooks/
        └── brain-sync-enforcer/
            ├── index.ts          # Hook registration
            ├── handler.ts        # Event handling
            ├── constants.ts      # Directive text, patterns
            └── session-state.ts  # Per-session tracking
```

**Hook-Registrierung** in `src/hooks/index.ts`:
```typescript
export { createBrainSyncEnforcer } from "./brain-sync-enforcer";
```

**Einbinden** in `src/create-hooks.ts`:
```typescript
const brainSyncEnforcer = isHookEnabled("brain-sync-enforcer")
  ? safeHook("brain-sync-enforcer", () => createBrainSyncEnforcer(ctx, {
      retryIntervalMs: 10000,
      maxRetries: 5,
    }))
  : null;
```

**Deaktivieren** via `oh-my-openagent.json`:
```json
{
  "disabled_hooks": ["brain-sync-enforcer"]
}
```

### Als eigenständiger Prozess

Falls keine Plugin-Integration gewünscht:

```bash
# Parallel zum opencode-Prozess starten:
bun run scripts/brain-sync-enforcer.js --session=ses_abc123

# Der Prozess:
# 1. Überwacht die Session auf session.idle Events
# 2. Injiziert BRAIN SYNC ENFORCER bei idle
# 3. Prüft Agent-Antworten auf Bestätigung
# 4. Re-injiziert bei keiner Antwort (alle 10s)
```

---

## 4. Workflow: Vollständiger Brain Sync

### Global Brain (.pcpm/)

```bash
# Global Brain setup (einmalig pro Projekt):
node /Users/jeremy/dev/global-brain/src/cli.js setup-hooks \
  --project $(basename "$PWD") \
  --project-root "$PWD" \
  --agents-directive

# Brain sync manuell anstoßen:
node /Users/jeremy/dev/global-brain/src/cli.js sync \
  --project $(basename "$PWD")
```

### Local Brain (AGENTS.md)

```bash
# Deep initialization:
/init-deep

# Manuelle AGENTS.md Aktualisierung:
# - Projekt-Zusammenfassung aktualisieren
# - Neue Architektur-Entscheidungen dokumentieren
# - Offene TODOs eintragen
```

### Checkliste

- [ ] `.pcpm/` Verzeichnis existiert und ist aktuell
- [ ] `AGENTS.md` enthält neuesten Projektstand
- [ ] Alle Architektur-Entscheidungen dokumentiert
- [ ] Offene Todos in `.sisyphus/plans/` erfasst
- [ ] Antwort: "Brains updated"

---

## 5. Erweiterung: Eigene Directive Types

### Im Watcher (einfach)

Neuen Key in `DIRECTIVE_ACTIONS` einfügen:

```javascript
"BRAIN SYNC ENFORCER": [
  { content: "Brain Sync durchfuehren", priority: "high" },
],
```

### Im Plugin (komplett)

Für echte Plugin-Integration mit Prompt-Injection:

```typescript
// constants.ts
export const HOOK_NAME = "brain-sync-enforcer";
export const BRAIN_SYNC_PROMPT = `[SYSTEM DIRECTIVE: OH-MY-OPENCODE - BRAIN SYNC ENFORCER]
...`;
export const CONFIRMATION_PATTERNS = [/brains?\s+updated?/i, ...];

// handler.ts
export function createBrainSyncEnforcer(ctx, options) {
  const handler = async ({ event }) => {
    if (event.type !== "session.idle") return;
    const sessionID = event.properties?.sessionID;
    if (!sessionID) return;

    const todos = await ctx.client.session.todo({ path: { id: sessionID } });
    if (!hasIncompleteTodos(todos)) return;

    await ctx.client.session.promptAsync({
      path: { id: sessionID },
      body: { parts: [{ type: "text", text: BRAIN_SYNC_PROMPT }] }
    });
  };
  return { handler };
}
```

---

## 6. Troubleshooting

| Problem | Lösung |
|---------|--------|
| Watcher erkennt keine Directives | Session-Verzeichnis prüfen: `~/.local/share/opencode/messages/` |
| Directives werden doppelt verarbeitet | State-File löschen: `rm /tmp/opensin-directive-watcher-state.json` |
| Daemon startet nicht | PID-File prüfen: `rm /tmp/opensin-directive-watcher.pid` |
| Brain Sync Enforcer nicht aktiv | Hook-Name in `disabled_hooks` prüfen |
| Agent antwortet nicht auf Brain Sync | Retry-Interval erhöhen (`--interval=15000`) |

---

## 7. Dateien-Übersicht

| Datei | Zweck |
|-------|-------|
| `scripts/system-directive-watcher.js` | Background Watcher für alle Directive Types |
| `scripts/brain-sync-enforcer.js` | Brain Sync Enforcer (eigenständig) |
| `local-plugins/oh-my-opencode-sin/dist/index.js` | Oh-My-Opencode Plugin (Source der Directives) |
| `/tmp/opensin-directive-watcher-state.json` | Watcher State (processed Directives) |
| `/tmp/opensin-brain-sync-state.json` | Brain Sync State (Session-Tracking) |

---

## 8. AGENTS.md Integration

Damit Agenten den Brain Sync Enforcer richtig verstehen, folgende Sektion in die projektspezifische `AGENTS.md` aufnehmen:

```markdown
# 🚨 BRAIN SYNC ENFORCER (PRIORITY -7.5) 🚨

Wenn du eine `[SYSTEM DIRECTIVE: OH-MY-OPENCODE - BRAIN SYNC ENFORCER]` Nachricht erhältst:

1. PRÜFE sofort ob Global Brain (.pcpm/) und Local Brain (AGENTS.md) aktuell sind
2. Falls NEIN: Führe den Brain Sync SOFORT durch
3. Antworte NUR mit: "Brains updated"
4. Du darfst NICHT weiterarbeiten oder stoppen ohne diese Bestätigung

Brain Sync Checklist:
- `.pcpm/` Verzeichnis aktuell? → `node global-brain/src/cli.js sync`
- `AGENTS.md` aktuell? → Projektstand dokumentieren
- Antwort: "Brains updated"
```
