"""Minimal PNG read/write (8-bit RGB/RGBA, filters 0-4) plus a side-by-side
composer, so the two Origin panels become one figure without an image library."""
import struct
import sys
import zlib

import numpy as np


def png_read(path):
    data = open(path, "rb").read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG: %s" % path
    pos, idat, pal = 8, [], None
    w = h = depth = ctype = None
    while pos < len(data):
        (ln,) = struct.unpack(">I", data[pos:pos + 4])
        typ = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            w, h, depth, ctype = struct.unpack(">IIBB", body[:10])
        elif typ == b"PLTE":
            pal = np.frombuffer(body, dtype=np.uint8).reshape(-1, 3)
        elif typ == b"IDAT":
            idat.append(body)
        elif typ == b"IEND":
            break
        pos += 12 + ln
    assert depth == 8, "only 8-bit PNG supported (got %s)" % depth
    nch = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ctype]
    raw = zlib.decompress(b"".join(idat))
    stride = w * nch
    out = np.empty((h, stride), dtype=np.uint8)
    prev = np.zeros(stride, dtype=np.uint8)
    p = 0
    for y in range(h):
        f = raw[p]
        line = np.frombuffer(raw[p + 1:p + 1 + stride], dtype=np.uint8).copy()
        p += 1 + stride
        if f == 1:
            for i in range(nch, stride):
                line[i] = (int(line[i]) + int(line[i - nch])) & 0xFF
        elif f == 2:
            line = (line.astype(np.int32) + prev.astype(np.int32)).astype(np.uint8)
        elif f == 3:
            for i in range(stride):
                a = int(line[i - nch]) if i >= nch else 0
                line[i] = (int(line[i]) + ((a + int(prev[i])) >> 1)) & 0xFF
        elif f == 4:
            for i in range(stride):
                a = int(line[i - nch]) if i >= nch else 0
                b = int(prev[i])
                c = int(prev[i - nch]) if i >= nch else 0
                pp = a + b - c
                pa, pb, pc = abs(pp - a), abs(pp - b), abs(pp - c)
                pred = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (int(line[i]) + pred) & 0xFF
        out[y] = line
        prev = line
    img = out.reshape(h, w, nch)
    if ctype == 3:
        img = pal[img[:, :, 0]]
    elif ctype == 0:
        img = np.repeat(img, 3, axis=2)
    elif ctype == 4:
        img = np.repeat(img[:, :, :1], 3, axis=2)
    elif ctype == 6:
        rgb = img[:, :, :3].astype(np.float32)
        a = img[:, :, 3:4].astype(np.float32) / 255.0
        img = (rgb * a + 255.0 * (1 - a)).round().astype(np.uint8)
    return img.astype(np.uint8)


def png_write(path, img):
    h, w, _ = img.shape
    raw = b"".join(b"\x00" + img[y].tobytes() for y in range(h))

    def chunk(t, b):
        return struct.pack(">I", len(b)) + t + b + struct.pack(">I", zlib.crc32(t + b) & 0xFFFFFFFF)

    open(path, "wb").write(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b""))


def ink_box(img, thresh=245, pad=12):
    """Bounding box of everything that is not white."""
    mask = (img < thresh).any(axis=2)
    rows = np.where(mask.any(axis=1))[0]
    cols = np.where(mask.any(axis=0))[0]
    t, b = max(0, rows[0] - pad), min(img.shape[0], rows[-1] + 1 + pad)
    l, r = max(0, cols[0] - pad), min(img.shape[1], cols[-1] + 1 + pad)
    return img[t:b, l:r]


def scale_to_height(img, height):
    """Nearest-neighbour vertical+horizontal rescale to a target height."""
    h, w, _ = img.shape
    if h == height:
        return img
    new_w = max(1, int(round(w * height / h)))
    yi = (np.arange(height) * h / height).astype(np.int32).clip(0, h - 1)
    xi = (np.arange(new_w) * w / new_w).astype(np.int32).clip(0, w - 1)
    return img[yi][:, xi]


if __name__ == "__main__":
    a = ink_box(png_read(sys.argv[1]))
    b = ink_box(png_read(sys.argv[2]))
    print("panel a ink box: %dx%d" % (a.shape[1], a.shape[0]))
    print("panel b ink box: %dx%d" % (b.shape[1], b.shape[0]))

    # Match panel heights, then lay them out with a gap.
    height = max(a.shape[0], b.shape[0])
    a = scale_to_height(a, height)
    b = scale_to_height(b, height)
    gap = int(round(height * 0.05))
    margin = int(round(height * 0.03))
    W = a.shape[1] + gap + b.shape[1] + 2 * margin
    H = height + 2 * margin
    canvas = np.full((H, W, 3), 255, dtype=np.uint8)
    canvas[margin:margin + height, margin:margin + a.shape[1]] = a
    x0 = margin + a.shape[1] + gap
    canvas[margin:margin + height, x0:x0 + b.shape[1]] = b
    png_write(sys.argv[3], canvas)
    print("composed %dx%d -> %s" % (W, H, sys.argv[3]))
    print("width share: a=%.0f%%  b=%.0f%%" % (100 * a.shape[1] / W, 100 * b.shape[1] / W))
