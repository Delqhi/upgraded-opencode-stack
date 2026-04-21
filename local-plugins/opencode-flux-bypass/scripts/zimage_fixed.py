import nodriver as uc
import asyncio
import os
import base64
import sys


async def main():
    prompt = (
        sys.argv[1] if len(sys.argv) > 1 else "Dark cinematic neon cyberpunk background"
    )
    output_path = sys.argv[2] if len(sys.argv) > 2 else "output.jpg"

    print(f"Generating: {prompt}")

    browser = await uc.start(headless=True)
    page = await browser.get("https://zimage.design/")

    try:
        await asyncio.sleep(5)

        elements = await page.select_all("textarea")
        target = None
        for el in elements:
            placeholder = await el.get_attribute("placeholder")
            if placeholder and "prompt" in placeholder.lower():
                target = el
                break

        if not target:
            target = await page.select('textarea[placeholder*="Enter your prompt"]')

        await target.send_keys(prompt)

        buttons = await page.select_all("button")
        gen_btn = None
        for btn in buttons:
            text = await btn.get_text()
            if "Generate" in text:
                gen_btn = btn
                break

        if not gen_btn:
            gen_btn = await page.select('button:has-text("Generate")')

        await gen_btn.click()
        print("Waiting for image...")

        img = None
        for _ in range(60):
            await asyncio.sleep(1)
            imgs = await page.select_all("img")
            for i in imgs:
                src = await i.get_attribute("src")
                if src and (src.startswith("blob:") or src.startswith("data:")):
                    cls = await i.get_attribute("class")
                    if cls and "generated" in cls.lower():
                        img = i
                        break
            if img:
                break

        if not img:
            img = await page.wait_for(
                'img[src^="blob:"], img[src^="data:"], .generated-image img', timeout=10
            )

        img_src = await img.get_attribute("src")

        if img_src.startswith("data:"):
            header, encoded = img_src.split(",", 1)
            data = base64.b64decode(encoded)
            with open(output_path, "wb") as f:
                f.write(data)
        else:
            script = f"fetch('{img_src}').then(r => r.arrayBuffer()).then(buf => Array.from(new Uint8Array(buf)))"
            buf_array = await page.evaluate(script)
            with open(output_path, "wb") as f:
                f.write(bytes(buf_array))

        print(f"Success: saved to {output_path}")
    except Exception as e:
        print(f"Error: {e}")
        await page.save_screenshot("/tmp/zimage_debug.png")
        print("Debug screenshot saved to /tmp/zimage_debug.png")
        sys.exit(1)
    finally:
        await browser.stop()


if __name__ == "__main__":
    asyncio.run(main())
