#!/usr/bin/env python3
"""
LAYER 2 — MAIN OBJECT
======================
Responsibility: Generate ONLY the single hero object for the right side.
- For topic about AI/money: a glowing laptop with profit chart, or floating dollar bills
- Output is RGBA PNG with transparent background (object isolated, right-half positioned)
- The object will be composited over the background by Layer 5

Strategy:
  AI generates the object on white/solid bg → we remove bg via chroma/alpha
  OR we ask AI to generate on pure black and use screen/lighten blend mode in compositor.
  We use pure-black bg approach (easier, no green-screen issues with complex objects).

Usage:
    python3 layer_2_object.py <variant> <topic> <object_type> <out_path>
    variant:     "A" (subtle/clean) or "B" (dramatic/explosive)
    object_type: "laptop_chart" | "money_burst" | "robot_death" | "dollar_rain"
"""

from __future__ import annotations
import sys
import subprocess
from pathlib import Path
from PIL import Image, ImageFilter, ImageEnhance

ROUTER = Path.home() / ".config/opencode/skills/imagegen/scripts/gemini_image_router.py"

OBJECT_PROMPTS = {
    "laptop_chart": {
        "A": (
            "A single sleek glowing laptop computer on pure black background, "
            "screen shows a rising green neon profit chart with upward trend line, "
            "subtle green light emitting from screen illuminating the keyboard, "
            "cinematic product photography, isolated object on solid black, "
            "no background environment, no text, no people, no reflections, "
            "high contrast, premium tech aesthetic, right-side placement"
        ),
        "B": (
            "A glowing laptop computer exploding with green neon energy on pure black background, "
            "screen showing a skyrocketing green profit chart, gold dollar coins flying out, "
            "intense green light rays emanating from the device, dramatic cinematic lighting, "
            "isolated object on solid black background, no people, no text, "
            "explosive tech aesthetic, maximum contrast"
        ),
    },
    "money_burst": {
        "A": (
            "A neat stack of dollar bills with subtle green neon glow on pure black background, "
            "clean minimal money stack, slight gold shimmer, soft green rim light, "
            "isolated on solid black, no people, no text overlay, premium financial aesthetic"
        ),
        "B": (
            "An explosion of dollar bills and gold coins bursting outward on pure black background, "
            "money flying in all directions, intense neon green and gold light beams, "
            "dramatic money explosion, cinematic lighting, isolated on solid black, "
            "no people, no characters, maximum energy and motion blur"
        ),
    },
    "robot_death": {
        "A": (
            "A single cracked broken robot head on pure black background, "
            "a dramatic X crossing its eye, subtle red warning light, "
            "clean isolated object, cinematic lighting, solid black background, no text"
        ),
        "B": (
            "A dramatic shattered robot exploding into pieces on pure black background, "
            "sparks flying, red and green warning lights, dramatic destruction scene, "
            "cinematic lighting, isolated on solid black, no people, maximum dramatic impact"
        ),
    },
    "dollar_rain": {
        "A": (
            "A few dollar bills floating gracefully on pure black background, "
            "subtle green neon glow around bills, clean minimal composition, "
            "soft light rays, isolated on black, no people, premium aesthetic"
        ),
        "B": (
            "Dozens of dollar bills raining down with green neon energy on pure black background, "
            "gold coins scattering, intense wealth explosion, dramatic cinematic lighting, "
            "isolated on black background, no people, maximum visual impact"
        ),
    },
}


def remove_black_bg(img: Image.Image, threshold: int = 30) -> Image.Image:
    """
    Convert near-black pixels to transparent.
    Used because AI generates objects on pure black — we screen-blend in compositor
    but also want a proper alpha channel for fine compositing control.
    threshold=30 keeps dark shadows partially opaque (natural falloff).
    """
    img = img.convert("RGBA")
    pixels = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            brightness = (r + g + b) // 3
            if brightness < threshold:
                pixels[x, y] = (r, g, b, 0)
            elif brightness < 80:
                # Partial transparency for shadows — smooth falloff
                alpha = int((brightness - threshold) / (80 - threshold) * 255)
                pixels[x, y] = (r, g, b, alpha)
    return img


def run(variant: str, topic: str, object_type: str, out_path: Path) -> int:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    prompts = OBJECT_PROMPTS.get(object_type, OBJECT_PROMPTS["laptop_chart"])
    prompt = prompts.get(variant, prompts["A"])

    print(f"[Layer 2] Object '{object_type}' ({variant}) → {out_path}", flush=True)

    result = subprocess.run(
        [
            "python3",
            str(ROUTER),
            "generate",
            "--prompt",
            prompt,
            "--use-case",
            "stylized-concept",
            "--size",
            "1024x1024",
            "--out",
            str(out_path.with_suffix(".tmp.png")),
            "--force",
            "--no-augment",
        ],
        capture_output=True,
        text=True,
    )

    candidates = sorted(
        [p for p in out_path.parent.glob(f"{out_path.stem}.tmp*") if p.is_file()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        print(f"[Layer 2] ERROR: no output produced\n{result.stderr}", flush=True)
        return 1

    src = candidates[0]
    try:
        img = Image.open(src).convert("RGBA")

        # Remove pure-black background to get isolated object with alpha
        img = remove_black_bg(img, threshold=25)

        # Scale object to fit right-half of 1920x1080 canvas
        # Target: max ~700x700 px, will be placed right-center by compositor
        img.thumbnail((700, 700), Image.Resampling.LANCZOS)

        # Add subtle glow bloom around bright areas
        glow = img.filter(ImageFilter.GaussianBlur(12))
        glow = ImageEnhance.Brightness(glow).enhance(1.4)
        base = Image.new("RGBA", img.size, (0, 0, 0, 0))
        base.alpha_composite(glow)
        base.alpha_composite(img)

        base.save(out_path, format="PNG")
        src.unlink(missing_ok=True)
        print(
            f"[Layer 2] ✅ Saved {out_path} ({out_path.stat().st_size // 1024}KB)",
            flush=True,
        )
        return 0
    except Exception as e:
        print(f"[Layer 2] ERROR: {e}", flush=True)
        return 1


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: layer_2_object.py <A|B> <topic> <object_type> <out_path>")
        sys.exit(1)
    sys.exit(run(sys.argv[1].upper(), sys.argv[2], sys.argv[3], Path(sys.argv[4])))
