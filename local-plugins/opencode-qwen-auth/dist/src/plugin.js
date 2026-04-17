import { QWEN_DEFAULT_SCOPES, QWEN_OAUTH_BASE_URL } from "./constants";
import { getMinRateLimitWait, loadAccounts, lockedSelectAndSave, markRateLimited, recordFailure, recordSuccess, saveAccounts, selectAccount, updateAccount, upsertAccount, } from "./plugin/account";
import { accessTokenExpired, isOAuthAuth } from "./plugin/auth";
import { loadConfig } from "./plugin/config";
import { createLogger, initDebugFromEnv, setLoggerQuietMode, } from "./plugin/logger";
import { getHealthTracker, getTokenTracker, initHealthTracker, initTokenTracker, } from "./plugin/rotation";
import { refreshAccessToken } from "./plugin/token";
import { authorizeQwenDevice, pollQwenDeviceToken, } from "./qwen/oauth";
import { transformResponsesToChatCompletions } from "./transform/request";
import { createTransformContext, transformChatCompletionsToResponses, } from "./transform/response";
import { createSSETransformContext, createSSETransformStream, } from "./transform/sse";
const logger = createLogger("plugin");
// Dead Qwen refresh tokens should not re-enter rotation immediately.
// Once Qwen marks a refresh token invalid, the only real recovery is a fresh
// `providers login` flow, so a long cooldown prevents endless reuse loops.
const INVALID_AUTH_COOLDOWN_MS = 24 * 60 * 60 * 1000;
const UNSUPPORTED_QWEN_REQUEST_FIELDS = [
    "allowAll",
    "autoAccept",
    "confirm",
    "fallback",
];
function normalizeUrl(value, fallback) {
    if (typeof value !== "string") {
        return fallback;
    }
    const trimmed = value.trim();
    if (!trimmed)
        return fallback;
    if (trimmed.startsWith("http://") || trimmed.startsWith("https://")) {
        return trimmed;
    }
    return `https://${trimmed}`;
}
function buildOAuthOptions(config) {
    return {
        clientId: config.client_id,
        oauthBaseUrl: normalizeUrl(config.oauth_base_url, QWEN_OAUTH_BASE_URL),
        scopes: QWEN_DEFAULT_SCOPES,
    };
}
function ensureStorage(auth) {
    return {
        version: 1,
        accounts: [
            {
                refreshToken: auth.refresh,
                accessToken: auth.access,
                expires: auth.expires,
                resourceUrl: auth.resourceUrl,
                addedAt: Date.now(),
                lastUsed: Date.now(),
            },
        ],
        activeIndex: 0,
    };
}
function sanitizeMalformedUrl(url) {
    let result = url.trim();
    // Strip leading sentinel prefix (undefined/null) only at start
    // OpenCode may pass "undefined/chat/completions" when provider has no baseUrl
    result = result.replace(/^(undefined|null)(?=\/|$)/, "");
    // Prevent protocol-relative URL after stripping (e.g., "undefined//path" -> "//path" is dangerous)
    // Collapse multiple leading slashes to single slash
    if (result.startsWith("//")) {
        result = `/${result.replace(/^\/+/, "")}`;
    }
    return result;
}
function applyResourceUrl(input, baseUrl) {
    let rawUrl;
    if (typeof input === "string") {
        rawUrl = input;
    }
    else if (input instanceof URL) {
        rawUrl = input.toString();
    }
    else {
        rawUrl = input.url;
    }
    // Sanitize malformed URLs from OpenCode (e.g., "undefined/chat/completions")
    rawUrl = sanitizeMalformedUrl(rawUrl);
    // If sanitization resulted in empty string, treat as root path
    if (!rawUrl) {
        rawUrl = "/";
    }
    let originalUrl;
    try {
        originalUrl = new URL(rawUrl);
    }
    catch {
        if (!baseUrl) {
            throw new Error(`Qwen OAuth requires a base URL for ${rawUrl}`);
        }
        originalUrl = new URL(rawUrl, baseUrl);
    }
    if (!baseUrl) {
        return { url: originalUrl.toString() };
    }
    const base = new URL(baseUrl);
    const basePath = base.pathname.replace(/\/$/, "");
    const originalPath = originalUrl.pathname;
    let combinedPath = originalPath;
    if (originalPath.startsWith(basePath)) {
        combinedPath = `${basePath}${originalPath.slice(basePath.length)}`;
    }
    else {
        combinedPath = `${basePath}${originalPath.startsWith("/") ? "" : "/"}${originalPath}`;
    }
    base.pathname = combinedPath;
    base.search = originalUrl.search;
    base.hash = originalUrl.hash;
    return { url: base.toString() };
}
function extractRetryAfterMs(response) {
    const retryAfterMs = response.headers.get("retry-after-ms");
    if (retryAfterMs) {
        const value = Number.parseInt(retryAfterMs, 10);
        if (!Number.isNaN(value) && value > 0) {
            return value;
        }
    }
    const retryAfter = response.headers.get("retry-after");
    if (retryAfter) {
        const value = Number.parseInt(retryAfter, 10);
        if (!Number.isNaN(value) && value > 0) {
            return value * 1000;
        }
    }
    return null;
}
const BACKOFF_TIERS = {
    QUOTA_EXHAUSTED: [60_000, 300_000, 1800_000],
    RATE_LIMIT_EXCEEDED: [30_000, 60_000],
    SERVER_ERROR: [20_000, 40_000],
    UNKNOWN: [60_000],
};
function parseRateLimitReason(response) {
    const errorHeader = response.headers.get("x-error-code");
    if (errorHeader) {
        const upper = errorHeader.toUpperCase();
        if (upper.includes("QUOTA"))
            return "QUOTA_EXHAUSTED";
        if (upper.includes("RATE"))
            return "RATE_LIMIT_EXCEEDED";
        if (upper.includes("SERVER") || upper.includes("CAPACITY"))
            return "SERVER_ERROR";
    }
    if (response.status >= 500)
        return "SERVER_ERROR";
    return "UNKNOWN";
}
function getBackoffMs(reason, consecutiveFailures) {
    const tier = BACKOFF_TIERS[reason];
    return tier[Math.min(consecutiveFailures, tier.length - 1)];
}
function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}
function stripUnsupportedQwenRequestFields(payload) {
    if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
        return payload;
    }
    const cleaned = { ...payload };
    for (const key of UNSUPPORTED_QWEN_REQUEST_FIELDS) {
        delete cleaned[key];
    }
    return cleaned;
}
// Codes that indicate a refresh token is permanently dead and the account
// should be quarantined for INVALID_AUTH_COOLDOWN_MS (24h).
// - invalid_grant / invalid_request: Qwen server says token is revoked/expired
// - waf_challenge: Aliyun WAF returned HTML instead of JSON (TLS fingerprint block)
// - parse_error: Response body was not valid JSON at all
function isInvalidRefreshCode(code) {
    return (code === "invalid_grant" ||
        code === "invalid_request" ||
        code === "waf_challenge" ||
        code === "parse_error");
}
// Hard cap on rotation attempts per single request to prevent hanging
// when hundreds/thousands of accounts have dead tokens. After this many
// consecutive failures the plugin throws immediately instead of trying
// every single account (which could take 90+ minutes with 2694 accounts).
const MAX_ROTATION_ATTEMPTS = 10;
function quarantineInvalidAccount(storage, index) {
    return updateAccount(storage, index, {
        accessToken: "",
        expires: 0,
        rateLimitResetAt: Date.now() + INVALID_AUTH_COOLDOWN_MS,
    });
}
function selectAuthorizationAuth(latestAuth, selectedAuth) {
    // `getAuth()` can lag behind a just-rotated or just-refreshed account.
    // Only prefer the externally stored auth record when it clearly refers to
    // the same refresh token and still has a live access token.
    if (!isOAuthAuth(latestAuth)) {
        return selectedAuth;
    }
    if (latestAuth.refresh === selectedAuth.refresh &&
        latestAuth.access &&
        !accessTokenExpired(latestAuth)) {
        return latestAuth;
    }
    return selectedAuth;
}
async function ensureAuthInStorage(storage, auth) {
    const now = Date.now();
    const baseStorage = storage ?? ensureStorage(auth);
    const updated = upsertAccount(baseStorage, {
        refreshToken: auth.refresh,
        accessToken: auth.access,
        expires: auth.expires,
        resourceUrl: auth.resourceUrl,
        addedAt: now,
        lastUsed: now,
    });
    await saveAccounts(updated);
    return updated;
}
function initializeTrackers(config) {
    initHealthTracker(config.health_score
        ? {
            initial: config.health_score.initial,
            successReward: config.health_score.success_reward,
            rateLimitPenalty: config.health_score.rate_limit_penalty,
            failurePenalty: config.health_score.failure_penalty,
            recoveryRatePerHour: config.health_score.recovery_rate_per_hour,
            minUsable: config.health_score.min_usable,
        }
        : undefined);
    initTokenTracker(config.token_bucket
        ? {
            maxTokens: config.token_bucket.max_tokens,
            regenerationRatePerMinute: config.token_bucket.regeneration_rate_per_minute,
        }
        : undefined);
}
function getPidOffset(config) {
    if (!config.pid_offset_enabled)
        return 0;
    return process.pid;
}
export const createQwenOAuthPlugin = (providerId) => async ({ client, directory }) => {
    const config = loadConfig(directory);
    setLoggerQuietMode(config.quiet_mode);
    initDebugFromEnv();
    initializeTrackers(config);
    const pidOffset = getPidOffset(config);
    logger.debug("Plugin initialized", {
        providerId,
        directory,
        strategy: config.rotation_strategy,
        pidOffset: config.pid_offset_enabled ? pidOffset : "disabled",
    });
    const oauthOptions = buildOAuthOptions(config);
    return {
        auth: {
            provider: providerId,
            async loader(getAuth, provider) {
                const auth = (await getAuth());
                if (!isOAuthAuth(auth)) {
                    return {};
                }
                let accountStorage = await ensureAuthInStorage(await loadAccounts(), auth);
                if (provider.models) {
                    for (const model of Object.values(provider.models)) {
                        if (model) {
                            model.cost = {
                                input: 0,
                                output: 0,
                                cache: { read: 0, write: 0 },
                            };
                        }
                    }
                }
                return {
                    apiKey: "",
                    fetch: async (input, init) => {
                        let attempts = 0;
                        const forcedRefreshTokens = new Set();
                        const healthTracker = getHealthTracker();
                        const tokenTracker = getTokenTracker();
                        const selectOptions = {
                            healthTracker,
                            tokenTracker,
                            pidOffset,
                        };
                        while (true) {
                            const now = Date.now();
                            // Atomic file-locked selection: loads fresh state from
                            // disk, selects an account, writes the updated activeIndex
                            // back — all under a single file lock. This prevents 12+
                            // concurrent sessions from picking the same account and
                            // burning single-use refresh tokens.
                            const selection = await lockedSelectAndSave(config.rotation_strategy, now, selectOptions);
                            if (!selection) {
                                // Reload fresh state for rate-limit wait calculation
                                const freshState = await loadAccounts();
                                if (freshState) accountStorage = freshState;
                                const waitMs = getMinRateLimitWait(accountStorage, now);
                                if (!waitMs) {
                                    throw new Error("No available Qwen OAuth accounts. Re-authenticate to continue.");
                                }
                                const maxWaitMs = (config.max_rate_limit_wait_seconds ?? 0) * 1000;
                                if (maxWaitMs > 0 && waitMs > maxWaitMs) {
                                    throw new Error("All Qwen OAuth accounts are rate-limited. Try again later.");
                                }
                                await sleep(waitMs);
                                continue;
                            }
                            accountStorage = selection.storage;
                            const account = selection.account;
                            const accountIndex = selection.index;
                            const authRecord = {
                                type: "oauth",
                                refresh: account.refreshToken,
                                access: account.accessToken,
                                expires: account.expires,
                                resourceUrl: account.resourceUrl,
                            };
                            let selectedAuth = authRecord;
                            const refreshBuffer = config.proactive_refresh
                                ? config.refresh_window_seconds
                                : 0;
                            if (!selectedAuth.access ||
                                accessTokenExpired(selectedAuth, refreshBuffer)) {
                                logger.debug("Token refresh needed", {
                                    accountIndex,
                                    hasAccess: !!selectedAuth.access,
                                    proactive: config.proactive_refresh,
                                });
                                try {
                                    // Multi-session concurrency fix: Check if another session already
                                    // refreshed this account while we were preparing to refresh. 
                                    // If the refresh token on disk has changed, we just grab the new 
                                    // tokens and retry instead of burning a single-use token twice.
                                    const freshStorage = await loadAccounts();
                                    const freshAccount = freshStorage?.accounts[accountIndex];
                                    if (freshAccount && freshAccount.refreshToken !== selectedAuth.refresh) {
                                        logger.debug("Another session already refreshed this token proactively. Retrying.", {
                                            accountIndex
                                        });
                                        accountStorage = freshStorage;
                                        continue;
                                    }

                                    const refreshed = await refreshAccessToken(selectedAuth, oauthOptions, client, providerId);
                                    if (!refreshed) {
                                        throw new Error("Token refresh failed");
                                    }
                                    logger.debug("Token refreshed successfully", {
                                        accountIndex,
                                    });
                                    accountStorage = updateAccount(accountStorage, accountIndex, {
                                        refreshToken: refreshed.refresh,
                                        accessToken: refreshed.access,
                                        expires: refreshed.expires,
                                        resourceUrl: refreshed.resourceUrl ?? account.resourceUrl,
                                        lastUsed: now,
                                    });
                                    await saveAccounts(accountStorage);
                                    selectedAuth = refreshed;
                                }
                                catch (error) {
                                    const refreshError = error;
                                    logger.debug("Token refresh failed", {
                                        accountIndex,
                                        code: refreshError.code,
                                    });
                                    if (isInvalidRefreshCode(refreshError.code)) {
                                        accountStorage = quarantineInvalidAccount(accountStorage, accountIndex);
                                        await saveAccounts(accountStorage);
                                    }
                                    attempts += 1;
                                    if (attempts >= MAX_ROTATION_ATTEMPTS) {
                                        throw error;
                                    }
                                    continue;
                                }
                            }
                            const latestAuth = (await getAuth());
                            if (!isOAuthAuth(latestAuth)) {
                                return fetch(input, init);
                            }
                            const activeAuth = selectAuthorizationAuth(latestAuth, selectedAuth);
                            // Get URL from input - OpenCode already constructs full URLs
                            let rawUrl;
                            if (typeof input === "string") {
                                rawUrl = input;
                            }
                            else if (input instanceof URL) {
                                rawUrl = input.toString();
                            }
                            else {
                                rawUrl = input.url;
                            }
                            // Sanitize malformed URLs (e.g., "undefined/path")
                            rawUrl = sanitizeMalformedUrl(rawUrl);
                            let requestInit = init ? { ...init } : {};
                            if (input instanceof Request) {
                                requestInit = {
                                    method: requestInit.method ?? input.method,
                                    headers: requestInit.headers ?? input.headers,
                                    body: requestInit.body ?? input.body,
                                    signal: requestInit.signal ?? input.signal,
                                    duplex: requestInit.duplex,
                                };
                            }
                            if (requestInit && !requestInit.headers) {
                                requestInit.headers = {};
                            }
                            logger.debug("Request init snapshot", {
                                inputType: input instanceof Request ? "request" : typeof input,
                                hasBody: !!requestInit?.body,
                                bodyType: requestInit?.body?.constructor?.name ?? typeof requestInit?.body,
                            });
                            const headers = new Headers(requestInit?.headers);
                            if (activeAuth.access) {
                                headers.set("Authorization", `Bearer ${activeAuth.access}`);
                            }
                            const needsResponsesTransform = rawUrl.endsWith("/responses");
                            const finalUrl = rawUrl.replace(/\/responses$/, "/chat/completions");
                            const finalInit = { ...requestInit };
                            if (needsResponsesTransform && requestInit?.body) {
                                try {
                                    const bodyStr = typeof requestInit.body === "string"
                                        ? requestInit.body
                                        : await new Response(requestInit.body).text();
                                    const body = JSON.parse(bodyStr);
                                    const transformed = transformResponsesToChatCompletions(body);
                                    finalInit.body = JSON.stringify(transformed);
                                    logger.verbose("Transformed request body", {
                                        messagesCount: transformed.messages?.length,
                                        hasTools: !!transformed.tools,
                                    });
                                }
                                catch {
                                    logger.debug("Body parse failed, using original");
                                }
                            }

                            headers.set("User-Agent", "QwenCode/0.11.1 (darwin; arm64)");
                            headers.set("X-DashScope-AuthType", "qwen-oauth");
                            headers.set("X-DashScope-CacheControl", "enable");
                            headers.set("X-DashScope-UserAgent", "QwenCode/0.11.1 (darwin; arm64)");
                            if (finalInit.body) {
                                try {
                                    const bodyText = typeof finalInit.body === "string"
                                        ? finalInit.body
                                        : await new Response(finalInit.body).text();
                                    const parsed = stripUnsupportedQwenRequestFields(JSON.parse(bodyText));
                                    const msgs = parsed.messages || [];
                                    const magicSystemMsg = "You are Qwen Code, an interactive CLI agent developed by Alibaba Group, specializing in software engineering tasks. Your primary goal is to help users safely and efficiently, adhering strictly to the following instructions and utilizing your available tools.";
                                    if (!msgs.some(m => m.role === "system" && m.content.includes("You are Qwen Code"))) {
                                        parsed.messages = [{ role: "system", content: magicSystemMsg }, ...msgs];
                                    }
                                    if (parsed.max_tokens && parsed.max_tokens > 8192) {
                                        parsed.max_tokens = 8192;
                                    }
                                    logger.debug("Prepared request body", {
                                        model: parsed.model,
                                        keys: Object.keys(parsed),
                                    });
                                    finalInit.body = JSON.stringify(parsed);
                                }
                                catch (error) {
                                    logger.debug("Request body normalization skipped", {
                                        error: error instanceof Error ? error.message : String(error),
                                    });
                                }
                            }
                            logger.debug("Sending request", {
                                url: finalUrl,
                                method: finalInit.method ?? "POST",
                                needsTransform: needsResponsesTransform,
                            });
                            const response = await fetch(finalUrl, {
                                ...finalInit,
                                headers,
                            });
                            logger.debug("Response received", {
                                status: response.status,
                                contentType: response.headers.get("content-type"),
                            });
                            if (response.status === 401 || response.status === 403) {
                                logger.debug("Authentication failed, attempting recovery", {
                                    status: response.status,
                                    accountIndex,
                                });
                                healthTracker.recordFailure(accountIndex);
                                accountStorage = recordFailure(accountStorage, accountIndex);
                                const refreshKey = activeAuth.refresh ?? account.refreshToken;
                                const canForceRefresh = !!refreshKey && !forcedRefreshTokens.has(refreshKey);
                                if (canForceRefresh) {
                                    forcedRefreshTokens.add(refreshKey);
                                    
                                    // Multi-session concurrency fix: Check if another session already
                                    // refreshed this account while we were failing. If the refresh
                                    // token on disk has changed, we just grab the new tokens and retry
                                    // the API call instead of burning a single-use refresh token twice.
                                    const freshStorage = await loadAccounts();
                                    const freshAccount = freshStorage?.accounts[accountIndex];
                                    if (freshAccount && freshAccount.refreshToken !== refreshKey) {
                                        logger.debug("Another session already refreshed this token. Retrying API with new tokens.", {
                                            accountIndex
                                        });
                                        activeAuth.refresh = freshAccount.refreshToken;
                                        activeAuth.access = freshAccount.accessToken;
                                        activeAuth.expires = freshAccount.expires;
                                        accountStorage = freshStorage;
                                        continue;
                                    }

                                    try {
                                        const recovered = await refreshAccessToken(activeAuth, oauthOptions, client, providerId);
                                        if (recovered) {
                                            accountStorage = updateAccount(accountStorage, accountIndex, {
                                                refreshToken: recovered.refresh,
                                                accessToken: recovered.access,
                                                expires: recovered.expires,
                                                resourceUrl: recovered.resourceUrl ?? account.resourceUrl,
                                                lastUsed: Date.now(),
                                            });
                                            await saveAccounts(accountStorage);
                                            continue;
                                        }
                                    }
                                    catch (error) {
                                        const refreshError = error;
                                        logger.debug("Forced refresh after auth failure failed", {
                                            accountIndex,
                                            code: refreshError.code,
                                        });
                                        if (isInvalidRefreshCode(refreshError.code)) {
                                            accountStorage = quarantineInvalidAccount(accountStorage, accountIndex);
                                        }
                                        await saveAccounts(accountStorage);
                                    }
                                }
                                else {
                                    accountStorage = quarantineInvalidAccount(accountStorage, accountIndex);
                                    await saveAccounts(accountStorage);
                                }
                                attempts += 1;
                                if (attempts >= MAX_ROTATION_ATTEMPTS) {
                                    throw new Error("All Qwen OAuth accounts have invalid or expired credentials. Run `opencode providers login --provider qwen --method \\\"Qwen OAuth\\\"` to reconnect.");
                                }
                                continue;
                            }
                            // Transform streaming response from Chat Completions to Responses API format
                            if (needsResponsesTransform &&
                                response.ok &&
                                response.body &&
                                response.headers
                                    .get("content-type")
                                    ?.includes("text/event-stream")) {
                                const sseCtx = createSSETransformContext(logger);
                                const transformStream = createSSETransformStream(sseCtx);
                                const transformedBody = response.body.pipeThrough(transformStream);
                                return new Response(transformedBody, {
                                    status: response.status,
                                    statusText: response.statusText,
                                    headers: response.headers,
                                });
                            }
                            if (needsResponsesTransform &&
                                response.ok &&
                                !response.headers
                                    .get("content-type")
                                    ?.includes("text/event-stream")) {
                                logger.debug("Transforming non-streaming response");
                                const chatBody = await response.json();
                                const ctx = createTransformContext();
                                const responsesBody = transformChatCompletionsToResponses(chatBody, ctx);
                                return new Response(JSON.stringify(responsesBody), {
                                    status: response.status,
                                    statusText: response.statusText,
                                    headers: new Headers({
                                        "content-type": "application/json",
                                    }),
                                });
                            }
                            if (response.status === 429 || response.status >= 500) {
                                const reason = parseRateLimitReason(response);
                                const headerMs = extractRetryAfterMs(response);
                                const tieredMs = getBackoffMs(reason, attempts);
                                const retryAfterMs = headerMs ?? tieredMs;
                                logger.debug("Rate limited or server error", {
                                    status: response.status,
                                    reason,
                                    accountIndex,
                                    retryAfterMs,
                                    attempts,
                                    totalAccounts: accountStorage.accounts.length,
                                });
                                accountStorage = markRateLimited(accountStorage, accountIndex, retryAfterMs);
                                accountStorage = recordFailure(accountStorage, accountIndex);
                                if (response.status === 429) {
                                    healthTracker.recordRateLimit(accountIndex);
                                }
                                else {
                                    healthTracker.recordFailure(accountIndex);
                                }
                                await saveAccounts(accountStorage);
                                attempts += 1;
                                if (attempts >= MAX_ROTATION_ATTEMPTS) {
                                    const waitMs = getMinRateLimitWait(accountStorage, Date.now());
                                    if (waitMs) {
                                        logger.debug("All accounts rate limited, waiting", {
                                            waitMs,
                                        });
                                        await sleep(waitMs);
                                        attempts = 0;
                                        continue;
                                    }
                                    return response;
                                }
                                continue;
                            }
                            accountStorage = recordSuccess(accountStorage, accountIndex);
                            healthTracker.recordSuccess(accountIndex);
                            await saveAccounts(accountStorage);
                            return response;
                        }
                    },
                };
            },
            methods: [
                {
                    label: "Qwen OAuth",
                    type: "oauth",
                    authorize: async () => {
                        const device = await authorizeQwenDevice(oauthOptions);
                        const url = device.verificationUriComplete ?? device.verificationUri;
                        const instructions = `Open ${device.verificationUri} and enter code ${device.userCode}`;
                        return {
                            url,
                            method: "auto",
                            instructions,
                            callback: async () => {
                                const result = await pollQwenDeviceToken(oauthOptions, device.deviceCode, device.intervalSeconds, device.expiresAt, device.codeVerifier);
                                if (result.type === "success") {
                                    return {
                                        type: "success",
                                        refresh: result.refresh,
                                        access: result.access,
                                        expires: result.expires,
                                        resourceUrl: result.resourceUrl,
                                    };
                                }
                                return { type: "failed", error: result.error };
                            },
                        };
                    },
                },
            ],
        },
    };
};
export const QwenCLIOAuthPlugin = createQwenOAuthPlugin("qwen");
export const QwenOAuthPlugin = QwenCLIOAuthPlugin;
export { sanitizeMalformedUrl, applyResourceUrl };
export default QwenOAuthPlugin;
//# sourceMappingURL=plugin.js.map
