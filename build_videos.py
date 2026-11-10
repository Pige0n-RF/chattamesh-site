#!/usr/bin/env python3
"""Build the three Videos pages off the About shell.

Like build_hardware.py, these are generated wholesale so they always pick up
the current nav, footer, background and token block. Add videos to the VIDEOS
dict below and re-run -- do not hand-edit the HTML.

Players are click-to-play facades handled by public/js/yt.js, which also
derives each thumbnail from the video id. A facade is a real link to YouTube
until clicked, so it still works with scripting off. The real
iframe swapped in on click. A YouTube iframe pulls roughly a megabyte and sets
cookies before anyone presses play, so a page of eight videos would cost eight
megabytes to load for a visitor who watches none.

The Meetings live player is a facade for a second reason. A static site cannot
tell whether a stream is running -- that needs the YouTube Data API and a key,
which cannot be hidden in static assets. Embedded raw, an idle channel renders
YouTube's own error panel and reads as a broken page. Behind a facade the
viewer opens the player deliberately, so "nothing is live right now" lands as
an answer rather than a fault.
"""
import os
import re

PUB = "public"
CHANNEL_ID = "UCaMYXY0MGVQ6HpgaP99y3BA"
YT_URL = "https://www.youtube.com/@ChattanoogaMesh"

# ---------------------------------------------------------------- content
# Each entry: (youtube_id, title, blurb). Leave a list empty and the page
# renders its empty state instead.
VIDEOS = {
    "welcome": [],
    "information": [],
    "meetings": [
        ("uWH2PoxXLX0", "ChattaMesh meeting — October 3, 2026",
         "Regions presentation, the FCC 500 kHz topic, funding options, and "
         "the move to quarterly in-person plus monthly Discord meetings."),
    ],
}

PAGES = {
    "welcome": dict(
        file="videos-welcome.html",
        # A featured playlist from someone else's channel. Embedding is the
        # sanctioned way to show it: the player carries their branding and the
        # view counts against their channel, not ours.
        playlist=dict(
            id="PLshzThxhw4O4WU_iZo3NmNZOv6KMrUuF9",
            title="MeshCore QuickStart",
            author="The Comms Channel",
            author_url="https://www.youtube.com/@The_Comms_Channel",
            count="9 videos",
            blurb="The clearest introduction to MeshCore we've found. Worth "
                  "watching before you flash anything &mdash; it covers what "
                  "the firmware is doing and why, not just which buttons to "
                  "press."),
        h1="Welcome",
        lede="New to the mesh? Start here. Getting a node on the air, the "
             "settings that matter, and what to expect once you're talking.",
        empty="The first welcome videos are being recorded now.",
        next_link=("Getting Started", "getting-started.html"),
        next_text="the written walkthrough covers the same ground today"),
    "information": dict(
        file="videos-information.html",
        playlist=dict(
            id="PLPB1CPS5mUOY",
            title="MeshCore Decoded",
            author="The Comms Channel",
            author_url="https://www.youtube.com/@The_Comms_Channel",
            blurb="A deeper dive into the MeshCore settings &mdash; what each "
                  "one means, what regions are, and how they fit together."),
        h1="Information",
        lede="Deeper instructional videos &mdash; region scoping, repeater "
             "siting, antennas, and the things that are easier shown than "
             "written.",
        empty="No instructional videos posted yet.",
        next_link=("Setup &amp; Information", "setup-information.html"),
        next_text="the reference pages cover this in writing"),
    "meetings": dict(
        file="videos-meetings.html",
        h1="Meetings",
        lede="We stream meetings live on YouTube and keep the recordings here "
             "afterwards.",
        empty="No other meeting recordings posted yet.",
        next_link=("Discord", "https://discord.gg/XF354A3e9m"),
        next_text="meeting times go out on Discord first"),
}

# ---------------------------------------------------------------------- CSS

CSS = """
  /* ===== VIDEOS ===== */
  .vid-head{max-width:64ch; margin-bottom:40px;}
  .vid-head h1{font-size:clamp(2rem, 5vw, 2.9rem); line-height:1.05; margin-bottom:16px;}
  .vid-head p{color:var(--muted); font-size:1.05rem;}

  .vid-grid{display:grid; gap:22px; grid-template-columns:repeat(auto-fit, minmax(310px, 1fr));}
  .vid-card{
    background:var(--panel); border:1px solid var(--line-soft);
    border-radius:var(--radius); overflow:hidden;
    display:flex; flex-direction:column;
  }
  .vid-body{padding:15px 17px 18px; display:flex; flex-direction:column; gap:7px;}
  .vid-card h3{font-size:1rem; margin:0; line-height:1.35;}
  .vid-card p{color:var(--muted); font-size:0.9rem; margin:0; line-height:1.6;}

  /* Facade: a link to YouTube until clicked, then the real player replaces
     it in place. Being a link means it still works without JS. */
  .vid-frame{
    position:relative; width:100%; aspect-ratio:16/9;
    background:var(--panel-2); border:0; padding:0; margin:0;
    display:block; cursor:pointer; overflow:hidden;
    border-bottom:1px solid var(--line-soft);
    text-decoration:none; color:inherit; -webkit-tap-highlight-color:transparent;
  }
  .vid-frame:hover{text-decoration:none;}
  .vid-frame img{
    position:absolute; inset:0; width:100%; height:100%;
    object-fit:cover; display:block;
  }
  .vid-frame iframe{position:absolute; inset:0; width:100%; height:100%; border:0;}
  .vid-play{
    position:absolute; left:50%; top:50%; transform:translate(-50%,-50%);
    width:62px; height:44px; border-radius:11px;
    background:rgba(110,112,230,0.92);
    display:flex; align-items:center; justify-content:center;
    transition:background .15s ease, transform .15s ease;
    pointer-events:none;
  }
  .vid-play svg{width:20px; height:20px; color:#fff;}
  .vid-frame:hover .vid-play{background:var(--signal); transform:translate(-50%,-50%) scale(1.06);}
  .vid-frame:focus-visible{outline:2px solid var(--signal); outline-offset:-2px;}

  /* ----- live panel on the Meetings page ----- */
  .live{
    background:var(--panel); border:1px solid var(--line);
    border-radius:var(--radius); overflow:hidden; margin-bottom:46px;
  }
  .live-bar{
    display:flex; align-items:center; gap:11px; flex-wrap:wrap;
    padding:13px 18px; border-bottom:1px solid var(--line-soft);
  }
  .live-dot{
    width:9px; height:9px; border-radius:50%; background:var(--amber);
    box-shadow:0 0 7px var(--amber); flex:none;
    animation:live-pulse 2.4s ease-in-out infinite;
  }
  @keyframes live-pulse{0%,100%{opacity:1;} 50%{opacity:0.3;}}
  @media (prefers-reduced-motion: reduce){ .live-dot{animation:none;} }
  .live-bar h2{font-size:1.05rem; margin:0;}
  .live-bar .live-note{color:var(--muted-2); font-size:0.85rem; margin-left:auto;}
  .live-frame{
    position:relative; width:100%; aspect-ratio:16/9;
    background:var(--panel-2); border:0; padding:0; margin:0;
    display:block; cursor:pointer; overflow:hidden;
    text-decoration:none; color:inherit; -webkit-tap-highlight-color:transparent;
  }
  .live-frame:hover{text-decoration:none;}
  .live-frame iframe{position:absolute; inset:0; width:100%; height:100%; border:0;}
  .live-inner{
    position:absolute; inset:0; display:flex; flex-direction:column;
    align-items:center; justify-content:center; gap:13px; padding:26px;
    text-align:center;
  }
  .live-inner .vid-play{position:static; transform:none;}
  .live-frame:hover .live-inner .vid-play{transform:scale(1.06);}
  .live-inner strong{color:var(--text); font-size:1.02rem; font-weight:600;}
  .live-inner span{color:var(--muted-2); font-size:0.88rem; max-width:44ch; line-height:1.6;}

  .feat{
    background:var(--panel); border:1px solid var(--line);
    border-radius:var(--radius); overflow:hidden; margin-bottom:46px;
  }
  .feat-bar{
    display:flex; align-items:baseline; gap:12px; flex-wrap:wrap;
    padding:14px 18px; border-bottom:1px solid var(--line-soft);
  }
  .feat-bar h2{font-size:1.05rem; margin:0;}
  .feat-by{color:var(--muted-2); font-size:0.88rem;}
  .feat-by a{color:var(--signal);}
  .feat-count{
    margin-left:auto; font-family:'JetBrains Mono', monospace;
    font-size:0.72rem; letter-spacing:0.1em; color:var(--muted-2);
  }

  .live-foot{
    padding:13px 18px; border-top:1px solid var(--line-soft);
    color:var(--muted-2); font-size:0.86rem; line-height:1.65; margin:0;
  }
  .live-foot em{color:var(--muted); font-style:normal;}
  .live-foot a{color:var(--signal);}

  .vid-empty{
    border:1px dashed var(--line); border-radius:var(--radius);
    padding:38px 26px; text-align:center; color:var(--muted-2); font-size:0.95rem;
  }
  .vid-empty p{margin:0 0 6px;}
  .vid-empty a{color:var(--signal);}

  .vid-foot{
    margin-top:44px; padding-top:22px; border-top:1px solid var(--line-soft);
    color:var(--muted-2); font-size:0.92rem;
  }
  .vid-foot a{color:var(--signal);}
"""

PLAY = ('<span class="vid-play"><svg viewBox="0 0 24 24" fill="currentColor" '
        'aria-hidden="true"><path d="M8 5.2v13.6L19 12Z"/></svg></span>')


def esc(t):
    return (t.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def video_card(vid, title, blurb):
    t = esc(title)
    return f"""      <div class="vid-card">
        <a class="vid-frame" data-yt="{vid}"
           href="https://www.youtube.com/watch?v={vid}"
           target="_blank" rel="noopener" aria-label="Play: {t}">
          {PLAY}
        </a>
        <div class="vid-body">
          <h3>{t}</h3>
          <p>{esc(blurb)}</p>
        </div>
      </div>"""


def check_playlist(pl, where):
    n = len(pl["id"])
    # 13 is in the list because of PLPB1CPS5mUOY (MeshCore Decoded), which looks
    # truncated next to the 34-char norm but was confirmed working by hand. The
    # length heuristic is a smell test, not a spec -- don't warn on a verified id.
    if n not in (13, 18, 24, 34):
        print(f"  !! {where}: playlist id {pl['id']!r} is {n} characters. "
              f"YouTube ids are normally 34 (or 18 for older lists), so this "
              f"one looks truncated -- the embed will show \"playlist does not "
              f"exist\". Paste the full list= value from the address bar.")


def playlist_block(pl):
    """Featured playlist, behind the same click-to-play facade as everything
    else. No thumbnail: there is no stable per-playlist image URL, and a
    branded panel beats hotlinking a first-video still that can change."""
    return f"""    <div class="feat">
      <div class="feat-bar">
        <h2>{esc(pl['title'])}</h2>
        <span class="feat-by">by <a href="{pl['author_url']}" target="_blank"
          rel="noopener">{esc(pl['author'])}</a></span>
        {f'<span class="feat-count">{esc(pl["count"])}</span>' if pl.get('count') else ''}
      </div>
      <a class="live-frame" data-list="{pl['id']}"
         href="https://www.youtube.com/playlist?list={pl['id']}"
         target="_blank" rel="noopener"
         aria-label="Play the {esc(pl['title'])} playlist">
        <span class="live-inner">
          {PLAY}
          <strong>Play the playlist</strong>
          <span>{pl['blurb']}</span>
        </span>
      </a>
      <p class="live-foot">Not ours &mdash; we just think it's the best starting
        point. <a href="https://www.youtube.com/playlist?list={pl['id']}"
        target="_blank" rel="noopener">Open on YouTube</a>.</p>
    </div>
"""


LIVE = f"""    <div class="live">
      <div class="live-bar">
        <span class="live-dot" aria-hidden="true"></span>
        <h2>Live stream</h2>
        <span class="live-note">Meetings appear here while they're running</span>
      </div>
      <a class="live-frame" data-live="{CHANNEL_ID}"
         href="{YT_URL}/live" target="_blank" rel="noopener"
         aria-label="Open the live meeting player">
        <span class="live-inner">
          {PLAY}
          <strong>Open the live player</strong>
          <span>If a meeting is running, it starts here.</span>
        </span>
      </a>
      <p class="live-foot">Not meeting time? The player will say
        <em>&ldquo;Video Play Configuration Error&rdquo;</em> &mdash; that is
        YouTube's way of saying nothing is live right now, not a fault on this
        page. You can also
        <a href="{YT_URL}/live" target="_blank" rel="noopener">watch on
        YouTube</a>, or check Discord for the next one.</p>
    </div>
"""

SCRIPT = '\n<script src="js/yt.js" defer></script>\n'


def build(key, shell):
    meta = PAGES[key]
    items = VIDEOS[key]

    if meta.get("playlist"):
        check_playlist(meta["playlist"], meta["file"])

    if items:
        body = ('    <div class="vid-grid">\n'
                + "\n".join(video_card(*v) for v in items) + "\n    </div>")
    else:
        body = (f'    <div class="vid-empty">\n      <p>{meta["empty"]}</p>\n'
                f'      <p>Everything we post lands on '
                f'<a href="{YT_URL}" target="_blank" rel="noopener">the YouTube '
                f'channel</a> first.</p>\n    </div>')

    label, href = meta["next_link"]
    ext = ' target="_blank" rel="noopener"' if href.startswith("http") else ""

    main = f"""<main>
  <div class="wrap">
    <div class="vid-head">
      <h1>{meta['h1']}</h1>
      <p>{meta['lede']}</p>
    </div>

{playlist_block(meta['playlist']) if meta.get('playlist') else ''}{LIVE if key == 'meetings' else ''}{body}

    <p class="vid-foot">In the meantime, <a href="{href}"{ext}>{label}</a>
      &mdash; {meta['next_text']}.</p>
  </div>
</main>"""

    # Swap the About-only rules for the video ones, exactly as the hardware
    # build does, so page-specific CSS does not leak between pages.
    i = shell.index("  .about-col{max-width:60ch;}")
    j = (shell.index("  .btn-discord:hover{background:#6c75f5; text-decoration:none;}\n")
         + len("  .btn-discord:hover{background:#6c75f5; text-decoration:none;}\n"))
    page = shell[:i] + CSS.strip("\n") + "\n" + shell[j:]

    m = re.search(r"<main>.*?</main>", page, re.S)
    assert m, "main block"
    page = page[:m.start()] + main + page[m.end():]

    page = page.replace('<a href="about.html" class="active">About</a>',
                        '<a href="about.html">About</a>')
    page = page.replace('class="nav-drop-btn tab-videos" id="vidBtn"',
                        'class="nav-drop-btn tab-videos active" id="vidBtn"')

    page = re.sub(r"<!-- seo:start -->.*?<!-- seo:end -->\n?", "", page, flags=re.S)
    page = re.sub(r"<title>.*?</title>", f"<title>{meta['h1']}</title>",
                  page, flags=re.S)
    assert page.count("</body>") == 1, "body close"
    page = page.replace("</body>", SCRIPT + "</body>")
    return page


shell = open(os.path.join(PUB, "about.html"), encoding="utf-8").read()
assert "vidBtn" in shell, "run patch_videos_nav.py first"

for key, meta in PAGES.items():
    out = build(key, shell)
    open(os.path.join(PUB, meta["file"]), "w", encoding="utf-8").write(out)
    n = len(VIDEOS[key])
    print(f"  {meta['file']:28s} {len(out):,} bytes  "
          f"({n} video{'' if n == 1 else 's'})")
