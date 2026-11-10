#!/usr/bin/env python3
"""Move the Videos tab from the left of About to the left of Discord.

Lifts the existing block rather than rebuilding it, so the mark and classes
stay byte-identical. Idempotent by assertion.
"""
import os
import re

PUB = "public"
ALL = ["index.html", "getting-started.html", "hardware.html",
       "setup-information.html", "about.html"]

# The whole tab, from its opening <a ... class="tab-videos"> to its </a>.
VIDEOS_RE = re.compile(
    r'[ \t]*<a href="https://www\.youtube\.com/@ChattanoogaMesh"[^>]*'
    r'class="tab-videos">\n.*?\n[ \t]*</a>\n', re.S)

# Insertion point: the Discord tab's own opening line.
DISCORD_RE = re.compile(r'^[ \t]*<a href="https://discord\.gg/[^"]*"[^>]*'
                        r'class="tab-discord">$', re.M)

for name in ALL:
    src = open(os.path.join(PUB, name), encoding="utf-8").read()

    m = VIDEOS_RE.search(src)
    assert m, f"{name}: Videos tab not found"
    block = m.group(0)
    src = src[:m.start()] + src[m.end():]

    d = DISCORD_RE.search(src)
    assert d, f"{name}: Discord tab not found"
    src = src[:d.start()] + block + src[d.start():]

    open(os.path.join(PUB, name), "w", encoding="utf-8").write(src)
    print(f"  {name}: Videos moved to the left of Discord")
