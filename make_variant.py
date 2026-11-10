#!/usr/bin/env python3
"""Build the "Discord coming soon" variant of the site.

Derives from ./public rather than being a hand-maintained fork, so the two
versions can't drift: rerun this after any change to the main site.

    python3 make_variant.py            # -> ./public-soon

Only ChattaMesh's own invite is removed. The partner meshes' Discord links
(TennMesh, NashMesh, NC Mesh, Mountain Mesh) are theirs and stay live.
"""
import os
import re
import shutil
import sys

SRC = "public"
DST = sys.argv[1] if len(sys.argv) > 1 else "public-soon"
INVITE = "https://discord.gg/XF354A3e9m"

PAGES = ["index.html", "announcements.html", "getting-started.html",
         "hardware.html", "setup-information.html", "videos-welcome.html",
         "videos-information.html", "videos-meetings.html", "funding.html", "about.html"]

DISCORD_GLYPH = (
    '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">'
    '<path d="M20.317 4.37a19.79 19.79 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c'
    '-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617'
    '-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032'
    '.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 '
    '5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0'
    '-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128c.126-.094.252'
    '-.192.372-.291a.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 '
    '0 0 1 .078.01c.12.099.246.197.373.291a.077.077 0 0 1-.006.128 12.3 12.3 0 0 1'
    '-1.873.892.076.076 0 0 0-.041.107c.36.698.772 1.363 1.225 1.993a.076.076 0 0 0 '
    '.084.028 19.84 19.84 0 0 0 6.002-3.03.077.077 0 0 0 .032-.055c.5-5.177-.838'
    '-9.673-3.549-13.66a.06.06 0 0 0-.031-.028ZM8.02 15.33c-1.183 0-2.157-1.086-2.157'
    '-2.419 0-1.333.955-2.419 2.157-2.419 1.211 0 2.176 1.096 2.157 2.42 0 1.332-.955 '
    '2.418-2.157 2.418Zm7.975 0c-1.183 0-2.157-1.086-2.157-2.419 0-1.333.955-2.419 '
    '2.157-2.419 1.211 0 2.176 1.096 2.157 2.42 0 1.332-.946 2.418-2.157 2.418Z"/></svg>')

SOON_BLOCK = (f'<span class="discord-soon">{DISCORD_GLYPH}'
              f'<span>Discord Coming Soon</span></span>')

CSS = """
  /* ===== DISCORD COMING SOON ===== */
  /* Not a link and not styled as one -- a dashed, muted panel so nobody taps
     it expecting an invite. Glyph above the label. */
  .discord-soon{
    display:inline-flex; flex-direction:column; align-items:center; gap:9px;
    padding:15px 24px; border:1px dashed var(--line); border-radius:var(--radius);
    background:var(--panel-2); color:var(--muted-2);
    font-family:'Space Grotesk', sans-serif; font-weight:600; font-size:0.9rem;
    text-align:center; line-height:1.2;
  }
  .discord-soon svg{width:26px; height:26px; flex:none; color:var(--signal); opacity:0.72;}

  /* The nav bar is a fixed-height row, so the tab keeps the glyph inline with
     the label rather than stacking. It also has to restate the tab typography
     and the 16px glyph size: those rules are scoped to `.nav-tabs a`, and this
     is deliberately a <span> because it doesn't go anywhere. */
  .nav-tabs .tab-discord.is-soon{
    font-family:'Space Grotesk', sans-serif; font-weight:500; font-size:0.86rem;
    color:var(--muted-2); padding:0 13px; height:100%;
    display:inline-flex; align-items:center; gap:7px;
    white-space:nowrap; cursor:default;
    border-bottom:2px solid transparent;
  }
  .nav-tabs .tab-discord.is-soon svg{width:16px; height:16px; flex:none; opacity:0.75;}
"""


def soon_tag(inner):
    """Nav tab -> a non-interactive span."""
    inner = re.sub(r">\s*Discord\s*<", ">Discord Coming Soon<", ">" + inner + "<")[1:-1]
    return f'<span class="tab-discord is-soon">{inner}</span>'


def build(src_dir, dst_dir):
    # Build into a staging directory and swap it in only once every page has
    # been processed. A previous run asserted partway through and left a tree
    # with some pages converted and some not -- which still looked like a
    # variant, and passed its own gates, because nothing checked the whole tree.
    stage = dst_dir + ".building"
    for d in (stage, stage + ".old"):
        if os.path.exists(d):
            shutil.rmtree(d)
    shutil.copytree(src_dir, stage)
    dst_dir, final_dir = stage, dst_dir

    for name in PAGES:
        p = os.path.join(dst_dir, name)
        s = open(p, encoding="utf-8").read()
        before = s.count(INVITE)

        # 1 -- stylesheet
        assert s.count("</style>") == 1, f"{name}: style close"
        s = s.replace("</style>", CSS + "</style>")

        # 2/3/4 -- every link to the invite, whatever shape it takes.
        # One pass keyed off the tag's attributes rather than three regexes that
        # each assumed href came first: `<a class="dc-inline" href="...">` slipped
        # past all of them and the invite survived into the variant.
        def replace_link(m):
            attrs, inner = m.group(1), m.group(2)
            if "tab-discord" in attrs:
                return soon_tag(inner)
            if "btn-discord" in attrs or "btn-ghost" in attrs:
                return SOON_BLOCK
            return inner.strip() + " (coming soon)"

        s = re.sub(r'<a\b([^>]*href="' + re.escape(INVITE) + r'"[^>]*)>(.*?)</a>',
                   replace_link, s, flags=re.S)

        # 5 -- structured data: no public profile to point at yet
        s = re.sub(r'\n\s*"sameAs": \[\n\s*"' + re.escape(INVITE) + r'"\n\s*\]', "", s)
        s = re.sub(r',(\s*\n\s*)\}', r'\1}', s) if '"sameAs"' not in s else s

        # 6 -- prose that presented Discord as the live contact route
        s = s.replace(
            "Discord is the fastest way to reach us.",
            "Our Discord is opening soon and will be the fastest way to reach us.")
        s = s.replace(
            "please get in touch on Discord.",
            "please watch for the Discord opening soon.")
        s = s.replace(
            "More recommendations and discussion in the ChattaMesh Discord (coming soon).",
            "More recommendations and discussion once the ChattaMesh Discord opens.")

        assert INVITE not in s, f"{name}: invite survived"
        open(p, "w", encoding="utf-8").write(s)
        print(f"  {name:26s} {before} ChattaMesh Discord reference(s) replaced")

    # Whole-tree sweep: no page, including ones not in PAGES, may still carry
    # the invite. This is the check that would have caught the half-built tree.
    stragglers = []
    for root, _, files in os.walk(dst_dir):
        for f in files:
            if not f.endswith((".html", ".xml", ".txt")):
                continue
            fp = os.path.join(root, f)
            if INVITE in open(fp, encoding="utf-8", errors="replace").read():
                stragglers.append(os.path.relpath(fp, dst_dir))
    assert not stragglers, f"invite survived in: {stragglers}"

    # Partner invites are other groups' and must survive.
    idx = open(os.path.join(dst_dir, "index.html"), encoding="utf-8").read()
    partners = re.findall(r"discord\.gg/([A-Za-z0-9]+)", idx)
    print(f"\n  partner Discord links kept: {sorted(set(partners))}")

    # Everything passed -- swap the staged tree in.
    if os.path.exists(final_dir):
        os.rename(final_dir, stage + ".old")
        shutil.rmtree(stage + ".old")
    os.rename(stage, final_dir)


if __name__ == "__main__":
    build(SRC, DST)
    print(f"\nvariant written to {DST}/")
