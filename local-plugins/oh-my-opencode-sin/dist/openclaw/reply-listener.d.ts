import type { OpenClawConfig } from "./types";
export declare const DAEMON_IDENTITY_MARKER = "--openclaw-reply-listener-daemon";
export declare function logReplyListenerMessage(message: string): void;
interface DaemonState {
    isRunning: boolean;
    pid: number | null;
    startedAt: string;
    lastPollAt: string | null;
    telegramLastUpdateId: number | null;
    discordLastMessageId: string | null;
    messagesInjected: number;
    errors: number;
    lastError?: string;
}
export declare function isReplyListenerProcess(pid: number): Promise<boolean>;
export declare function isDaemonRunning(): Promise<boolean>;
export declare function sanitizeReplyInput(text: string): string;
export declare function pollLoop(): Promise<void>;
export declare function startReplyListener(config: OpenClawConfig): Promise<{
    success: boolean;
    message: string;
    state?: DaemonState;
    error?: string;
}>;
export declare function stopReplyListener(): Promise<{
    success: boolean;
    message: string;
    state?: DaemonState;
    error?: string;
}>;
export {};
