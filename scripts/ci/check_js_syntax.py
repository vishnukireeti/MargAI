#!/usr/bin/env python3
"""Runs `node --check` against every inline <script> block in index.html.

Catches a syntax error (stray bracket, broken template literal, etc.) in
any script block before it ships -- not just the main one. Scripts with
a `src` attribute (CDN scripts) are skipped since there's no local source
to check, and `type="application/ld+json"` blocks are skipped since
they're JSON, not JS.
"""
import re
import subprocess
import sys
import tempfile
import os

PATH = "index.html"

SCRIPT_RE = re.compile(
    r'<script\b([^>]*)>(.*?)</script>', re.DOTALL | re.IGNORECASE
)
SRC_RE = re.compile(r'\bsrc\s*=', re.IGNORECASE)
TYPE_RE = re.compile(r'\btype\s*=\s*["\']?([^"\'\s>]+)', re.IGNORECASE)


def main():
    with open(PATH, "r", encoding="utf-8") as f:
        content = f.read()

    blocks = []
    for m in SCRIPT_RE.finditer(content):
        attrs, body = m.group(1), m.group(2)
        if SRC_RE.search(attrs):
            continue
        type_match = TYPE_RE.search(attrs)
        script_type = type_match.group(1).lower() if type_match else "text/javascript"
        if script_type not in ("text/javascript", "application/javascript", "module", ""):
            continue
        if not body.strip():
            continue
        line_no = content[: m.start(2)].count("\n") + 1
        blocks.append((line_no, body))

    if not blocks:
        print("No inline <script> blocks found to check.")
        return

    failures = []
    for line_no, body in blocks:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".js", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(body)
            tmp_path = tmp.name
        try:
            result = subprocess.run(
                ["node", "--check", tmp_path],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                failures.append((line_no, result.stderr.strip()))
        finally:
            os.unlink(tmp_path)

    if failures:
        print(f"JS syntax check FAILED in {len(failures)} of {len(blocks)} inline <script> block(s):\n")
        for line_no, err in failures:
            print(f"  --- block starting near index.html:{line_no} ---")
            print(f"  {err}\n")
        sys.exit(1)

    print(f"JS syntax OK: {len(blocks)} inline <script> block(s) checked.")


if __name__ == "__main__":
    main()
