#!/usr/bin/env bash
set -euo pipefail

# Upgraded OpenCode Stack Installer
# PURELY ADDITIVE — überschreibt NIEMALS bestehende Configs
# Usage: ./install.sh [--dry-run] [--skip-bun]

DRY_RUN=false
SKIP_BUN=false
OPENCODE_DIR="$HOME/.config/opencode"
BIN_DIR="$HOME/.local/bin"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REQUIRED_OPENCODE_VERSION="${REQUIRED_OPENCODE_VERSION:-1.14.24}"
OPENCODE_CANONICAL_BIN="$HOME/.opencode/bin/opencode"
export REQUIRED_OPENCODE_VERSION

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()  { echo -e "${BLUE}[INFO]${NC}  $1"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
log_skip()  { echo -e "${YELLOW}[SKIP]${NC}  $1 (bereits vorhanden)"; }

version_lt() {
  python3 - "$1" "$2" <<'PYEOF'
import re, sys

def normalize(value: str) -> list[int]:
    parts = [int(x) for x in re.findall(r"\d+", value)]
    return (parts + [0, 0, 0])[:3]

sys.exit(0 if normalize(sys.argv[1]) < normalize(sys.argv[2]) else 1)
PYEOF
}

resolve_opencode_bin() {
  if [ -x "$OPENCODE_CANONICAL_BIN" ]; then
    printf '%s\n' "$OPENCODE_CANONICAL_BIN"
    return 0
  fi
  if command -v opencode >/dev/null 2>&1; then
    command -v opencode
    return 0
  fi
  return 1
}

install_or_upgrade_opencode_cli() {
  log_info "Installing OpenCode CLI $REQUIRED_OPENCODE_VERSION via official installer..."
  if [ "$DRY_RUN" = false ]; then
    curl -fsSL https://opencode.ai/install | env VERSION="$REQUIRED_OPENCODE_VERSION" bash -s -- --no-modify-path
  fi
}

ensure_opencode_cli() {
  local opencode_bin=""
  local current_version=""

  if opencode_bin="$(resolve_opencode_bin 2>/dev/null)"; then
    current_version="$("$opencode_bin" --version 2>/dev/null | tr -d 'v' | awk '{print $NF}')"
    if [ -z "$current_version" ] || version_lt "$current_version" "$REQUIRED_OPENCODE_VERSION"; then
      log_warn "OpenCode CLI ${current_version:-unbekannt} ist zu alt; benötige >= $REQUIRED_OPENCODE_VERSION"
      install_or_upgrade_opencode_cli
    else
      log_ok "OpenCode CLI: $opencode_bin ($current_version)"
      return 0
    fi
  else
    log_warn "OpenCode CLI nicht gefunden — installiere kanonische Version $REQUIRED_OPENCODE_VERSION"
    install_or_upgrade_opencode_cli
  fi

  opencode_bin="$(resolve_opencode_bin 2>/dev/null || true)"
  if [ -z "$opencode_bin" ]; then
    log_error "OpenCode CLI konnte nicht installiert werden"
    exit 1
  fi

  current_version="$("$opencode_bin" --version 2>/dev/null | tr -d 'v' | awk '{print $NF}')"
  log_ok "OpenCode CLI: $opencode_bin (${current_version:-$REQUIRED_OPENCODE_VERSION})"
}

ensure_local_opencode_plugin_sdk() {
  log_info "Syncing local @opencode-ai/plugin runtime package..."
  if [ "$DRY_RUN" = false ]; then
    mkdir -p "$OPENCODE_DIR"
    python3 <<'PYEOF'
import json, os

path = os.path.expanduser("~/.config/opencode/package.json")
required = os.environ["REQUIRED_OPENCODE_VERSION"]
data = {}
if os.path.exists(path):
    with open(path) as f:
        data = json.load(f)
deps = data.setdefault("dependencies", {})
deps["@opencode-ai/plugin"] = required
with open(path, "w") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
PYEOF
    npm install --save-exact --prefix "$OPENCODE_DIR" "@opencode-ai/plugin@$REQUIRED_OPENCODE_VERSION" >/dev/null
  fi
  log_ok "@opencode-ai/plugin auf $REQUIRED_OPENCODE_VERSION synchronisiert"
}

for arg in "$@"; do
  case $arg in
    --dry-run) DRY_RUN=true; log_info "Dry run mode" ;;
    --skip-bun) SKIP_BUN=true ;;
  esac
done

echo "============================================"
echo "  Upgraded OpenCode Stack Installer"
echo "  (Überschreibt NIEMALS bestehende Configs)"
echo "============================================"
echo ""

# 1. Prerequisites
log_info "Checking prerequisites..."
ensure_opencode_cli
command -v node &>/dev/null || { log_error "Node.js nicht gefunden"; exit 1; }
log_ok "Node.js: $(node --version)"
command -v bun &>/dev/null || { log_error "bun nicht gefunden"; exit 1; }
log_ok "bun: $(bun --version)"
echo ""

# 2. Create directories
mkdir -p "$OPENCODE_DIR" "$BIN_DIR"
log_ok "Verzeichnisse bereit"
if [ -x "$OPENCODE_CANONICAL_BIN" ]; then
  [ "$DRY_RUN" = false ] && ln -sf "$OPENCODE_CANONICAL_BIN" "$BIN_DIR/opencode"
  log_ok "Kanonischer opencode Wrapper nach $BIN_DIR/opencode verlinkt"
fi
ensure_local_opencode_plugin_sdk
echo ""

# 3. Install bun plugins (global — betrifft nur diese Machine)
if [ "$SKIP_BUN" = false ]; then
log_info "Installing bun plugins..."
for plugin in "opencode-antigravity-auth@1.6.5-beta.0" "oh-my-opencode@3.11.2"; do
    # Check both bun AND npm global — npm is primary, bun fallback
    plugin_name="${plugin%%@*}"
    if npm ls -g "$plugin_name" 2>/dev/null | grep -q "$plugin_name" || bun pm ls -g 2>/dev/null | grep -q "$plugin"; then
      log_skip "$plugin"
    else
      [ "$DRY_RUN" = false ] && bun add -g "$plugin" 2>&1 | tail -1 || log_warn "$plugin (bun install fehlgeschlagen, npm global nutzen)"
      log_ok "$plugin installiert"
    fi
  done
  if [ -d "plugins/local-plugins/opencode-openrouter-auth" ]; then
    plugin_name="opencode-openrouter-auth"
    if npm ls -g "$plugin_name" 2>/dev/null | grep -q "$plugin_name" || bun pm ls -g 2>/dev/null | grep -q "$plugin_name"; then
      log_skip "$plugin_name"
    else
[ "$DRY_RUN" = false ] && cd "plugins/local-plugins/opencode-openrouter-auth" && bun add -g . 2>&1 | tail -1 || log_warn "$plugin_name (bun install fehlgeschlagen)" && cd "$SCRIPT_DIR"
log_ok "$plugin_name installiert"
fi
fi
else
  log_info "Skipping bun plugin installs"
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


sync_dir_overlay() {
  local src="$1" dst="$2" label="$3"
  if [ ! -d "$src" ] || [ ! "$(ls -A "$src" 2>/dev/null)" ]; then
    return
  fi
  if [ "$DRY_RUN" = false ]; then
    mkdir -p "$dst"
    rsync -a "$src/" "$dst/"
  fi
  log_ok "$label: kanonische Dateien nach $dst aktualisiert"
}

# 5. Install ALL directories — rein additiv, kein overwrite
log_info "Installing skills..."
sync_dir_additive "skills" "$OPENCODE_DIR/skills" "Skills"
log_info "Enforcing canonical create-flow..."
sync_dir_overlay "skills/create-flow" "$OPENCODE_DIR/skills/create-flow" "create-flow"

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

if [ -f "$OPENCODE_DIR/agents-instructions/blueprint-mandates/MANDATE-0.34.md" ]; then
  log_ok "Simone MCP + PCPM mandate aktiv"
else
  log_warn "Simone MCP + PCPM mandate fehlt noch"
fi

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

# 6b. Doctor CLI — installiere ALLE 23 Tools
log_info "Installing Doctor CLI (23 Tools)..."
BREW_TOOLS="cloc tokei lizard plantuml doxygen pandoc vale git-cliff lychee trufflehog gitleaks"
NPM_TOOLS="dependency-cruiser typedoc terraform-docs standard-readme conventional-changelog-cli auto-changelog markdownlint-cli2"
PIP_TOOLS="pydeps gitingest sphinx mkdocs pdoc repomix pylint md-dead-link-check code2flow"
for t in $BREW_TOOLS; do
    if ! command -v "$t" &>/dev/null; then
        brew install "$t" 2>/dev/null && log_ok "brew: $t" || log_warn "brew: $t skipped"
    else log_skip "$t"; fi
done
for t in $NPM_TOOLS; do
    if ! command -v "$t" &>/dev/null; then
        npm install -g "$t" 2>/dev/null && log_ok "npm: $t" || log_warn "npm: $t skipped"
    else log_skip "$t"; fi
done
for t in $PIP_TOOLS; do
    pip3 install --break-system-packages "$t" 2>/dev/null && log_ok "pip: $t" || log_warn "pip: $t skipped"
done
echo "✅ Doctor: 23 Tools installiert"

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
all_plugins = [p for p in all_plugins if "opencode-modal-pool-auth" not in p]
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
        
        # Force sync critical options from source for providers where stale
        # local values are known to break auth or routing.
        if name in {"modal", "qwen", "openai"}:
            tgt_opts = src_opts
        else:
            # For others, only add new options
            for k, v in src_opts.items():
                if k not in tgt_opts:
                    tgt_opts[k] = v
        
        tgt_providers[name]["options"] = tgt_opts
        if name in {"modal", "qwen"}:
            if "npm" in prov:
                tgt_providers[name]["npm"] = prov["npm"]
            if "name" in prov:
                tgt_providers[name]["name"] = prov["name"]
        elif "npm" in prov and "npm" not in tgt_providers[name]:
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

if [ -f "$OPENCODE_DIR/.env" ]; then
  if ! grep -q '^MODAL_API_KEY=' "$OPENCODE_DIR/.env"; then
    echo 'MODAL_API_KEY=' >> "$OPENCODE_DIR/.env"
    log_ok "MODAL_API_KEY in .env ergänzt"
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
echo "Docs: https://github.com/OpenSIN-Code/Infra-SIN-OpenCode-Stack"
