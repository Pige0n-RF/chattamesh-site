#!/usr/bin/env python3
"""Build funding.html off the About shell.

Generated like the other content pages. Edit the data below and re-run; the
HTML is overwritten.

Three of the four ledger sections are deliberately empty. They use the same
"coming soon" panel so an unfilled section reads as not-yet-published rather
than broken -- which matters more here than anywhere else on the site, because
the whole point of the page is that money is accounted for in public.
"""
import os
import re

import committee

PUB = "public"
DISCORD = "https://discord.gg/XF354A3e9m"

seats = committee.seats_html("        ")

STATUS = committee.STATUS

OPTIONS = [
    ("Option 1", "The &ldquo;GoFundMe&rdquo; approach",
     "Funded repeater by repeater. Each build gets its own appeal, and people "
     "give to the specific thing they want to see go up.", False),
    ("Option 2", "The &ldquo;non-profit / club&rdquo; approach",
     "Electing a treasurer and running a registered non-profit. "
     "<strong>No one at this time wants to run a non-profit</strong>, so this "
     "one is parked unless someone volunteers.", False),
    ("Option 3", "The &ldquo;NashMesh&rdquo; approach",
     "A PayPal pool that can be donated to, with resource allocation voted "
     "upon by the group.", True),
]

# (heading, body html or None for the coming-soon panel)
# (amount, what it went to, date shown, ISO date for <time>)
ALLOCATIONS = [
    ("$100", "Toward repeater boards", "10/9/2026", "2026-10-09"),
]

alloc_rows = "\n".join(
    f"""        <div class="alloc-row">
          <p class="alloc-amt">{amt}</p>
          <p class="alloc-what">{what}</p>
          <p class="alloc-date"><time datetime="{iso}">{shown}</time></p>
        </div>"""
    for amt, what, shown, iso in ALLOCATIONS)

LEDGER = [
    ("Resource allocation history",
     f'<div class="alloc">\n{alloc_rows}\n      </div>'),
    ("Current resource pool",
     '<p class="ledger-figure">$0</p>'),
    ("How to contribute",
     f'<p>Through the <a href="{committee.PAYPAL_URL}" target="_blank" '
     f'rel="noopener">ChattaMesh PayPal Pool</a>, or by scanning the QR '
     f'code above &mdash; the same code is on hand at meetings and '
     f'presentations.</p>'),
]

CSS = """
  /* ===== FUNDING ===== */
  .fund-head{max-width:64ch; margin-bottom:38px;}
  .fund-head h1{font-size:clamp(2rem, 5vw, 2.9rem); line-height:1.05; margin-bottom:14px;}
  .fund-head .status{
    display:inline-flex; align-items:center; gap:8px; margin-bottom:16px;
    font-family:'JetBrains Mono', monospace; font-size:0.68rem;
    letter-spacing:0.14em; text-transform:uppercase; color:var(--rose);
    border:1px solid var(--rose-dim); background:rgba(242,200,97,0.09);
    border-radius:3px; padding:4px 10px;
  }
  .fund-head p{color:var(--muted); font-size:1.05rem;}

  .fund-sub{
    font-family:'JetBrains Mono', monospace; font-size:0.72rem;
    letter-spacing:0.14em; text-transform:uppercase; color:var(--muted-2);
    margin:0 0 14px;
  }

  .opt-grid{display:grid; gap:16px; grid-template-columns:repeat(auto-fit, minmax(260px,1fr)); margin-bottom:22px;}
  .opt{
    background:var(--panel); border:1px solid var(--line-soft);
    border-radius:var(--radius); padding:20px 20px 22px;
    display:flex; flex-direction:column; gap:9px;
  }
  .opt .n{
    font-family:'JetBrains Mono', monospace; font-size:0.68rem;
    letter-spacing:0.14em; text-transform:uppercase; color:var(--signal);
  }
  .opt h3{font-size:1.02rem; margin:0; line-height:1.35;}
  .opt p{color:var(--muted); font-size:0.92rem; line-height:1.65; margin:0;}
  .opt strong{color:var(--text); font-weight:600;}

  .opt.chosen{border-color:var(--signal); background:rgba(110,112,230,0.07);}
  .opt.chosen .n{color:var(--rose);}
  .opt .n em{
    font-style:normal; margin-left:9px; padding:2px 7px;
    border:1px solid var(--rose-dim); border-radius:3px;
    background:rgba(242,200,97,0.1); color:var(--rose);
  }

  /* ===== COMMITTEE =====
     Qualified with .fc-block because the block sets its own `p` rule, which
     is (0,1,1) and beats a bare class. */
  .fc-block{
    background:var(--panel); border:1px solid var(--line-soft);
    border-radius:var(--radius); padding:22px 22px 24px; margin-bottom:50px;
  }
  .fc-block p{color:var(--muted); font-size:0.94rem; line-height:1.65; margin:0 0 11px;}
  .fc-block p:last-child{margin-bottom:0;}
  .fc-block strong{color:var(--text); font-weight:600;}
  .fc-block a{color:var(--signal);}
  .fc-block h2{font-size:1.05rem; margin:0 0 12px;}
  .fc-block p.fc-head{
    font-family:'JetBrains Mono', monospace; font-size:0.72rem;
    letter-spacing:0.14em; text-transform:uppercase; color:var(--rose);
    margin:24px 0 9px;
  }
  .fc-block ul:not(.fc-seats){margin:0 0 11px; padding-left:20px;}
  .fc-block li{color:var(--muted); font-size:0.94rem; line-height:1.65; margin-bottom:5px;}

  .transparency{
    border-left:3px solid var(--amber); background:var(--panel-2);
    padding:15px 18px; border-radius:0 var(--radius) var(--radius) 0;
    color:var(--muted); font-size:0.95rem; line-height:1.65; margin:0 0 50px;
  }
  .transparency strong{color:var(--text);}

  .ledger{display:flex; flex-direction:column; gap:18px;}
  .ledger-row{
    background:var(--panel); border:1px solid var(--line-soft);
    border-radius:var(--radius); padding:20px 22px 22px;
  }
  .ledger-row h2{font-size:1.05rem; margin:0 0 12px;}
  .ledger-row p{color:var(--muted); font-size:0.94rem; line-height:1.65; margin:0;}
  .ledger-row a{color:var(--signal);}
  /* Needs the .ledger-row prefix: `.ledger-row p` is (0,1,1) and would
     otherwise outrank a bare class on font-size and colour. */
  .ledger-row p.ledger-figure{
    font-size:2rem; font-weight:700; color:var(--rose);
    line-height:1; margin:0 0 8px;
  }
  /* Allocation line items. Amount left, what it bought in the middle,
     date pushed right. Every class is .ledger-row p.x (0,2,1): `.ledger-row p`
     is (0,1,1) and outranks a bare class, which is what silently killed
     .ledger-figure in Rev 2.3. */
  .alloc{display:flex; flex-direction:column; gap:11px;}
  .alloc-row{display:flex; align-items:baseline; gap:14px; flex-wrap:wrap;}
  .ledger-row p.alloc-amt{
    font-family:'JetBrains Mono', monospace; font-size:1.02rem; font-weight:700;
    color:var(--rose); flex:none; margin:0;
  }
  .ledger-row p.alloc-what{flex:1 1 auto; margin:0;}
  .ledger-row p.alloc-date{
    font-family:'JetBrains Mono', monospace; font-size:0.78rem;
    color:var(--muted-2); flex:none; margin:0 0 0 auto; white-space:nowrap;
  }

  .soon{
    border:1px dashed var(--line); border-radius:var(--radius);
    padding:22px; text-align:center; color:var(--muted-2); font-size:0.92rem;
  }
""" + committee.CSS

opts = "\n".join(f"""        <div class="opt{' chosen' if picked else ''}">
          <span class="n">{n}{'<em>chosen</em>' if picked else ''}</span>
          <h3>{title}</h3>
          <p>{body}</p>
        </div>""" for n, title, body, picked in OPTIONS)

rows = "\n".join(f"""      <div class="ledger-row">
        <h2>{head}</h2>
        {body if body else '<div class="soon">Coming soon.</div>'}
      </div>""" for head, body in LEDGER)

MAIN = f"""<main>
  <div class="wrap">
    <div class="fund-head">
      <h1>Funding</h1>
      <span class="status">{STATUS}</span>
      <p>ChattaMesh is funded by a <strong>PayPal Pool</strong>, with a
        committee of Fund Stewards voting on how it gets spent. The other
        options the group weighed are below, along with the public ledger.</p>
    </div>

    <div class="fc-block">
      <h2>Mesh Fund Committee</h2>

      <div class="pool">
        <img src="{committee.PAYPAL_QR}" width="564" height="564"
             alt="QR code linking to the ChattaMesh PayPal Pool."
             loading="lazy" decoding="async">
        <div class="pool-body">
          <p>Donations go to the ChattaMesh PayPal Pool, held by
            <strong>{committee.HOLDER}</strong>. Scan the code or use the link.</p>
          <a class="btn-pool" href="{committee.PAYPAL_URL}" target="_blank"
             rel="noopener">Contribute to the pool</a>
        </div>
      </div>

      <p class="fc-head">Your Fund Stewards</p>
      <p>The stewards vote, without bias, on how our donated and shared
        resources get spent. The focus is <strong>repeater parts</strong>
        &mdash; expanding and strengthening the mesh.</p>
      <ul class="fc-seats">
{seats}
      </ul>
      <p>If you have a concern about a specific steward, raise it publicly in
        <code>#funding</code> on <a href="{DISCORD}" target="_blank"
        rel="noopener">our Discord</a>, or bring it to the monthly meeting
        &mdash; 3rd Wednesday, 7:00 PM.</p>
    </div>

    <p class="fund-sub">Options on the table</p>
    <div class="opt-grid">
{opts}
    </div>

    <p class="transparency"><strong>Whichever option we choose</strong>,
      allocation of resources and donations needs to be made extremely public,
      for the sake of transparency. That is the one thing already agreed.</p>

    <p class="fund-sub">The ledger</p>
    <div class="ledger">
{rows}
    </div>
  </div>
</main>"""

shell = open(os.path.join(PUB, "about.html"), encoding="utf-8").read()
assert 'href="funding.html"' in shell, "run the nav patch first"

i = shell.index("  .about-col{max-width:60ch;}")
tail = "  .btn-discord:hover{background:#6c75f5; text-decoration:none;}\n"
j = shell.index(tail) + len(tail)
page = shell[:i] + CSS.strip("\n") + "\n" + shell[j:]

m = re.search(r"<main>.*?</main>", page, re.S)
assert m, "main block"
page = page[:m.start()] + MAIN + page[m.end():]

page = page.replace('<a href="about.html" class="active">About</a>',
                    '<a href="about.html">About</a>')
page = page.replace('<a href="funding.html">Funding</a>',
                    '<a href="funding.html" class="active">Funding</a>')

page = re.sub(r"<!-- seo:start -->.*?<!-- seo:end -->\n?", "", page, flags=re.S)
page = re.sub(r"<title>.*?</title>", "<title>Funding</title>", page, flags=re.S)

open(os.path.join(PUB, "funding.html"), "w", encoding="utf-8").write(page)
print(f"funding.html built ({len(page):,} bytes, {len(OPTIONS)} options, "
      f"{len(LEDGER)} ledger sections)")
