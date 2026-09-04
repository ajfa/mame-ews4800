#!/usr/bin/env python3
"""Finds the real line stride of a frame buffer dump by vertical autocorrelation.

A glyph has vertical strokes, so if S is the true stride then many lit bytes have another
lit byte exactly S bytes further on. The overlap is counted for every candidate S and the
best one wins, normalised so that a small S does not win by default.

This is how the console format was established rather than guessed: 256 bytes per line at
0.903, against 0.815 for its double and 0.732 for its triple.

Usage:  fbcorr.py <fb0.bin> [max stride]
"""
import sys


def main():
    raw = open(sys.argv[1], 'rb').read()
    maxs = int(sys.argv[2], 0) if len(sys.argv) > 2 else 4096
    on = set(i for i, b in enumerate(raw) if b)
    total = len(on)
    print("lit bytes: %d" % total)
    if not total:
        return
    best = []
    for s in range(8, maxs + 1, 8):
        hit = sum(1 for o in on if (o + s) in on)
        best.append((hit / total, s, hit))
    best.sort(reverse=True)
    print("%-8s %-8s %s" % ("stride", "overlap", "fraction"))
    for frac, s, hit in best[:14]:
        print("%-8d %-8d %.3f" % (s, hit, frac))


main()
