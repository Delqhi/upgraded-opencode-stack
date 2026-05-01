# OpenRouter OAuth Plugin

This plugin allows authentication with OpenRouter via OAuth PKCE, which ties API usage to your OpenRouter account instead of using limited API keys.

## Features

- Implements OpenRouter's OAuth PKCE flow
- Provides access to all OpenRouter models (especially free tier models like Qwen 3.6 Plus Preview)
- Bypasses daily free-model limits that affect API key-based access
- Stores credentials securely in `~/.openrouter/oauth_creds.json`

## Installation

The plugin is located at:
`~/.config/opencode/node_modules/opencode-openrouter-auth/`

It has been added to your opencode.json plugin array:
"opencode-openrouter-auth"

## Usage

Once OpenCode recognizes the plugin, you should be able to run:

```
opencode auth login --provider openrouter
```

This will:

1. Open your browser to OpenRouter's OAuth page
2. Authenticate with your OpenRouter account
3. Store the credentials locally
4. Allow you to use OpenRouter models tied to your account

## Models Available

- qwen/qwen3.6-plus:free
- qwen/qwen3.5-122b:free
- qwen/qwen3.5-397b:free
- openai/gpt-4o
- anthropic/claude-sonnet

## How It Solves Your Problem

Instead of using limited API keys that hit "free-models-per-day" limits, this plugin authenticates via OAuth and ties usage to your OpenRouter account with its respective credits and limits.
