#!/usr/bin/env python3
"""Prepare supplied product photos for public/images/hardware/.

Output is WebP with an alpha channel, so shots sit on the card colour instead
of in a white box. Three paths, picked per file:

  keep   - the file already has real alpha; use it as-is
  key    - flat studio background; flood-fill in from the four corners and
           make that region transparent
  photo  - an environmental shot (a node on a fence, a product on a desk).
           There is no background to remove, so it keeps its own and gets
           letterboxed with its sampled border colour

Keying is deliberately not applied to the `photo` files: flood-filling a
lifestyle shot eats into the subject and leaves a ragged edge.

Each shot is trimmed to its content bounding box before being letterboxed onto
an 800x500 canvas. The slot CSS uses object-fit:cover, so matching 16:10 up
front is what stops a centre crop decapitating a 45-inch antenna, and the trim
makes the product as large as the frame allows.
"""
import glob
import os

from PIL import Image, ImageDraw, ImageFilter

SRC = "/mnt/user-data/uploads"
# Uploads do not always land in one place: a resumed session can leave some
# files under the harness upload dir with a hash prefix instead. Resolve each
# source by name across both roots rather than assuming one.
SRC_FALLBACKS = ["/root/.claude/uploads"]
OUT = "/home/claude/ship/public/images/hardware"
W, H = 800, 500

KEEP, KEY, PHOTO, AUTO = "keep", "key", "photo", "auto"

# supplied file -> (slug, mode). PHOTO is the only mode worth declaring by
# hand; AUTO decides keep-vs-key from the corner alpha, because "the file has
# an alpha channel" and "the file has a transparent background" are different
# claims -- atlavox_whip.png has alpha and an opaque white backdrop, and
# trusting the channel alone left it as a white box on the card.
#
# The earlier wiotracker.jpg is absent on purpose: it was PWRD-branded
# hardware, not a Wio Tracker. The MeshCore file supplied afterwards is used.
# supplied file -> (slug, mode, thresh). PHOTO is the only mode worth
# declaring by hand; AUTO decides keep-vs-key from the corner alpha, because
# "the file has an alpha channel" and "the file has a transparent background"
# are different claims -- atlavox_whip.png has alpha and an opaque white
# backdrop, and trusting the channel alone left it as a white box.
#
# thresh only matters in KEY mode. The three Rokland antennas are white
# fiberglass on white, so the default fill walks straight through the middle of
# the mast and leaves the antenna cut in half; they need a tight one.
MAP = {
    "Peak_mesh_ultimate.avif":                     ("peakmesh-ultimate", PHOTO, 24),
    "Kaostech.webp":                               ("kaos-tree-repeater", PHOTO, 24),

    "Seeed_T1000E.png":                            ("t1000e",            AUTO, 24),
    "WisMesh_TAG.png":                             ("wismesh-tag",       AUTO, 24),
    "sensecap-solar-node-p1-pro.png":              ("sensecap-p1-pro",   AUTO, 24),
    "pouch_cell.png":                              ("pouch",             AUTO, 24),

    "Muzi_works_whip.jpg":                         ("muzi-whip",         AUTO, 24),
    "Alfa915.jpg":                                 ("alfa-5dbi",         AUTO, 24),
    "atlavox_whip.png":                            ("atlavox-whip",      AUTO, 24),
    "rokland58dbi.webp":                           ("rokland-5-8dbi",    AUTO, 10),
    "rokland8dbi.webp":                            ("rokland-8dbi",      AUTO, 10),
    "rokland10dbi.png":                            ("rokland-10dbi",     AUTO, 10),

    "Heltecv4-r8.png":                             ("heltec-v4-r8",      AUTO, 24),
    "seeed_studio_wio_tracker_l1_pro_meshcore.png": ("wio-l1-pro",       AUTO, 24),
    "Heltec_V4.png":                               ("heltec-v4",         AUTO, 24),
    "RAK_standard.webp":                           ("rak-standard",      AUTO, 24),
    "RAK1W_booster.webp":                          ("rak-booster",       AUTO, 24),
    "SCREW-COVER-BOXES-WITH-KNOCKOUT-IP68.png":    ("pvc-screw",         AUTO, 24),

    # REV2 additions. chattradio.jpg is a logo on its own blue field rather than
    # a product on a backdrop, so it keeps that field -- keying it would strip
    # the design's own colour.
    "GAT562-30s-front_jpg.webp":                   ("gat562-30s",        AUTO, 24),
    "T-ECHO_3.webp":                               ("t-echo",            AUTO, 24),
    "heltec_v3.jpg":                               ("heltec-v3",         AUTO, 24),
    "hinge_cover_pvc.jpg":                         ("pvc-hinge",         AUTO, 24),
    "aluminum_nebra.jpg":                          ("alu-nebra",         AUTO, 24),
    "12w_soshine.jpg":                             ("soshine-12w",       AUTO, 24),
    "waveshare_solar.jpg":                         ("waveshare-manager", AUTO, 24),
    "chattradio.jpg":                              ("chattradio",        PHOTO, 24),
    "aluminum_hingecover.webp":                    ("alu-hinge",         AUTO, 24),
    "Molicel18650.webp":                           ("18650",             AUTO, 24),
    "molicel21700.webp":                           ("21700",             AUTO, 24),
}

# Sources whose framing fights the 16:10 slot get a pre-crop (l, t, r, b) in
# source pixels. The Ka0s shot is a portrait photo of a node hanging in a pine;
# letterboxed whole it would sit in tall bars of sky, so it's cropped to the
# branch-and-enclosure band instead.
CROP = {
    "Kaostech.webp": (0, 180, 1140, 892),
}


MAGIC = (255, 0, 255)


def resolve(name):
    """Find a source file by name across the upload roots."""
    direct = os.path.join(SRC, name)
    if os.path.exists(direct):
        return direct
    for root in SRC_FALLBACKS:
        hits = sorted(glob.glob(os.path.join(root, "**", "*-" + name), recursive=True))
        hits += sorted(glob.glob(os.path.join(root, "**", name), recursive=True))
        if hits:
            return hits[0]
    raise SystemExit(f"source image not found anywhere: {name}")


def transparent_bg(im, cut=32):
    """True when all four corners are clear -- a real cut-out, not just alpha."""
    rgba = im.convert("RGBA")
    w, h = rgba.size
    corners = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]
    return max(rgba.getpixel(c)[3] for c in corners) < cut


def border_colour(im):
    """Median colour of the outer frame, used as the letterbox fill."""
    import statistics
    rgb = im.convert("RGB")
    w, h = rgb.size
    px = rgb.load()
    edge = ([px[x, 0] for x in range(0, w, 3)] + [px[x, h - 1] for x in range(0, w, 3)]
            + [px[0, y] for y in range(0, h, 3)] + [px[w - 1, y] for y in range(0, h, 3)])
    return tuple(int(statistics.median(c[i] for c in edge)) for i in range(3))


def key_background(im, thresh=24):
    """Flood-fill the backdrop away and return the image with it made clear.

    Seeds run all the way round the perimeter, not just the four corners: the
    Muzi shot has a lighter reflective wedge at the bottom centre that no
    corner seed could reach, and it survived as a white blob under the antenna.
    """
    rgb = im.convert("RGB")
    w, h = rgb.size
    work = rgb.copy()
    seeds = []
    sx, sy = max(1, w // 40), max(1, h // 40)
    seeds += [(x, 0) for x in range(0, w, sx)] + [(x, h - 1) for x in range(0, w, sx)]
    seeds += [(0, y) for y in range(0, h, sy)] + [(w - 1, y) for y in range(0, h, sy)]
    for seed in seeds:
        try:
            ImageDraw.floodfill(work, seed, MAGIC, thresh=thresh)
        except ValueError:
            pass

    mask = Image.new("L", (w, h), 255)
    px, mp = work.load(), mask.load()
    for y in range(h):
        for x in range(w):
            if px[x, y] == MAGIC:
                mp[x, y] = 0

    # Erode a pixel, then soften: the fill stops just short of the true edge and
    # leaves a bright fringe that reads as a halo against the dark card.
    mask = mask.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.6))
    rgba = rgb.convert("RGBA")
    rgba.putalpha(mask)
    return rgba


def trim(im):
    """Drop empty margin so the product fills more of the frame."""
    from PIL import ImageChops
    a = im.getchannel("A")
    if a.getextrema()[0] < 250:
        box = a.point(lambda p: 255 if p > 8 else 0).getbbox()
    else:
        rgb = im.convert("RGB")
        bg = Image.new("RGB", rgb.size, (255, 255, 255))
        box = ImageChops.difference(rgb, bg).convert("L").point(
            lambda p: 255 if p > 7 else 0).getbbox()
    if not box:
        return im
    pad = 10
    x0, y0, x1, y1 = box
    return im.crop((max(0, x0 - pad), max(0, y0 - pad),
                    min(im.width, x1 + pad), min(im.height, y1 + pad)))


os.makedirs(OUT, exist_ok=True)
for name, (slug, mode, thresh) in MAP.items():
    im = Image.open(resolve(name))
    if name in CROP:
        im = im.crop(CROP[name])

    if mode == AUTO:
        mode = KEEP if transparent_bg(im) else KEY

    if mode == KEY:
        im = key_background(im, thresh)
        fill = (0, 0, 0, 0)
    elif mode == KEEP:
        im = im.convert("RGBA")
        fill = (0, 0, 0, 0)
    else:
        fill = border_colour(im) + (255,)
        im = im.convert("RGBA")

    im = trim(im)
    im.thumbnail((W, H), Image.LANCZOS)
    canvas = Image.new("RGBA", (W, H), fill)
    canvas.paste(im, ((W - im.width) // 2, (H - im.height) // 2), im)

    path = os.path.join(OUT, f"{slug}.webp")
    canvas.save(path, "WEBP", quality=86, method=6)
    print(f"  {slug + '.webp':24s} {mode:5s}  {im.size} in {W}x{H}"
          f"  {os.path.getsize(path) // 1024} KB")

# Clear the old opaque JPEGs so nothing stale ships.
for f in os.listdir(OUT):
    if f.endswith(".jpg"):
        os.remove(os.path.join(OUT, f))

# ---------------------------------------------------------------- clubs

# Local radio club marks. These are logos, not product shots: no letterbox and
# no fixed aspect, just a trimmed transparent PNG that the card sizes itself.
# PNG rather than WebP because each is flat colour with hard edges, where PNG
# is both smaller and cleaner than lossy WebP.
CLUBS = {
    "w4gta_logo_transparent_hi-scaled.png": "w4gta",
    "CARC_Logo_IMG_0025_Full_Size.jpg":     "w4am",
    "cleveland_ARC.jpg":                    "ka4j",
}

CLUB_DIR = "/home/claude/ship/public/images/clubs"
os.makedirs(CLUB_DIR, exist_ok=True)
print()
for name, slug in CLUBS.items():
    im = Image.open(resolve(name))
    mode = KEEP if transparent_bg(im) else KEY
    im = key_background(im) if mode == KEY else im.convert("RGBA")
    im = trim(im)
    im.thumbnail((512, 512), Image.LANCZOS)
    out = os.path.join(CLUB_DIR, f"{slug}.png")
    im.save(out, "PNG", optimize=True)
    print(f"  {slug + '.png':24s} {mode:5s}  {im.size}  "
          f"{os.path.getsize(out) // 1024} KB")

print()
# NC Mesh partner logo. The supplied file already has a transparent background,
# so it stays PNG -- a JPEG would flatten it to a black plate on the panel.
NEI = "/home/claude/ship/public/images/neighbors"
os.makedirs(NEI, exist_ok=True)
# Skip when the source isn't in this session's uploads -- the built file is
# already committed, and re-deriving it is not required to rebuild the site.
try:
    src_logo = resolve("ncmesh_logo.png")
except SystemExit:
    src_logo = None
if src_logo is None:
    print("\n  ncmesh.png               source absent; keeping committed file")
    raise SystemExit(0)
logo = Image.open(src_logo).convert("RGBA")
logo = logo.crop(logo.getchannel("A").point(lambda p: 255 if p > 8 else 0).getbbox())
logo.thumbnail((512, 512), Image.LANCZOS)
logo.save(os.path.join(NEI, "ncmesh.png"), "PNG", optimize=True)
print(f"\n  ncmesh.png               {logo.size}  "
      f"{os.path.getsize(os.path.join(NEI, 'ncmesh.png')) // 1024} KB")
