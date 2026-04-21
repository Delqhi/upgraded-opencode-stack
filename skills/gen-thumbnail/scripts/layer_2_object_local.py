#!/usr/bin/env python3
"""
LAYER 2b — PROCEDURAL OBJECT (PIL-only, no AI)
================================================
Fallback for when NVIDIA/AI image generation is unavailable.
Draws a high-quality glowing object using pure PIL geometry.

Produces a transparent RGBA PNG at 700x700px with:
  - Variant A: clean glowing laptop with profit chart
  - Variant B: explosive money burst with coins

This is a LOCAL-ONLY layer — no network calls, instant execution.

Usage:
    python3 layer_2_object_local.py <variant> <out_path>
"""

from __future__ import annotations
import sys
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import os

CANVAS = 700


def load_font(size: int) -> ImageFont.FreeTypeFont:
    for p in [
        "/System/Library/Fonts/Supplemental/Impact.ttf",
        "/System/Library/Fonts/Supplemental/Arial Black.ttf",
        "/System/Library/Fonts/Arial.ttf",
    ]:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except:
                pass
    return ImageFont.load_default()


def draw_laptop_A(draw: ImageDraw.ImageDraw, img: Image.Image) -> None:
    """Clean glowing laptop with rising profit chart — Variant A — BRIGHT & VIVID."""
    cx, cy = CANVAS // 2, CANVAS // 2

    # Laptop body — bright neon green glow, much larger and more prominent
    body_left, body_top = cx - 160, cy - 90
    body_right, body_bottom = cx + 160, cy + 120

    # INTENSE glow behind laptop — multiple layers for heavy bloom effect
    for spread in range(60, 0, -6):
        alpha = int((60 - spread) * 6)
        # Color: bright electric green
        col = (60, 255, 100, alpha)
        draw.rounded_rectangle(
            [
                body_left - spread,
                body_top - spread,
                body_right + spread,
                body_bottom + spread,
            ],
            radius=25,
            outline=col,
            width=4,
        )

    # Laptop lid (screen) — bright neon green glass look
    draw.rounded_rectangle(
        [body_left, body_top, body_right, cy + 15],
        radius=12,
        fill=(10, 30, 10, 255),
        outline=(100, 255, 150, 255),
        width=6,
    )

    # Screen content — profit chart — very bright neon green on deep black
    screen_l, screen_t, screen_r, screen_b = (
        body_left + 12,
        body_top + 10,
        body_right - 12,
        cy + 5,
    )

    # Chart background — deep black for maximum contrast
    draw.rectangle([screen_l, screen_t, screen_r, screen_b], fill=(0, 20, 0, 255))

    # Rising chart line — thick glowing neon
    chart_pts = [
        (screen_l + 15, screen_b - 15),
        (screen_l + 70, screen_b - 50),
        (screen_l + 125, screen_b - 40),
        (screen_l + 180, screen_b - 90),
        (screen_l + 235, screen_b - 110),
        (screen_r - 15, screen_b - 150),
    ]
    # Multiple passes for glow effect
    draw.line(chart_pts, fill=(80, 255, 120, 180), width=10)  # outer glow
    draw.line(chart_pts, fill=(150, 255, 200, 255), width=6)  # mid glow
    draw.line(chart_pts, fill=(200, 255, 220, 255), width=3)  # core line

    # Chart area fill under line — bright semi-transparent green
    for i, pt in enumerate(chart_pts[:-1]):
        x1, y1 = pt
        x2, y2 = chart_pts[i + 1]
        alpha = 150
        draw.polygon(
            [(x1, y1), (x2, y2), (x2, screen_b), (x1, screen_b)],
            fill=(80, 255, 120, alpha),
        )

    # Laptop base — bright green neon border
    draw.rounded_rectangle(
        [body_left + 8, cy + 15, body_right - 8, body_bottom],
        radius=8,
        fill=(15, 40, 15, 255),
        outline=(120, 255, 180, 255),
        width=6,
    )

    # HUGE dollar sign floating top-right — intense gold with multi-layer glow
    dollar_y = body_top - 70
    # Outer glow layers
    for offset in [
        (5, 5),
        (-5, -5),
        (5, -5),
        (-5, 5),
        (3, 0),
        (-3, 0),
        (0, 3),
        (0, -3),
    ]:
        draw.text(
            (body_right - 30 + offset[0], dollar_y + offset[1]),
            "$",
            font=load_font(80),
            fill=(255, 240, 50, 180),
            stroke_width=3,
            stroke_fill=(200, 255, 0, 200),
            anchor="mm",
        )
    # Core bright gold text
    draw.text(
        (body_right - 30, dollar_y),
        "$",
        font=load_font(80),
        fill=(255, 255, 200, 255),
        stroke_width=6,
        stroke_fill=(180, 100, 0, 255),
        anchor="mm",
    )


def draw_money_burst_B(draw: ImageDraw.ImageDraw, img: Image.Image) -> None:
    """Explosive money burst with coins — Variant B."""
    cx, cy = CANVAS // 2, CANVAS // 2

    # Central glow burst
    for r in range(180, 0, -18):
        alpha = int((180 - r) * 1.1)
        c = (25, 255, 76, alpha)
        draw.ellipse(
            [cx - r, cy - r, cx + r, cy + r], fill=(0, 0, 0, 0), outline=c, width=3
        )

    # Radiate dollar bills as rectangles at angles
    num_bills = 8
    for i in range(num_bills):
        angle = (i / num_bills) * 2 * math.pi + 0.3
        dist = 120 + (i % 3) * 40
        bx = int(cx + math.cos(angle) * dist)
        by = int(cy + math.sin(angle) * dist)

        # Draw a small rotated bill shape
        bill_w, bill_h = 100, 50
        corners = [
            (-bill_w // 2, -bill_h // 2),
            (bill_w // 2, -bill_h // 2),
            (bill_w // 2, bill_h // 2),
            (-bill_w // 2, bill_h // 2),
        ]
        rot_angle = angle + math.pi / 6
        rotated = [
            (
                bx + int(x * math.cos(rot_angle) - y * math.sin(rot_angle)),
                by + int(x * math.sin(rot_angle) + y * math.cos(rot_angle)),
            )
            for x, y in corners
        ]
        draw.polygon(
            rotated, fill=(20, 100, 40, 200), outline=(25, 255, 76, 230), width=2
        )
        # $ text on bill
        draw.text(
            (bx, by),
            "$",
            font=load_font(28),
            fill=(255, 255, 200, 230),
            stroke_width=1,
            stroke_fill=(0, 60, 0, 255),
            anchor="mm",
        )

    # Gold coins
    coin_positions = [
        (cx + 60, cy - 80),
        (cx - 90, cy + 60),
        (cx + 130, cy + 40),
        (cx - 50, cy - 120),
        (cx + 40, cy + 120),
    ]
    for px, py in coin_positions:
        r = 28
        draw.ellipse(
            [px - r, py - r, px + r, py + r],
            fill=(200, 160, 0, 220),
            outline=(255, 214, 0, 255),
            width=3,
        )
        draw.text(
            (px, py),
            "$",
            font=load_font(22),
            fill=(255, 255, 100, 255),
            stroke_width=1,
            stroke_fill=(120, 80, 0, 255),
            anchor="mm",
        )

    # Central bright core
    for r in (55, 40, 25, 12):
        alpha = int((55 - r) * 5.5)
        draw.ellipse(
            [cx - r, cy - r, cx + r, cy + r], fill=(25, 255, 76, min(255, alpha))
        )


def run(variant: str, out_path: Path) -> int:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"[Layer 2 local] Procedural object ({variant}) → {out_path}", flush=True)

    img = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if variant == "B":
        draw_money_burst_B(draw, img)
    else:
        draw_laptop_A(draw, img)

    # Soft glow bloom over the whole object
    glow = img.filter(ImageFilter.GaussianBlur(8))
    final = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    final.alpha_composite(glow)
    final.alpha_composite(img)

    final.save(out_path, format="PNG")
    print(
        f"[Layer 2 local] ✅ Saved {out_path} ({out_path.stat().st_size // 1024}KB)",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: layer_2_object_local.py <A|B> <out_path>")
        sys.exit(1)
    sys.exit(run(sys.argv[1].upper(), Path(sys.argv[2])))
