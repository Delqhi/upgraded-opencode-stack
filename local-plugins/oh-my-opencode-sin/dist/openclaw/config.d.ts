import type { OpenClawConfig, OpenClawGateway } from "./types";
export declare function normalizeReplyListenerConfig(config: OpenClawConfig): OpenClawConfig;
export declare function resolveGateway(config: OpenClawConfig, event: string): {
    gatewayName: string;
    gateway: OpenClawGateway;
    instruction: string;
} | null;
export declare function validateGatewayUrl(url: string): boolean;
