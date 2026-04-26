# Video Check Command

`/video-check` is the token-efficient video analysis command for OpenCode.

## What it does
- Extracts up to 8 scene-change keyframes from a local video
- Sends them to `nvidia/meta/llama-3.2-11b-vision-instruct`
- Returns short bullet summaries or JSON for CI/CD

## Requirements
- Node.js 18+
- `ffmpeg`
- `NVIDIA_API_KEY`

## Usage

```bash
/video-check ./clip.mp4
```

Force chunking or JSON output:

```bash
/video-check ./clip.mp4 --chunk --json
```

## Implementation
- `commands/video-check.sh` is a thin wrapper
- `commands/video-check.mjs` contains the actual pipeline
- `skills/video-check/SKILL.md` documents the skill for OpenCode users
