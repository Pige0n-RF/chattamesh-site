#!/usr/bin/env python3
"""Build announcements.html off the About shell.

Generated, like the hardware and videos pages, so it always picks up the
current nav, footer and token block. Add to ITEMS and re-run; do not hand-edit
the HTML, it is overwritten.

The meeting carries schema.org Event markup in the body. seo.py owns the head
fence, so this goes in as a second JSON-LD block rather than fighting it --
valid, and qa.py parses every block on the page either way.
"""
import os
import re

import committee

PUB = "public"
DISCORD = "https://discord.gg/XF354A3e9m"

# ------------------------------------------------------------------ meeting

# ----------------------------------------------------------------- upcoming
# Both dates are open. After the October meeting the group settled on in-person
# quarterly and Discord monthly, so the cadence is known even when the date
# isn't -- worth showing, so "TBD" reads as scheduled-not-yet-dated rather than
# abandoned.

UPCOMING = [
    dict(kind="On Discord", cadence="Monthly",
         when="3rd Wednesday, 7:00 PM"),
    dict(kind="In person", cadence="Quarterly", when="TBD"),
]

# Standing agenda for the Discord meeting.
AGENDA = [
    "Battlefield Marathon Races",
    "Catoosa County EMA",
    "Infrastructure check-in and deadzone discussion",
]

# ------------------------------------------------------------- last meeting

LAST = dict(
    date_human="October 3, 2026",
    iso="2026-10-03",
    stream_id="uWH2PoxXLX0",
    stream_url="https://www.youtube.com/watch?v=uWH2PoxXLX0",
    thanks=[
        ('<a href="https://w4am.net/" target="_blank" rel="noopener">Chattanooga '
         'Amateur Radio Club</a> for coming in, opening the doors, and letting '
         'us use their classroom'),
        "@HeWhoPuns for hosting the meeting",
        "@Animusreptor for live streaming, mixing, and providing audio equipment",
    ],
    minutes=[
        ("Welcome and introductions", []),
        ("Review from last meeting", []),
        ("Regions presentation &mdash; Pige0n", [
            ('<span class="note">&ldquo;Thanks for being kind with my anxiety. '
             'Never done this before. Love you all!&rdquo; &mdash;Pige0n</span>'),
        ]),
        ("The FCC 500 kHz topic", [
            "No current plan of action to change. LoRa scans are being done on "
            "key infrastructure sites to determine the best frequency to use at "
            "500 kHz BW.",
            "No urgent need to change settings at this point.",
        ]),
        ("ThinkNode M9 malware", []),
        ("The website &mdash; settings, contacts, guides, etc.", [
            '<span class="note">(Please don\'t make me program a forum :( '
            '&mdash;Pige0n)</span>',
            "Please request any specific guides for anything you'd like!",
            "Adding a funding model &mdash; who donates, what's used.",
            "Add meeting minutes.",
        ]),
        ("Discord", []),
        ("The next meetup, and should they be more frequent?", [
            '<span class="decided">Decided</span> In-person meetings quarterly.',
            '<span class="decided">Decided</span> Discord for monthly meetings. '
            'Dates TBD.',
        ]),
        ('Funding <em>(to be continued)</em> &mdash; <a href="funding.html">see the funding page</a>', [
            ("Discussed three potential options:", [
                ('<strong>Option 1 &mdash; the &ldquo;GoFundMe&rdquo; '
                 'approach.</strong> Repeater-by-repeater basis.'),
                ('<strong>Option 2 &mdash; the &ldquo;non-profit / club&rdquo; '
                 'approach.</strong> Electing a treasurer and running a '
                 'non-profit. No one at this time wants to run a non-profit.'),
                ('<strong>Option 3 &mdash; the &ldquo;NashMesh&rdquo; '
                 'approach.</strong> A PayPal pool that can be donated to, with '
                 'resource allocation voted upon.'),
            ]),
            "Whichever option we choose, allocation of resources and donations "
            "needs to be made extremely public, for the sake of transparency.",
        ]),
        ("Extra things brought up", [
            ('Discussions with Chris-W4YEM of <a href="https://www.carc.cc/" '
             'target="_blank" rel="noopener">Cleveland ARC</a> about future '
             'MC/MT deployments.'),
            "Using repeater names to advertise small mom-and-pop businesses. "
            "Made clear there will be no advertisements taking up any airtime "
            "beyond the standard advert by repeater name.",
            "Alabama regions: at this time no Alabama regions are known, and we "
            "do not intend to impose anything upon them.",
        ]),
    ],
)

# ------------------------------------------------------------------- items
# (tag, title, html body). Newest first; the meeting above is pinned on top.

DISCORD_INLINE = (
    f'<a class="dc-inline" href="{DISCORD}" target="_blank" rel="noopener">'
    '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">'
    '<path d="M20.317 4.37a19.79 19.79 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c'
    '-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617'
    '-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032'
    '.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 '
    '5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0'
    '-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128c.126-.094.252'
    '-.192.372-.291a.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 '
    '0 0 1 .078.01c.12.099.246.197.373.291a.077.077 0 0 1-.006.128 12.3 12.3 0 0 1'
    '-1.873.892.076.076 0 0 0-.041.107c.36.698.772 1.363 1.225 1.993a.076.076 0 0 0 '
    '.084.028 19.84 19.84 0 0 0 6.002-3.03.077.077 0 0 0 .032-.055c.5-5.177-.838'
    '-9.673-3.549-13.66a.06.06 0 0 0-.031-.028ZM8.02 15.33c-1.183 0-2.157-1.086-2.157'
    '-2.419 0-1.333.955-2.419 2.157-2.419 1.211 0 2.176 1.096 2.157 2.42 0 1.332-.955 '
    '2.418-2.157 2.418Zm7.975 0c-1.183 0-2.157-1.086-2.157-2.419 0-1.333.955-2.419 '
    '2.157-2.419 1.211 0 2.176 1.096 2.157 2.42 0 1.332-.946 2.418-2.157 2.418Z"/>'
    '</svg>Discord</a>')

SCOPES = ["us", "us-east", "us-southeast", "us-tn", "us-tn-east", "us-tn-cha"]

ITEMS = [
    ("Regions", "Rolling out region scoping", f"""
      <p><strong>The big one.</strong> We're rolling out regions and getting
        ahead of things. As a default, most repeaters in Chattanooga are running
        this set of scopes:</p>
      <p class="scope-row">{''.join(f'<code>{s}</code>' for s in SCOPES)}</p>
      <p>There's more on setting up regions for your own repeater on the
        <a href="setup-information.html">Setup &amp; Information</a> page.</p>"""),

    ("MeshMapper", "Wardriving traffic is scoped to us-tn", """
      <p>MeshMapper is the app we use for wardriving. To keep that traffic local
        and avoid bothering our neighbors on the other side of the borders, we've
        scoped all <code>#wardriving</code> traffic to <code>us-tn</code> and
        enforced hybrid mode. A lot of members are also running the airtime
        saving function in the beta.</p>"""),

    ("MeshOMatic", "Getting CHA onto the map", """
      <p>We're working alongside AkkerKid to get the CHA region onto
        <a href="https://map.meshomatic.net/" target="_blank" rel="noopener">MeshOMatic</a>,
        and donating some computing power and wardriving data toward it. It's a
        great tool and worth a look.</p>"""),

    ("Website", "What's new here", f"""
      <p>Added a Videos tab, with The Comms Channel's playlists embedded. Added
        more hardware recommendations with links to where to buy them. Added
        more local mesh communities and radio clubs to the home page.</p>
      <p>If there's something else you'd like to see on the site, tell us on
        {DISCORD_INLINE}.</p>"""),
]

# --------------------------------------------------------------- archive
# Past events, newest first. Each entry is a finished .meet card; they
# live inside the collapsed <details> at the foot of the page.
ARCHIVED = [
    """
      <div class="meet past">
        <div class="meet-bar">
          <span class="meet-pin">Past event</span>
          <h2>Hamfest Chattanooga 2026 &mdash; October 16&ndash;17</h2>
        </div>
        <div class="meet-body hamfest">
          <img class="hamfest-banner" src="images/announcements/hamfest-2026.webp"
               width="1000" height="667" loading="lazy" decoding="async"
               alt="Hamfest Chattanooga 2026 &mdash; TennMesh, MeshCore, ChattaMesh
                    and UCMesh logos over the Chattanooga skyline and Walnut Street
                    Bridge at sunset.">
          <p>Hamfest Chattanooga 2026 is at the <strong>Catoosa County (GA)
            Colonnade</strong>. It&rsquo;s a spectacular new venue for the show,
            and only about two miles from I-75 at GA Exit 2A &mdash; which is
            itself about two miles below the Tennessee&ndash;Georgia state line,
            just south of Chattanooga.</p>
          <p class="addr">264 Catoosa Cir<br>Ringgold, GA 30736</p>
          <div class="panel">
            <p class="panel-head">MeshCore panel &middot; 4:00&ndash;5:00 PM</p>
            <p>Come learn about MeshCore.</p>
            <p class="panelists">Panelists: The Comms Channel (TennMesh)
              &middot; Pige0n (ChattaMesh) &middot; xJCross (UCMesh)</p>
          </div>
        </div>
      </div>
""",
]

# ---------------------------------------------------------------------- CSS

CSS = """
  /* ===== ANNOUNCEMENTS ===== */
  .ann-head{max-width:64ch; margin-bottom:38px;}
  .ann-head h1{font-size:clamp(2rem, 5vw, 2.9rem); line-height:1.05; margin-bottom:16px;}
  .ann-head p{color:var(--muted); font-size:1.05rem;}

  /* pinned meeting */
  .meet{
    background:var(--panel); border:1px solid var(--signal);
    border-radius:var(--radius); overflow:hidden; margin-bottom:46px;
    box-shadow:0 0 0 1px rgba(110,112,230,0.16), 0 14px 40px rgba(0,0,0,0.3);
  }
  .meet-bar{
    display:flex; align-items:center; gap:11px; flex-wrap:wrap;
    padding:13px 20px; background:var(--signal-dim);
    border-bottom:1px solid var(--line-soft);
  }
  .meet-pin{
    font-family:'JetBrains Mono', monospace; font-size:0.68rem;
    letter-spacing:0.16em; text-transform:uppercase; color:#c9cbf7;
  }
  .meet-bar h2{font-size:1.05rem; margin:0; color:var(--text);}
  .meet-body{padding:24px 20px 26px;}

  .meet-when{
    display:flex; flex-wrap:wrap; gap:12px 34px; margin-bottom:22px;
    padding-bottom:20px; border-bottom:1px solid var(--line-soft);
  }
  .meet-when > div{display:flex; flex-direction:column; gap:5px;}
  .meet-when .k{
    font-family:'JetBrains Mono', monospace; font-size:0.68rem;
    letter-spacing:0.13em; text-transform:uppercase; color:var(--muted-2);
  }
  .meet-when .v{color:var(--text); font-size:1.04rem; font-weight:600;}
  .meet-when .v small{display:block; color:var(--muted); font-weight:400; font-size:0.86rem;}

  .agenda-label{
    font-family:'JetBrains Mono', monospace; font-size:0.7rem;
    letter-spacing:0.14em; text-transform:uppercase; color:var(--muted-2);
    margin-bottom:12px;
  }
  .agenda{list-style:none; margin:0; padding:0; counter-reset:ag;}
  .agenda > li{
    counter-increment:ag; position:relative;
    padding:0 0 14px 34px; color:var(--text); font-size:0.98rem; line-height:1.5;
  }
  .agenda > li:last-child{padding-bottom:0;}
  .agenda > li::before{
    content:counter(ag); position:absolute; left:0; top:0;
    width:22px; height:22px; border-radius:50%;
    background:var(--panel-2); border:1px solid var(--line);
    font-family:'JetBrains Mono', monospace; font-size:0.7rem; color:var(--muted-2);
    display:flex; align-items:center; justify-content:center;
  }
  .agenda ul{list-style:none; margin:9px 0 0; padding:0;}
  .agenda ul li{
    color:var(--muted); font-size:0.91rem; line-height:1.6;
    padding:0 0 4px 15px; position:relative;
  }
  .agenda ul li::before{
    content:''; position:absolute; left:0; top:0.62em;
    width:5px; height:5px; border-radius:50%; background:var(--line);
  }

  /* next meetings */
  .next-grid{display:grid; gap:14px; grid-template-columns:repeat(auto-fit, minmax(210px,1fr)); margin-bottom:16px;}
  .next-card{
    background:var(--panel-2); border:1px solid var(--line-soft);
    border-radius:var(--radius); padding:16px 18px;
    display:flex; flex-direction:column; gap:6px;
  }
  .next-kind{
    font-family:'JetBrains Mono', monospace; font-size:0.68rem;
    letter-spacing:0.14em; text-transform:uppercase; color:var(--muted-2);
  }
  .next-when{font-size:1.35rem; font-weight:700; color:var(--rose); line-height:1;}
  .next-cadence{color:var(--muted); font-size:0.88rem;}
  .next-note{color:var(--muted-2); font-size:0.9rem; line-height:1.6; margin:0;}

  /* last meeting */
  .meet.past{border-color:var(--line); box-shadow:none;}
  .meet.past .meet-bar{background:var(--panel-2);}
  .meet.past .meet-pin{color:var(--muted-2);}

  /* True 16:9, capped by width rather than height. A max-height was
     overriding the aspect ratio and flattening this to ~3:1, which cropped the
     thumbnail to a slice and left the 16:9 player pillarboxed inside it. Width
     is the right lever: the box keeps the video's shape and the panel does not
     get tall enough to push the minutes off the screen. */
  .live-frame{
    position:relative; width:100%; max-width:760px; aspect-ratio:16/9;
    background:var(--panel-2); border:1px solid var(--line-soft);
    border-radius:var(--radius); padding:0; margin:0 auto 10px;
    display:block; cursor:pointer; overflow:hidden;
    text-decoration:none; color:inherit; -webkit-tap-highlight-color:transparent;
  }
  .live-frame:hover{text-decoration:none;}
  .live-frame img{position:absolute; inset:0; width:100%; height:100%; object-fit:cover;}
  .live-frame .live-inner{z-index:1; background:rgba(26,29,44,0.45);}
  .live-frame iframe{position:absolute; inset:0; width:100%; height:100%; border:0;}
  .live-inner{
    position:absolute; inset:0; display:flex; flex-direction:column;
    align-items:center; justify-content:center; gap:11px; padding:22px; text-align:center;
  }
  .live-inner strong{color:var(--text); font-size:1rem; font-weight:600;}
  .live-inner > span:last-child{color:var(--muted-2); font-size:0.87rem;}
  .vid-play{
    width:58px; height:41px; border-radius:10px; background:rgba(110,112,230,0.92);
    display:flex; align-items:center; justify-content:center; transition:background .15s ease;
  }
  .vid-play svg{width:19px; height:19px; color:#fff;}
  .live-frame:hover .vid-play{background:var(--signal);}
  .live-foot{color:var(--muted-2); font-size:0.86rem; margin:0 auto 22px; max-width:760px;}
  .live-foot a{color:var(--signal);}

  .thanks{list-style:none; margin:0 0 22px; padding:0;}
  .thanks li{
    color:var(--muted); font-size:0.94rem; line-height:1.6;
    padding:0 0 7px 20px; position:relative;
  }
  .thanks li::before{
    content:''; position:absolute; left:3px; top:0.62em;
    width:6px; height:6px; border-radius:50%; background:var(--amber);
  }
  .thanks a{color:var(--signal);}

  .agenda ul.lvl2{margin:7px 0 0 0;}
  .agenda ul li a{color:var(--signal);}
  .agenda .note{color:var(--muted-2); font-style:italic;}
  .agenda .decided{
    display:inline-block; margin-right:7px;
    font-family:'JetBrains Mono', monospace; font-size:0.62rem;
    letter-spacing:0.12em; text-transform:uppercase;
    color:var(--amber); border:1px solid var(--amber-dim);
    background:rgba(79,184,96,0.1); border-radius:3px; padding:2px 6px;
  }
  .agenda strong{color:var(--text); font-weight:600;}

  /* ===== RACE DAY =====
     The ops chart is 3040px of dense infographic. On a phone it is unreadable
     at any width the page can give it, so the card restates the facts people
     actually need in text and the picture links out to the full-size file.
     Classes are qualified (.race p.x) because `.race p` above is (0,1,1). */
  .race-chart{display:block; width:100%; height:auto; border-radius:var(--radius);
              border:1px solid var(--line-soft); background:#fff; margin:0 0 7px;}
  .race p.chart-note{font-size:0.8rem; color:var(--muted-2); margin:0 0 18px; text-align:center;}
  .race-maps{display:grid; gap:18px; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); margin-bottom:6px;}
  .race-alert{
    border:1px solid var(--rose-dim); background:rgba(242,200,97,0.1);
    border-radius:var(--radius); padding:15px 18px; margin:0 0 20px;
  }
  .race p.alert-head{
    font-family:'JetBrains Mono', monospace; font-size:0.7rem;
    letter-spacing:0.14em; text-transform:uppercase; color:var(--rose);
    margin:0 0 9px;
  }
  .as-table{width:100%; border-collapse:collapse; margin:0 0 11px; font-size:0.9rem;}
  .as-table th{
    font-family:'JetBrains Mono', monospace; font-size:0.66rem;
    letter-spacing:0.1em; text-transform:uppercase; color:var(--muted-2);
    text-align:left; font-weight:400; padding:0 10px 7px 0; border-bottom:1px solid var(--line-soft);
  }
  .as-table td{padding:8px 10px 8px 0; color:var(--muted); border-bottom:1px solid var(--line-soft);}
  .as-table td.n{color:var(--rose); font-weight:700; font-family:'JetBrains Mono', monospace; white-space:nowrap;}
  .as-table td.mi{font-family:'JetBrains Mono', monospace; font-size:0.8rem; color:var(--muted-2); white-space:nowrap;}
  .race a{color:var(--signal);}
  .race p.fc-head{
    font-family:'JetBrains Mono', monospace; font-size:0.72rem;
    letter-spacing:0.14em; text-transform:uppercase; color:var(--rose);
    margin:24px 0 9px;
  }
  .race-when{
    display:flex; flex-wrap:wrap; gap:9px 26px; margin:0 0 15px;
    padding:14px 17px; border:1px solid var(--line-soft);
    border-radius:var(--radius); background:var(--panel-2);
  }
  .race-when div{display:flex; flex-direction:column; gap:3px;}
  .race-when .k{
    font-family:'JetBrains Mono', monospace; font-size:0.66rem;
    letter-spacing:0.12em; text-transform:uppercase; color:var(--muted-2);
  }
  .race-when .v{color:var(--text); font-weight:600; font-size:0.94rem;}
  .race ul{margin:0 0 11px; padding-left:20px;}
  .race li{color:var(--muted); font-size:0.95rem; line-height:1.68; margin-bottom:5px;}

  /* ===== FUNDING COMMITTEE DRAFT =====
     Body type and .panel are shared with .hamfest above. The seat-list rules
     come from committee.py so this page and the funding page cannot drift. */
  .fundcom a{color:var(--signal);}
  .fundcom p.draft-note{
    border-left:3px solid var(--amber); background:var(--panel-2);
    padding:11px 15px; border-radius:0 var(--radius) var(--radius) 0;
    color:var(--muted-2); font-size:0.88rem; margin:0 0 22px;
  }
  .fundcom p.fc-head{
    font-family:'JetBrains Mono', monospace; font-size:0.72rem;
    letter-spacing:0.14em; text-transform:uppercase; color:var(--rose);
    margin:26px 0 9px;
  }
  .fundcom ul:not(.fc-seats){margin:0 0 11px; padding-left:20px;}
  .fundcom li{color:var(--muted); font-size:0.95rem; line-height:1.68; margin-bottom:5px;}
  /* ===== ARCHIVED EVENTS =====
     Native <details>, not the wireToggle() pattern from setup-information.html:
     that script lives inline in that page alone, and this page is generated
     from the About shell, so reusing it would mean shipping a second copy.
     <details> also works with JS off and is keyboard-accessible for free.
     Styled to match .regions-toggle so the two read as the same control. */
  .arch{margin-top:46px;}
  .arch summary{
    display:flex; align-items:center; gap:13px; cursor:pointer;
    padding:15px 18px; border-radius:var(--radius);
    border:1px solid var(--line-soft);
    background:linear-gradient(90deg, rgba(110,112,230,0.15), rgba(110,112,230,0.04));
    list-style:none;
  }
  /* Safari and Chrome each need their own kill switch for the default marker. */
  .arch summary::-webkit-details-marker{display:none;}
  .arch summary::marker{content:"";}
  .arch summary:hover{background:linear-gradient(90deg, rgba(110,112,230,0.22), rgba(110,112,230,0.08));}
  .arch-icon{
    color:var(--signal); font-size:0.9rem; flex:none;
    transition:transform 0.18s ease;
  }
  .arch[open] .arch-icon{transform:rotate(90deg);}
  .arch-label{font-weight:700; font-size:1.05rem; color:var(--text);}
  .arch-sub{
    font-family:'JetBrains Mono', monospace; font-size:0.72rem;
    letter-spacing:0.1em; text-transform:uppercase; color:var(--muted-2);
    margin-left:auto;
  }
  .arch-body{padding-top:20px;}
  @media (max-width:560px){
    .arch summary{flex-wrap:wrap;}
    .arch-sub{margin-left:44px;}
  }

  .ann-list{display:flex; flex-direction:column; gap:18px;}
  .ann{
    background:var(--panel); border:1px solid var(--line-soft);
    border-radius:var(--radius); padding:20px 22px 22px;
  }
  .ann-tag{
    font-family:'JetBrains Mono', monospace; font-size:0.68rem;
    letter-spacing:0.14em; text-transform:uppercase; color:var(--rose);
    display:block; margin-bottom:7px;
  }
  .ann h3{font-size:1.08rem; margin:0 0 10px;}
  .ann p{color:var(--muted); font-size:0.95rem; line-height:1.68; margin:0 0 11px;}
  .ann p:last-child{margin-bottom:0;}
  .ann a{color:var(--signal);}

  /* Hamfest block. It sits in a .meet shell above the meeting cards, and
     .meet-body sets no paragraph rules, so this restates the body type.
     Every class is written .hamfest p.x (0,2,1) rather than bare (0,1,0):
     the stylesheet is full of element-qualified descendant rules that would
     otherwise outrank them, which is what ate .ledger-figure in Rev 2.3. */
  .hamfest p, .fundcom p, .race p{color:var(--muted); font-size:0.95rem; line-height:1.68; margin:0 0 11px;}
  .hamfest p:last-child, .fundcom p:last-child, .race p:last-child{margin-bottom:0;}
  .hamfest strong, .fundcom strong, .race strong{color:var(--text); font-weight:600;}
  .hamfest-banner{
    display:block; width:100%; height:auto; margin:0 0 17px;
    border:1px solid var(--line-soft); border-radius:var(--radius);
  }
  .hamfest p.addr{
    font-family:'JetBrains Mono', monospace; font-size:0.84rem;
    line-height:1.75; color:var(--text);
  }
  .hamfest .panel, .fundcom .panel, .race .panel{
    border-left:3px solid var(--signal); background:var(--panel-2);
    padding:14px 17px 15px; border-radius:0 var(--radius) var(--radius) 0;
    margin-top:16px;
  }
  .hamfest p.panel-head, .fundcom p.panel-head, .race p.panel-head{
    font-family:'JetBrains Mono', monospace; font-size:0.7rem;
    letter-spacing:0.14em; text-transform:uppercase; color:var(--signal);
    margin:0 0 9px;
  }
  .hamfest p.panelists{color:var(--text); font-size:0.9rem; margin:0;}
  .ann code, .scope-row code{
    font-family:'JetBrains Mono', monospace; font-size:0.84rem;
    background:var(--panel-2); border:1px solid var(--line-soft);
    border-radius:4px; padding:2px 7px; color:var(--rose);
  }
  .scope-row{display:flex; flex-wrap:wrap; gap:7px;}

  .dc-inline{
    display:inline-flex; align-items:center; gap:5px; vertical-align:baseline;
    color:#8b95f7; font-weight:500;
  }
  .dc-inline svg{width:15px; height:15px; flex:none; position:relative; top:2px;}
""" + committee.CSS


def sub_list(items, depth=1):
    """Render a nested minutes list. Entries are a string, or a
    (string, [children]) pair -- the funding options go three levels deep."""
    out = []
    for it in items:
        if isinstance(it, tuple):
            head, kids = it
            out.append(f"<li>{head}{sub_list(kids, depth + 1)}</li>")
        else:
            out.append(f"<li>{it}</li>")
    return f'<ul class="lvl{depth}">' + "".join(out) + "</ul>"


def minutes_html(minutes):
    rows = []
    for head, subs in minutes:
        rows.append(f"          <li>{head}"
                    + (sub_list(subs) if subs else "") + "</li>")
    return "\n".join(rows)


def upcoming_html(rows):
    out = []
    for u in rows:
        out.append(f"""        <div class="next-card">
          <span class="next-kind">{u['kind']}</span>
          <span class="next-when">{u['when']}</span>
          <span class="next-cadence">{u['cadence']}</span>
        </div>""")
    return "\n".join(out)


agenda_html = "\n".join(f"          <li>{a}</li>" for a in AGENDA)
seats = committee.seats_html()
archive_html = "\n".join(ARCHIVED)
arch_count = f"{len(ARCHIVED)} past event{'' if len(ARCHIVED) == 1 else 's'}"

MAIN = f"""<main>
  <div class="wrap">
    <div class="ann-head">
      <h1>Announcements</h1>
      <p>What's happening on the Chattanooga mesh &mdash; meetings, rollouts,
        and what's changed lately.</p>
    </div>

    <div class="meet">
      <div class="meet-bar">
        <span class="meet-pin">Today</span>
        <h2>Battlefield Races &mdash; operator brief</h2>
      </div>
      <div class="meet-body race">
        <div class="race-alert">
          <p class="alert-head">Aid station numbers &mdash; read this first</p>
          <p>Use the <strong>official numbers below</strong>, from the race
            packet. An earlier ChattaMesh chart numbered the stations
            differently and only AS1 matched. Net Control, the medics and race
            officials all work from the official numbering, so a message
            prefixed with the wrong number sends help to the wrong place.</p>
        </div>

        <table class="as-table">
          <tr><th>Station</th><th>Where</th><th>Mile</th></tr>
          <tr><td class="n">1</td><td>Lafayette Rd at the Lap 2 start</td><td class="mi">2 &middot; 11 &middot; 24</td></tr>
          <tr><td class="n">2</td><td>Brotherton Rd junction</td><td class="mi">4 &middot; 15</td></tr>
          <tr><td class="n">3</td><td>South loop, Lafayette Rd</td><td class="mi">9 &middot; 21</td></tr>
          <tr><td class="n">4</td><td>Near Wilder Tower</td><td class="mi">23</td></tr>
          <tr><td class="n">5</td><td>The 13.1 spur off Lafayette Rd</td><td class="mi">13 &middot; 14</td></tr>
          <tr><td class="n">6</td><td>Jays Mill Rd</td><td class="mi">17 &middot; 18</td></tr>
        </table>
        <p>The map marks a point on Jays Mill Rd near mile 19 as
          <strong>&ldquo;Not an Aid Station&rdquo;</strong> &mdash; it looks
          like one and isn&rsquo;t. The half marathon runs the inner loop only,
          so it does not pass stations 5 or 6.</p>

        <div class="race-maps">
          <div>
            <a href="images/announcements/course-marathon-full.webp" target="_blank" rel="noopener">
              <img class="race-chart" src="images/announcements/course-marathon.webp"
                   width="1200" height="1553" decoding="async"
                   alt="Official marathon course map: two laps from the Barnhardt Circle
                        start/finish, with the six numbered aid stations, mile markers and
                        portalets marked."></a>
            <p class="chart-note">Marathon &mdash; tap for full size</p>
          </div>
          <div>
            <a href="images/announcements/course-half-full.webp" target="_blank" rel="noopener">
              <img class="race-chart" src="images/announcements/course-half.webp"
                   width="1200" height="1553" decoding="async"
                   alt="Official half marathon course map: one lap of the inner loop with
                        four aid stations and mile markers."></a>
            <p class="chart-note">Half marathon &mdash; tap for full size</p>
          </div>
        </div>

        <p>ChattaMesh is running MeshCore alongside <strong>Catoosa/Walker
          ARES</strong>. Every post is a mesh operator paired with a ham &mdash;
          <strong>no ham licence is needed to run mesh</strong>.</p>

        <p class="fc-head">Race day times</p>
        <div class="race-when">
          <div><span class="k">Roads close</span><span class="v">5:30 AM &ndash; 2:00 PM</span></div>
          <div><span class="k">Marathon &amp; half</span><span class="v">7:30 AM</span></div>
          <div><span class="k">Wheelchair half</span><span class="v">7:27 AM</span></div>
          <div><span class="k">5K</span><span class="v">8:00 AM</span></div>
          <div><span class="k">Jr Marathon</span><span class="v">10:00 AM</span></div>
          <div><span class="k">Course closes</span><span class="v">2:00 PM</span></div>
        </div>
        <p>Roads into Barnhardt Circle close at <strong>5:30 AM</strong> and
          barricades go up from 4:30. <strong>You need an official race vehicle
          pass to get through &mdash; contact Xach (KR4OWY, Pige0n) for
          one</strong>, and sort it before you set off rather than at the
          barricade. Packet pick-up runs 6:00&ndash;7:00. Every station sends a
          test message at 7:00.</p>

        <p class="fc-head">What you&rsquo;ll be doing</p>
        <ul>
          <li>Pair up with your ham and duplicate their voice traffic on the mesh</li>
          <li>Relay Net Control, EMA and medic traffic back to them</li>
          <li>Log the time and text of everything you send or receive</li>
          <li>Send <strong>SWEEP</strong> when the last runner passes, and stay
            until Net Control releases you</li>
        </ul>
        <p>Messages go out as <strong>station &middot; category &middot; bib
          number &middot; what&rsquo;s happening</strong> &mdash; for example
          <strong>AS2 MED Bib 1234 ankle injury, needs transport</strong>.
          Categories are MED, SUPPLY, STATUS and SWEEP. Bib numbers only, never
          runner names. Life-safety calls still go by voice and 911 first; the
          mesh is the backup and the written record.</p>

        <p class="fc-head">What to bring</p>
        <ul>
          <li>A charged MeshCore companion with its antenna, and your phone with
            the MeshCore app</li>
          <li>Power bank and cables &mdash; the course is supported until 2:00 PM</li>
          <li>Folding chair, water, snacks, notepad and pen</li>
          <li>Layers and rain gear; it&rsquo;s in the low 40s at the start</li>
        </ul>
        <p>The event channel key is shared by QR code at check-in, so
          there&rsquo;s nothing to set up beforehand.</p>

        <div class="panel">
          <p class="panel-head">On the day</p>
          <p>Updates go out on the <a href="{DISCORD}" target="_blank"
            rel="noopener">ChattaMesh Discord</a>. Questions to Xach (KR4OWY)
            for ChattaMesh, or Max (N4NWD), Emergency Coordinator for
            Catoosa/Walker ARES. Times and aid station numbers on this page come
            from the official 2026 race packet.</p>
        </div>
      </div>
    </div>
    <div class="meet">
      <div class="meet-bar">
        <span class="meet-pin">Now official</span>
        <h2>Mesh Fund Committee</h2>
      </div>
      <div class="meet-body fundcom">
        <p class="draft-note">The committee is seated and the pool is open.
          This is no longer a draft.</p>

        <p class="fc-head">The pool is live</p>
        <div class="pool">
          <img src="{committee.PAYPAL_QR}" width="564" height="564"
               alt="QR code linking to the ChattaMesh PayPal Pool."
               loading="lazy" decoding="async">
          <div class="pool-body">
            <p>Donations go to the ChattaMesh PayPal Pool, held by
              <strong>{committee.HOLDER}</strong>. Scan the code or use the
              link &mdash; the stewards have access to the account.</p>
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
        <p>If you have a concern about a specific steward, raise it publicly
          in <code>#funding</code> on {DISCORD_INLINE}.</p>

        <p class="fc-head">Transparency</p>
        <p>This site and the Discord will both keep a public log of the current
          pool balance and every purchase made from it. The
          <a href="funding.html">funding page</a> is where that log lives.</p>

        <div class="panel">
          <p class="panel-head">Questions</p>
          <p>Anything to raise about the fund? <code>#funding</code> on the
            Discord, or bring it to the monthly meeting.</p>
        </div>
      </div>
    </div>

    <div class="meet">
      <div class="meet-bar">
        <span class="meet-pin">Next meetings</span>
        <h2>Monthly on Discord, 3rd Wednesday</h2>
      </div>
      <div class="meet-body fundcom">
        <div class="next-grid">
{upcoming_html(UPCOMING)}
        </div>
        <p class="fc-head">On the agenda</p>
        <ul>
{agenda_html}
        </ul>
        <p class="next-note">The Discord meeting is the 3rd Wednesday of every
          month at 7:00 PM. In-person meetings stay quarterly; those dates go
          out on Discord first.</p>
      </div>
    </div>

    <div class="meet past">
      <div class="meet-bar">
        <span class="meet-pin">Last meeting</span>
        <h2>{LAST['date_human']}</h2>
      </div>
      <div class="meet-body">
        <a class="live-frame" data-yt="{LAST['stream_id']}"
           href="https://www.youtube.com/watch?v={LAST['stream_id']}"
           target="_blank" rel="noopener"
           aria-label="Play the archived stream from {LAST['date_human']}">
          <span class="live-inner">
            <span class="vid-play"><svg viewBox="0 0 24 24" fill="currentColor"
              aria-hidden="true"><path d="M8 5.2v13.6L19 12Z"/></svg></span>
            <strong>Watch the archived stream</strong>
            <span>Plays from the beginning.</span>
          </span>
        </a>
        <p class="live-foot"><a href="{LAST['stream_url']}" target="_blank"
          rel="noopener">Open on YouTube</a> if you'd rather watch it there.</p>

        <p class="agenda-label">Thanks to</p>
        <ul class="thanks">
""" + "\n".join(f"          <li>{t}</li>" for t in LAST["thanks"]) + f"""
        </ul>

        <p class="agenda-label">Minutes</p>
        <ol class="agenda">
{minutes_html(LAST['minutes'])}
        </ol>

      </div>
    </div>

    <div class="ann-list">
""" + "\n".join(
    f'''      <div class="ann">
        <span class="ann-tag">{tag}</span>
        <h3>{title}</h3>{body.rstrip()}
      </div>''' for tag, title, body in ITEMS
# f-string: this trailing chunk carries {arch_count} and {archive_html}. It was
# a plain string before the archive went in, so both rendered as literal braces.
) + f"""
    </div>

    <details class="arch">
      <summary>
        <span class="arch-icon">&#9656;</span>
        <span class="arch-label">Archived Events</span>
        <span class="arch-sub">{arch_count}</span>
      </summary>
      <div class="arch-body">
{archive_html}
      </div>
    </details>
  </div>
</main>"""


shell = open(os.path.join(PUB, "about.html"), encoding="utf-8").read()

i = shell.index("  .about-col{max-width:60ch;}")
tail = "  .btn-discord:hover{background:#6c75f5; text-decoration:none;}\n"
j = shell.index(tail) + len(tail)
page = shell[:i] + CSS.strip("\n") + "\n" + shell[j:]

m = re.search(r"<main>.*?</main>", page, re.S)
assert m, "main block"
page = page[:m.start()] + MAIN + page[m.end():]

page = page.replace('<a href="about.html" class="active">About</a>',
                    '<a href="about.html">About</a>')
page = page.replace('<a href="announcements.html">Announcements</a>',
                    '<a href="announcements.html" class="active">Announcements</a>')

page = re.sub(r"<!-- seo:start -->.*?<!-- seo:end -->\n?", "", page, flags=re.S)
page = re.sub(r"<title>.*?</title>", "<title>Announcements</title>", page, flags=re.S)

SCRIPT = '\n<script src="js/yt.js" defer></script>\n'
assert page.count("</body>") == 1, "body close"
page = page.replace("</body>", SCRIPT + "</body>")

open(os.path.join(PUB, "announcements.html"), "w", encoding="utf-8").write(page)
print(f"announcements.html built ({len(page):,} bytes, "
      f"{len(ITEMS)} items + pinned meeting)")
