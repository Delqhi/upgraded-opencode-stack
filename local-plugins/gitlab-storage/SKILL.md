# ⚠️ DEPRECATED — GitLab Storage Plugin

> **WICHTIG:** Dieses Plugin ist **VERALTET** und wird nicht mehr unterstützt.  
> **ERSATZ:** Verwende stattdessen **A2A-SIN-Box-Storage** (room-09) für alle Speicheranforderungen.  
> Siehe: `docs/storage/box-cloud-storage.md` für Migration.

# 🛑 GITLAB STORAGE DEPRECATED — Unendlicher Speicher für die gesamte SIN-Flotte

> **ZWECK (VERALTET):** Alle schweren Dateien, Logs, Backups, Docker-Images, Reports und Agent-Artefakte wurden früher in private GitLab-Repos (10GB free each, unendlich viele Repos) verlagert.  
> **STATUS:** GitLab hat unser Konto gesperrt (zu viele Dateien).  
> **ABLÖSUNG:** Ab sofort nutzt OpenSIN **Box.com** als primären Cloud Storage via `A2A-SIN-Box-Storage`.

---

## 📁 Skill-Struktur (VERALTET)

```
~/.config/opencode/skills/gitlab-storage/
├── SKILL.md                    ← Du bist hier
├── config/
│   ├── storage-registry.json   ← Zentrales Register: WAS liegt WO und WARUM
│   └── machine-links.json      ← Welche Maschine nutzt welche Storage-Repos
└── scripts/
    └── gitlab_storage_manager.py  ← Das Haupttool (baut auf gitlab_logcenter.py auf)
```

---

## 🔑 Token & Auth

| Variable                 | Pfad                                      | Zweck                                              |
| ------------------------ | ----------------------------------------- | -------------------------------------------------- |
| `GITLAB_LOGCENTER_TOKEN` | `~/.config/opencode/gitlab_logcenter.env` | GitLab API Token (privat, aus SIN-Passwordmanager) |
| `GITLAB_STORAGE_TOKEN`   | `~/.config/opencode/gitlab_logcenter.env` | Gleicher Token, alias                              |

**Token kommt aus:** `sin-passwordmanager` → `gitlab.com` → `GITLAB_LOGCENTER_TOKEN`

---

## 🛠️ CLI-Befehle (Agent-Pflicht)

### Storage-Management

```bash
# Storage für ein Projekt initialisieren
gitlab_storage_manager.py init --project <name> [--visibility private|public]

# Datei in GitLab-Repo hochladen
gitlab_storage_manager.py upload --project <name> --file <pfad> [--category <kat>] [--tags t1,t2]

# Status aller Storage-Repos prüfen
gitlab_storage_manager.py status --project <name> [--json]

# Dateien suchen
gitlab_storage_manager.py search --project <name> --query <text>

# Dateien auflisten
gitlab_storage_manager.py list --project <name> [--category <kat>] [--date YYYY-MM-DD]

# Datei herunterladen
gitlab_storage_manager.py download --project <name> --path <repo_pfad> --output <lokal>

# Repo-Rotation erzwingen (wenn voll)
gitlab_storage_manager.py rotate --project <name>

# Aktives Repo anzeigen
gitlab_storage_manager.py get-active --project <name>
```

### Kategorien

| Kategorie         | Zweck                                  | Beispiele                    |
| ----------------- | -------------------------------------- | ---------------------------- |
| `logs`            | Application Logs, Crash Logs           | `runner.log`, `crash.dump`   |
| `video`           | Screen Recordings, CDP Screencasts     | `browser_recording.mp4`      |
| `screenshots`     | Browser Screenshots, UI Captures       | `screenshot.png`             |
| `browser`         | CDP Console, Network, Performance Logs | `console.log`, `network.har` |
| `reports`         | Crash Analysis, RCA Reports            | `crash_analysis.json`        |
| `docker-images`   | Exportierte Docker Images              | `supabase_backup.tar`        |
| `backups`         | Datenbank-Backups, Config-Backups      | `supabase_db.sql.gz`         |
| `agent-artifacts` | Agent Build-Outputs, Test-Results      | `test_results.json`          |
| `misc`            | Alles andere                           | `unknown.dat`                |

---

## 🏗️ Storage-Register (WAS liegt WO und WARUM)

**Zentrales Register:** `config/storage-registry.json`

Jeder Eintrag enthält:

```json
{
  "project": "sin-solver",
  "repo_name": "sin-solver-logcenter-001",
  "repo_id": 12345678,
  "visibility": "private",
  "purpose": "Logs und Backups für SIN Solver Flotte",
  "owner_machine": "oci-vm-92.5.60.87",
  "categories": ["logs", "video", "screenshots"],
  "created_at": "2026-04-13T16:00:00Z",
  "size_limit_gb": 9,
  "current_size_gb": 0.5,
  "files_count": 142
}
```

### Bekannte Projekte (MIGRIERT — Stand: 2026-04-13)

| Projekt          | Alter Storage-Repo       | Neuer Speicherort          | Status      |
| ---------------- | ------------------------ | -------------------------- | ----------- |
| `sin-solver`     | `sin-solver-logcenter-*` | Box.com `/Cache` (room-09) | ✅ migriert |
| `sin-backend`    | `sin-backend-storage-*`  | Box.com `/Cache` (room-09) | ✅ migriert |
| `oci-vm`         | `oci-vm-storage-*`       | Box.com `/Cache` (room-09) | ✅ migriert |
| `opencode-stack` | `opencode-stack-logs-*`  | Box.com `/Cache` (room-09) | ✅ migriert |
| `sin-code`       | `sin-code-artifacts-*`   | Box.com `/Cache` (room-09) | ✅ migriert |

---

## 🔗 Machine-Links (VERALTET — Nicht mehr verwendet)

**HINWEIS:** Diese Konfiguration ist veraltet. Durch die zentrale Box Storage Service (`room-09-box-storage`) sind keine lokalen sync_dirs mehr nötig. Alle Uploads gehen direkt an Box.com.

**Alte Konfiguration (für Referenz):**

```json
{
  "oci-vm-92.5.60.87": {
    "projects": ["sin-solver", "sin-backend", "oci-vm"],
    "sync_dirs": {
      "/var/log": "logs",
      "/opt/sin-supabase/backups": "backups",
      "/tmp/agent-artifacts": "agent-artifacts"
    }
  },
  "mac-jeremy": {
    "projects": ["sin-solver", "opencode-stack"],
    "sync_dirs": {
      "/tmp/opencode-logs": "logs",
      "/tmp/screenshots": "screenshots"
    }
  },
  "hf-vm-delqhi-simone-mcp": {
    "projects": ["sin-solver"],
    "sync_dirs": {
      "/tmp/logs": "logs",
      "/tmp/reports": "reports"
    }
  }
}
```

---

## 🔄 Auto-Rotation (VERALTET — Wird nicht mehr genutzt)

- **Limit:** 9 GB pro Repo (10 GB free - 1 GB Safety)
- **Trigger:** Bei Upload prüft Script automatisch ob Repo voll ist
- **Action:** Erstellt automatisch `-001`, `-002`, `-003`, ... Repos
- **Unendlicher Speicher:** Jedes Repo = 9 GB × unendlich viele Repos

---

## 🌐 Public vs Private Repos

**REGELN:**

| Inhalt                          | Visibility  | Grund                                       |
| ------------------------------- | ----------- | ------------------------------------------- |
| Logs, Backups, Crash-Dumps      | **private** | Enthalten sensible Daten, Secrets, IPs      |
| Agent-Artefakte, Test-Results   | **private** | Interne Entwicklungsdaten                   |
| Screenshots, Videos von UIs     | **private** | Können User-Daten zeigen                    |
| Docker-Images                   | **private** | Enthalten Configs, Secrets                  |
| **Öffentliche Demos/Showcases** | **public**  | Nur wenn explizit gewollt und keine Secrets |

**IMMER private**, es sei denn der User sagt explizit "public".

---

## ⚡ Migration OCI VM → GitLab Storage

### Was muss von der OCI VM migriert werden:

| Datei/Verzeichnis                 | Ziel-Kategorie    | Größe (geschätzt) |
| --------------------------------- | ----------------- | ----------------- |
| `/var/log/*.log`                  | `logs`            | ~440 MB           |
| `/opt/sin-supabase/backups/`      | `backups`         | ~225 MB           |
| `/opt/OpenSIN-Code/.git/objects/` | `backups`         | ~363 MB           |
| Docker-Images (backup)            | `docker-images`   | ~7 GB             |
| `/tmp/agent-artifacts/`           | `agent-artifacts` | variabel          |
| `~/.cache/`                       | `misc`            | ~144 MB           |

### Migration-Befehl:

```bash
# Auf OCI VM ausführen:
cd ~
gitlab_storage_manager.py init --project oci-vm
gitlab_storage_manager.py upload --project oci-vm --file /var/log/syslog --category logs --tags system,boot
# ... für jede Datei
```

---

## 🚨 WICHTIGE HINWEISE (DEPRECATED)

1. ⚠️ **Dieses Plugin ist DEPRECATED.** Verwende stattdessen `A2A-SIN-Box-Storage` (room-09).
2. **NICHT MEHR VERWENDEN** für neue Projekte.
3. Bestehende Uploads wurden migriert; neueste Daten liegen in Box.com.
4. Die hier beschriebenen Befehle funktionieren nur noch über Kompatibilitätsschicht (`box_storage.py`) und sind ab sofort zu vermeiden.
5. **Token:** `GITLAB_LOGCENTER_TOKEN` wird nicht mehr unterstützt — verwende `BOX_STORAGE_API_KEY`.

---

## 📋 Integration mit bestehendem gitlab_logcenter.py (DEPRECATED)

Dieser Skill **erweitert** das `gitlab_logcenter.py` — **ABER:** Beide sind deprecated.

- **Bestehende Funktion:** Log-Speicherung für Crash-Analyse (veraltet)
- **Neu (historisch):** Allgemeine Dateispeicherung, Machine-Links, Storage-Register (veraltet)
- **Status:** Alles ersetzt durch `A2A-SIN-Box-Storage`

**Verwende stattdessen:** `box_storage.py` (gleiche API, anderes Backend).

---

## 🔍 Quick Reference für Agenten (DEPRECATED)

```
FRAGE: Wo speichere ich eine große Datei?
ANTWORT: box_storage.py verwenden (nicht mehr gitlab_storage_manager.py)

FRAGE: Wie finde ich eine alte Datei?
ANTWORT: box_storage.upload_file() und eigene Indexierung (Box.com)

FRAGE: Ist mein Storage-Repo voll?
ANTWORT: Box.com hat 10GB free, automatische Volume-Erweiterung bei 9GB

FRAGE: Welches Repo nutze ich?
ANTWORT: Box Storage service (room-09-box-storage:3000)

FRAGE: Neue Maschine anbinden?
ANTWORT: Nicht mehr nötig — alle gehen an zentrale Box Storage.
```

**Siehe:** `docs/storage/box-cloud-storage.md` für aktuelle Anleitung.

---
