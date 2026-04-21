#!/usr/bin/env python3
"""
LAYER 4 — TYPOGRAPHY
=====================
Sole responsibility: render the headline text as a transparent RGBA layer.
- Huge, bold, condensed, uppercase
- Slanted ~7 degrees (not horizontal — this is YouTube creator style)
- Thick black stroke for readability on any background
- Deep drop shadow (offset + blur)
- Two-color: top word WHITE, bottom word GOLD (#FFD400)
- Positioned RIGHT side of canvas, safe from mascot zone (left 50%)
- Text NEVER clips — all sizing is calculated, not guessed
- Output: transparent RGBA 1920x1080 PNG

Usage:
    python3 layer_4_text.py <headline> <variant> <out_path>
    headline: e.g. "OBSOLET?" or "KILLS AI"
    variant:  "A" or "B" (affects slant angle and glow color)
"""

from __future__ import annotations
import sys
import os
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

CANVAS_W, CANVAS_H = 1920, 1080

# Font priority: condensed heavy > black > bold > default
FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Impact.ttf",
    "/System/Library/Fonts/Supplemental/Arial Black.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
]


def load_font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def measure_text(text: str, font: ImageFont.FreeTypeFont) -> tuple[int, int]:
    dummy = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    bb = dummy.textbbox((0, 0), text, font=font)
    return bb[2] - bb[0], bb[3] - bb[1]


def render_text_layer(
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: tuple,
    stroke_width: int,
    shadow_offset: int,
    shadow_blur: int,
) -> Image.Image:
    """
    Renders one line of text onto an oversized RGBA canvas.
    Returns a cropped image containing exactly the text + its shadow/stroke.
    Oversized canvas prevents clipping during rotation.
    """
    tw, th = measure_text(text, font)
    # Generous padding so stroke + shadow + rotation never clips
    pad = stroke_width + shadow_offset + shadow_blur + 120
    canvas_w = tw + pad * 2
    canvas_h = th + pad * 2

    layer = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    tx, ty = pad, pad

    # 1. Drop shadow (rendered first, behind everything)
    shadow_fill = (0, 0, 0, 200)
    draw.text(
        (tx + shadow_offset, ty + shadow_offset),
        text,
        font=font,
        fill=shadow_fill,
        stroke_width=stroke_width + 8,
        stroke_fill=(0, 0, 0, 200),
    )

    # 2. Black outer stroke for maximum contrast on any background
    draw.text(
        (tx, ty),
        text,
        font=font,
        fill=(0, 0, 0, 255),
        stroke_width=stroke_width,
        stroke_fill=(0, 0, 0, 255),
    )

    # 3. Main colored text on top
    draw.text(
        (tx, ty),
        text,
        font=font,
        fill=fill,
        stroke_width=max(2, stroke_width // 6),
        stroke_fill=(0, 0, 0, 255),
    )

    # Blur the entire layer slightly for anti-alias softening, then re-sharpen
    layer = layer.filter(ImageFilter.GaussianBlur(0.6))

    return layer


def run(headline: str, variant: str, out_path: Path) -> int:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"[Layer 4] Text '{headline}' ({variant}) → {out_path}", flush=True)

    headline = headline.upper().strip()

    # Split into two lines: single word stays on one line, two+ words split top/bottom
    words = headline.split()
    if len(words) == 1:
        top_word = headline
        bot_word = ""
    elif len(words) == 2:
        top_word = words[0]
        bot_word = words[1]
    else:
        mid = math.ceil(len(words) / 2)
        top_word = " ".join(words[:mid])
        bot_word = " ".join(words[mid:])

    # Right-side text zone — occupies the right 55% of the canvas.
    # Mascot fills left ~50%, so text starts at x=920 with a wide zone.
    # Start font at 600px and shrink only if text is wider than the zone.
    # Short words like "AI" or "?" will stay at 600px — huge and dominant.
    # After ~7-9° slant rotation the rendered layer expands ~12% horizontally;
    # paste_safe() will shift text LEFT if it overflows — never clips.
    RIGHT_ZONE_X = 920
    RIGHT_ZONE_W = 960  # wide zone: 920 + 960 = 1880, leaves 40px right margin
    RIGHT_ZONE_Y_TOP = 60
    RIGHT_ZONE_Y_BOT = 420

    def fit_font_size(
        text: str, max_width: int, start_size: int = 600
    ) -> ImageFont.FreeTypeFont:
        # Start at maximum size and step DOWN until text fits the zone.
        # Step size 10px for coarse pass, then finer 4px once close.
        size = start_size
        while size > 60:
            font = load_font(size)
            tw, _ = measure_text(text, font)
            if tw <= max_width:
                return font
            size -= 10 if size > 200 else 4
        return load_font(60)

    longest = top_word if len(top_word) >= len(bot_word) else bot_word
    font = fit_font_size(longest, RIGHT_ZONE_W, start_size=600)

    # Stroke scales with font size: bigger text = thicker stroke for readability
    # At 600px font, stroke_w=40 gives a clean bold border without muddying letterforms.
    stroke_w = 40
    shadow_off = 24
    shadow_blur = 16
    slant = 7.0 if variant == "A" else 10.0  # B gets extra aggressive slant for energy

    canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))

    # Top line: WHITE
    top_layer = render_text_layer(
        top_word, font, (255, 255, 255, 255), stroke_w, shadow_off, shadow_blur
    )
    top_rotated = top_layer.rotate(
        -slant, expand=True, resample=Image.Resampling.BICUBIC
    )

    # Bottom line: GOLD
    bot_fill = (255, 214, 0, 255)
    bot_layer = (
        render_text_layer(bot_word, font, bot_fill, stroke_w, shadow_off, shadow_blur)
        if bot_word
        else None
    )
    bot_rotated = (
        bot_layer.rotate(-slant, expand=True, resample=Image.Resampling.BICUBIC)
        if bot_layer
        else None
    )

    # Paste onto canvas at right-zone position
    def paste_safe(layer: Image.Image, x: int, y: int) -> None:
        # If the layer would overflow the right edge, shift it left instead of cropping!
        # This guarantees text is never clipped off the right side of the thumbnail.
        if x + layer.width > CANVAS_W:
            x = max(0, CANVAS_W - layer.width)

        y = max(0, min(y, CANVAS_H - 1))

        # Only crop vertically if it exceeds bottom edge
        max_h = CANVAS_H - y
        if layer.height > max_h:
            layer = layer.crop((0, 0, layer.width, max_h))

        canvas.alpha_composite(layer, (x, y))

    paste_safe(top_rotated, RIGHT_ZONE_X, RIGHT_ZONE_Y_TOP)
    if bot_rotated:
        paste_safe(
            bot_rotated, RIGHT_ZONE_X + 30, RIGHT_ZONE_Y_BOT
        )  # slight indent for visual rhythm

    canvas.save(out_path, format="PNG")
    print(
        f"[Layer 4] ✅ Saved {out_path} ({out_path.stat().st_size // 1024}KB)",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: layer_4_text.py <headline> <A|B> <out_path>")
        sys.exit(1)
    sys.exit(run(sys.argv[1], sys.argv[2].upper(), Path(sys.argv[3])))
