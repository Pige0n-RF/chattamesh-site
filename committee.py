"""Mesh Fund Committee -- shared by two generators.

The announcement card (build_announcements.py) and the funding page
(build_funding.py) publish the same stewards, the same account holder and the
same pool link. Those change as the committee changes, so they live here once
rather than in two files that would quietly drift apart -- which is how the
treasury figure ended up disagreeing with itself in Rev 2.3.

Edit the data below and re-run both generators.
"""

# The committee was seated on 14 November 2026. Before that this read
# "First draft -- open for feedback" and both pages framed it as a proposal.
STATUS = "Committee seated"

# Who creates and holds the PayPal Pool account.
HOLDER = "@Zixxorb | Cleveland"

# The live pool. Set to None and both pages go back to saying the pool is not
# open yet, rather than publishing a dead link.
PAYPAL_URL = "https://www.paypal.com/pool/9ujedceAb6?sr=wccr"

# Scanned from a phone at meetings and presentations. Regenerate with
# tools/make-qr.py if PAYPAL_URL ever changes -- a stale QR code takes money
# to the wrong place and nobody can tell by looking at it.
PAYPAL_QR = "images/funding-qr.png"

# The Fund Stewards, as they are named in Discord. Handles are published
# exactly as written: several carry their own area ("| Cleveland", "| CHA"),
# so there is no separate location field to get wrong.
SEATS = [
    "@Zixxorb | Cleveland",
    "@HeWhoPuns",
    "@Pige0n | Redbank",
    "@MadMax911",
    "@BCx | CHA",
]


def seats_html(indent="          "):
    """The steward list. Both pages carry the .fc-seats CSS below."""
    return "\n".join(f'{indent}<li><span class="who">{who}</span></li>'
                     for who in SEATS)


# Both pages set a `p` rule on the block that holds this markup, and
# `.fundcom p` / `.fc-block p` are (0,1,1). A bare class is (0,1,0) and
# loses, so every paragraph class here is written qualified by its parent.
# That trap has now cost this project three separate bugs.
CSS = """
  .fc-seats{list-style:none; padding:0; margin:0 0 11px;
            display:flex; flex-direction:column; gap:7px;}
  .fc-seats li{
    display:flex; align-items:baseline; gap:10px; margin:0;
    padding:9px 13px; border:1px solid var(--line-soft);
    border-radius:var(--radius); background:var(--panel-2);
  }
  .fc-seats .who{color:var(--text); font-weight:600; font-size:0.93rem;}

  .pool{
    display:flex; align-items:center; gap:20px; flex-wrap:wrap;
    border:1px solid var(--signal); background:rgba(110,112,230,0.08);
    border-radius:var(--radius); padding:18px 20px; margin:0 0 14px;
  }
  .pool img{
    width:132px; height:132px; flex:none; border-radius:6px;
    background:#fff; padding:6px;
  }
  .pool-body{flex:1 1 220px; min-width:0;}
  .pool .btn-pool{
    display:inline-block; margin-top:4px; padding:10px 18px;
    background:var(--signal); color:#fff; font-weight:600; font-size:0.95rem;
    border-radius:var(--radius); text-decoration:none; word-break:break-word;
  }
  .pool .btn-pool:hover{background:#6c75f5; text-decoration:none;}
"""
