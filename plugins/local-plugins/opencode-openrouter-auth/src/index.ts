import { spawn } from 'node:child_process';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { join } from 'node:path';
import { homedir } from 'node:os';
import { createInterface } from 'node:readline/promises';
import { stdin, stdout } from 'node:process';

const PROVIDER_ID = 'openrouter';
const BASE_URL = 'https://openrouter.ai/api/v1';
const KEYS_PAGE = 'https://openrouter.ai/settings/keys';

const MODELS = {
  'qwen/qwen3-coder:free': { name: 'Qwen 3 Coder (Free)', ctx: 262144, out: 33792, reasoning: false },
  'qwen/qwen3.5-coder:free': { name: 'Qwen 3.5 Coder (Free)', ctx: 262144, out: 33792, reasoning: false },
  'qwen/qwen3.6-plus:free': { name: 'Qwen 3.6 Plus (Free)', ctx: 1048576, out: 32768, reasoning: false },
  'qwen/qwen3.5-122b:free': { name: 'Qwen 3.5 122B (Free)', ctx: 262144, out: 32768, reasoning: false },
  'qwen/qwen3.5-397b:free': { name: 'Qwen 3.5 397B (Free)', ctx: 262144, out: 32768, reasoning: false },
  'deepseek/deepseek-chat-v3-0324:free': { name: 'DeepSeek V3 0324 (Free)', ctx: 163840, out: 16384, reasoning: false },
  'deepseek/deepseek-r1:free': { name: 'DeepSeek R1 (Free)', ctx: 163840, out: 32768, reasoning: true },
  'google/gemini-2.5-flash-preview:free': { name: 'Gemini 2.5 Flash (Free)', ctx: 1048576, out: 65536, reasoning: true },
  'meta-llama/llama-4-maverick:free': { name: 'Llama 4 Maverick (Free)', ctx: 1048576, out: 32768, reasoning: false },
  'microsoft/phi-4:free': { name: 'Phi-4 (Free)', ctx: 16384, out: 16384, reasoning: false },
} as const;

const CREDS_FILE = join(homedir(), '.openrouter', 'api_key.json');

async function loadStoredKey(): Promise<string | null> {
  try {
    const content = await readFile(CREDS_FILE, 'utf-8');
    const creds = JSON.parse(content);
    return creds.key || creds.apiKey || null;
  } catch {
    return null;
  }
}

async function saveStoredKey(key: string): Promise<void> {
  await mkdir(join(homedir(), '.openrouter'), { recursive: true });
  await writeFile(CREDS_FILE, JSON.stringify({ key, updated: new Date().toISOString() }, null, 2));
}

function openBrowser(url: string): void {
  try {
    const cmd = process.platform === 'darwin' ? 'open' : process.platform === 'win32' ? 'rundll32' : 'xdg-open';
    const args = process.platform === 'win32' ? ['url.dll,FileProtocolHandler', url] : [url];
    const child = spawn(cmd, args, { stdio: 'ignore', detached: true });
    child.unref?.();
  } catch {}
}

export const OpenRouterAuthPlugin = async (_input: unknown) => {
  return {
    auth: {
      provider: PROVIDER_ID,

      loader: async (
        getAuth: () => Promise<{ type: string; access?: string; refresh?: string; expires?: number }>,
        provider: { models?: Record<string, { cost?: { input: number; output: number } }> },
      ) => {
        if (provider?.models) {
          for (const model of Object.values(provider.models)) {
            if (model) model.cost = { input: 0, output: 0 };
          }
        }

        const auth = await getAuth();
        if (auth?.type === 'oauth' && auth.access) {
          return { apiKey: auth.access, baseURL: BASE_URL };
        }

        const storedKey = await loadStoredKey();
        if (storedKey) {
          return { apiKey: storedKey, baseURL: BASE_URL };
        }

        return null;
      },

      methods: [
        {
          type: 'oauth' as const,
          label: 'OpenRouter API Key (openrouter.ai)',
          authorize: async () => {
            openBrowser(KEYS_PAGE);

            return {
              url: KEYS_PAGE,
              callback: async () => {
                try {
                  const rl = createInterface({ input: stdin, output: stdout });
                  let apiKey: string;
                  try {
                    apiKey = (await rl.question('\nPaste your OpenRouter API key: ')).trim();
                  } finally {
                    rl.close();
                  }

                  if (!apiKey || !apiKey.startsWith('sk-or-') || apiKey.length < 20) {
                    console.log('Invalid key format. OpenRouter keys start with sk-or-v1-...');
                    return { type: 'failed' as const };
                  }

                  const resp = await fetch(`${BASE_URL}/models`, {
                    headers: { 'Authorization': `Bearer ${apiKey}` },
                  });
                  if (!resp.ok) {
                    console.log('API key validation failed.');
                    return { type: 'failed' as const };
                  }

                  await saveStoredKey(apiKey);

                  return {
                    type: 'success' as const,
                    access: apiKey,
                    refresh: '',
                    expires: Date.now() + 365 * 24 * 60 * 60 * 1000,
                  };
                } catch (e) {
                  console.error(`Error: ${e instanceof Error ? e.message : e}`);
                  return { type: 'failed' as const };
                }
              },
            };
          },
        },
      ],
    },

    config: async (config: Record<string, unknown>) => {
      const providers = (config.provider as Record<string, unknown>) || {};

      providers[PROVIDER_ID] = {
        npm: '@ai-sdk/openai-compatible',
        name: 'OpenRouter',
        options: { baseURL: BASE_URL },
        models: Object.fromEntries(
          Object.entries(MODELS).map(([id, m]) => [
            id,
            {
              id,
              name: m.name,
              reasoning: m.reasoning,
              limit: { context: m.ctx, output: m.out },
              cost: { input: 0, output: 0 },
              modalities: { input: ['text'], output: ['text'] },
            },
          ])
        ),
      };

      config.provider = providers;
    },
  };
};

export default OpenRouterAuthPlugin;
