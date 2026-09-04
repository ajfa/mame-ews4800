#!/usr/bin/env python3
"""Subtracts two program counter histogram dumps and names the difference.

The EWS_PCHIST histogram is CUMULATIVE from frame zero, so looking at the whole of it
mixes phases, menus, package copying, kernel rebuild, and says nothing about what the
machine is doing right now. Subtracting two dumps gives the phase between them.

This is how a stalled install was diagnosed without seeing the screen: 95 per cent in the
idle page and 3 per cent in user space means the machine is waiting for a key, not
building a kernel. Confirmed afterwards, the disk resumed writing 51 seconds after the
answer went in.

Names come out by 4 KB page, which hides the real function: in page 8022f000 the preceding
symbol is uidquota_get but the one that lives inside is idle, at 0x8022fe80. So the label
here uses the symbols found INSIDE the page, not the one before it.

Usage:  pcdiff.py <vmunix> <before.log> <after.log> [n]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hwcompare import load_syms  # noqa: E402


def load(path):
    hdr, h = None, {}
    for line in open(path):
        if line.startswith('#'):
            hdr = line.strip()
            continue
        p = line.split()
        if len(p) == 2:
            h[int(p[0], 16)] = int(p[1])
    return hdr, h


def main():
    vmunix, a, b = sys.argv[1], sys.argv[2], sys.argv[3]
    top = int(sys.argv[4]) if len(sys.argv) > 4 else 20

    syms = sorted([s for s in load_syms(vmunix) if s[1]], key=lambda s: s[1])
    ha, A = load(a)
    hb, B = load(b)
    print('before  %s' % ha)
    print('after   %s' % hb)
    print()

    def label(pg):
        if pg >= 0xbfc00000:
            return 'boot ROM'
        if not (0x80000000 <= pg < 0xa0000000):
            return 'user space'
        inside = [s for s in syms if pg <= s[1] <= pg + 0xfff]
        prev = None
        for s in syms:
            if s[1] < pg:
                prev = s
            else:
                break
        if not inside:
            return prev[0] if prev else 'kernel?'
        names = [s[0] for s in inside]
        if len(names) <= 3:
            return '/'.join(names)
        return '%s..%s (%d fn)' % (names[0], names[-1], len(names))

    delta = {}
    for pg in set(A) | set(B):
        d = B.get(pg, 0) - A.get(pg, 0)
        if d > 0:
            delta[pg] = d
    total = sum(delta.values()) or 1
    print('%d samples in the window, %d pages' % (total, len(delta)))
    print()
    for pg in sorted(delta, key=lambda p: -delta[p])[:top]:
        print('  %6.2f%%  %08x  %8d  %s'
              % (100.0 * delta[pg] / total, pg, delta[pg], label(pg)))


main()
