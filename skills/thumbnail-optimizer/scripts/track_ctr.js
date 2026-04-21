import fs from "fs";

const winner = process.argv[2]; // A or B
const winnerCTR = parseFloat(process.argv[3]);
const loserCTR = parseFloat(process.argv[4]);

if (!winner || isNaN(winnerCTR) || isNaN(loserCTR)) {
  console.log("❌ Usage: node track_ctr.js <Winner_A_or_B> <Winner_CTR> <Loser_CTR>");
  process.exit(1);
}

const dataPath = "outputs/data/performance.json";

// Ensure data dir exists
if (!fs.existsSync("outputs/data")) {
  fs.mkdirSync("outputs/data", { recursive: true });
}

let data = {
  previousCTR: 0,
  learnings: [],
  history: []
};

if (fs.existsSync(dataPath)) {
  data = JSON.parse(fs.readFileSync(dataPath, "utf8"));
}

// Check if we improved
const improved = winnerCTR > data.previousCTR;
let learning = "";

// A simple simulation of an LLM finding the learning based on what variation won
// In a full implementation, you'd feed the images + CTR to a Vision model here.
if (winner.toUpperCase() === "A") {
  learning = "Use close-up face shots and extremely high contrast glowing elements.";
} else {
  learning = "Include dramatic motion, upward trends, and bold composition elements.";
}

console.log(`📈 Results: Winner ${winner.toUpperCase()} (${winnerCTR}%) vs Loser (${loserCTR}%)`);

if (improved) {
  console.log(`✨ CTR improved from ${data.previousCTR}% to ${winnerCTR}%!`);
  data.previousCTR = winnerCTR;
  data.learnings.push(learning);
  console.log(`🧠 Added new learning: "${learning}"`);
} else {
  console.log(`📉 No overall improvement against historical best (${data.previousCTR}%). Retaining current learnings.`);
}

data.history.push({
  timestamp: new Date().toISOString(),
  winner: winner.toUpperCase(),
  winnerCTR,
  loserCTR
});

fs.writeFileSync(dataPath, JSON.stringify(data, null, 2));
console.log(`✅ Performance data saved to ${dataPath}`);
