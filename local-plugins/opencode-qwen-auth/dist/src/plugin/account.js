import { randomBytes } from "node:crypto";
import { promises as fs } from "node:fs";
import { homedir } from "node:os";
import { dirname, join } from "node:path";
import lockfile from "proper-lockfile";
import { getHealthTracker, getTokenTracker, selectHybridAccount, } from "./rotation";
const STORAGE_VERSION = 1;
function getConfigDir() {
    if (process.platform === "win32") {
        return join(process.env.APPDATA || join(homedir(), "AppData", "Roaming"), "opencode");
    }
    const base = process.env.XDG_CONFIG_HOME || join(homedir(), ".config");
    return join(base, "opencode");
}
export function getStoragePath() {
    return join(getConfigDir(), "qwen-auth-accounts.json");
}
async function ensureFileExists(path) {
    try {
        await fs.access(path);
    }
    catch {
        await fs.mkdir(dirname(path), { recursive: true, mode: 0o700 });
        const empty = {
            version: STORAGE_VERSION,
            accounts: [],
            activeIndex: 0,
        };
        await fs.writeFile(path, JSON.stringify(empty, null, 2), {
            encoding: "utf-8",
            mode: 0o600,
        });
    }
}
async function withFileLock(path, fn) {
    await ensureFileExists(path);
    const release = await lockfile.lock(path, {
        stale: 10000,
        retries: {
            retries: 5,
            minTimeout: 100,
            maxTimeout: 1000,
            factor: 2,
        },
    });
    try {
        return await fn();
    }
    finally {
        await release().catch(() => undefined);
    }
}
function normalizeStorage(storage) {
    const MAX_CONSECUTIVE_FAILURES = 20;
    const now = Date.now();
    const accounts = storage.accounts.filter((account) => {
        // Must have a refresh token — no token means the account was not properly set up
        if (!account?.refreshToken) return false;
        // Remove accounts with too many consecutive failures — they are dead
        if ((account.health?.consecutiveFailures ?? 0) > MAX_CONSECUTIVE_FAILURES) return false;
// Remove accounts whose access token is expired AND have high failure counts
    // This catches accounts with expired refresh tokens that keep failing on refresh attempts
    // We allow a grace period: only remove if they have been failing consistently
    const hasExpiredToken = !account.accessToken && (!account.expires || account.expires < now);
    const hasHighFailures = (account.health?.failureCount ?? 0) > 50;
    if (hasExpiredToken && hasHighFailures) return false;
    // BUG-FIX: Remove accounts with empty accessToken AND expires=0 (never got a token)
    // These are "zombie stubs" from failed OAuth flows — filter out regardless of failureCount
    if (!account.accessToken && account.expires === 0) return false;
    return true;
    });
    const activeIndex = accounts.length > 0
        ? Math.min(Math.max(storage.activeIndex, 0), accounts.length - 1)
        : 0;
    return { version: STORAGE_VERSION, accounts, activeIndex };
}
function mergeAccounts(existing, incoming) {
    const map = new Map();
    for (const account of existing.accounts) {
        map.set(account.refreshToken, account);
    }
    for (const account of incoming.accounts) {
        const current = map.get(account.refreshToken);
        if (current) {
            map.set(account.refreshToken, {
                ...current,
                ...account,
                lastUsed: Math.max(current.lastUsed, account.lastUsed),
            });
        }
        else {
            map.set(account.refreshToken, account);
        }
    }
    return normalizeStorage({
        version: STORAGE_VERSION,
        accounts: Array.from(map.values()),
        activeIndex: incoming.activeIndex,
    });
}
export async function loadAccounts() {
    try {
        const path = getStoragePath();
        const content = await fs.readFile(path, "utf-8");
        const parsed = JSON.parse(content);
        if (!parsed ||
            parsed.version !== STORAGE_VERSION ||
            !Array.isArray(parsed.accounts)) {
            return null;
        }
        return normalizeStorage(parsed);
    }
    catch (error) {
        const code = error.code;
        if (code === "ENOENT") {
            return null;
        }
        return null;
    }
}
export async function saveAccounts(storage) {
    const path = getStoragePath();
    await withFileLock(path, async () => {
        const existing = await loadAccounts();
        const merged = existing
            ? mergeAccounts(existing, storage)
            : normalizeStorage(storage);
        const tempPath = `${path}.${randomBytes(6).toString("hex")}.tmp`;
        await fs.mkdir(dirname(path), { recursive: true, mode: 0o700 });
        await fs.writeFile(tempPath, JSON.stringify(merged, null, 2), {
            encoding: "utf-8",
            mode: 0o600,
        });
        await fs.rename(tempPath, path);
        await fs.chmod(path, 0o600);
    });
}
export function upsertAccount(storage, account) {
    const index = storage.accounts.findIndex((item) => item.refreshToken === account.refreshToken);
    if (index === -1) {
        return normalizeStorage({
            version: STORAGE_VERSION,
            accounts: [...storage.accounts, account],
            activeIndex: storage.activeIndex,
        });
    }
    const updated = [...storage.accounts];
    updated[index] = {
        ...updated[index],
        ...account,
        lastUsed: account.lastUsed,
    };
    return normalizeStorage({
        version: STORAGE_VERSION,
        accounts: updated,
        activeIndex: storage.activeIndex,
    });
}
export function updateAccount(storage, index, update) {
    const accounts = [...storage.accounts];
    const current = accounts[index];
    if (!current)
        return storage;
    accounts[index] = { ...current, ...update };
    return normalizeStorage({
        version: STORAGE_VERSION,
        accounts,
        activeIndex: storage.activeIndex,
    });
}
export function selectAccount(storage, strategy, now, options) {
    const total = storage.accounts.length;
    if (total === 0)
        return null;
    if (strategy === "hybrid") {
        const healthTracker = options?.healthTracker ?? getHealthTracker();
        const tokenTracker = options?.tokenTracker ?? getTokenTracker();
        const pidOffset = options?.pidOffset ?? 0;
        const accountsWithMetrics = storage.accounts.map((account, idx) => ({
            index: idx,
            lastUsed: account.lastUsed,
            healthScore: healthTracker.getScore(idx),
            tokens: tokenTracker.getTokens(idx),
            isRateLimited: !!(account.rateLimitResetAt && account.rateLimitResetAt > now),
        }));
        if (pidOffset > 0 && accountsWithMetrics.length > 1) {
            const rotateBy = pidOffset % accountsWithMetrics.length;
            for (let i = 0; i < rotateBy; i++) {
                const first = accountsWithMetrics.shift();
                if (first)
                    accountsWithMetrics.push(first);
            }
        }
        const result = selectHybridAccount(accountsWithMetrics, healthTracker.config.minUsable, tokenTracker.getMaxTokens());
        if (!result) {
            return null;
        }
        const selectedIndex = result.index;
        const selectedAccount = storage.accounts[selectedIndex];
        if (!selectedAccount)
            return null;
        tokenTracker.consume(selectedIndex);
        const updatedAccounts = [...storage.accounts];
        updatedAccounts[selectedIndex] = {
            ...selectedAccount,
            lastUsed: now,
        };
        const updated = normalizeStorage({
            version: STORAGE_VERSION,
            accounts: updatedAccounts,
            activeIndex: selectedIndex,
        });
        return {
            account: updatedAccounts[selectedIndex],
            index: selectedIndex,
            storage: updated,
        };
    }
    const startIndex = strategy === "round-robin"
        ? (storage.activeIndex + 1) % total
        : Math.min(storage.activeIndex, total - 1);
    for (let offset = 0; offset < total; offset += 1) {
        const index = (startIndex + offset) % total;
        const account = storage.accounts[index];
        if (!account)
            continue;
        if (account.rateLimitResetAt && account.rateLimitResetAt > now) {
            continue;
        }
        const updatedAccounts = [...storage.accounts];
        updatedAccounts[index] = {
            ...account,
            lastUsed: now,
        };
        const updated = normalizeStorage({
            version: STORAGE_VERSION,
            accounts: updatedAccounts,
            activeIndex: index,
        });
        return { account: updatedAccounts[index], index, storage: updated };
    }
    return null;
}
export function markRateLimited(storage, index, retryAfterMs) {
    const resetAt = Date.now() + retryAfterMs;
    return updateAccount(storage, index, { rateLimitResetAt: resetAt });
}
export function getMinRateLimitWait(storage, now) {
    const waits = storage.accounts
        .map((account) => account.rateLimitResetAt ? account.rateLimitResetAt - now : null)
        .filter((value) => value !== null && value > 0);
    if (waits.length === 0) {
        return null;
    }
    return Math.min(...waits);
}
function ensureHealth(account) {
    return (account.health ?? {
        successCount: 0,
        failureCount: 0,
        consecutiveFailures: 0,
    });
}
export function calculateHealthScore(account) {
    const health = ensureHealth(account);
    const total = health.successCount + health.failureCount;
    if (total === 0)
        return 1.0;
    const successRate = health.successCount / total;
    const recencyPenalty = Math.min(health.consecutiveFailures * 0.15, 0.5);
    return Math.max(0, successRate - recencyPenalty);
}
export function recordSuccess(storage, index) {
    const account = storage.accounts[index];
    if (!account)
        return storage;
    const health = ensureHealth(account);
    return updateAccount(storage, index, {
        health: {
            ...health,
            successCount: health.successCount + 1,
            consecutiveFailures: 0,
            lastSuccess: Date.now(),
        },
    });
}
export function recordFailure(storage, index) {
    const account = storage.accounts[index];
    if (!account)
        return storage;
    const health = ensureHealth(account);
    return updateAccount(storage, index, {
        health: {
            ...health,
            failureCount: health.failureCount + 1,
            consecutiveFailures: health.consecutiveFailures + 1,
            lastFailure: Date.now(),
        },
    });
}
export function isAccountUsable(account, threshold = 0.2) {
    return calculateHealthScore(account) >= threshold;
}
//# sourceMappingURL=account.js.map