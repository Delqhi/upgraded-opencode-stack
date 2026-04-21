#!/usr/bin/env python3
import argparse
import re
import sys
from html import unescape
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


def fetch(url: str, timeout: int):
    request = Request(url, headers={"User-Agent": "check-my-dev-in-web/1.0"})
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="ignore")
            return {
                "status_code": getattr(response, "status", 200),
                "text": body,
                "url": response.geturl(),
            }
    except HTTPError as error:
        body = (
            error.read().decode("utf-8", errors="ignore")
            if hasattr(error, "read")
            else ""
        )
        return {"status_code": error.code, "text": body, "url": url}
    except URLError as error:
        raise RuntimeError(f"request failed for {url}: {error}") from error


def extract_title(html: str) -> str:
    match = re.search(r"<title>(.*?)</title>", html, re.I | re.S)
    return unescape(match.group(1).strip()) if match else ""


def extract_assets(base_url: str, html: str):
    patterns = [
        r'<script[^>]+src=["\']([^"\']+)["\']',
        r'<link[^>]+href=["\']([^"\']+)["\']',
        r'<img[^>]+src=["\']([^"\']+)["\']',
    ]
    assets = []
    for pattern in patterns:
        for match in re.findall(pattern, html, re.I):
            if match.startswith(("data:", "mailto:", "javascript:")):
                continue
            full = urljoin(base_url, match)
            if full not in assets:
                assets.append(full)
    return assets


def main():
    parser = argparse.ArgumentParser(
        description="Fast HTML/assets/routes smoke check for local web builds"
    )
    parser.add_argument(
        "--url", required=True, help="Base URL, e.g. http://127.0.0.1:4173"
    )
    parser.add_argument(
        "--route",
        action="append",
        dest="routes",
        default=[],
        help="Route to verify, e.g. /pricing",
    )
    parser.add_argument(
        "--timeout", type=int, default=15, help="Request timeout in seconds"
    )
    args = parser.parse_args()

    base_url = args.url.rstrip("/")
    routes = args.routes or ["/"]

    print("== check-my-dev-in-web smoke ==")
    print(f"base_url: {base_url}")
    print(f"routes: {' '.join(routes)}")
    print()

    try:
        root = fetch(base_url, args.timeout)
    except Exception as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 2
    print(f"root_status: {root['status_code']}")
    if root["status_code"] >= 400:
        print("FAIL: root HTML request failed", file=sys.stderr)
        return 2

    root_html = root["text"]
    print(f"root_bytes: {len(root_html.encode('utf-8'))}")
    if len(root_html.encode("utf-8")) < 100:
        print("WARN: root HTML is suspiciously small")

    title = extract_title(root_html)
    print(f"title: {title or '<missing>'}")

    broken_assets = 0
    assets = extract_assets(base_url + "/", root_html)
    for index, asset in enumerate(assets, start=1):
        try:
            response = fetch(asset, args.timeout)
            code = response["status_code"]
        except Exception:
            code = 599
        print(f"asset[{index}]: {code} {asset}")
        if code >= 400:
            broken_assets += 1

    print(f"asset_count: {len(assets)}")
    print(f"broken_assets: {broken_assets}")

    route_fail = 0
    for route in routes:
        route_url = base_url + route
        try:
            response = fetch(route_url, args.timeout)
        except Exception as error:
            print(f"route: {route} status=599 bytes=0 error={error}")
            route_fail += 1
            continue
        body = response["text"]
        print(
            f"route: {route} status={response['status_code']} bytes={len(body.encode('utf-8'))}"
        )
        if response["status_code"] >= 400:
            route_fail += 1

    if broken_assets > 0:
        print("FAIL: one or more referenced assets are broken", file=sys.stderr)
        return 3

    if route_fail > 0:
        print("FAIL: one or more checked routes failed", file=sys.stderr)
        return 4

    print()
    print("PASS: HTML, referenced assets, and checked routes responded successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
