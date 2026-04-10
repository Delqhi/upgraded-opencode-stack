import type { CreatedHooks } from "../create-hooks";
type CommandExecuteBeforeInput = {
    command: string;
    sessionID: string;
    arguments: string;
};
type CommandExecuteBeforeOutput = {
    parts: Array<{
        type: string;
        text?: string;
        [key: string]: unknown;
    }>;
};
export declare function createCommandExecuteBeforeHandler(args: {
    hooks: CreatedHooks;
}): (input: CommandExecuteBeforeInput, output: CommandExecuteBeforeOutput) => Promise<void>;
export {};
