#!/usr/bin/env python3
"""Rev1.1.2 -- About page: badge alongside the copy, Community Involvement.

All new CSS goes between the existing `.about-col` and `.btn-discord:hover`
anchors on purpose: build_hardware.py slices that exact range out when it
builds hardware.html off this shell, so About-only rules don't leak.
"""
import os
import re

P = "public/about.html"
src = open(P, encoding="utf-8").read()

# ------------------------------------------------------------------ CSS

CSS_ANCHOR = "  .btn-discord:hover{background:#6c75f5; text-decoration:none;}\n"
NEW_CSS = """
  /* Badge sits beside the copy on desktop, above it on mobile. Stacking
     reversed so the mark leads on a phone rather than being buried. */
  .about-grid{display:flex; align-items:flex-start; gap:56px;}
  .about-grid .about-col{flex:1 1 auto; min-width:0;}
  .about-badge{flex:0 0 300px; width:300px; margin-top:8px;}
  .about-badge img{width:100%; height:auto; display:block;}
  @media (max-width:900px){
    .about-grid{flex-direction:column-reverse; gap:28px; align-items:center;}
    .about-badge{flex:none; width:min(220px, 60vw); margin:0 auto;}
  }

  /* ===== COMMUNITY INVOLVEMENT ===== */
  .involve{margin-top:64px; padding-top:8px;}
  .involve > h2{font-size:1.6rem; margin-bottom:8px;}
  .involve > p.involve-sub{color:var(--muted); margin-bottom:26px; max-width:62ch;}
  .involve-grid{
    display:grid; gap:16px;
    grid-template-columns:repeat(auto-fit, minmax(258px, 1fr));
  }
  .involve-card{
    background:var(--panel); border:1px solid var(--line-soft);
    border-radius:var(--radius); padding:22px 22px 24px;
    display:flex; flex-direction:column; gap:12px;
  }
  .involve-card h3{font-size:1.05rem; margin:0; display:flex; align-items:center; gap:10px;}
  .involve-card h3 svg{width:19px; height:19px; flex:none; color:var(--signal);}
  .involve-card p{color:var(--muted); font-size:0.94rem; margin:0; line-height:1.62;}
  .involve-card .involve-foot{margin-top:auto; padding-top:6px;}
  .involve-card .btn-discord{width:auto;}
"""
assert src.count(CSS_ANCHOR) == 1, "about css anchor"
src = src.replace(CSS_ANCHOR, CSS_ANCHOR + NEW_CSS)

# ------------------------------------------------- badge beside the copy

OPEN_OLD = '  <div class="wrap">\n    <div class="about-col">'
OPEN_NEW = '''  <div class="wrap about-grid">
    <div class="about-col">'''
assert src.count(OPEN_OLD) == 1, "about-col open"
src = src.replace(OPEN_OLD, OPEN_NEW)

BADGE = '''    <div class="about-badge">
      <img src="images/chattamesh/chattamesh-badge.png"
           alt="ChattaMesh badge — the bridge, the ridge and the signal"
           width="600" height="600">
    </div>
'''

# ------------------------------------------------- community involvement

DISCORD_SVG = ('<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor" '
               'aria-hidden="true"><path d="M20.317 4.37a19.79 19.79 0 0 0-4.885-1.515'
               '.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0'
               '-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 '
               '19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 '
               '18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 '
               '.084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 '
               '13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128c.126-.094.252-.192.372'
               '-.291a.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 '
               '0 1 .078.01c.12.099.246.197.373.291a.077.077 0 0 1-.006.128 12.3 12.3 0 0 '
               '1-1.873.892.076.076 0 0 0-.041.107c.36.698.772 1.363 1.225 1.993a.076.076 '
               '0 0 0 .084.028 19.84 19.84 0 0 0 6.002-3.03.077.077 0 0 0 .032-.055c.5'
               '-5.177-.838-9.673-3.549-13.66a.06.06 0 0 0-.031-.028ZM8.02 15.33c-1.183 '
               '0-2.157-1.086-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.211 0 2.176 '
               '1.096 2.157 2.42 0 1.332-.955 2.418-2.157 2.418Zm7.975 0c-1.183 0-2.157'
               '-1.086-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.211 0 2.176 1.096 '
               '2.157 2.42 0 1.332-.946 2.418-2.157 2.418Z"/></svg>')

ICON = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" '
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{}</svg>')

INVOLVE = f'''
    <section class="involve">
      <h2>Community Involvement</h2>
      <p class="involve-sub">The mesh only reaches as far as people put it. Here
        are three ways in, from easiest to most useful.</p>

      <div class="involve-grid">
        <div class="involve-card">
          <h3>{ICON.format('<path d="M3 11 12 4l9 7"/><path d="M5 10v10h14V10"/><path d="M12 20v-5"/>')}
            Deploy a repeater</h3>
          <p>The easiest way to get your hands dirty with us is to simply deploy
            a repeater. You don't have to have a roof to get on the mesh or
            contribute meaningfully, but if you do have a roof, let's get a
            repeater up there and get you meshin'.</p>
          <div class="involve-foot">
            <a class="btn btn-ghost" href="hardware.html#repeaters">See repeater hardware</a>
          </div>
        </div>

        <div class="involve-card">
          <h3>{ICON.format('<path d="M12 21V9"/><path d="M8 21h8"/><path d="M12 9 6 3"/><path d="m12 9 6-6"/><circle cx="12" cy="9" r="1.6"/>')}
            Provide high site access</h3>
          <p>High site repeaters are extremely beneficial to the mesh &mdash; they
            reduce hops, increase routing consistency, and let us implement
            regions and filters across the local mesh. If you manage a downtown
            highrise, own a tower or silo, or have access to any high-elevation
            site, please get in touch on Discord.</p>
          <div class="involve-foot">
            <a class="btn btn-ghost" href="https://discord.gg/XF354A3e9m"
               target="_blank" rel="noopener">Contact us on Discord</a>
          </div>
        </div>

        <div class="involve-card">
          <h3>{ICON.format('<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2Z"/>')}
            Join the Discord</h3>
          <p>Join the discussion, ask questions, or just hang out and watch the
            mesh grow. Everyone has their place and their own voice in this
            community &mdash; so use it!</p>
          <div class="involve-foot">
            <a class="btn btn-discord" href="https://discord.gg/XF354A3e9m"
               target="_blank" rel="noopener">{DISCORD_SVG} Join the ChattaMesh Discord</a>
          </div>
        </div>
      </div>
    </section>
'''

# The badge is a sibling of .about-col inside the flex row; the involvement
# section goes after that row, full width.
CLOSE_OLD = """      </div>
    </div>
  </div>
</main>"""
CLOSE_NEW = f"""      </div>
    </div>
{BADGE}  </div>

  <div class="wrap">
{INVOLVE}  </div>
</main>"""
assert src.count(CLOSE_OLD) == 1, "about main close"
src = src.replace(CLOSE_OLD, CLOSE_NEW)

open(P, "w", encoding="utf-8").write(src)
print(f"about.html: badge + Community Involvement ({len(src):,} bytes)")
