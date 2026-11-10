#!/usr/bin/env python3
"""ChattaMe.sh v1.3 -- Hardware tab, nav dropdown, TennMesh copy fix.

Run from the repo root. Idempotent: every insertion is guarded by an assert on
the anchor's occurrence count, so a second run fails loudly rather than
duplicating markup.
"""
import os
import re

PUB = "public"
PAGES = ["index.html", "getting-started.html", "setup-information.html",
         "about.html"]


def read(p):
    return open(os.path.join(PUB, p), encoding="utf-8").read()


def write(p, s):
    open(os.path.join(PUB, p), "w", encoding="utf-8").write(s)


# ------------------------------------------------------- 1. TennMesh copy

OLD_TENN = ("Greater Tennessee Mesh &mdash; the parent mesh every group below "
            "falls under.")
NEW_TENN = ("Greater Tennessee Mesh &mdash; the parent mesh every group, in "
            "Tennessee, below falls under.")

s = read("index.html")
assert s.count(OLD_TENN) == 1, "TennMesh partner copy anchor"
write("index.html", s.replace(OLD_TENN, NEW_TENN))
print("index.html: TennMesh partner copy updated")


# ------------------------------------------------- 2. nav dropdown (CSS + markup)

# The menu is position:fixed and placed from the trigger's bounding box at open
# time. .nav-tabs is an overflow-x:auto scroller, so an absolutely positioned
# child would be clipped by it -- fixed sidesteps that entirely, and the nav is
# sticky so it stays put while the menu is open.
DROP_CSS = """
  /* nav dropdown */
  .nav-drop{position:relative; height:100%; display:inline-flex; align-items:center;}
  .nav-drop-btn{
    font-family:'Space Grotesk', sans-serif; font-weight:500; font-size:0.86rem;
    color:var(--muted); padding:0 13px; height:100%;
    display:inline-flex; align-items:center; gap:6px; white-space:nowrap;
    background:none; border:0; border-bottom:2px solid transparent; cursor:pointer;
    transition:color .15s ease, border-color .15s ease;
  }
  .nav-drop-btn:hover{color:var(--text); border-bottom-color:var(--line);}
  .nav-drop-btn.active{color:var(--signal); border-bottom-color:var(--signal);}
  .nav-drop-btn .caret{width:11px; height:11px; flex:none; transition:transform .18s ease;}
  .nav-drop-btn[aria-expanded="true"]{color:var(--text);}
  .nav-drop-btn[aria-expanded="true"] .caret{transform:rotate(180deg);}
  .nav-drop-menu{
    position:fixed; z-index:60; min-width:186px; padding:6px;
    background:var(--panel); border:1px solid var(--line); border-radius:var(--radius);
    box-shadow:0 12px 32px rgba(0,0,0,0.45);
    display:flex; flex-direction:column; gap:2px;
  }
  .nav-drop-menu[hidden]{display:none;}
  .nav-drop-menu a{
    font-family:'Space Grotesk', sans-serif; font-weight:500; font-size:0.86rem;
    color:var(--muted); padding:9px 12px; border-radius:4px;
    display:block; white-space:nowrap; border:0;
  }
  .nav-drop-menu a:hover, .nav-drop-menu a:focus-visible{
    background:var(--panel-2); color:var(--text); text-decoration:none; outline:none;
  }
  @media (max-width:880px){ .nav-drop-btn{padding:0 10px; font-size:0.8rem;} }
"""

CSS_ANCHOR = "  .nav-tabs a svg{width:16px; height:16px; flex:none;}\n"

CARET = ('<svg class="caret" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
         'stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" '
         'aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>')

DROP_MARKUP = """      <div class="nav-drop">
        <button type="button" class="nav-drop-btn{active}" id="hwBtn"
                aria-expanded="false" aria-haspopup="true" aria-controls="hwMenu">
          Hardware {caret}
        </button>
        <div class="nav-drop-menu" id="hwMenu" role="menu" hidden>
          <a role="menuitem" href="hardware.html#companions">Companions</a>
          <a role="menuitem" href="hardware.html#repeaters">Repeaters</a>
          <a role="menuitem" href="hardware.html#antennas">Antennas</a>
          <a role="menuitem" href="hardware.html#diy">DIY</a>
        </div>
      </div>
"""

DROP_JS = """
<script>
// Nav dropdown. The menu is fixed-positioned rather than absolute because
// .nav-tabs is a horizontal scroller and would clip it.
(function(){
  var btn  = document.getElementById('hwBtn');
  var menu = document.getElementById('hwMenu');
  if (!btn || !menu) return;

  function place(){
    var r = btn.getBoundingClientRect();
    menu.style.top  = (r.bottom + 4) + 'px';
    // Keep it on screen on narrow viewports.
    var w = menu.offsetWidth || 186;
    menu.style.left = Math.max(8, Math.min(r.left, window.innerWidth - w - 8)) + 'px';
  }
  function open(){
    menu.hidden = false;
    btn.setAttribute('aria-expanded', 'true');
    place();
  }
  function close(){
    menu.hidden = true;
    btn.setAttribute('aria-expanded', 'false');
  }
  function toggle(){ menu.hidden ? open() : close(); }

  btn.addEventListener('click', function(e){ e.stopPropagation(); toggle(); });
  document.addEventListener('click', function(e){
    if (!menu.hidden && !menu.contains(e.target)) close();
  });
  document.addEventListener('keydown', function(e){
    if (e.key === 'Escape' && !menu.hidden){ close(); btn.focus(); }
  });
  // Any geometry change invalidates a fixed position, so just dismiss.
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

GS_TAB = re.compile(
    r'([ \t]*<a href="getting-started\.html"[^>]*>Getting Started</a>\n)')


def add_dropdown(src, active=False):
    assert src.count(CSS_ANCHOR) == 1, "nav CSS anchor"
    assert "nav-drop-btn" not in src, "dropdown already present"
    src = src.replace(CSS_ANCHOR, CSS_ANCHOR + DROP_CSS)

    m = GS_TAB.search(src)
    assert m, "Getting Started tab anchor"
    markup = DROP_MARKUP.format(active=" active" if active else "", caret=CARET)
    src = src[:m.end(1)] + markup + src[m.end(1):]

    assert src.count("</body>") == 1, "body close anchor"
    return src.replace("</body>", DROP_JS + "</body>")


for name in PAGES:
    src = read(name)
    write(name, add_dropdown(src))
    print(f"{name}: Hardware dropdown added")


# ---------------------------------------------------------- 3. hardware.html

HW_CSS = """
  /* ===== HARDWARE ===== */
  .hw-head{max-width:64ch; margin-bottom:44px;}
  .hw-head h1{font-size:clamp(2rem, 5vw, 2.9rem); line-height:1.05; margin-bottom:16px;}
  .hw-head p{color:var(--muted); font-size:1.05rem;}

  .hw-section{margin-bottom:56px; scroll-margin-top:76px;}
  .hw-section > h2{
    font-size:1.5rem; margin-bottom:6px;
    display:flex; align-items:center; gap:12px;
  }
  .hw-section > h2::after{
    content:''; flex:1; height:1px; background:var(--line-soft);
  }
  .hw-section > .hw-note{color:var(--muted-2); font-size:0.92rem; margin-bottom:22px;}

  .hw-sub{
    font-family:'JetBrains Mono', monospace; font-size:0.72rem;
    letter-spacing:0.14em; text-transform:uppercase; color:var(--muted-2);
    margin:26px 0 12px;
  }

  .hw-grid{display:grid; gap:12px; grid-template-columns:repeat(auto-fit, minmax(232px, 1fr));}
  .hw-card{
    background:var(--panel); border:1px solid var(--line-soft);
    border-radius:var(--radius); padding:16px 18px;
    display:flex; flex-direction:column; gap:8px;
  }
  .hw-card h3{font-size:1rem; margin:0; line-height:1.3;}
  .hw-card p{color:var(--muted); font-size:0.9rem; margin:0; line-height:1.5;}
  .hw-card .spec{
    font-family:'JetBrains Mono', monospace; font-size:0.76rem;
    color:var(--bridge-blue); letter-spacing:0.02em;
  }

  /* the vibe scale, low to high */
  .tier{
    align-self:flex-start;
    font-family:'JetBrains Mono', monospace; font-size:0.66rem;
    letter-spacing:0.1em; text-transform:uppercase;
    padding:3px 8px; border-radius:3px; border:1px solid;
  }
  .tier-basic{color:var(--muted-2); border-color:var(--line); background:var(--panel-2);}
  .tier-alright{color:#7fa5e8; border-color:#2f4a7d; background:rgba(42,99,200,0.12);}
  .tier-cooking{color:#9698f0; border-color:var(--signal-dim); background:rgba(110,112,230,0.12);}
  .tier-gas{color:var(--rose); border-color:var(--rose-dim); background:rgba(242,200,97,0.10);}
  .tier-fire{
    color:var(--rose); border-color:var(--rose); background:rgba(242,200,97,0.16);
    box-shadow:0 0 12px rgba(242,200,97,0.28);
  }
  .tier-avoid{color:#e8724f; border-color:#7a3a26; background:rgba(232,114,79,0.12);}

  .hw-callout{
    border-left:3px solid var(--rose); background:var(--panel-2);
    padding:12px 16px; border-radius:0 var(--radius) var(--radius) 0;
    color:var(--muted); font-size:0.92rem; margin-bottom:16px;
  }
  .hw-callout strong{color:var(--text);}

  .hw-soon{
    border:1px dashed var(--line); border-radius:var(--radius);
    padding:28px; text-align:center; color:var(--muted-2); font-size:0.95rem;
  }

  .conn-table{width:100%; border-collapse:collapse; font-size:0.9rem;}
  .conn-table th{
    text-align:left; padding:9px 14px;
    font-family:'JetBrains Mono', monospace; font-size:0.7rem;
    letter-spacing:0.12em; text-transform:uppercase; color:var(--muted-2);
    border-bottom:1px solid var(--line);
  }
  .conn-table td{
    padding:12px 14px; border-bottom:1px solid var(--line-soft);
    color:var(--muted); vertical-align:top; line-height:1.55;
  }
  .conn-table tr:last-child td{border-bottom:0;}
  .conn-table .pair{
    font-family:'JetBrains Mono', monospace; color:var(--text);
    white-space:nowrap; font-size:0.84rem;
  }
  .conn-table td ul{margin:0; padding-left:16px;}
  .conn-table td li{margin:0 0 3px;}
  .conn-wrap{
    background:var(--panel); border:1px solid var(--line-soft);
    border-radius:var(--radius); overflow-x:auto;
  }
  .hearts{font-size:1.1rem; letter-spacing:2px;}
"""


def card(name, tier=None, spec=None, desc=None):
    t = f'\n          <span class="tier tier-{tier[0]}">{tier[1]}</span>' if tier else ""
    s = f'\n          <div class="spec">{spec}</div>' if spec else ""
    d = f'\n          <p>{desc}</p>' if desc else ""
    return f"""        <div class="hw-card">
          <h3>{name}</h3>{t}{s}{d}
        </div>"""


def grid(cards):
    return '      <div class="hw-grid">\n' + "\n".join(cards) + "\n      </div>"


companions = grid([
    card("Seeed T1000-E"),
    card("WisMesh TAG"),
    card("Wio Tracker L1 Pro"),
    card("Heltec WiFi LoRa 32 V4-R8"),
])

ant_sma = grid([
    card("Muzi Works", ("gas", "Gas"), desc="Companion gas."),
    card("Stock SenseCAP Solar", ("alright", "Alright"),
         desc="It's alright for a small repeater antenna."),
    card("Atvalox Whip", ("gas", "Gas"), desc="Companion gas."),
])

ant_n = grid([
    card("Alfa 5 dBi", ("basic", "Basic"),
         desc="Basic. Small step up from a whip. Small repeater use."),
    card("Rokland 5.8 dBi", ("cooking", "Cooking"),
         desc="Cooking. Starting to get big-boy coverage now."),
    card("Rokland 8 dBi", ("cooking", "Cookish?"),
         desc="Cookish? Haven't noticed a significant gain over the 5.8 dBi."),
    card("Rokland 10 dBi", ("gas", "Gas"),
         desc="Gas. Lonnnnng ol' distance."),
])

enclosures = grid([
    card("PVC &mdash; screw cover", ("basic", "Basic")),
    card("PVC &mdash; hinge cover", ("cooking", "Cooking")),
    card("Aluminum &mdash; hinge cover", ("gas", "Gas")),
    card("Aluminum &mdash; Nebra", ("fire", "Straight Fire")),
])

boards = grid([
    card("RAK Standard", spec="22 dBm",
         desc="Good for residential roof repeaters &mdash; &ldquo;neighborhood&rdquo; coverage."),
    card("RAK 1W", spec="30 dBm",
         desc="Better for residential roof repeaters &mdash; &ldquo;whole side of town&rdquo; "
              "coverage. Built-in (decent) filters."),
    card("Heltec v4",
         desc="I dunno. People seem to like it."),
    card("Station G3",
         desc='<span class="hearts">&#10084;&#65039; &#10084;&#65039; &#10084;&#65039;</span>'),
])

batteries = grid([
    card("Li-ion 18650", ("alright", "Solid"), desc="Standard option. Solid."),
    card("Li-ion 21700", ("gas", "Very Solid"),
         desc="Upgraded option. Very solid, higher capacity."),
    card("Li-ion pouch cell", ("avoid", "Avoid"),
         desc="Spicy pillows. We'd advise against these."),
])

COAX = [
    ("IPEX &rarr; SMA", ["From board to SMA antenna", "From board to filter"]),
    ("IPEX &rarr; RP-SMA", ["From board to RP-SMA antenna"]),
    ("IPEX &rarr; N-Type", ["From board to N-Type antenna"]),
    ("SMA &rarr; SMA", ["From boards <em>with built-in SMA output</em> to antenna",
                        "From boards <em>with built-in SMA output</em> to filter",
                        "From filter to antenna"]),
    ("SMA &rarr; RP-SMA", ["From SMA output to RP-SMA antenna"]),
    ("RP-SMA &rarr; SMA", ["From RP-SMA output to SMA antenna",
                           "Seeed SenseCAP Solar to SMA antenna"]),
    ("SMA &rarr; N-Type", ["From SMA output to N-Type antenna",
                           "From SMA filter output to antenna"]),
    ("RP-SMA &rarr; N-Type", ["From RP-SMA output to N-Type antenna"]),
]

coax_rows = "\n".join(
    f'            <tr><td class="pair">{p}</td><td><ul>'
    + "".join(f"<li>{u}</li>" for u in uses)
    + "</ul></td></tr>"
    for p, uses in COAX
)

HW_MAIN = f"""<main>
  <div class="wrap">
    <div class="hw-head">
      <h1>Hardware</h1>
      <p>What we actually run, and what we'd tell a friend to buy. Opinions are
         ours, prices aren't &mdash; check current listings before you order. If
         something here isn't clear, ask in Discord and someone will talk you
         through it.</p>
    </div>

    <section class="hw-section" id="companions">
      <h2>Companions</h2>
      <p class="hw-note">Handheld and pocket nodes &mdash; what you carry.</p>
{companions}
    </section>

    <section class="hw-section" id="repeaters">
      <h2>Repeaters</h2>
      <p class="hw-note">Pre-built, ready to mount.</p>
      <div class="hw-soon">Picks for this section are still being decided.
        Ask in Discord in the meantime &mdash; or see
        <a href="#diy">DIY</a> if you'd rather build one.</div>
    </section>

    <section class="hw-section" id="antennas">
      <h2>Antennas</h2>
      <p class="hw-note">The single biggest thing you can change. Match the
         connector to your board before you order.</p>

      <p class="hw-sub">SMA / RP-SMA</p>
{ant_sma}

      <p class="hw-sub">N-Type</p>
{ant_n}
    </section>

    <section class="hw-section" id="diy">
      <h2>DIY Supplies</h2>
      <p class="hw-note">Parts for building your own repeater.</p>

      <p class="hw-sub">Enclosures</p>
{enclosures}

      <p class="hw-sub">Boards</p>
{boards}

      <p class="hw-sub">Batteries</p>
      <div class="hw-callout"><strong>Only buy from a trusted source.</strong>
        Counterfeit and re-wrapped cells are common, and a bad cell in a sealed
        box on a roof is not a problem you want to find out about later.</div>
{batteries}

      <p class="hw-sub">Coax whips &amp; cable</p>
      <div class="conn-wrap">
        <table class="conn-table">
          <thead><tr><th>Connector pair</th><th>What it's for</th></tr></thead>
          <tbody>
{coax_rows}
          </tbody>
        </table>
      </div>
    </section>
  </div>
</main>"""

# Build the page off the About shell: same nav, footer, background, and token
# block, with the About-only rules swapped for the hardware ones.
shell = read("about.html")

ABOUT_CSS_START = "  .about-col{max-width:60ch;}"
ABOUT_CSS_END = "  .btn-discord:hover{background:#6c75f5; text-decoration:none;}\n"
i = shell.index(ABOUT_CSS_START)
j = shell.index(ABOUT_CSS_END) + len(ABOUT_CSS_END)
hw = shell[:i] + HW_CSS.strip("\n") + "\n" + shell[j:]

# Swap the main content.
m = re.search(r"<main>.*?</main>", hw, re.S)
assert m, "main block"
hw = hw[:m.start()] + HW_MAIN + hw[m.end():]

# Active tab moves from About to the Hardware dropdown.
hw = hw.replace('<a href="about.html" class="active">About</a>',
                '<a href="about.html">About</a>')
hw = hw.replace('class="nav-drop-btn" id="hwBtn"',
                'class="nav-drop-btn active" id="hwBtn"')

# Placeholder title; seo.py owns the real one.
hw = re.sub(r"<title>.*?</title>", "<title>Hardware</title>", hw, flags=re.S)
# Drop the About page's SEO fence so seo.py writes a fresh one.
hw = re.sub(r"<!-- seo:start -->.*?<!-- seo:end -->\n?", "", hw, flags=re.S)

write("hardware.html", hw)
print(f"hardware.html: created ({len(hw):,} bytes)")
