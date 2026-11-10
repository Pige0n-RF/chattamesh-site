#!/usr/bin/env python3
"""Start the Regions group collapsed on Setup & Information.

The parent toggle shipped expanded, so the page opened with three long
sections already unrolled. Its three children were already collapsed, so this
makes the whole group consistent: everything starts shut and the reader opens
what they want.

Idempotent by assertion: re-running fails loudly rather than double-applying.
"""
import os

P = os.path.join("public", "setup-information.html")
src = open(P, encoding="utf-8").read()

# --- the toggle itself: closed state, and the label that goes with it -------
OLD_BTN = ('    <button type="button" class="regions-toggle parent-toggle" '
           'id="regionsGroupToggle" aria-expanded="true">\n'
           '      <span class="regions-toggle-icon">&#9656;</span>\n'
           '      <span class="regions-toggle-label">Hide Regions</span>')
NEW_BTN = ('    <button type="button" class="regions-toggle parent-toggle" '
           'id="regionsGroupToggle" aria-expanded="false" '
           'aria-controls="regionsGroupContent">\n'
           '      <span class="regions-toggle-icon">&#9656;</span>\n'
           '      <span class="regions-toggle-label">Show Regions</span>')
assert src.count(OLD_BTN) == 1, "parent toggle anchor"
src = src.replace(OLD_BTN, NEW_BTN)

# --- hide the three sections the toggle drives ------------------------------
# It sets .hidden on these three by id, so the initial state has to match what
# the script will do on the first click -- not on the wrapper, or the first
# click would unhide the sections while the wrapper stayed shut.
for sec in ("scopes", "standard-repeater", "border-repeater"):
    old = f'<section id="{sec}">'
    assert src.count(old) == 1, f"{sec} section"
    src = src.replace(old, f'<section id="{sec}" hidden>')

open(P, "w", encoding="utf-8").write(src)
print(f"setup-information.html: Regions group starts collapsed ({len(src):,} bytes)")
