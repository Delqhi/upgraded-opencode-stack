import fs from "fs";
import path from "path";

function parseArgs(argv) {
  const positionals = [];
  const flags = {};

  for (let i = 0; i < argv.length; i++) {
    const token = argv[i];

    if (!token.startsWith("--")) {
      positionals.push(token);
      continue;
    }

    const key = token.slice(2);
    const next = argv[i + 1];

    if (next && !next.startsWith("--")) {
      flags[key] = next;
      i++;
    } else {
      flags[key] = "true";
    }
  }

  return { positionals, flags };
}

function readJson(filePath, fallback) {
  if (!fs.existsSync(filePath)) return fallback;
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function uniqueList(values, limit = 5) {
  return [...new Set(values.filter(Boolean).map((value) => String(value).trim()).filter(Boolean))].slice(0, limit);
}

function pickText(...candidates) {
  for (const value of candidates) {
    if (value && String(value).trim()) return String(value).trim();
  }
  return "";
}

function inferVariant(lastRun, variantId) {
  const variations = Array.isArray(lastRun?.variations) ? lastRun.variations : [];
  return variations.find((variant) => String(variant.id || "").toUpperCase() === variantId) || {
    id: variantId,
    headline: "",
    prompt: "",
    model: "",
    concept: "",
    emotion: "",
    face: "",
    motionCue: "",
    background: "",
    brandToken: ""
  };
}

const { positionals, flags } = parseArgs(process.argv.slice(2));
const [winnerRaw, winnerCTRRaw, loserCTRRaw] = positionals;

if (!winnerRaw || winnerCTRRaw === undefined || loserCTRRaw === undefined) {
  console.log("❌ Usage: node track_ctr.js <Winner_A_or_B> <Winner_CTR> <Loser_CTR> --do-more \"...\" --do-less \"...\" --brand-token \"...\" --visual-motif \"...\"");
  process.exit(1);
}

const winner = String(winnerRaw).toUpperCase();
const winnerCTR = Number.parseFloat(winnerCTRRaw);
const loserCTR = Number.parseFloat(loserCTRRaw);

if (!['A', 'B'].includes(winner) || Number.isNaN(winnerCTR) || Number.isNaN(loserCTR)) {
  console.log("❌ Invalid input. Winner must be A or B, and CTR values must be numbers.");
  process.exit(1);
}

const dataDir = path.join(process.cwd(), "outputs", "data");
const performancePath = path.join(dataDir, "performance.json");
const lastRunPath = path.join(dataDir, "last_run.json");

fs.mkdirSync(dataDir, { recursive: true });

const performance = readJson(performancePath, {
  previousCTR: 0,
  do_more: [],
  do_less: [],
  brand_token: [],
  visual_motif: [],
  history: []
});

const lastRun = readJson(lastRunPath, {});
const winnerVar = inferVariant(lastRun, winner);
const loserVar = inferVariant(lastRun, winner === "A" ? "B" : "A");

const explicitDoMore = pickText(flags["do-more"], flags.do_more);
const explicitDoLess = pickText(flags["do-less"], flags.do_less);
const explicitBrandToken = pickText(flags["brand-token"], flags.brand_token);
const explicitVisualMotif = pickText(flags["visual-motif"], flags.visual_motif);

const doMore = uniqueList([
  explicitDoMore,
  winnerVar.concept,
  winnerVar.face ? `face: ${winnerVar.face}` : "",
  winnerVar.motionCue ? `motion: ${winnerVar.motionCue}` : "",
  winnerVar.prompt ? `prompt: ${winnerVar.prompt}` : ""
], 5);

const doLess = uniqueList([
  explicitDoLess,
  loserVar.concept ? `avoid: ${loserVar.concept}` : "",
  loserVar.background ? `avoid: ${loserVar.background}` : "",
  loserVar.prompt ? `avoid: ${loserVar.prompt}` : ""
], 5);

const brandToken = uniqueList([
  explicitBrandToken,
  winnerVar.brandToken,
  lastRun?.brand?.character,
  lastRun?.brand?.name
], 5);

const visualMotif = uniqueList([
  explicitVisualMotif,
  winnerVar.motionCue,
  winnerVar.concept,
  winnerVar.emotion,
  winnerVar.face
], 5);

const improved = winnerCTR > Number(performance.previousCTR || 0);
const delta = Number((winnerCTR - loserCTR).toFixed(2));

performance.previousCTR = Math.max(Number(performance.previousCTR || 0), winnerCTR);
performance.do_more = uniqueList([...performance.do_more, ...doMore], 5);
performance.do_less = uniqueList([...performance.do_less, ...doLess], 5);
performance.brand_token = uniqueList([...performance.brand_token, ...brandToken], 5);
performance.visual_motif = uniqueList([...performance.visual_motif, ...visualMotif], 5);

performance.history.push({
  timestamp: new Date().toISOString(),
  winner,
  winnerCTR,
  loserCTR,
  delta,
  topic: lastRun?.topic || "",
  winner_variant: {
    id: winnerVar.id || winner,
    headline: winnerVar.headline || "",
    prompt: winnerVar.prompt || "",
    model: winnerVar.model || ""
  },
  loser_variant: {
    id: loserVar.id || (winner === "A" ? "B" : "A"),
    headline: loserVar.headline || "",
    prompt: loserVar.prompt || "",
    model: loserVar.model || ""
  },
  do_more: doMore,
  do_less: doLess,
  brand_token: brandToken,
  visual_motif: visualMotif,
  improved
});

fs.writeFileSync(performancePath, JSON.stringify(performance, null, 2), "utf8");

console.log(`📈 Winner ${winner}: ${winnerCTR}% | Loser: ${loserCTR}% | Δ ${delta}%`);
console.log(improved ? "✨ New best CTR recorded." : "ℹ️ Historical best unchanged.");
console.log(`🧠 do_more: ${performance.do_more.join(" | ") || "-"}`);
console.log(`🧠 do_less: ${performance.do_less.join(" | ") || "-"}`);
console.log(`🧠 brand_token: ${performance.brand_token.join(" | ") || "-"}`);
console.log(`🧠 visual_motif: ${performance.visual_motif.join(" | ") || "-"}`);
console.log(`✅ Saved: ${performancePath}`);
