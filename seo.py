#!/usr/bin/env python3
"""ChattaMe.sh v1.1 -- SEO head injection.

Run from the repo root:

    python3 seo.py            # inject into ./public
    python3 seo.py --dir DIR  # inject into somewhere else
    python3 seo.py --check    # report only, write nothing

Everything it writes is fenced between <!-- seo:start --> and <!-- seo:end -->,
and the fence is stripped before each run, so this is safe to re-run after any
content edit. The page's own <title> is removed and re-emitted inside the fence
so there is exactly one title element afterwards.

Canonicals are extensionless. Cloudflare Workers' asset handler serves
getting-started.html at /getting-started and 301s the .html form, so the
extensionless URL is the one that should be indexed.
"""

import argparse
import datetime
import html
import json
import os
import re
import sys
from html.parser import HTMLParser

SITE = "https://chattame.sh"
OG_IMAGE = f"{SITE}/images/og-card.png"
OG_ALT = "ChattaMesh — MeshCore LoRa mesh radio network for Chattanooga, Tennessee"
DISCORD = "https://discord.gg/XF354A3e9m"

START, END = "<!-- seo:start -->", "<!-- seo:end -->"

# ---------------------------------------------------------------- page table

PAGES = {
    "index.html": dict(
        path="/",
        title="ChattaMesh — MeshCore Mesh Radio Network in Chattanooga, TN",
        desc=(
            "ChattaMesh is a volunteer-run MeshCore LoRa mesh network for "
            "Chattanooga, Tennessee. Node setup, region scoping, and public "
            "channel reference for local operators."
        ),
        crumb=None,
        schema="home",
    ),
    "announcements.html": dict(
        path="/announcements",
        title="Announcements — Meetings & Updates | ChattaMesh",
        desc=(
            "News from the Chattanooga mesh: the next community meeting, region "
            "scoping rollout, wardriving updates, and what's changed on the site."
        ),
        crumb="Announcements",
        schema="tech",
    ),
    "getting-started.html": dict(
        path="/getting-started",
        title="Getting Started — MeshCore Node Setup | ChattaMesh",
        desc=(
            "Configure a MeshCore companion or repeater node for the Chattanooga "
            "mesh: radio settings, TX/RX delay tiers, coding rate, and "
            "copy-paste CLI commands."
        ),
        crumb="Getting Started",
        schema="tech",
    ),
    "setup-information.html": dict(
        path="/setup-information",
        title="Setup & Information — Region Scoping | ChattaMesh",
        desc=(
            "How MeshCore region scoping works, from unscoped traffic down to "
            "us-tn-cha, plus public channel assignments and repeater "
            "configuration for the Chattanooga mesh."
        ),
        crumb="Setup & Information",
        schema="tech",
    ),
    "hardware.html": dict(
        path="/hardware",
        title="Hardware — Nodes, Antennas & DIY Parts | ChattaMesh",
        desc=(
            "Hardware picks for the Chattanooga mesh: MeshCore companion nodes, "
            "repeaters, SMA and N-type antennas, plus enclosures, boards, "
            "batteries, and coax for DIY builds."
        ),
        crumb="Hardware",
        schema="tech",
    ),
    "videos-welcome.html": dict(
        path="/videos-welcome",
        title="Welcome Videos — Getting on the Mesh | ChattaMesh",
        desc=(
            "Video walkthroughs for new ChattaMesh members: getting a MeshCore "
            "node on the air, the settings that matter, and what to expect once "
            "you're talking."
        ),
        crumb="Welcome Videos",
        schema="tech",
    ),
    "videos-information.html": dict(
        path="/videos-information",
        title="Instructional Videos — MeshCore How-To | ChattaMesh",
        desc=(
            "Instructional videos for the Chattanooga mesh: region scoping, "
            "repeater siting, antennas, and the parts that are easier shown "
            "than written."
        ),
        crumb="Instructional Videos",
        schema="tech",
    ),
    "videos-meetings.html": dict(
        path="/videos-meetings",
        title="Meetings — Live Stream & Recordings | ChattaMesh",
        desc=(
            "Watch ChattaMesh meetings live on YouTube, or catch up with the "
            "recordings afterwards. Community mesh radio in Chattanooga, "
            "Tennessee."
        ),
        crumb="Meetings",
        schema="tech",
    ),
    "funding.html": dict(
        path="/funding",
        title="Funding — How ChattaMesh Pays For Infrastructure",
        desc=(
            "How the Chattanooga mesh funds repeaters and infrastructure: the "
            "options under discussion, donations received, and where the money "
            "goes. Kept public on purpose."
        ),
        crumb="Funding",
        schema="tech",
    ),
    "about.html": dict(
        path="/about",
        title="About ChattaMesh — Community Mesh Radio in Chattanooga",
        desc=(
            "Who runs ChattaMesh, how the network fits into the TennMesh "
            "umbrella, and how to get involved with community LoRa mesh radio "
            "in the Chattanooga area."
        ),
        crumb="About",
        schema="about",
    ),
}

# Pages from v1.0 that v1.1 merged away. If they're still on disk they get a
# noindex so anything already in the index falls out rather than competing with
# the merged page for the same terms.
RETIRED = {"settings-explained-uc.html", "information-v1.html"}


# --------------------------------------------------------------- structured data

def org_node():
    return {
        "@type": "Organization",
        "@id": f"{SITE}/#org",
        "name": "ChattaMesh",
        "alternateName": "chattame.sh",
        "url": f"{SITE}/",
        "logo": {
            "@type": "ImageObject",
            "url": f"{SITE}/images/chattamesh/chattamesh-mark.png",
            "width": 512,
            "height": 512,
        },
        "description": (
            "A volunteer-run community MeshCore LoRa mesh radio network serving "
            "Chattanooga, Tennessee and the surrounding Tennessee Valley."
        ),
        "parentOrganization": {
            "@type": "Organization",
            "name": "TennMesh",
            "url": "https://tennmesh.com/",
        },
        "areaServed": {
            "@type": "GeoCircle",
            "geoMidpoint": {
                "@type": "GeoCoordinates",
                "latitude": 35.0456,
                "longitude": -85.3097,
            },
            "geoRadius": 80000,
        },
        "sameAs": [DISCORD],
    }


def website_node():
    return {
        "@type": "WebSite",
        "@id": f"{SITE}/#website",
        "url": f"{SITE}/",
        "name": "ChattaMesh",
        "inLanguage": "en-US",
        "publisher": {"@id": f"{SITE}/#org"},
    }


def breadcrumb_node(label, url):
    return {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE}/"},
            {"@type": "ListItem", "position": 2, "name": label, "item": url},
        ],
    }


def jsonld_for(meta, url):
    kind = meta["schema"]
    if kind == "home":
        graph = [
            org_node(),
            website_node(),
            {
                "@type": "WebPage",
                "@id": url + "#page",
                "url": url,
                "name": meta["title"],
                "description": meta["desc"],
                "isPartOf": {"@id": f"{SITE}/#website"},
                "about": {"@id": f"{SITE}/#org"},
                "primaryImageOfPage": {"@type": "ImageObject", "url": OG_IMAGE},
            },
        ]
    elif kind == "tech":
        graph = [
            {
                "@type": "TechArticle",
                "@id": url + "#article",
                "headline": meta["title"],
                "description": meta["desc"],
                "url": url,
                "inLanguage": "en-US",
                "isPartOf": {"@id": f"{SITE}/#website"},
                "publisher": {"@id": f"{SITE}/#org"},
                "author": {"@id": f"{SITE}/#org"},
                "image": OG_IMAGE,
                "proficiencyLevel": "Beginner",
                "about": [
                    {"@type": "Thing", "name": "MeshCore"},
                    {"@type": "Thing", "name": "LoRa mesh networking"},
                ],
            },
            breadcrumb_node(meta["crumb"], url),
        ]
    else:  # about
        graph = [
            {
                "@type": "AboutPage",
                "@id": url + "#page",
                "url": url,
                "name": meta["title"],
                "description": meta["desc"],
                "isPartOf": {"@id": f"{SITE}/#website"},
                "mainEntity": {"@id": f"{SITE}/#org"},
            },
            breadcrumb_node(meta["crumb"], url),
        ]
    return {"@context": "https://schema.org", "@graph": graph}


# ------------------------------------------------------------------ head block

def build_block(meta):
    url = SITE + meta["path"] if meta["path"] != "/" else SITE + "/"
    t, d = html.escape(meta["title"]), html.escape(meta["desc"])
    ld = json.dumps(jsonld_for(meta, url), indent=2, ensure_ascii=False)
    ld = "\n".join("  " + line for line in ld.splitlines()).lstrip()

    return f"""{START}
<title>{t}</title>
<meta name="description" content="{d}">
<link rel="canonical" href="{url}">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">

<meta property="og:type" content="website">
<meta property="og:site_name" content="ChattaMesh">
<meta property="og:locale" content="en_US">
<meta property="og:title" content="{t}">
<meta property="og:description" content="{d}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{OG_IMAGE}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{html.escape(OG_ALT)}">

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{t}">
<meta name="twitter:description" content="{d}">
<meta name="twitter:image" content="{OG_IMAGE}">
<meta name="twitter:image:alt" content="{html.escape(OG_ALT)}">

<meta name="geo.region" content="US-TN">
<meta name="geo.placename" content="Chattanooga, Tennessee">
<meta name="ICBM" content="35.0456, -85.3097">

<link rel="sitemap" type="application/xml" href="/sitemap.xml">

<script type="application/ld+json">
{ld}
</script>
{END}"""


NOINDEX_BLOCK = f"""{START}
<meta name="robots" content="noindex,follow">
<link rel="canonical" href="{SITE}/setup-information">
{END}"""


# ----------------------------------------------------------------- injection

FENCE_RE = re.compile(re.escape(START) + r".*?" + re.escape(END) + r"\n?", re.S)
TITLE_RE = re.compile(r"[ \t]*<title>.*?</title>\n?", re.S | re.I)
VIEWPORT_RE = re.compile(r'^.*<meta[^>]+name="viewport".*$', re.M | re.I)


def inject(src, block, drop_title=True):
    src = FENCE_RE.sub("", src)
    if drop_title:
        # The block re-emits it; stripping first is what makes re-runs safe.
        src = TITLE_RE.sub("", src)
    m = VIEWPORT_RE.search(src)
    if not m:
        raise SystemExit("no viewport meta to anchor against")
    return src[: m.end()] + "\n" + block + src[m.end():]


# ------------------------------------------------------------------ QA gate

class Walk(HTMLParser):
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
            "meta", "param", "source", "track", "wbr"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.errors = [], []

    def handle_starttag(self, tag, attrs):
        if tag not in self.VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in self.VOID:
            return
        if not self.stack:
            self.errors.append(f"stray </{tag}>")
        elif self.stack[-1] == tag:
            self.stack.pop()
        elif tag in self.stack:
            while self.stack and self.stack.pop() != tag:
                pass
        else:
            self.errors.append(f"unmatched </{tag}>")


def qa(name, text):
    errs = []
    w = Walk()
    w.feed(text)
    errs += w.errors
    if w.stack:
        errs.append(f"unclosed: {w.stack}")
    if text.count("<title>") != 1:
        errs.append(f"{text.count('<title>')} title elements")
    if text.count("<style>") != text.count("</style>"):
        errs.append("style tag imbalance")
    if "<style>\n<style>" in text or "<style><style>" in text:
        errs.append("duplicate <style> -- stylesheet will not apply")
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>',
                         text, re.S):
        try:
            json.loads(m.group(1))
        except json.JSONDecodeError as e:
            errs.append(f"invalid JSON-LD: {e}")
    if name in PAGES and text.count('rel="canonical"') != 1:
        errs.append("canonical count != 1")
    return errs


# ------------------------------------------------------- sitemap and robots

# Home carries the most weight, the two reference pages next, About last.
PRIORITY = {"/": "1.0", "/announcements": "0.9", "/getting-started": "0.9",
            "/setup-information": "0.9", "/hardware": "0.8",
            "/videos-welcome": "0.7", "/videos-meetings": "0.6",
            "/videos-information": "0.6", "/funding": "0.6", "/about": "0.5"}


def write_sitemap(outdir, lastmod):
    rows = []
    for name, meta in PAGES.items():
        if not os.path.exists(os.path.join(outdir, name)):
            continue
        loc = SITE + ("/" if meta["path"] == "/" else meta["path"])
        rows.append(
            "  <url>\n"
            f"    <loc>{loc}</loc>\n"
            f"    <lastmod>{lastmod}</lastmod>\n"
            "    <changefreq>monthly</changefreq>\n"
            f"    <priority>{PRIORITY.get(meta['path'], '0.5')}</priority>\n"
            "  </url>"
        )
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           + "\n".join(rows) + "\n</urlset>\n")
    open(os.path.join(outdir, "sitemap.xml"), "w", encoding="utf-8").write(xml)
    return len(rows)


ROBOTS = f"""# chattame.sh -- ChattaMesh community mesh radio network
# Everything here is public reference material. Crawl it.

User-agent: *
Allow: /

# The merged pages replaced these in v1.1; they carry a noindex as well.
Disallow: /settings-explained-uc
Disallow: /information-v1

Sitemap: {SITE}/sitemap.xml
"""


# ---------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="public")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    if not os.path.isdir(args.dir):
        raise SystemExit(f"no such directory: {args.dir}")

    failed = False
    seen = set()
    for name in sorted(os.listdir(args.dir)):
        if not name.endswith(".html"):
            continue
        p = os.path.join(args.dir, name)
        src = open(p, encoding="utf-8").read()

        if name in PAGES:
            block = build_block(PAGES[name])
            seen.add(name)
        elif name in RETIRED:
            block = NOINDEX_BLOCK
        else:
            print(f"  skip   {name}  (not in page table)")
            continue

        out = inject(src, block, drop_title=(name in PAGES))
        errs = qa(name, out)
        if errs:
            failed = True
            print(f"  FAIL   {name}")
            for e in errs:
                print(f"         - {e}")
            continue

        if args.check:
            state = "would change" if out != src else "up to date"
            print(f"  ok     {name}  ({state})")
        else:
            open(p, "w", encoding="utf-8").write(out)
            print(f"  wrote  {name}  ({len(out):,} bytes)")

    missing = set(PAGES) - seen
    if missing:
        print(f"\n  note: page table has no file for {sorted(missing)}")

    if failed:
        sys.exit(1)

    if not args.check:
        stamp = datetime.date.today().isoformat()
        n = write_sitemap(args.dir, stamp)
        open(os.path.join(args.dir, "robots.txt"), "w",
             encoding="utf-8").write(ROBOTS)
        print(f"  wrote  sitemap.xml  ({n} urls, lastmod {stamp})")
        print("  wrote  robots.txt")

    print("\nSEO gate passed.")


if __name__ == "__main__":
    main()
