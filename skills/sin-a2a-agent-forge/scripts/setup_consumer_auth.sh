#!/usr/bin/env bash
# Auto-inject Producer-Consumer Auth into a new A2A Agent
# Usage: ./setup_consumer_auth.sh /path/to/new-agent-root

set -euo pipefail

if [[ -z "${1:-}" ]]; then
  echo "Usage: $0 /path/to/new-agent-root"
  exit 1
fi

AGENT_ROOT="$1"

if [[ ! -d "$AGENT_ROOT" ]]; then
  echo "Error: Directory $AGENT_ROOT does not exist."
  exit 1
fi

SCRIPT_DIR="$AGENT_ROOT/scripts"
mkdir -p "$SCRIPT_DIR"

PULL_SCRIPT="$SCRIPT_DIR/hf_pull_script.py"

echo "Injecting hf_pull_script.py into $SCRIPT_DIR..."

cat << 'PYSCRIPT' > "$PULL_SCRIPT"
#!/usr/bin/env python3
"""
A2A Consumer Rotator (HF VM Pull Script)
Pulls a fresh OpenAI token from SIN-Supabase when a rate-limit is hit.
Infinite Scaling Architecture.
"""

import os
import json
import requests
from pathlib import Path

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
AUTH_FILE = Path.home() / ".local" / "share" / "opencode" / "auth.json"

def pull_fresh_token():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ FEHLER: SUPABASE_URL oder SUPABASE_SERVICE_ROLE_KEY fehlen!")
        return False
        
    base_url = SUPABASE_URL.rstrip('/')
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    print("🔍 Suche frischen Token im Pool...")
    get_url = f"{base_url}/rest/v1/openai_account_pool?status=eq.FRESH&limit=1"
    resp = requests.get(get_url, headers=headers, timeout=5)
    
    if resp.status_code != 200 or not resp.json():
        print("❌ FEHLER: Kein frischer Token im Pool verfügbar!")
        return False
        
    row = resp.json()[0]
    row_id = row["id"]
    new_auth_data = row["auth_json_data"]
    
    patch_url = f"{base_url}/rest/v1/openai_account_pool?id=eq.{row_id}"
    requests.patch(patch_url, headers=headers, json={"status": "IN_USE"}, timeout=5)

    AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)
    current_data = {}
    if AUTH_FILE.exists():
        try:
            current_data = json.loads(AUTH_FILE.read_text())
        except:
            pass
            
    current_data["openai"] = new_auth_data
    AUTH_FILE.write_text(json.dumps(current_data, indent=2))
    print(f"🚀 ERFOLG: Lokale auth.json überschrieben. (ID: {row_id})")
    return True

if __name__ == "__main__":
    pull_fresh_token()
PYSCRIPT

chmod +x "$PULL_SCRIPT"
echo "✅ Consumer Auth Script installed at $PULL_SCRIPT"
