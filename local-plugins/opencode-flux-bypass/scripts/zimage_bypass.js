import { chromium } from "playwright-extra";
import stealth from "puppeteer-extra-plugin-stealth";
import fs from "fs";
import path from "path";

chromium.use(stealth());

async function run() {
  const prompt = process.argv[2] || "Dark cinematic neon cyberpunk background, deep green and teal light, 4k";
  const outputPath = process.argv[3] || "/Users/jeremy/.config/opencode/skills/gen-image/outputs/layers/bg_A_new.jpg";

  console.log(`[Bypass] Generating: ${prompt}`);
  
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  try {
    await page.goto("https://zimage.design/");
    
    await page.fill('textarea[placeholder*="Enter your prompt"]', prompt);
    
    await page.click('button:has-text("Generate")');
    
    console.log("[Bypass] Waiting for image...");
    const imgSelector = 'img[src^="blob:"], img[src^="data:"], .generated-image img';
    await page.waitForSelector(imgSelector, { timeout: 60000 });
    
    const imgUrl = await page.getAttribute(imgSelector, "src");
    
    if (imgUrl.startsWith("blob:")) {
      const buffer = await page.evaluate(async (url) => {
        const response = await fetch(url);
        const arrayBuffer = await response.arrayBuffer();
        return Array.from(new Uint8Array(arrayBuffer));
      }, imgUrl);
      fs.writeFileSync(outputPath, Buffer.from(buffer));
    } else {
      const base64Data = imgUrl.split(",")[1];
      fs.writeFileSync(outputPath, Buffer.from(base64Data, "base64"));
    }
    
    console.log(`[Bypass] Success: saved to ${outputPath}`);
  } catch (error) {
    console.error(`[Bypass] Failed: ${error.message}`);
    const debugPath = "/tmp/image_bypass_error.png";
    await page.screenshot({ path: debugPath });
    console.log(`[Bypass] Error screenshot saved to ${debugPath}`);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

run();
