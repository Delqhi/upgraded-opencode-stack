---
name: doctor
description: Full-system audit & healing skill. Checks ALL repos in a project for documentation consistency, outdated claims (CGEventPostToPid, cua-driver, SkyLight), missing VoiceOver-trick, wrong repo names, and methodological drift. Like a doctor making rounds — diagnoses, treats, and discharges healthy.
license: MIT
compatibility: opencode
metadata:
  audience: all-agents
  workflow: repo-health-audit
  trigger: doctor, audit, gesund, reinigen, health-check
---

# /doctor — Repo-Gesundheitscheck & Heilung

> "Alles wie ein Doktor reinigen und gesund machen."

Use this skill when:
- User asks to audit, clean, or heal documentation across repos
- After major architectural changes (e.g., CGEventPostToPid → AXPress)
- User says "prüfe alle md dateien", "doktor", "reinigen", "gesund machen"
- Before release — verify no documentation lies remain

## Phase 1: Diagnose (Audit)

### 1.1 Identifiziere alle zugehörigen Repos
Check `workspace.yaml` oder frage den User. Typisch für Stealth-Triade:
- `stealth-runner` (Orchestrator)
- `skylight-cli` (ACT)
- `unmask-cli` (SENSE)
- `playstealth-cli` (HIDE)
- `A2A-SIN-Worker-heypiggy` (Archiv)

### 1.2 Finde alle MD-Dateien
```bash
for repo in REPO1 REPO2 ...; do
  find "$repo" -name "*.md" -not -path "*/.git/*" -not -path "*/node_modules/*"
done
```

### 1.3 Suche nach TECHNISCHEN LÜGEN
Diese Patterns bedeuten FAST IMMER eine Lüge in aktuellen Docs:
- `CGEventPostToPid` / `SLEventPostToPid` — außer in "funktioniert NICHT"-Kontext
- `SkyLight.framework` als aktiver Klick-Mechanismus
- `cua-driver` als empfohlenes Tool
- Behauptung dass Klicks "unsichtbar" via CGEvent sind

Ausnahmen (KEINE Lügen):
- In Verbotslisten (`banned.md`: "❌ CGEventPostToPid")
- Mit Negation ("funktioniert NICHT", "ignoriert", "does NOT work")
- Historische Docs mit `⚠️ HISTORICAL`-Header
- Archiv-Repos mit deutlichem Archiv-Vermerk

### 1.4 Prüfe auf FEHLENDE Informationen
- VoiceOver-Trick dokumentiert? (in brain.md + AGENTS.md der Klick-Repos)
- AXPress als Klick-Mechanismus genannt?
- `--force-renderer-accessibility` als VERBOTEN markiert?
- Korrekte Versionsnummern?

### 1.5 Erstelle Diagnose-Report
Tabelle pro Repo: Datei | Gefunden | Schwere | Aktion

## Phase 2: Behandlung (Fix)

### 2.1 CGEventPostToPid-Lügen ersetzen
```markdown
# FALSCH:
Click via CGEventPostToPid (SkyLight.framework)

# RICHTIG:
Click via AXUIElementPerformAction (Accessibility API — AXPress)
CGEventPostToPid funktioniert NICHT auf Chrome 148/macOS 26.
```

### 2.2 VoiceOver-Trick einfügen
```markdown
## Chrome Accessibility aktivieren (VoiceOver-Trick)
1. VoiceOver 1× starten: `osascript -e 'tell application "VoiceOver" to launch'`
2. chrome://accessibility → "Suppress automatic" deaktivieren
3. VoiceOver stoppen: `osascript -e 'tell application "VoiceOver" to quit'`
4. AX-Tree bleibt dauerhaft aktiv. Kein --force-renderer-accessibility nötig.
```

### 2.3 Historische Docs markieren
```markdown
> ⚠️ HISTORICAL — Pre-AXPress era. CGEventPostToPid outdated.
```
Nicht umschreiben — nur Header hinzufügen.

### 2.4 brain.md updaten
Muss enthalten: Klick-Mechanismus, VoiceOver-Trick, Verbote, Status, NVIDIA-Modell

## Phase 3: Nachsorge (Verify)

### 3.1 Final Audit
```bash
grep -rn "CGEventPostToPid\|SLEventPostToPid" REPO --include="*.md" \
  | grep -v "NICHT\|not\|ignoriert\|does NOT\|TOT\|⚠️\|HISTORICAL\|Pre-AXPress"
```
Erwartet: 0 Treffer in aktiven Docs (nur in historischen/Archiv).

### 3.2 Commit & Push
Jedes Repo einzeln committen mit klarer Message:
```
docs: doctor-audit — CGEventPostToPid → AXPress, VoiceOver-Trick
```

### 3.3 workspace.yaml prüfen/erstellen
Falls workspace.yaml fehlt, erstellen mit Verweisen auf alle zugehörigen Repos.

## Bekannte Krankheitsbilder

| Symptom | Diagnose | Behandlung |
|---------|----------|------------|
| README sagt "CGEventPostToPid" | Veraltete Doku | AXPress + VoiceOver-Trick |
| brain.md nennt falsches Repo | Copy-Paste-Fehler | Korrigieren |
| "SkyLight.framework" als aktiv | Pre-AXPress-Ära | AXPress ersetzen |
| Kein VoiceOver erwähnt | Fehlende Prerequisite | Einfügen in AGENTS.md |
| cua-driver als Tool empfohlen | Veraltete Architektur | skylight-cli ersetzen |
| --force-renderer-accessibility | Crasht Chrome | Als VERBOTEN markieren |
