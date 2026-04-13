// ==UserScript==
// @name         SIN-InkogniFlow Browser Logger
// @namespace    https://opensin.ai
// @version      1.0.0
// @description  Captures DOM-level browser events and posts them to the SIN-InkogniFlow merge server.
// @match        *://*/*
// @grant        GM_xmlhttpRequest
// @connect      localhost
// ==/UserScript==

(function () {
    "use strict";

    var SERVER_URL = "http://localhost:5000/browser_log";

    function generateSelector(el) {
        if (!el || el.nodeType !== 1) return "";
        if (el.id) return "#" + CSS.escape(el.id);
        var parts = [];
        while (el && el.nodeType === 1) {
            var seg = el.tagName.toLowerCase();
            if (el.id) {
                parts.unshift("#" + CSS.escape(el.id));
                break;
            }
            if (el.className && typeof el.className === "string") {
                var classes = el.className.trim().split(/\s+/).filter(Boolean);
                if (classes.length) seg += "." + classes.map(function (c) { return CSS.escape(c); }).join(".");
            }
            var parent = el.parentElement;
            if (parent) {
                var siblings = Array.from(parent.children).filter(function (s) { return s.tagName === el.tagName; });
                if (siblings.length > 1) {
                    var idx = siblings.indexOf(el) + 1;
                    seg += ":nth-of-type(" + idx + ")";
                }
            }
            parts.unshift(seg);
            el = el.parentElement;
        }
        return parts.join(" > ");
    }

    function getElementInfo(el) {
        if (!el) return null;
        return {
            tag: el.tagName ? el.tagName.toLowerCase() : "",
            id: el.id || "",
            classes: (el.className && typeof el.className === "string") ? el.className.trim().split(/\s+/).filter(Boolean) : [],
            selector: generateSelector(el),
            text: (el.textContent || "").substring(0, 200).trim(),
            href: el.href || "",
            type: el.type || "",
            value: (el.value !== undefined && el.type !== "password") ? String(el.value).substring(0, 100) : "",
            rect: el.getBoundingClientRect ? (function () {
                var r = el.getBoundingClientRect();
                return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
            })() : null
        };
    }

    function postEvent(eventType, data) {
        var payload = {
            source: "browser",
            type: eventType,
            timestamp: new Date().toISOString(),
            url: window.location.href,
            title: document.title,
            data: data
        };
        try {
            if (typeof GM_xmlhttpRequest !== "undefined") {
                GM_xmlhttpRequest({
                    method: "POST",
                    url: SERVER_URL,
                    headers: { "Content-Type": "application/json" },
                    data: JSON.stringify(payload)
                });
            } else {
                fetch(SERVER_URL, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload),
                    mode: "cors"
                });
            }
        } catch (e) {
            // Server may not be running
        }
    }

    document.addEventListener("click", function (e) {
        var target = e.target || e.srcElement;
        postEvent("click", {
            element: getElementInfo(target),
            mouseX: e.clientX,
            mouseY: e.clientY,
            button: e.button,
            modifiers: {
                alt: e.altKey,
                ctrl: e.ctrlKey,
                meta: e.metaKey,
                shift: e.shiftKey
            }
        });
    }, true);

    var inputDebounce = {};
    document.addEventListener("input", function (e) {
        var target = e.target || e.srcElement;
        var selector = generateSelector(target);
        var now = Date.now();
        if (inputDebounce[selector] && now - inputDebounce[selector] < 300) return;
        inputDebounce[selector] = now;

        postEvent("input", {
            element: getElementInfo(target),
            inputType: e.inputType || "unknown",
            value: (target.type !== "password" && target.value !== undefined) ? String(target.value).substring(0, 100) : ""
        });
    }, true);

    document.addEventListener("change", function (e) {
        var target = e.target || e.srcElement;
        postEvent("change", {
            element: getElementInfo(target),
            checked: target.checked !== undefined ? target.checked : null,
            value: (target.type !== "password" && target.value !== undefined) ? String(target.value).substring(0, 100) : ""
        });
    }, true);

    var scrollTimer = null;
    window.addEventListener("scroll", function () {
        if (scrollTimer) return;
        scrollTimer = setTimeout(function () {
            scrollTimer = null;
            postEvent("scroll", {
                scrollX: window.scrollX,
                scrollY: window.scrollY,
                scrollHeight: document.documentElement.scrollHeight,
                clientHeight: document.documentElement.clientHeight
            });
        }, 200);
    }, true);

    var lastUrl = window.location.href;
    var urlObserver = new MutationObserver(function () {
        if (window.location.href !== lastUrl) {
            lastUrl = window.location.href;
            postEvent("navigation", { url: lastUrl, title: document.title });
        }
    });
    urlObserver.observe(document.body, { childList: true, subtree: true });

    window.addEventListener("popstate", function () {
        postEvent("navigation", { url: window.location.href, title: document.title, trigger: "popstate" });
    });

    document.addEventListener("submit", function (e) {
        var form = e.target || e.srcElement;
        postEvent("submit", {
            element: getElementInfo(form),
            action: form.action || "",
            method: form.method || ""
        });
    }, true);

    document.addEventListener("focus", function (e) {
        var target = e.target || e.srcElement;
        postEvent("focus", { element: getElementInfo(target) });
    }, true);

    document.addEventListener("keydown", function (e) {
        if (e.key === "Tab" || e.key === "Enter" || e.key === "Escape" || e.key.startsWith("Arrow")) {
            var target = e.target || e.srcElement;
            postEvent("keydown", {
                element: getElementInfo(target),
                key: e.key,
                code: e.code,
                modifiers: { alt: e.altKey, ctrl: e.ctrlKey, meta: e.metaKey, shift: e.shiftKey }
            });
        }
    }, true);

    console.log("[SIN-InkogniFlow Browser Logger] Active — posting to", SERVER_URL);
})();
