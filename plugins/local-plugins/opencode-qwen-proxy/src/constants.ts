/**
 * Qwen OAuth and API Constants
 */

export const QWEN_PROVIDER_ID = 'qwen';

export const QWEN_OAUTH_CONFIG = {
  baseUrl: 'https://chat.qwen.ai',
  deviceCodeEndpoint: 'https://chat.qwen.ai/api/v1/oauth2/device/code',
  tokenEndpoint: 'https://chat.qwen.ai/api/v1/oauth2/token',
  clientId: 'f0304373b74a44d2b584a3fb70ca9e56',
  scope: 'openid profile email model.completion',
  grantType: 'urn:ietf:params:oauth:grant-type:device_code',
} as const;

export const QWEN_API_CONFIG = {
  defaultBaseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
  portalBaseUrl: 'https://portal.qwen.ai/v1',
  chatEndpoint: '/chat/completions',
  modelsEndpoint: '/models',
  baseUrl: 'https://portal.qwen.ai/v1',
} as const;

export const CALLBACK_PORT = 14561;

export const QWEN_MODELS = {
  'coder-model': {
    id: 'coder-model',
    name: 'Qwen 3.6 Plus',
    contextWindow: 1048576,
    maxOutput: 65536,
    description: 'Qwen 3.6 Plus - efficient hybrid model with leading coding performance',
    reasoning: false,
    cost: { input: 0, output: 0 },
  },
  'vision-model': {
    id: 'vision-model',
    name: 'Qwen 3.6 Vision Plus',
    contextWindow: 131072,
    maxOutput: 32768,
    description: 'Latest Qwen 3.6 Vision Plus model, supports image input',
    reasoning: false,
    cost: { input: 0, output: 0 },
  },
} as const;
