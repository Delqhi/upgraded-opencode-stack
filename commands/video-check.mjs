#!/usr/bin/env node
import { spawnSync } from 'node:child_process';
import { mkdtempSync, rmSync, readdirSync, readFileSync, existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const MODEL = 'nvidia/meta/llama-3.2-11b-vision-instruct';
const ENDPOINT = 'https://integrate.api.nvidia.com/v1/chat/completions';
const API_KEY = process.env.NVIDIA_API_KEY;

if (!API_KEY) {
  console.error('NVIDIA_API_KEY not set');
  process.exit(1);
}

const args = process.argv.slice(2);
const flags = new Set(args.filter((a) => a.startsWith('--')));
const positional = args.filter((a) => !a.startsWith('--'));
const videoPath = positional[0];
const customPrompt = positional.slice(1).join(' ').trim();

if (!videoPath || flags.has('--help') || flags.has('-h')) {
  console.log('Usage: /video-check <video-path> [custom-prompt] [--json] [--chunk]');
  process.exit(0);
}

if (!existsSync(videoPath)) {
  console.error(`Video not found: ${videoPath}`);
  process.exit(1);
}

const jsonMode = flags.has('--json');
const forceChunk = flags.has('--chunk');
const tmpRoot = mkdtempSync(join(tmpdir(), 'video-check-'));
process.on('exit', () => rmSync(tmpRoot, { recursive: true, force: true }));

const prompt = customPrompt || 'Analysiere das Video präzise. Nenne: 1) Hauptszenen/Ablauf, 2) wichtige Objekte/Personen, 3) Kontext/Handlung, 4) Auffälligkeiten. Antworte maximal in 6 kurzen Stichpunkten. Keine Einleitung, keine Füllwörter.';

function run(cmd, argv) {
  const res = spawnSync(cmd, argv, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] });
  if (res.error) throw res.error;
  if (res.status !== 0) {
    throw new Error((res.stderr || res.stdout || '').trim() || `${cmd} failed with code ${res.status}`);
  }
  return res.stdout || '';
}

function durationSeconds(file) {
  const out = run('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', file]);
  return Number.parseFloat(out.trim()) || 0;
}

function extractFrames(file, outDir, maxFrames) {
  run('ffmpeg', [
    '-hide_banner', '-loglevel', 'error', '-y', '-i', file,
    '-vf', "select='eq(n,0)+gt(scene,0.35)',scale=768:768:force_original_aspect_ratio=decrease,pad=768:768:(ow-iw)/2:(oh-ih)/2:black",
    '-frames:v', String(maxFrames), '-q:v', '3', join(outDir, 'frame_%03d.jpg')
  ]);
  return readdirSync(outDir).filter((f) => f.endsWith('.jpg')).sort();
}

function encodeFrames(dir, files) {
  return files.map((file) => ({
    type: 'image_url',
    image_url: { url: `data:image/jpeg;base64,${readFileSync(join(dir, file)).toString('base64')}` }
  }));
}

async function callNim(textPrompt, images) {
  const payload = {
    model: MODEL,
    temperature: 0,
    max_tokens: 350,
    top_p: 0.9,
    messages: [{
      role: 'user',
      content: [
        { type: 'text', text: textPrompt },
        ...images,
      ]
    }]
  };

  const res = await fetch(ENDPOINT, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${API_KEY}`
    },
    body: JSON.stringify(payload)
  });

  const raw = await res.text();
  if (!res.ok) throw new Error(`NIM ${res.status}: ${raw}`);
  const data = JSON.parse(raw);
  return (data?.choices?.[0]?.message?.content || '').trim();
}

function toJsonMaybe(text) {
  const fenced = text.match(/```(?:json)?\s*([\s\S]*?)```/i);
  const body = fenced?.[1] || text;
  const first = body.indexOf('{');
  const last = body.lastIndexOf('}');
  if (first === -1 || last === -1 || last <= first) return null;
  try { return JSON.parse(body.slice(first, last + 1)); } catch { return null; }
}

async function analyzeSegment(label, file, promptText, maxFrames) {
  const segDir = mkdtempSync(join(tmpRoot, `${label}-`));
  try {
    const frames = extractFrames(file, segDir, maxFrames);
    const effectiveFrames = frames.length ? frames : (() => {
      run('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-i', file, '-frames:v', '1', '-q:v', '3', join(segDir, 'frame_001.jpg')]);
      return readdirSync(segDir).filter((f) => f.endsWith('.jpg')).sort();
    })();
    const images = encodeFrames(segDir, effectiveFrames);
    const analysis = await callNim(promptText, images);
    return { frames: effectiveFrames.length, analysis };
  } finally {
    rmSync(segDir, { recursive: true, force: true });
  }
}

function printResult(summary, chunks) {
  if (jsonMode) {
    const parsed = toJsonMaybe(summary);
    const payload = parsed || { summary, chunks };
    console.log(JSON.stringify(payload, null, 2));
  } else {
    console.log(`\n🎬 Video-Analyse${chunks?.length ? ` (${chunks.length} Chunks)` : ''}:\n${summary}\n`);
  }
}

async function main() {
  const duration = durationSeconds(videoPath);
  const shouldChunk = forceChunk || duration > 120;
  if (!shouldChunk) {
    const result = await analyzeSegment('single', videoPath, prompt, 8);
    printResult(result.analysis, [{ chunk: 1, analysis: result.analysis }]);
    return;
  }

  const chunkSize = 120;
  const numChunks = Math.max(1, Math.ceil(duration / chunkSize));
  const segmentAnalyses = [];
  for (let i = 0; i < numChunks; i++) {
    const segFile = join(tmpRoot, `seg_${i}.mp4`);
    run('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-i', videoPath, '-ss', String(i * chunkSize), '-t', String(chunkSize), '-c', 'copy', segFile]);
    const result = await analyzeSegment(`chunk_${i + 1}`, segFile, `[Chunk ${i + 1}/${numChunks}] ${prompt}`, 6);
    segmentAnalyses.push({ chunk: i + 1, analysis: result.analysis });
  }

  const summaryPrompt = `Fasse diese Chunk-Analysen präzise zusammen. Maximal 6 Stichpunkte. Keine Einleitung.\n\n${segmentAnalyses.map((c) => `Chunk ${c.chunk}: ${c.analysis}`).join('\n')}`;
  const summary = await callNim(summaryPrompt, []);
  printResult(summary, segmentAnalyses);
}

main().catch((err) => {
  console.error(`❌ ${err.message}`);
  process.exit(1);
});
