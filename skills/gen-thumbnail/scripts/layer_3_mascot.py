#!/usr/bin/env python3
"""
LAYER 3 — MASCOT PROCESSOR
===========================
Sole responsibility: take the real mascot PNG, apply emotion/energy treatment,
size it correctly, position it left-dominant, and output a transparent RGBA layer
at full 1920x1080 canvas size ready for compositing.

Emotion modes (set by variant):
  A = calm / curious / smug  → normal saturation, soft green rim glow
  B = shocked / hype / intense → boosted contrast, bright green/gold glow burst, slight tilt

Usage:
    python3 layer_3_mascot.py <variant> <mascot_src> <out_path>
"""

from __future__ import annotations
import sys
from pathlib import Path
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw


CANVAS_W, CANVAS_H = 1920, 1080


def apply_emotion(mascot: Image.Image, variant: str) -> Image.Image:
    mascot = mascot.convert("RGBA")

    if variant == "B":
        # Boost contrast and saturation for high-energy dramatic look
        mascot = ImageEnhance.Contrast(mascot).enhance(1.25)
        mascot = ImageEnhance.Color(mascot).enhance(1.35)
        # Slight rightward tilt to add energy / motion feel
        mascot = mascot.rotate(-4, expand=True, resample=Image.Resampling.BICUBIC)
    else:
        # Subtle saturation lift for clean confident look
        mascot = ImageEnhance.Color(mascot).enhance(1.1)

    return mascot


def build_glow(mascot: Image.Image, variant: str) -> Image.Image:
    # Extract alpha channel as mask to build glow only around mascot silhouette
    alpha = mascot.split()[3]

    if variant == "B":
        # Multi-layer glow: outer green burst + inner gold rim
        glow_color_outer = (25, 255, 76, 90)  # neon green, semi-transparent
        glow_color_inner = (255, 214, 0, 110)  # gold rim
        blur_outer = 55
        blur_inner = 22
    else:
        # Single soft green rim glow
        glow_color_outer = (25, 255, 76, 70)
        glow_color_inner = (25, 255, 76, 50)
        blur_outer = 35
        blur_inner = 14

    def make_glow_layer(blur_r: int, color: tuple) -> Image.Image:
        tinted = Image.new("RGBA", mascot.size, color)
        tinted.putalpha(alpha)
        blurred = tinted.filter(ImageFilter.GaussianBlur(blur_r))
        return blurred

    outer = make_glow_layer(blur_outer, glow_color_outer)
    inner = make_glow_layer(blur_inner, glow_color_inner)

    glow = Image.new("RGBA", mascot.size, (0, 0, 0, 0))
    glow.alpha_composite(outer)
    glow.alpha_composite(inner)
    return glow


def run(variant: str, mascot_src: Path, out_path: Path) -> int:
    if not mascot_src.exists():
        print(f"[Layer 3] ERROR: mascot not found at {mascot_src}", flush=True)
        return 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"[Layer 3] Mascot ({variant}) → {out_path}", flush=True)

    mascot = Image.open(mascot_src).convert("RGBA")
    mascot = apply_emotion(mascot, variant)

    # Scale mascot to 110% of canvas height — intentional overflow.
    # Real YouTube creators (MrBeast style) have the character OVERFLOW the canvas
    # bottom edge. The head and torso dominate the frame. This is the look we want.
    # 110% means the mascot is taller than the canvas — the bottom portion is cropped,
    # which is FINE and intentional. It fills the entire left half visually.
    target_h = int(CANVAS_H * 1.10)
    ratio = target_h / mascot.height
    target_w = int(mascot.width * ratio)
    mascot = mascot.resize((target_w, target_h), Image.Resampling.LANCZOS)

    # Build glow halo sized to match scaled mascot
    glow = build_glow(mascot, variant)

    # Position: anchor mascot so its VERTICAL CENTER aligns with canvas center (not bottom).
    # This ensures the face/character upper body is fully visible even with overflow.
    # The mascot is left-aligned with a small inset margin.
    margin_left = -30  # slight negative inset so mascot bleeds off left edge slightly
    pos_x = margin_left
    # Center the mascot vertically: shift up so middle of mascot = middle of canvas
    pos_y = (
        CANVAS_H - target_h
    ) // 2  # negative value = top of mascot is above canvas top

    # Glow offset slightly to create depth — pulled left/up relative to mascot
    glow_x = pos_x - 40
    glow_y = pos_y - 30

    canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))

    # Clamp to canvas bounds before compositing
    def safe_composite(layer: Image.Image, x: int, y: int) -> None:
        # If position is negative, crop the layer accordingly
        lx, ly = max(x, 0), max(y, 0)
        cx = -x if x < 0 else 0
        cy = -y if y < 0 else 0
        cropped = layer.crop((cx, cy, layer.width, layer.height))
        canvas.alpha_composite(cropped, (lx, ly))

    safe_composite(glow, glow_x, glow_y)
    safe_composite(mascot, pos_x, pos_y)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path, format="PNG")
    print(
        f"[Layer 3] ✅ Saved {out_path} ({out_path.stat().st_size // 1024}KB)",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: layer_3_mascot.py <A|B> <mascot_src> <out_path>")
        sys.exit(1)
    sys.exit(run(sys.argv[1].upper(), Path(sys.argv[2]), Path(sys.argv[3])))
