#!/usr/bin/env node
/**
 * Dashboard Sync Script - Updates a2a.delqhi.com registry with all agents
 * Usage: node scripts/dashboard-sync.mjs --dry-run | --apply
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');

function loadJsonC(filePath) {
  const raw = fs.readFileSync(filePath, 'utf-8');
  const cleaned = raw.replace(/^\s*\/\/.*$/gm, '');
  return JSON.parse(cleaned);
}

function loadTeamConfigs() {
  const teams = {};
  const files = fs.readdirSync(ROOT).filter(f => f.startsWith('my-sin-team-') && f.endsWith('.json'));
  for (const file of files) {
    const key = file.replace('my-sin-', '').replace('.json', '');
    try { teams[key] = loadJsonC(path.join(ROOT, file)); } catch (e) {}
  }
  return teams;
}

function generateRegistry() {
  const ohMySin = loadJsonC(path.join(ROOT, 'oh-my-sin.json'));
  const teamConfigs = loadTeamConfigs();
  const registry = {
    version: '5.0.0',
    generatedAt: new Date().toISOString(),
    teams: {},
    agents: [],
    models: { explore: 'nvidia-nim/stepfun-ai/step-3.5-flash', librarian: 'nvidia-nim/stepfun-ai/step-3.5-flash' }
  };
  for (const [teamKey, teamInfo] of Object.entries(ohMySin.teams || {})) {
    const config = teamConfigs[teamKey.replace('team-', '')] || {};
    registry.teams[teamKey] = {
      name: teamInfo.name, manager: teamInfo.manager, description: teamInfo.description,
      primaryModel: teamInfo.primary_model, fallbackModels: teamInfo.fallback_models || [],
      members: teamInfo.members || [], config: config.categories || {}
    };
    for (const member of (teamInfo.members || [])) {
      registry.agents.push({ name: member, team: teamKey, manager: teamInfo.manager, primaryModel: teamInfo.primary_model, status: 'active' });
    }
  }
  return registry;
}

const args = process.argv.slice(2);
const dryRun = args.includes('--dry-run');
const apply = args.includes('--apply');
if (!dryRun && !apply) { console.log('Usage: node scripts/dashboard-sync.mjs [--dry-run | --apply]'); process.exit(1); }

const registry = generateRegistry();
if (dryRun) {
  console.log('DASHBOARD SYNC PREVIEW');
  console.log('Teams:', Object.keys(registry.teams).length);
  console.log('Agents:', registry.agents.length);
  for (const [key, team] of Object.entries(registry.teams)) {
    console.log(team.name + ' (' + team.members.length + ' agents): ' + team.members.join(', '));
  }
}
if (apply) {
  const outputPath = path.join(ROOT, 'docs', 'operations', 'dashboard-registry.json');
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, JSON.stringify(registry, null, 2));
  console.log('Registry written:', outputPath);
}
