import nodriver as uc
import asyncio
import os
import sys


async def run():
    print("Starting browser...")
    browser = await uc.start(headless=True)
    page = await browser.get("https://dreamai.art/")

    try:
        await asyncio.sleep(5)
        print("Page loaded, searching for textarea...")

        elements = await page.select_all("textarea")
        target = None
        for el in elements:
            placeholder = await el.get_attribute("placeholder")
            if placeholder and "prompt" in placeholder.lower():
                target = el
                break

        if target:
            print("Entering prompt...")
            await target.send_keys(
                "Dark cinematic neon cyberpunk background, deep green and teal light, 4k"
            )

            buttons = await page.select_all("button")
            gen_btn = None
            for btn in buttons:
                text = await btn.get_text()
                if "Generate" in text:
                    gen_btn = btn
                    break

            if gen_btn:
                print("Clicking Generate...")
                await gen_btn.click()
                await asyncio.sleep(15)
                await page.save_screenshot("/tmp/dreamai_test.png")
                print("Result screenshot saved to /tmp/dreamai_test.png")
            else:
                print("Generate button not found")
        else:
            print("Textarea not found")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await browser.stop()


if __name__ == "__main__":
    asyncio.run(run())
