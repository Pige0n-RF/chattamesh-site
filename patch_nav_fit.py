#!/usr/bin/env python3
"""Fit all nine nav tabs on the bar instead of scrolling them out of sight.

The bar was capped by the site's 1080px `.wrap`, so the tabs had 831px and
needed 929 -- the tail (Videos, Discord) scrolled off with no visible
affordance, so it read as cut off rather than scrollable.

Anchors are matched by brace-balancing rather than literal text: the generated
pages carry the same CSS on one line where the hand-edited ones span several,
and a literal anchor silently matched nothing on six of the nine pages.

Writes happen only after every page has been transformed, so a failure part way
through cannot leave half the site patched.
"""
import os

PUB = "public"
ALL = ["index.html", "announcements.html", "getting-started.html",
       "hardware.html", "setup-information.html", "videos-welcome.html",
       "videos-information.html", "videos-meetings.html", "about.html"]


def block(src, opener, start=0):
    """Span of a CSS rule or at-rule, matched by balancing braces."""
    i = src.find(opener, start)
    if i < 0:
        return None
    j = src.index("{", i)
    depth = 0
    for k in range(j, len(src)):
        if src[k] == "{":
            depth += 1
        elif src[k] == "}":
            depth -= 1
            if depth == 0:
                return i, k + 1
    return None


def find_rule(src, selector, must_contain):
    """First block for `selector` whose body contains `must_contain`.

    The same rule is written three different ways across the nine pages -- on
    one line, across several, and with differing leading whitespace -- so match
    the selector and confirm the body rather than anchoring on literal text.
    """
    at = 0
    while True:
        b = block(src, selector, at)
        if not b:
            return None
        if must_contain in src[b[0]:b[1]]:
            return b
        at = b[1]


NAV_WRAP = """nav .wrap{
    display:flex; align-items:center; justify-content:space-between;
    gap:18px; height:60px; max-width:1280px;
  }"""

NAV_TABS = """.nav-tabs{
    display:flex; align-items:center; gap:0; height:100%;
    overflow-x:auto; scrollbar-width:none; -ms-overflow-style:none;
    /* Fades the right edge only once the bar has actually overflowed, so an
       overflowing bar looks scrollable instead of chopped. */
    -webkit-mask-image:linear-gradient(to right, #000 calc(100% - 26px), transparent 100%);
    mask-image:linear-gradient(to right, #000 calc(100% - 26px), transparent 100%);
  }
  .nav-tabs:not(.is-scrollable){-webkit-mask-image:none; mask-image:none;}"""

MEDIA = """/* Step down before falling back to the scroller. The wordmark goes
     first -- the mark still identifies the site without it. */
  @media (max-width:1180px){
    .brand .brand-wordmark{display:none;}
  }
  @media (max-width:1000px){
    nav .wrap{padding:0 18px; gap:12px;}
    .nav-tabs a, .nav-drop-btn{padding:0 8px; font-size:0.82rem;}
    .nav-tabs a{gap:5px;}
  }
  @media (max-width:880px){
    nav .wrap{padding:0 16px; gap:10px;}
    .nav-tabs a, .nav-drop-btn{padding:0 9px; font-size:0.8rem;}
  }"""

SCRIPT = """
<script>
// Flag the tab bar scrollable only when it actually overflows, so the fade on
// the right edge shows up when there is somewhere to scroll and not before.
(function(){
  var tabs = document.querySelector('.nav-tabs');
  if (!tabs) return;
  function sync(){
    tabs.classList.toggle('is-scrollable', tabs.scrollWidth - tabs.clientWidth > 2);
  }
  sync();
  window.addEventListener('resize', sync);
  window.addEventListener('load', sync);
})();
</script>
"""

staged = {}
for name in ALL:
    s = open(os.path.join(PUB, name), encoding="utf-8").read()
    if "is-scrollable" in s:
        print(f"  {name:28s} already applied, skipped")
        continue

    b = find_rule(s, "nav .wrap{", "height:60px")
    assert b, f"{name}: nav .wrap"
    s = s[:b[0]] + NAV_WRAP + s[b[1]:]

    b = find_rule(s, ".nav-tabs{", "overflow-x:auto")
    assert b, f"{name}: .nav-tabs"
    s = s[:b[0]] + NAV_TABS + s[b[1]:]

    n = s.count("padding:0 13px")
    assert n == 2, f"{name}: expected 2 tab-padding rules, found {n}"
    s = s.replace("padding:0 13px", "padding:0 10px")

    # Remove every existing 880px nav media block, then add the new ladder once.
    removed = 0
    while True:
        b = block(s, "@media (max-width:880px)")
        if not b:
            break
        chunk = s[b[0]:b[1]]
        if "nav" not in chunk and "brand" not in chunk:
            break
        s = s[:b[0]].rstrip(" ") + s[b[1]:].lstrip("\n")
        removed += 1
    assert removed >= 1, f"{name}: no 880px nav media block found"

    # NAV_TABS has already replaced the original rule, so anchor on the line
    # it ends with rather than the text that is no longer there.
    tail = ".nav-tabs:not(.is-scrollable){-webkit-mask-image:none; mask-image:none;}"
    assert s.count(tail) == 1, f"{name}: reinsertion point"
    at = s.index(tail) + len(tail)
    s = s[:at] + "\n  " + MEDIA + s[at:]

    assert s.count("</body>") == 1, f"{name}: body close"
    s = s.replace("</body>", SCRIPT + "</body>")
    staged[name] = s

for name, s in staged.items():
    open(os.path.join(PUB, name), "w", encoding="utf-8").write(s)
    print(f"  {name:28s} {len(s):,} bytes")
print(f"\nnav: {len(staged)} page(s) updated")
