# NVIDIA NIM Provider Integration

## Problem

OpenCode 1.3.10+ verwendet standardmäßig die OpenAI **Responses API** (`/v1/responses`) für alle OpenAI-kompatiblen Provider. NVIDIA NIM unterstützt jedoch **nur** die Chat Completions API (`/v1/chat/completions`).

**Fehler ohne Lösung:**
```
APIError: Not Found: 404 page not found
URL: https://integrate.api.nvidia.com/v1/responses
```

## Lösung

Ein lokaler Proxy übersetzt eingehende `/v1/responses` Requests in `/v1/chat/completions` bevor sie an NVIDIA gesendet werden.

### Proxy starten

```bash
NVIDIA_API_KEY=nvapi-xxx node ~/.config/opencode/scripts/nvidia-proxy.js &
```

Der Proxy läuft auf `http://127.0.0.1:4199` und:
- Übersetzt `/v1/responses` → `/v1/chat/completions`
- Konvertiert `input` → `messages` Format
- Forwarded alle anderen Requests unverändert

### Provider Konfiguration

In `~/.config/opencode/opencode.json`:

```json
{
  "provider": {
    "nvidia-nim": {
      "npm": "@ai-sdk/openai",
      "name": "NVIDIA NIM",
      "options": {
        "baseURL": "http://127.0.0.1:4199/v1",
        "apiKey": "{env:NVIDIA_API_KEY}"
      },
      "models": {
        "minimax-m2.7": {
          "name": "Minimax M2.7 (NVIDIA NIM)",
          "id": "minimaxai/minimax-m2.7",
          "limit": {
            "context": 204800,
            "output": 8192
          }
        }
      }
    }
  }
}
```

## Verfügbare Modelle

| Modell | ID | Context | Max Output |
|--------|-----|---------|------------|
| Minimax M2.7 | minimaxai/minimax-m2.7 | 204,800 | 8,192 |
| Qwen 3.5 122B | qwen/qwen3.5-122b-a10b | 262,144 | 32,768 |
| Qwen 3.5 397B | qwen/qwen3.5-397b-a17b | 262,144 | 32,768 |
| Step 3.5 Flash | stepfun-ai/step-3.5-flash | 262,144 | 32,768 |

## Verwendung

```bash
# Mit minimax-m2.7
opencode run "Deine Frage" --model nvidia-nim/minimax-m2.7

# Als Fallback für sin-executor-solo
# In der Agent-Konfiguration: "fallback": "nvidia-nim/minimax-m2.7"
```

## Troubleshooting

**Proxy läuft nicht:**
```bash
ps aux | grep nvidia-proxy
lsof -i :4199
```

**API Key prüfen:**
```bash
curl -s -X POST "https://integrate.api.nvidia.com/v1/chat/completions" \
  -H "Authorization: Bearer $NVIDIA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"minimaxai/minimax-m2.7","messages":[{"role":"user","content":"hi"}],"max_tokens":10}'
```

**Logs prüfen:**
```bash
tail -f /tmp/nvidia-proxy.log
```
