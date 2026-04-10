import type { ModelFallbackState } from "./hook";
export declare function getNextReachableFallback(sessionID: string, state: ModelFallbackState): {
    providerID: string;
    modelID: string;
    variant?: string;
} | null;
