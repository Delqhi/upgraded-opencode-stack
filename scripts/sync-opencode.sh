#!/bin/bash
set -euo pipefail

echo "🚀 Starte OpenCode Fleet Synchronization (Mac -> Target VMs)..."
echo ""
echo "⚠️  AUTH ISOLATION POLICY:"
echo "   Jede Maschine hat IHREN EIGENEN OpenCode Zen Auth Account!"
echo "   auth.json, opencode.db und alle Auth-Dateien werden NIEMALS synchronisiert."
echo "   Mac 1 = Auth Account #1 | Mac 2 = Auth Account #2 | HF VM 1 = Auth Account #3 | etc."
echo ""

# Target machines
TARGETS_HOSTS=("ubuntu@92.5.60.87")
TARGETS_LABELS=("OCI VM (Primary)")

# Add HF VMs if they have SSH access
# ["ubuntu@hf-vm-1.hf.space"]="HF VM 1"
# ["ubuntu@hf-vm-2.hf.space"]="HF VM 2"

# Files that MUST NEVER be synced (Auth isolation)
EXCLUSIONS=(
  # OpenCode Zen Auth
  'auth.json'
  'antigravity-accounts.json'
  'token.json'
  'telegram_config.json'
  
  # Database files (contain auth state)
  '*.db'
  '*.sqlite*'
  'opencode.db'
  'zen-auth.db'
  
  # Browser profiles (contain cookies/sessions)
  'browser-profiles/'
  'chrome-profiles/'
  'firefox-profiles/'
  'Default/'
  'Geschäftlich/'
  
  # Cache and temp files
  'logs/'
  'tmp/'
  '.cache/'
  '*.log'
  '*.tmp'
  
  # Local state files
  'state.json'
  'session.json'
  'last-login.json'
  
  # HF pull scripts (may contain machine-specific tokens)
  'hf_pull_script.py'
  'hf-bootstrap.json'
  
  # Room13 worktrees (local dev state)
  '.room13-worktrees/'
)

# Build rsync exclude arguments
EXCLUDE_ARGS=""
for exc in "${EXCLUSIONS[@]}"; do
  EXCLUDE_ARGS="$EXCLUDE_ARGS --exclude '$exc'"
done

SYNC_COUNT=0
FAIL_COUNT=0

for i in "${!TARGETS_HOSTS[@]}"; do
  HOST="${TARGETS_HOSTS[$i]}"
  LABEL="${TARGETS_LABELS[$i]}"
  TARGET_DIR="~/.config/opencode/"
  
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "📡 Syncing to: $LABEL ($HOST)"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  
  # Test connection
  if ! ssh -o ConnectTimeout=10 -o BatchMode=yes $HOST "echo '✅ Connected'" 2>/dev/null; then
    echo "❌ Cannot connect to $LABEL ($HOST) - skipping"
    FAIL_COUNT=$((FAIL_COUNT + 1))
    continue
  fi
  
  # Ensure target directory exists
  ssh -o ConnectTimeout=10 $HOST "mkdir -p $TARGET_DIR"
  
  # Sync with ALL exclusions
  eval rsync -avz --delete $EXCLUDE_ARGS \
    ~/.config/opencode/ "$HOST:$TARGET_DIR"
  
  if [ $? -eq 0 ]; then
    echo "✅ Sync to $LABEL completed successfully"
    SYNC_COUNT=$((SYNC_COUNT + 1))

    # ========================================================================
    # 🚨 ANTIGRAVITY PLUGIN ENFORCEMENT AUF DEM REMOTE-ZIEL (PRIORITY -10.0)
    # ========================================================================
    # WARUM: rsync kopiert opencode.json 1:1 vom Mac zum Remote.
    # Wenn die Mac-Datei bereits korrekt ist, ist das Remote-Ergebnis korrekt.
    # ABER: Falls die Mac-Datei jemals beschädigt wurde (Plugin fehlt oder
    # an falscher Position), propagiert rsync diese Beschädigung an ALLE
    # Remotes gleichzeitig. Diese Post-Sync-Prüfung fängt genau das ab.
    #
    # KONSEQUENZ OHNE DIESE PRÜFUNG:
    # Ein einziger falscher commit auf dem Mac = gesamte Fleet ohne Antigravity.
    # Das bedeutet: kein Claude, kein Gemini, keine antigravity-* Modelle.
    # Dieser SSH-Check ist die letzte Verteidigungslinie.
    #
    # DIESE REGEL DARF NIEMALS ENTFERNT WERDEN.
    # Referenz: AGENTS.md Priority -10.0 — Antigravity Plugin Verbot
    # ========================================================================
    echo "🚨 Enforcing antigravity plugin protection on $LABEL..."
    ssh -o ConnectTimeout=10 $HOST 'python3 -c "
import json, sys, os

# Pfad zur opencode.json auf dem Remote-System
target = os.path.expanduser(\"~/.config/opencode/opencode.json\")

# Das Plugin das IMMER als ERSTES in der Plugin-Liste stehen MUSS.
# Ohne diesen Eintrag: kein Google OAuth, keine antigravity-Modelle.
PLUGIN = \"opencode-antigravity-auth@1.6.5-beta.0\"
# Package-Name-Präfix (versionsunabhängige Erkennung)
PKG = \"opencode-antigravity-auth\"

# Sicherheitscheck: Existiert die Datei auf dem Remote?
if not os.path.exists(target):
    print(\"  ⚠️  opencode.json nicht gefunden auf Remote — überspringe Enforcement\")
    sys.exit(0)

# Config laden und Plugin-Array auslesen
with open(target) as f:
    cfg = json.load(f)
plugins = cfg.get(\"plugin\", [])

# Prüfen ob antigravity BEREITS an Position 0 ist
if plugins and plugins[0].startswith(PKG):
    # ✅ Korrekt — kein Eingriff nötig
    print(\"  ✅ Antigravity plugin ist korrekt an Position 0: \" + plugins[0])
else:
    # 🚨 EINGRIFF NÖTIG auf dem Remote
    old_first = plugins[0] if plugins else \"(leer)\"

    # Alle bestehenden antigravity-Einträge entfernen (könnten an falscher Position sein)
    plugins_without = [p for p in plugins if not p.startswith(PKG)]

    # Plugin ZWINGEND an Index 0 einfügen — niemals anders
    plugins_fixed = [PLUGIN] + plugins_without
    cfg[\"plugin\"] = plugins_fixed

    # Config-Datei auf dem Remote überschreiben
    with open(target, \"w\") as f:
        json.dump(cfg, f, indent=2)

    # Laute Warnung: Diese Situation sollte durch die Mac-seitige Prüfung
    # (install.sh Schritt 7b) verhindert worden sein. Wenn wir hier landen,
    # war die Mac-Datei beim rsync-Zeitpunkt bereits beschädigt.
    print(\"  🚨🚨🚨 REMOTE ANTIGRAVITY PLUGIN ENFORCEMENT AUSGELÖST 🚨🚨🚨\")
    print(\"  🚨 Vorheriges erstes Plugin auf Remote war: \" + old_first)
    print(\"  🚨 opencode-antigravity-auth wurde remote an Position 0 gesetzt!\")
    print(\"  ⚠️  Prüfe Mac-seitige opencode.json — möglicherweise ist sie beschädigt!\")
"'
    echo ""

    # Verify auth isolation on target
    echo "🔍 Verifying auth isolation on $LABEL..."
    ssh -o ConnectTimeout=10 $HOST "
      echo '  Checking auth files on target...'
      if [ -f ~/.config/opencode/auth.json ]; then
        echo '  ⚠️  WARNING: auth.json exists on target (should be machine-specific!)'
      else
        echo '  ✅ auth.json correctly excluded'
      fi
      if [ -f ~/.config/opencode/opencode.db ]; then
        echo '  ⚠️  WARNING: opencode.db exists on target (should be machine-specific!)'
      else
        echo '  ✅ opencode.db correctly excluded'
      fi
      if [ -f ~/.config/opencode/antigravity-accounts.json ]; then
        echo '  ⚠️  WARNING: antigravity-accounts.json exists on target'
      else
        echo '  ✅ antigravity-accounts.json correctly excluded'
      fi
    "
  else
    echo "❌ Sync to $LABEL failed"
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
  echo ""
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Sync Summary:"
echo "   ✅ Successful: $SYNC_COUNT"
echo "   ❌ Failed: $FAIL_COUNT"
echo "   🔒 Auth isolation: ENFORCED"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "⚠️  REMINDER: Each machine MUST have its own OpenCode Zen Auth account!"
echo "   Do NOT copy auth.json, opencode.db, or antigravity-accounts.json between machines."
echo "   Each machine authenticates independently with its own credentials."
