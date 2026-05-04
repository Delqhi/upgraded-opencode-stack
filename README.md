# Infra-SIN-OpenCode-Stack — Cognitive Assembly Line

**Version:** 1.0.0  
**Stand:** 2026-05-01  
**Autoren:** SIN-Zeus + Explore Agent  

---

## 🧠 Was ist die Cognitive Assembly Line?

Die Cognitive Assembly Line ist eine strukturierte Pipeline für automatisierte, parallele Agenten-Workflows. Sie besteht aus 6 Phasen:

```
User Prompt → Descriptor → Router → Parallel Swarms → Validation Layer → Execution Layer → Aggregation → Final Output
```

---

## 📦 Enthaltene Komponenten

### **Main Agents** (in `OpenSIN-documentation/.opencode/opencode.json`)
- `SIN-Zeus` — Control Plane Orchestrator
- `coder-sin-swarm` — Primary Coding Agent
- `Coder-SIN-Qwen` — Alternative Coding Agent
- `Stealth-Orchestrator` — Browser Automation
- `SIN-Solo` — Single-Agent Executor
- **Neu:** `explore` — Codebase Analysis (Step 3.5 Flash, reasoning high)
- **Neu:** `orchestrator` — Pipeline Coordination (Minimax M2.7)

### **Subagents** (in `oh-my-opencode.json` — diese Datei)
21 spezialisierte Subagents, organisiert in 6 Gruppen:

| Gruppe | Subagents | Zweck |
|--------|-----------|-------|
| **Audio & Medien** | `audio_agent`, `multimedia_looker` | TTS, STT, Vision, GUI |
| **Web-Recherche** | `athena`, `argus`, `daedalus`, `hermes_scout` | Strategic, Multi-Source, Technical Research, Fast Retrieval |
| **Code-Qualität** | *placeholder* (code-checker, test-runner, security-scanner, performance-auditor) | Linting, Testing, Security, Perf |
| **Dokumentation** | *placeholder* (doc-writer, pr-generator, changelog-writer) | Docs, PRs, Changelog |
| **DevOps** | *placeholder* (ci-agent, env-manager, infra-provisioner, backup-agent) | CI/CD, Env, IaC, Backup |
| **Data Science** | *placeholder* (data-viz, data-analyzer, ml-trainer, ml-deployer) | Viz, EDA, ML Training/Deployment |

**Aktive Subagents:** 13 von 21 sind als MCP-Server in OpenCode.json konfiguriert (enabled: true/false). Die noch fehlenden 8 sind als Platzhalter in OpenCode.json vorhanden, müssen aber noch implementiert werden.

---

## 🔌 MCP-Server Integration

Jeder Subagent wird als **MCP-Server** bereitgestellt. Die Konfiguration erfolgt in:

- **OpenSIN-documentation/.opencode/opencode.json** (MCP-Sektion)
- **OpenSIN-documentation/.opencode/oh-my-opencode.json** (Subagent-Definitionen — diese Datei)

** Beispiel für einen Subagent (`audio_agent`):**

```json
{
  "role": "Audio TTS/SST",
  "model": "groq/whisper-large-v3",
  "fallback_model": "nvidia-nim/whisper-large-v3",
  "tools": ["whisper", "coqui-tts", "ffmpeg"],
  "benchmarks": ["audio_transcription", "tts_quality"],
  "responsibilities": ["Sprache-zu-Text", "Text-zu-Sprache", "Audio-Analyse"]
}
```

---

## 🚀 Nutzung der Pipeline

### 1. Pipeline-Descriptor
Analysiert den User-Prompt und erstellt ein Pipeline-Template:

```bash
echo "Erstelle eine Python-Funktion..." | opencode run --command pipeline-descriptor
```

**Output:**
```json
{
  "pipeline": ["analyze_codebase_patterns", "determine_test_structure"],
  "subagents": ["explore"],
  "complexity": "low",
  "estimated_time": "2-5"
}
```

### 2. Pipeline-Router
Dispatcht Tasks an Subagents basierend auf dem Descriptor:

```bash
opencode run --command pipeline-router --args '{"subagents": ["explore", "librarian"]}'
```

### 3. Validation Layer
Führt Code-Qualitäts-Checks aus (sobald MCPs aktiviert):

```bash
opencode run --command pipeline-validation --args '{"target": "src/"}'
```

### 4. Execution Layer
Führt Domain-Specialists aus:

```bash
opencode run --command pipeline-execution --args '{"agent": "coder-sin-swarm", "task": "..."}'
```

### 5. Aggregation
Sammelt Ergebnisse und generiert PR/Docs:

```bash
opencode run --command pipeline-aggregation --args '{"pr_title": "..."}'
```

### 6. Vollständige Pipeline
Alle Phasen in einem:

```bash
echo "User prompt" | opencode run --command pipeline-full
```

---

## 📊 Benchmark-Vergleich (2026)

Die aktuellsten Coding-Benchmarks für Modelle wie GLM-5.1, DeepSeek V4-Pro, Qwen 3.6 Max, MiniMax M2.5, Mistral Small 4, Codestral, Step 3.5 Flash, etc. sind dokumentiert in:

**OpenSIN-documentation:** `docs/guides/aktuelle-coding-benchmarks-2026.md`

---

## 🛠️ Entwicklung & Erweiterung

### Neue Subagents hinzufügen

1. **MCP-Server implementieren** in `OpenSIN-backend/bin/` (z.B. `code-checker`, `test-runner`)
2. **MCP-Konfiguration** in `OpenSIN-documentation/.opencode/opencode.json` hinzufügen
3. **Subagent-Definition** in `oh-my-opencode.json` (dieser Datei) hinzufügen
4. **Pipeline-Commands** erweitern, wenn nötig

###ipeline anpassen

Die Pipeline-Commands sind in `OpenSIN-documentation/.opencode/opencode.json` definiert. Sie können nach Bedarf erweitert werden (z.B. `pipeline-<stage>` für spezifische Workflows).

---

## 📚 Verwandte Dokumentation

- **OpenSIN-documentation AGENTS.md** — Agent-Mandates und Tech-Stack Rules
- **OpenCode Config Reference** — https://opencode.ai/config.json
- **Cognitive Assembly Line Blueprint** — `docs/guides/cognitive-assembly-line-subagent-blueprint.md`

---

## 🤝 Contributing

Änderungen an dieser Konfiguration sollten über Pull Requests erfolgen. Siehe `OpenSIN-documentation/CONTRIBUTING.md`.

---

**Powered by OpenSIN-AI** — Enterprise AI Agents working autonomously.
