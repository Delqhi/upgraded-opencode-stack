# OMOC Dispatch Architecture V2

## Problem

Der oh-my-opencode Plugin v3.16.0 enthält hartcodierte Fallback-Ketten in `AGENT_MODEL_REQUIREMENTS` und `CATEGORY_MODEL_REQUIREMENTS`. Wenn unsere konfigurierten Modelle (aus `oh-my-openagent.json`) nicht verfügbar sind, fällt der Plugin automatisch auf Anbieter wie `xai/grok-code-fast-1` oder `anthropic/claude-haiku-4.5` zurück – Modelle, die wir nicht nutzen wollen.

### Hardcoded Fallback Chains (aus dem Plugin)

```javascript
var AGENT_MODEL_REQUIREMENTS = {
  explore: {
    fallbackChain: [
      { model: "gpt-5.4", providers: ["openai"] },
      { model: "gpt-5.3-codex", providers: ["openai"] },
      { model: "minimax-m2.5", providers: ["opencode-go"] },
      { model: "grok-fast", providers: ["xai"] }, // ❌ UNERWÜNSCHT
      { model: "claude-haiku", providers: ["anthropic"] }, // ❌ UNERWÜNSCHT
    ],
  },
  librarian: {
    fallbackChain: [
      /* enthält minimax, grok, haiku */
    ],
  },
  // ... weitere Agents
};
```

Diese Chains werden aktiviert, wenn:

1. Unser primäres Modell aus `oh-my-openagent.json` fehlschlägt (rate-limit, 404)
2. Alle unsere konfigurierten `fallback_models` fehlschlagen
3. → Dann wird die hartkodierte Kette durchlaufen

---

## Lösung

### Schicht 1: Exhaustive oh-my-openagent.json

Für jeden Agenten haben wir 4-5 unserer eigenen Fallback-Modelle definiert:

```json
{
  "agents": {
    "explore": {
      "model": "google/antigravity-gemini-3.1-pro",
      "fallback_models": [
        "google/antigravity-gemini-3-flash",
        "openai/gpt-5.4",
        "google/antigravity-gemini-3.1-pro",
        "google/antigravity-claude-sonnet-4-6",
        "qwen/coder-model"
      ]
    },
    "oracle": {
      "model": "openai/gpt-5.4",
      "fallback_models": [
        "google/antigravity-gemini-3.1-pro",
        "google/antigravity-claude-opus-4-6-thinking",
        "google/antigravity-claude-sonnet-4-6",
        "qwen/coder-model"
      ]
    }
    // ... usw.
  }
}
```

Dadurch wird die Wahrscheinlichkeit, dass ALLE unsere Modelle gleichzeitig ausfallen, extrem reduziert.

### Schicht 2: Plugin-Fork mit neutralisierten Hardcoded Fallbacks

Da die AGENT_MODEL_REQUIREMENTS und CATEGORY_MODEL_REQUIREMENTS nicht über Config überschrieben werden können, haben wir einen Fork des Plugins erstellt:

- Plugin: `oh-my-opencode-sin` (lokal in `~/.config/opencode/local-plugins/oh-my-opencode-sin/`)
- Änderung: Die beiden Anforderungsobjekte werden durch leere Objekte ersetzt:

```javascript
// Vor (offizielles Plugin)
var AGENT_MODEL_REQUIREMENTS = { explore: { fallbackChain: [...] }, ... };

// Nach (Fork)
var AGENT_MODEL_REQUIREMENTS = {}; // Keine hartkodierten Fallbacks
var CATEGORY_MODEL_REQUIREMENTS = {}; // Keine hartkodierten Kategoriefallbacks
```

Die `resolveModelPipeline()` Funktion prüft dann nur noch:

1. `intent.userModel` (unser primäres Modell)
2. `intent.userFallbackModels` (unsere Fallback-Liste)
3. `policy.systemDefaultModel` (globaler Default aus opencode.json)

Die hartkodierte Fallback-Kette wird nie mehr erreicht, da sie leer ist.

### Schicht 3: Plugin-Umschaltung in opencode.json

In `~/.config/opencode/opencode.json`:

```json
{
  "plugin": [
    "opencode-antigravity-auth@1.6.5-beta.0",
    "/Users/jeremy/.config/opencode/local-plugins/oh-my-opencode-sin"
  ]
}
```

Dadurch wird der geforkte Plugin anstelle des npm-basierten `oh-my-openagent` geladen. Der benutzerdefinierte Fork liest weiterhin die `oh-my-openagent.json` für die Modell-Zuordnung, verwendet aber keine internen Hardcoded-Fallbackketten.

---

## Architektur-Diagramm

```
┌──────────────────────────────────────────────────┐
│           oh-my-opencode-sin (Fork)               │
│   resolveModelPipeline(request)                  │
│   ├─ 1. intent.userModel?                       │
│   ├─ 2. intent.userFallbackModels?              │
│   └─ 3. policy.systemDefaultModel               │
│   (AGENT_MODEL_REQUIREMENTS = {} )               │
└──────────────────────────────────────────────────┘
                      ▲
                      │ geladen via
                      │
┌──────────────────────────────────────────────────┐
│          ~/.config/opencode/oh-my-openagent.json │
│   { "explore": { "model": "...", "fallback_models": [...] } } │
└──────────────────────────────────────────────────┘
                      ▲
                      │
┌──────────────────────────────────────────────────┐
│          ~/.config/opencode/opencode.json         │
│   "plugin": ["...", "/path/to/oh-my-opencode-sin"] │
└──────────────────────────────────────────────────┘
```

---

## Verifikationsplan

### Test 1: Agent-Model-Auflösung prüfen

```bash
# Auf OCI VM (wo alle Provider verfügbar sind)
opencode run "Write a Python hello world" --agent explore --format json 2>&1 | tee /tmp/explore.log
# Prüfen: Im Log muss der gewählte Model aus der Config stehen (z.B. "google/antigravity-gemini-3.1-pro")
# NICHT: "xai/grok" oder "anthropic/claude-haiku"
```

### Test 2: Fallback-Kette durchspielen

Manuell den primären Model temporär als unavailable markieren (z.B. Provider deaktivieren) und beobachten, ob der erste Eintrag aus unserer `fallback_models`-Liste gewählt wird.

### Test 3: Kompletter End-to-End Swarm

`omoc-plan-swarm` aufrufen und verifizieren, dass alle beteiligten Agents aus unserer Whitelist stammen.

---

## Commits & Dateien

### Neu/Geändert

- `~/.config/opencode/oh-my-openagent.json` (exhaustive fallbacks, bereits committed in upgraded-opencode-stack@2c1f28a)
- `~/.config/opencode/local-plugins/oh-my-opencode-sin/` (Fork)
  - `package.json` (Name geändert)
  - `dist/index.js` (AGENT_MODEL_REQUIREMENTS{}, CATEGORY_MODEL_REQUIREMENTS{})
- `~/.config/opencode/opencode.json` (Plugin-Pfad angepasst)
- `upgraded-opencode-stack/oh-my-openagent.json` (mirrored)
- `upgraded-opencode-stack/docs/dispatch-architecture-v2.md` (dieses Dokument)

---

## Warum ein Fork?

- Es gibt keinen Config-Key, um `AGENT_MODEL_REQUIREMENTS` zu überschreiben.
- Die einzige Alternative wäre, den `call_omo_agent`-Tool zu wrappen, aber der wird intern vom Plugin verwendet; wir müssten jeden Aufruf patchen.
- Der Fork ändert nur 2 Zeilen (die beiden Objekte leeren) und reverts die restliche Logik intakt. Updates des offiziellen Plugins können durch erneutes Kopieren und Leeren der Objekte eingepflegt werden (Merge-Conflict-arme Stelle).

---

## Nächste Schritte

1. Fork-Verzeichnis `oh-my-opencode-sin` ins `upgraded-opencode-stack` Repo committen.
2. `sin-sync` erneut laufen lassen, um den Fork auf den OCI VM zu spiegeln.
3. Live-Verifikationstests auf OCI VM durchführen.
4. GitHub Issue #4 mit diesem Design-Doc und den Ergebnissen updaten.
