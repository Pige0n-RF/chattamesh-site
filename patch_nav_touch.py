#!/usr/bin/env python3
"""Fix the nav dropdowns on touch devices. Two separate bugs.

1. A tap fires a synthetic `mouseenter` *before* the `click`. That opened the
   menu, and the click guard -- which only suppressed navigation when the menu
   was still hidden -- then saw an already-open menu and let the link through.
   Tapping "Hardware" went straight to hardware.html and the menu was never
   usable. Hover-open is now limited to a real mouse via `pointerType`.

2. The scroll-fade added in Rev 2.1.1 put `mask-image` on `.nav-tabs`. Masking
   clips the element's whole painted subtree, and the dropdown panel is a
   descendant -- `position:fixed` does not exempt it. Below 900px, where the bar
   overflows and the fade switches on, the menu rendered completely invisible
   even when forced open. The fade moved to an overlay on `nav` that is not an
   ancestor of the menu.

Both only showed on narrow/touch viewports, which is why the desktop gates kept
passing. Writes are staged and happen only once all nine pages transform.
"""
import os

PUB = "public"
ALL = ["index.html", "announcements.html", "getting-started.html",
       "hardware.html", "setup-information.html", "videos-welcome.html",
       "videos-information.html", "videos-meetings.html", "about.html"]


def block(src, opener, start=0):
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
    at = 0
    while True:
        b = block(src, selector, at)
        if not b:
            return None
        if must_contain in src[b[0]:b[1]]:
            return b
        at = b[1]


# ---------------------------------------------------------------------- CSS
# The fade lives on nav, not on .nav-tabs. A mask on .nav-tabs clips every
# descendant it paints, dropdown panels included.
NAV_TABS = """.nav-tabs{
    display:flex; align-items:center; gap:0; height:100%;
    overflow-x:auto; scrollbar-width:none; -ms-overflow-style:none;
  }"""

FADE = """
  /* Scroll affordance. Deliberately an overlay on nav rather than a mask on
     .nav-tabs: a mask clips the whole painted subtree, and the dropdown panels
     are descendants of .nav-tabs, so masking made them invisible on every
     viewport narrow enough to overflow. */
  nav{position:sticky;}
  nav.tabs-overflow::after{
    content:''; position:absolute; top:0; right:0; height:60px; width:30px;
    background:linear-gradient(to right, rgba(31,35,52,0), var(--bg-alt) 85%);
    pointer-events:none; z-index:1;
  }"""

# ---------------------------------------------------------------------- JS
NEW_JS = """
<script>
// Nav dropdowns. Each trigger is a real link, so on a mouse the menu opens on
// hover and clicking navigates. Menus are fixed-positioned because .nav-tabs is
// a horizontal scroller and would otherwise clip them.
//
// Touch needs care: a tap fires a synthetic mouseenter before the click, so
// hovering-to-open would open the menu and the click would then find it open
// and follow the link. Pointer events carry pointerType, so hover-open is
// limited to a real mouse and taps get an explicit first-tap-opens rule.
(function(){
  var drops = [];
  function isMouse(e){ return e.pointerType === 'mouse'; }

  document.querySelectorAll('.nav-drop').forEach(function(wrap){
    var btn  = wrap.querySelector('.nav-drop-btn');
    var menu = wrap.querySelector('.nav-drop-menu');
    if (!btn || !menu) return;

    var d = {wrap:wrap, btn:btn, menu:menu, timer:null,
             dismissed:false, touch:false, viaPointer:false};

    d.place = function(){
      var r = btn.getBoundingClientRect();
      menu.style.top = (r.bottom + 4) + 'px';
      var w = menu.offsetWidth || 186;
      menu.style.left = Math.max(8, Math.min(r.left, window.innerWidth - w - 8)) + 'px';
    };
    d.open = function(){
      drops.forEach(function(o){ if (o !== d) o.close(); });
      clearTimeout(d.timer);
      menu.hidden = false;
      btn.setAttribute('aria-expanded', 'true');
      d.place();
    };
    d.close = function(){
      menu.hidden = true;
      btn.setAttribute('aria-expanded', 'false');
    };
    // Small delay so the diagonal trip from the tab to the menu doesn't drop it.
    d.closeSoon = function(){ d.timer = setTimeout(d.close, 180); };

    wrap.addEventListener('pointerenter', function(e){ if (isMouse(e)) d.open(); });
    wrap.addEventListener('pointerleave', function(e){ if (isMouse(e)) d.closeSoon(); });
    menu.addEventListener('pointerenter', function(e){ if (isMouse(e)) clearTimeout(d.timer); });
    menu.addEventListener('pointerleave', function(e){ if (isMouse(e)) d.closeSoon(); });

    btn.addEventListener('pointerdown', function(e){
      d.touch = !isMouse(e);
      d.viaPointer = true;
    });
    // Keyboard focus opens; pointer focus does not, or a tap would open here
    // and then navigate on the click that follows.
    btn.addEventListener('focus', function(){
      if (!d.dismissed && !d.viaPointer) d.open();
    });
    btn.addEventListener('blur', function(){ d.dismissed = false; d.viaPointer = false; });
    wrap.addEventListener('focusout', function(e){
      if (!wrap.contains(e.relatedTarget)) d.close();
    });

    // Touch: first tap opens, second follows the link.
    btn.addEventListener('click', function(e){
      if (d.touch && menu.hidden){ e.preventDefault(); d.open(); }
      d.viaPointer = false;
    });

    drops.push(d);
  });

  if (!drops.length) return;
  function each(fn){ drops.forEach(fn); }

  document.addEventListener('keydown', function(e){
    if (e.key !== 'Escape') return;
    each(function(d){
      if (!d.menu.hidden){ d.dismissed = true; d.close(); d.btn.focus(); }
    });
  });
  document.addEventListener('click', function(e){
    each(function(d){ if (!d.menu.hidden && !d.wrap.contains(e.target)) d.close(); });
  });
  window.addEventListener('resize', function(){
    each(function(d){ if (!d.menu.hidden) d.close(); });
  });
  window.addEventListener('scroll', function(){
    each(function(d){ if (!d.menu.hidden) d.place(); });
  }, {passive:true});
  var tabs = document.querySelector('.nav-tabs');
  if (tabs) tabs.addEventListener('scroll', function(){
    each(function(d){ if (!d.menu.hidden) d.place(); });
  }, {passive:true});
})();
</script>
"""

FADE_JS = """
<script>
// Flag the bar overflowing so the fade on nav's right edge only shows when
// there is somewhere to scroll. The class goes on nav, not .nav-tabs -- see
// the note by the CSS.
(function(){
  var tabs = document.querySelector('.nav-tabs');
  var nav = tabs && tabs.closest('nav');
  if (!nav) return;
  function sync(){
    nav.classList.toggle('tabs-overflow', tabs.scrollWidth - tabs.clientWidth > 2);
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
    assert "tabs-overflow" not in s, f"{name}: already applied"

    # 1 -- drop the mask, add the overlay fade
    b = find_rule(s, ".nav-tabs{", "overflow-x:auto")
    assert b, f"{name}: .nav-tabs rule"
    s = s[:b[0]] + NAV_TABS + FADE + s[b[1]:]

    old_not = ".nav-tabs:not(.is-scrollable){-webkit-mask-image:none; mask-image:none;}"
    assert s.count(old_not) == 1, f"{name}: is-scrollable reset rule"
    s = s.replace(old_not + "\n  ", "").replace(old_not, "")

    # 2 -- replace both scripts
    i = s.index("\n<script>\n// Nav dropdowns.")
    j = s.index("</script>\n", i) + len("</script>\n")
    s = s[:i] + NEW_JS + s[j:]

    # index.html says "Mark", the other eight say "Flag" -- a leftover from the
    # two-stage patch that produced them. Accept either.
    i = -1
    for probe in ("\n<script>\n// Flag the tab bar scrollable",
                  "\n<script>\n// Mark the tab bar scrollable"):
        i = s.find(probe)
        if i >= 0:
            break
    assert i >= 0, f"{name}: fade script"
    j = s.index("</script>\n", i) + len("</script>\n")
    s = s[:i] + FADE_JS + s[j:]

    assert "is-scrollable" not in s, f"{name}: stale is-scrollable left behind"
    # Scoped to the nav rule: .skyline-frame has its own legitimate mask.
    nb = find_rule(s, ".nav-tabs{", "overflow-x:auto")
    assert nb and "mask-image" not in s[nb[0]:nb[1]], f"{name}: mask still on .nav-tabs"
    staged[name] = s

for name, s in staged.items():
    open(os.path.join(PUB, name), "w", encoding="utf-8").write(s)
    print(f"  {name:28s} {len(s):,} bytes")
print(f"\nnav: touch handling and scroll fade fixed on {len(staged)} pages")
