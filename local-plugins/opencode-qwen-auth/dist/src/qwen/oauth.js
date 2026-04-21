import { createHash, randomBytes } from "node:crypto";
import { QWEN_DEFAULT_CLIENT_ID, QWEN_DEFAULT_SCOPES, QWEN_DEVICE_CODE_ENDPOINT, QWEN_OAUTH_BASE_URL, QWEN_TOKEN_ENDPOINT, } from "../constants";
import { calculateTokenExpiry } from "../plugin/auth";
function createOAuthBody(entries) {
    return new URLSearchParams(entries);
}
function parseJsonResponseText(responseText, context, response) {
    const text = typeof responseText === "string" ? responseText : "";
    try {
        return JSON.parse(text);
    }
    catch (error) {
        const preview = text.trim().replace(/\s+/g, " ").slice(0, 240);
        const contentType = response.headers.get("content-type") ?? "unknown content-type";
        const details = preview
            ? `${response.status} ${response.statusText} (${contentType}) — ${preview}`
            : `${response.status} ${response.statusText} (${contentType})`;
        const message = `${context}: expected JSON but received non-JSON response (${details})`;
        throw new Error(message, { cause: error });
    }
}
function resolveOAuthUrl(base, endpoint) {
    const normalized = typeof base === "string" && base.trim() ? base : QWEN_OAUTH_BASE_URL;
    try {
        return new URL(endpoint, normalized).toString();
    }
    catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        throw new Error(`Invalid OAuth base URL: ${normalized}. ${message}`);
    }
}
function resolveClientId(clientId) {
    const trimmed = typeof clientId === "string" ? clientId.trim() : "";
    return trimmed || QWEN_DEFAULT_CLIENT_ID;
}
function base64UrlEncode(buffer) {
    return buffer
        .toString("base64")
        .replace(/\+/g, "-")
        .replace(/\//g, "_")
        .replace(/=+$/, "");
}
function createPkcePair() {
    const verifier = base64UrlEncode(randomBytes(32));
    const challenge = base64UrlEncode(createHash("sha256").update(verifier).digest());
    return { verifier, challenge };
}
export async function authorizeQwenDevice(options) {
    const scopes = options.scopes ?? QWEN_DEFAULT_SCOPES;
    const { verifier, challenge } = createPkcePair();
    const response = await fetch(resolveOAuthUrl(options.oauthBaseUrl, QWEN_DEVICE_CODE_ENDPOINT), {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body: createOAuthBody({
            client_id: resolveClientId(options.clientId),
            scope: scopes.join(" "),
            code_challenge: challenge,
            code_challenge_method: "S256",
        }),
    });
    if (!response.ok) {
        const message = await response.text();
        throw new Error(message || "Failed to start Qwen device flow");
    }
    const responseText = await response.text();
    const payload = parseJsonResponseText(responseText, "Qwen device authorization", response);
    const expiresAt = calculateTokenExpiry(Date.now(), payload.expires_in);
    const intervalSeconds = payload.interval ?? 5;
    return {
        deviceCode: payload.device_code,
        userCode: payload.user_code,
        verificationUri: payload.verification_uri,
        verificationUriComplete: payload.verification_uri_complete,
        expiresAt,
        intervalSeconds,
        codeVerifier: verifier,
    };
}
function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}
export async function pollQwenDeviceToken(options, deviceCode, intervalSeconds, expiresAt, codeVerifier) {
    let currentInterval = intervalSeconds;
    while (Date.now() < expiresAt) {
        const response = await fetch(resolveOAuthUrl(options.oauthBaseUrl, QWEN_TOKEN_ENDPOINT), {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
            },
            body: createOAuthBody({
                client_id: resolveClientId(options.clientId),
                grant_type: "urn:ietf:params:oauth:grant-type:device_code",
                device_code: deviceCode,
                code_verifier: codeVerifier,
            }),
        });
        if (response.ok) {
            const responseText = await response.text();
            const payload = parseJsonResponseText(responseText, "Qwen token polling", response);
            if (!payload.refresh_token) {
                return { type: "failed", error: "Missing refresh token" };
            }
            return {
                type: "success",
                access: payload.access_token,
                refresh: payload.refresh_token,
                expires: calculateTokenExpiry(Date.now(), payload.expires_in),
                resourceUrl: payload.resource_url,
            };
        }
        const errorText = await response.text();
        let errorPayload = {};
        try {
            errorPayload = JSON.parse(errorText);
        }
        catch {
            errorPayload = {};
        }
        const code = errorPayload.error;
        if (code === "authorization_pending") {
            await sleep(currentInterval * 1000);
            continue;
        }
        if (code === "slow_down") {
            currentInterval += 5;
            await sleep(currentInterval * 1000);
            continue;
        }
        if (code === "expired_token") {
            return { type: "failed", error: "Device code expired", code };
        }
        return {
            type: "failed",
            error: errorPayload.error_description ?? "OAuth polling failed",
            code,
        };
    }
    return { type: "failed", error: "Device authorization expired" };
}
export async function refreshQwenToken(options, refreshToken) {
    const response = await fetch(resolveOAuthUrl(options.oauthBaseUrl, QWEN_TOKEN_ENDPOINT), {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body: createOAuthBody({
            client_id: resolveClientId(options.clientId),
            grant_type: "refresh_token",
            refresh_token: refreshToken,
        }),
    });
    if (!response.ok) {
        const errorPayload = (await response
            .json()
            .catch(() => ({})));
        return {
            type: "failed",
            error: errorPayload.error_description ?? "Failed to refresh token",
            code: errorPayload.error,
        };
    }
    const responseText = await response.text();
    const payload = parseJsonResponseText(responseText, "Qwen token refresh", response);
    return {
        type: "success",
        access: payload.access_token,
        refresh: payload.refresh_token ?? refreshToken,
        expires: calculateTokenExpiry(Date.now(), payload.expires_in),
        resourceUrl: payload.resource_url,
    };
}
//# sourceMappingURL=oauth.js.map
