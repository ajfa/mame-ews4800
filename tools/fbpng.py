#!/usr/bin/env python3
"""Converts a frame buffer dump, 1 bpp and 256 bytes per line, into a PNG.

No dependencies: the PNG is assembled by hand with zlib from the standard library. It
crops to the visible 1280x1024 by default.

The stride is 256 bytes, which is 2048 pixels at one bit each, of which 1280 are visible.
That was established by autocorrelation, see fbcorr.py, not by guessing.

Usage:  fbpng.py <fb0.bin> <out.png> [--stride 256] [--width 1280] [--height 1024]
                                     [--y0 0] [--scale 1]
"""
import struct
import sys
import zlib


def main():
    src, dst = sys.argv[1], sys.argv[2]
    args = sys.argv[3:]

    def opt(name, default):
        return int(args[args.index(name) + 1], 0) if name in args else default

    pitch = opt('--stride', 256)
    width = opt('--width', 1280)
    height = opt('--height', 1024)
    y0 = opt('--y0', 0)
    scale = opt('--scale', 1)

    raw = open(src, 'rb').read()
    rows = []
    for y in range(y0, y0 + height):
        base = y * pitch
        line = bytearray()
        for x in range(width):
            b = raw[base + (x >> 3)] if base + (x >> 3) < len(raw) else 0
            line.append(0 if (b >> (7 - (x & 7))) & 1 else 255)
        if scale > 1:
            line = bytearray(b for b in line for _ in range(scale))
        for _ in range(scale):
            rows.append(bytes(line))

    w, h = width * scale, len(rows)
    body = b''.join(bytes([0]) + r for r in rows)

    def chunk(tag, data):
        return (struct.pack('>I', len(data)) + tag + data
                + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF))

    png = (bytes([0x89]) + b'PNG\r\n' + bytes([0x1a]) + b'\n'
           + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 0, 0, 0, 0))
           + chunk(b'IDAT', zlib.compress(body, 9))
           + chunk(b'IEND', b''))
    open(dst, 'wb').write(png)
    print("%s: %d x %d" % (dst, w, h))


main()
