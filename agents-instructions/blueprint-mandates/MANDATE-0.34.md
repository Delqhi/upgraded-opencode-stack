# MANDATE 0.34: SIMONE MCP + PCPM ARE MANDATORY (V19.3 - 2026-04-12)

**EFFECTIVE:** 2026-04-12  
**SCOPE:** ALL OpenCode agents, ALL repositories, ALL task sessions  
**STATUS:** ACTIVE MANDATE

**🎯 PRINZIP:** Jeder Agent MUSS Simone MCP verwenden und PCPM als Pflicht-Gedächtnis/Planungsbasis laden, bevor irgendeine Planungs-, Analyse-, oder Implementierungsarbeit beginnt.

---

#### 📌 PFLICHTEN

- **Simone MCP ist verpflichtend** für symbolische Navigation, strukturelle Code-Edits, MCP-Workflows und agentische Code-Aufgaben.
- **PCPM ist verpflichtend** als persistente Plan-/Memory-Schicht für jeden neuen Task-Start.
- Wenn Simone MCP Hooks, Metadata oder Runtime fehlen, MUSS der Agent sie zuerst installieren bzw. synchronisieren.
- Wenn PCPM Hooks oder Projekt-Memory fehlen, MUSS der Agent zuerst das Global-Brain/PCPM initialisieren.
- Direkte Ad-hoc-Edits ohne Simone MCP sind **nicht** der Standard, wenn Simone MCP verfügbar ist.

---

#### 🔧 PRAKTISCHE REGEL

1. Prüfe, ob Simone MCP im Repo vorhanden und gestartet werden kann.
2. Prüfe, ob `.pcpm/` bzw. OpenCode-Hooks aktiv sind.
3. Erst dann mit Analyse, Planung oder Code-Arbeit beginnen.

---

#### ✅ MINDESTSTANDARD

| Pflichtsurface | Erwartung                                       |
| -------------- | ----------------------------------------------- |
| Simone MCP     | Aktiviert, erreichbar, von Agenten verwendet    |
| PCPM           | Aktiviert, geladen, als Aufgaben-Memory genutzt |
| Repo README    | Verweist klar auf die Pflichtnutzung            |
| Install-Skript | Prüft und meldet die Pflichtnutzung             |
