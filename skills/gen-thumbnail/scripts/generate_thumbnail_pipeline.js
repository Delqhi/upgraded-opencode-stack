import fs from "fs";
import path from "path";
import { execFileSync } from "child_process";

const ROOT = process.cwd();
const OUT = {
  data: path.join(ROOT, "outputs/data"),
  thumbnails: path.join(ROOT, "outputs/thumbnails"),
  previews: path.join(ROOT, "outputs/previews"),
};

const DEFAULT_BRAND = {
  name: "OpenSIN Profit Thumbnail System",
  generation_backend: "opencode-image-flow",
  image_command: "\\generate-image",
  model_hint: "google/antigravity-gemini-3-flash",
  output_source_dir: ".opencode/generated-images/",
  reference_style: "left-dominant mascot, right-stacked headline, neon green/yellow money visuals, dark background, glossy high-contrast YouTube thumbnail",
  palette: {
    primary: "#19FF4C",
    secondary: "#FFD400",
    accent: "#FFFFFF",
    background: "#050608",
    shadow: "#000000"
  },
  accent: "neon green glow",
  border: "thick black outline with soft green rim light",
  character: "white-and-green masked creator mascot with smug confident eyes and slight smile",
  composition: {
    layout: "giant face on the left, bold stacked headline on the right, laptop profit chart bottom-right, arrow connecting face to laptop",
    face_position: "left dominant close-up",
    text_position: "upper-right stacked block",
    hook_object: "glowing laptop with rising graph and dollar signs",
    motion_cue: "large curved yellow arrow plus floating bills and spark particles",
    background: "dark studio background with green glow and light streaks"
  },
  typography: {
    style: "oversized condensed uppercase, white top line, yellow second line, heavy black stroke",
    max_words: 4,
    preferred_headlines: ["AUTO PROFIT?", "AI MAKES MONEY", "MONEY ALONE"]
  },
  motifs: {
    money: true,
    arrow: true,
    graph: true,
    floating_bills: true,
    green_particles: true,
    laptop_profit_screen: true
  },
  constraints: {
    max_visual_elements: 3,
    face_dominant: true,
    high_contrast: true,
    simple_background: true,
    curiosity_gap: true,
    negative_space_for_text: true,
    brand_repeatability: true,
    no_midjourney: true,
    no_raw_gemini_rest: true
  },
  prompt_tokens: {
    brand_token: "white-and-green masked creator mascot",
    visual_motif: "curved yellow arrow to glowing profit laptop",
    do_more: [
      "close-up face dominance",
      "strong neon glow",
      "one clear money object"
    ],
    do_less: [
      "busy collage",
      "tiny text",
      "more than three objects"
    ]
  }
};

function ensureDirs() {
  for (const dir of Object.values(OUT)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

function readJsonIfExists(filePath, fallback) {
  if (!fs.existsSync(filePath)) return fallback;
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function writeJson(filePath, value) {
  fs.writeFileSync(filePath, JSON.stringify(value, null, 2), "utf8");
}

function bootstrapStateFiles() {
  const brandPath = path.join(OUT.data, "brand_config.json");
  const performancePath = path.join(OUT.data, "performance.json");

  if (!fs.existsSync(brandPath)) {
    writeJson(brandPath, DEFAULT_BRAND);
  }

  if (!fs.existsSync(performancePath)) {
    writeJson(performancePath, {
      previousCTR: 0,
      do_more: [],
      do_less: [],
      brand_token: [],
      visual_motif: [],
      history: []
    });
  }
}

function loadBrandConfig() {
  const custom = readJsonIfExists(path.join(OUT.data, "brand_config.json"), null);
  return custom ? { ...DEFAULT_BRAND, ...custom } : DEFAULT_BRAND;
}

function loadPerformance() {
  return readJsonIfExists(path.join(OUT.data, "performance.json"), {
    previousCTR: 0,
    do_more: [],
    do_less: [],
    brand_token: [],
    visual_motif: [],
    history: []
  });
}

function loadSpec() {
  return readJsonIfExists(path.join(OUT.data, "spec.json"), null);
}

function buildLearningHints(perf) {
  return [
    perf?.do_more?.length ? `do more: ${perf.do_more.join(" | ")}` : "",
    perf?.do_less?.length ? `do less: ${perf.do_less.join(" | ")}` : "",
    perf?.brand_token?.length ? `brand token: ${perf.brand_token[0]}` : "",
    perf?.visual_motif?.length ? `visual motif: ${perf.visual_motif[0]}` : "",
  ].filter(Boolean);
}

function headlineForVariant(variantId, brand) {
  return brand?.typography?.preferred_headlines?.[variantId === "A" ? 0 : 1] || (variantId === "A" ? "GEFUNDEN?!" : "AUTO PROFIT?");
}

function promptForVariant(topicText, variantId, brand, perf, spec) {
  const headline = headlineForVariant(variantId, brand);
  const baseVisuals = variantId === "A"
    ? "shocked creator face, one glowing laptop, one yellow arrow, dark background"
    : "smug creator face, one rising graph, one burst of money, dark background";
  const learning = buildLearningHints(perf).join(", ");
  const specHint = spec?.final_prompts?.[variantId] ? `Final prompt hint: ${spec.final_prompts[variantId]}` : "";

  return [
    "Use case: stylized-concept",
    "Asset type: YouTube thumbnail",
    `Primary request: ${topicText}`,
    "Subject: face-dominant creator mascot",
    "Style: high contrast, glossy, cinematic, premium creator thumbnail",
    "Composition: left-side face dominance, right-side headline space, single hook object",
    `Visuals: max 3 elements total; ${baseVisuals}`,
    "Motion cue: curved arrow, spark particles, motion streaks, or floating money",
    "Background: simple dark studio background",
    `Color palette: ${brand.palette.primary}, ${brand.palette.secondary}, ${brand.palette.accent}`,
    `Brand consistency: recurring ${brand.character}, ${brand.accent}, ${brand.border}`,
    `Text overlay: reserved negative space for \"${headline}\"`,
    "Constraints: no clutter, no collage, no extra objects, no Midjourney, no raw Gemini REST",
    learning,
    specHint
  ].filter(Boolean).join(", ");
}

function latestFileInDir(dir) {
  if (!fs.existsSync(dir)) return null;
  return fs.readdirSync(dir)
    .map((name) => path.join(dir, name))
    .filter((filePath) => fs.statSync(filePath).isFile())
    .sort((a, b) => fs.statSync(b).mtimeMs - fs.statSync(a).mtimeMs)[0] || null;
}

function latestGeneratedImage() {
  const dirs = [path.join(ROOT, ".opencode/generated-images"), path.join(ROOT, "output/imagegen")];
  for (const dir of dirs) {
    const file = latestFileInDir(dir);
    if (file) return file;
  }
  return null;
}

function runImage(prompt, fileName) {
  const message = `/generate-image ${prompt}; file name should be ${fileName}; save it at .opencode/generated-images`;
  execFileSync("opencode", ["run", message, "--model=google/antigravity-gemini-3-flash", "--format", "json"], {
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"]
  });
  const produced = latestGeneratedImage();
  if (!produced) {
    throw new Error(`No generated image was found for ${fileName}`);
  }
  return produced;
}

async function writeFinalImage(rawPath, finalPath, headline) {
  try {
    const sharp = (await import("sharp")).default;
    const overlay = `
      <svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080">
        <rect width="1920" height="1080" fill="transparent"/>
        <rect x="44" y="44" width="1832" height="992" rx="44" fill="none" stroke="#000000" stroke-width="16"/>
        <rect x="72" y="828" width="1776" height="176" rx="28" fill="rgba(0,0,0,0.42)"/>
        <rect x="72" y="828" width="16" height="176" fill="#19FF4C"/>
        <text x="112" y="940" font-family="Arial Black, Impact, sans-serif" font-size="112" font-weight="900" fill="#FFFFFF" stroke="#000000" stroke-width="14" paint-order="stroke fill" letter-spacing="-2">${headline}</text>
      </svg>
    `;
    await sharp(rawPath).resize(1920, 1080, { fit: "cover", position: "attention" }).composite([{ input: Buffer.from(overlay), top: 0, left: 0 }]).png().toFile(finalPath);
  } catch {
    fs.copyFileSync(rawPath, finalPath);
  }
}

function buildPreviewHtml(topicText, brand, results) {
  const cards = results.map((result) => `
    <section class="card">
      <div class="label">${result.id}</div>
      <img src="../thumbnails/${path.basename(result.finalPath)}" alt="Thumbnail ${result.id}" />
      <div class="meta">
        <div><strong>Headline:</strong> ${result.headline}</div>
        <div><strong>Prompt:</strong> ${result.prompt}</div>
        <div><strong>Source:</strong> ${result.source}</div>
      </div>
    </section>
  `).join("");

  return `<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Thumbnail Preview - ${topicText}</title>
  <style>
    body { margin: 0; font-family: Arial, sans-serif; background: #0b0f19; color: #fff; padding: 24px; }
    h1, h2 { margin: 0 0 12px; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(420px, 1fr)); gap: 20px; }
    .card { background: #111827; border: 1px solid #243041; border-radius: 18px; overflow: hidden; }
    .label { padding: 10px 14px; font-weight: 800; background: #00e5ff; color: #001018; }
    img { width: 100%; display: block; aspect-ratio: 16 / 9; object-fit: cover; background: #111; }
    .meta { padding: 14px; font-size: 14px; line-height: 1.45; color: #d6def0; }
    .brand { color: #00e5ff; }
  </style>
</head>
<body>
  <h1>Thumbnail A/B Preview</h1>
  <h2 class="brand">${topicText} • ${brand.name}</h2>
  <div class="grid">${cards}</div>
</body>
</html>`;
}

async function main() {
  ensureDirs();
  bootstrapStateFiles();

  const topic = process.argv.slice(2).join(" ").trim();
  const brand = loadBrandConfig();
  const perf = loadPerformance();
  const spec = loadSpec();

  const promptA = promptForVariant(topic, "A", brand, perf, spec);
  const promptB = promptForVariant(topic, "B", brand, perf, spec);
  const headlineA = headlineForVariant("A", brand);
  const headlineB = headlineForVariant("B", brand);

  fs.writeFileSync(path.join(OUT.thumbnails, "prompt_A.txt"), promptA, "utf8");
  fs.writeFileSync(path.join(OUT.thumbnails, "prompt_B.txt"), promptB, "utf8");

  const rawA = runImage(promptA, "thumbnail_A");
  const rawB = runImage(promptB, "thumbnail_B");

  const finalA = path.join(OUT.thumbnails, "thumbnail_A.png");
  const finalB = path.join(OUT.thumbnails, "thumbnail_B.png");

  await writeFinalImage(rawA, finalA, headlineA);
  await writeFinalImage(rawB, finalB, headlineB);

  const previewHtml = buildPreviewHtml(topic, brand, [
    { id: "A", headline: headlineA, prompt: promptA, finalPath: finalA, source: "OpenCode image flow" },
    { id: "B", headline: headlineB, prompt: promptB, finalPath: finalB, source: "OpenCode image flow" }
  ]);

  fs.writeFileSync(path.join(OUT.previews, "preview.html"), previewHtml, "utf8");
  writeJson(path.join(OUT.data, "last_run.json"), {
    topic,
    brand,
    generatedAt: new Date().toISOString(),
    variations: [
      { id: "A", headline: headlineA, prompt: promptA, finalPath: finalA },
      { id: "B", headline: headlineB, prompt: promptB, finalPath: finalB }
    ]
  });

  console.log(`✅ Pipeline completed: ${path.join(OUT.previews, "preview.html")}`);
}

main().catch((error) => {
  console.error("❌ Thumbnail pipeline failed");
  console.error(error?.message || error);
  process.exit(1);
});
