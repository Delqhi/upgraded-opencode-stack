/**
 * OpenRouter OAuth and API Constants
 * Based on OpenRouter PKCE OAuth documentation
 * https://openrouter.ai/docs/use-cases/oauth-pkce
 */

// Provider ID
export const OPENROUTER_PROVIDER_ID = 'openrouter';

// OAuth PKCE Endpoints
export const OPENROUTER_OAUTH_CONFIG = {
  baseUrl: 'https://openrouter.ai',
  authorizationEndpoint: 'https://openrouter.ai/api/v1/auth/oauth/authorize',
  tokenEndpoint: 'https://openrouter.ai/api/v1/auth/oauth/token',
  clientId: 'a6f97563-a28e-4d4b-9b96-3a115c14e39a', // From OpenRouter docs
  redirectUri: 'https://localhost:1455/callback',  // Standard OpenCode callback
  scope: 'read write',
  grantType: 'authorization_code',
} as const;

// API Configuration
export const OPENROUTER_API_CONFIG = {
  // Default base URL for API calls
  defaultBaseUrl: 'https://openrouter.ai/api/v1',
  // Endpoint for chat completions
  chatEndpoint: '/chat/completions',
  // Endpoint for models
  modelsEndpoint: '/models',
  // Used by OpenCode to configure the provider
  baseUrl: 'https://openrouter.ai/api/v1',
} as const;

// Available OpenRouter models accessible via OAuth
export const OPENROUTER_MODELS = {
  // --- Free Models ---
  'qwen/qwen3.6-plus:free': {
    id: 'qwen/qwen3.6-plus:free',
    name: 'Qwen 3.6 Plus (Free with OAuth)',
    contextWindow: 1048576, // 1M tokens
    maxOutput: 32768, // 32K tokens
    description: 'Latest Qwen model - free tier with OAuth',
    reasoning: false,
    cost: { input: 0, output: 0 }, // Free via OAuth
  },
  'qwen/qwen3.5-122b:free': {
    id: 'qwen/qwen3.5-122b:free',
    name: 'Qwen 3.5 122B (Free with OAuth)',
    contextWindow: 262144,
    maxOutput: 32768,
    description: 'Qwen 3.5 model (122B parameters) - free tier with OAuth',
    reasoning: false,
    cost: { input: 0, output: 0 },
  },
  'qwen/qwen3.5-397b:free': {
    id: 'qwen/qwen3.5-397b:free',
    name: 'Qwen 3.5 397B (Free with OAuth)',
    contextWindow: 262144,
    maxOutput: 32768,
    description: 'Qwen 3.5 model (397B parameters) - free tier with OAuth',
    reasoning: false,
    cost: { input: 0, output: 0 },
  },
  // --- Popular Models ---
  'openai/gpt-4o': {
    id: 'openai/gpt-4o',
    name: 'OpenAI GPT-4o',
    contextWindow: 128000,
    maxOutput: 16384,
    description: 'OpenAI GPT-4o model',
    reasoning: false,
    cost: { input: 0, output: 0 },
  },
  'anthropic/claude-sonnet': {
    id: 'anthropic/claude-sonnet',
    name: 'Anthropic Claude Sonnet',
    contextWindow: 200000,
    maxOutput: 8192,
    description: 'Anthropic Claude Sonnet model',
    reasoning: false,
    cost: { input: 0, output: 0 },
  },
} as const;
