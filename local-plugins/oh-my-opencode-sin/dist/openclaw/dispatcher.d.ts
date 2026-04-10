import type { OpenClawGateway } from "./types";
export declare function validateGatewayUrl(url: string): boolean;
export declare function interpolateInstruction(template: string, variables: Record<string, string | undefined>): string;
export declare function shellEscapeArg(value: string): string;
export declare function resolveCommandTimeoutMs(gatewayTimeout?: number, envTimeoutRaw?: string | undefined): number;
export declare function wakeGateway(gatewayName: string, gatewayConfig: OpenClawGateway, payload: unknown): Promise<{
    gateway: string;
    success: boolean;
    error?: string;
    statusCode?: number;
}>;
export declare function wakeCommandGateway(gatewayName: string, gatewayConfig: OpenClawGateway, variables: Record<string, string | undefined>): Promise<{
    gateway: string;
    success: boolean;
    error?: string;
}>;
type KillableProcess = {
    pid?: number;
    kill: (signal?: NodeJS.Signals) => void;
};
export declare function terminateCommandProcess(proc: KillableProcess, signal: NodeJS.Signals): void;
export {};
