import { join } from 'node:path';
import { homedir } from 'node:os';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import type { OpenRouterCredentials } from '../types';

const CREDS_DIR = join(homedir(), '.openrouter');
const CREDS_FILE = join(CREDS_DIR, 'oauth_creds.json');

export async function loadCredentials(): Promise<OpenRouterCredentials | null> {
  try {
    const content = await readFile(CREDS_FILE, 'utf-8');
    return JSON.parse(content);
  } catch {
    return null;
  }
}

export async function saveCredentials(credentials: OpenRouterCredentials): Promise<void> {
  try {
    await mkdir(CREDS_DIR, { recursive: true });
    await writeFile(CREDS_FILE, JSON.stringify(credentials, null, 2));
  } catch (e) {
    throw new Error(`Failed to save OpenRouter credentials: ${(e as Error).message}`);
  }
}