#!/usr/bin/env python3
"""Regenerate the PayPal Pool QR code from committee.PAYPAL_URL.

Run this whenever PAYPAL_URL changes. A stale QR code is the worst kind of
bug here: it looks fine, scans fine, and sends money to the wrong place.

    pip install "qrcode[pil]" opencv-python-headless
    python3 tools/make-qr.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import committee  # noqa: E402

import qrcode  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "public", committee.PAYPAL_QR)

assert committee.PAYPAL_URL, "PAYPAL_URL is None -- nothing to encode"

# Error correction H: this gets printed on paper and photographed in daylight
# at hamfests. A scuffed or partly shadowed code still has to scan.
q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H,
                  box_size=12, border=3)
q.add_data(committee.PAYPAL_URL)
q.make(fit=True)
q.make_image(fill_color="#0f1320", back_color="white").convert("RGB").save(OUT)

# Never ship one of these unverified: decode it back and compare.
try:
    import cv2
    import numpy as np
    from PIL import Image
    det = cv2.QRCodeDetector()
    for px in (564, 180):
        im = Image.open(OUT).convert("RGB").resize((px, px), Image.LANCZOS)
        got, _, _ = det.detectAndDecode(np.array(im)[:, :, ::-1])
        assert got == committee.PAYPAL_URL, f"{px}px decodes to {got!r}"
        print(f"  verified at {px}px")
except ImportError:
    print("  WARNING: opencv not installed, QR written but NOT verified")

print(f"{OUT} <- {committee.PAYPAL_URL}")
