#!/usr/bin/env python3
"""Headless-browser smoke test: loads index.html the way a real visitor's
browser would (over HTTP, not file://, since file:// triggers different
cross-origin stylesheet rules than production) and checks for the kind of
regression that silent HTML/JS bugs cause -- a blank page, a JS error on
load, or metadata landing in the wrong place -- none of which a syntax or
structure check alone can catch, because they only show up once a real
browser actually runs the page.

Requires: pip install playwright && playwright install --with-deps chromium
"""
import http.server
import socket
import sys
import threading
import contextlib
from playwright.sync_api import sync_playwright


def free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@contextlib.contextmanager
def local_server():
    port = free_port()
    handler = lambda *a, **kw: http.server.SimpleHTTPRequestHandler(*a, **kw)
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        httpd.shutdown()


def main():
    problems = []

    with local_server() as base_url:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()

            console_errors = []
            page.on(
                "console",
                lambda msg: console_errors.append(msg.text) if msg.type == "error" else None,
            )
            page.on("pageerror", lambda exc: console_errors.append(f"pageerror: {exc}"))

            page.goto(f"{base_url}/index.html", wait_until="networkidle")
            page.wait_for_timeout(1000)

            result = page.evaluate(
                """
                () => {
                    const link = document.querySelector('link[href="/assets/tailwind.css"]');
                    let tailwindRuleCount = null;
                    for (const s of document.styleSheets) {
                        try {
                            if (s.href && s.href.includes('tailwind.css')) tailwindRuleCount = s.cssRules.length;
                        } catch (e) {}
                    }
                    return {
                        headCount: document.querySelectorAll('head').length,
                        bodyCount: document.querySelectorAll('body').length,
                        hasCanonical: !!document.querySelector('link[rel="canonical"]'),
                        hasOgTitle: !!document.querySelector('meta[property="og:title"]'),
                        hasTailwindLink: !!link,
                        tailwindRuleCount: tailwindRuleCount,
                        bodyText: document.body.innerText.length,
                        careersDataLength: typeof careersData !== 'undefined' ? careersData.length : null,
                        examsDataLength: typeof examsData !== 'undefined' ? examsData.length : null,
                        collegesDataLength: typeof collegesData !== 'undefined' ? collegesData.length : null,
                    };
                }
                """
            )
            browser.close()

    if result["headCount"] != 1:
        problems.append(f"Expected exactly one <head>, found {result['headCount']}.")
    if result["bodyCount"] != 1:
        problems.append(f"Expected exactly one <body>, found {result['bodyCount']}.")
    if not result["hasCanonical"]:
        problems.append("Missing <link rel=\"canonical\"> in rendered <head>.")
    if not result["hasOgTitle"]:
        problems.append("Missing <meta property=\"og:title\"> in rendered <head>.")
    if not result["hasTailwindLink"]:
        problems.append("Missing <link href=\"/assets/tailwind.css\"> in rendered <head>.")
    if not result["tailwindRuleCount"]:
        problems.append("Tailwind stylesheet did not load any CSS rules.")
    if result["bodyText"] < 200:
        problems.append(
            f"Rendered body text looks suspiciously short ({result['bodyText']} chars) "
            f"-- the page may not be rendering real content."
        )
    for key in ("careersDataLength", "examsDataLength", "collegesDataLength"):
        if not result[key]:
            problems.append(f"{key} is empty or undefined -- base catalog data failed to load.")

    # Real JS errors during load are always a failure. A couple of third-party
    # network calls (GA4/Sentry/fonts) are inert placeholders until those IDs
    # are configured, and blocked/offline third-party fetches during a CI run
    # are expected noise, not app bugs -- filter those out specifically.
    noisy_markers = (
        "googletagmanager", "google-analytics", "sentry", "fonts.gstatic",
        "fonts.googleapis", "ERR_TUNNEL_CONNECTION_FAILED", "ERR_NAME_NOT_RESOLVED",
        "ERR_INTERNET_DISCONNECTED", "jsdelivr",
    )
    real_errors = [
        e for e in console_errors if not any(marker in e for marker in noisy_markers)
    ]
    if real_errors:
        problems.append(f"{len(real_errors)} unexpected console error(s): " + " | ".join(real_errors[:5]))

    if problems:
        print("Browser smoke test FAILED:\n")
        for p in problems:
            print(f"  - {p}")
        sys.exit(1)

    print("Browser smoke test OK: page renders, head metadata intact, base data loaded, no JS errors.")


if __name__ == "__main__":
    main()
