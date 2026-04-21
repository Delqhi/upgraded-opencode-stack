#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


CANVAS_W, CANVAS_H = 1920, 1080
RIGHT_ZONE_X = 930
RIGHT_ZONE_Y = 96
RIGHT_ZONE_W = 860
RIGHT_ZONE_H = 300
FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Impact.ttf",
    "/System/Library/Fonts/Supplemental/Arial Black.ttf",
    "/System/Library/Fonts/Arial.ttf",
]


def load_font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def measure(
    draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont
) -> tuple[int, int, int, int]:
    box = draw.textbbox((0, 0), text, font=font)
    return box[0], box[1], box[2] - box[0], box[3] - box[1]


def render_line(
    words: list[str],
    font: ImageFont.FreeTypeFont,
    colors: list[tuple[int, int, int, int]],
    stroke_w: int,
) -> Image.Image:
    temp = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    draw = ImageDraw.Draw(temp)
    gap = max(24, font.size // 6)

    widths = []
    heights = []
    for word in words:
        _, _, w, h = measure(draw, word, font)
        widths.append(w)
        heights.append(h)

    line_w = sum(widths) + gap * (len(words) - 1)
    line_h = max(heights) if heights else 0
    pad = stroke_w + 150
    layer = Image.new("RGBA", (line_w + pad * 2, line_h + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    x = pad
    for index, word in enumerate(words):
        _, _, w, h = measure(draw, word, font)
        y = pad + (line_h - h) // 2
        fill = colors[min(index, len(colors) - 1)]
        d.text(
            (x + 24, y + 24),
            word,
            font=font,
            fill=(0, 0, 0, 185),
            stroke_width=stroke_w + 10,
            stroke_fill=(0, 0, 0, 185),
        )
        d.text(
            (x, y),
            word,
            font=font,
            fill=(0, 0, 0, 255),
            stroke_width=stroke_w,
            stroke_fill=(0, 0, 0, 255),
        )
        d.text((x, y), word, font=font, fill=fill)
        x += w + gap

    return layer.filter(ImageFilter.GaussianBlur(0.35))


def fit_font(words: list[str], start_size: int = 500) -> ImageFont.FreeTypeFont:
    probe = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    draw = ImageDraw.Draw(probe)
    size = start_size
    while size > 72:
        font = load_font(size)
        gap = max(24, font.size // 6)
        widths = []
        heights = []
        for word in words:
            _, _, w, h = measure(draw, word, font)
            widths.append(w)
            heights.append(h)
        line_w = sum(widths) + gap * (len(words) - 1)
        line_h = max(heights) if heights else 0
        if line_w <= RIGHT_ZONE_W and line_h <= RIGHT_ZONE_H:
            return font
        size -= 18 if size > 220 else 8
    return load_font(72)


def run(headline: str, variant: str, out_path: Path) -> int:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    words = [part for part in headline.upper().split()[:3] if part]
    if not words:
        words = ["AI"]

    font = fit_font(words, start_size=520 if len(words) <= 2 else 470)
    stroke_w = max(12, font.size // 14)
    angle = 7.0 if variant == "A" else 10.0

    colors = [(255, 255, 255, 255)] + [(255, 214, 0, 255)] * 2
    line = render_line(words, font, colors, stroke_w)
    rotated = line.rotate(-angle, expand=True, resample=Image.Resampling.BICUBIC)

    canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    x = RIGHT_ZONE_X
    y = RIGHT_ZONE_Y

    bbox = rotated.getbbox()
    if bbox:
        rotated = rotated.crop(bbox)

    if x + rotated.width > CANVAS_W - 40:
        x = CANVAS_W - rotated.width - 40
    if y + rotated.height > RIGHT_ZONE_Y + RIGHT_ZONE_H:
        y = RIGHT_ZONE_Y + RIGHT_ZONE_H - rotated.height

    canvas.alpha_composite(rotated, (max(0, x), max(0, y)))
    canvas.save(out_path, format="PNG")
    print(f"[Layer 4] Typography saved -> {out_path}", flush=True)
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: layer_4_text.py <headline> <variant> <out_path>")
        sys.exit(1)
    sys.exit(run(sys.argv[1], sys.argv[2].upper(), Path(sys.argv[3])))
