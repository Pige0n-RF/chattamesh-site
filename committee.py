"""Funding & Resource Committee -- shared by two generators.

The announcement card (build_announcements.py) and the funding page
(build_funding.py) publish the same names, the same account holder and the
same seat list. Those will change as seats fill, so they live here once
rather than in two files that would quietly drift apart -- which is exactly
how the treasury figure ended up disagreeing with itself in Rev 2.3.

Edit the data below and re-run both generators.
"""

# Shown as the status chip on the funding page and the pin on the card.
STATUS = "First draft &mdash; open for feedback"

# Who creates and holds the PayPal Pool account.
HOLDER = "@Zixxorb | Cleveland"

# There is no PayPal link yet: the pool opens once the committee exists.
# Set this to the pool URL and both pages pick it up.
PAYPAL_URL = None

# (handle, area) -- None marks a seat nobody has claimed.
SEATS = [
    ("@zixxorb2", "Cleveland"),
    ("@hewhopuns", "Red Bank"),
    ("@Pige0n | Redbank", "Red Bank / Hixson"),
    (None, None),
    (None, None),
]

FILLED = sum(1 for who, _ in SEATS if who)
OPEN = len(SEATS) - FILLED


def seats_html(indent="          "):
    """The nominee list. Both pages carry the .fc-seats CSS below."""
    out = []
    for who, where in SEATS:
        if who:
            out.append(f'{indent}<li><span class="who">{who}</span>'
                       f'<span class="where">{where}</span></li>')
        else:
            out.append(f'{indent}<li class="open">'
                       f'<span class="who">Open seat</span></li>')
    return "\n".join(out)


# Both pages set a `p` rule on the block that holds this markup, and
# `.fundcom p` / `.ledger-row p` are (0,1,1). A bare class is (0,1,0) and
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
  .fc-seats .where{
    font-family:'JetBrains Mono', monospace; font-size:0.74rem;
    color:var(--muted-2); margin-left:auto;
  }
  .fc-seats li.open{border-style:dashed; background:none;}
  .fc-seats li.open .who{color:var(--muted-2); font-weight:400; font-style:italic;}
"""
