#!/usr/bin/env python3
"""ChattaMe.sh v1.3 -- build public/hardware.html from the expanded REV1.3 doc.

Regenerates the page wholesale off the About shell, so it always picks up the
current nav, footer, background and token block. Re-runnable: seo.py owns the
head fence and is stripped here before it writes a fresh one.
"""
import os
import re

PUB = "public"


def read(p):
    return open(os.path.join(PUB, p), encoding="utf-8").read()


# ---------------------------------------------------------------------- CSS

HW_CSS = """
  /* ===== HARDWARE ===== */
  .hw-head{max-width:64ch; margin-bottom:44px;}
  .hw-head h1{font-size:clamp(2rem, 5vw, 2.9rem); line-height:1.05; margin-bottom:16px;}
  .hw-head p{color:var(--muted); font-size:1.05rem; margin-bottom:12px;}

  .hw-section{margin-bottom:60px; scroll-margin-top:76px;}
  .hw-section > h2{font-size:1.5rem; margin-bottom:6px; display:flex; align-items:center; gap:12px;}
  .hw-section > h2::after{content:''; flex:1; height:1px; background:var(--line-soft);}
  .hw-section > .hw-note{color:var(--muted-2); font-size:0.92rem; margin-bottom:22px;}

  .hw-sub{
    font-family:'JetBrains Mono', monospace; font-size:0.72rem;
    letter-spacing:0.14em; text-transform:uppercase; color:var(--muted-2);
    margin:30px 0 14px;
  }

  /* max track width keeps a 2-item row (Repeaters) from stretching each
     card to half the page and blowing the 16:10 shot up with it */
  .hw-grid{display:grid; gap:16px; grid-template-columns:repeat(auto-fit, minmax(232px, 320px));}
  .hw-card{
    background:var(--panel); border:1px solid var(--line-soft);
    border-radius:var(--radius); overflow:hidden;
    display:flex; flex-direction:column;
  }

  /* Product shot slot. The placeholder sits underneath; a real photo covers it,
     and a missing one removes the <img> so the placeholder shows through. */
  .hw-shot{
    position:relative; aspect-ratio:16/10; max-height:200px; background:var(--panel-2);
    border-bottom:1px solid var(--line-soft);
    display:flex; align-items:center; justify-content:center;
  }
  .hw-shot .ph{width:30px; height:30px; color:var(--line); flex:none;}
  .hw-shot img{position:absolute; inset:0; width:100%; height:100%; object-fit:cover;}
  .hw-shot.has-shot .ph{visibility:hidden;}

  .hw-body{padding:16px 18px 18px; display:flex; flex-direction:column; gap:9px; flex:1;}
  .hw-card h3{font-size:1rem; margin:0; line-height:1.3;}
  .hw-card p{color:var(--muted); font-size:0.89rem; margin:0; line-height:1.6;}

  .hw-chips{display:flex; flex-wrap:wrap; gap:6px;}
  .chip{
    font-family:'JetBrains Mono', monospace; font-size:0.66rem;
    letter-spacing:0.08em; text-transform:uppercase;
    padding:3px 8px; border-radius:3px; border:1px solid var(--line);
    color:var(--muted-2); background:var(--panel-2);
  }
  .chip-conn{color:#7fa5e8; border-color:#2f4a7d; background:rgba(42,99,200,0.12);}

  .hw-specs{
    display:flex; flex-direction:column; gap:4px;
    font-size:0.8rem; color:var(--muted-2);
    border-top:1px solid var(--line-soft); padding-top:9px;
  }
  .hw-specs div{display:flex; gap:8px;}
  .hw-specs .k{
    font-family:'JetBrains Mono', monospace; font-size:0.68rem;
    letter-spacing:0.08em; text-transform:uppercase; color:var(--muted-2);
    flex:none; min-width:74px; padding-top:1px;
  }
  .hw-specs .v{color:var(--muted);}

  .hw-foot{margin-top:auto; padding-top:11px;}
  .hw-buy{
    font-family:'Space Grotesk', sans-serif; font-size:0.83rem; font-weight:600;
    background:var(--signal); color:#fff; border-radius:6px; padding:9px 15px;
    display:inline-flex; align-items:center; gap:8px;
    transition:background .15s ease, transform .1s ease;
  }
  .hw-buy:hover{background:#8385ee; color:#fff; text-decoration:none;}
  .hw-buy:active{transform:translateY(1px);}
  .hw-buy svg{width:15px; height:15px; flex:none;}
  .hw-search{
    font-family:'JetBrains Mono', monospace; font-size:0.74rem;
    color:var(--muted-2); line-height:1.55; display:block;
  }
  .hw-search em{color:var(--muted); font-style:normal;}

  .hw-callout{
    border-left:3px solid var(--rose); background:var(--panel-2);
    padding:13px 16px; border-radius:0 var(--radius) var(--radius) 0;
    color:var(--muted); font-size:0.9rem; line-height:1.6; margin:0 0 16px;
  }
  .hw-callout strong{color:var(--text);}
  .hw-callout.info{border-left-color:var(--bridge-blue);}
  .hw-callout a{color:var(--signal);}

  .conn-table{width:100%; border-collapse:collapse; font-size:0.89rem;}
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
    white-space:nowrap; font-size:0.83rem;
  }
  .conn-table td ul{margin:0; padding-left:16px;}
  .conn-table td li{margin:0 0 3px;}
  .conn-wrap{
    background:var(--panel); border:1px solid var(--line-soft);
    border-radius:var(--radius); overflow-x:auto;
  }
"""

CART = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        '<path d="M6 6h15l-1.6 8.4a2 2 0 0 1-2 1.6H9.2a2 2 0 0 1-2-1.6L5.4 3.6A1 1 0 0 0 4.4 3H2"/>'
        '<circle cx="10" cy="20" r="1.4"/><circle cx="18" cy="20" r="1.4"/></svg>')

PH = ('<svg class="ph" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
      'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" '
      'aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"/>'
      '<circle cx="9" cy="10" r="1.6"/><path d="m3 16 5-4 4 3 3-2 6 5"/></svg>')


def card(name, slug, alt, chips=(), specs=(), desc="", link=None,
         link_text="Buy Now", search=None):
    """One product card. Any of the optional blocks can be dropped."""
    ch = ""
    if chips:
        ch = ('\n          <div class="hw-chips">'
              + "".join(f'<span class="{c}">{t}</span>' for c, t in chips)
              + "</div>")
    sp = ""
    if specs:
        sp = ('\n          <div class="hw-specs">'
              + "".join(f'<div><span class="k">{k}</span>'
                        f'<span class="v">{v}</span></div>' for k, v in specs)
              + "</div>")
    ds = f'\n          <p>{desc}</p>' if desc else ""
    ft = ""
    if link:
        ft = (f'\n          <div class="hw-foot"><a class="hw-buy" href="{link}" '
              f'target="_blank" rel="noopener">{CART} {link_text}</a></div>')
    elif search:
        ft = f'\n          <div class="hw-foot"><span class="hw-search">{search}</span></div>'

    return f"""        <div class="hw-card">
          <div class="hw-shot">{PH}<img src="images/hardware/{slug}.webp" alt="{alt}" loading="lazy" onload="this.parentNode.classList.add('has-shot');" onerror="this.remove();"></div>
          <div class="hw-body">
          <h3>{name}</h3>{ch}{sp}{ds}{ft}
          </div>
        </div>"""


def grid(cards):
    return '      <div class="hw-grid">\n' + "\n".join(cards) + "\n      </div>"


CONN = "chip chip-conn"

# ------------------------------------------------------------- companions

companions = grid([
    card("Seeed T1000-E", "t1000e", "Seeed SenseCAP Card Tracker T1000-E",
         chips=[(CONN, "Internal")],
         specs=[("Battery", "700 mAh internal, non-replaceable")],
         desc="Card-style companion. Good to throw in a backpack or your pocket.",
         link="https://www.seeed.cc/product/sensecap-card-tracker-t1000-e-for-meshtastic"),

    card("WisMesh TAG", "wismesh-tag", "RAKwireless WisMesh TAG card-sized node",
         chips=[(CONN, "Internal")],
         specs=[("Battery", "1000 mAh internal, non-replaceable")],
         desc="Card-style companion. Same idea as the T1000-E, with a bigger "
              "battery and a real button.",
         link="https://store.rokland.com/products/wismesh-tag-from-rakwireless-mokosmart-meshtastic-compatible-card-sized-node-us915-mhz"),

    card("Wio Tracker L1 Pro", "wio-l1-pro", "Seeed Wio Tracker L1 Pro",
         chips=[(CONN, "RP-SMA")],
         specs=[("Battery", "2000 mAh internal, rechargeable")],
         desc="Great little companion for everyday use. Much better battery life "
              "than the card-style ones, and it ships assembled.",
         link="https://www.seeedstudio.com/Wio-Tracker-L1-Pro-p-6454.html"),

    card("GAT562 30s Kit", "gat562-30s",
         "GAT562 30s Kit MeshCore board with OLED and GPS",
         chips=[(CONN, "SMA")],
         specs=[("Output", "30 dBm")],
         desc="Far more transmit power than a typical companion. Comes as an "
              "open board with OLED and GPS rather than a sealed handheld.",
         link="https://shop.mtoolstec.com/product/gat562-30s-kit-30dbm-mesh-device"),

    card("LILYGO T-ECHO", "t-echo", "LILYGO T-ECHO e-paper companion node",
         chips=[(CONN, "SMA")],
         desc="E-paper companion in a small sealed case. The display draws "
              "nothing to hold an image and stays readable in direct sun.",
         link="https://lilygo.cc/products/t-echo-meshtastic"),

    card("Heltec WiFi LoRa 32 V4-R8", "heltec-v4-r8",
         "Heltec WiFi LoRa 32 V4-R8 Expansion Kit Gen 2",
         chips=[(CONN, "SMA")],
         specs=[("Battery", "user supplied &mdash; one flat-top 18650")],
         desc="Favorite touch screen device, and it comes with Snake.",
         link="https://heltec.org/project/v4-r8-ex/"),
])

# --------------------------------------------------------------- repeaters

repeaters = grid([
    card("Seeed SenseCAP Solar (P1-Pro)", "sensecap-p1-pro",
         "Seeed SenseCAP Solar Node P1-Pro",
         chips=[(CONN, "RP-SMA")],
         specs=[("Battery", "4 &times; 3350 mAh 18650 = 13,400 mAh"),
                ("Solar", "5 W")],
         desc="All-in-one, ready-to-flash repeater. Reliable for neighborhood "
              "and gap filling. Worth upgrading the antenna. Not for use on a "
              "highsite.",
         link="https://www.seeedstudio.com/SenseCAP-Solar-Node-P1-Pro-for-Meshtastic-LoRa-p-6412.html"),

    card("Ka0sComTech Tree Repeater", "kaos-tree-repeater",
         "Ka0sComTech tree repeater hanging from a pine branch",
         specs=[("Battery", "10,000 mAh of 21700"),
                ("Solar", "600 mA"),
                ("Board", "Heltec T114")],
         desc="Preassembled MeshCore repeater &mdash; hanging mount, weather "
              "resistant. Made by a Georgia local mesh user. Show some support "
              "for our community: the Buy Now link applies a CHATTAMESH coupon "
              "automatically at checkout.",
         link="https://www.etsy.com/shop/Ka0sComTech?etsrc=sdt&amp;coupon=CHATTAMESH"),

    card("PeakMesh Ultimate", "peakmesh-ultimate",
         "PeakMesh Ultimate solar mesh node",
         chips=[(CONN, "SMA")],
         specs=[("Battery", "2 &times; Samsung 21700, ~10,000 mAh"),
                ("Solar", "2 &times; 1 W ETFE (~2 W)")],
         desc="Hand-built solar nodes out of Merritt Island, FL. Wall, pole or "
              "gutter mount. Ships flashed with Meshtastic, so ask in the order "
              "notes for MeshCore instead.",
         link="https://www.etsy.com/listing/1776412240/peakmesh-ultimate-solar-meshtastic-radio"),
])

# ---------------------------------------------------------------- antennas

ant_sma = grid([
    card("Muzi Works Whip", "muzi-whip", "Muzi Works 17 cm 915 MHz whip antenna",
         chips=[(CONN, "SMA")],
         specs=[("Length", "17 cm")],
         desc="One of the most common companion whips and popular for a reason.",
         link="https://muzi.works/products/4-pack-whip-antenna-17cm-915mhz"),

    card("Stock SenseCAP Solar antenna", "sensecap-antenna",
         "Stock 2 dBi dipole antenna from the SenseCAP Solar node",
         chips=[(CONN, "RP-SMA")],
         specs=[("Gain", "2 dBi dipole")],
         desc="The antenna that comes with the SenseCAP Solar. It does fine for "
              "a residential rooftop antenna. Not sold separately &mdash; the "
              "link is the node it ships inside of.",
         link="https://www.seeedstudio.com/SenseCAP-Solar-Node-P1-Pro-for-Meshtastic-LoRa-p-6412.html",
         link_text="Buy the node"),

    card("Atlavox Whip", "atlavox-whip", "Atlavox 915 MHz whip antenna",
         chips=[(CONN, "SMA / RP-SMA")],
         specs=[("Length", "7.8&Prime;"), ("Gain", "2.5 dBi peak")],
         desc="Another common whip, also popular for a reason. Order the RP-SMA "
              "for a Wio Tracker upgrade!",
         link="https://atlavox.com/collections/antennas"),
])

ant_n = grid([
    card("Alfa 5 dBi", "alfa-5dbi", "Alfa AOA-915-5ACM outdoor omni antenna",
         chips=[(CONN, "N-male")],
         specs=[("Model", "AOA-915-5ACM"), ("Band", "902&ndash;928 MHz"),
                ("Size", "22 &times; 180 mm, 81.5 g")],
         desc="Good for small-footprint repeater builds &mdash; neighborhood and "
              "downtown gap coverage.",
         link="https://muzi.works/products/alfa-outdoor-antenna"),

    card("Rokland 5.8 dBi", "rokland-5-8dbi",
         "Rokland 5.8 dBi N-male fiberglass omni antenna",
         chips=[(CONN, "N-male")],
         specs=[("Length", "32&Prime; fiberglass"),
                ("Beamwidth", "35&deg; vertical")],
         desc="Your first &ldquo;big&rdquo; upgrade &mdash; going to make you "
              "feel like you're doing something.",
         link="https://store.rokland.com/products/5-8-dbi-n-male-omni-outdoor-915-mhz-antenna-large-profile-32-height-for-helium-rak-miner-2-nebra-indoor-bobcat"),

    card("Rokland 8 dBi", "rokland-8dbi",
         "Rokland 8 dBi low profile fiberglass omni antenna",
         chips=[(CONN, "N-female")],
         specs=[("Length", "25.2&Prime; low profile"),
                ("Beamwidth", "25&deg; vertical")],
         desc="No tests to back it up, but Pige0n hasn't found any great "
              "difference between this and the 5.8.",
         link="https://store.rokland.com/products/8-dbi-outdoor-fiberglass-antenna-us-868-915-mhz-for-meshtastic-helium-iot"),

    card("Rokland 10 dBi Backcountry", "rokland-10dbi",
         "Rokland 10 dBi Backcountry N-male omni antenna",
         chips=[(CONN, "N-male")],
         specs=[("Length", "45&Prime;"), ("Beamwidth", "12&deg; vertical")],
         desc="Budget-friendly antenna for highsite and infrastructure use. Be "
              "warned: it's 45 inches long.",
         link="https://store.rokland.com/products/10-dbi-backcountry-n-male-omni-outdoor-helium-915-mhz-antenna-48-for-rak-miner-2-nebra-indoor-bobcat-hotspots"),
])

# --------------------------------------------------------------- enclosures

enclosures = grid([
    card("PVC &mdash; screw cover", "pvc-screw", "PVC NEMA 4X junction box with screw cover",
         desc="Cheapest weatherproof option. Screw cover means four screws every "
              "time you need to get in, so pick this when you expect to set it "
              "and forget it.",
         search='Search <em>&ldquo;PVC junction box screw cover NEMA 4X 6x6x4&rdquo;</em> '
                '&mdash; Cantex and Carlon are the usual brands, in any big-box '
                'electrical aisle.'),

    card("PVC &mdash; hinge cover", "pvc-hinge", "Hinged-cover PVC weatherproof enclosure",
         desc="Same enclosure, hinged lid. Worth the small upcharge on anything "
              "you'll be opening to swap batteries or reflash. Ships with a "
              "mounting plate, brackets and cable glands.",
         link="https://www.amazon.com/dp/B0BZHGCBTH"),

    card("Aluminum &mdash; hinge cover", "alu-hinge", "Cast aluminum IP67 enclosure with hinged lid",
         desc="Step up for highsite and infrastructure builds. Rigid, UV-proof, "
              "and won't go chalky after a few Tennessee summers. Remember the "
              "metal is an RF barrier &mdash; the antenna has to be outside it.",
         search='Search <em>&ldquo;cast aluminum enclosure hinged IP67&rdquo;</em>'),

    card("Aluminum &mdash; Nebra", "alu-nebra", "Nebra-style cast aluminum enclosure",
         desc="Nebra-style extruded aluminum case with end plates. Popular for "
              "the style, the threaded holes, and the fact that the enclosure "
              "itself is a heatsink to keep those batteries cool!",
         link="https://www.amazon.com/dp/B0G8HN1Y9B"),
])

# ------------------------------------------------------------------- boards

boards = grid([
    card("RAK Standard", "rak-standard", "RAK WisBlock Meshtastic Starter Kit",
         desc="RAK19007 base + RAK4631 core. Good for residential roof repeaters "
              "&mdash; &ldquo;neighborhood&rdquo; coverage.",
         link="https://store.rakwireless.com/products/wisblock-meshtastic-starter-kit-new"),

    card("RAK High Power Booster", "rak-booster",
         "RAK WisMesh High Power Booster starter kit",
         desc="RAK3401 core + RAK13302 booster + RAK19007 base. Better for "
              "residential roof repeaters &mdash; &ldquo;whole side of town&rdquo; "
              "coverage, with built-in filters. Formerly sold as the "
              "&ldquo;1W&rdquo;.",
         link="https://store.rokland.com/products/coming-soon-wismesh-1w-booster-starter-kit-with-nrf52840-sx1262-and-sky66122-pa-for-extended-meshtastic-range"),

    card("Heltec V3", "heltec-v3", "Heltec WiFi LoRa 32 V3 board",
         desc="The V4's predecessor and still everywhere. Same footprint, "
              "cheaper, and the one most guides are written against.",
         link="https://www.amazon.com/dp/B0GQLBS3MM"),

    card("Heltec V4", "heltec-v4", "Heltec WiFi LoRa 32 V4 board",
         desc="ESP32 board, same footprint and pinout as the V3. Cheap, easy to "
              "find and well supported. Draws far more at idle than the RAK "
              "boards, so it suits a mains-powered node better than a solar "
              "repeater.",
         link="https://heltec.org/project/wifi-lora-32-v4/"),

])

# ---------------------------------------------------------------- batteries

batteries = grid([
    card("Li-ion 18650", "18650", "Li-ion 18650 cells",
         specs=[("Cells", "Samsung 30Q or 35E, Panasonic NCR18650GA")],
         desc="Standard option. Solid."),

    card("Li-ion 21700", "21700", "Li-ion 21700 cells",
         specs=[("Cells", "Samsung 40T, Molicel P42A")],
         desc="Upgraded option. Very solid, higher capacity."),

    card("Li-ion pouch cell", "pouch", "Li-ion pouch cell",
         desc="Spicy pillows. We would advise against those."),
])

# ------------------------------------------------------------ solar panels

solar_panels = grid([
    card("SoShine 12 W panel", "soshine-12w", "SoShine 12 W solar panel with mount",
         specs=[("Output", "12 W")],
         desc="Wall or pole mount with the bracket included. Plenty of headroom "
              "for a repeater that has to ride out a cloudy week.",
         link="https://www.amazon.com/dp/B0GCH9894Z"),
])

# ---------------------------------------------------------- solar managers

solar_managers = grid([
    card("Waveshare Solar Power Manager", "waveshare-manager",
         "Waveshare solar power manager board",
         desc="Takes the panel in, charges the pack, and hands your board a "
              "regulated 5 V. Screw terminals for the panel and battery, USB-C "
              "and a barrel jack, and a four-LED charge gauge.",
         link="https://www.amazon.com/dp/B0CT2ZBML9"),
])

# --------------------------------------------------------------- uhf/vhf/hf

uhf_vhf_hf = grid([
    card("ChattRadio", "chattradio", "ChattRadio, Chattanooga Tennessee",
         desc="Your one-stop shop for all things UHF/VHF/HF. Extremely "
              "knowledgeable, helpful people selling top-notch service and "
              "equipment. They're starting to carry some MeshCore gear &mdash; "
              "your support will add more!",
         link="https://www.chattradio.com/",
         link_text="Visit ChattRadio"),
])

# --------------------------------------------------------------------- coax

COAX = [
    ("IPEX &rarr; SMA", ["Board to SMA antenna", "Board to filter"]),
    ("IPEX &rarr; RP-SMA", ["Board to RP-SMA antenna"]),
    ("IPEX &rarr; N-Type", ["Board to N-Type antenna"]),
    ("SMA &rarr; SMA", ["Boards <em>with built-in SMA output</em> to antenna",
                        "Boards <em>with built-in SMA output</em> to filter",
                        "Filter to antenna"]),
    ("SMA &rarr; RP-SMA", ["SMA output to RP-SMA antenna"]),
    ("RP-SMA &rarr; SMA", ["RP-SMA output to SMA antenna",
                           "SenseCAP Solar to SMA antenna"]),
    ("SMA &rarr; N-Type female", ["SMA output to N-Type antenna",
                                  "SMA filter output to antenna"]),
    ("RP-SMA &rarr; N-Type female", ["RP-SMA output to N-Type antenna"]),
    ("N-Type male &rarr; N-Type female",
     ["N-Type antennas mounted away from the enclosure"]),
]

coax_rows = "\n".join(
    f'            <tr><td class="pair">{p}</td><td><ul>'
    + "".join(f"<li>{u}</li>" for u in uses) + "</ul></td></tr>"
    for p, uses in COAX
)

# --------------------------------------------------------------------- main

HW_MAIN = f"""<main>
  <div class="wrap">
    <div class="hw-head">
      <h1>Hardware</h1>
      <p>Popular hardware sourced from asking the #Public channel on the mesh!
         Opinions are the community's, prices aren't &mdash; check current
         listings before you order. You may find these cheaper elsewhere!</p>
      <p>More recommendations and discussion in the
         <a href="https://discord.gg/XF354A3e9m" target="_blank" rel="noopener">ChattaMesh
         Discord</a>.</p>
    </div>

    <section class="hw-section" id="companions">
      <h2>Companions</h2>
      <p class="hw-note">Handheld and pocket nodes &mdash; what you carry.</p>
{companions}
    </section>

    <section class="hw-section" id="repeaters">
      <h2>Repeaters</h2>
      <p class="hw-note">Pre-built and ready to flash. If you'd rather build your
         own, see <a href="#diy">DIY Supplies</a>.</p>
{repeaters}
    </section>

    <section class="hw-section" id="antennas">
      <h2>Antennas</h2>
      <p class="hw-note">The single biggest thing you can change. Match the
         connector to your board before you order &mdash; and remember gain is
         bought by flattening the pattern, so the biggest number isn't always the
         right answer.</p>

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
      <div class="hw-callout"><strong>Only buy cells from a trusted source.</strong>
        We're deliberately not linking Amazon for cells &mdash; counterfeit and
        rewrapped ones are rampant, and a fake cell in a sealed box on someone's
        roof is the one failure mode in this whole page that starts a fire. Try
        18650batterystore.com, illumn.com, or liionwholesale.com.</div>
{batteries}

      <p class="hw-sub">Solar panels</p>
{solar_panels}

      <p class="hw-sub">Solar managers</p>
      <div class="hw-callout">Some people open the backing on a panel and pull
        the voltage regulator out. Without it the panel puts out around 16 V.
        <strong>Check what your board or solar manager can actually accept
        before you do that</strong> &mdash; the regulator is the only thing
        standing between a bright day and a dead board.</div>
{solar_managers}

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

    <section class="hw-section" id="uhf-vhf-hf">
      <h2>UHF / VHF / HF</h2>
      <p class="hw-note">Off the mesh and onto the ham bands &mdash; local
         people worth knowing.</p>
{uhf_vhf_hf}
    </section>
  </div>
</main>"""

# ------------------------------------------------------------------- assemble

shell = read("about.html")

A, B = "  /* ===== HARDWARE ===== */", "  .btn-discord:hover{background:#6c75f5; text-decoration:none;}\n"
if A in shell:
    raise SystemExit("about.html unexpectedly carries hardware CSS")
i = shell.index("  .about-col{max-width:60ch;}")
j = shell.index(B) + len(B)
hw = shell[:i] + HW_CSS.strip("\n") + "\n" + shell[j:]

m = re.search(r"<main>.*?</main>", hw, re.S)
assert m, "main block"
hw = hw[:m.start()] + HW_MAIN + hw[m.end():]

hw = hw.replace('<a href="about.html" class="active">About</a>',
                '<a href="about.html">About</a>')
hw = hw.replace('class="nav-drop-btn" id="hwBtn"',
                'class="nav-drop-btn active" id="hwBtn"')

hw = re.sub(r"<!-- seo:start -->.*?<!-- seo:end -->\n?", "", hw, flags=re.S)
hw = re.sub(r"<title>.*?</title>", "<title>Hardware</title>", hw, flags=re.S)

open(os.path.join(PUB, "hardware.html"), "w", encoding="utf-8").write(hw)
print(f"hardware.html rebuilt ({len(hw):,} bytes)")

os.makedirs(os.path.join(PUB, "images", "hardware"), exist_ok=True)
slugs = sorted(set(re.findall(r"images/hardware/([\w-]+)\.webp", hw)))
print(f"{len(slugs)} product shot slots: {', '.join(slugs)}")
