"""Recolour the WorkPerks design-principle illustrations, indigo to green.

RUN THIS ONLY AGAINST THE INDIGO ORIGINALS, which live untouched at
02. Work/01. Workperks/Ref./design principles/. It rewrites its arguments in
place and the map is not idempotent, so running it over the already-green
files in assets/img/workperks/principles/ rotates them a second time.

Hue-map the five principle illustrations from the indigo / cyan / magenta
family into a green one.

Hue in, measured across all five files: 180..310, with the ground at 233 and
96% of the pixels inside 210..250.
Hue out: h' = 148 - 0.38 * (h - 233)  ->  119..168
  ground  233 -> 148  deep emerald
  cyan    193 -> 163  mint, the light end
  magenta 289 -> 127  shamrock, the mid end
The band is compressed rather than rotated: a straight rotation that put the
ground in green left the magenta tail back in blue, which is the colour being
removed.

Saturation is untouched and lightness takes L**1.22. Preserving relative
luminance instead was tried first and came out muddy: green carries 0.72 of
the luminance weight against blue's 0.07, so holding luminance forces every
green down into the ground and the artwork loses its light end. The curve
keeps the highlights bright and pulls only the dark end down, so the ground
stays as deep as the indigo it replaces.
"""
import zlib, struct, sys, colorsys, os

ANCHOR_IN, ANCHOR_OUT, SLOPE = 233.0, 148.0, -0.38

def decode(path):
    d = open(path, 'rb').read(); pos = 8; idat = b''
    while pos < len(d):
        ln = struct.unpack('>I', d[pos:pos+4])[0]; typ = d[pos+4:pos+8]
        data = d[pos+8:pos+8+ln]
        if typ == b'IHDR': w, h, bd, ct, comp, filt, inter = struct.unpack('>IIBBBBB', data)
        elif typ == b'IDAT': idat += data
        pos += 12 + ln
    assert bd == 8 and ct == 6 and inter == 0, (bd, ct, inter)
    raw = zlib.decompress(idat); bpp = 4; stride = w * bpp
    out = bytearray(); prev = bytearray(stride); i = 0
    for y in range(h):
        f = raw[i]; i += 1
        line = bytearray(raw[i:i+stride]); i += stride
        if f == 1:
            for x in range(bpp, stride): line[x] = (line[x] + line[x-bpp]) & 255
        elif f == 2:
            for x in range(stride): line[x] = (line[x] + prev[x]) & 255
        elif f == 3:
            for x in range(stride):
                a = line[x-bpp] if x >= bpp else 0
                line[x] = (line[x] + ((a + prev[x]) >> 1)) & 255
        elif f == 4:
            for x in range(stride):
                a = line[x-bpp] if x >= bpp else 0
                b = prev[x]; c = prev[x-bpp] if x >= bpp else 0
                p = a + b - c; pa = abs(p-a); pb = abs(p-b); pc = abs(p-c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[x] = (line[x] + pr) & 255
        out += line; prev = line
    return w, h, bytearray(out)

def encode(path, w, h, px):
    raw = bytearray()
    stride = w * 4
    for y in range(h):
        raw.append(0)
        raw += px[y*stride:(y+1)*stride]
    def chunk(typ, data):
        return struct.pack('>I', len(data)) + typ + data + struct.pack('>I', zlib.crc32(typ + data) & 0xffffffff)
    out = b'\x89PNG\r\n\x1a\n'
    out += chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0))
    out += chunk(b'IDAT', zlib.compress(bytes(raw), 9))
    out += chunk(b'IEND', b'')
    open(path, 'wb').write(out)

def lin(c):
    c /= 255.0
    return c/12.92 if c <= 0.04045 else ((c+0.055)/1.055)**2.4
def unlin(c):
    c = max(0.0, min(1.0, c))
    return 12.92*c if c <= 0.0031308 else 1.055*(c**(1/2.4)) - 0.055
def Y(r, g, b):
    return 0.2126*lin(r) + 0.7152*lin(g) + 0.0722*lin(b)

cache = {}
DARKEN = 0.45   # the value the live files were produced with

def convert(r, g, b):
    key = (r, g, b)
    if key in cache: return cache[key]
    hh, ll, ss = colorsys.rgb_to_hls(r/255, g/255, b/255)
    if ss < 0.02:                     # neutral: nothing to rotate
        cache[key] = key; return key
    deg = hh * 360.0
    if deg < 90: deg += 360           # keep the 180..310 band contiguous
    nd = (ANCHOR_OUT + SLOPE * (deg - ANCHOR_IN)) % 360.0
    nr, ng, nb = colorsys.hls_to_rgb(nd/360.0, ll ** (1 + DARKEN * (1 - ll)), ss)
    val = tuple(max(0, min(255, int(round(v*255)))) for v in (nr, ng, nb))
    cache[key] = val
    return val

for name in sys.argv[1:]:
    w, h, px = decode(name)
    for i in range(0, len(px), 4):
        px[i], px[i+1], px[i+2] = convert(px[i], px[i+1], px[i+2])
    encode(name, w, h, px)
    print(f'{os.path.basename(name)}  {w}x{h}  {len(cache)} distinct colours')
