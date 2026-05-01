# history.md — Development History (Updated 2026-05-01)

## 2026-05-01: Stealth-Orchestrator Agent + install.sh Fix

**Neuer Agent:**
- `agents/stealth-orchestrator/agent.json`: A2A Agent Card für den Stealth-Quad Orchestrator
- Modell: `nvidia-nim/nvidia/nemotron-3-nano-omni-30b-a3b-reasoning`
- 15 Capabilities (live_video_eye, hybrid_screenshot_video, skylight_click, survey_orchestration...)
- Team: Workers, Manager: SIN-Zeus
- `agents/stealth-orchestrator/README.md`: Vollständige Architektur-Dokumentation

**Install-Fix:**
- `install.sh` bun Plugin-Install: npm-global Check VOR bun, `|| true` Fallback
- Fix für `wrap-ansi-cjs@^7.0.0 failed to resolve` (bun vs npm Kompatibilitäts-Problem)
- Plugins werden jetzt korrekt erkannt wenn via npm global installiert

**Bereinigung:**
- Kaputte lokale Agent-Config in `stealth-runner/.opencode/agents/` gelöscht
- `sin-sync` deployed Agent auf OCI VM

**Verteilungs-Status:**
- ✅ Mac (lokal): `~/.config/opencode/agents/stealth-orchestrator/`
- ✅ OCI VM (92.5.60.87): via sin-sync
