"use strict";
var __assign = (this && this.__assign) || function () {
    __assign = Object.assign || function(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
                t[p] = s[p];
        }
        return t;
    };
    return __assign.apply(this, arguments);
};
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
Object.defineProperty(exports, "__esModule", { value: true });
exports.PoolClient = void 0;
var constants_1 = require("./constants");
var PoolClient = /** @class */ (function () {
    function PoolClient(baseUrl, timeoutMs, gatewayKey, masterKey) {
        if (baseUrl === void 0) { baseUrl = (_a = process.env.MODAL_POOL_URL) !== null && _a !== void 0 ? _a : constants_1.DEFAULT_POOL_ADMIN_BASE_URL; }
        if (timeoutMs === void 0) { timeoutMs = Number((_b = process.env.MODAL_POOL_TIMEOUT_MS) !== null && _b !== void 0 ? _b : constants_1.DEFAULT_POOL_TIMEOUT_MS); }
        if (gatewayKey === void 0) { gatewayKey = process.env.MODAL_GATEWAY_KEY || "sk-sin-fleet-master"; }
        if (masterKey === void 0) { masterKey = process.env.MODAL_POOL_MASTER_KEY || "sk-modal-pool-2026"; }
        var _a, _b;
        this.baseUrl = baseUrl;
        this.timeoutMs = timeoutMs;
        this.gatewayKey = gatewayKey;
        this.masterKey = masterKey;
    }
    PoolClient.prototype.checkout = function (sessionId_1) {
        return __awaiter(this, arguments, void 0, function (sessionId, label) {
            var url;
            if (label === void 0) { label = ""; }
            return __generator(this, function (_a) {
                url = new URL("pool/checkout", this.withSlash(this.baseUrl));
                url.searchParams.set("session_id", sessionId);
                if (label)
                    url.searchParams.set("label", label);
                return [2 /*return*/, this.request(url.toString(), { method: "GET" })];
            });
        });
    };
    PoolClient.prototype.reportRateLimited = function (sessionId, apiKey) {
        return __awaiter(this, void 0, void 0, function () {
            var url;
            return __generator(this, function (_a) {
                url = new URL("pool/rate-limited", this.withSlash(this.baseUrl));
                url.searchParams.set("session_id", sessionId);
                url.searchParams.set("api_key", apiKey);
                return [2 /*return*/, this.request(url.toString(), { method: "POST" })];
            });
        });
    };
    PoolClient.prototype.returnKey = function (sessionId) {
        return __awaiter(this, void 0, void 0, function () {
            var url;
            return __generator(this, function (_a) {
                url = new URL("pool/return", this.withSlash(this.baseUrl));
                url.searchParams.set("session_id", sessionId);
                return [2 /*return*/, this.request(url.toString(), { method: "POST" })];
            });
        });
    };
    PoolClient.prototype.addKey = function (apiKey, label) {
        return __awaiter(this, void 0, void 0, function () {
            var url;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        if (!this.masterKey) {
                            throw new Error("MODAL_POOL_MASTER_KEY is required");
                        }
                        url = new URL("pool/keys", this.withSlash(this.baseUrl));
                        url.searchParams.set("api_key", apiKey);
                        if (label)
                            url.searchParams.set("label", label);
                        url.searchParams.set("master", this.masterKey);
                        return [4 /*yield*/, this.request(url.toString(), { method: "POST" })];
                    case 1:
                        _a.sent();
                        return [2 /*return*/];
                }
            });
        });
    };
    PoolClient.prototype.withSlash = function (value) {
        return value.endsWith("/") ? value : "".concat(value, "/");
    };
    PoolClient.prototype.request = function (url, init) {
        return __awaiter(this, void 0, void 0, function () {
            var controller, timer, headers, response, text, data;
            var _a;
            return __generator(this, function (_b) {
                switch (_b.label) {
                    case 0:
                        controller = new AbortController();
                        timer = setTimeout(function () { return controller.abort(); }, this.timeoutMs);
                        _b.label = 1;
                    case 1:
                        _b.trys.push([1, , 4, 5]);
                        headers = new Headers((_a = init.headers) !== null && _a !== void 0 ? _a : {});
                        if (this.gatewayKey)
                            headers.set("authorization", "Bearer ".concat(this.gatewayKey));
                        return [4 /*yield*/, fetch(url, __assign(__assign({}, init), { headers: headers, signal: controller.signal }))];
                    case 2:
                        response = _b.sent();
                        return [4 /*yield*/, response.text()];
                    case 3:
                        text = _b.sent();
                        data = text ? JSON.parse(text) : {};
                        if (!response.ok) {
                            throw new Error("pool request failed ".concat(response.status, ": ").concat(text));
                        }
                        return [2 /*return*/, data];
                    case 4:
                        clearTimeout(timer);
                        return [7 /*endfinally*/];
                    case 5: return [2 /*return*/];
                }
            });
        });
    };
    return PoolClient;
}());
exports.PoolClient = PoolClient;
