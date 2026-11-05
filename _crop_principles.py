"""Crop the dead ground off the left of the design-principle illustrations.

Run after _greenify_principles.py, against the files in
assets/img/workperks/principles/. Idempotent: once an image is flush its
left pad is 0 and a second run is a no-op.

WHY THIS EXISTS
The five illustrations are screenshots, so each one carries its own flat
ground and each one sits in a different place on it: measured left pads of
50, 38, 57, 47 and 55 source pixels. The chapter renders every image at one
fixed height (9rem), so those pads scale by different amounts and the five
drawings start at five different distances from the plate edge — up to 10px
apart on screen. The CSS already starts the image box at the left of the
plate (.wp-pr__art is a flex row at flex-start); the remaining offset is
inside the files, so only the files can fix it.

Cropping is invisible because the thing being removed is the artwork's own
ground and the plate behind it is painted at that same colour,
--wp-pr-ground:#023218. What leaves the left edge is replaced by the plate.

The edge is found with a tolerance of 10/255 against the corner pixel.
These are screenshots and the ground carries about +/-5 of noise, so a
tighter threshold finds the noise instead of the drawing; measured column
deviation jumps from under 10 to about 190 at the real edge, so anything
between roughly 8 and 40 picks the same column.

Only the left is cropped. The slack on the right is behind the drawing in
the same ground colour and costs nothing to keep, and the top and bottom
set where the drawing sits in a fixed-height plate, which is not what this
is about.

After running, update the width/height attributes on the five <img> tags in
_pages/01b-work-workperks.html to the sizes printed here, then rebuild.
"""
import importlib.util, glob, os, sys

TOL = 10

_spec = importlib.util.spec_from_file_location(
    "_greenify_principles",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "_greenify_principles.py"))
_g = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_g)
decode, encode = _g.decode, _g.encode


def left_pad(w, h, px):
    """First column holding anything that is not the ground."""
    g = px[0], px[1], px[2], px[3]
    left = w
    for y in range(h):
        base = y * w * 4
        for x in range(left):
            i = base + x * 4
            if (max(abs(px[i] - g[0]), abs(px[i+1] - g[1]), abs(px[i+2] - g[2])) > TOL
                    or abs(px[i+3] - g[3]) > TOL):
                left = x
                break
    return 0 if left == w else left


def crop_left(w, h, px, n):
    out = bytearray()
    for y in range(h):
        base = y * w * 4
        out += px[base + n * 4: base + w * 4]
    return w - n, h, out


def main(paths):
    for p in paths:
        w, h, px = decode(p)
        n = left_pad(w, h, px)
        if n == 0:
            print(f"{os.path.basename(p):20s} {w}x{h}  already flush")
            continue
        nw, nh, out = crop_left(w, h, px, n)
        encode(p, nw, nh, out)
        print(f"{os.path.basename(p):20s} {w}x{h} -> {nw}x{nh}  (cropped {n}px)")


if __name__ == "__main__":
    args = sys.argv[1:] or sorted(glob.glob(
        os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "assets/img/workperks/principles/*.png")))
    main(args)
