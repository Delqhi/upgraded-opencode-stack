#!/usr/bin/env python3
"""
LAYER 1 — BACKGROUND (PROCEDURAL — NO AI, NO API)
==================================================
Responsibility: Generate ONLY the dark atmospheric background using pure PIL.
- No objects, no characters, no text, no faces
- Pure cinematic dark studio atmosphere with colored lighting
- Full 1920x1080 canvas, left side slightly darker (mascot will go there)
- Output: RGBA PNG saved to outputs/layers/layer_1_background.png

WHY PROCEDURAL? The user mandates: "niemals generative API oder Google Gemini API".
We only use Antigravity plugin for LLM tasks. For images, we generate locally with PIL.
This is faster, free, and 100% under our control.

Usage:
    python3 layer_1_background.py <variant> <topic> <out_path>
    variant: "A" (minimal/clean) or "B" (dramatic/explosive)
"""

from __future__ import annotations
import sys
import random
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance


CANVAS_W, CANVAS_H = 1920, 1080


def draw_cloud_noise(
    draw: ImageDraw.ImageDraw, w: int, h: int, base_color: tuple, density: float = 0.3
) -> None:
    """Draw soft cloud-like noise patches with Gaussian blur for atmospheric fog."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # Generate random blobs
    for _ in range(int(800 * density)):
        x = random.randint(0, w)
        y = random.randint(0, h)
        r = random.randint(60, 200)
        a = random.randint(30, 120)
        col = (*base_color[:3], a)
        d.ellipse([x - r, y - r, x + r, y + r], fill=col)
    img = img.filter(ImageFilter.GaussianBlur(random.randint(40, 80)))
    return img


def draw_rays(
    draw: ImageDraw.ImageDraw, w: int, h: int, color: tuple, count: int = 8
) -> None:
    """Draw subtle light rays from a source point (usually top-right)."""
    rays = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(rays)
    src_x = w - random.randint(100, 300)
    src_y = -random.randint(50, 200)  # above canvas
    for i in range(count):
        angle = math.radians(random.randint(70, 110))
        length = random.randint(h, int(h * 1.5))
        end_x = src_x + math.cos(angle) * length
        end_y = src_y + math.sin(angle) * length
        # Gradient-like thick line
        for thickness in range(8, 0, -2):
            a = int(20 * (thickness / 8))
            d.line([src_x, src_y, end_x, end_y], fill=(*color[:3], a), width=thickness)
    return rays.filter(ImageFilter.GaussianBlur(20))


def draw_particles(
    draw: ImageDraw.ImageDraw, w: int, h: int, color: tuple, count: int = 100
) -> None:
    """Draw small glowing particles/sparks scattered around."""
    particles = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(particles)
    for _ in range(count):
        x = random.randint(0, w)
        y = random.randint(0, h)
        r = random.randint(2, 7)
        a = random.randint(80, 200)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(*color[:3], a))
    return particles.filter(ImageFilter.GaussianBlur(1))


def build_background_A() -> Image.Image:
    """Variant A: clean, minimal, mysterious."""
    # Base: deep black with very slight green tint
    base = Image.new("RGBA", (CANVAS_W, CANVAS_H), (5, 6, 8, 255))
    overlay = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))

    # Subtle green fog concentrated on the right side
    fog = draw_cloud_noise(None, CANVAS_W, CANVAS_H, (25, 255, 76, 0), density=0.25)
    # Mask to keep left side darker
    mask = Image.new("L", (CANVAS_W, CANVAS_H), 0)
    dm = ImageDraw.Draw(mask)
    # Gradient mask: left (dark) → right (visible fog)
    for x in range(CANVAS_W):
        strength = int(min(1.0, (x - 200) / (CANVAS_W - 600)) * 255)
        dm.line([(x, 0), (x, CANVAS_H)], fill=max(0, strength))
    fog.putalpha(mask)
    overlay.alpha_composite(fog)

    # Faint light rays from top-right
    rays = draw_rays(None, CANVAS_W, CANVAS_H, (25, 255, 76, 0))
    overlay.alpha_composite(rays)

    # Very subtle lens flare streaks
    flare = draw_cloud_noise(None, CANVAS_W, CANVAS_H, (25, 255, 76, 0), density=0.08)
    overlay.alpha_composite(flare)

    base.alpha_composite(overlay)
    return base


def build_background_B() -> Image.Image:
    """Variant B: explosive, dramatic, high energy."""
    base = Image.new("RGBA", (CANVAS_W, CANVAS_H), (5, 6, 8, 255))
    overlay = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))

    # Intense energy burst from right-center
    cx, cy = CANVAS_W * 0.75, CANVAS_H * 0.5

    # Multi-layer burst rings
    for r in range(400, 0, -40):
        alpha = int((400 - r) * 0.4)
        ring = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
        d = ImageDraw.Draw(ring)
        # Outer green, inner gold
        col = (255, 214, 0, alpha) if r < 150 else (25, 255, 76, alpha)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col, width=12)
        ring = ring.filter(ImageFilter.GaussianBlur(15))
        overlay.alpha_composite(ring)

    # Volumetric light beams
    beams = draw_rays(None, CANVAS_W, CANVAS_H, (25, 255, 76, 0), count=12)
    overlay.alpha_composite(beams)

    # Green + gold particles
    particles_green = draw_particles(
        None, CANVAS_W, CANVAS_H, (25, 255, 76, 0), count=120
    )
    overlay.alpha_composite(particles_green)
    particles_gold = draw_particles(
        None, CANVAS_W, CANVAS_H, (255, 214, 0, 0), count=60
    )
    overlay.alpha_composite(particles_gold)

    # Dense smoke trails (more aggressive)
    smoke = draw_cloud_noise(None, CANVAS_W, CANVAS_H, (25, 255, 76, 0), density=0.6)
    overlay.alpha_composite(smoke)

    base.alpha_composite(overlay)

    # Add color contrast boost
    enhancer = ImageEnhance.Contrast(base)
    base = enhancer.enhance(1.3)
    return base


def run(variant: str, topic: str, out_path: Path) -> int:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"[Layer 1] Background ({variant}) → {out_path}", flush=True)

    variant = variant.upper()
    if variant == "A":
        img = build_background_A()
    elif variant == "B":
        img = build_background_B()
    else:
        print(f"[Layer 1] ERROR: unknown variant '{variant}'", flush=True)
        return 1

    img.save(out_path, format="PNG")
    print(
        f"[Layer 1] ✅ Saved {out_path} ({out_path.stat().st_size // 1024}KB)",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: layer_1_background.py <A|B> <topic> <out_path>")
        sys.exit(1)
    sys.exit(run(sys.argv[1].upper(), sys.argv[2], Path(sys.argv[3])))
