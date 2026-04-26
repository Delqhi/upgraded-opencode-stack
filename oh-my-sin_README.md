# oh-my-sin.json — Zentrales A2A Team Register

<p align="center">
<a href="https://github.com/Delqhi/upgraded-opencode-stack/blob/main/LICENSE">
<img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License" />
</a>
<a href="https://github.com/Delqhi/upgraded-opencode-stack">
<img src="https://img.shields.io/badge/upgraded--opencode--stack-2.2.1-7B3FE4?style=for-the-badge" alt="Version" />
</a>
<a href="https://opensin.ai">
<img src="https://img.shields.io/badge/OpenSIN--AI-Enterprise-7B3FE4?style=for-the-badge" alt="OpenSIN-AI" />
</a>
</p>

<p align="center">
<a href="#overview">Überblick</a> · <a href="#teams">Alle 17 Teams</a> · <a href="#structure">Struktur</a> · <a href="#models">Modelle</a> · <a href="#defaults">Defaults</a> · <a href="#usage">Verwendung</a>
</p>

<p align="center">
<em>Das zentrale Register das alle 17 A2A Teams klassifiziert — mit Managern, Mitgliedern und Modell-Hierarchien.</em>
</p>

---

## Overview

**oh-my-sin.json** ist das zentrale Team Register der OpenSIN-AI Flotte. Es definiert:

| Aspekt | Details |
|:---|:---|
| **17 Teams** | Coding, Worker, Infrastructure, Google Apps, Apple Apps, Social, Messaging, Forum, Legal, Commerce, Community, Research, Media, CyberSec, uvm. |
| **Team Manager** | Jedes Team hat einen eigenen A2A Manager Agent |
| **Mitglieder** | Die Agenten die zu jedem Team gehören |
| **Primär-Modell** | Das Haupt-Modell für den Team Manager |
| **Fallback-Modelle** | Failover-Kette wenn das Primary nicht verfügbar ist |

> [!IMPORTANT]
> Dieses Register ist Pflicht für alle A2A-Agenten! Bevor ein Agent einen Task startet, muss er das passende Team aus diesem Register auswählen.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

## Alle 17 Teams

### 1. Team Coding

**Zweck:** Elite-Coder-Flotte für Implementation, Testing, Deployment

| Feld | Wert |
|:---|:---|
| **Manager** | `A2A-SIN-Zeus` |
| **Config** | `my-sin-team-code.json` |
| **Primary Model** | `google/antigravity-claude-sonnet-4-6` |

**Mitglieder:**
- `A2A-SIN-Simone-MCP`
- `A2A-SIN-Frontend`
- `A2A-SIN-Backend`
- `A2A-SIN-Fullstack`

**Fallback Models:**
1. `nvidia/minimaxai/minimax-m2.7`
2. `qwen/coder-model`
3. `google/antigravity-gemini-3.1-pro`

---

### 2. Team Worker

**Zweck:** Autonome Worker für Surveys, Freelancing, Monetarisierung

| Feld | Wert |
|:---|:---|
| **Manager** | `A2A-SIN-Team-Worker` |
| **Config** | `my-sin-team-worker.json` |
| **Primary Model** | `meta/llama-3.2-11b-vision-instruct` |

**Mitglieder:**
- `A2A-SIN-Worker-Prolific`
- `A2A-SIN-Worker-Freelancer`
- `A2A-SIN-Worker-Survey`

**Fallback Models:**
1. `nvidia/minimaxai/minimax-m2.7`
2. `qwen/coder-model`
3. `nvidia-nim/stepfun-ai/step-3.5-flash`

---

### 3. Team Infrastructure

**Zweck:** DevOps-Flotte für Deployment, CI/CD, Monitoring, Infrastructure

| Feld | Wert |
|:---|:---|
| **Manager** | `A2A-SIN-Team-Infrastructure` |
| **Config** | `my-sin-team-infrastructure.json` |
| **Primary Model** | `nvidia/minimaxai/minimax-m2.7` |

**Mitglieder:**
- `A2A-SIN-Deploy`
- `A2A-SIN-Monitoring`
- `A2A-SIN-Security`

**Fallback Models:**
1. `google/antigravity-claude-sonnet-4-6`
2. `qwen/coder-model`
3. `google/antigravity-gemini-3.1-pro`

---

### 4. Team Google Apps

**Zweck:** Google Workspace Integration — Docs, Sheets, Drive, Gmail

| Feld | Wert |
|:---|:---|
| **Manager** | `A2A-SIN-Google-Apps` |
| **Config** | `my-sin-team-google-apps.json` |
| **Primary Model** | `google/antigravity-gemini-3.1-pro` |

**Mitglieder:**
- `A2A-SIN-Google-Docs`
- `A2A-SIN-Google-Sheets`
- `A2A-SIN-Google-Drive`

**Fallback Models:**
1. `nvidia/minimaxai/minimax-m2.7`
2. `qwen/coder-model`
3. `google/antigravity-claude-sonnet-4-6`

---

### 5. Team Apple Apps

**Zweck:** Apple Ecosystem — macOS Automation, iOS, Shortcuts

| Feld | Wert |
|:---|:---|
| **Manager** | `A2A-SIN-Apple-Apps` |
| **Config** | `my-sin-team-apple-apps.json` |
| **Primary Model** | `nvidia/minimaxai/minimax-m2.7` |

**Mitglieder:**
- `A2A-SIN-Apple-Shortcuts`
- `A2A-SIN-Apple-macOS`

**Fallback Models:**
1. `google/antigravity-gemini-3-flash`
2. `qwen/coder-model`

---

### 6. Team Apple

**Zweck:** macOS/iOS Automation — Mail, Notes, Calendar, FaceTime, Safari, etc.

| Feld | Wert |
|:---|:---|
| **Manager** | `A2A-SIN-Apple` |
| **Config** | `my-sin-apple.json` |
| **Primary Model** | `nvidia/minimaxai/minimax-m2.7` |

**Mitglieder:**
- `A2A-SIN-Apple-Mail`
- `A2A-SIN-Apple-Notes`
- `A2A-SIN-Apple-Calendar-Contacts`
- `A2A-SIN-Apple-Reminders`
- `A2A-SIN-Apple-Photos-Files`
- `A2A-SIN-Apple-FaceTime`
- `A2A-SIN-Apple-Notifications`
- `A2A-SIN-Apple-Mobile`
- `A2A-SIN-Apple-Safari-WebKit`
- `A2A-SIN-Apple-DeviceControl`
- `A2A-SIN-Apple-Shortcuts`
- `A2A-SIN-Apple-SystemSettings`

**Fallback Models:**
1. `google/antigravity-gemini-3-flash`
2. `qwen/coder-model`

---

### 7. Team Social

**Zweck:** Social Media Automation — TikTok, Instagram, X, LinkedIn, Facebook, YouTube

| Feld | Wert |
|:---|:---|
| **Manager** | `A2A-SIN-Social` |
| **Config** | `my-sin-social.json` |
| **Primary Model** | `google/antigravity-gemini-3.1-pro` |

**Mitglieder:**
- `A2A-SIN-Instagram`
- `A2A-SIN-Medium`
- `A2A-SIN-YouTube`
- `A2A-SIN-TikTok`
- `A2A-SIN-X-Twitter`

**Fallback Models:**
1. `nvidia/minimaxai/minimax-m2.7`
2. `google/antigravity-claude-sonnet-4-6`

---

### 8. Team Messaging

**Zweck:** Messaging Integration — WhatsApp, Telegram, Signal, Discord, iMessage

| Feld | Wert |
|:---|:---|
| **Manager** | `A2A-SIN-Messaging` |
| **Config** | `my-sin-messaging.json` |
| **Primary Model** | `meta/llama-3.2-11b-vision-instruct` |

**Mitglieder:**
- `A2A-SIN-WhatsApp`
- `A2A-SIN-Teams`
- `A2A-SIN-WeChat`
- `A2A-SIN-LINE`
- `A2A-SIN-Nostr`
- `A2A-SIN-Zoom`

**Fallback Models:**
1. `nvidia/minimaxai/minimax-m2.7`
2. `qwen/coder-model`

---

### 9. Team Forum

**Zweck:** Forum Automation — Reddit, HackerNews, StackOverflow, Quora, DevTo

| Feld | Wert |
|:---|:---|
| **Manager** | `A2A-SIN-Forum` |
| **Config** | `my-sin-forum.json` |
| **Primary Model** | `meta/llama-3.2-11b-vision-instruct` |

**Mitglieder:**
- `A2A-SIN-StackOverflow`
- `A2A-SIN-Quora`

**Fallback Models:**
1. `nvidia/minimaxai/minimax-m2.7`
2. `qwen/coder-model`

---

### 10. Team Legal

**Zweck:** Legal Automation — ClaimWriter, Patents, Damages, Compliance, Contract

| Feld | Wert |
|:---|:---|
| **Manager** | `A2A-SIN-Legal` |
| **Config** | `my-sin-legal.json` |
| **Primary Model** | `google/antigravity-gemini-3.1-pro` |

**Mitglieder:**
- `A2A-SIN-Patents`
- `A2A-SIN-Tax`

**Fallback Models:**
1. `nvidia/minimaxai/minimax-m2.7`
2. `qwen/coder-model`

---

### 11. Team Commerce

**Zweck:** Commerce Automation — Shop-Finance, Shop-Logistic, TikTok-Shop, Stripe

| Feld | Wert |
|:---|:---|
| **Manager** | `A2A-SIN-Commerce` |
| **Config** | `my-sin-commerce.json` |
| **Primary Model** | `google/antigravity-gemini-3.1-pro` |

**Mitglieder:**
- `A2A-SIN-TikTok-Shop`

**Fallback Models:**
1. `nvidia/minimaxai/minimax-m2.7`
2. `google/antigravity-claude-sonnet-4-6`

---

### 12. Team Community

**Zweck:** Community Management — Discord, WhatsApp, Telegram, YouTube Community

| Feld | Wert |
|:---|:---|
| **Manager** | `A2A-SIN-Community` |
| **Config** | `my-sin-community.json` |
| **Primary Model** | `meta/llama-3.2-11b-vision-instruct` |

**Mitglieder:** _(leer — in Entwicklung)_

**Fallback Models:**
1. `nvidia/minimaxai/minimax-m2.7`
2. `qwen/coder-model`

---

### 13. Team Google

**Zweck:** Google Workspace — Google-Apps, Google-Chat, Opal

| Feld | Wert |
|:---|:---|
| **Manager** | `A2A-SIN-Google` |
| **Config** | `my-sin-google.json` |
| **Primary Model** | `google/antigravity-gemini-3.1-pro` |

**Mitglieder:**
- `A2A-SIN-Opal`

**Fallback Models:**
1. `nvidia/minimaxai/minimax-m2.7`
2. `qwen/coder-model`

---

### 14. Team Microsoft

**Zweck:** Microsoft 365 — Teams, Outlook, OneDrive, Excel, Word, PowerPoint

| Feld | Wert |
|:---|:---|
| **Manager** | `A2A-SIN-Microsoft` |
| **Config** | `my-sin-microsoft.json` |
| **Primary Model** | `nvidia/minimaxai/minimax-m2.7` |

**Mitglieder:** _(leer — in Entwicklung)_

**Fallback Models:**
1. `google/antigravity-claude-sonnet-4-6`
2. `qwen/coder-model`

---

### 15. Team Research

**Zweck:** Deep Research Agent

| Feld | Wert |
|:---|:---|
| **Manager** | `A2A-SIN-Research` |
| **Config** | `my-sin-research.json` |
| **Primary Model** | `google/antigravity-gemini-3.1-pro` |

**Mitglieder:**
- `A2A-SIN-Research`

**Fallback Models:**
1. `nvidia/minimaxai/minimax-m2.7`
2. `google/antigravity-claude-opus-4-6-thinking`

---

### 16. Team Media ComfyUI

**Zweck:** Media Generation — ImageGen, VideoGen, ComfyUI Workflows

| Feld | Wert |
|:---|:---|
| **Manager** | `A2A-SIN-Media-ComfyUI` |
| **Config** | `my-sin-media-comfyui.json` |
| **Primary Model** | `google/antigravity-gemini-3.1-pro` |

**Mitglieder:** _(leer — in Entwicklung)_

**Fallback Models:**
1. `nvidia/minimaxai/minimax-m2.7`
2. `google/antigravity-claude-sonnet-4-6`

---

### 17. Team Media Music

**Zweck:** Music Production — Beats, Producer, Singer, Songwriter, Videogen

| Feld | Wert |
|:---|:---|
| **Manager** | `A2A-SIN-Media-Music` |
| **Config** | `my-sin-media-music.json` |
| **Primary Model** | `google/antigravity-gemini-3.1-pro` |

**Mitglieder:** _(leer — in Entwicklung)_

**Fallback Models:**
1. `nvidia/minimaxai/minimax-m2.7`
2. `google/antigravity-claude-sonnet-4-6`

---

### 18. Team Coding CyberSec

**Zweck:** Security Specialists — BugBounty, Cloudflare, Security-Spezialisten

| Feld | Wert |
|:---|:---|
| **Manager** | `A2A-SIN-Code-CyberSec` |
| **Config** | `my-sin-coding-cybersec.json` |
| **Primary Model** | `google/antigravity-claude-sonnet-4-6` |

**Mitglieder:**
- `A2A-SIN-Security-Recon`
- `A2A-SIN-Security-Fuzz`

**Fallback Models:**
1. `nvidia/minimaxai/minimax-m2.7`
2. `google/antigravity-gemini-3.1-pro`

---

### 19. Team Coding Frontend

**Zweck:** Frontend Specialists — Accessibility, App-Shell, Commerce-UI, Design-Systems

| Feld | Wert |
|:---|:---|
| **Manager** | `A2A-SIN-Code-Frontend` |
| **Config** | `my-sin-coding-frontend.json` |
| **Primary Model** | `google/antigravity-gemini-3.1-pro` |

**Mitglieder:** _(leer — in Entwicklung)_

**Fallback Models:**
1. `google/antigravity-claude-sonnet-4-6`
2. `nvidia/minimaxai/minimax-m2.7`

---

### 20. Team Coding Backend

**Zweck:** Backend Specialists — Server, OracleCloud, Passwordmanager

| Feld | Wert |
|:---|:---|
| **Manager** | `A2A-SIN-Code-Backend` |
| **Config** | `my-sin-coding-backend.json` |
| **Primary Model** | `google/antigravity-claude-sonnet-4-6` |

**Mitglieder:** _(leer — in Entwicklung)_

**Fallback Models:**
1. `nvidia/minimaxai/minimax-m2.7`
2. `google/antigravity-gemini-3.1-pro`

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

## Struktur

Jeder Team-Eintrag hat folgende Struktur:

```json
"team-name": {
    "name": "Team Display Name",
    "description": "Was das Team macht",
    "manager": "A2A-SIN-Manager-Name",
    "config_file": "my-sin-team-name.json",
    "members": [
        "A2A-SIN-Agent-1",
        "A2A-SIN-Agent-2"
    ],
    "primary_model": "google/antigravity-claude-sonnet-4-6",
    "fallback_models": [
        "nvidia/minimaxai/minimax-m2.7",
        "qwen/coder-model",
        "google/antigravity-gemini-3.1-pro"
    ]
}
```

| Feld | Pflicht | Beschreibung |
|:---|:---:|:---|
| `name` | ✅ | Anzeigename des Teams |
| `description` | ✅ | Was das Team macht |
| `manager` | ✅ | A2A Manager Agent für dieses Team |
| `config_file` | ✅ | Pfad zur Team-Config (my-sin-team-*.json) |
| `members` | ✅ | Liste aller Agenten im Team (kann leer sein) |
| `primary_model` | ✅ | Bevorzugtes Modell für den Manager |
| `fallback_models` | ✅ | Failover-Kette (3 Modelle) |

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

## Modelle

### Verfügbare Modelle

| Modell | Typ | Verwendung |
|:---|:---|:---|
| `google/antigravity-claude-sonnet-4-6` | Premium | Coding, Security, komplexe Tasks |
| `google/antigravity-claude-opus-4-6-thinking` | Premium | Deep Research, komplexe Analyse |
| `google/antigravity-gemini-3.1-pro` | Standard | Google Workspace, Media, Legal |
| `google/antigravity-gemini-3-flash` | Fast | Worker, Messaging, Forum |
| `nvidia/minimaxai/minimax-m2.7` | Standard | Infrastructure, Apple, Backup |
| `qwen/coder-model` | Budget | Coding-assist, schnelle Tasks |
| `nvidia-nim/stepfun-ai/step-3.5-flash` | Budget | Explore/Librarian, interne Tasks |

### Modell-Auswahl Regeln

> [!TIP]
> ** Regel 1:** Primary Model zuerst versuchen
> ** Regel 2:** Bei 429 Rate-Limit → nächstes Modell in Fallback-Kette
> ** Regel 3:** Bei 401 Unauthorized → Token refreshen, dann Retry
> ** Regel 4:** Bei 3 aufeinanderfolgenden Fehlern → Team Manager escalieren

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

## Defaults

Der `defaults` Block gilt für alle Teams:

```json
"defaults": {
    "explore_model": "nvidia-nim/stepfun-ai/step-3.5-flash",
    "librarian_model": "nvidia-nim/stepfun-ai/step-3.5-flash",
    "fallback_models": [
        "google/antigravity-gemini-3-flash",
        "nvidia/minimaxai/minimax-m2.7",
        "qwen/coder-model"
    ]
}
```

| Feld | Modell | Zweck |
|:---|:---|:---|
| `explore_model` | nvidia-nim/stepfun-ai/step-3.5-flash | Codebase-Analyse (subagent) |
| `librarian_model` | nvidia-nim/stepfun-ai/step-3.5-flash | Documentation-Lookup (subagent) |

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

## Verwendung

### Team für Task auswählen

```python
# Beispiel: Einen Survey-Task starten
team = "team-worker"
task = "survey_prolific"

# Primary Model nutzen
model = teams[team]["primary_model"]

# Bei Rate-Limit: Fallback durchgehen
for model in [teams[team]["primary_model"]] + teams[team]["fallback_models"]:
    result = call_model(model, task)
    if result.status == "success":
        break
    elif result.status == "rate_limit":
        continue  # nächstes Modell
```

### Neues Team hinzufügen

```json
"team-neu": {
    "name": "Team Neu",
    "description": "Beschreibung",
    "manager": "A2A-SIN-Team-Neu",
    "config_file": "my-sin-team-neu.json",
    "members": [
        "A2A-SIN-Neu-1",
        "A2A-SIN-Neu-2"
    ],
    "primary_model": "google/antigravity-gemini-3.1-pro",
    "fallback_models": [
        "nvidia/minimaxai/minimax-m2.7",
        "qwen/coder-model"
    ]
}
```

> [!IMPORTANT]
> Nach Änderung: `sin-sync` ausführen um die Config auf alle VMs zu verteilen!

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

## Changelog

### v2.2.1 (2026-04-14) — Big Boss Update
- **20 Teams** total (17 + 3 Coding Sub-Specializations)
- **Neue Teams:** Media ComfyUI, Media Music, Coding CyberSec, Coding Frontend, Coding Backend
- **Modell-Hierarchien** vollständig dokumentiert
- **Defaults** für explore/librarian Modelle

### v2.0.0 (2026-04-11)
- Initiale Version mit 15 Teams

---

## Related

| Datei | Beschreibung |
|:---|:---|
| [`upgraded-opencode-stack/README.md`](https://github.com/Delqhi/upgraded-opencode-stack) | Hauptrepository mit allen A2A Agents |
| [`my-sin-team-*.json`](https://github.com/Delqhi/upgraded-opencode-stack) | Individuelle Team-Konfigurationen |
| [`oh-my-openagent.json`](https://github.com/Delqhi/upgraded-opencode-stack) | Subagenten-Modell-Konfiguration |

---

## License

Distributed under the **MIT License**. See [LICENSE](../LICENSE) for more information.

---

<p align="center">
<a href="https://opensin.ai">
<img src="https://img.shields.io/badge/🤖_Powered_by-OpenSIN--AI-7B3FE4?style=for-the-badge&logo=github&logoColor=white" alt="Powered by OpenSIN-AI" />
</a>
</p>
<p align="center">
<sub>Entwickelt vom <a href="https://opensin.ai"><strong>OpenSIN-AI</strong></a> Ökosystem – Enterprise AI Agents die autonom arbeiten.</sub><br/>
<sub>🌐 <a href="https://opensin.ai">opensin.ai</a> · 💬 <a href="https://opensin.ai/agents">Alle Agenten</a> · 🚀 <a href="https://opensin.ai/dashboard">Dashboard</a></sub>
</p>

<p align="right">(<a href="#readme-top">back to top</a>)</p>