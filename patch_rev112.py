#!/usr/bin/env python3
"""ChattaMe.sh Rev1.1.2 patch.

Idempotent by assertion: every edit asserts its anchor occurs exactly once, so
a second run fails loudly rather than duplicating markup.
"""
import os
import re

PUB = "public"
ALL = ["index.html", "getting-started.html", "hardware.html",
       "setup-information.html", "about.html"]


def read(p):
    return open(os.path.join(PUB, p), encoding="utf-8").read()


def write(p, s):
    open(os.path.join(PUB, p), "w", encoding="utf-8").write(s)


# ================= 1. Hardware tab: a real link, menu on hover =============
# Was a <button> that only toggled. Now it navigates on click and the menu
# opens on hover, so the sub-sections stay reachable without a click.

OLD_BTN_RE = re.compile(
    r'<button type="button" class="nav-drop-btn( active)?" id="hwBtn"\s*\n'
    r'\s*aria-expanded="false" aria-haspopup="true" aria-controls="hwMenu">\s*\n'
    r'\s*Hardware (<svg class="caret".*?</svg>)\s*\n\s*</button>', re.S)


def link_tab(src):
    m = OLD_BTN_RE.search(src)
    assert m, "Hardware button anchor"
    active = m.group(1) or ""
    caret = m.group(2)
    new = (f'<a href="hardware.html" class="nav-drop-btn{active}" id="hwBtn"\n'
           f'           aria-expanded="false" aria-haspopup="true" '
           f'aria-controls="hwMenu">Hardware {caret}</a>')
    return src[:m.start()] + new + src[m.end():]


OLD_JS_RE = re.compile(r'\n<script>\n// Nav dropdown\..*?\n\}\)\(\);\n</script>\n', re.S)

NEW_JS = """
<script>
// Nav dropdown. The trigger is a real link to hardware.html, so the menu opens
// on hover (and on keyboard focus) rather than on click -- clicking navigates.
// The menu is fixed-positioned because .nav-tabs is a horizontal scroller and
// would clip an absolutely positioned child.
(function(){
  var wrap = document.querySelector('.nav-drop');
  var btn  = document.getElementById('hwBtn');
  var menu = document.getElementById('hwMenu');
  if (!wrap || !btn || !menu) return;

  var hideTimer;

  function place(){
    var r = btn.getBoundingClientRect();
    menu.style.top = (r.bottom + 4) + 'px';
    var w = menu.offsetWidth || 186;
    menu.style.left = Math.max(8, Math.min(r.left, window.innerWidth - w - 8)) + 'px';
  }
  function open(){
    clearTimeout(hideTimer);
    menu.hidden = false;
    btn.setAttribute('aria-expanded', 'true');
    place();
  }
  function close(){
    menu.hidden = true;
    btn.setAttribute('aria-expanded', 'false');
  }
  // Small delay so the diagonal trip from the tab to the menu doesn't drop it.
  function closeSoon(){ hideTimer = setTimeout(close, 180); }

  wrap.addEventListener('mouseenter', open);
  wrap.addEventListener('mouseleave', closeSoon);
  menu.addEventListener('mouseenter', function(){ clearTimeout(hideTimer); });
  menu.addEventListener('mouseleave', closeSoon);

  // Escape closes then focuses the trigger -- without this guard that focus
  // fires the handler below and reopens the menu immediately.
  var dismissed = false;
  btn.addEventListener('focus', function(){ if (!dismissed) open(); });
  btn.addEventListener('blur', function(){ dismissed = false; });
  wrap.addEventListener('focusout', function(e){
    if (!wrap.contains(e.relatedTarget)) close();
  });
  document.addEventListener('keydown', function(e){
    if (e.key === 'Escape' && !menu.hidden){ dismissed = true; close(); btn.focus(); }
  });

  // Touch has no hover: first tap opens the menu, second follows the link.
  btn.addEventListener('click', function(e){
    if (window.matchMedia('(hover: none)').matches && menu.hidden){
      e.preventDefault();
      open();
    }
  });
  document.addEventListener('click', function(e){
    if (!menu.hidden && !wrap.contains(e.target)) close();
  });

  window.addEventListener('resize', function(){ if (!menu.hidden) close(); });
  window.addEventListener('scroll', function(){ if (!menu.hidden) place(); },
                          {passive:true});
  var tabs = document.querySelector('.nav-tabs');
  if (tabs) tabs.addEventListener('scroll', function(){
    if (!menu.hidden) place();
  }, {passive:true});
})();
</script>
"""

DROP_CSS_OLD = """  .nav-drop-btn{
    font-family:'Space Grotesk', sans-serif; font-weight:500; font-size:0.86rem;
    color:var(--muted); padding:0 13px; height:100%;
    display:inline-flex; align-items:center; gap:6px; white-space:nowrap;
    background:none; border:0; border-bottom:2px solid transparent; cursor:pointer;
    transition:color .15s ease, border-color .15s ease;
  }"""
DROP_CSS_NEW = """  .nav-drop-btn{
    font-family:'Space Grotesk', sans-serif; font-weight:500; font-size:0.86rem;
    color:var(--muted); padding:0 13px; height:100%;
    display:inline-flex; align-items:center; gap:6px; white-space:nowrap;
    background:none; border:0; border-bottom:2px solid transparent; cursor:pointer;
    text-decoration:none;
    transition:color .15s ease, border-color .15s ease;
  }
  .nav-drop-btn:hover{text-decoration:none;}"""

for name in ALL:
    src = read(name)
    src = link_tab(src)
    assert DROP_CSS_OLD in src, f"{name}: nav-drop-btn css"
    src = src.replace(DROP_CSS_OLD, DROP_CSS_NEW)
    m = OLD_JS_RE.search(src)
    assert m, f"{name}: dropdown script"
    src = src[:m.start()] + NEW_JS + src[m.end():]
    write(name, src)
print("nav: Hardware tab now links, menu opens on hover")


# ============ 2. Skyline fades out instead of stopping dead ================
SKY_OLD = "  .skyline-frame{position:relative; height:220px; width:100%;}"
SKY_NEW = """  .skyline-frame{
    position:relative; height:220px; width:100%;
    /* the ridge used to stop at a hard horizontal edge; fade it into the page */
    -webkit-mask-image:linear-gradient(to bottom, #000 0%, #000 38%, rgba(0,0,0,0.35) 76%, transparent 100%);
    mask-image:linear-gradient(to bottom, #000 0%, #000 38%, rgba(0,0,0,0.35) 76%, transparent 100%);
  }"""
for name in ["index.html", "getting-started.html"]:
    src = read(name)
    assert src.count(SKY_OLD) == 1, f"{name}: skyline anchor"
    write(name, src.replace(SKY_OLD, SKY_NEW))
print("skyline: hard cutoff replaced with a gradient fade")


# ====== 3. Partner cards squarer so the logos can be bigger ================
src = read("index.html")
PG_OLD = """  .partner-card{display:flex; flex-direction:column; gap:12px;}
  .partner-logo-wrap{height:64px; display:flex; align-items:center;}
  .partner-logo{max-height:60px; max-width:220px; width:auto; display:block;}"""
PG_NEW = """  .partner-card{display:flex; flex-direction:column; gap:14px;}
  /* Taller, more square cards: the logo well roughly doubles, and the wordmarks
     are centred in it rather than left-aligned in a thin strip. */
  .partner-logo-wrap{
    height:120px; display:flex; align-items:center; justify-content:center;
    background:var(--panel-2); border:1px solid var(--line-soft);
    border-radius:var(--radius); padding:16px;
  }
  .partner-logo{max-height:88px; max-width:100%; width:auto; display:block;}
  @media (max-width:720px){ .partner-logo-wrap{height:100px;} }"""
assert src.count(PG_OLD) == 1, "partner grid css"
src = src.replace(PG_OLD, PG_NEW)
write("index.html", src)
print("partners: logo wells enlarged and squared up")


# ============ 4. Footer wording ===========================================
for name in ALL:
    src = read(name)
    old = "<p>Proud Partner <a href=\"https://tennmesh.com\""
    assert src.count(old) == 1, f"{name}: footer partner line"
    write(name, src.replace(old, "<p>Proud Partner of <a href=\"https://tennmesh.com\""))
print("footer: 'Proud Partner of'")
