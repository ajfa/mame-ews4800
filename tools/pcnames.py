#!/usr/bin/env python3
"""Names the program counter histogram that install.lua dumps with EWS_PCHIST=1.

Each line of fvtags/pchist.log is a hexadecimal PC and a sample count. They are grouped by
FUNCTION using the kernel's .unixsyms section, which is what carries meaning: four hundred
loose addresses say nothing, "seventy per cent in this routine" does.

Addresses outside the kernel are grouped separately, as user space or boot ROM.

The histogram is bucketed by 4 KB page, so a name here is the symbol PRECEDING the page
and can mislead. Use pcpage.py to see who actually lives inside.

Usage:  pcnames.py <vmunix> <pchist.log> [n]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hwcompare import load_syms  # noqa: E402


def main():
    vmunix, path = sys.argv[1], sys.argv[2]
    top = int(sys.argv[3]) if len(sys.argv) > 3 else 25

    ordered = sorted([s for s in load_syms(vmunix) if s[1]], key=lambda s: s[1])
    addrs = [s[1] for s in ordered]

    def name_of(a):
        # binary search for the symbol preceding the address
        lo, hi = 0, len(addrs) - 1
        if not addrs or a < addrs[0]:
            return None
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if addrs[mid] <= a:
                lo = mid
            else:
                hi = mid - 1
        nm, ad = ordered[lo][0], ordered[lo][1]
        return '%s+0x%x' % (nm, a - ad) if a != ad else nm

    total, groups, places = 0, {}, {}
    for line in open(path):
        # the header carries exact totals per range, independent of any bucketing
        if line.startswith('#'):
            print(line.rstrip())
            c = line.split()
            if len(c) >= 11:
                samples = float(c[4]) or 1.0
                print('  kernel %.2f%%   user %.2f%%   ROM %.2f%%'
                      % (100 * int(c[6]) / samples, 100 * int(c[8]) / samples,
                         100 * int(c[10]) / samples))
            print()
            continue
        p = line.split()
        if len(p) != 2:
            continue
        pc, cnt = int(p[0], 16), int(p[1])
        total += cnt
        if 0x80000000 <= pc < 0xa0000000:
            nm = name_of(pc) or 'kernel?'
            key = nm.split('+')[0]
        elif pc >= 0xbfc00000:
            key = 'boot ROM'
        else:
            key = 'user space'
        groups[key] = groups.get(key, 0) + cnt
        places.setdefault(key, []).append((cnt, pc))

    print('%d samples across %d pages of 4 KB'
          % (total, sum(len(v) for v in places.values())))
    print()
    for k in sorted(groups, key=lambda k: -groups[k])[:top]:
        worst = sorted(places[k], reverse=True)[:3]
        detail = ' '.join('%08x x%d' % (a, c) for c, a in worst)
        print('  %6.2f%%  %-28s %8d   %s'
              % (100.0 * groups[k] / total, k, groups[k], detail))


main()
