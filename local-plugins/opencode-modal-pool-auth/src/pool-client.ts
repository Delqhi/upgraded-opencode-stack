import { DEFAULT_POOL_ADMIN_BASE_URL, DEFAULT_POOL_TIMEOUT_MS } from "./constants";

type LeaseResponse = {
  api_key: string | null;
  source?: string;
  error?: string;
  retry_after?: number;
};

export class PoolClient {
  constructor(
    private readonly baseUrl: string = process.env.MODAL_POOL_URL ?? DEFAULT_POOL_ADMIN_BASE_URL,
    private readonly timeoutMs: number = Number(process.env.MODAL_POOL_TIMEOUT_MS ?? DEFAULT_POOL_TIMEOUT_MS),
    private readonly gatewayKey: string = process.env.MODAL_GATEWAY_KEY || "sk-sin-fleet-master",
    private readonly masterKey: string = process.env.MODAL_POOL_MASTER_KEY || "sk-modal-pool-2026",
  ) {}

  async checkout(sessionId: string, label = ""): Promise<LeaseResponse> {
    const url = new URL("pool/checkout", this.withSlash(this.baseUrl));
    url.searchParams.set("session_id", sessionId);
    if (label) url.searchParams.set("label", label);
    return this.request(url.toString(), { method: "GET" });
  }

  async reportRateLimited(sessionId: string, apiKey: string): Promise<LeaseResponse> {
    const url = new URL("pool/rate-limited", this.withSlash(this.baseUrl));
    url.searchParams.set("session_id", sessionId);
    url.searchParams.set("api_key", apiKey);
    return this.request(url.toString(), { method: "POST" });
  }

  async returnKey(sessionId: string): Promise<LeaseResponse> {
    const url = new URL("pool/return", this.withSlash(this.baseUrl));
    url.searchParams.set("session_id", sessionId);
    return this.request(url.toString(), { method: "POST" });
  }

  async addKey(apiKey: string, label: string): Promise<void> {
    if (!this.masterKey) {
      throw new Error("MODAL_POOL_MASTER_KEY is required");
    }
    const url = new URL("pool/keys", this.withSlash(this.baseUrl));
    url.searchParams.set("api_key", apiKey);
    if (label) url.searchParams.set("label", label);
    url.searchParams.set("master", this.masterKey);
    await this.request(url.toString(), { method: "POST" });
  }

  private withSlash(value: string): string {
    return value.endsWith("/") ? value : `${value}/`;
  }

  private async request(url: string, init: RequestInit): Promise<any> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeoutMs);
    try {
      const headers = new Headers(init.headers ?? {});
      if (this.gatewayKey) headers.set("authorization", `Bearer ${this.gatewayKey}`);
      const response = await fetch(url, { ...init, headers, signal: controller.signal });
      const text = await response.text();
      const data = text ? JSON.parse(text) : {};
      if (!response.ok) {
        throw new Error(`pool request failed ${response.status}: ${text}`);
      }
      return data;
    } finally {
      clearTimeout(timer);
    }
  }
}
