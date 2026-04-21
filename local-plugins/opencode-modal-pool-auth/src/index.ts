import {
  DEFAULT_COOLDOWN_SECONDS,
  DEFAULT_MAX_RETRIES,
  DEFAULT_MODAL_BASE_URL,
  DEFAULT_POOL_TIMEOUT_MS,
  DEFAULT_WAIT_TIMEOUT_SECONDS,
  PROVIDER_ID,
} from "./constants";
import { PoolClient } from "./pool-client";

type ApiAuth = { type: string; key?: string };
type SessionState = { apiKey: string; retryAfter?: number; };

const poolClient = new PoolClient(
  process.env.MODAL_POOL_URL || undefined,
  Number(process.env.MODAL_POOL_TIMEOUT_MS || DEFAULT_POOL_TIMEOUT_MS),
  process.env.MODAL_GATEWAY_KEY || undefined,
  process.env.MODAL_POOL_MASTER_KEY || undefined,
);
const sessionState = new Map<string, SessionState>();
let activeSessionId = process.env.OPENCODE_SESSION_ID ?? `pid-${process.pid}`;

function toUrlString(input: RequestInfo | URL): string {
  if (typeof input === "string") return input;
  if (input instanceof URL) return input.toString();
  return input.url;
}

function isModalRequest(input: RequestInfo | URL): boolean {
  return toUrlString(input).startsWith(process.env.MODAL_BASE_URL ?? DEFAULT_MODAL_BASE_URL);
}

function resolveSessionId(input?: RequestInfo | URL, init?: RequestInit): string {
  const headers = new Headers(init?.headers ?? (input instanceof Request ? input.headers : undefined));
  return headers.get("x-opencode-session-id") ?? headers.get("x-session-id") ?? activeSessionId;
}

function withModalAuth(request: Request, apiKey: string): Request {
  const headers = new Headers(request.headers);
  headers.set("authorization", `Bearer ${apiKey}`);
  headers.set("api-key", apiKey);
  return new Request(request, { headers });
}

async function isRateLimitResponse(response: Response): Promise<boolean> {
  if (response.status === 429) return true;
  const body = (await response.clone().text()).toLowerCase();
  return body.includes("too many concurrent requests") || (body.includes("rate") && body.includes("limit"));
}

async function ensureSessionKey(sessionId: string): Promise<SessionState> {
  const existing = sessionState.get(sessionId);
  if (existing) return existing;
  
  while (true) {
    // WICHTIG: Wir pollen den Pool so lange, bis ein Key wirklich frei ist.
    // Ohne diese Schleife wirft der Plugin-Loader sofort einen Error und die
    // laufende opencode-Session stirbt, obwohl der Pool nur kurz erschöpft ist.
    const lease = await poolClient.checkout(sessionId, `session-${sessionId}`);
    if (lease.api_key) {
      const next = { apiKey: lease.api_key };
      sessionState.set(sessionId, next);
      return next;
    }
    
    if (lease.retry_after) {
      // retry_after kommt vom Pool und ist die kanonische Wartezeit. Wir
      // respektieren sie exakt, statt lokal irgendwelche geratenen Backoffs
      // zu erfinden, damit der Plugin-Prozess und der Pool synchron bleiben.
      await new Promise(r => setTimeout(r, lease.retry_after! * 1000));
      continue;
    }
    
    throw new Error(`No Modal API keys available in pool`);
  }
}

async function rotateSessionKey(sessionId: string, previousApiKey: string): Promise<SessionState> {
  while (true) {
    // Diese Rotation darf NICHT einfach fehlschlagen, wenn gerade alle Keys in
    // Cooldown sind. Sonst endet ein einzelnes 429 sofort in einem User-Error,
    // obwohl der Pool wenige Sekunden später wieder einen Key liefern könnte.
    const lease = await poolClient.reportRateLimited(sessionId, previousApiKey);
    if (lease.api_key) {
      const next = { apiKey: lease.api_key };
      sessionState.set(sessionId, next);
      return next;
    }
    
    if (lease.retry_after) {
      // Auch nach einem Rate-Limit vertrauen wir auf die Pool-seitige Retry-Zeit,
      // damit alle Sessions denselben globalen Cooldown respektieren.
      await new Promise(r => setTimeout(r, lease.retry_after! * 1000));
      continue;
    }
    
    throw new Error(`No Modal API keys available in pool`);
  }
}

async function releaseSession(sessionId: string): Promise<void> {
  if (!sessionState.has(sessionId)) return;
  sessionState.delete(sessionId);
  try {
    await poolClient.returnKey(sessionId);
  } catch {}
}

export const ModalPoolAuthPlugin = async (_input: unknown) => {
  return {
    event: async (input: any) => {
      const eventType = input?.event?.type;
      const properties = input?.properties ?? {};
      if (eventType === "session.created") {
        const sessionID = properties.sessionID ?? properties?.info?.id;
        if (sessionID) activeSessionId = String(sessionID);
      }
      if (eventType === "session.closed" || eventType === "session.stopped") {
        const sessionID = properties.sessionID;
        if (sessionID) await releaseSession(String(sessionID));
      }
    },
    auth: {
      provider: PROVIDER_ID,
      loader: async (_getAuth: () => Promise<ApiAuth>) => {
        return {
          apiKey: "",
          baseURL: process.env.MODAL_BASE_URL ?? DEFAULT_MODAL_BASE_URL,
          fetch: async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
            if (!isModalRequest(input)) return fetch(input, init);
            const sessionId = resolveSessionId(input, init);
            const baseRequest = new Request(input, init);
            let current = await ensureSessionKey(sessionId);
            let attempts = 0;
            while (true) {
              const authedRequest = withModalAuth(baseRequest.clone(), current.apiKey);
              const response = await fetch(authedRequest);
              if (!(await isRateLimitResponse(response))) {
                return response;
              }
              attempts += 1;
              if (attempts > Number(process.env.MODAL_POOL_MAX_RETRIES ?? DEFAULT_MAX_RETRIES)) {
                return response;
              }
              current = await rotateSessionKey(sessionId, current.apiKey);
            }
          },
        };
      },
      methods: [
        {
          type: "api" as const,
          label: "Modal API key -> GLM pool",
          prompts: [
            {
              type: "text" as const,
              key: "api_key",
              message: "Modal API key",
              placeholder: "modalresearch_...",
              validate: (value: string) =>
                value.startsWith("modalresearch_") ? undefined : "Expected modalresearch_... key",
            },
            {
              type: "text" as const,
              key: "label",
              message: "Optional label",
              placeholder: "modal-key-3",
            },
          ],
          authorize: async (inputs?: Record<string, string>) => {
            const apiKey = inputs?.api_key?.trim() ?? "";
            const label = inputs?.label?.trim() ?? "";
            if (!apiKey) return { type: "failed" as const };
            await poolClient.addKey(apiKey, label);
            return {
              type: "success" as const,
              key: process.env.MODAL_GATEWAY_KEY ?? apiKey,
              provider: PROVIDER_ID,
            };
          },
        },
      ],
    },
    config: async (config: Record<string, any>) => {
      const providers = (config.provider as Record<string, any>) ?? {};
      if (!providers[PROVIDER_ID]) {
        providers[PROVIDER_ID] = {
          npm: "@ai-sdk/openai-compatible",
          options: {
            baseURL: process.env.MODAL_BASE_URL ?? DEFAULT_MODAL_BASE_URL,
          },
        };
      }
      config.provider = providers;
    },
  };
};

process.on("exit", () => {
  for (const sessionId of sessionState.keys()) {
    void releaseSession(sessionId);
  }
});

export default ModalPoolAuthPlugin;
