#!/usr/bin/env python3
"""
GEN-THUMB COMPOSER
==================
Orchestrator for the 5-layer workflow.
Updates to defaults: Short punchy text based on research.
"""

import argparse
import base64
import json
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = Path.cwd()
OUTPUT_DIR = PROJECT_ROOT / "outputs"


def run_script(script_name: str, args: list[str]) -> None:
    cmd = [sys.executable, str(BASE_DIR / script_name), *args]
    print(f"  ▶ {script_name} {' '.join(args)}", flush=True)
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if res.stdout:
        print(res.stdout, end="", flush=True)
    if res.stderr:
        print(res.stderr, end="", flush=True)
    if res.returncode != 0:
        raise RuntimeError(f"{script_name} failed with exit code {res.returncode}")


def build_variant(
    variant: str, topic: str, emotion: str, explicit_text: str | None
) -> dict:
    headline = explicit_text or ("1 VS MANY" if variant == "A" else "TOO SLOW")

    layers_dir = OUTPUT_DIR / "layers"
    layers_dir.mkdir(parents=True, exist_ok=True)

    bg_p = layers_dir / f"{variant}_1_bg.jpg"
    obj_p = layers_dir / f"{variant}_2_obj.png"
    masc_p = layers_dir / f"{variant}_3_masc.png"
    txt_p = layers_dir / f"{variant}_4_txt.png"
    final_p = OUTPUT_DIR / f"thumbnail_{variant}.png"

    print(f"\n{'=' * 40}\nBuilding Variant {variant}\n{'=' * 40}")

    run_script("layer_1_background.py", [variant, topic, str(bg_p)])
    run_script("layer_2_object_local.py", [variant, str(obj_p)])
    run_script(
        "layer_3_mascot.py",
        [variant, emotion, str(PROJECT_ROOT / "assets/mascot.png"), str(masc_p)],
    )
    run_script("layer_4_text.py", [headline, variant, str(txt_p)])
    run_script(
        "compose_thumbnail.py",
        [str(bg_p), str(obj_p), str(masc_p), str(txt_p), str(final_p)],
    )

    return {"id": variant, "headline": headline, "final": str(final_p)}


def build_preview(results: list[dict]) -> Path:
    cards = "".join(
        [
            f'<div style="margin-bottom:20px"><h2>Variant {r["id"]} - {r["headline"]}</h2><img src="data:image/png;base64,{base64.b64encode(Path(r["final"]).read_bytes()).decode()}" style="width:100%;max-width:800px;border:2px solid #333;border-radius:8px"></div>'
            for r in results
        ]
    )
    html = f"<html><body style='background:#111;color:#fff;font-family:sans-serif;padding:40px'><h1>Thumbnails</h1>{cards}</body></html>"
    p = OUTPUT_DIR / "preview.html"
    p.write_text(html)
    return p


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("topic", help="Video topic")
    parser.add_argument("--emotion-a", default="shocked", help="Emotion for variant A")
    parser.add_argument("--emotion-b", default="angry", help="Emotion for variant B")
    parser.add_argument("--text", default="", help="Override text")
    args = parser.parse_args()

    results = [
        build_variant("A", args.topic, args.emotion_a, args.text),
        build_variant("B", args.topic, args.emotion_b, args.text),
    ]

    build_preview(results)
    print("\n✅ Done! Check outputs/preview.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
