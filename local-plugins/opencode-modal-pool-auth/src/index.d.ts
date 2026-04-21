type ApiAuth = {
    type: string;
    key?: string;
};
export declare const ModalPoolAuthPlugin: (_input: unknown) => Promise<{
    event: (input: any) => Promise<void>;
    auth: {
        provider: any;
        loader: (_getAuth: () => Promise<ApiAuth>) => Promise<{
            apiKey: string;
            baseURL: any;
            fetch: (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>;
        }>;
        methods: {
            type: "api";
            label: string;
            prompts: ({
                type: "text";
                key: string;
                message: string;
                placeholder: string;
                validate: (value: string) => "Expected modalresearch_... key" | undefined;
            } | {
                type: "text";
                key: string;
                message: string;
                placeholder: string;
                validate?: never;
            })[];
            authorize: (inputs?: Record<string, string>) => Promise<{
                type: "failed";
                key?: never;
                provider?: never;
            } | {
                type: "success";
                key: any;
                provider: any;
            }>;
        }[];
    };
    config: (config: Record<string, any>) => Promise<void>;
}>;
export default ModalPoolAuthPlugin;
//# sourceMappingURL=index.d.ts.map