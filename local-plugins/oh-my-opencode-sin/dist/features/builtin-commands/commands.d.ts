import type { BuiltinCommandName, BuiltinCommands } from "./types";
export interface LoadBuiltinCommandsOptions {
    useRegisteredAgents?: boolean;
}
export declare function loadBuiltinCommands(disabledCommands?: BuiltinCommandName[], options?: LoadBuiltinCommandsOptions): BuiltinCommands;
