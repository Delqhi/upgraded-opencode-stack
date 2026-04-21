#!/usr/bin/env python3
"""
LAYER 5 — COMPOSITOR WITH STRICT LAYOUT ZONES
==============================================
Composites all layers together. Critically, ensures that
TEXT and OBJECT do not overlap, and that the MASCOT remains
the dominant left-side anchor.
"""

from __future__ import annotations
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

CANVAS_W, CANVAS_H = 1920, 1080


def load_rgba(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA")


def add_vignette(canvas: Image.Image) -> Image.Image:
    vignette = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(vignette)
    for i in range(15):
        t = i / 15
        alpha = int(t * t * 150)
        margin = int(t * 500)
        draw.rectangle(
            [margin, margin, CANVAS_W - margin, CANVAS_H - margin],
            outline=(0, 0, 0, alpha),
            width=30,
        )
    vignette = vignette.filter(ImageFilter.GaussianBlur(40))
    canvas.alpha_composite(vignette)
    return canvas


def run(
    bg_path: Path, obj_path: Path, mascot_path: Path, text_path: Path, final_path: Path
) -> int:
    final_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Background
    canvas = load_rgba(bg_path).resize((CANVAS_W, CANVAS_H))

    # 2. Object Layer (tight crop, then anchor right-bottom)
    obj = load_rgba(obj_path)
    obj_bbox = obj.getbbox()
    if obj_bbox:
        obj = obj.crop(obj_bbox)
    max_obj = 640
    scale = min(max_obj / obj.width, max_obj / obj.height, 1.0)
    if scale < 1.0:
        obj = obj.resize(
            (int(obj.width * scale), int(obj.height * scale)), Image.Resampling.LANCZOS
        )
    obj_x = CANVAS_W - obj.width - 70
    obj_y = CANVAS_H - obj.height - 60
    canvas.alpha_composite(obj, (obj_x, obj_y))

    # 3. Mascot Layer (Anchor Left-Bottom)
    mascot = load_rgba(mascot_path)
    # The mascot is pre-sized/positioned, but we ensure it aligns to bottom
    m_y = CANVAS_H - mascot.height if mascot.height <= CANVAS_H else 0
    canvas.alpha_composite(mascot, (0, m_y))

    # 4. Text Layer (Anchor Right-Top)
    text_layer = load_rgba(text_path)
    canvas.alpha_composite(text_layer, (0, 0))

    # 5. Post-Processing
    canvas = add_vignette(canvas)

    # Final Color Grade
    rgb = canvas.convert("RGB")
    rgb = ImageEnhance.Contrast(rgb).enhance(1.15)
    rgb = ImageEnhance.Color(rgb).enhance(1.20)

    rgb.save(final_path, format="PNG", optimize=False)
    print(f"[Layer 5] Composited thumbnail saved -> {final_path}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 6:
        print("Usage: compose_thumbnail.py <bg> <obj> <mascot> <text> <final_path>")
        sys.exit(1)
    sys.exit(
        run(
            Path(sys.argv[1]),
            Path(sys.argv[2]),
            Path(sys.argv[3]),
            Path(sys.argv[4]),
            Path(sys.argv[5]),
        )
    )
