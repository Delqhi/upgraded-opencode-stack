# A2A-SIN-Vision-Colab Agent

## 🎯 Purpose

Screen recording + AI vision analysis via **google-colab-ai**. Every agent can:

- Record screen
- Capture screenshots
- Get AI analysis through Colab's free Gemini models
- **NO API KEY NEEDED** — uses Google account auth

## 🟢 Architecture (V2 — google-colab-ai)

```
[Agent] → look-screen CLI → [Colab + google-colab-ai] → Gemini Vision Analysis → [Agent]
              ↓
        Supabase Vision Logs
```

## 📋 Usage

### Quick Start

```bash
# Check status
look-screen --status

# Analyze screenshot
look-screen --screenshot /tmp/screen.png --describe

# Continuous monitoring
look-screen --interval 3

# Record screen
look-screen --record
# ... do something ...
look-screen --stop
```

### In Code (Any Agent)

```python
import subprocess

# Screenshot
subprocess.run(["screencapture", "-x", "/tmp/screen.png"])

# Analyze
result = subprocess.run(
    ["look-screen", "--screenshot", "/tmp/screen.png", "--describe"],
    capture_output=True, text=True
)
analysis = result.stdout
```

### In Colab (google-colab-ai)

```python
from google.colab import ai

# Text analysis
response = ai.generate_text("What is on this screen?")

# Vision analysis
response = ai.generate_text(
    "Describe this screenshot.",
    images=[screenshot_image]
)
```

## 🔧 Setup

1. Start Colab notebooks (2 accounts)
2. Save URLs to `~/.config/opencode/vision-colab-{1,2}.url`
3. Run `python3 ~/.open-auth-Token-Refresh-Service/tools/vision_colab_setup.py`

## 📁 Files

| File                                                                              | Purpose             |
| --------------------------------------------------------------------------------- | ------------------- |
| `~/.open-auth-Token-Refresh-Service/tools/look_screen.py`                         | CLI main            |
| `~/.open-auth-Token-Refresh-Service/tools/vision_colab_setup.py`                  | Setup wizard        |
| `~/.open-auth-Token-Refresh-Service/tools/vision-colab/colab_vision_hub_v2.ipynb` | Colab notebook      |
| `~/.config/opencode/vision-colab-{1,2}.url`                                       | Colab instance URLs |

## 🔗 Resources

- [google-colab-ai Getting Started](https://colab.research.google.com/github/googlecolab/colabtools/blob/main/notebooks/Getting_started_with_google_colab_ai.ipynb)
- [Colab MCP Server (March 2026)](https://googledevelopers.blogspot.com/announcing-the-colab-mcp-server-connect-any-ai-agent-to-google-colab/)
- [GitHub Issues #11-13](https://github.com/OpenSIN-AI/OpenSIN-Code/issues)
