type LeaseResponse = {
    api_key: string | null;
    source?: string;
    error?: string;
    retry_after?: number;
};
export declare class PoolClient {
    private readonly baseUrl;
    private readonly timeoutMs;
    private readonly gatewayKey;
    private readonly masterKey;
    constructor(baseUrl?: string, timeoutMs?: number, gatewayKey?: string, masterKey?: string);
    checkout(sessionId: string, label?: string): Promise<LeaseResponse>;
    reportRateLimited(sessionId: string, apiKey: string): Promise<LeaseResponse>;
    returnKey(sessionId: string): Promise<LeaseResponse>;
    addKey(apiKey: string, label: string): Promise<void>;
    private withSlash;
    private request;
}
export {};
//# sourceMappingURL=pool-client.d.ts.map