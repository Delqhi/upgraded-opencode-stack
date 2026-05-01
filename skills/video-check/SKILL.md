---
name: video-check
description: "Use when the user asks to analyze a video file frame-by-frame with a token-efficient vision workflow. Prefer the bundled `/video-check` command, which extracts scene-change keyframes and sends them to `nvidia/meta/llama-3.2-11b-vision-instruct` via NVIDIA NIM."
---

> OpenCode mirror: sourced from `~/.config/opencode/skills/video-check` and mirrored for OpenCode CLI usage.

# Video Check

Analyzes a local video with a compact, production-style frame-sampling pipeline.

## When to use

- Summarize a video clip
- Extract key scenes, objects, people, text, or anomalies
- Produce short, structured notes from screen recordings, demos, meetings, or dashcam clips

## Workflow

1. Verify `node`, `ffmpeg`, and `NVIDIA_API_KEY` are available.
2. Ensure `NVIDIA_API_KEY` is set.
3. Extract up to 8 scene-change keyframes (first frame always included as fallback).
4. Encode frames as inline images and send them to `nvidia/meta/llama-3.2-11b-vision-instruct`.
5. Return a short answer with at most 6 bullet points.

## Token / cost optimization

- Scene-change sampling avoids fixed-FPS bloat.
- Max 8 frames keeps the request compact.
- 768px square frames are enough for robust vision understanding.
- `temperature: 0` and a short prompt reduce output churn.

## Output style

- Main scenes / progression
- Important objects / people
- Context / action
- Notable issues / anomalies

## Command

Use the bundled Node ESM command:

```bash
/video-check /path/to/video.mp4
```

Optional custom prompt:

```bash
/video-check /path/to/video.mp4 "Find text overlays and summarize only the facts."
```

Useful flags:

- `--json` for CI/CD output
- `--chunk` to force chunking on short clips
