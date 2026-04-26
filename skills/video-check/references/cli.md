# video-check CLI

## Requirements
- Node.js 18+
- `ffmpeg`
- `NVIDIA_API_KEY`

## Usage

```bash
/video-check ./clip.mp4
```

Custom prompt:

```bash
/video-check ./clip.mp4 "Erkenne alle Texteinblendungen und fasse sie zusammen."
```

## Notes
- The command samples up to 8 scene-change keyframes.
- Model: `nvidia/meta/llama-3.2-11b-vision-instruct`
- Output is intentionally short and structured.
- `--json` emits CI/CD-friendly structured output.
- `--chunk` forces long-video segmentation.
