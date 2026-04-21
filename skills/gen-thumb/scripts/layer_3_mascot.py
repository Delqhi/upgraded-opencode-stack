#!/usr/bin/env python3
"""
LAYER 3 — MASCOT WITH EXPRESSION MODIFICATION
===============================================
Takes the real OpenSIN mascot PNG and MODIFIES the facial expression
to match the requested emotion. This is the CRITICAL layer that the
user demanded: "immer das selbe Maskottchen, aber der Gesichtsausdruck
verändert sich" — same mascot, different face every thumbnail.

MASCOT ANATOMY (from pixel analysis of assets/mascot.png 1024x1024):
  - White sphere body (RGBA ~231,230,232,255)
  - Green superhero mask band: y 298–604
  - Left eye center:  (333, 454), box (203,358)–(429,490)
  - Right eye center: (688, 435), box (578,358)–(821,490)
  - Mouth region: box (211,491)–(919,708), center (565,599)
  - Sphere center: (511, 491), radius ~421
  - Sphere surface white: RGBA (231, 230, 232, 255)

EXPRESSION MODES:
  - shocked:  Big O mouth, wide eyes, raised brows → "OMG WTF" energy
  - excited:  Wide grin, squinted happy eyes → "LET'S GO" energy
  - angry:    Downward frown, narrowed eyes → "I'M DONE" energy
  - scared:   Trembling O mouth, huge eyes → "OH NO" energy
  - smug:     Asymmetric smirk, half-closed eyes → "I told you so"

WORKFLOW:
  1. Load mascot PNG
  2. Locate mouth (black pixels below center y)
  3. Erase existing mouth by painting over with sphere surface color
  4. Draw new mouth shape for the requested emotion
  5. Modify eye shapes (enlarge, narrow, squint)
  6. Apply color/glow treatment per variant
  7. Scale to 110% canvas height, position left-dominant
  8. Output transparent RGBA layer at 1920×1080

Usage:
    python3 layer_3_mascot.py <variant> <emotion> <mascot_src> <out_path>
    variant: "A" or "B"
    emotion: shocked | excited | angry | scared | smug
"""

from __future__ import annotations
import sys
import math
from pathlib import Path
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw
import numpy as np

# ============================================================================
# CANVAS DIMENSIONS (standard YouTube thumbnail)
# ============================================================================
CANVAS_W, CANVAS_H = 1920, 1080

# ============================================================================
# MASCOT PIXEL CONSTANTS (measured from actual mascot.png analysis)
# These are coordinates in the ORIGINAL 1024×1024 mascot image.
# All expression drawing happens at this scale BEFORE resizing to canvas.
# ============================================================================
MASCOT_SIZE = 1024  # Original mascot image is 1024×1024
SPHERE_CENTER = (511, 491)  # Center of the white sphere
SPHERE_RADIUS = 421  # Approximate radius of visible sphere
SPHERE_WHITE = (231, 230, 232, 255)  # The surface color of the white sphere

# Mouth region: black pixels below sphere center
MOUTH_BOX = (211, 491, 919, 708)  # left, top, right, bottom
MOUTH_CENTER = (565, 599)  # Center of existing mouth

# Eye positions in original image coordinates
LEFT_EYE_CENTER = (333, 454)  # Center of left pupil cluster
LEFT_EYE_BOX = (203, 358, 429, 490)  # Bounding box of left eye blacks
RIGHT_EYE_CENTER = (688, 435)  # Center of right pupil cluster
RIGHT_EYE_BOX = (578, 358, 821, 490)  # Bounding box of right eye blacks

# Green mask band spans y=298 to y=604
MASK_Y_TOP = 298
MASK_Y_BOT = 604


def erase_mouth(img: Image.Image) -> Image.Image:
    """
    Erase the existing mouth by painting over black mouth pixels with
    the sphere's surface color. We only touch pixels in the mouth region
    (below center y) that are black (R<60, G<60, B<60).

    This gives us a "blank face" canvas to draw new expressions onto.
    We also need to handle the subtle shading gradient on the sphere —
    instead of a flat color, we sample the actual surrounding pixels
    to create a smooth blend.
    """
    arr = np.array(img)  # shape (H, W, 4) RGBA

    # Define mouth search region with generous padding
    # The mouth box is (211,491)–(919,708) but we add padding for safety
    y_start = max(0, MOUTH_BOX[1] - 10)
    y_end = min(arr.shape[0], MOUTH_BOX[3] + 10)
    x_start = max(0, MOUTH_BOX[0] - 10)
    x_end = min(arr.shape[1], MOUTH_BOX[2] + 10)

    # Find black mouth pixels: R<80, G<80, B<80, alpha>128
    region = arr[y_start:y_end, x_start:x_end]
    r, g, b, a = region[:, :, 0], region[:, :, 1], region[:, :, 2], region[:, :, 3]
    is_black = (r < 80) & (g < 80) & (b < 80) & (a > 128)

    # For each black pixel, replace with the sphere surface color.
    # We use a distance-based shade: pixels further from center are slightly
    # darker, matching the sphere's natural 3D shading gradient.
    cy, cx = SPHERE_CENTER[1] - y_start, SPHERE_CENTER[0] - x_start

    ys, xs = np.where(is_black)
    for i in range(len(ys)):
        py, px = ys[i], xs[i]
        # Calculate distance from sphere center for shading
        dist = math.sqrt(
            (px + x_start - SPHERE_CENTER[0]) ** 2
            + (py + y_start - SPHERE_CENTER[1]) ** 2
        )
        # Shade factor: closer to center = brighter, edges = slightly darker
        shade = max(0.85, 1.0 - (dist / SPHERE_RADIUS) * 0.2)
        # Apply shaded sphere color
        region[py, px] = (
            int(SPHERE_WHITE[0] * shade),
            int(SPHERE_WHITE[1] * shade),
            int(SPHERE_WHITE[2] * shade),
            255,
        )

    arr[y_start:y_end, x_start:x_end] = region

    # Apply a tiny gaussian blur ONLY in the mouth region to smooth the edges
    # of the erased area so it doesn't look choppy
    result = Image.fromarray(arr, "RGBA")

    # Crop the mouth region, blur slightly, paste back
    mouth_crop = result.crop((x_start, y_start, x_end, y_end))
    mouth_blurred = mouth_crop.filter(ImageFilter.GaussianBlur(2.5))
    result.paste(mouth_blurred, (x_start, y_start))

    return result


def draw_expression(img: Image.Image, emotion: str) -> Image.Image:
    """
    Draw a new facial expression onto the blank-faced mascot.
    Each emotion gets a distinct mouth shape and eye modification.

    All coordinates are in the original 1024×1024 mascot space.
    The mouth is drawn as black (0,0,0,255) on the white sphere.
    """
    draw = ImageDraw.Draw(img)

    # Mouth center position (slightly right of sphere center, matching original)
    mx, my = MOUTH_CENTER

    if emotion == "shocked":
        # ============================================================
        # SHOCKED: Big open "O" mouth — the classic MrBeast expression
        # Wide open, perfectly round, conveying "WHAT?!" energy.
        # This is THE highest-CTR expression according to research.
        # ============================================================

        # Draw a big open O mouth — ellipse with black fill
        mouth_rx = 85  # horizontal radius of the O
        mouth_ry = 95  # vertical radius (slightly taller than wide)

        # Outer black ring of the mouth
        draw.ellipse(
            [mx - mouth_rx, my - mouth_ry, mx + mouth_rx, my + mouth_ry],
            fill=(0, 0, 0, 255),
            outline=(0, 0, 0, 255),
            width=8,
        )
        # Inner dark gray "throat" for depth
        inner_rx = mouth_rx - 22
        inner_ry = mouth_ry - 22
        draw.ellipse(
            [mx - inner_rx, my - inner_ry, mx + inner_rx, my + inner_ry],
            fill=(30, 10, 10, 255),
        )
        # Tiny highlight reflection on lower lip for 3D feel
        draw.ellipse(
            [mx - 15, my + mouth_ry - 18, mx + 15, my + mouth_ry - 8],
            fill=(60, 60, 60, 180),
        )

        # WIDEN the eyes — draw slightly larger black pupils over existing ones
        # Left eye: enlarge pupil downward and outward for "wide-eyed" look
        _draw_wide_eye(draw, LEFT_EYE_CENTER, radius=52)
        _draw_wide_eye(draw, RIGHT_EYE_CENTER, radius=52)

    elif emotion == "excited":
        # ============================================================
        # EXCITED: Wide upward grin — "LET'S GOOO" energy
        # Big curved smile, squinted happy eyes (anime-style joy)
        # ============================================================

        # Wide arc smile — thick curved line going UP
        smile_width = 130
        smile_y_offset = 20  # shift mouth slightly down from center

        # Draw thick curved smile using arc
        for thickness in range(18):
            y_off = my + smile_y_offset + thickness
            draw.arc(
                [mx - smile_width, y_off - 60, mx + smile_width, y_off + 60],
                start=10,
                end=170,
                fill=(0, 0, 0, 255),
                width=4,
            )

        # Add mouth corners turning up sharply for extra grin effect
        # Left corner
        draw.line(
            [
                (mx - smile_width + 10, my + smile_y_offset - 5),
                (mx - smile_width - 15, my + smile_y_offset - 35),
            ],
            fill=(0, 0, 0, 255),
            width=12,
        )
        # Right corner
        draw.line(
            [
                (mx + smile_width - 10, my + smile_y_offset - 5),
                (mx + smile_width + 15, my + smile_y_offset - 35),
            ],
            fill=(0, 0, 0, 255),
            width=12,
        )

        # Happy squinted eyes — horizontal crescents instead of round pupils
        _draw_happy_eye(draw, LEFT_EYE_CENTER)
        _draw_happy_eye(draw, RIGHT_EYE_CENTER)

    elif emotion == "angry":
        # ============================================================
        # ANGRY: Downward frown, aggressive teeth-baring
        # Narrowed eyes, furrowed brow energy
        # ============================================================

        # Angry frown: wide arc curving DOWN
        frown_width = 120
        frown_y = my + 15

        for thickness in range(16):
            draw.arc(
                [
                    mx - frown_width,
                    frown_y - 50 + thickness,
                    mx + frown_width,
                    frown_y + 50 + thickness,
                ],
                start=190,
                end=350,
                fill=(0, 0, 0, 255),
                width=5,
            )

        # Show teeth: small white rectangles in the frown opening
        teeth_y = frown_y - 8
        for tx in range(mx - 70, mx + 70, 22):
            draw.rectangle(
                [tx, teeth_y - 14, tx + 16, teeth_y + 4],
                fill=(255, 255, 255, 240),
                outline=(180, 180, 180, 200),
                width=1,
            )

        # Angry narrowed eyes — flat lines, aggressive
        _draw_angry_eye(draw, LEFT_EYE_CENTER, is_left=True)
        _draw_angry_eye(draw, RIGHT_EYE_CENTER, is_left=False)

    elif emotion == "scared":
        # ============================================================
        # SCARED: Wobbly open mouth, HUGE terrified eyes
        # Trembling energy, vulnerability
        # ============================================================

        # Wobbly/wavy O mouth — like shocked but asymmetric
        mouth_rx = 70
        mouth_ry = 80
        # Offset slightly left and down for asymmetric scared look
        sx, sy = mx - 15, my + 10

        draw.ellipse(
            [sx - mouth_rx, sy - mouth_ry, sx + mouth_rx, sy + mouth_ry],
            fill=(0, 0, 0, 255),
        )
        # Inner darkness
        draw.ellipse(
            [
                sx - mouth_rx + 20,
                sy - mouth_ry + 20,
                sx + mouth_rx - 20,
                sy + mouth_ry - 20,
            ],
            fill=(20, 5, 5, 255),
        )

        # HUGE terrified eyes — much bigger than normal
        _draw_wide_eye(draw, LEFT_EYE_CENTER, radius=62)
        _draw_wide_eye(draw, RIGHT_EYE_CENTER, radius=62)

        # Add tiny highlight dots in eyes for "glistening with fear" look
        for eye_c in [LEFT_EYE_CENTER, RIGHT_EYE_CENTER]:
            draw.ellipse(
                [eye_c[0] - 12, eye_c[1] - 18, eye_c[0], eye_c[1] - 8],
                fill=(255, 255, 255, 220),
            )

    else:  # smug (default/fallback)
        # ============================================================
        # SMUG: Asymmetric smirk, one raised brow, confident
        # The "I told you so" expression — keeps original vibe
        # ============================================================

        # Asymmetric smirk — rises on the right side
        smirk_pts = [
            (mx - 90, my + 10),
            (mx - 40, my + 15),
            (mx, my + 5),
            (mx + 50, my - 15),
            (mx + 100, my - 40),
        ]
        draw.line(smirk_pts, fill=(0, 0, 0, 255), width=14, joint="curve")

        # Slightly thickened for boldness
        smirk_pts_thick = [(x, y + 4) for x, y in smirk_pts]
        draw.line(smirk_pts_thick, fill=(0, 0, 0, 255), width=10, joint="curve")

        # Half-closed confident eyes — left normal, right slightly narrowed
        _draw_wide_eye(draw, LEFT_EYE_CENTER, radius=42)
        _draw_smug_eye(draw, RIGHT_EYE_CENTER)

    return img


def _draw_wide_eye(draw: ImageDraw.ImageDraw, center: tuple, radius: int = 48) -> None:
    """
    Draw a wide-open eye: big round black pupil.
    Used for shocked and scared expressions.
    The eye is drawn as a solid black circle at the given center.
    """
    cx, cy = center
    # Outer eye (black pupil)
    draw.ellipse(
        [cx - radius, cy - radius, cx + radius, cy + radius], fill=(0, 0, 0, 255)
    )
    # White highlight reflection — small circle in upper-left of pupil
    # This is crucial for making the eye look "alive" and not dead/flat
    hl_r = max(6, radius // 5)
    draw.ellipse(
        [
            cx - radius // 3 - hl_r,
            cy - radius // 3 - hl_r,
            cx - radius // 3 + hl_r,
            cy - radius // 3 + hl_r,
        ],
        fill=(255, 255, 255, 230),
    )


def _draw_happy_eye(draw: ImageDraw.ImageDraw, center: tuple) -> None:
    """
    Draw a happy squinted eye: upward-curved arc (anime-style happy eyes).
    Used for excited/joyful expressions.
    """
    cx, cy = center
    eye_w = 55  # half-width of the arc

    # Draw thick upward arc — the "^" or "∩" shape anime characters make when happy
    for t in range(14):
        draw.arc(
            [cx - eye_w, cy - 30 + t, cx + eye_w, cy + 30 + t],
            start=200,
            end=340,
            fill=(0, 0, 0, 255),
            width=5,
        )


def _draw_angry_eye(draw: ImageDraw.ImageDraw, center: tuple, is_left: bool) -> None:
    """
    Draw an angry narrowed eye: flat horizontal line with aggressive angle.
    The eyebrow/mask ridge implies the furrowed brow; the eye itself is
    a narrow slit with a small intense pupil visible.
    """
    cx, cy = center

    # Narrow slit eye — horizontal ellipse, very flat
    slit_w = 55
    slit_h = 18
    # Angle the slit: inner corners up, outer corners down (angry V shape)
    angle = 12 if is_left else -12

    # Draw the slit as a rotated narrow ellipse via polygon approximation
    points = []
    for deg in range(0, 360, 5):
        rad = math.radians(deg)
        x = cx + slit_w * math.cos(rad)
        y = cy + slit_h * math.sin(rad)
        # Apply rotation
        rot = math.radians(angle)
        rx = cx + (x - cx) * math.cos(rot) - (y - cy) * math.sin(rot)
        ry = cy + (x - cx) * math.sin(rot) + (y - cy) * math.cos(rot)
        points.append((rx, ry))

    draw.polygon(points, fill=(0, 0, 0, 255))

    # Small intense pupil inside the slit
    draw.ellipse(
        [cx - 10, cy - 10, cx + 10, cy + 10],
        fill=(40, 0, 0, 255),  # very dark red-black for intensity
    )


def _draw_smug_eye(draw: ImageDraw.ImageDraw, center: tuple) -> None:
    """
    Draw a half-closed smug eye: relaxed, confident, slightly droopy.
    Used for the smug/confident expression.
    """
    cx, cy = center

    # Half-closed eye: bottom half is a normal pupil circle,
    # top half is covered by an "eyelid" (sphere-colored arc)
    pupil_r = 42
    draw.ellipse(
        [cx - pupil_r, cy - pupil_r, cx + pupil_r, cy + pupil_r], fill=(0, 0, 0, 255)
    )

    # "Eyelid" — cover the top 40% with sphere color
    # This makes the eye look half-closed / relaxed
    lid_y = cy - pupil_r
    lid_h = int(pupil_r * 0.7)
    draw.chord(
        [cx - pupil_r - 5, lid_y - 10, cx + pupil_r + 5, lid_y + lid_h * 2 + 10],
        start=180,
        end=360,
        fill=SPHERE_WHITE,
    )

    # Highlight
    draw.ellipse([cx - 8, cy - 6, cx + 2, cy + 2], fill=(255, 255, 255, 200))


def build_glow(mascot: Image.Image, variant: str, emotion: str) -> Image.Image:
    """
    Build a colored glow halo around the mascot silhouette.
    The glow color changes based on variant AND emotion for visual variety:
      - Variant A: softer green glow (curiosity/calm energy)
      - Variant B: intense green+gold burst (dramatic/explosive energy)
      - Shocked/Scared: adds a rim of electric blue for urgency
      - Angry: adds red-orange rim for aggression
      - Excited: adds gold/yellow burst for positivity

    The glow is built by extracting the alpha mask, tinting it, and blurring.
    """
    alpha = mascot.split()[3]

    # Base glow colors per variant
    if variant == "B":
        glow_outer_color = (25, 255, 76, 100)  # neon green, stronger
        glow_inner_color = (255, 214, 0, 120)  # gold rim
        blur_outer, blur_inner = 60, 25
    else:
        glow_outer_color = (25, 255, 76, 75)  # softer neon green
        glow_inner_color = (25, 255, 76, 55)  # gentle green
        blur_outer, blur_inner = 40, 16

    # Emotion-based accent glow (third layer)
    emotion_colors = {
        "shocked": (50, 120, 255, 70),  # electric blue
        "excited": (255, 240, 50, 80),  # golden yellow
        "angry": (255, 60, 20, 75),  # aggressive red-orange
        "scared": (100, 50, 255, 65),  # eerie purple
        "smug": (25, 255, 76, 50),  # just more green
    }
    accent_color = emotion_colors.get(emotion, (25, 255, 76, 50))

    def make_glow_layer(blur_r: int, color: tuple) -> Image.Image:
        tinted = Image.new("RGBA", mascot.size, color)
        tinted.putalpha(alpha)
        blurred = tinted.filter(ImageFilter.GaussianBlur(blur_r))
        return blurred

    outer = make_glow_layer(blur_outer, glow_outer_color)
    inner = make_glow_layer(blur_inner, glow_inner_color)
    accent = make_glow_layer(35, accent_color)

    glow = Image.new("RGBA", mascot.size, (0, 0, 0, 0))
    glow.alpha_composite(outer)
    glow.alpha_composite(accent)
    glow.alpha_composite(inner)
    return glow


def apply_variant_treatment(
    mascot: Image.Image, variant: str, emotion: str
) -> Image.Image:
    """
    Apply variant-specific color treatment to the mascot AFTER expression is drawn.
    Variant A = clean, slightly enhanced
    Variant B = high energy, boosted contrast/saturation, slight tilt
    """
    mascot = mascot.convert("RGBA")

    if variant == "B":
        # Boost contrast and saturation for high-energy dramatic look
        mascot = ImageEnhance.Contrast(mascot).enhance(1.20)
        mascot = ImageEnhance.Color(mascot).enhance(1.30)
        # Slight rightward tilt for dynamic energy feel
        mascot = mascot.rotate(-3, expand=True, resample=Image.Resampling.BICUBIC)
    else:
        # Clean, subtle enhancement
        mascot = ImageEnhance.Color(mascot).enhance(1.08)
        mascot = ImageEnhance.Contrast(mascot).enhance(1.05)

    return mascot


def run(variant: str, emotion: str, mascot_src: Path, out_path: Path) -> int:
    """
    Main pipeline:
    1. Load mascot
    2. Erase existing mouth
    3. Draw new expression based on emotion
    4. Apply variant color treatment
    5. Scale to 110% canvas height (MrBeast-style overflow)
    6. Build glow halo
    7. Position on 1920×1080 canvas (left-dominant)
    8. Save
    """
    if not mascot_src.exists():
        print(f"[Layer 3] ERROR: mascot not found at {mascot_src}", flush=True)
        return 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"[Layer 3] Mascot ({variant}, {emotion}) → {out_path}", flush=True)

    # Step 1: Load original mascot
    mascot = Image.open(mascot_src).convert("RGBA")
    print(f"[Layer 3] Loaded mascot: {mascot.size}, mode={mascot.mode}", flush=True)

    # Step 2: Erase existing mouth to create blank canvas for new expression
    mascot = erase_mouth(mascot)
    print(f"[Layer 3] Mouth erased, drawing '{emotion}' expression...", flush=True)

    # Step 3: Draw the new facial expression
    mascot = draw_expression(mascot, emotion)

    # Step 4: Apply variant-specific color treatment
    mascot = apply_variant_treatment(mascot, variant, emotion)

    # Step 5: Scale mascot to 110% of canvas height
    # Real YouTube creators (MrBeast style) have the character OVERFLOW the canvas
    # bottom edge. The head and torso dominate the frame — fills the left half.
    target_h = int(CANVAS_H * 1.10)
    ratio = target_h / mascot.height
    target_w = int(mascot.width * ratio)
    mascot = mascot.resize((target_w, target_h), Image.Resampling.LANCZOS)

    # Step 6: Build glow halo sized to match scaled mascot
    glow = build_glow(mascot, variant, emotion)

    # Step 7: Position on canvas
    # Left-aligned with slight negative inset so mascot bleeds off left edge
    margin_left = -30
    pos_x = margin_left
    # Center vertically: middle of mascot = middle of canvas
    pos_y = (CANVAS_H - target_h) // 2

    # Glow offset for depth effect
    glow_x = pos_x - 40
    glow_y = pos_y - 30

    canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))

    def safe_composite(layer: Image.Image, x: int, y: int) -> None:
        """Composite a layer onto canvas, handling negative positions by cropping."""
        lx, ly = max(x, 0), max(y, 0)
        cx = -x if x < 0 else 0
        cy = -y if y < 0 else 0
        # Ensure we don't crop beyond the layer boundaries
        crop_right = min(layer.width, CANVAS_W - lx + cx)
        crop_bottom = min(layer.height, CANVAS_H - ly + cy)
        if crop_right <= cx or crop_bottom <= cy:
            return  # nothing to composite
        cropped = layer.crop((cx, cy, crop_right, crop_bottom))
        canvas.alpha_composite(cropped, (lx, ly))

    safe_composite(glow, glow_x, glow_y)
    safe_composite(mascot, pos_x, pos_y)

    # Step 8: Save
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path, format="PNG")
    print(
        f"[Layer 3] ✅ Saved {out_path} ({out_path.stat().st_size // 1024}KB)",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: layer_3_mascot.py <A|B> <emotion> <mascot_src> <out_path>")
        print("  emotion: shocked | excited | angry | scared | smug")
        sys.exit(1)
    sys.exit(
        run(
            sys.argv[1].upper(),
            sys.argv[2].lower(),
            Path(sys.argv[3]),
            Path(sys.argv[4]),
        )
    )
