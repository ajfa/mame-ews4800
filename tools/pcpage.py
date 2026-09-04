#!/usr/bin/env python3
"""Lists the kernel symbols that fall inside a 4 KB page.

The EWS_PCHIST histogram groups samples by page, so pcnames.py can only name the symbol
that PRECEDES the start of the page. That hides the real function: idle sits at 0x8022fe80
and was reported for a long time as uidquota_get, the symbol before the page boundary.
The number was right, the label was not.

Usage:  pcpage.py <vmunix> <page address in hex> [...]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hwcompare import load_syms  # noqa: E402


def main():
    vmunix = sys.argv[1]
    syms = sorted([s for s in load_syms(vmunix) if s[1]], key=lambda s: s[1])
    for arg in sys.argv[2:]:
        base = int(arg, 16) & ~0xfff
        print('page %08x - %08x' % (base, base + 0xfff))
        prev = None
        for s in syms:
            nm, ad = s[0], s[1]
            if ad < base:
                prev = (nm, ad)
            elif ad <= base + 0xfff:
                print('    %08x  %s' % (ad, nm))
        if prev:
            print('  (runs on from %08x %s, %d bytes earlier)'
                  % (prev[1], prev[0], base - prev[1]))
        print()


main()
