#!/usr/bin/env python3
"""Add a Local Radio Clubs section to the home page, under the partner meshes.

The logo wells carry a light plate rather than sitting on the panel navy. These
are third-party brand marks drawn for light backgrounds -- the W4GTA mark is
dark navy line art and all but disappears on the dark card. The transparent
PNGs are what make the plate work: a white disc logo on a white plate reads as
one shape instead of a white box pasted on navy.

Idempotent by assertion.
"""
import os

P = os.path.join("public", "index.html")
src = open(P, encoding="utf-8").read()
assert 'id="clubs"' not in src, "clubs section already present"

# --------------------------------------------------------------------- CSS
CSS_ANCHOR = "  @media (max-width:720px){ .partner-grid{grid-template-columns:1fr;} }\n"
CSS = """
  /* ===== LOCAL RADIO CLUBS ===== */
  .clubs-grid{
    display:grid; gap:18px;
    grid-template-columns:repeat(auto-fit, minmax(230px, 1fr));
  }
  .club-card{display:flex; flex-direction:column; gap:14px;}
  /* Light plate: these marks are drawn for white, not for the panel navy. */
  .club-logo-wrap{
    height:150px; display:flex; align-items:center; justify-content:center;
    background:#f4f5f8; border:1px solid var(--line-soft);
    border-radius:var(--radius); padding:18px;
  }
  .club-logo{max-height:112px; max-width:100%; width:auto; display:block;}
  .club-card h3{font-size:1rem; margin:0;}
  .club-call{
    font-family:'JetBrains Mono', monospace; font-size:0.72rem;
    letter-spacing:0.12em; color:var(--rose);
  }
  .club-links{display:flex; align-items:center; gap:14px; margin-top:auto; padding-top:4px;}
  .club-links a{
    font-family:'JetBrains Mono', monospace; font-size:0.76rem;
    display:inline-flex; align-items:center; gap:6px;
  }
  .club-links svg{width:15px; height:15px;}
  @media (max-width:720px){ .club-logo-wrap{height:132px;} }
"""
assert src.count(CSS_ANCHOR) == 1, "partner grid css anchor"
src = src.replace(CSS_ANCHOR, CSS_ANCHOR + CSS)

# ------------------------------------------------------------------ markup
GLOBE = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
         'stroke-width="1.8" aria-hidden="true"><circle cx="12" cy="12" r="9"/>'
         '<path d="M3 12h18"/><path d="M12 3a15 15 0 0 1 0 18a15 15 0 0 1 0-18Z"/>'
         '</svg>')

# Names and callsigns are taken from the marks themselves.
CLUBS = [
    ("Tri-States Amateur Radio Club", "W4GTA", "w4gta",
     "https://tristatesarc.com/club/", "tristatesarc.com"),
    ("Chattanooga Amateur Radio Club", "W4AM", "w4am",
     "https://w4am.net/", "w4am.net"),
    ("Cleveland Amateur Radio Club", "KA4J", "ka4j",
     "https://www.carc.cc/", "carc.cc"),
]

cards = []
for name, call, slug, url, label in CLUBS:
    cards.append(f'''      <div class="card club-card">
        <div class="club-logo-wrap"><img class="club-logo"
          src="images/clubs/{slug}.png" alt="{name} ({call})"
          loading="lazy" onerror="this.remove();"></div>
        <div>
          <h3>{name}</h3>
          <span class="club-call">{call}</span>
        </div>
        <div class="club-links">
        <a href="{url}" target="_blank" rel="noopener">{GLOBE}{label}</a>
        </div>
      </div>''')

SECTION = '''
<section id="clubs">
  <div class="wrap">
    <div class="section-head">
      <div>
        <span class="section-tag">Local Radio Clubs</span>
        <h2>On the Ham Bands</h2>
      </div>
      <p class="section-desc">Mesh isn't the only radio in town. These clubs run
        nets, testing sessions, and emergency comms across the Tennessee Valley.</p>
    </div>

    <div class="clubs-grid">
''' + "\n\n".join(cards) + '''
    </div>
  </div>
</section>
'''

# Straight after the partners section, before the footer.
CLOSE = "</section>\n\n<footer>"
assert src.count(CLOSE) == 1, "partners close / footer"
src = src.replace(CLOSE, "</section>\n" + SECTION + "\n<footer>")

open(P, "w", encoding="utf-8").write(src)
print(f"index.html: Local Radio Clubs section added ({len(src):,} bytes)")
