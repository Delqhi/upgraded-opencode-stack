# 🚨 HUGGING FACE SPACE HARDWARE RULE (PRIORITY -7 — ABSOLUT, KEINE AUSNAHMEN) 🚨

**ABSOLUTES VERBOT: KEINE GPU/ZeroGPU SPACES FÜR A2A AGENT RUNTIMES!**

## WARUM

- HF Free Tier erlaubt UNBEGRENZT CPU-Basic Spaces gleichzeitig ($0)
- GPU/ZeroGPU Spaces haben Quota-Limit (8x) und benötigen Payment
- Alle Agent Spaces MÜSSEN auf CPU-Basic laufen

## PFLICHTEN

1. **JEDES HF Space MUSS auf `cpu-basic` Hardware konfiguriert sein**
2. **NIEMALS** GPU, ZeroGPU, oder paid Hardware für Agent Runtimes
3. **IMMER** Keep-Alive-Ping alle 5 Minuten (verhindert 48h Sleep)

## PFLICHT-DATEIEN FÜR JEDES HF SPACE

Jedes HF Space MUSS diese Dateien enthalten:

1. **Dockerfile** — Node.js/Python Container Definition
2. **A2A Server** — Express/FastAPI mit A2A Protocol (`server.js` oder `app.py`)
3. **Agent Logic** — Die eigentliche Agenten-Funktionalität
4. **Health Endpoint** — `/health` Endpoint für Monitoring
5. **A2A Card** — `/.well-known/agent-card.json` für Agent Discovery

## KORREKTE SPACE ERSTELLUNG

```bash
# 1. Space erstellen
curl -X POST https://huggingface.co/api/repos/create \
  -H "Authorization: Bearer $HF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "sin-my-agent", "type": "space", "sdk": "docker"}'

# 2. Hardware auf CPU-Basic setzen
curl -X POST https://huggingface.co/api/spaces/{owner}/{space}/hardware \
  -H "Authorization: Bearer $HF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"flavor": "cpu-basic"}'

# 3. Dockerfile + Code deployen (via git push)
git clone https://huggingface.co/spaces/{owner}/{space}
cp Dockerfile server.js package.json .well-known/agent-card.json {space}/
cd {space} && git add . && git commit -m "deploy agent" && git push
```

## KEEP-ALIVE PFLICHT

Jedes Space MUSS Keep-Alive-Ping haben (alle 5min) um 48h Sleep zu verhindern.

## KOSTEN

| Hardware  | Kosten  | Max gleichzeitig     |
| --------- | ------- | -------------------- |
| cpu-basic | **$0**  | **UNBEGRENZT**       |
| zerogpu   | FREE    | 8 pro Account        |
| gpu (T4)  | $288/Mo | Unbegrenzt (Payment) |

**FAZIT: CPU-Basic = $0, UNBEGRENZT Spaces!**

Siehe auch: [Global Dev Docs HF Space Hardware Standard](https://github.com/OpenSIN-AI/Global-Dev-Docs-Standard/blob/main/standards/hf-space-hardware.md)
