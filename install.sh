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
  for plugin in "opencode-antigravity-auth@1.6.5-beta.0" "oh-my-opencode@3.11.2" "opencode-qwencode-auth"; do
    if npm ls -g "$plugin" 2>/dev/null | grep -q "$plugin"; then
      log_skip "$plugin"
    else
      [ "$DRY_RUN" = false ] && npm install -g "$plugin" 2>&1 | tail -1
      log_ok "$plugin installiert"
    fi
  done
  # Local openrouter auth
  if [ -d "plugins/local-plugins/opencode-openrouter-auth" ]; then
    if npm ls -g "opencode-openrouter-auth" 2>/dev/null | grep -q "opencode-openrouter-auth"; then
      log_skip "opencode-openrouter-auth"
    else
      [ "$DRY_RUN" = false ] && cd "plugins/local-plugins/opencode-openrouter-auth" && npm install -g . 2>&1 | tail -1 && cd "$SCRIPT_DIR"
      log_ok "opencode-openrouter-auth installiert"
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

# Merge providers — NUR neue Provider und Modelle
src_providers = src.get("provider", {})
tgt_providers = tgt.get("provider", {})
for name, prov in src_providers.items():
    if name not in tgt_providers:
        tgt_providers[name] = prov
    else:
        # NUR neue Modelle hinzufügen
        src_models = prov.get("models", {})
        tgt_models = tgt_providers[name].get("models", {})
        new_models = 0
        for mname, mconf in src_models.items():
            if mname not in tgt_models:
                tgt_models[mname] = mconf
                new_models += 1
        tgt_providers[name]["models"] = tgt_models
        # NUR neue Optionen
        src_opts = prov.get("options", {})
        tgt_opts = tgt_providers[name].get("options", {})
        for k, v in src_opts.items():
            if k not in tgt_opts: tgt_opts[k] = v
        tgt_providers[name]["options"] = tgt_opts
        if "npm" in prov and "npm" not in tgt_providers[name]:
            tgt_providers[name]["npm"] = prov["npm"]
tgt["provider"] = tgt_providers

# Merge agents — NUR neue
src_agents = src.get("agent", {})
tgt_agents = tgt.get("agent", {})
new_agents = 0
for name, aconf in src_agents.items():
    if name not in tgt_agents:
        tgt_agents[name] = aconf
        new_agents += 1
tgt["agent"] = tgt_agents

# Merge commands — NUR neue
src_cmds = src.get("command", {})
tgt_cmds = tgt.get("command", {})
new_cmds = 0
for name, cconf in src_cmds.items():
    if name not in tgt_cmds:
        tgt_cmds[name] = cconf
        new_cmds += 1
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

# 8. AGENTS.md — NUR wenn user keine hat
if [ -f "AGENTS.md" ]; then
  if [ -f "$OPENCODE_DIR/AGENTS.md" ]; then
    log_skip "AGENTS.md (deine bestehende wurde NICHT überschrieben)"
    log_info "Tipp: Vergleiche mit: diff ~/.config/opencode/AGENTS.md AGENTS.md"
  else
    if [ "$DRY_RUN" = false ]; then
      cp AGENTS.md "$OPENCODE_DIR/AGENTS.md"
    fi
    log_ok "AGENTS.md erstellt"
  fi
fi

# 9. .env.example als .env — NUR wenn keine existiert
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
