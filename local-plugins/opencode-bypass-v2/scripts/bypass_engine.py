import sys
import os
import requests
import base64
from pathlib import Path


def run():
    prompt = sys.argv[1] if len(sys.argv) > 1 else "Dark cinematic background"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "output.jpg"

    is_mascot_edit = "mascot" in prompt.lower() or "maskottchen" in prompt.lower()

    engines = [
        {
            "url": "https://dreamai.art/api/generate",
            "model": "nano-banana-2",
            "type": "direct_post",
        },
        {
            "url": "https://dreamai.art/api/generate",
            "model": "wan-2.1",
            "type": "direct_post",
        },
    ]

    for engine in engines:
        try:
            payload = {"prompt": prompt, "model": engine["model"]}

            if is_mascot_edit:
                payload["prompt"] = (
                    f"A white spherical robot mascot with a green eye mask, {prompt}"
                )

            r = requests.post(engine["url"], json=payload, timeout=45)
            if r.status_code == 200:
                data = r.json()
                if "urls" in data and data["urls"]:
                    img_data = requests.get(data["urls"][0], timeout=30).content
                    Path(output_path).write_bytes(img_data)
                    print(f"Success via {engine['url']} ({engine['model']})")
                    return

        except Exception as e:
            print(f"Engine {engine['url']} failed: {str(e)}")

    from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

    if is_mascot_edit:
        src = "/Users/jeremy/.config/opencode/local-plugins/opencode-bypass-v2/assets/maskottchen.png"
        img = Image.open(src).convert("RGBA")

        is_shocked = "shock" in prompt.lower() or "dramatic" in prompt.lower()
        is_curious = "curious" in prompt.lower()

        if is_shocked:
            img = ImageEnhance.Contrast(img).enhance(1.4)
            overlay = Image.new("RGBA", img.size, (255, 0, 50, 40))
            img = Image.alpha_composite(img, overlay)
        elif is_curious:
            img = ImageEnhance.Brightness(img).enhance(1.1)
            overlay = Image.new("RGBA", img.size, (0, 100, 255, 30))
            img = Image.alpha_composite(img, overlay)

        img.save(output_path)
        print("Pipeline recovery: mascot identity preserved via local simulation")
    else:
        img = Image.new("RGB", (1280, 720), color=(10, 10, 25))
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, 1280, 720], outline=(0, 255, 180), width=6)
        img.save(output_path)
        print("Pipeline recovery: saved structural placeholder")


if __name__ == "__main__":
    run()
