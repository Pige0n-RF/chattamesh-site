#!/usr/bin/env python3
"""Render gate for the SEO pass.

The static gate can't catch a stylesheet that parses but doesn't apply -- the
duplicate-<style> bug looked fine on disk and rendered white. So load each page
in real Chromium, read the computed background off the live DOM, and confirm
the head metadata resolves the way a crawler would see it.

    python3 verify_seo.py [dir]
"""
import glob
import json
import os
import sys

from playwright.sync_api import sync_playwright

EXPECTED_BG = "rgb(26, 29, 44)"  # --bg #1a1d2c
directory = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "public")

fails = []
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 900})

    for f in sorted(glob.glob(os.path.join(directory, "*.html"))):
        name = os.path.basename(f)
        page.goto("file://" + f)
        page.wait_for_timeout(250)

        bg = page.evaluate(
            "getComputedStyle(document.body).backgroundColor")
        title = page.title()
        desc = page.evaluate(
            "document.querySelector('meta[name=description]')?.content || ''")
        canon = page.evaluate(
            "document.querySelector('link[rel=canonical]')?.href || ''")
        robots = page.evaluate(
            "document.querySelector('meta[name=robots]')?.content || ''")
        og = page.evaluate(
            "document.querySelector('meta[property=\"og:image\"]')?.content || ''")
        h1s = page.evaluate("document.querySelectorAll('h1').length")
        titles = page.evaluate("document.querySelectorAll('title').length")
        ld = page.evaluate(
            "[...document.querySelectorAll('script[type=\"application/ld+json\"]')]"
            ".map(s => s.textContent)")

        errs = []
        if bg != EXPECTED_BG:
            errs.append(f"body background is {bg}, expected {EXPECTED_BG}")
        if titles != 1:
            errs.append(f"{titles} title elements")
        if h1s != 1:
            errs.append(f"{h1s} h1 elements (want exactly 1)")

        indexable = "noindex" not in robots
        if indexable:
            if not (10 < len(title) <= 65):
                errs.append(f"title length {len(title)} outside 10-65")
            if not (110 <= len(desc) <= 165):
                errs.append(f"description length {len(desc)} outside 110-165")
            if not canon:
                errs.append("no canonical")
            if not og:
                errs.append("no og:image")
            if not ld:
                errs.append("no JSON-LD")
            for block in ld:
                try:
                    json.loads(block)
                except json.JSONDecodeError as e:
                    errs.append(f"bad JSON-LD: {e}")

        tag = "noindex" if not indexable else f"t{len(title)} d{len(desc)}"
        if errs:
            fails.append(name)
            print(f"  FAIL   {name}")
            for e in errs:
                print(f"         - {e}")
        else:
            print(f"  ok     {name:28s} {tag}")

    browser.close()

if fails:
    sys.exit(f"\n{len(fails)} page(s) failed.")
print("\nRender gate passed.")
