#!/usr/bin/env bash
set -euo pipefail

URL=""
ROUTES=()
TIMEOUT=15
TMP_DIR=""

cleanup() {
  if [[ -n "${TMP_DIR:-}" && -d "${TMP_DIR:-}" ]]; then
    rm -rf "$TMP_DIR"
  fi
}

trap cleanup EXIT

usage() {
  cat <<'EOF'
Usage:
  check_my_dev_in_web.sh --url <base-url> [--route /path] [--route /other] [--timeout 15]

Examples:
  check_my_dev_in_web.sh --url http://127.0.0.1:4173 --route / --route /pricing
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --url)
      URL="$2"
      shift 2
      ;;
    --route)
      ROUTES+=("$2")
      shift 2
      ;;
    --timeout)
      TIMEOUT="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ -z "$URL" ]]; then
  echo "Missing --url" >&2
  usage >&2
  exit 1
fi

if [[ ${#ROUTES[@]} -eq 0 ]]; then
  ROUTES=("/")
fi

TMP_DIR="$(mktemp -d)"

echo "== check-my-dev-in-web smoke =="
echo "base_url: $URL"
echo "routes: ${ROUTES[*]}"
echo

HTML_FILE="$TMP_DIR/root.html"
HTTP_CODE="$(curl -L -sS -o "$HTML_FILE" -w '%{http_code}' --max-time "$TIMEOUT" "$URL")"
echo "root_status: $HTTP_CODE"
if [[ "$HTTP_CODE" -lt 200 || "$HTTP_CODE" -ge 400 ]]; then
  echo "FAIL: root HTML request failed" >&2
  exit 2
fi

HTML_BYTES="$(wc -c < "$HTML_FILE" | tr -d ' ')"
echo "root_bytes: $HTML_BYTES"
if [[ "$HTML_BYTES" -lt 100 ]]; then
  echo "WARN: root HTML is suspiciously small"
fi

TITLE="$(python3 - <<'PY' "$HTML_FILE"
from pathlib import Path
import re, sys
text = Path(sys.argv[1]).read_text(errors='ignore')
m = re.search(r'<title>(.*?)</title>', text, re.I | re.S)
print(m.group(1).strip() if m else '')
PY
)"
echo "title: ${TITLE:-<missing>}"

ASSET_REPORT="$TMP_DIR/assets.txt"
python3 - <<'PY' "$HTML_FILE" "$URL" > "$ASSET_REPORT"
from pathlib import Path
from urllib.parse import urljoin
import re, sys
html = Path(sys.argv[1]).read_text(errors='ignore')
base = sys.argv[2]
assets = []
patterns = [r'<script[^>]+src=["\']([^"\']+)["\']', r'<link[^>]+href=["\']([^"\']+)["\']']
for pattern in patterns:
    for match in re.findall(pattern, html, re.I):
        if match.startswith('data:') or match.startswith('mailto:') or match.startswith('javascript:'):
            continue
        assets.append(urljoin(base, match))
seen = set()
for asset in assets:
    if asset not in seen:
        seen.add(asset)
        print(asset)
PY

BROKEN=0
ASSET_COUNT=0
while IFS= read -r asset; do
  [[ -z "$asset" ]] && continue
  ASSET_COUNT=$((ASSET_COUNT + 1))
  code="$(curl -L -sS -o /dev/null -w '%{http_code}' --max-time "$TIMEOUT" "$asset")"
  echo "asset[$ASSET_COUNT]: $code $asset"
  if [[ "$code" -lt 200 || "$code" -ge 400 ]]; then
    BROKEN=$((BROKEN + 1))
  fi
done < "$ASSET_REPORT"

echo "asset_count: $ASSET_COUNT"
echo "broken_assets: $BROKEN"

ROUTE_FAIL=0
for route in "${ROUTES[@]}"; do
  full_url="${URL%/}${route}"
  route_file="$TMP_DIR/route$(echo "$route" | tr '/?' '__').html"
  code="$(curl -L -sS -o "$route_file" -w '%{http_code}' --max-time "$TIMEOUT" "$full_url")"
  bytes="$(wc -c < "$route_file" | tr -d ' ')"
  echo "route: $route status=$code bytes=$bytes"
  if [[ "$code" -lt 200 || "$code" -ge 400 ]]; then
    ROUTE_FAIL=$((ROUTE_FAIL + 1))
  fi
done

if [[ "$BROKEN" -gt 0 ]]; then
  echo "FAIL: one or more referenced assets are broken" >&2
  exit 3
fi

if [[ "$ROUTE_FAIL" -gt 0 ]]; then
  echo "FAIL: one or more checked routes failed" >&2
  exit 4
fi

echo
echo "PASS: HTML, referenced assets, and checked routes responded successfully"
