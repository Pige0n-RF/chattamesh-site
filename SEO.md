# ChattaMe.sh v1.1 — SEO

## Already applied

The four pages in `public/` have the block injected, and `sitemap.xml`,
`robots.txt`, and `images/og-card.png` are in place. Nothing to do before
deploy. To re-run after a content edit:

```bash
python3 seo.py                # ./public, also rewrites sitemap.xml + robots.txt
python3 verify_seo.py public  # render gate (needs playwright + chromium)
```

`seo.py --check` reports without writing.

Re-run it after any content edit. Everything it writes is fenced between
`<!-- seo:start -->` and `<!-- seo:end -->`, and the fence is stripped before
each pass, so re-running is byte-identical rather than additive. The page's own
`<title>` is removed and re-emitted inside the fence — there is exactly one
title element afterwards, which the gate checks.

## What lands in each head

| | |
|---|---|
| `<title>` | unique per page, 49–59 chars |
| `<meta name="description">` | unique per page, 149–162 chars |
| `<link rel="canonical">` | extensionless absolute URL |
| `<meta name="robots">` | `index,follow,max-image-preview:large,max-snippet:-1` |
| Open Graph | type, site_name, locale, title, description, url, image (+ dimensions and alt) |
| Twitter | `summary_large_image` with title, description, image, alt |
| Geo | `geo.region`, `geo.placename`, `ICBM` at 35.0456, −85.3097 |
| JSON-LD | see below |

Canonicals are extensionless (`/getting-started`, not `/getting-started.html`).
Cloudflare's asset handler serves the extensionless form and 301s the `.html`
one, so that's the URL that should be indexed. If you ever change
`html_handling` in `wrangler.jsonc`, the canonicals have to move with it.

## Structured data

Home carries an `@graph` with `Organization`, `WebSite`, and `WebPage`. The
Organization node names TennMesh as `parentOrganization` and sets `areaServed`
to an 80 km `GeoCircle` around downtown Chattanooga — that geographic claim is
the part most likely to help you on local queries.

Getting Started and Setup & Information are `TechArticle` plus a two-level
`BreadcrumbList`. About is `AboutPage` with the Organization as `mainEntity`.

Deliberately **not** used: `HowTo` (Google retired the rich result in 2023, so
it's markup with no upside) and `SearchAction` (there's no site search to point
it at, and claiming one you don't have is a quality flag).

## Retired pages

`settings-explained-uc.html` and `information-v1.html` are already deleted, so
nothing was written for them. `robots.txt` still disallows both paths, and if
either file ever reappears `seo.py` will give it `noindex,follow` plus a
canonical pointing at Setup & Information — so anything Google crawled under
v1.0 falls out of the index instead of competing with the merged page.

## Assets

`public/images/og-card.png` is 1200×630, built from the badge's own mark
(`og-card.svg` is the source). Text is converted to outlines with real advance
widths from the `hmtx` tables rather than left as `<text>`, so it renders the
same everywhere without a font dependency — same reasoning as the exported logo
marks using literal hex instead of `var()` tokens.

The JSON-LD `logo` field points at your existing
`images/chattamesh/chattamesh-mark.png`, which is already 512×512 — no second
copy of the mark. `seo-assets/og-card.svg` and `make_card.py` are the build
source for the card and are deliberately outside `public/`.

## Not automated — worth doing once

1. **Google Search Console** — verify `chattame.sh` via the Cloudflare DNS TXT
   method, then submit `https://chattame.sh/sitemap.xml`. Bing Webmaster Tools
   can import the GSC property directly.
2. **Pick one hostname.** `chattamesh.com` and `chattame.sh` both resolve. Every
   canonical here points at `chattame.sh`; add a Cloudflare bulk redirect from
   `chattamesh.com/*` → `chattame.sh/$1` (301) so the two don't split authority.
3. **Get linked.** For a site this size, inbound links from tennmesh.com,
   MtnMesh, NashMesh, the MeshCore community lists, and any Chattanooga
   maker/ham club page will move ranking far more than anything on-page.
4. **Alt text.** The gate checks for one `h1` per page but doesn't audit `alt`
   attributes. The inline SVG diagrams should carry `role="img"` and
   `aria-label` — good for screen readers and for image understanding both.

## Gates

`seo.py` runs an HTMLParser tag walk, a `<style>` balance and duplicate check,
`json.loads` on every JSON-LD block, and a canonical count, and refuses to write
a file that fails. `verify_seo.py` then loads each page in real Chromium and
reads computed `backgroundColor` off the live DOM — the duplicate-`<style>` bug
parsed clean on disk and still rendered white, so markup inspection alone isn't
enough. It also asserts one `<title>`, one `<h1>`, and title/description inside
sane length bands.
