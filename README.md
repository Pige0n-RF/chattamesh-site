# ChattaMesh — Rev 2.9

Static site for chattame.sh. Ten pages, no framework, no build step at serve
time. Everything under `public/` is what deploys.

## Deploy

```bash
cp wrangler.example.jsonc wrangler.jsonc    # only if you don't already have one
npx wrangler deploy
```

If you already have a `wrangler.jsonc`, **keep yours** — it carries the account
and worker name the template can't know. The only setting that matters here is
`"assets": {"directory": "./public"}`.

Canonical URLs are extensionless (`/hardware`, not `/hardware.html`). That
relies on the Workers asset handler serving the extensionless form and 301ing
the `.html` one. If you change `html_handling`, change the canonicals in
`seo.py` to match or the two will disagree.

## What's in the box

```
public/                 the site — this is the deployable tree
  *.html                9 pages
  images/               30 product shots, club and partner logos, brand marks
  js/mesh-bg.js         ambient canvas background, no network calls
  sitemap.xml           generated
  robots.txt            generated
public-soon/            same site with the Discord invite removed (see below)
tools/fetch-logos.sh    fetches the one logo not committed
wrangler.example.jsonc  Cloudflare config template
```

Generators and gates live at the root. **The HTML is generated — don't hand-edit
it.** Four pages are built from data:

| Page | Built by | Edit this |
|---|---|---|
| `hardware.html` | `build_hardware.py` | the card lists in that file |
| `videos-*.html` | `build_videos.py` | `VIDEOS` and `PAGES` dicts |
| `announcements.html` | `build_announcements.py` | `MEETING`, `ITEMS`, `ARCHIVED` |
| `funding.html` | `build_funding.py` | `OPTIONS`, `ALLOCATIONS`, `LEDGER` |
| committee names | `committee.py` | `SEATS`, `HOLDER`, `PAYPAL_URL` |
| every head | `seo.py` | the `PAGES` table |

The others (`index`, `getting-started`, `setup-information`, `about`) are edited
directly — only their `<!-- seo:start -->` fence is generated.

## Rebuild after any change

```bash
python3 prep_images.py          # only when images change
python3 build_hardware.py
python3 build_videos.py
python3 build_announcements.py
python3 seo.py                  # inject heads, regenerate sitemap + robots
python3 make_variant.py         # public/ -> public-soon/

python3 qa.py                   # static: tags, CSS, JSON-LD, dead links
python3 verify.py               # real Chromium: renders, nav, accordions
python3 verify_seo.py public    # titles, descriptions, canonicals
```

All three gates must pass. `verify.py` needs Playwright and Chromium.

## The two builds

`public/` links the live Discord invite. `public-soon/` replaces every one of
them with a "Discord Coming Soon" panel — nav tab, CTA buttons, inline prose,
and the JSON-LD `sameAs`. Deploy whichever suits; they are otherwise identical.

`public-soon/` is **generated**, never hand-edited. `make_variant.py` deletes
and rebuilds it from `public/` on every run, so the two cannot drift. It builds
into a staging directory, sweeps every file for the invite, and only swaps in on
success — a failed run leaves the previous variant untouched rather than a
half-converted tree.

Partner meshes' own Discord links (TennMesh, NashMesh, NC Mesh, Mountain Mesh)
survive in both builds. Those are theirs.

## Known outstanding

**Two logos are not committed: `images/neighbors/tennmesh.png` and
`images/clubs/gcarc.png`.** Run `tools/fetch-logos.sh` once locally. The
build sandbox can reach neither tennmesh.com nor collegedalehams.org.
Nothing breaks without them: each card falls back to the live URL on the
owner's site, and then drops the image entirely rather than showing a broken
icon. `qa.py` lists both as deferred rather than failing on them.

**The funding page is the only place money is reported.** As of Rev 2.4 the
treasury block is gone from Announcements, so there is one figure in one place
rather than two that can disagree. The ledger reads: $100 allocated toward
repeater boards, $0 currently pooled. Donors are not named anywhere, by request
— keep it that way when adding rows.

**The live meeting player shows "Video Play Configuration Error" when nothing is
streaming.** That is YouTube's idle state for a channel-level live embed, not a
fault. A static site can't detect live-vs-offline — that needs the YouTube Data
API and a key, which can't be hidden in static assets. The panel on
`videos-meetings.html` names that exact string so a visitor can't mistake it for
a broken page.

**Before going live:** `chattamesh.com` and `chattame.sh` both resolve, and every
canonical points at `chattame.sh`. Add a Cloudflare bulk redirect
(`chattamesh.com/*` → `chattame.sh/$1`, 301) or the two split link authority.
Then verify in Google Search Console and submit `/sitemap.xml`.

---

Full change history, design decisions and the reasoning behind them are in
`DEPLOY.md`.
