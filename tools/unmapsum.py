#!/usr/bin/env python3
"""Summarises MAME's unmapped access log, produced with EWS_UNMAPLOG=1.

Groups by 64 KB window and by program counter, which is what carries meaning. A hundred
loose lines say nothing; "the kernel asks for this window from this routine" does.

Usage:  unmapsum.py <run.out> [vmunix]    (the kernel is optional, it names the PCs)
"""
import os
import re
import sys

LINE = re.compile(
    r"\((?P<pc>[0-9A-F]{8})\).*unmapped program memory (?P<op>read from|write to) "
    r"(?P<addr>[0-9A-F]+)")


def main():
    path = sys.argv[1]
    vmunix = sys.argv[2] if len(sys.argv) > 2 else None

    name_of = lambda a: ''
    if vmunix:
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from hwcompare import load_syms
            syms = sorted([(s[0], s[1]) for s in load_syms(vmunix) if s[1]],
                          key=lambda s: s[1])
            addrs = [a for _n, a in syms]

            def name_of(a):
                lo, hi = 0, len(addrs) - 1
                if not addrs or a < addrs[0] or a > addrs[-1] + 0x10000:
                    return ''
                while lo < hi:
                    mid = (lo + hi + 1) // 2
                    if addrs[mid] <= a:
                        lo = mid
                    else:
                        hi = mid - 1
                nm, ad = syms[lo]
                return nm if a == ad else '%s+0x%x' % (nm, a - ad)
        except Exception as e:
            print('(no symbol names: %s)' % e)

    windows = {}
    for ln in open(path, errors='replace'):
        m = LINE.search(ln)
        if not m:
            continue
        pc = int(m.group('pc'), 16)
        addr = int(m.group('addr'), 16)
        op = 'R' if m.group('op').startswith('read') else 'W'
        win = addr & ~0xffff
        e = windows.setdefault(win, {'n': 0, 'ops': set(), 'pcs': {},
                                     'lo': addr, 'hi': addr})
        e['n'] += 1
        e['ops'].add(op)
        e['pcs'][pc] = e['pcs'].get(pc, 0) + 1
        e['lo'] = min(e['lo'], addr)
        e['hi'] = max(e['hi'], addr)

    if not windows:
        print('no unmapped access in %s' % path)
        return

    print('%-12s %6s %-4s %-21s %s' % ('64K window', 'times', 'R/W',
                                       'actual range', 'accessed from'))
    for win in sorted(windows):
        e = windows[win]
        pcs = sorted(e['pcs'].items(), key=lambda kv: -kv[1])[:3]
        who = '  '.join('%08x%s x%d' % (pc, ('=' + name_of(pc)) if name_of(pc) else '', c)
                        for pc, c in pcs)
        print('%08x     %6d %-4s %08x-%08x  %s'
              % (win, e['n'], ''.join(sorted(e['ops'])), e['lo'], e['hi'], who))


main()
