#!/usr/bin/env python3
"""REV2 edits to build_hardware.py: new cards, DIY subsections, UHF/VHF/HF.

Amazon URLs are reduced to their canonical /dp/<ASIN> form. The supplied links
carried `dib=` session blobs and `qid=` timestamps that go stale; the short form
is the permanent one and resolves to the same listing.
"""
import re

p = "build_hardware.py"
s = open(p, encoding="utf-8").read()

AMZ = "https://www.amazon.com/dp/"

# ------------------------------------------------ 1. companions: two new cards
anchor = '''    card("Heltec WiFi LoRa 32 V4-R8", "heltec-v4-r8",'''
new = '''    card("GAT562 30s Kit", "gat562-30s",
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

''' + anchor
assert s.count(anchor) == 1, "companions anchor"
s = s.replace(anchor, new)

# ------------------------------- 2. enclosures: real listings for two of them
old_hinge = '''    card("PVC &mdash; hinge cover", "pvc-hinge", "PVC NEMA 4X junction box with hinged cover",
         desc="Same enclosure, hinged lid. Worth the small upcharge on anything "
              "you'll be opening to swap batteries or reflash.",
         search='Search <em>&ldquo;PVC junction box hinged cover NEMA 4X&rdquo;</em>'),'''
new_hinge = f'''    card("PVC &mdash; hinge cover", "pvc-hinge", "Hinged-cover PVC weatherproof enclosure",
         desc="Same enclosure, hinged lid. Worth the small upcharge on anything "
              "you'll be opening to swap batteries or reflash. Ships with a "
              "mounting plate, brackets and cable glands.",
         link="{AMZ}B0BZHGCBTH"),'''
assert s.count(old_hinge) == 1, "pvc hinge card"
s = s.replace(old_hinge, new_hinge)

old_nebra = '''    card("Aluminum &mdash; Nebra", "alu-nebra", "Nebra-style extruded aluminum enclosure",
         desc="Nebra-style extruded aluminum case with end plates. Popular for "
              "the style, the threaded holes, and the fact that the enclosure "
              "itself is a heatsink to keep those batteries cool!",
         search='No canonical seller &mdash; several options from Chinese '
                'distributors (AliExpress, Alibaba). Sellers rotate constantly.'),'''
new_nebra = f'''    card("Aluminum &mdash; Nebra", "alu-nebra", "Nebra-style cast aluminum enclosure",
         desc="Nebra-style extruded aluminum case with end plates. Popular for "
              "the style, the threaded holes, and the fact that the enclosure "
              "itself is a heatsink to keep those batteries cool!",
         link="{AMZ}B0G8HN1Y9B"),'''
assert s.count(old_nebra) == 1, "nebra card"
s = s.replace(old_nebra, new_nebra)

# --------------------------------------------------- 3. boards: Heltec V3
board_anchor = '''    card("Heltec V4", "heltec-v4", "Heltec WiFi LoRa 32 V4 board",'''
board_new = f'''    card("Heltec V3", "heltec-v3", "Heltec WiFi LoRa 32 V3 board",
         desc="The V4's predecessor and still everywhere. Same footprint, "
              "cheaper, and the one most guides are written against.",
         link="{AMZ}B0GQLBS3MM"),

''' + board_anchor
assert s.count(board_anchor) == 1, "boards anchor"
s = s.replace(board_anchor, board_new)

# --------------------------- 4/5. solar panels and managers, as their own grids
coax_marker = "# --------------------------------------------------------------------- coax"
solar = f'''# ------------------------------------------------------------ solar panels

solar_panels = grid([
    card("SoShine 12 W panel", "soshine-12w", "SoShine 12 W solar panel with mount",
         specs=[("Output", "12 W")],
         desc="Wall or pole mount with the bracket included. Plenty of headroom "
              "for a repeater that has to ride out a cloudy week.",
         link="{AMZ}B0GCH9894Z"),
])

# ---------------------------------------------------------- solar managers

solar_managers = grid([
    card("Waveshare Solar Power Manager", "waveshare-manager",
         "Waveshare solar power manager board",
         desc="Takes the panel in, charges the pack, and hands your board a "
              "regulated 5 V. Screw terminals for the panel and battery, USB-C "
              "and a barrel jack, and a four-LED charge gauge.",
         link="{AMZ}B0CT2ZBML9"),
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

''' + coax_marker
assert s.count(coax_marker) == 1, "coax marker"
s = s.replace(coax_marker, solar)

# ------------------------------------- 6. DIY subsections + UHF/VHF/HF section
old_diy = '''      <p class="hw-sub">Batteries</p>
      <div class="hw-callout"><strong>Only buy from a trusted source.</strong>
        We're deliberately not linking Amazon here &mdash; counterfeit and
        rewrapped cells are rampant, and a fake cell in a sealed box on someone's
        roof is the one failure mode in this whole page that starts a fire. Try
        18650batterystore.com, illumn.com, or liionwholesale.com.</div>
{batteries}

      <p class="hw-sub">Coax whips &amp; cable</p>'''
new_diy = '''      <p class="hw-sub">Batteries</p>
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

      <p class="hw-sub">Coax whips &amp; cable</p>'''
assert s.count(old_diy) == 1, "diy body"
s = s.replace(old_diy, new_diy)

# new top-level section after the DIY one
old_close = '''      </div>
    </section>
  </div>
</main>"""'''
new_close = '''      </div>
    </section>

    <section class="hw-section" id="uhf-vhf-hf">
      <h2>UHF / VHF / HF</h2>
      <p class="hw-note">Off the mesh and onto the ham bands &mdash; local
         people worth knowing.</p>
{uhf_vhf_hf}
    </section>
  </div>
</main>"""'''
assert s.count(old_close) == 1, "main close"
s = s.replace(old_close, new_close)

open(p, "w", encoding="utf-8").write(s)
print("build_hardware.py updated for REV2")
