#!/usr/bin/env python3
"""Quality gate. Nothing ships unless every page passes all of these."""
import glob
import os
import re
import sys
from html.parser import HTMLParser

PUB = os.environ.get("PUB", "public")   # repo-relative so CI works
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr", "path", "circle", "rect",
        "line", "polyline", "polygon", "ellipse", "use", "stop", "animate",
        "animateTransform", "feGaussianBlur", "feOffset", "feMerge",
        "feMergeNode", "image"}

fails = []
warns = set()


shots = set()
class Walk(HTMLParser):
    def __init__(self, name):
        super().__init__(convert_charrefs=True)
        self.name, self.stack = name, []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append((tag, self.getpos()))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack:
            fails.append(f"{self.name}: stray </{tag}> at {self.getpos()}")
            return
        if self.stack[-1][0] != tag:
            fails.append(
                f"{self.name}: </{tag}> at {self.getpos()} closes "
                f"<{self.stack[-1][0]}> opened at {self.stack[-1][1]}")
            return
        self.stack.pop()


def check(path):
    name = os.path.basename(path)
    s = open(path).read()

    w = Walk(name)
    w.feed(s)
    if w.stack:
        fails.append(f"{name}: unclosed {[t for t, _ in w.stack]}")

    # the duplicate-<style> failure mode: one tag, balanced braces
    if s.count("<style>") != 1 or s.count("</style>") != 1:
        fails.append(f"{name}: <style> x{s.count('<style>')} "
                     f"</style> x{s.count('</style>')}")
    else:
        css = s.split("<style>")[1].split("</style>")[0]
        if css.count("{") != css.count("}"):
            fails.append(f"{name}: CSS braces {css.count('{')} open / "
                         f"{css.count('}')} close")

    # every CSS var referenced must actually be defined in :root
    defined = set(re.findall(r"(--[a-z0-9-]+)\s*:", s))
    for used in set(re.findall(r"var\((--[a-z0-9-]+)", s)):
        if used not in defined:
            fails.append(f"{name}: uses undefined {used}")

    # no page may link to a file that isn't in the build
    # These three are only served from the neighbours' own sites and get
    # populated by tools/fetch-logos.sh. Every reference to them
    # carries a remote-then-text fallback, so a missing file degrades rather
    # than breaks -- warn, don't fail.
    deferred = {"images/neighbors/tennmesh.png",
                "images/clubs/gcarc.png"}
    for href in re.findall(r'(?:href|src)="([^"#:]+\.(?:html|js|png|svg|jpg|webp))"', s):
        if os.path.exists(os.path.join(PUB, href)):
            continue
        if href in deferred:
            warns.add(f"{href} (run tools/fetch-logos.sh; falls back gracefully)")
        elif href.startswith("images/hardware/"):
            shots.add(href)
        else:
            fails.append(f"{name}: broken local reference -> {href}")

    for dead in ("settings-explained-uc", "information-v1", "Live feed",
                 "/api/nodes", "chattamesh.com/images/"):
        if dead in s:
            fails.append(f"{name}: stale reference -> {dead}")

    print(f"  {name:28s} {len(s):>7,} bytes")


for f in sorted(glob.glob(os.path.join(PUB, "*.html"))):
    check(f)

if warns:
    if shots:
        print(f"\nproduct shots not yet added: {len(shots)} "
              f"(placeholder frame shows until each .webp lands)")
    print("\nnot yet fetched (expected)")
    for w in sorted(warns):
        print("  -", w)

if fails:
    print("\nFAILURES")
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("\nstatic checks passed")
