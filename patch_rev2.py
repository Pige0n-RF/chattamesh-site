#!/usr/bin/env python3
"""ChattaMe.sh REV2 -- Videos tab, YouTube links, UHF/VHF/HF nav entry.

Idempotent by assertion: every edit asserts its anchor occurs exactly once, so
a second run fails loudly rather than duplicating markup.
"""
import os
import re

PUB = "public"
ALL = ["index.html", "getting-started.html", "hardware.html",
       "setup-information.html", "about.html"]

YT_URL = "https://www.youtube.com/@ChattanoogaMesh"

# The YouTube mark with the plate on currentColor and the triangle left white,
# so the "red play button" reads as ChattaMesh purple wherever it is placed.
YT_GLYPH = (
    '<svg viewBox="0 0 24 24" aria-hidden="true">'
    '<path fill="currentColor" d="M23.5 6.2a3 3 0 0 0-2.12-2.12C19.5 3.5 12 3.5 12 '
    '3.5s-7.5 0-9.38.58A3 3 0 0 0 .5 6.2 31.3 31.3 0 0 0 0 12a31.3 31.3 0 0 0 .5 '
    '5.8 3 3 0 0 0 2.12 2.12C4.5 20.5 12 20.5 12 20.5s7.5 0 9.38-.58A3 3 0 0 0 '
    '23.5 17.8 31.3 31.3 0 0 0 24 12a31.3 31.3 0 0 0-.5-5.8Z"/>'
    '<path fill="#fff" d="M9.55 15.57 15.82 12 9.55 8.43Z"/></svg>')


def read(p):
    return open(os.path.join(PUB, p), encoding="utf-8").read()


def write(p, s):
    open(os.path.join(PUB, p), "w", encoding="utf-8").write(s)


# ============================ 1. Videos tab =================================
# Sits left of About and carries the YouTube mark. External, like Live Maps and
# Discord, so it gets the same target/rel treatment.

TAB_CSS_ANCHOR = "  .nav-tabs a.tab-discord{color:#8b95f7;}\n"
TAB_CSS = """  .nav-tabs a.tab-videos{color:var(--signal);}
  .nav-tabs a.tab-videos:hover{color:var(--text); border-bottom-color:var(--signal);}
"""

VIDEOS_TAB = (f'      <a href="{YT_URL}" target="_blank" rel="noopener" '
              f'class="tab-videos">\n        {YT_GLYPH}\n        Videos\n      </a>\n')

ABOUT_TAB_RE = re.compile(r'([ \t]*<a href="about\.html"[^>]*>About</a>\n)')

for name in ALL:
    src = read(name)
    assert src.count(TAB_CSS_ANCHOR) == 1, f"{name}: discord tab css"
    assert "tab-videos" not in src, f"{name}: Videos tab already present"
    src = src.replace(TAB_CSS_ANCHOR, TAB_CSS + TAB_CSS_ANCHOR)

    m = ABOUT_TAB_RE.search(src)
    assert m, f"{name}: About tab anchor"
    src = src[:m.start(1)] + VIDEOS_TAB + src[m.start(1):]
    write(name, src)
print("nav: Videos tab added left of About on all five pages")


# ==================== 2. UHF/VHF/HF in the Hardware menu ====================
MENU_OLD = '          <a role="menuitem" href="hardware.html#diy">DIY</a>\n'
MENU_NEW = (MENU_OLD +
            '          <a role="menuitem" href="hardware.html#uhf-vhf-hf">UHF / VHF / HF</a>\n')

for name in ALL:
    src = read(name)
    assert src.count(MENU_OLD) == 1, f"{name}: DIY menu item"
    write(name, src.replace(MENU_OLD, MENU_NEW))
print("nav: UHF / VHF / HF added to the Hardware menu")


# ======================= 3. YouTube link on About ===========================
about = read("about.html")

CSS_ANCHOR = "  .btn-discord:hover{background:#6c75f5; text-decoration:none;}\n"
YT_CSS = """  /* YouTube plate on the brand purple rather than YouTube red, matching the
     Videos tab; the triangle stays white so the mark still reads as YouTube. */
  .btn-youtube{background:var(--signal); color:#fff;}
  .btn-youtube:hover{background:#8385ee; color:#fff; text-decoration:none;}
  .btn-youtube svg{width:20px; height:20px; flex:none;}
  .btn svg{flex:none;}
"""
assert about.count(CSS_ANCHOR) == 1, "about: btn-discord css"
about = about.replace(CSS_ANCHOR, CSS_ANCHOR + YT_CSS)

CTA_ANCHOR = '          <a class="btn btn-ghost" href="getting-started.html">Get a node on the mesh</a>'
YT_BTN = (f'          <a class="btn btn-youtube" href="{YT_URL}" target="_blank" '
          f'rel="noopener">{YT_GLYPH} Watch on YouTube</a>\n')
assert about.count(CTA_ANCHOR) == 1, "about: contact CTA row"
about = about.replace(CTA_ANCHOR, YT_BTN + CTA_ANCHOR)

# And a sentence, so the channel is mentioned in the prose and not only as a chip.
PROSE_OLD = ("<p>Never be afraid to ask questions. We have dumb answers for the "
             "dumb questions.</p>")
PROSE_NEW = (PROSE_OLD + '\n\n      <p>We also put build walkthroughs and mesh '
             f'footage on <a href="{YT_URL}" target="_blank" rel="noopener">our '
             'YouTube channel</a>.</p>')
assert about.count(PROSE_OLD) == 1, "about: prose anchor"
about = about.replace(PROSE_OLD, PROSE_NEW)

write("about.html", about)
print("about: YouTube button and prose link added")
