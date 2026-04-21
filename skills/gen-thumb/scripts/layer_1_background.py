#!/usr/bin/env python3
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


ROUTER = Path(
    "/Users/jeremy/.config/opencode/skills/imagegen/scripts/gemini_image_router.py"
)


def build_args(variant: str, topic: str) -> list[str]:
    if variant == "B":
        return [
            "--use-case",
            "stylized-concept",
            "--scene",
            f"Cinematic thumbnail background for {topic}; black void on the left, explosive neon green and gold energy on the right",
            "--subject",
            "abstract energy bloom and particle storm",
            "--style",
            "ultra polished cinematic concept art, premium creator thumbnail, dark-mode friendly, no clutter",
            "--composition",
            "wide frame, large negative space on the left for a mascot, bright focal energy on the right",
            "--lighting",
            "dramatic, high contrast, volumetric rays, premium thumbnail lighting",
            "--palette",
            "black, charcoal, neon green, gold, subtle emerald highlights",
            "--constraints",
            "background only, no text, no logos, no watermark, no people, no UI, no clutter",
            "--negative",
            "cartoon style, cheap glow, oversaturated noise, amateur composition",
        ]

    return [
        "--use-case",
        "stylized-concept",
        "--scene",
        f"Minimal cinematic thumbnail background for {topic}; nearly black left side with subtle green haze and a brighter right edge",
        "--subject",
        "abstract atmospheric glow",
        "--style",
        "clean premium concept art, restrained, high-end, elegant, dark, no clutter",
        "--composition",
        "wide frame, large empty dark area on the left for the mascot, clean glow on the right for text and object",
        "--lighting",
        "soft cinematic glow, controlled contrast, subtle volumetric haze",
        "--palette",
        "black, charcoal, neon green, subtle gold accents",
        "--constraints",
        "background only, no text, no logos, no watermark, no people, no UI, no clutter",
        "--negative",
        "cartoon style, cheap glow, oversaturated noise, amateur composition",
    ]


def run(variant: str, topic: str, out_path: Path) -> int:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    print(
        f"[Layer 1] Generating routed background ({variant}) -> {out_path}", flush=True
    )

    cmd = [
        sys.executable,
        str(ROUTER),
        "generate",
        "--prompt",
        f"Create a premium YouTube thumbnail background about: {topic}.",
        "--size",
        "1536x1024",
        "--out",
        str(out_path),
        *build_args(variant, topic),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    if result.stdout:
        print(result.stdout, end="", flush=True)
    if result.stderr:
        print(result.stderr, end="", flush=True)
    if result.returncode != 0:
        return result.returncode

    if out_path.exists():
        return 0

    for alt_suffix in (".jpeg", ".jpg", ".png"):
        alt = out_path.with_suffix(alt_suffix)
        if alt.exists():
            shutil.move(str(alt), str(out_path))
            return 0

    print(f"[Layer 1] ERROR: no image written to {out_path}", flush=True)
    return 1


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: layer_1_background.py <A|B> <topic> <out_path>")
        sys.exit(1)
    sys.exit(run(sys.argv[1].upper(), sys.argv[2], Path(sys.argv[3])))
