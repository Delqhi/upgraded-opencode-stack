import http from "node:http";
import os from "node:os";
import { setTimeout as sleep } from "node:timers/promises";

const CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann";
const ISSUER = "https://auth.openai.com";
const CODEX_BASE_URL = "https://chatgpt.com/backend-api/codex";
const CODEX_API_ENDPOINT = `${CODEX_BASE_URL}/responses`;
const OAUTH_PORT = 1455;
const OAUTH_TIMEOUT_MS = 5 * 60 * 1000;
const OAUTH_POLLING_SAFETY_MARGIN_MS = 3000;
const ALLOWED_MODELS = new Set([
  "gpt-5-codex",
  "gpt-5.1-codex",
  "gpt-5.1-codex-max",
  "gpt-5.1-codex-mini",
  "gpt-5.2",
  "gpt-5.2-codex",
  "gpt-5.3-codex",
  "gpt-5.4",
  "gpt-5.4-fast",
  "gpt-5.4-mini",
  "gpt-5.4-mini-fast",
  "gpt-5.5",
  "gpt-5.5-fast",
  "gpt-5.5-pro",
]);
const OAUTH_DUMMY_KEY = "oauth";

let oauthServer;
let pendingOAuth;

function base64UrlEncode(buffer) {
  return Buffer.from(buffer)
    .toString("base64")
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
}

function generateRandomString(length) {
  const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~";
  const bytes = crypto.getRandomValues(new Uint8Array(length));
  return Array.from(bytes)
    .map((b) => chars[b % chars.length])
    .join("");
}

async function generatePKCE() {
  const verifier = generateRandomString(43);
  const hash = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(verifier));
  return { verifier, challenge: base64UrlEncode(hash) };
}

function generateState() {
  return base64UrlEncode(crypto.getRandomValues(new Uint8Array(32)));
}

function parseJwtClaims(token) {
  if (typeof token !== "string") return undefined;
  const parts = token.split(".");
  if (parts.length !== 3) return undefined;
  try {
    return JSON.parse(Buffer.from(parts[1], "base64url").toString("utf8"));
  } catch {
    return undefined;
  }
}

function extractAccountIdFromClaims(claims) {
  return (
    claims?.chatgpt_account_id ||
    claims?.["https://api.openai.com/auth"]?.chatgpt_account_id ||
    claims?.organizations?.[0]?.id
  );
}

function extractAccountId(tokens) {
  return (
    extractAccountIdFromClaims(parseJwtClaims(tokens?.id_token)) ||
    extractAccountIdFromClaims(parseJwtClaims(tokens?.access_token))
  );
}

function buildAuthorizeUrl(redirectUri, pkce, state) {
  const params = new URLSearchParams({
    response_type: "code",
    client_id: CLIENT_ID,
    redirect_uri: redirectUri,
    scope: "openid profile email offline_access",
    code_challenge: pkce.challenge,
    code_challenge_method: "S256",
    id_token_add_organizations: "true",
    codex_cli_simplified_flow: "true",
    state,
    originator: "opencode",
  });
  return `${ISSUER}/oauth/authorize?${params.toString()}`;
}

async function exchangeCodeForTokens(code, redirectUri, pkce) {
  const response = await fetch(`${ISSUER}/oauth/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "authorization_code",
      code,
      redirect_uri: redirectUri,
      client_id: CLIENT_ID,
      code_verifier: pkce.verifier,
    }).toString(),
  });
  if (!response.ok) {
    throw new Error(`Token exchange failed: ${response.status}`);
  }
  return response.json();
}

async function refreshAccessToken(refreshToken) {
  const response = await fetch(`${ISSUER}/oauth/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "refresh_token",
      refresh_token: refreshToken,
      client_id: CLIENT_ID,
    }).toString(),
  });
  if (!response.ok) {
    throw new Error(`Token refresh failed: ${response.status}`);
  }
  return response.json();
}

function startOAuthServer() {
  if (oauthServer) {
    return { port: OAUTH_PORT, redirectUri: `http://localhost:${OAUTH_PORT}/auth/callback` };
  }

  oauthServer = http.createServer((req, res) => {
    const url = new URL(req.url || "/", `http://localhost:${OAUTH_PORT}`);

    if (url.pathname === "/auth/callback") {
      const code = url.searchParams.get("code");
      const state = url.searchParams.get("state");
      const error = url.searchParams.get("error");
      const errorDescription = url.searchParams.get("error_description");

      if (error) {
        pendingOAuth?.reject(new Error(errorDescription || error));
        pendingOAuth = undefined;
        res.writeHead(200, { "Content-Type": "text/html" });
        res.end("<html><body><h1>Authorization failed</h1></body></html>");
        return;
      }

      if (!code || !pendingOAuth || state !== pendingOAuth.state) {
        pendingOAuth?.reject(new Error("Invalid OAuth callback state"));
        pendingOAuth = undefined;
        res.writeHead(400, { "Content-Type": "text/html" });
        res.end("<html><body><h1>Invalid OAuth callback</h1></body></html>");
        return;
      }

      const current = pendingOAuth;
      pendingOAuth = undefined;
      exchangeCodeForTokens(code, `http://localhost:${OAUTH_PORT}/auth/callback`, current.pkce)
        .then((tokens) => current.resolve(tokens))
        .catch((err) => current.reject(err));

      res.writeHead(200, { "Content-Type": "text/html" });
      res.end(
        "<html><body><h1>Authorization successful</h1><script>setTimeout(()=>window.close(),1500)</script></body></html>",
      );
      return;
    }

    res.writeHead(404);
    res.end("Not found");
  });

  oauthServer.listen(OAUTH_PORT);
  return { port: OAUTH_PORT, redirectUri: `http://localhost:${OAUTH_PORT}/auth/callback` };
}

function stopOAuthServer() {
  if (oauthServer) {
    oauthServer.close();
    oauthServer = undefined;
  }
}

function waitForOAuthCallback(pkce, state) {
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      if (pendingOAuth) {
        pendingOAuth = undefined;
        reject(new Error("OAuth callback timeout"));
      }
    }, OAUTH_TIMEOUT_MS);

    pendingOAuth = {
      pkce,
      state,
      resolve(tokens) {
        clearTimeout(timeout);
        resolve(tokens);
      },
      reject(error) {
        clearTimeout(timeout);
        reject(error);
      },
    };
  });
}

async function getFreshAuth(getAuth, inputClient) {
  const currentAuth = await getAuth();
  if (currentAuth?.type !== "oauth") return currentAuth;

  if (currentAuth.access && currentAuth.expires && currentAuth.expires > Date.now() + 15_000) {
    return currentAuth;
  }

  const tokens = await refreshAccessToken(currentAuth.refresh);
  const accountId = extractAccountId(tokens) || currentAuth.accountId;
  const nextAuth = {
    type: "oauth",
    refresh: tokens.refresh_token,
    access: tokens.access_token,
    expires: Date.now() + (tokens.expires_in ?? 3600) * 1000,
    ...(accountId ? { accountId } : {}),
  };

  await inputClient.auth.set({
    path: { id: "openai" },
    body: nextAuth,
  });

  return nextAuth;
}

function shouldRouteModel(modelId) {
  return ALLOWED_MODELS.has(String(modelId || "").trim());
}

function buildModel(id, name, limit, reasoning = true) {
  return {
    id,
    name,
    reasoning,
    limit,
    cost: { input: 0, output: 0, cache: { read: 0, write: 0 } },
    modalities: { input: ["text", "image"], output: ["text"] },
  };
}

export default async function OpenAICodexBridgePlugin(input) {
  return {
    auth: {
      provider: "openai",
      async loader(getAuth) {
        const auth = await getAuth();
        if (auth?.type !== "oauth") return {};

        return {
          apiKey: OAUTH_DUMMY_KEY,
          baseURL: CODEX_BASE_URL,
          async fetch(requestInput, init) {
            const authNow = await getFreshAuth(getAuth, input.client);
            if (authNow?.type !== "oauth") {
              return fetch(requestInput, init);
            }

            const request = new Request(requestInput, init);
            const headers = new Headers(request.headers);
            headers.delete("authorization");
            headers.delete("Authorization");
            headers.set("authorization", `Bearer ${authNow.access}`);
            headers.set("originator", "opencode");
            headers.set(
              "User-Agent",
              `opencode/${os.platform()} ${os.release()}; ${os.arch()}`,
            );

            const modelId = headers.get("x-model") || headers.get("x-opencode-model") || "";
            if (authNow.accountId) {
              headers.set("ChatGPT-Account-Id", authNow.accountId);
            }

            const parsed = new URL(request.url);
            const url =
              shouldRouteModel(modelId) ||
              parsed.pathname.includes("/v1/responses") ||
              parsed.pathname.includes("/chat/completions")
                ? CODEX_API_ENDPOINT
                : request.url;

            return fetch(url, {
              method: request.method,
              headers,
              body:
                request.method === "GET" || request.method === "HEAD"
                  ? undefined
                  : request.body,
              duplex: request.body ? "half" : undefined,
              signal: request.signal,
              redirect: request.redirect,
            });
          },
        };
      },
      methods: [
        {
          label: "ChatGPT Pro/Plus (browser)",
          type: "oauth",
          authorize: async () => {
            const { redirectUri } = startOAuthServer();
            const pkce = await generatePKCE();
            const state = generateState();
            const authUrl = buildAuthorizeUrl(redirectUri, pkce, state);
            const callbackPromise = waitForOAuthCallback(pkce, state);

            return {
              url: authUrl,
              instructions: "Complete authorization in your browser.",
              method: "auto",
              callback: async () => {
                const tokens = await callbackPromise;
                stopOAuthServer();
                return {
                  type: "success",
                  refresh: tokens.refresh_token,
                  access: tokens.access_token,
                  expires: Date.now() + (tokens.expires_in ?? 3600) * 1000,
                  accountId: extractAccountId(tokens),
                };
              },
            };
          },
        },
        {
          label: "ChatGPT Pro/Plus (device code)",
          type: "oauth",
          authorize: async () => {
            const deviceResponse = await fetch(`${ISSUER}/api/accounts/deviceauth/usercode`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ client_id: CLIENT_ID }),
            });
            if (!deviceResponse.ok) throw new Error("Failed to initiate device authorization");

            const deviceData = await deviceResponse.json();
            const interval = Math.max(Number.parseInt(deviceData.interval || "5", 10) || 5, 1) * 1000;

            return {
              url: `${ISSUER}/codex/device`,
              instructions: `Enter code: ${deviceData.user_code}`,
              method: "auto",
              callback: async () => {
                while (true) {
                  const response = await fetch(`${ISSUER}/api/accounts/deviceauth/token`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                      device_auth_id: deviceData.device_auth_id,
                      user_code: deviceData.user_code,
                    }),
                  });

                  if (response.ok) {
                    const data = await response.json();
                    const tokenResponse = await fetch(`${ISSUER}/oauth/token`, {
                      method: "POST",
                      headers: { "Content-Type": "application/x-www-form-urlencoded" },
                      body: new URLSearchParams({
                        grant_type: "authorization_code",
                        code: data.authorization_code,
                        redirect_uri: `${ISSUER}/deviceauth/callback`,
                        client_id: CLIENT_ID,
                        code_verifier: data.code_verifier,
                      }).toString(),
                    });
                    if (!tokenResponse.ok) {
                      throw new Error(`Token exchange failed: ${tokenResponse.status}`);
                    }
                    const tokens = await tokenResponse.json();
                    return {
                      type: "success",
                      refresh: tokens.refresh_token,
                      access: tokens.access_token,
                      expires: Date.now() + (tokens.expires_in ?? 3600) * 1000,
                      accountId: extractAccountId(tokens),
                    };
                  }

                  if (response.status !== 403 && response.status !== 404) {
                    return { type: "failed" };
                  }

                  await sleep(interval + OAUTH_POLLING_SAFETY_MARGIN_MS);
                }
              },
            };
          },
        },
      ],
    },
    provider: {
      id: "openai",
      async models(provider) {
        return {
          ...(provider.models || {}),
          "gpt-5.5": provider.models?.["gpt-5.5"] || buildModel("gpt-5.5", "GPT-5.5", { context: 1000000, output: 32768 }),
          "gpt-5.5-fast": provider.models?.["gpt-5.5-fast"] || buildModel("gpt-5.5-fast", "GPT-5.5 Fast", { context: 1000000, output: 32768 }, false),
          "gpt-5.5-pro": provider.models?.["gpt-5.5-pro"] || buildModel("gpt-5.5-pro", "GPT-5.5 Pro", { context: 1000000, output: 32768 }),
        };
      },
    },
    "chat.headers": async (inputCtx, output) => {
      if (inputCtx.model.providerID !== "openai") return;
      output.headers.originator = "opencode";
      output.headers["x-opencode-model"] = inputCtx.model.modelID;
      output.headers["User-Agent"] = `opencode (${os.platform()} ${os.release()}; ${os.arch()})`;
      output.headers.session_id = inputCtx.sessionID;
    },
  };
}
