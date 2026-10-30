#!/usr/bin/env python3
"""Sanity-checks index.html's document structure.

This exists because of a real bug: an earlier save accidentally left a
second, stray <!doctype html><html><head>...</head><body> skeleton on
line 1 (on top of the real one later in the file). Per the HTML5 parsing
spec, that silently made every <meta>/<link>/<script> tag meant for <head>
land inside <body> instead -- so canonical links, Open Graph tags, and
structured data were being dropped from <head> with no visible error.

A plain text diff or eyeballing the file never would have caught it (the
page still *rendered* fine -- browsers are very forgiving). Only parsing
the file the way a browser does, and counting tags, catches it. This
script does that with Python's stdlib HTMLParser, so it needs no
dependencies and runs the same locally and in CI.
"""
import sys
from html.parser import HTMLParser

PATH = "index.html"

STRUCTURAL_TAGS = {"html", "head", "body"}


class StructureChecker(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.counts = {tag: 0 for tag in STRUCTURAL_TAGS}
        self.open_stack = []
        # Track which top-level tag each <head>-only element (meta/link/title)
        # actually lands under, since that's exactly what the real bug broke.
        self.head_only_elements_outside_head = []
        self._in_head = False
        self._in_body = False
        self._head_closed = False

    def handle_starttag(self, tag, attrs):
        if tag in STRUCTURAL_TAGS:
            self.counts[tag] += 1
            if tag == "head":
                self._in_head = True
            if tag == "body":
                self._in_body = True
            self.open_stack.append(tag)
            return
        if tag in ("meta", "link", "title") and not self._in_head and self._in_body:
            self.head_only_elements_outside_head.append((tag, self.getpos()[0]))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag == "head":
            self._in_head = False
            self._head_closed = True


def main():
    with open(PATH, "r", encoding="utf-8") as f:
        content = f.read()

    problems = []

    first_line = content.split("\n", 1)[0].strip()
    if not first_line.lower().startswith("<!doctype html>"):
        problems.append(
            f"First line of {PATH} must start with '<!doctype html>' "
            f"(found: {first_line[:60]!r})"
        )

    checker = StructureChecker()
    checker.feed(content)

    for tag in STRUCTURAL_TAGS:
        n = checker.counts[tag]
        if n != 1:
            problems.append(f"Expected exactly one <{tag}> tag, found {n}.")

    if checker.head_only_elements_outside_head:
        examples = ", ".join(
            f"<{tag}> at line {line}"
            for tag, line in checker.head_only_elements_outside_head[:8]
        )
        problems.append(
            f"{len(checker.head_only_elements_outside_head)} <meta>/<link>/<title> "
            f"tag(s) that belong in <head> were parsed as landing in <body> instead "
            f"(this is exactly the earlier duplicate-wrapper bug's symptom): {examples}"
        )

    if problems:
        print("HTML structure check FAILED:\n")
        for p in problems:
            print(f"  - {p}")
        sys.exit(1)

    print(
        f"HTML structure OK: single doctype/html/head/body, "
        f"all head-only tags land in <head>."
    )


if __name__ == "__main__":
    main()
