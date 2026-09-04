#!/usr/bin/env python3
"""Shows whatever is drawn in a frame buffer dump, as ASCII.

It first finds the box that contains everything non zero, so there is no need to guess
where to look, and then prints that area one character per pixel, split into widths that
fit a terminal.

Usage:  fbascii.py <fb0.bin> [--stride 2048] [--maxwidth 200]
"""
import sys


def main():
    path = sys.argv[1]
    args = sys.argv[2:]

    def opt(name, default):
        return int(args[args.index(name) + 1], 0) if name in args else default

    stride = opt('--stride', 2048)
    maxw = opt('--maxwidth', 200)

    raw = open(path, 'rb').read()
    rows = len(raw) // stride

    x0, x1, y0, y1 = stride, -1, rows, -1
    for y in range(rows):
        line = raw[y * stride:(y + 1) * stride]
        if not any(line):
            continue
        y0 = min(y0, y)
        y1 = max(y1, y)
        first = next(i for i, b in enumerate(line) if b)
        last = len(line) - 1 - next(i for i, b in enumerate(reversed(line)) if b)
        x0 = min(x0, first)
        x1 = max(x1, last)

    if y1 < 0:
        print("the dump is all zero")
        return

    print("box with content: x %d..%d  y %d..%d  (%d x %d)"
          % (x0, x1, y0, y1, x1 - x0 + 1, y1 - y0 + 1))

    for xs in range(x0, x1 + 1, maxw):
        xe = min(xs + maxw - 1, x1)
        print("\n--- columns %d..%d" % (xs, xe))
        for y in range(y0, y1 + 1):
            line = raw[y * stride:(y + 1) * stride]
            print(''.join('#' if line[x] else '.' for x in range(xs, xe + 1)))


main()
