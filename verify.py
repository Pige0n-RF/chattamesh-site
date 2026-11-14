#!/usr/bin/env python3
"""Real-browser verification.

The static gate can't catch a stylesheet that parses but doesn't apply -- the
duplicate-<style> bug looked fine on disk and rendered white. So: launch
Chromium, read computed styles back off the live DOM, and exercise the two
pieces of new interactive behaviour.
"""
import http.server
import functools
import socketserver
import os
import sys
import threading

from playwright.sync_api import sync_playwright

PUB = os.environ.get("PUB", "public")   # repo-relative so CI works
PORT = 8765
PAGES = ["index.html", "announcements.html", "getting-started.html",
         "hardware.html", "setup-information.html", "videos-welcome.html",
         "videos-information.html", "videos-meetings.html", "funding.html", "about.html"]

BG = "rgb(26, 29, 44)"      # --bg
TEXT = "rgb(237, 238, 242)"  # --text

fails = []


def serve():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=PUB)
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("127.0.0.1", PORT), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def main():
    serve()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        errors = []
        # The sandbox has no route to fonts.googleapis.com or to the neighbours'
        # sites, so their failures are environmental, not defects. Requests are
        # recorded by URL and the offline hosts filtered out; anything else --
        # a real 404 on our own assets, a JS exception -- still fails the run.
        OFFLINE = ("cdnjs.cloudflare.com", "fonts.googleapis.com", "fonts.gstatic.com", "tennmesh.com",
                   "images/neighbors/tennmesh.png",
                   "collegedalehams.org", "images/clubs/gcarc.png",
                   # Hardware product shots: empty slots by design until photos
                   # are gathered. Each <img> has an onerror that drops it back
                   # to the placeholder frame, so a 404 is cosmetic, not broken.
                   "images/hardware/",
                   # Video thumbnails are third-party and the sandbox proxy
                   # denies YouTube. A facade whose still fails to load still
                   # shows its panel and play button, so this is cosmetic here
                   # and fine in a real browser.
                   "i.ytimg.com")
        page.on("requestfailed",
                lambda r: errors.append("net " + r.url)
                if not any(o in r.url for o in OFFLINE) else None)
        page.on("response",
                lambda r: errors.append(f"{r.status} {r.url}")
                if r.status >= 400 and not any(o in r.url for o in OFFLINE) else None)
        page.on("pageerror", lambda e: errors.append("js " + str(e)))

        for name in PAGES:
            del errors[:]
            page.goto(f"http://127.0.0.1:{PORT}/{name}", wait_until="networkidle")

            # 1 -- the stylesheet actually applied
            bg = page.evaluate("getComputedStyle(document.body).backgroundColor")
            fg = page.evaluate("getComputedStyle(document.body).color")
            if bg != BG:
                fails.append(f"{name}: body background {bg}, expected {BG}")
            if fg != TEXT:
                fails.append(f"{name}: body color {fg}, expected {TEXT}")

            # 2 -- ambient canvas present, sized, behind content, drawing
            info = page.evaluate("""() => {
                const c = document.getElementById('mesh-bg');
                if (!c) return null;
                const cs = getComputedStyle(c);
                const ctx = c.getContext('2d');
                const d = ctx.getImageData(0, 0, c.width, c.height).data;
                let ink = 0;
                for (let i = 3; i < d.length; i += 4000) if (d[i] > 0) ink++;
                return {z: cs.zIndex, pos: cs.position, pe: cs.pointerEvents,
                        w: c.width, h: c.height, ink};
            }""")
            if not info:
                fails.append(f"{name}: no #mesh-bg canvas")
            else:
                if info["pos"] != "fixed" or info["z"] != "-1":
                    fails.append(f"{name}: canvas {info['pos']} z={info['z']}")
                if info["pe"] != "none":
                    fails.append(f"{name}: canvas intercepts pointer events")
                if info["w"] < 100 or info["h"] < 100:
                    fails.append(f"{name}: canvas unsized {info['w']}x{info['h']}")
                if info["ink"] == 0:
                    fails.append(f"{name}: canvas drew nothing")

            # 3 -- nav is the merged tab set, with the right one active.
            # Scoped to direct children: the Hardware dropdown's menu items are
            # also <a> inside .nav-tabs and would otherwise be counted as tabs.
            # Full list, not a prefix: this is what pins Videos to the left of
            # About and catches a reorder anywhere in the bar.
            tabs = page.eval_on_selector_all(
                ".nav-tabs > a", "els => els.map(e => e.textContent.trim())")
            want_tabs = ["Home", "Announcements", "Getting Started",
                         "Setup & Information", "About", "Funding",
                         "Live Maps", "Discord"]
            # In the coming-soon build the Discord tab is a non-interactive
            # <span>, so it is not among the direct <a> children.
            if page.query_selector(".tab-discord.is-soon"):
                want_tabs = want_tabs[:-1]
            if tabs != want_tabs:
                fails.append(f"{name}: nav tabs {tabs}")

            if name == "hardware.html":
                if not page.query_selector("#hwBtn.active"):
                    fails.append(f"{name}: Hardware tab not marked active")
            elif name.startswith("videos-"):
                if not page.query_selector("#vidBtn.active"):
                    fails.append(f"{name}: Videos tab not marked active")
            else:
                active = page.eval_on_selector_all(
                    ".nav-tabs > a.active",
                    "els => els.map(e => e.getAttribute('href'))")
                if active != [name]:
                    fails.append(f"{name}: active tab {active}")

            # 3b -- both dropdowns: closed by default, open on hover, right
            # items, on-screen, and independent of one another
            MENUS = [
                ("Hardware", "#hwBtn", "#hwMenu", "hardware.html",
                 ["hardware.html#companions", "hardware.html#repeaters",
                  "hardware.html#antennas", "hardware.html#diy",
                  "hardware.html#uhf-vhf-hf"]),
                ("Videos", "#vidBtn", "#vidMenu", "videos-welcome.html",
                 ["https://www.youtube.com/@ChattanoogaMesh",
                  "videos-welcome.html", "videos-information.html",
                  "videos-meetings.html"]),
            ]
            # Playwright keeps the pointer where it was across navigations, so
            # park it off the nav before asserting the menus start closed.
            page.mouse.move(4, 700)
            page.wait_for_timeout(250)

            for label, btn, menu, href, want in MENUS:
                if page.eval_on_selector(menu, "e => e.hidden") is not True:
                    fails.append(f"{name}: {label} menu not hidden on load")
                # The trigger is a real link, so clicking navigates. Hover.
                page.hover(btn)
                page.wait_for_timeout(140)
                items = page.eval_on_selector_all(
                    f"{menu} a", "els => els.map(e => e.getAttribute('href'))")
                if items != want:
                    fails.append(f"{name}: {label} menu items {items}")
                box = page.eval_on_selector(
                    menu, "e => { const r = e.getBoundingClientRect();"
                          " return [r.width, r.height, r.left, r.top]; }")
                if box[0] < 120 or box[1] < 100:
                    fails.append(f"{name}: {label} menu collapsed {box}")
                if box[2] < 0 or box[2] + box[0] > page.viewport_size["width"]:
                    fails.append(f"{name}: {label} menu off-screen {box}")
                page.keyboard.press("Escape")
                page.wait_for_timeout(140)
                if page.eval_on_selector(menu, "e => e.hidden") is not True:
                    fails.append(f"{name}: {label} menu did not close on Escape")
                if page.eval_on_selector(btn, "e => e.tagName") != "A":
                    fails.append(f"{name}: {label} tab is not a link")
                if page.eval_on_selector(btn, "e => e.getAttribute('href')") != href:
                    fails.append(f"{name}: {label} tab href wrong")

            # Two menus share one script now: opening the second must close the
            # first, or hovering along the bar leaves both panels stacked up.
            page.hover("#hwBtn")
            page.wait_for_timeout(140)
            page.hover("#vidBtn")
            page.wait_for_timeout(220)
            both = page.evaluate(
                "() => [...document.querySelectorAll('.nav-drop-menu')]"
                ".filter(m => !m.hidden).length")
            if both != 1:
                fails.append(f"{name}: {both} menus open at once")
            page.keyboard.press("Escape")
            page.mouse.move(4, 700)
            page.wait_for_timeout(200)

            # 3b2 -- every tab is actually on the bar at desktop width. Nine
            # tabs already overflowed the old 1080 container and the tail
            # scrolled out of sight silently; adding a tenth should fail here,
            # not in someone's browser.
            fit = page.evaluate(
                "() => {const t = document.querySelector('.nav-tabs');"
                " return [t.scrollWidth, t.clientWidth];}")
            if fit[0] - fit[1] > 2:
                fails.append(f"{name}: nav overflows by {fit[0]-fit[1]}px "
                             f"at {page.viewport_size['width']}px")

            # 3c -- every dropdown target must exist on hardware.html, or the
            # menu silently lands people at the top of the page
            if name == "hardware.html":
                hw_targets = MENUS[0][4]
                missing = page.evaluate(
                    "(hrefs) => hrefs.map(h => h.split('#')[1])"
                    ".filter(id => !document.getElementById(id))", hw_targets)
                if missing:
                    fails.append(f"{name}: menu targets missing {missing}")

            # 3d -- the Regions group on Setup & Information ships collapsed,
            # and its children stay individually collapsed when it opens
            if name == "setup-information.html":
                btn = "#regionsGroupToggle"
                if page.eval_on_selector(btn, "e => e.getAttribute('aria-expanded')") != "false":
                    fails.append(f"{name}: Regions group not collapsed on load")
                shown = page.evaluate(
                    "ids => ids.filter(i => {const e = document.getElementById(i);"
                    " return e && e.offsetParent !== null;})",
                    ["scopes", "standard-repeater", "border-repeater"])
                if shown:
                    fails.append(f"{name}: Regions sections visible on load {shown}")
                page.click(btn)
                page.wait_for_timeout(150)
                still = page.evaluate(
                    "ids => ids.filter(i => {const e = document.getElementById(i);"
                    " return e && e.offsetParent === null;})",
                    ["scopes", "standard-repeater", "border-repeater"])
                if still:
                    fails.append(f"{name}: Regions did not open {still}")
                kids = page.evaluate(
                    "ids => ids.filter(i => !document.getElementById(i).hidden)",
                    ["regionsContent", "standardRepeaterContent",
                     "borderRepeaterContent"])
                if kids:
                    fails.append(f"{name}: child sections auto-opened {kids}")
                page.click(btn)
                page.wait_for_timeout(150)

            # 4 -- brand wordmark rendered at a sane size
            box = page.eval_on_selector(
                ".brand-wordmark",
                "e => { const r = e.getBoundingClientRect(); return [r.width, r.height]; }")
            if not (60 < box[0] < 240 and 8 < box[1] < 26):
                fails.append(f"{name}: brand wordmark box {box}")

            # 5 -- footer copy
            foot = page.eval_on_selector(".footer-text", "e => e.textContent")
            if "The local group for MeshCore in Chattanooga, TN" not in foot:
                fails.append(f"{name}: footer tagline missing")
            if "Proud Partner" not in foot:
                fails.append(f"{name}: footer partner line missing")

            if errors:
                fails.append(f"{name}: console errors {errors[:3]}")

            print(f"  {name:28s} ok")

        # ---- page-specific behaviour ------------------------------------
        page.goto(f"http://127.0.0.1:{PORT}/getting-started.html", wait_until="networkidle")
        page.context.grant_permissions(["clipboard-read", "clipboard-write"])
        for block in ("#delayCli", "#verCli"):
            n = page.eval_on_selector_all(f"{block} .copy-btn", "e => e.length")
            lines = page.eval_on_selector_all(f"{block} .line", "e => e.length")
            if n == 0 or n != lines:
                fails.append(f"copy buttons: {block} {n} buttons / {lines} lines")
        first = page.locator("#delayCli .copy-btn").first
        expected = first.get_attribute("data-copy")
        first.click()
        page.wait_for_timeout(250)
        got = page.evaluate("navigator.clipboard.readText()")
        if got != expected:
            fails.append(f"copy: clipboard {got!r} != {expected!r}")
        if first.text_content().strip() != "Copied":
            fails.append(f"copy: button label {first.text_content()!r}")

        # tab switch must re-render lines that are still wired
        page.click('#verTabs .tab-btn:nth-child(4)')
        page.wait_for_timeout(100)
        page.locator("#verCli .copy-btn").first.click()
        page.wait_for_timeout(250)
        if not page.evaluate("navigator.clipboard.readText()").startswith("region put"):
            fails.append("copy: re-rendered block not wired")

        page.goto(f"http://127.0.0.1:{PORT}/index.html", wait_until="networkidle")
        cards = page.eval_on_selector_all(
            "#partners .partner-card h3", "els => els.map(e => e.textContent)")
        # Four meshes, then the two ham clubs that joined the section in
        # Rev 2.5. Order is the DOM order, so this also pins the clubs
        # below the meshes rather than mixed in among them.
        if cards != ["Upper Cumberland Mesh", "NashMesh", "NC Mesh", "Mountain Mesh",
                     "Tri-States Amateur Radio Club",
                     "Greater Collegedale Adventist Radio Club"]:
            fails.append(f"partners: {cards}")
        if page.eval_on_selector(".partner-umbrella h3", "e => e.textContent") != "TennMesh":
            fails.append("partners: TennMesh not the umbrella")
        # a missing logo file must drop the <img>, never leave a broken icon,
        # and never duplicate the name that the heading already carries
        state = page.evaluate('''() => {
            const out = [];
            document.querySelectorAll('#partners .partner-card, '
                                    + '#partners .partner-umbrella').forEach(w => {
                const img = w.querySelector('img.partner-logo');
                out.push([w.querySelector('h3').textContent,
                          img ? (img.naturalWidth > 0 ? 'logo' : 'BROKEN') : 'none']);
            });
            return out;
        }''')
        for who, st in state:
            if st == 'BROKEN':
                fails.append(f"partners: {who} shows a broken image")
        if page.eval_on_selector_all('.partner-name-fallback', 'e => e.length'):
            fails.append("partners: text fallback duplicates a heading")
        print("  partner logos:", {w: s for w, s in state})

        page.goto(f"http://127.0.0.1:{PORT}/setup-information.html", wait_until="networkidle")
        order = page.eval_on_selector_all("main section, body > section", "els => els.map(e => e.id)")
        if order[-1] != "more-coming-soon":
            fails.append(f"setup: section order {order}")
        # the accordions still open. The Regions group now ships collapsed, so
        # the child toggle is not reachable until the parent is opened -- which
        # is the real journey a reader takes.
        page.click("#regionsGroupToggle")
        page.wait_for_timeout(150)
        page.click("#regionsToggle")
        page.wait_for_timeout(120)
        if page.eval_on_selector("#regionsContent", "e => e.hidden"):
            fails.append("setup: Regions Explained did not expand")

        # Announcements: the archive is a <details>, not the wireToggle()
        # pattern, so it needs its own check. It must ship closed, must open on
        # a click, and past events must stay out of the pinned area at the top.
        page.goto(f"http://127.0.0.1:{PORT}/announcements.html",
                  wait_until="networkidle")
        pins = page.eval_on_selector_all(
            ".meet .meet-pin", "els => els.map(e => e.textContent.trim())")
        if "Next meetings" not in pins or "Last meeting" not in pins:
            fails.append(f"announcements: meeting cards missing from {pins}")
        elif pins.index("Next meetings") > pins.index("Last meeting"):
            fails.append(f"announcements: meeting cards out of order {pins}")
        if "Past event" in pins[:pins.index("Last meeting")]:
            fails.append(f"announcements: archived card above the meetings {pins}")
        if page.eval_on_selector("details.arch", "e => e.open"):
            fails.append("announcements: archive does not ship collapsed")
        if page.locator(".hamfest-banner").is_visible():
            fails.append("announcements: archived content visible while collapsed")
        page.click("details.arch summary")
        page.wait_for_timeout(200)
        if not page.eval_on_selector("details.arch", "e => e.open"):
            fails.append("announcements: archive did not expand")
        if not page.locator(".arch-body .meet.past").count():
            fails.append("announcements: archive expanded but empty")
        print("  archived events       ",
              page.eval_on_selector(".arch-sub", "e => e.textContent"))

        page.goto(f"http://127.0.0.1:{PORT}/about.html", wait_until="networkidle")
        txt = page.eval_on_selector("main", "e => e.textContent")
        for phrase in ("mesh group for Chattanooga", "Contact us",
                       "dumb answers for the dumb questions"):
            if phrase not in txt:
                fails.append(f"about: missing {phrase!r}")

        # ---- mobile pass -------------------------------------------------
        page.set_viewport_size({"width": 390, "height": 844})
        for name in PAGES:
            page.goto(f"http://127.0.0.1:{PORT}/{name}", wait_until="networkidle")
            over = page.evaluate(
                "document.documentElement.scrollWidth - document.documentElement.clientWidth")
            if over > 1:
                fails.append(f"{name} @390px: horizontal overflow {over}px")
        print("  mobile 390px               ok")

        # --- touch: the dropdowns, on a real touch context -------------------
        # A resized desktop viewport is not a touch device: it still has hover
        # and a mouse pointer, so it never exercised the tap path. Both mobile
        # dropdown bugs lived here and every desktop check passed throughout.
        touch = browser.new_context(
            viewport={"width": 390, "height": 844},
            has_touch=True, is_mobile=True,
            user_agent=("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                        "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"))
        tp = touch.new_page()
        for btn, menu, dest in (("#hwBtn", "#hwMenu", "hardware.html"),
                                ("#vidBtn", "#vidMenu", "videos-welcome.html")):
            tp.goto(f"http://127.0.0.1:{PORT}/index.html", wait_until="networkidle")
            tp.wait_for_timeout(300)
            tp.eval_on_selector(btn, "e => e.scrollIntoView({block:'center',inline:'center'})")
            tp.wait_for_timeout(200)
            tp.tap(btn)
            tp.wait_for_timeout(350)

            if tp.eval_on_selector(menu, "e => e.hidden"):
                fails.append(f"touch: {btn} first tap did not open {menu}")
            if not tp.url.endswith("index.html"):
                fails.append(f"touch: {btn} first tap navigated away")
            # Masking the bar used to clip the fixed panel to nothing, so an
            # open menu could still be invisible. Measure it.
            vis = tp.eval_on_selector(menu, """e => {
                const r = e.getBoundingClientRect(), s = getComputedStyle(e);
                return r.height > 50 && r.width > 50
                    && s.visibility !== 'hidden' && s.opacity !== '0';}""")
            if not vis:
                fails.append(f"touch: {menu} opened but is not visible")

            tp.tap(btn)
            tp.wait_for_timeout(500)
            if not tp.url.endswith(dest):
                fails.append(f"touch: {btn} second tap did not navigate to {dest}")
        touch.close()
        print("  touch dropdowns            ok")

        # --- video thumbnails auto-derive from the id ------------------------
        # The sandbox cannot reach i.ytimg.com, and yt.js removes an <img> that
        # fails both sizes, so stub the host to test the mechanism rather than
        # the network. maxresdefault 404s for plenty of real videos; the
        # fallback to hqdefault is the part worth pinning.
        PNG = bytes.fromhex(
            "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
            "0000000a49444154789c6360000002000100ffff03000006000557bfabd4000000"
            "0049454e44ae426082")
        shot = browser.new_context(viewport={"width": 1280, "height": 900})
        asked = []

        def _thumb(route):
            url = route.request.url
            asked.append(url)
            if "maxresdefault" in url:
                route.fulfill(status=404)
            else:
                route.fulfill(status=200, content_type="image/png", body=PNG)

        shot.route("**://i.ytimg.com/**", _thumb)
        shot.route("**://*.youtube*/**", lambda r: r.abort())
        sp = shot.new_page()
        for name in ("videos-meetings.html", "announcements.html"):
            asked.clear()
            sp.goto(f"http://127.0.0.1:{PORT}/{name}", wait_until="networkidle")
            for n in range(sp.locator("[data-yt]").count()):
                sp.locator("[data-yt]").nth(n).scroll_into_view_if_needed()
                sp.wait_for_timeout(250)
            sp.wait_for_timeout(700)
            ids = sp.eval_on_selector_all(
                "[data-yt]", "els => els.map(e => e.getAttribute('data-yt'))")
            srcs = sp.eval_on_selector_all(
                "[data-yt] img", "els => els.map(e => e.getAttribute('src'))")
            if len(srcs) != len(ids):
                fails.append(f"{name}: {len(ids)} videos but {len(srcs)} thumbnails")
            for vid in ids:
                if not any(vid in s for s in srcs):
                    fails.append(f"{name}: no thumbnail derived for {vid}")
            if ids and not any("maxresdefault" in u for u in asked):
                fails.append(f"{name}: never tried maxresdefault")
            if ids and not any("hqdefault" in u for u in asked):
                fails.append(f"{name}: did not fall back to hqdefault")
            # the facade must stay a usable link with scripting off
            tags = sp.eval_on_selector_all(
                "[data-yt]", "els => els.map(e => e.tagName + ':' + !!e.getAttribute('href'))")
            for t in tags:
                if t != "A:true":   # JS serializes the boolean lowercase
                    fails.append(f"{name}: facade is {t}, want a link with href")
        shot.close()
        print("  video thumbnails           ok")

        # --- every player box is 16:9 ----------------------------------------
        # A max-height once overrode aspect-ratio and flattened the archived
        # stream to ~3:1: the thumbnail showed a cropped slice and the 16:9
        # player pillarboxed inside it. Both the facade and the iframe that
        # replaces it have to keep the video's shape.
        for name in ("announcements.html", "videos-meetings.html",
                     "videos-welcome.html"):
            page.goto(f"http://127.0.0.1:{PORT}/{name}", wait_until="networkidle")
            page.wait_for_timeout(250)
            boxes = page.evaluate("""() =>
                [...document.querySelectorAll('.vid-frame, .live-frame')]
                  .map(e => { const r = e.getBoundingClientRect();
                              return [Math.round(r.width), Math.round(r.height)]; })
                  .filter(b => b[0] > 0 && b[1] > 0)""")
            for w, hh in boxes:
                ratio = w / hh
                if abs(ratio - 16 / 9) > 0.05:
                    fails.append(f"{name}: player box {w}x{hh} is "
                                 f"{ratio:.2f}:1, not 16:9")
        print("  player boxes 16:9          ok")

        browser.close()

    if fails:
        print("\nFAILURES")
        for f in fails:
            print("  -", f)
        return 1
    print("\nbrowser checks passed")
    return 0


sys.exit(main())
