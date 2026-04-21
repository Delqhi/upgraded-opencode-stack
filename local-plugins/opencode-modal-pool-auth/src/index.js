"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (this && this.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g = Object.create((typeof Iterator === "function" ? Iterator : Object).prototype);
    return g.next = verb(0), g["throw"] = verb(1), g["return"] = verb(2), typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (g && (g = 0, op[0] && (_ = 0)), _) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};
var _a;
Object.defineProperty(exports, "__esModule", { value: true });
exports.ModalPoolAuthPlugin = void 0;
var constants_1 = require("./constants");
var pool_client_1 = require("./pool-client");
var poolClient = new pool_client_1.PoolClient(process.env.MODAL_POOL_URL || undefined, Number(process.env.MODAL_POOL_TIMEOUT_MS || constants_1.DEFAULT_POOL_TIMEOUT_MS), process.env.MODAL_GATEWAY_KEY || undefined, process.env.MODAL_POOL_MASTER_KEY || undefined);
var sessionState = new Map();
var activeSessionId = (_a = process.env.OPENCODE_SESSION_ID) !== null && _a !== void 0 ? _a : "pid-".concat(process.pid);
function toUrlString(input) {
    if (typeof input === "string")
        return input;
    if (input instanceof URL)
        return input.toString();
    return input.url;
}
function isModalRequest(input) {
    var _a;
    return toUrlString(input).startsWith((_a = process.env.MODAL_BASE_URL) !== null && _a !== void 0 ? _a : constants_1.DEFAULT_MODAL_BASE_URL);
}
function resolveSessionId(input, init) {
    var _a, _b, _c;
    var headers = new Headers((_a = init === null || init === void 0 ? void 0 : init.headers) !== null && _a !== void 0 ? _a : (input instanceof Request ? input.headers : undefined));
    return (_c = (_b = headers.get("x-opencode-session-id")) !== null && _b !== void 0 ? _b : headers.get("x-session-id")) !== null && _c !== void 0 ? _c : activeSessionId;
}
function withModalAuth(request, apiKey) {
    var headers = new Headers(request.headers);
    headers.set("authorization", "Bearer ".concat(apiKey));
    headers.set("api-key", apiKey);
    return new Request(request, { headers: headers });
}
function isRateLimitResponse(response) {
    return __awaiter(this, void 0, void 0, function () {
        var body;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    if (response.status === 429)
                        return [2 /*return*/, true];
                    return [4 /*yield*/, response.clone().text()];
                case 1:
                    body = (_a.sent()).toLowerCase();
                    return [2 /*return*/, body.includes("too many concurrent requests") || (body.includes("rate") && body.includes("limit"))];
            }
        });
    });
}
function ensureSessionKey(sessionId) {
    return __awaiter(this, void 0, void 0, function () {
        var existing, _loop_1, state_1;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    existing = sessionState.get(sessionId);
                    if (existing)
                        return [2 /*return*/, existing];
                    _loop_1 = function () {
                        var lease, next;
                        return __generator(this, function (_b) {
                            switch (_b.label) {
                                case 0: return [4 /*yield*/, poolClient.checkout(sessionId, "session-".concat(sessionId))];
                                case 1:
                                    lease = _b.sent();
                                    if (lease.api_key) {
                                        next = { apiKey: lease.api_key };
                                        sessionState.set(sessionId, next);
                                        return [2 /*return*/, { value: next }];
                                    }
                                    if (!lease.retry_after) return [3 /*break*/, 3];
                                    // retry_after kommt vom Pool und ist die kanonische Wartezeit. Wir
                                    // respektieren sie exakt, statt lokal irgendwelche geratenen Backoffs
                                    // zu erfinden, damit der Plugin-Prozess und der Pool synchron bleiben.
                                    return [4 /*yield*/, new Promise(function (r) { return setTimeout(r, lease.retry_after * 1000); })];
                                case 2:
                                    // retry_after kommt vom Pool und ist die kanonische Wartezeit. Wir
                                    // respektieren sie exakt, statt lokal irgendwelche geratenen Backoffs
                                    // zu erfinden, damit der Plugin-Prozess und der Pool synchron bleiben.
                                    _b.sent();
                                    return [2 /*return*/, "continue"];
                                case 3: throw new Error("No Modal API keys available in pool");
                            }
                        });
                    };
                    _a.label = 1;
                case 1:
                    if (!true) return [3 /*break*/, 3];
                    return [5 /*yield**/, _loop_1()];
                case 2:
                    state_1 = _a.sent();
                    if (typeof state_1 === "object")
                        return [2 /*return*/, state_1.value];
                    return [3 /*break*/, 1];
                case 3: return [2 /*return*/];
            }
        });
    });
}
function rotateSessionKey(sessionId, previousApiKey) {
    return __awaiter(this, void 0, void 0, function () {
        var _loop_2, state_2;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    _loop_2 = function () {
                        var lease, next;
                        return __generator(this, function (_b) {
                            switch (_b.label) {
                                case 0: return [4 /*yield*/, poolClient.reportRateLimited(sessionId, previousApiKey)];
                                case 1:
                                    lease = _b.sent();
                                    if (lease.api_key) {
                                        next = { apiKey: lease.api_key };
                                        sessionState.set(sessionId, next);
                                        return [2 /*return*/, { value: next }];
                                    }
                                    if (!lease.retry_after) return [3 /*break*/, 3];
                                    // Auch nach einem Rate-Limit vertrauen wir auf die Pool-seitige Retry-Zeit,
                                    // damit alle Sessions denselben globalen Cooldown respektieren.
                                    return [4 /*yield*/, new Promise(function (r) { return setTimeout(r, lease.retry_after * 1000); })];
                                case 2:
                                    // Auch nach einem Rate-Limit vertrauen wir auf die Pool-seitige Retry-Zeit,
                                    // damit alle Sessions denselben globalen Cooldown respektieren.
                                    _b.sent();
                                    return [2 /*return*/, "continue"];
                                case 3: throw new Error("No Modal API keys available in pool");
                            }
                        });
                    };
                    _a.label = 1;
                case 1:
                    if (!true) return [3 /*break*/, 3];
                    return [5 /*yield**/, _loop_2()];
                case 2:
                    state_2 = _a.sent();
                    if (typeof state_2 === "object")
                        return [2 /*return*/, state_2.value];
                    return [3 /*break*/, 1];
                case 3: return [2 /*return*/];
            }
        });
    });
}
function releaseSession(sessionId) {
    return __awaiter(this, void 0, void 0, function () {
        var _a;
        return __generator(this, function (_b) {
            switch (_b.label) {
                case 0:
                    if (!sessionState.has(sessionId))
                        return [2 /*return*/];
                    sessionState.delete(sessionId);
                    _b.label = 1;
                case 1:
                    _b.trys.push([1, 3, , 4]);
                    return [4 /*yield*/, poolClient.returnKey(sessionId)];
                case 2:
                    _b.sent();
                    return [3 /*break*/, 4];
                case 3:
                    _a = _b.sent();
                    return [3 /*break*/, 4];
                case 4: return [2 /*return*/];
            }
        });
    });
}
var ModalPoolAuthPlugin = function (_input) { return __awaiter(void 0, void 0, void 0, function () {
    return __generator(this, function (_a) {
        return [2 /*return*/, {
                event: function (input) { return __awaiter(void 0, void 0, void 0, function () {
                    var eventType, properties, sessionID, sessionID;
                    var _a, _b, _c, _d;
                    return __generator(this, function (_e) {
                        switch (_e.label) {
                            case 0:
                                eventType = (_a = input === null || input === void 0 ? void 0 : input.event) === null || _a === void 0 ? void 0 : _a.type;
                                properties = (_b = input === null || input === void 0 ? void 0 : input.properties) !== null && _b !== void 0 ? _b : {};
                                if (eventType === "session.created") {
                                    sessionID = (_c = properties.sessionID) !== null && _c !== void 0 ? _c : (_d = properties === null || properties === void 0 ? void 0 : properties.info) === null || _d === void 0 ? void 0 : _d.id;
                                    if (sessionID)
                                        activeSessionId = String(sessionID);
                                }
                                if (!(eventType === "session.closed" || eventType === "session.stopped")) return [3 /*break*/, 2];
                                sessionID = properties.sessionID;
                                if (!sessionID) return [3 /*break*/, 2];
                                return [4 /*yield*/, releaseSession(String(sessionID))];
                            case 1:
                                _e.sent();
                                _e.label = 2;
                            case 2: return [2 /*return*/];
                        }
                    });
                }); },
                auth: {
                    provider: constants_1.PROVIDER_ID,
                    loader: function (_getAuth) { return __awaiter(void 0, void 0, void 0, function () {
                        var _a;
                        return __generator(this, function (_b) {
                            return [2 /*return*/, {
                                    apiKey: "",
                                    baseURL: (_a = process.env.MODAL_BASE_URL) !== null && _a !== void 0 ? _a : constants_1.DEFAULT_MODAL_BASE_URL,
                                    fetch: function (input, init) { return __awaiter(void 0, void 0, void 0, function () {
                                        var sessionId, baseRequest, current, attempts, authedRequest, response;
                                        var _a;
                                        return __generator(this, function (_b) {
                                            switch (_b.label) {
                                                case 0:
                                                    if (!isModalRequest(input))
                                                        return [2 /*return*/, fetch(input, init)];
                                                    sessionId = resolveSessionId(input, init);
                                                    baseRequest = new Request(input, init);
                                                    return [4 /*yield*/, ensureSessionKey(sessionId)];
                                                case 1:
                                                    current = _b.sent();
                                                    attempts = 0;
                                                    _b.label = 2;
                                                case 2:
                                                    if (!true) return [3 /*break*/, 6];
                                                    authedRequest = withModalAuth(baseRequest.clone(), current.apiKey);
                                                    return [4 /*yield*/, fetch(authedRequest)];
                                                case 3:
                                                    response = _b.sent();
                                                    return [4 /*yield*/, isRateLimitResponse(response)];
                                                case 4:
                                                    if (!(_b.sent())) {
                                                        return [2 /*return*/, response];
                                                    }
                                                    attempts += 1;
                                                    if (attempts > Number((_a = process.env.MODAL_POOL_MAX_RETRIES) !== null && _a !== void 0 ? _a : constants_1.DEFAULT_MAX_RETRIES)) {
                                                        return [2 /*return*/, response];
                                                    }
                                                    return [4 /*yield*/, rotateSessionKey(sessionId, current.apiKey)];
                                                case 5:
                                                    current = _b.sent();
                                                    return [3 /*break*/, 2];
                                                case 6: return [2 /*return*/];
                                            }
                                        });
                                    }); },
                                }];
                        });
                    }); },
                    methods: [
                        {
                            type: "api",
                            label: "Modal API key -> GLM pool",
                            prompts: [
                                {
                                    type: "text",
                                    key: "api_key",
                                    message: "Modal API key",
                                    placeholder: "modalresearch_...",
                                    validate: function (value) {
                                        return value.startsWith("modalresearch_") ? undefined : "Expected modalresearch_... key";
                                    },
                                },
                                {
                                    type: "text",
                                    key: "label",
                                    message: "Optional label",
                                    placeholder: "modal-key-3",
                                },
                            ],
                            authorize: function (inputs) { return __awaiter(void 0, void 0, void 0, function () {
                                var apiKey, label;
                                var _a, _b, _c, _d, _e;
                                return __generator(this, function (_f) {
                                    switch (_f.label) {
                                        case 0:
                                            apiKey = (_b = (_a = inputs === null || inputs === void 0 ? void 0 : inputs.api_key) === null || _a === void 0 ? void 0 : _a.trim()) !== null && _b !== void 0 ? _b : "";
                                            label = (_d = (_c = inputs === null || inputs === void 0 ? void 0 : inputs.label) === null || _c === void 0 ? void 0 : _c.trim()) !== null && _d !== void 0 ? _d : "";
                                            if (!apiKey)
                                                return [2 /*return*/, { type: "failed" }];
                                            return [4 /*yield*/, poolClient.addKey(apiKey, label)];
                                        case 1:
                                            _f.sent();
                                            return [2 /*return*/, {
                                                    type: "success",
                                                    key: (_e = process.env.MODAL_GATEWAY_KEY) !== null && _e !== void 0 ? _e : apiKey,
                                                    provider: constants_1.PROVIDER_ID,
                                                }];
                                    }
                                });
                            }); },
                        },
                    ],
                },
                config: function (config) { return __awaiter(void 0, void 0, void 0, function () {
                    var providers;
                    var _a, _b;
                    return __generator(this, function (_c) {
                        providers = (_a = config.provider) !== null && _a !== void 0 ? _a : {};
                        if (!providers[constants_1.PROVIDER_ID]) {
                            providers[constants_1.PROVIDER_ID] = {
                                npm: "@ai-sdk/openai-compatible",
                                options: {
                                    baseURL: (_b = process.env.MODAL_BASE_URL) !== null && _b !== void 0 ? _b : constants_1.DEFAULT_MODAL_BASE_URL,
                                },
                            };
                        }
                        config.provider = providers;
                        return [2 /*return*/];
                    });
                }); },
            }];
    });
}); };
exports.ModalPoolAuthPlugin = ModalPoolAuthPlugin;
process.on("exit", function () {
    for (var _i = 0, _a = sessionState.keys(); _i < _a.length; _i++) {
        var sessionId = _a[_i];
        void releaseSession(sessionId);
    }
});
exports.default = exports.ModalPoolAuthPlugin;
