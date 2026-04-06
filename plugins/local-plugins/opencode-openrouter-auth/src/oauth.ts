import { spawn } from 'node:child_process';
import { readFile } from 'node:fs/promises';
import type { OpenRouterAuthConfig, OpenRouterCredentials, OpenRouterTokenResponse } from '../types';
import { OPENROUTER_OAUTH_CONFIG } from './constants';
import { loadCredentials, saveCredentials } from './plugin/auth';

export async function performPKCEFlow(config: OpenRouterAuthConfig): Promise<OpenRouterCredentials> {
  // Generate PKCE code verifier and challenge
  const codeVerifier = generateRandomString(128);
  const codeChallenge = await generateCodeChallenge(codeVerifier);
  
  // Construct authorization URL with PKCE parameters
  const authUrl = new URL(config.authorizationEndpoint);
  authUrl.searchParams.set('response_type', 'code');
  authUrl.searchParams.set('client_id', config.clientId);
  authUrl.searchParams.set('redirect_uri', config.redirectUri);
  authUrl.searchParams.set('scope', config.scope);
  authUrl.searchParams.set('code_challenge', codeChallenge);
  authUrl.searchParams.set('code_challenge_method', 'S256');
  
  // Open browser for user authorization
  await openBrowser(authUrl.toString());
  
  // Listen for callback on localhost
  const authCode = await waitForCallback();
  
  // Exchange authorization code for tokens
  const tokenResponse = await exchangeCodeForTokens({
    code: authCode,
    clientId: config.clientId,
    redirectUri: config.redirectUri,
    codeVerifier,
    tokenEndpoint: config.tokenEndpoint,
  });
  
  const credentials: OpenRouterCredentials = {
    accessToken: tokenResponse.access_token,
    refreshToken: tokenResponse.refresh_token,
    expiryDate: Date.now() + (tokenResponse.expires_in * 1000),
    createdAt: Date.now(),
  };
  
  await saveCredentials(credentials);
  return credentials;
}

function generateRandomString(length: number): string {
  const charset = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let result = '';
  const randomBytes = crypto.getRandomValues(new Uint8Array(length));
  
  for (let i = 0; i < length; i++) {
    result += charset[randomBytes[i] % charset.length];
  }
  
  return result;
}

async function generateCodeChallenge(verifier: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(verifier);
  const digest = await crypto.subtle.digest('SHA-256', data);
  
  return btoa(String.fromCharCode(...new Uint8Array(digest)))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '');
}

function openBrowser(url: string): Promise<void> {
  return new Promise((resolve) => {
    const platform = process.platform;
    let command: string;
    let args: string[];

    switch (platform) {
      case 'darwin':
        command = 'open';
        args = [url];
        break;
      case 'win32':
        command = 'cmd';
        args = ['/c', 'start', url];
        break;
      case 'linux':
        command = 'xdg-open';
        args = [url];
        break;
      default:
        throw new Error(`Unsupported platform: ${platform}`);
    }

    const child = spawn(command, args, { stdio: 'ignore', detached: true });
    child.unref?.();
    resolve();
  });
}

function waitForCallback(): Promise<string> {
  return new Promise((resolve, reject) => {
    // For now, we'll simulate this by reading from a file that would be written by the callback handler
    // In a real implementation, this would be an HTTP server listening for the redirect
    const checkFile = async () => {
      try {
        const content = await readFile('/tmp/openrouter_oauth_callback', 'utf-8');
        // Parse the callback file to extract the authorization code
        const match = content.match(/code=([^&]+)/);
        if (match) {
          resolve(match[1]);
          return;
        }
        reject(new Error('Invalid callback format'));
      } catch (err) {
        setTimeout(checkFile, 1000); // Check again in 1 second
      }
    };

    setTimeout(() => {
      reject(new Error('Timeout waiting for OAuth callback'));
    }, 300000); // 5 minute timeout

    checkFile();
  });
}

interface ExchangeCodeParams {
  code: string;
  clientId: string;
  redirectUri: string;
  codeVerifier: string;
  tokenEndpoint: string;
}

async function exchangeCodeForTokens(params: ExchangeCodeParams): Promise<OpenRouterTokenResponse> {
  const body = new URLSearchParams({
    grant_type: 'authorization_code',
    client_id: params.clientId,
    redirect_uri: params.redirectUri,
    code: params.code,
    code_verifier: params.codeVerifier,
  });

  const response = await fetch(params.tokenEndpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body,
  });

  if (!response.ok) {
    throw new Error(`Token exchange failed: ${response.status} ${response.statusText}`);
  }

  const data: OpenRouterTokenResponse = await response.json();
  return data;
}