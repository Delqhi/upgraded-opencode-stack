import { spawn } from "child_process";
import fs from "fs";
import path from "path";

async function run() {
  const prompt = process.argv[2] || "Dark cinematic neon cyberpunk background, deep green and teal light, 4k";
  const outputPath = process.argv[3] || "/Users/jeremy/.config/opencode/skills/gen-image/outputs/layers/bg_A_new.jpg";

  console.log(`[Bypass] Generating: ${prompt}`);

  const pythonScript = `
import nodriver as uc
import asyncio
import os
import base64

async def main():
    browser = await uc.start(headless=True)
    page = await browser.get("https://zimage.design/")
    
    # Wait and fill prompt
    textarea = await page.select('textarea[placeholder*="Enter your prompt"]')
    await textarea.send_keys("${prompt.replace(/"/g, '\\"')}")
    
    # Click generate
    button = await page.select('button:has-text("Generate")')
    await button.click()
    
    print("[Bypass] Waiting for image...")
    # Wait for img with src
    img = await page.wait_for('img[src^="blob:"], img[src^="data:"], .generated-image img', timeout=60)
    img_src = await img.get_attribute("src")
    
    if img_src.startswith("data:"):
        header, encoded = img_src.split(",", 1)
        data = base64.b64decode(encoded)
        with open("${outputPath}", "wb") as f:
            f.write(data)
    else:
        # For blob URLs we need to fetch via JS
        script = f"fetch('{img_src}').then(r => r.arrayBuffer()).then(buf => Array.from(new Uint8Array(buf)))"
        buf_array = await page.evaluate(script)
        with open("${outputPath}", "wb") as f:
            f.write(bytes(buf_array))
            
    print(f"[Bypass] Success: saved to ${outputPath}")
    await browser.stop()

if __name__ == "__main__":
    asyncio.run(main())
`;

  const tmpScript = "/tmp/zimage_bypass.py";
  fs.writeFileSync(tmpScript, pythonScript);

  const py = spawn("python3", [tmpScript]);
  
  py.stdout.on("data", (data) => console.log(data.toString().trim()));
  py.stderr.on("data", (data) => console.error(data.toString().trim()));

  py.on("close", (code) => {
    if (code === 0) {
      console.log(`[Bypass] Process finished successfully`);
    } else {
      console.error(`[Bypass] Process failed with code ${code}`);
      process.exit(1);
    }
  });
}

run();
