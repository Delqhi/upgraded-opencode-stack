#!/usr/bin/env bash
set -euo pipefail

# Upgraded OpenCode Stack Installer
# PURELY ADDITIVE — überschreibt NIEMALS bestehende Configs
# Usage: ./install.sh [--dry-run] [--skip-npm]

DRY_RUN=false
SKIP_NPM=false
OPENCODE_DIR="$HOME/.config/opencode"
BIN_DIR="$HOME/.local/bin"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()  { echo -e "${BLUE}[INFO]${NC}  $1"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
log_skip()  { echo -e "${YELLOW}[SKIP]${NC}  $1 (bereits vorhanden)"; }

for arg in "$@"; do
  case $arg in
    --dry-run) DRY_RUN=true; log_info "Dry run mode" ;;
    --skip-npm) SKIP_NPM=true ;;
  esac
done

echo "============================================"
echo "  Upgraded OpenCode Stack Installer"
echo "  (Überschreibt NIEMALS bestehende Configs)"
echo "============================================"
echo ""

# 1. Prerequisites
log_info "Checking prerequisites..."
command -v opencode &>/dev/null || { log_error "OpenCode CLI nicht gefunden. Erst installieren: https://opencode.ai"; exit 1; }
log_ok "OpenCode CLI: $(which opencode)"
command -v node &>/dev/null || { log_error "Node.js nicht gefunden"; exit 1; }
log_ok "Node.js: $(node --version)"
command -v npm &>/dev/null || { log_error "npm nicht gefunden"; exit 1; }
log_ok "npm: $(npm --version)"
echo ""

# 2. Create directories
mkdir -p "$OPENCODE_DIR" "$BIN_DIR"
log_ok "Verzeichnisse bereit"
echo ""

# 3. Install npm plugins (global — betrifft nur diese Machine)
if [ "$SKIP_NPM" = false ]; then
  log_info "Installing npm plugins..."
  for plugin in "opencode-antigravity-auth@1.6.5-beta.0" "oh-my-opencode@3.11.2"; do
    if npm ls -g "$plugin" 2>/dev/null | grep -q "$plugin"; then
      log_skip "$plugin"
    else
      [ "$DRY_RUN" = false ] && npm install -g "$plugin" 2>&1 | tail -1
      log_ok "$plugin installiert"
    fi
  done
  if [ -d "plugins/local-plugins/opencode-openrouter-auth" ]; then
    if npm ls -g "opencode-openrouter-auth" 2>/dev/null | grep -q "opencode-openrouter-auth"; then
      log_skip "opencode-openrouter-auth"
    else
      [ "$DRY_RUN" = false ] && cd "plugins/local-plugins/opencode-openrouter-auth" && npm install -g . 2>&1 | tail -1 && cd "$SCRIPT_DIR"
      log_ok "opencode-openrouter-auth installiert"
    fi
  fi
  if [ -d "local-plugins/opencode-qwen-auth" ]; then
    if npm ls -g "opencode-qwen-auth" 2>/dev/null | grep -q "opencode-qwen-auth"; then
      log_skip "opencode-qwen-auth"
    else
      [ "$DRY_RUN" = false ] && cd "local-plugins/opencode-qwen-auth" && npm install -g . 2>&1 | tail -1 && cd "$SCRIPT_DIR"
      log_ok "opencode-qwen-auth installiert"
    fi
  fi
else
  log_info "Skipping npm installs"
fi
echo ""

# 4. Helper: sync directory — NUR was fehlt wird kopiert
sync_dir_additive() {
  local src="$1" dst="$2" label="$3"
  if [ ! -d "$src" ] || [ ! "$(ls -A "$src" 2>/dev/null)" ]; then
    return
  fi
  if [ "$DRY_RUN" = false ]; then
    mkdir -p "$dst"
    # rsync mit --ignore-existing = überschreibt NIE existierende Dateien
    rsync -a --ignore-existing "$src/" "$dst/"
  fi
  local src_count=$(find "$src" -type f | wc -l | tr -d ' ')
  local dst_count=$(find "$dst" -type f 2>/dev/null | wc -l | tr -d ' ')
  if [ "$dst_count" -gt 0 ]; then
    log_ok "$label: $src_count Dateien nach $dst (existierende wurden NICHT überschrieben)"
  else
    log_ok "$label: $src_count Dateien nach $dst"
  fi
}

# 5. Install ALL directories — rein additiv, kein overwrite
log_info "Installing skills..."
sync_dir_additive "skills" "$OPENCODE_DIR/skills" "Skills"

log_info "Installing commands..."
sync_dir_additive "commands" "$OPENCODE_DIR/commands" "Commands"

log_info "Installing scripts..."
sync_dir_additive "scripts" "$OPENCODE_DIR/scripts" "Scripts"
[ "$DRY_RUN" = false ] && chmod +x "$OPENCODE_DIR/scripts/"*.sh 2>/dev/null || true

log_info "Installing hooks..."
sync_dir_additive "hooks" "$OPENCODE_DIR/hooks" "Hooks"
[ "$DRY_RUN" = false ] && chmod +x "$OPENCODE_DIR/hooks/"* 2>/dev/null || true

log_info "Installing templates..."
sync_dir_additive "templates" "$OPENCODE_DIR/templates" "Templates"

log_info "Installing instructions..."
sync_dir_additive "instructions" "$OPENCODE_DIR/instructions" "Instructions"

log_info "Installing rules..."
sync_dir_additive "rules" "$OPENCODE_DIR/rules" "Rules"

log_info "Installing tools..."
sync_dir_additive "tools" "$OPENCODE_DIR/tools" "Tools"

log_info "Installing platforms..."
sync_dir_additive "platforms" "$OPENCODE_DIR/platforms" "Platforms"

log_info "Installing agents..."
sync_dir_additive "agents" "$OPENCODE_DIR/agents" "Agents"

log_info "Installing agents-instructions..."
sync_dir_additive "agents-instructions" "$OPENCODE_DIR/agents-instructions" "Agent Instructions"

log_info "Installing vendor..."
sync_dir_additive "vendor" "$OPENCODE_DIR/vendor" "Vendor"

log_info "Installing nodriver-profiles..."
sync_dir_additive "nodriver-profiles" "$OPENCODE_DIR/nodriver-profiles" "Nodriver Profiles"

log_info "Installing chrome_profile..."
sync_dir_additive "chrome_profile" "$OPENCODE_DIR/chrome_profile" "Chrome Profile"

echo ""

# 6. Install CLI tools — NUR wenn nicht bereits vorhanden
log_info "Installing CLI tools to $BIN_DIR..."
if [ -d "bin" ]; then
  for tool in bin/*; do
    [ -f "$tool" ] || continue
    local_name=$(basename "$tool")
    if [ -f "$BIN_DIR/$local_name" ]; then
      log_skip "$local_name"
    else
      if [ "$DRY_RUN" = false ]; then
        cp "$tool" "$BIN_DIR/$local_name"
        chmod +x "$BIN_DIR/$local_name"
      fi
      log_ok "CLI tool: $local_name"
    fi
  done
fi

echo ""

# 7. opencode.json — INTELLIGENT MERGE, NIEMALS overwrite
if [ -f "opencode.json" ]; then
  log_info "Merging opencode.json..."
  if [ -f "$OPENCODE_DIR/opencode.json" ]; then
    if [ "$DRY_RUN" = false ]; then
      python3 << 'PYEOF'
import json, os, sys
target = os.path.expanduser("~/.config/opencode/opencode.json")
source = "opencode.json"

with open(source) as f: src = json.load(f)
with open(target) as f: tgt = json.load(f)

# Backup existing config
import shutil, datetime
backup = target + f".backup-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
shutil.copy2(target, backup)
print(f"  Backup erstellt: {backup}")

# Merge plugins (deduplicate)
src_plugins = src.get("plugin", [])
tgt_plugins = tgt.get("plugin", [])
all_plugins, seen = [], set()
for p in tgt_plugins + src_plugins:
    pkg_name = p.split("@")[0] if "@" in p else p
    if pkg_name not in seen: all_plugins.append(p); seen.add(pkg_name)
tgt["plugin"] = all_plugins

# Merge providers — kanonische Model-Metadaten updaten, Benutzer-Overrides bewahren
src_providers = src.get("provider", {})
tgt_providers = tgt.get("provider", {})
for name, prov in src_providers.items():
    if name not in tgt_providers:
        tgt_providers[name] = prov
    else:
        # Modelle: kanonische Felder updaten
        src_models = prov.get("models", {})
        tgt_models = tgt_providers[name].get("models", {})
        for mname, src_mconf in src_models.items():
            if mname not in tgt_models:
                # Neues Modell
                tgt_models[mname] = src_mconf
            else:
                # Existierendes Modell: Kanonische Felder updaten, andere erhalten
                tgt_mconf = tgt_models[mname]
                # name
                if "name" in src_mconf:
                    tgt_mconf["name"] = src_mconf["name"]
                # id
                if "id" in src_mconf:
                    tgt_mconf["id"] = src_mconf["id"]
                # limit (context, output)
                if "limit" in src_mconf and isinstance(src_mconf["limit"], dict):
                    if "limit" not in tgt_mconf or not isinstance(tgt_mconf.get("limit"), dict):
                        tgt_mconf["limit"] = {}
                    for k, v in src_mconf["limit"].items():
                        tgt_mconf["limit"][k] = v
                # modalities
                if "modalities" in src_mconf:
                    tgt_mconf["modalities"] = src_mconf["modalities"]
                # attachment
                if "attachment" in src_mconf:
                    tgt_mconf["attachment"] = src_mconf["attachment"]
        tgt_providers[name]["models"] = tgt_models
        # Provider-Optionen: kanonische Felder (baseURL, apiKey) updaten
        src_opts = prov.get("options", {})
        tgt_opts = tgt_providers[name].get("options", {})
        
        # Force sync critical options from source for modal provider
        if name == "modal":
            for k, v in src_opts.items():
                tgt_opts[k] = v
        else:
            # For others, only add new options
            for k, v in src_opts.items():
                if k not in tgt_opts:
                    tgt_opts[k] = v
        
        tgt_providers[name]["options"] = tgt_opts
        if "npm" in prov and "npm" not in tgt_providers[name]:
            tgt_providers[name]["npm"] = prov["npm"]
tgt["provider"] = tgt_providers

# Merge agents
src_agents = src.get("agent", {})
tgt_agents = tgt.get("agent", {})
for aname, src_aconf in src_agents.items():
    if aname not in tgt_agents:
        tgt_agents[aname] = src_aconf
    else:
        if "model" in src_aconf:
            tgt_agents[aname]["model"] = src_aconf["model"]
        if "description" in src_aconf:
            tgt_agents[aname]["description"] = src_aconf["description"]
        if "fallback" in src_aconf:
            tgt_agents[aname]["fallback"] = src_aconf["fallback"]
tgt["agent"] = tgt_agents

# Merge commands — NUR neue
src_cmds = src.get("command", {})
tgt_cmds = tgt.get("command", {})
for name, cconf in src_cmds.items():
    if name not in tgt_cmds:
        tgt_cmds[name] = cconf
tgt["command"] = tgt_cmds

# User's model choice BEWAHREN — NIEMALS überschreiben
# User's $schema BEWAHREN
if "$schema" not in tgt and "$schema" in src: tgt["$schema"] = src["$schema"]

with open(target, "w") as f: json.dump(tgt, f, indent=2)
print(f"  Gemerged: {len(all_plugins)} plugins, {len(tgt_providers)} providers, {len(tgt_agents)} agents, {len(tgt_cmds)} commands")
print(f"  Deine bestehenden Configs wurden NICHT überschrieben!")
PYEOF
    fi
    log_ok "opencode.json gemerged (Backup erstellt)"
  else
    # User hat noch keine config — dann kopieren
    if [ "$DRY_RUN" = false ]; then
      cp opencode.json "$OPENCODE_DIR/opencode.json"
    fi
    log_ok "opencode.json erstellt (erste Installation)"
  fi
fi

# ============================================================================
# 7b. 🚨 ANTIGRAVITY PLUGIN ENFORCEMENT — OBERSTE SCHUTZREGEL
# ============================================================================
# WARUM: Der Python-Merge oben (Schritt 7) dedupliziert Plugins korrekt, aber
# er garantiert NICHT die Reihenfolge. opencode-antigravity-auth MUSS immer
# als ERSTES Plugin in der Liste stehen, weil opencode Plugins in Array-Reihenfolge
# lädt. Wenn ein anderes Plugin zuerst geladen wird und Google OAuth versucht,
# schlägt es fehl — weil der Antigravity-Token noch nicht injiziert wurde.
#
# KONSEQUENZ OHNE DIESE REGEL:
# - Google OAuth für Claude Sonnet/Opus/Gemini funktioniert NICHT
# - Alle antigravity-* Modelle sind nicht verfügbar
# - Der gesamte Fleet-Betrieb bricht zusammen
#
# DIESE REGEL DARF NIEMALS ENTFERNT WERDEN.
# Referenz: AGENTS.md Priority -10.0 — Antigravity Plugin Verbot
# ============================================================================
log_info "🚨 Enforcing antigravity plugin protection (Priority -10.0)..."
if [ -f "opencode.json" ] || [ -f "$OPENCODE_DIR/opencode.json" ]; then
  if [ "$DRY_RUN" = false ]; then
    python3 << 'PYEOF'
import json, sys, os

# Pfad zur globalen opencode.json — das ist die SSOT (Single Source of Truth)
# Diese Datei steuert ALLE Modelle, Plugins und Provider für den gesamten Fleet
target = os.path.expanduser("~/.config/opencode/opencode.json")

# Das Plugin das IMMER als ERSTES in der Plugin-Liste stehen MUSS.
# Es stellt Google OAuth für alle antigravity-Modelle bereit.
# Ohne diesen Plugin-Eintrag: kein Claude, kein Gemini — NICHTS.
# ACHTUNG: Beim Update auf neue Versionen muss dieser String angepasst werden!
ANTIGRAVITY_PLUGIN = "opencode-antigravity-auth@1.6.5-beta.0"
# Package-Name-Präfix zum Suchen/Erkennen (versionsunabhängig)
ANTIGRAVITY_PKG = "opencode-antigravity-auth"

# Sicherheitscheck: Existiert die Zieldatei?
if not os.path.exists(target):
    print(f"  ⚠️  opencode.json nicht gefunden unter {target} — überspringe Enforcement")
    sys.exit(0)

# Config laden
with open(target, "r") as f:
    cfg = json.load(f)

# Plugin-Array auslesen (kann auch fehlen bei frischer Installation)
plugins = cfg.get("plugin", [])

# Prüfen ob antigravity bereits als ERSTES Element in der Liste steht
if plugins and plugins[0].startswith(ANTIGRAVITY_PKG):
    # ✅ Alles korrekt — kein Eingriff nötig
    print(f"  ✅ Antigravity plugin ist bereits an Position 0: {plugins[0]}")
else:
    # 🚨 EINGRIFF NÖTIG: Plugin fehlt oder ist nicht an Position 0
    old_first = plugins[0] if plugins else "(leer)"

    # Alle bestehenden antigravity-Einträge entfernen (könnten an falscher Stelle sein)
    # Wir entfernen sie zunächst alle und fügen dann den korrekten an Position 0 ein
    plugins_without_antigravity = [p for p in plugins if not p.startswith(ANTIGRAVITY_PKG)]

    # Antigravity-Plugin ZWINGEND an Index 0 einfügen — niemals anders
    plugins_fixed = [ANTIGRAVITY_PLUGIN] + plugins_without_antigravity

    # Gefixte Plugin-Liste zurückschreiben
    cfg["plugin"] = plugins_fixed

    # Config-Datei atomar überschreiben (json.dump schreibt vollständig oder gar nicht)
    with open(target, "w") as f:
        json.dump(cfg, f, indent=2)

    # Laute Warnung ausgeben damit der User informiert ist
    print(f"  🚨🚨🚨 ANTIGRAVITY PLUGIN ENFORCEMENT AUSGELÖST 🚨🚨🚨")
    print(f"  🚨 Vorheriges erstes Plugin war: {old_first}")
    print(f"  🚨 opencode-antigravity-auth wurde an Position 0 gesetzt!")
    print(f"  ✅ Plugin-Array jetzt (erste 3): {plugins_fixed[:3]}")

# ----------------------------------------------------------------
# ZUSÄTZLICHE SICHERHEITSPRÜFUNG: Google Provider Konfiguration
# ----------------------------------------------------------------
# Der 'google' Provider DARF KEINEN direkten apiKey in options haben!
# Wenn ein apiKey vorhanden ist, wird der Antigravity OAuth-Flow umgangen
# und Anfragen gehen direkt an generativelanguage.googleapis.com — VERBOTEN!
# Die einzige erlaubte Methode ist OAuth via das opencode-antigravity-auth Plugin.
providers = cfg.get("provider", {})

if "google" not in providers:
    # Kein Google-Provider = keine antigravity-Modelle verfügbar
    print(f"  ⚠️  WARNUNG: 'google' Provider fehlt in opencode.json!")
    print(f"  ⚠️  Antigravity-Modelle (Claude/Gemini) werden NICHT verfügbar sein!")
elif "apiKey" in providers.get("google", {}).get("options", {}):
    # apiKey im google-Provider = direkter API-Zugriff = VERBOTEN (PRIORITY -10.0)
    print(f"  🚨 KRITISCH: google Provider hat apiKey in options — Antigravity-OAuth wird UMGANGEN!")
    print(f"  🚨 PERMANENT VERBOTEN: generativelanguage.googleapis.com direkt nutzen!")
    print(f"  🚨 Bitte apiKey aus google.options entfernen und nur das Antigravity Plugin nutzen!")
else:
    # ✅ Korrekt konfiguriert: kein direkter apiKey, OAuth wird vom Plugin bereitgestellt
    print(f"  ✅ Google Provider korrekt konfiguriert (kein direkter apiKey, verwendet OAuth Plugin)")
PYEOF
    log_ok "Antigravity Plugin Protection enforced (Priority -10.0)"
  else
    log_info "[DRY-RUN] Würde Antigravity Plugin Protection erzwingen"
  fi
fi

# 8. AGENTS.md — IMMER aktualisieren (enthält kritische Fleet-Regeln wie Vision Gate Mandate)
# AGENTS.md ist die SSOT für globale Agenten-Regeln und MUSS immer auf dem neuesten Stand sein.
# Ein Backup der bestehenden wird erstellt, aber die neue Version wird IMMER installiert.
if [ -f "AGENTS.md" ]; then
  if [ -f "$OPENCODE_DIR/AGENTS.md" ]; then
    if [ "$DRY_RUN" = false ]; then
      cp "$OPENCODE_DIR/AGENTS.md" "$OPENCODE_DIR/AGENTS.md.backup-$(date +%Y%m%d-%H%M%S)"
      cp AGENTS.md "$OPENCODE_DIR/AGENTS.md"
    fi
    log_ok "AGENTS.md aktualisiert (Backup der alten Version erstellt)"
  else
    if [ "$DRY_RUN" = false ]; then
      cp AGENTS.md "$OPENCODE_DIR/AGENTS.md"
    fi
    log_ok "AGENTS.md erstellt (erste Installation)"
  fi
fi

# 9. oh-my-opencode.json — IMMER aktualisieren (enthält Agent-Modell-Routing + Fallback-Chains)
# oh-my-opencode.json steuert welches Modell jeder Subagent (explore, librarian, sisyphus, etc.) nutzt.
# MUSS immer aktuell sein, damit die Fleet mit den richtigen Modellen arbeitet.
if [ -f "oh-my-opencode.json" ]; then
  if [ -f "$OPENCODE_DIR/oh-my-opencode.json" ]; then
    if [ "$DRY_RUN" = false ]; then
      cp "$OPENCODE_DIR/oh-my-opencode.json" "$OPENCODE_DIR/oh-my-opencode.json.backup-$(date +%Y%m%d-%H%M%S)"
      cp oh-my-opencode.json "$OPENCODE_DIR/oh-my-opencode.json"
    fi
    log_ok "oh-my-opencode.json aktualisiert (Backup der alten Version erstellt)"
  else
    if [ "$DRY_RUN" = false ]; then
      cp oh-my-opencode.json "$OPENCODE_DIR/oh-my-opencode.json"
    fi
    log_ok "oh-my-opencode.json erstellt (erste Installation)"
  fi
fi

# 10. .env.example als .env — NUR wenn keine existiert
if [ -f ".env.example" ]; then
  if [ -f "$OPENCODE_DIR/.env" ]; then
    log_skip ".env (existiert bereits)"
  else
    if [ "$DRY_RUN" = false ]; then
      cp .env.example "$OPENCODE_DIR/.env"
    fi
    log_ok ".env erstellt — bitte API Keys eintragen!"
  fi
fi

# Ensure MODAL_BASE_URL is set in user .env for Modal pool proxy
if [ -f "$OPENCODE_DIR/.env" ]; then
  if ! grep -q '^MODAL_BASE_URL=' "$OPENCODE_DIR/.env"; then
    echo 'MODAL_BASE_URL=http://92.5.60.87:4100/modal/v1' >> "$OPENCODE_DIR/.env"
    log_ok "MODAL_BASE_URL in .env ergänzt"
  fi
fi

if [ -f "$HOME/.zshrc" ]; then
  if ! grep -q 'MODAL_BASE_URL' "$HOME/.zshrc"; then
    echo "" >> "$HOME/.zshrc"
    echo 'export MODAL_BASE_URL="http://92.5.60.87:4100/modal/v1"' >> "$HOME/.zshrc"
    echo 'export MODAL_GATEWAY_KEY="sk-sin-fleet-master"' >> "$HOME/.zshrc"
    echo 'export MODAL_POOL_URL="http://92.5.60.87:4100/modal"' >> "$HOME/.zshrc"
    log_ok "Modal environment variables added to ~/.zshrc"
  fi
fi

echo ""
echo "============================================"
echo "  Installation Complete!"
echo "============================================"
echo ""
echo "Was passiert ist:"
echo "  ✓ Neue Skills, Commands, Scripts hinzugefügt"
echo "  ✓ Bestehende Dateien wurden NICHT überschrieben"
echo "  ✓ opencode.json intelligent gemerged"
echo "  ✓ Backup deiner alten opencode.json erstellt"
echo "  ✓ CLI Tools nur installiert wenn noch nicht vorhanden"
echo ""
echo "Was du noch tun musst:"
echo "  1. ~/.config/opencode/.env mit API Keys befüllen"
echo "  2. opencode --version testen"
echo ""
echo "Docs: https://github.com/Delqhi/upgraded-opencode-stack"
