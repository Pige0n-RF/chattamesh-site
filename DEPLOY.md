# ChattaMesh deployment notes

*Change history and design decisions. Start with README.md for how to build and deploy.*

# Deploying chattame.sh

The site is now **static only**. Dropping the live feed removed the one thing
that needed server code, so there is no longer any Worker script, no Durable
Object, no `/api/nodes`, no `/live`, and no `LIVE_API_KEY` to manage.

If you still have `src/` and the `.dev.vars` / secret from the old setup, they
can go. Nothing references them.

## Project layout

```
chattamesh/
├── wrangler.jsonc
├── public/                          served as static assets
│   ├── index.html
│   ├── getting-started.html
│   ├── setup-information.html       Settings Explained + Information, merged
│   ├── about.html
│   ├── apple-touch-icon.png
│   ├── js/
│   │   └── mesh-bg.js               ambient background, no network calls
│   └── images/
│       ├── chattamesh/              our marks
│       │   ├── chattamesh-badge.svg / .png
│       │   ├── chattamesh-mark.svg / .png
│       │   ├── chattamesh-wordmark.svg / .png
│       │   ├── chattamesh-wordmark-currentcolor.svg
│       │   └── chattamesh-favicon.svg
│       └── neighbors/               partner marks
│           ├── mtnmesh.svg
│           ├── nashmesh.png
│           └── fetch-logos.sh       fills in the remaining three
└── (src/ no longer needed)
```

## wrangler.jsonc

Assets-only. Drop the `durable_objects`, `migrations`, and `main` entries if
they're still there:

```jsonc
{
  "name": "chattamesh",
  "compatibility_date": "2025-01-01",
  "assets": { "directory": "./public" }
}
```

With no `main`, Wrangler deploys the directory as a static site and every
request is served straight from the edge.

## Before the first deploy: fetch the remaining partner logos

Two partner marks are committed (`mtnmesh.svg`, `nashmesh.png` — both pulled
from the projects' own repos). The other three are only published on the
groups' live sites:

```bash
cd public/images/neighbors && ./fetch-logos.sh
```

This is optional. Every logo slot on the page falls back — local file, then the
group's own URL, then the slot simply empties and the heading underneath
carries the name. Nothing renders as a broken image either way. The partnership
section just looks better with the files in place.

## Deploy

```bash
npx wrangler deploy
```

## Checks before pushing

Two scripts guard the failure modes that have bitten this site before:

- `qa.py` — walks the HTML with `HTMLParser` for unclosed or crossed tags,
  counts `<style>` tags and CSS braces (the duplicate-`<style>` bug that
  silently drops the whole stylesheet), flags any `var(--token)` that isn't
  defined in `:root`, and resolves every local `href`/`src` against the build.
- `verify.py` — launches Chromium, reads computed `backgroundColor` and `color`
  off the live DOM so a stylesheet that parses but doesn't *apply* still fails,
  confirms the ambient canvas is sized and actually drawing, exercises the Copy
  buttons against the real clipboard, opens an accordion, and checks for
  horizontal overflow at 390px.

Both exit non-zero on failure. Run `qa.py` then `verify.py`.

## What changed in this revision

- **Settings Explained** and **Information** merged into a single
  **Setup & Information** tab. `settings-explained-uc.html` and
  `information-v1.html` are deleted — if either URL is already indexed, add a
  redirect to `setup-information.html`.
- The live-feed background was replaced with an ambient one. `mesh-bg.js` makes
  no network calls at all; link opacity went from `0.30` to `0.48`.
- Nav wordmark is now the outlined logo lockup rather than a webfont
  approximation, so it matches the badge exactly.
- Every CLI command has its own Copy button.
- New Local Partnership section on the home page; About page has real content.

## v1.1 — SEO

`seo.py` owns everything between `<!-- seo:start -->` and `<!-- seo:end -->` in
each page head, plus `public/sitemap.xml` and `public/robots.txt`. It strips the
fence before each pass, so re-running after a content edit is idempotent rather
than additive. Don't hand-edit inside the fence — change the `PAGES` table in
`seo.py` instead.

```bash
python3 seo.py                # inject + regenerate sitemap/robots
python3 verify_seo.py public  # render gate
```

Canonicals are extensionless (`/getting-started`, not `/getting-started.html`),
which relies on the Workers asset handler serving the extensionless form. If you
change `html_handling` in `wrangler.jsonc`, the canonicals have to move with it.

Two things still to do by hand, both outside the repo:

1. Verify `chattame.sh` in Google Search Console (Cloudflare DNS TXT) and submit
   `https://chattame.sh/sitemap.xml`.
2. 301 `chattamesh.com/*` → `chattame.sh/$1` with a Cloudflare bulk redirect.
   Both hostnames currently resolve and every canonical points at `chattame.sh`,
   so until that redirect exists the two split link authority.

See `SEO.md` for the full picture.

## v1.3 — Hardware

New page `public/hardware.html`, reachable from a Hardware dropdown in the nav
on every page (Companions / Repeaters / Antennas / DIY, each an anchor into the
one page). The menu is `position:fixed` and placed from the trigger's bounding
box on open — `.nav-tabs` is an `overflow-x:auto` scroller, so an absolutely
positioned child gets clipped by it. It closes on outside click, Escape, and
resize, and re-places on scroll.

`verify.py` now scopes its tab assertion to `.nav-tabs > a`, since the menu's
own anchors are also `<a>` inside `.nav-tabs` and were being counted as tabs.
It also exercises the dropdown: hidden on load, four correct hrefs when open,
on-screen at 390px, closes on Escape.

Page content is generated by `build_hardware.py`, which rebuilds
`hardware.html` wholesale off the About shell so it always picks up the current
nav, footer and token block. Edit the data structures in that script, not the
HTML — a hand edit is lost on the next run. Order after any content change:

```bash
python3 build_hardware.py
python3 seo.py
python3 qa.py && python3 verify.py && python3 verify_seo.py public
```

Each of the 24 products has a photo slot at `images/hardware/<slug>.jpg` — run
`build_hardware.py` to print the slug list. Until a `.jpg` lands, the `<img>`
`onerror` drops it and the placeholder frame behind it shows, same pattern as
the partner logos. Both gates know these are expected-empty: `qa.py` counts
them, `verify.py` filters them out of its 404 check.

Still open:

- **All 23 product shots are in.**
- **Battery cells listed don't match the photos.** The 18650 card names Samsung
  30Q/35E and Panasonic NCR18650GA but shows a Molicel P28A; the 21700 names
  Samsung 40T and Molicel P42A but shows a Molicel P50B. Either the copy or the
  photos should move.
- **Atlavox RP-SMA** — the card now says to order RP-SMA for a Wio Tracker, but
  the linked listing is the SMA version. A direct RP-SMA link would be better.

### v1.3 revisions

- Discord invite moved from `aaPyXVrsc` to `XF354A3e9m` — 11 instances across all
  five pages plus the JSON-LD `sameAs`. The four other `discord.gg` links on the
  home page belong to partner meshes and were left alone.
- The Basic/Alright/Cooking/Gas/Straight Fire ranking chips are gone, along with
  the `.tier-*` rules. Station G3 keeps an Unverified marker, now `.chip-warn`.
- Companion, repeater and board copy cut back to the essentials — no voltages,
  FCC IDs, silicon part numbers or rail warnings. Boards are stack plus coverage.
- The vendor/barrel-converter note above the coax table was removed.

### v1.3 product photos

`prep_images.py` normalises supplied photos into `public/images/hardware/` as
WebP **with alpha**, so shots sit on the card colour rather than in a white box.
Three paths, picked per file:

- `keep` — the file already has a real cut-out; use its alpha as-is
- `key` — flat studio backdrop; flood-fill in from the four corners, erode a
  pixel and soften, then make that region transparent
- `photo` — an environmental shot (a node on a fence, a product on a desk).
  There's no backdrop to remove, so it keeps its own and gets letterboxed with
  its sampled border colour

Keep-vs-key is decided from the corner alpha, not from whether the file has an
alpha channel. Those are different claims: `atlavox_whip.png` has alpha *and* an
opaque white backdrop, and trusting the channel alone left it as a white box on
the card. Only the two `photo` files are declared by hand.

Keying is not applied to those two. Flood-filling a lifestyle shot eats into the
subject and leaves a ragged edge — it was tried and it looked it.

Each shot is trimmed to its content bounding box, then letterboxed onto an
800x500 canvas. The slot CSS is `object-fit:cover`, so matching 16:10 up front
is what stops a centre crop decapitating a 45-inch antenna, and the trim makes
the product as large as the frame allows.

Because the shots are transparent, the placeholder frame behind them showed
straight through. Each `<img>` now sets `.has-shot` on its parent `onload`, and
`.hw-shot.has-shot .ph` hides the icon.

The first `wiotracker.jpg` was not used — it was PWRD-branded hardware, not a
Wio Tracker. The MeshCore-branded file supplied afterwards fills that slot.

### v1.3 Upper Cumberland logo

`images/neighbors/ucmesh.svg` is UCMesh's own dark animated wordmark, dropped
into the existing partner slot (`.png` -> `.svg` in `index.html`). It sits in an
`<img>` like the others rather than being inlined, and both of the things that
could have broken there were checked in Chromium: the Josefin Sans `@font-face`
is a base64 woff2 inside the file, and the node pulse is SMIL `<animate>`.
Both run in an `<img>`-referenced SVG, so no markup change was needed. It's out
of the deferred lists in `qa.py` and `verify.py`.

TennMesh is now the only partner logo still missing — `fetch-logos.sh` is
outstanding for that one alone.

### Rev1.1.2

- Hardware tab is a real `<a href="hardware.html">`; the menu opens on hover and
  on keyboard focus rather than on click. On touch (`hover: none`) the first tap
  opens the menu and the second follows the link, so the sub-sections stay
  reachable without a pointer.
  - Escape sets a `dismissed` flag before `close(); btn.focus()`. Without it the
    focus fires the open-on-focus handler and the menu reopens instantly —
    `verify.py` caught this, and it now also asserts the tab is an `<a>` with
    the right `href`.
  - `verify.py` hovers instead of clicking, and parks the pointer off the nav
    between pages: Playwright keeps pointer position across navigations, so the
    menu was already open on the next page's load check.
- `.skyline-frame` gets a `mask-image` gradient so the ridge fades out instead
  of stopping at a hard horizontal edge. Index and Getting Started.
- Partner logo wells went from a 64px strip to a 120px panel with the mark
  centred, so wordmarks read at roughly 1.5x.
- About: badge beside the copy (stacked above it under 900px), plus a
  Community Involvement section. `main` is `display:flex` in the shared shell,
  so About's two `.wrap` blocks needed a single full-width `.about-page` parent
  — without it they laid out side by side and overflowed 200px at 390px.
- Hardware: `View listing` is now a `Buy Now` button with a cart glyph.
  Intro copy, Nebra and Heltec V4-R8 descriptions replaced.
- Image prep: flood-fill seeds run the whole perimeter, not just the corners
  (the Muzi shot has a lighter reflective wedge at the bottom centre that no
  corner seed reached, and it survived as a white blob). The three Rokland
  antennas are white fiberglass on white and get `thresh=10` — the default
  walked straight through the mast and cut the antenna in half.
- Footer reads "Proud Partner of". The TennMesh logo was already wired there
  with a remote fallback, so it renders live even with `tennmesh.png` absent.

### Ka0sComTech tree repeater

Third card in Repeaters, with a CHATTAMESH coupon carried in the query string
of the Etsy link (`&coupon=CHATTAMESH`) — if that link is ever edited by hand,
keep the parameter or the discount stops applying.

The supplied photo is portrait, a node hanging in a pine against sky. Letter-
boxed whole it would sit in tall bars of sky, so `prep_images.py` gained a
`CROP` table: a per-file pre-crop in source pixels, applied before the trim and
letterbox. It's the only entry so far.

### Two versions

`make_variant.py` derives a "Discord coming soon" build from `public/` into
`public-soon/`. It is a generator, not a fork: rerun it after any change to the
main site and the two stay in sync. Never hand-edit `public-soon/` — it is
deleted and rebuilt on every run.

```bash
python3 make_variant.py          # public/ -> public-soon/
```

What it changes, all keyed off the one ChattaMesh invite string:

- Nav tab becomes a non-interactive `<span>` reading "Discord Coming Soon".
  It restates the tab typography and the 16px glyph size, because those rules
  are scoped to `.nav-tabs a` and this deliberately isn't a link.
- Every CTA button (`btn-discord` and the `btn-ghost` on the high-site card)
  becomes a `.discord-soon` panel: dashed border, muted, glyph above the label.
  Styled so it doesn't read as tappable.
- Inline prose links become plain text with "(coming soon)".
- The JSON-LD `sameAs` array is dropped — there's no public profile to claim.
- Three sentences that presented Discord as the live contact route are reworded
  ("Discord is the fastest way to reach us", "please get in touch on Discord",
  and the Hardware intro line).

The script asserts the invite string is absent from every page afterwards, and
prints the partner invites it kept. The four partner meshes' Discord links
(TennMesh, NashMesh, NC Mesh, Mountain Mesh) are theirs and stay live.

### REV2

- **Videos tab** — external link to the YouTube channel, sitting directly left of
  Discord, so the three external links (Live Maps, Videos, Discord) group at the
  right end of the bar. The mark is YouTube's, with the plate on `currentColor`
  (so it inherits `--signal`) and the triangle left white; that is what makes the
  "red play button" read as ChattaMesh purple. Same treatment on the About page's
  `.btn-youtube`, beside the Discord button, plus a prose link.
- **UHF / VHF / HF** — new top-level Hardware section and a fifth entry in the
  Hardware dropdown. ChattRadio is its first card.
- **DIY Supplies** now runs Enclosures / Boards / Batteries / Solar panels /
  Solar managers / Coax whips & cable. The panel voltage-regulator warning is a
  callout above Solar managers, not buried in a card.
- **New cards**: GAT562 30s Kit and LILYGO T-ECHO (Companions), Heltec V3
  (Boards), SoShine 12 W (Solar panels), Waveshare manager (Solar managers).
  PVC hinge cover and Aluminum Nebra swapped their "search for it" notes for
  real listings.
- **Amazon links are stored as `https://www.amazon.com/dp/<ASIN>`.** The supplied
  URLs carried `dib=` session blobs and `qid=` timestamps that go stale; the
  short form is canonical and resolves to the same listing. Keep that shape.
- The battery callout now reads "not linking Amazon **for cells**" — the page
  links Amazon elsewhere now, and the warning is specifically about counterfeit
  cells, so the old wording read as a contradiction.

`verify.py` gained three things: the nav assertion is a full-list compare rather
than a prefix (which is what pins Videos to the left of About), it tolerates the
coming-soon build where the Discord tab is a `<span>`, and it checks every
dropdown `#target` actually exists on hardware.html — a menu item pointing at a
missing id silently dumps people at the top of the page.

`prep_images.py` resolves each source by name across both upload roots. A resumed
session can leave some files under the harness upload dir with a hash prefix
instead of in the shared uploads folder, and hard-coding one root broke the
rebuild. The NC Mesh logo step is skipped when its source is absent, since the
built file is committed.

### Regions group starts collapsed

`patch_regions_collapsed.py`. The parent toggle on Setup & Information shipped
expanded, so the page opened with three long sections already unrolled; its three
children were already collapsed, so the group is now consistent. Collapsed the
page is 2,699px instead of 3,586px, and Projected Channel Scope Alignments is
reachable without a long scroll.

The initial `hidden` goes on the three sections the script drives by id
(`scopes`, `standard-repeater`, `border-repeater`), not on the
`regionsGroupContent` wrapper. Put it on the wrapper and the first click would
unhide the sections while the wrapper stayed shut.

This broke an existing assertion in `verify.py` that clicked `#regionsToggle`
directly: that child now sits inside a collapsed parent and is not reachable
until the parent opens, which is the real journey a reader takes. The check
opens the parent first. A new assertion pins the behaviour — collapsed on load,
opens on click, and the children stay individually collapsed when it does.

### Local Radio Clubs

New `#clubs` section on the home page, under the partner meshes. Three cards:
Tri-States (W4GTA), Chattanooga (W4AM), Cleveland (KA4J). Assets are trimmed
transparent PNGs in `public/images/clubs/`, built by the CLUBS block in
`prep_images.py` — PNG rather than WebP because each is flat colour with hard
edges, where PNG is both smaller and cleaner than lossy WebP.

**The logo wells carry a light plate (`#f4f5f8`), not the panel navy.** These
are third-party marks drawn for white backgrounds: W4GTA is dark navy line art
and is all but invisible on the dark card. The transparency is what makes the
plate work — W4AM's white disc sits on the plate as one shape instead of a white
box pasted onto navy. Recolouring someone else's brand mark to suit our palette
was the alternative, and it is not ours to do.

Club names and callsigns are taken from the marks themselves, so the section
reads "Tri-States" (the mark says TRI-STATES … INC.) and "Amateur" throughout.

### Videos

`build_videos.py` generates `videos-welcome.html`, `videos-information.html` and
`videos-meetings.html` off the About shell, the same way `build_hardware.py`
does. Add videos to the `VIDEOS` dict — `(youtube_id, title, blurb)` — and
re-run. Do not hand-edit the HTML; it is overwritten. An empty list renders the
page's empty state, which is the current state of all three.

The Videos tab is a dropdown to `videos-welcome.html` with YouTube / Welcome /
Information / Meetings. Adding it forced the nav script to be generalised: it
was written against a single menu (`querySelector('.nav-drop')`, ids baked in)
and now wires every `.nav-drop` independently, with its own timer and state, and
closes the others when one opens.

**Players are click-to-play facades.** A YouTube iframe pulls roughly a megabyte
and sets cookies before anyone presses play, so a page of eight videos would
cost eight megabytes for a visitor who watches none. `verify.py` confirms zero
requests reach YouTube before a click. Regular videos use
`youtube-nocookie.com`.

**The live stream.** `youtube.com/embed/live_stream?channel=UCaMYXY0MGVQ6HpgaP99y3BA`
plays whatever is streaming on the channel, with no per-stream id to maintain.
Two things to know:

1. When nothing is live it renders **"Video Play Configuration Error"**. That is
   the idle state, not a misconfiguration, and it reads like a broken page. The
   panel names that exact string so a visitor cannot mistake it for our fault,
   and offers `@ChattanoogaMesh/live` as a route that never shows it.
2. A static site cannot detect live-vs-offline. That needs the YouTube Data API
   and a key, which cannot be hidden in static assets. A Cloudflare Worker could
   proxy the check, but the site was deliberately made pure-static in v1.1 and
   this is not worth reversing that for.

The live player is deliberately on `www.youtube.com`, not the nocookie host:
`live_stream?channel=` is documented there and unverified on nocookie. It only
loads after a click either way.

`verify.py` now sweeps eight pages, drives both dropdowns from one table, and
asserts that opening the second closes the first — two menus share one script,
and hovering along the bar used to be able to leave both panels stacked.

### Featured playlist

The Welcome page leads with **MeshCore QuickStart by The Comms Channel**
(`PLshzThxhw4O4WU_iZo3NmNZOv6KMrUuF9`, 9 videos), embedded as
`youtube-nocookie.com/embed/videoseries?list=...` behind the same click-to-play
facade as everything else.

It is driven by a `playlist` key on the page's entry in `PAGES` — id, title,
author, author_url, count, blurb — so any of the three pages can feature one by
adding that key. No thumbnail: there is no stable per-playlist image URL, and a
branded panel beats hotlinking a first-video still that changes whenever the
playlist is reordered.

It is somebody else's work, so the panel names the channel, links to it, links
to the playlist, and says outright that it is not ours. Embedding is the
sanctioned way to show it — the player carries their branding and the views
count against their channel.

### MeshCore Decoded, and a playlist-id guard

The Information page features **MeshCore Decoded** by The Comms Channel, using
the same `playlist` key as the Welcome page. `count` is now optional, because
this one's video count could not be verified.

**Its id is unverified.** `PLPB1CPS5mUOY` is 13 characters; YouTube playlist ids
are normally 34 (or 18 for older lists), and the two other Comms Channel
playlists we link are both 34. It looks like the URL was truncated on copy. The
sandbox proxy denies youtube.com, and WebFetch cannot run JavaScript, so a valid
embed and a broken one are indistinguishable from here — this could not be
settled either way before shipping.

`build_videos.py` now runs `check_playlist()` on every build and prints a loud
warning for any id of an unexpected length, so the risk shows up on each rebuild
rather than living in one chat message. Replace the id with the full `list=`
value from the address bar and the warning goes away.

**Fixed while here:** the Welcome page credited `@TheCommsChannel`. The real
handle is `@The_Comms_Channel` — that link was a 404. Both pages use the correct
one now.

### Announcements

`build_announcements.py` generates `announcements.html` off the About shell.
The October meeting is a pinned panel at the top (MEETING dict: date, venue,
nested agenda); everything else lives in ITEMS as `(tag, title, html)`, newest
first. Add and re-run — the HTML is overwritten.

The meeting carries schema.org `Event` markup in the body, so the date, venue
and organiser are machine-readable. `seo.py` owns the head fence, so it goes in
as a second JSON-LD block rather than fighting it; `qa.py` parses every block on
the page either way.

Region scopes on the page are `us`, `us-east`, `us-southeast`, `us-tn`,
`us-tn-east`, `us-tn-cha` — consistent with the hierarchy on Setup &
Information. Neither `chattamesh` nor the deprecated `us-cha` appears.

### Two variant-generator bugs this surfaced

The inline Discord link on the announcements page is written
`<a class="dc-inline" href="...">`, and `make_variant.py` was matching
`<a href="INVITE"` — href had to be the first attribute. All three of its
replacement rules made that assumption, so the invite sailed straight through
into the "coming soon" build. Replacement is now a single pass that keys off the
tag's attributes in any order.

Worse: when that assertion fired, the run had already copied the tree and
converted some pages. It left a **half-built** `public-soon/` on disk — index
converted, announcements not — and that tree passed all three variant gates,
because each page looked internally consistent and nothing checked the whole
thing. `make_variant.py` now builds into `public-soon.building/`, sweeps every
html/xml/txt file in the output for the invite, and only renames the staging
directory into place once that passes. A failed run leaves the previous variant
untouched rather than a plausible-looking broken one.

## Rev 2.1 — release

Cut 2026-09-27. Nine pages. Two builds (`public/`, `public-soon/`), all three
gates passing on both.

Housekeeping done for the release:

- **`fetch-logos.sh` moved out of `public/`** to `tools/`. It was being served
  as a static asset at `/images/neighbors/fetch-logos.sh`. Rewriting it turned
  up two real bugs: a leftover `cd "$(dirname "$0")"` that would have landed it
  in `tools/` and broken every fetch, and it was still chasing `ncmesh.jpg` and
  `ucmesh.png` — both of which are now committed under different extensions
  (`ncmesh.png`, `ucmesh.svg`), so running it would have written duplicate files
  nothing references. It now fetches only `tennmesh.png`, which is genuinely the
  one outstanding logo.
- **`wrangler.example.jsonc` added.** No wrangler config was in the tree; the
  authoritative one lives in the deploying project. It ships as `.example` so it
  cannot overwrite a real one, and documents the `html_handling` setting that
  the extensionless canonicals depend on.
- **`README.md` added** as the front door: deploy, rebuild order, which files
  are generated, and the outstanding items. `DEPLOY.md` stays as the reasoning
  log.

## Rev 2.1.1 — nav bar fits all nine tabs

The bar was inheriting `max-width:1080px` from the shared `.wrap`, so the tabs
had 831px to render 929px of content. `.nav-tabs` is an `overflow-x:auto`
scroller with the scrollbar hidden, so the tail — Videos and Discord — simply
scrolled out of sight with no affordance, and read as cut off.

Fixed in three steps, largest win first:

1. `nav .wrap` gets `max-width:1280px` of its own. A nav spanning wider than the
   prose column is a normal pattern; the prose column stays 1080.
2. Tab padding 13px → 10px and the 2px inter-tab gap removed.
3. A ladder of step-downs before the scroller is reached at all: the wordmark
   hides at 1180px, padding and type tighten again at 1000px and 880px.

All nine tabs are now on the bar down to 900px. Below that it still scrolls, but
`.nav-tabs` only gets a `mask-image` fade on its right edge while
`scrollWidth > clientWidth` — a small script toggles `.is-scrollable` on resize
— so an overflowing bar looks scrollable on purpose instead of chopped.

`verify.py` now asserts the bar does not overflow at desktop width. **Adding a
tenth tab will fail that check**, which is the point: this failed silently the
first time.

Two things this exposed about patching in general:

- The same CSS rule is written three different ways across the nine pages — on
  one line in the generated ones, across several in the hand-edited ones, with
  differing indentation. A literal-text anchor matched nothing on six of nine
  and the script reported success on the one page it did match.
  `patch_nav_fit.py` matches a rule by selector and confirms it by body content,
  balancing braces to find the extent.
- The first attempt wrote index.html then asserted on page two, leaving the site
  half-patched. It now transforms every page in memory and writes only once all
  nine succeed — the same staging discipline `make_variant.py` got earlier.

The fix lives in `about.html`, which is the shell all generated pages are built
from, so re-running the builders preserves it.

## Rev 2.2 — mobile dropdowns, October meeting minutes

### The dropdowns were broken on every touch device. Two separate bugs.

**1. Synthetic `mouseenter` defeated the touch guard.** A tap fires
`mouseenter` *before* `click`. The hover handler opened the menu, and the click
guard — which only suppressed navigation while the menu was still hidden — then
found it open and let the link through. Tapping "Hardware" went straight to
hardware.html; the menu was never usable. Traced:

```
touchstart  hidden=true
mouseenter  hidden=true
mouseenter  hidden=false   <- hover opened it
click       hidden=false   <- guard sees "already open", navigates
```

Hover-open is now gated on `pointerType === 'mouse'` via pointer events.
Keyboard focus still opens; pointer focus does not, or a tap would open on
focus and navigate on the click behind it.

**2. The Rev 2.1.1 scroll fade made the menu invisible.** The fade was a
`mask-image` on `.nav-tabs`. Masking clips the element's whole painted subtree,
and the dropdown panel is a descendant — `position:fixed` does not exempt it.
Below 900px, exactly where the bar overflows and the fade switches on, a
forced-open menu rendered as nothing at all. The fade is now an overlay
pseudo-element on `nav`, which is not an ancestor of the panel.

**Why the gates missed both:** `verify.py` tested mobile by resizing the desktop
viewport. A narrow desktop window still reports `hover: hover` and a fine
pointer, so the tap path was never executed. It now runs a real touch context
(`has_touch`, `is_mobile`) and asserts first-tap-opens, that the panel is
actually *measurably visible*, and that a second tap follows the link. The
visibility check is the one that would have caught bug 2.

### Announcements

Restructured for after the meeting rather than before it:

- **Next meetings** panel, both TBD, with the cadence the group settled on
  (in person quarterly, Discord monthly) so "TBD" reads as not-yet-dated rather
  than abandoned.
- **Last meeting, October 3 2026** — archived stream behind the usual
  click-to-play facade (`&t=1545s` carried through as the embed's `start`),
  thanks, full minutes, donations and treasury.
- The minutes renderer is recursive now; the funding options nest three deep.
- The `Event` JSON-LD is gone. With no date there is no event to mark up, and
  schema.org requires `startDate`. It comes back when a date does.

The October stream is also the first entry on `videos-meetings.html`, which had
been showing its empty state.

**Its title is mine, not YouTube's** — "ChattaMesh meeting — October 3, 2026".
The fetch proxy rate-limited youtube.com and instructed no retry, so the real
title could not be read. Worth correcting in `build_videos.py` if it differs.

`i.ytimg.com` joined the gate's offline-host list: video thumbnails are
third-party and the sandbox proxy denies YouTube. A facade whose still fails to
load keeps its panel and play button, so it degrades cleanly.

## Rev 2.2.1 — packaging fix

**Rev 2.2 shipped without `js/yt.js`.** The shared facade module existed in the
working tree but no page in the packaged zip referenced it, so the archived
meeting stream deployed as a bare panel with no thumbnail, and the player still
carried `&start=1545`. Nothing was wrong with the source; the bundle was cut
before those files landed. 2.2.1 is the same source, packaged correctly.

Worth noting for next time: the gates all pass against `public/`, and the
release step copies `public/` into a zip. Nothing verified that the *zip* was
built from the tree the gates had just checked. The Rev 2.1 release did unpack
its own artifact and gate that; this one did not.

### How thumbnails work now

`public/js/yt.js` is one module for the whole site. Any element carrying
`data-yt` gets a still injected automatically — no API key needed, since
YouTube serves thumbnails at a URL derived from the video id. It tries
`maxresdefault.jpg` (true 16:9, but not generated for every upload) and falls
back to `hqdefault.jpg` (always present, 4:3, letterbox cropped off by
`object-fit:cover`). If neither resolves the `<img>` removes itself and the
panel shows as before.

Facades are real links to YouTube, so they work with the script blocked;
`yt.js` only calls `preventDefault()` once it has a player to swap in. Nothing
reaches YouTube until a click.

Two facades still have no thumbnail, and cannot:

- **Playlist panels** (`data-list`) — YouTube publishes no per-playlist image,
  and deriving one needs the first video's id, which is not in the playlist URL.
- **The live panel** (`data-live`) — there is no fixed video to draw a still
  from until something is streaming.

Both stay as branded panels by design.

The archived October stream now plays from the beginning; the `data-t` offset
is gone and the copy reads "Plays from the beginning."

## Rev 2.2.2 — player box matches the thumbnail

The archived-stream facade on Announcements carried `max-height:330px` next to
`aspect-ratio:16/9`. Max-height wins, so the box rendered ~2.98:1 at desktop
width. Two consequences, both visible:

- `object-fit:cover` cropped the thumbnail to a thin horizontal slice of the
  frame.
- The 16:9 player that replaced it pillarboxed inside the too-wide box, so the
  video played smaller than the still it came from.

The cap is now on **width** (`max-width:760px`, centered) instead of height, so
the box keeps the video's shape. Measured facade-vs-player at five widths: both
sit at 1.78:1 from 1440px down to 390px. `.live-foot` shares the same max-width
so the caption stays with the player it belongs to.

Width is the right lever here: removing the cap entirely would give a 982x552
player at the top of a panel that also holds the full minutes, pushing them well
down the page.

`verify.py` now measures every `.vid-frame` and `.live-frame` across
Announcements, Meetings and Welcome and fails anything outside 16:9 by more than
0.05. The video pages were already correct; this stops the Announcements one
drifting back.

## Rev 2.3 — Funding page

New `funding.html`, generated by `build_funding.py` off the About shell. Tab
sits directly after About, which is where it belongs: both answer "who is this
and how does it work" rather than "how do I use it".

Three option cards, the transparency principle as a callout, then a four-row
ledger. Three of those rows are deliberately empty and share one "coming soon"
panel, so an unfilled section reads as not-yet-published rather than broken --
which matters more on this page than anywhere else on the site, since its whole
purpose is that money is accounted for in public. The Announcements minutes now
link through to it.

### Making room for a tenth tab

The bar was at exactly zero headroom after Rev 2.1.1 -- 928px needed, 928px
available -- so a tenth tab overflowed immediately. The overflow assertion added
in 2.1.1 caught it, which is what it was for.

Rather than shrink everything, the step-down ladder was re-spaced: padding and
type now tighten at 1100px (was 1000) and again at 940px, with a further step at
880px. All ten labels stay on the bar down to **860px**; below that the scroller
and its fade take over. No label was shortened and the nav container is still
1280px.

### One bug worth noting

`.ledger-figure` set the $100 to 2rem gold and had no effect: `.ledger-row p` is
(0,1,1) and a bare class is (0,1,0), so the generic rule won on both font-size
and colour. Qualified to `.ledger-row p.ledger-figure`. A reminder that the
element-qualified descendant rules in this stylesheet outrank bare utility
classes -- worth checking whenever a new one looks ignored.

## Rev 2.4 -- Hamfest, and money in one place

### Hamfest Chattanooga 2026

A new pinned-style card at the top of the announcement list: supplied banner,
venue, and the MeshCore panel. The date (October 16-17 2026) was not in the
supplied copy -- it came from the ARRL hamfest listing, which also confirms the
venue and names the Chattanooga Amateur Radio Club as sponsor. Flagged to Xach
rather than assumed correct. The panel's 4-5PM slot has no day attached in the
source copy; it is published without one.

The banner is `public/images/announcements/hamfest-2026.webp`, 1000x667, q74,
149 KB. `width`/`height` are set on the tag so the card doesn't reflow as it
loads, and it is `loading="lazy"` like every other below-the-fold image.

Three paragraph classes on that card (`.addr`, `.panel-head`, `.panelists`) are
written as `.ann p.addr` and so on. `.ann p` is (0,1,1); bare classes would have
lost on colour, size and margin -- the same trap that ate `.ledger-figure` in
Rev 2.3, checked for this time rather than discovered.

### Both Rev 2.3 open items are closed

**The two money figures no longer conflict** -- the treasury block is gone from
Announcements entirely, along with its CSS and the `treasury` field in `LAST`.
The funding ledger is now the only place a figure appears: $100 allocated toward
repeater boards, $0 currently pooled. The "Meeting donations" row was removed,
which also retires the "donated in cash at the 3 October meeting" line.

**The donor naming question is moot.** Jim asked not to be credited publicly.
Worth recording that he never was: the name appeared only in the meeting notes
sent to me, never in any generated page -- verified by grep across both builds
and all generators before saying so.

### Allocation rows

The resource-allocation entry is now a line item rather than a headline figure:
amount left, what it bought in the middle, date pushed right with `margin-left:
auto`. It is driven by an `ALLOCATIONS` list, so the next one is a tuple rather
than hand-written HTML. The date is wrapped in `<time datetime>` so it is
machine-readable as well as displayed in the US format Xach asked for.

Below roughly 460px the date wraps to its own line, still right-aligned. Left as
is -- the alternative is shrinking the description, which is the part people
actually read.

### UCMesh

Logo replaced with the supplied dark-mode badge SVG (42 KB, with the Josefin
Sans subset embedded as base64 woff2, so it renders the same without the font
installed). Checked against the other three partner logos: it sits at the same
88px wrap height.

Their Discord is live, so the inert "Discord coming soon" span on that card
became a real link. That was the last `.soon` span on index.html. The invite
joins the partner set `make_variant.py` deliberately preserves -- only
ChattaMesh's own invite is stripped from the variant build, and the run now
reports five partner invites kept rather than four.

## Rev 2.5 -- radio clubs as partners

Tri-States (W4GTA) moved out of "On the Ham Bands" and into the Local
Partnership section; GCARC added alongside it. Both are ham clubs, and the
section's h2 reads "The Meshes Around Us", which they are not -- so they sit
under their own `.partner-subhead` ("Radio clubs building it with us") below the
four mesh cards rather than mixed in among them. That keeps the heading honest
without renaming a section Xach did not ask to rename. The clubs section still
carries W4AM and KA4J.

**GCARC has no callsign badge.** Their site publishes no club callsign. The
abbreviation went into the `.club-call` badge at first, which, sitting in the
same amber mono tag as W4GTA next to it, reads as a callsign. Removed rather
than invented.

**Their logo is fetched, not committed.** The build sandbox can't reach
collegedalehams.org (proxy 403 on CONNECT, same as tennmesh.com), so
`tools/fetch-logos.sh` now takes both. The script's working directory moved up
one level to `public/images` so it can write into `neighbors/` and `clubs/`.
`qa.py`'s deferred set and `verify.py`'s OFFLINE list both learned about it.

The partner assertion in `verify.py` now pins all six names in DOM order, so it
fails if a club drifts above the meshes.

## Rev 2.6 -- Archived Events

The Hamfest ran 16-17 October, so it came off the top of the page and into a
collapsed "Archived Events" section at the foot of it, banner and panel intact.
Driven by an `ARCHIVED` list, newest first, so the next finished event is one
entry rather than a hand-moved block. The count in the summary ("1 past event")
is derived, and pluralises itself.

It is a native `<details>`, not the `wireToggle()` pattern from
setup-information.html. That script is inline in that page alone, and this page
is generated from the About shell, so reusing it would mean shipping a second
copy of it. `<details>` also collapses correctly with JS off and is
keyboard-accessible without any work. It is styled to match `.regions-toggle`
so the two read as the same control, which needs both
`summary::-webkit-details-marker` and `summary::marker` to suppress the default
triangle.

The archived banner goes back to `loading="lazy"`: it is below the fold and
behind a closed panel, so eager loading would cost every visitor 149 KB for
something most of them never open.

### Two bugs the gates caught

**`<style> x2 </style> x1`.** A CSS comment I wrote contained the literal text
`<style>` while explaining why this page does not reuse the other page's script.
`qa.py` counts those tags to check the block is balanced and does not care that
one was inside a comment. Reworded.

**`{arch_count}` rendered literally.** `MAIN` is assembled as an f-string, plus
a joined list, plus a trailing chunk -- and that trailing chunk was a plain
string. Everything before it interpolated, so the breakage was invisible until
the summary label read `{ARCH_COUNT}` on the rendered page. Marked `f`.

`verify.py` now checks the archive ships closed, opens on a click, is not empty
when open, and that past events stay out of the pinned area.

## Rev 2.7 -- Funding & Resource Committee

The committee draft is pinned at the top of Announcements and repeated as a
block on the funding page, which now shows the PayPal Pool as the chosen route:
Option 3 carries a "chosen" badge and a lit border, the status chip reads
"First draft -- open for feedback", and the intro says the decision is a draft
rather than settled.

**The names live in `committee.py`, not in either generator.** Both pages
publish the same five seats and the same account holder, and those change as
seats fill. Two copies of that list is exactly how the treasury figure ended up
disagreeing with itself in Rev 2.3, so the data, the seat renderer and the
`.fc-seats` CSS are imported by both. Filling a seat is one line in one file.

**There is no PayPal link, deliberately.** The pool opens once the committee is
seated, so "How to contribute" says that in as many words on both pages instead
of promising a link that does not exist. `committee.PAYPAL_URL` is `None` and
waiting; set it and both pages pick it up.

`#funding` is linked to the Discord invite everywhere it appears. The draft was
written for people already in that channel; on a public website the channel name
alone gives a reader nothing to click.

### The gate caught the pin order

`verify.py` asserted the pinned cards were exactly `["Next meetings", "Last
meeting"]`, so the new card broke it -- correctly, but for the wrong reason: the
assertion pinned an exact list when what matters is that the meeting cards keep
their relative order and nothing archived climbs above them. Rewritten to check
that instead, so the next pinned card does not trip it.

## Rev 2.8 -- Battlefield Races call for operators

Pinned above the committee draft, tagged "This Saturday". The event is 14
November, so this card has a short life and comes down (or moves into Archived
Events) once it is run.

**The chart is published twice.** The supplied graphic is 3040x3320 of dense
infographic -- six panels of timeline, duties, stations, kit and message format.
Squeezed into a phone-width card none of it is legible, and it is the only copy
of information an operator needs at 6am in the dark. So the card carries a
1400px display copy (183 KB) that links out to the full-size file (531 KB), and
restates every operational fact underneath it in real text: times, check-in
location, the parking cutoff, duties, kit list and message format. That text is
what works on a phone, in a screen reader and in search results; the picture is
the nice-to-have.

Emails are deliberately not repeated in the HTML. They are in the graphic
because Xach put them there, but a plain-text mailto on a public page is
scraped within days, so the card routes people to Discord and names the two
contacts by callsign instead.

## Rev 2.9 -- official race packet, aid stations renumbered

Xach sent the official 2026 packet at 3:20am on race morning. It disagrees
with the ChattaMesh ops graphic Rev 2.8 was built from, on the one detail that
matters most.

**Five of the six aid station numbers were wrong.** The packet's map numbers
them 1-6; the ops chart used a different order and only AS1 agreed:

    official 1 = chart AS1   (Lafayette Rd, Lap 2 start, mi 2/11/24)
    official 2 = chart AS3   (Brotherton Rd junction, mi 4/15)
    official 3 = chart AS5   (south loop, mi 9/21)
    official 4 = chart AS6   (Wilder Tower, mi 23)
    official 5 = chart AS2   (13.1 spur, mi 13/14)
    official 6 = chart AS4   (Jays Mill Rd, mi 17/18)

Every mesh message is prefixed with a station number, and Net Control, the
medics and race officials all work from the packet's numbering, so a MED
message from the wrong number routes help to the wrong point on a 26-mile
course. The card now leads with the conflict and the official table, and the
old ops graphic was deleted rather than kept alongside -- two numbering schemes
on one page is the failure mode, not the fix.

Other corrections from the packet: wheelchair half starts 7:27 (not 7:25);
roads into Barnhardt Circle close 5:30am (the chart said the lot closed at
6:45, which would have had operators setting off after the closure); 5K at
8:00, Jr Marathon at 10:00, course closes 2:00pm. The packet also marks a point
on Jays Mill Rd near mile 19 "Not an Aid Station" -- called out in the copy,
since it looks like one.

Both official course maps are published, marathon and half, each at a display
size and a full-size link. The half runs the inner loop only and does not reach
stations 5 or 6.

## Rev 3.0 -- the fund is real

The committee is seated, the pool is open, and the draft framing is gone from
both pages. Five Fund Stewards, named as they are in Discord.

**Handles are published verbatim, with no separate location field.** Three of
the five carry their own area ("| Cleveland", "| CHA"), so a `where` column
would have been redundant for them and invented for the other two. `SEATS` went
from (handle, area) tuples to a plain list, and the open-seat rendering came out
with it.

**The QR code is generated, not drawn, and it is verified before it ships.**
`tools/make-qr.py` reads `committee.PAYPAL_URL`, encodes at error-correction H
(it gets printed and photographed in daylight at hamfests) and then decodes its
own output back with OpenCV at both 564px and 180px, asserting it matches. A
wrong QR code is the worst bug on this site: it looks right, it scans, and it
sends money somewhere else. Nobody can spot it by eye, so the build checks it.
Re-run that script if the pool URL ever changes.

`committee.PAYPAL_URL` drives the link on both pages and the QR's contents from
one place. Set it back to None and both pages return to saying the pool is not
open rather than publishing a dead link.

Meetings: Discord monthly, 3rd Wednesday 7:00 PM, with the standing agenda
(Battlefield Marathon, Catoosa County EMA, infrastructure and deadzones) on the
card. In person stays quarterly, still TBD. The Discord card is listed first
now, since it is the one with a date on it.

### Open

Nothing outstanding on content. The remaining items are in README.md: the
uncommitted `tennmesh.png`, and the `chattamesh.com` -> `chattame.sh` redirect
before go-live.
