#!/usr/bin/env python3
from __future__ import annotations

import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


CANVAS = 900


def hex_points(
    cx: float, cy: float, radius: float, rotation_deg: float = 0.0
) -> list[tuple[float, float]]:
    points = []
    rot = math.radians(rotation_deg)
    for i in range(6):
        angle = rot + math.radians(60 * i - 30)
        points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    return points


def glow_hex(
    draw: ImageDraw.ImageDraw,
    cx: int,
    cy: int,
    radius: int,
    fill: tuple,
    outline: tuple,
    width: int = 5,
) -> None:
    draw.polygon(hex_points(cx, cy, radius), fill=fill, outline=outline)
    draw.polygon(hex_points(cx, cy, radius - 12), outline=outline, width=width)


def node_cluster_A(img: Image.Image, draw: ImageDraw.ImageDraw) -> None:
    cx, cy = CANVAS // 2, CANVAS // 2

    # Core node and orbiting agents create a clean "one vs many" visual.
    glow_hex(draw, cx, cy, 130, (10, 28, 18, 235), (70, 255, 120, 255), width=8)
    glow_hex(draw, cx, cy, 92, (0, 0, 0, 0), (170, 255, 210, 255), width=5)

    orbit = [
        (-155, -25, 62),
        (-105, -135, 48),
        (10, -165, 58),
        (135, -110, 46),
        (165, 28, 58),
        (100, 140, 48),
        (-18, 168, 62),
        (-140, 120, 50),
    ]

    for ox, oy, r in orbit:
        px, py = cx + ox, cy + oy
        draw.line([(cx, cy), (px, py)], fill=(90, 255, 140, 180), width=8)
        draw.line([(cx, cy), (px, py)], fill=(200, 255, 220, 220), width=3)
        glow_hex(draw, px, py, r, (10, 22, 14, 210), (60, 255, 120, 255), width=4)

    # Small tertiary nodes add complexity without clutter.
    for angle_deg, dist in [(15, 250), (70, 260), (135, 240), (210, 255), (300, 245)]:
        ang = math.radians(angle_deg)
        px = int(cx + math.cos(ang) * dist)
        py = int(cy + math.sin(ang) * dist)
        draw.line([(cx, cy), (px, py)], fill=(50, 220, 110, 120), width=4)
        draw.ellipse(
            [px - 18, py - 18, px + 18, py + 18],
            fill=(25, 255, 76, 180),
            outline=(220, 255, 230, 240),
            width=2,
        )


def node_cluster_B(img: Image.Image, draw: ImageDraw.ImageDraw) -> None:
    cx, cy = CANVAS // 2, CANVAS // 2

    # Variant B is more chaotic and explosive.
    for radius in range(250, 0, -24):
        alpha = int((250 - radius) * 0.45)
        draw.ellipse(
            [cx - radius, cy - radius, cx + radius, cy + radius],
            outline=(255, 214, 0, min(120, alpha)),
            width=4,
        )

    glow_hex(draw, cx, cy, 142, (28, 12, 0, 235), (255, 214, 0, 255), width=8)
    glow_hex(draw, cx, cy, 94, (0, 0, 0, 0), (255, 244, 170, 255), width=5)

    orbit = [
        (-165, -25, 58),
        (-95, -145, 48),
        (20, -180, 56),
        (150, -110, 46),
        (190, 18, 56),
        (110, 150, 48),
        (-25, 175, 60),
        (-160, 122, 50),
    ]

    for index, (ox, oy, r) in enumerate(orbit):
        px, py = cx + ox, cy + oy
        draw.line([(cx, cy), (px, py)], fill=(255, 214, 0, 160), width=9)
        draw.line([(cx, cy), (px, py)], fill=(255, 250, 200, 220), width=3)
        glow_hex(draw, px, py, r, (20, 8, 0, 220), (255, 214, 0, 255), width=4)
        if index % 2 == 0:
            draw.line(
                [(px - 30, py - 10), (px + 30, py + 20)],
                fill=(255, 120, 0, 180),
                width=4,
            )
            draw.line(
                [(px - 25, py + 15), (px + 25, py - 25)],
                fill=(255, 230, 120, 180),
                width=3,
            )

    sparks = [
        (cx - 260, cy - 155),
        (cx + 230, cy - 170),
        (cx - 240, cy + 180),
        (cx + 215, cy + 170),
        (cx + 10, cy - 255),
    ]
    for px, py in sparks:
        draw.ellipse([px - 10, py - 10, px + 10, py + 10], fill=(255, 214, 0, 255))
        draw.line([(px - 30, py), (px + 30, py)], fill=(255, 214, 0, 140), width=3)
        draw.line([(px, py - 30), (px, py + 30)], fill=(255, 214, 0, 140), width=3)


def run(variant: str, out_path: Path) -> int:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    print(
        f"[Layer 2] Generating agent-node object ({variant}) -> {out_path}", flush=True
    )

    img = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if variant == "B":
        node_cluster_B(img, draw)
    else:
        node_cluster_A(img, draw)

    glow = img.filter(ImageFilter.GaussianBlur(14))
    final = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    final.alpha_composite(glow)
    final.alpha_composite(img)

    final.save(out_path, format="PNG")
    print(
        f"[Layer 2] Saved {out_path} ({out_path.stat().st_size // 1024}KB)", flush=True
    )
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: layer_2_object_local.py <A|B> <out_path>")
        sys.exit(1)
    sys.exit(run(sys.argv[1].upper(), Path(sys.argv[2])))
