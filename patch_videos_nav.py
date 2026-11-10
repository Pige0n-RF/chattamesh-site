#!/usr/bin/env python3
"""Videos becomes a dropdown, and the nav script learns to handle more than one.

The dropdown logic was written against a single menu (`querySelector('.nav-drop')`,
ids baked in). A second menu needs it to wire every `.nav-drop` independently,
each finding its own trigger and panel, with its own hide timer.

Idempotent by assertion.
"""
import os
import re

PUB = "public"
ALL = ["index.html", "getting-started.html", "hardware.html",
       "setup-information.html", "about.html"]

YT_URL = "https://www.youtube.com/@ChattanoogaMesh"

CARET = ('<svg class="caret" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
         'stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" '
         'aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>')


def read(p):
    return open(os.path.join(PUB, p), encoding="utf-8").read()


def write(p, s):
    open(os.path.join(PUB, p), "w", encoding="utf-8").write(s)


# ------------------------------- 1. Videos tab -> dropdown ------------------
VIDEOS_RE = re.compile(
    r'([ \t]*)<a href="' + re.escape(YT_URL) + r'"[^>]*class="tab-videos">\n'
    r'(\s*<svg .*?</svg>)\n\s*Videos\n\s*</a>\n', re.S)

for name in ALL:
    src = read(name)
    m = VIDEOS_RE.search(src)
    assert m, f"{name}: Videos tab not found"
    ind, glyph = m.group(1), m.group(2).strip()

    block = (
        f'{ind}<div class="nav-drop">\n'
        f'{ind}  <a href="videos-welcome.html" class="nav-drop-btn tab-videos" id="vidBtn"\n'
        f'{ind}     aria-expanded="false" aria-haspopup="true" aria-controls="vidMenu">'
        f'{glyph} Videos {CARET}</a>\n'
        f'{ind}  <div class="nav-drop-menu" id="vidMenu" role="menu" hidden>\n'
        f'{ind}    <a role="menuitem" href="{YT_URL}" target="_blank" rel="noopener">YouTube</a>\n'
        f'{ind}    <a role="menuitem" href="videos-welcome.html">Welcome</a>\n'
        f'{ind}    <a role="menuitem" href="videos-information.html">Information</a>\n'
        f'{ind}    <a role="menuitem" href="videos-meetings.html">Meetings</a>\n'
        f'{ind}  </div>\n'
        f'{ind}</div>\n')
    write(name, src[:m.start()] + block + src[m.end():])
print("nav: Videos is now a dropdown")


# --------------------- 2. generalise the dropdown script --------------------
OLD_JS_RE = re.compile(r'\n<script>\n// Nav dropdown\..*?\n\}\)\(\);\n</script>\n', re.S)

NEW_JS = """
<script>
// Nav dropdowns. Each trigger is a real link, so the menu opens on hover (and
// on keyboard focus) rather than on click -- clicking navigates. Menus are
// fixed-positioned because .nav-tabs is a horizontal scroller and would clip an
// absolutely positioned child.
//
// Every .nav-drop is wired independently with its own timer and state, so a
// second menu cannot borrow the first one's.
(function(){
  var drops = [];

  document.querySelectorAll('.nav-drop').forEach(function(wrap){
    var btn  = wrap.querySelector('.nav-drop-btn');
    var menu = wrap.querySelector('.nav-drop-menu');
    if (!btn || !menu) return;

    var d = {wrap: wrap, btn: btn, menu: menu, timer: null, dismissed: false};

    d.place = function(){
      var r = btn.getBoundingClientRect();
      menu.style.top = (r.bottom + 4) + 'px';
      var w = menu.offsetWidth || 186;
      menu.style.left = Math.max(8, Math.min(r.left, window.innerWidth - w - 8)) + 'px';
    };
    d.open = function(){
      // Only one menu at a time, or hovering across the bar stacks them.
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

    wrap.addEventListener('mouseenter', d.open);
    wrap.addEventListener('mouseleave', d.closeSoon);
    menu.addEventListener('mouseenter', function(){ clearTimeout(d.timer); });
    menu.addEventListener('mouseleave', d.closeSoon);

    // Escape closes then focuses the trigger -- without this guard that focus
    // fires the handler below and reopens the menu.
    btn.addEventListener('focus', function(){ if (!d.dismissed) d.open(); });
    btn.addEventListener('blur', function(){ d.dismissed = false; });
    wrap.addEventListener('focusout', function(e){
      if (!wrap.contains(e.relatedTarget)) d.close();
    });

    // Touch has no hover: first tap opens the menu, second follows the link.
    btn.addEventListener('click', function(e){
      if (window.matchMedia('(hover: none)').matches && menu.hidden){
        e.preventDefault();
        d.open();
      }
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

for name in ALL:
    src = read(name)
    m = OLD_JS_RE.search(src)
    assert m, f"{name}: dropdown script not found"
    write(name, src[:m.start()] + NEW_JS + src[m.end():])
print("nav: dropdown script now wires every .nav-drop independently")
