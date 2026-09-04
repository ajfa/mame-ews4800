#!/usr/bin/env python3
"""Resolves $gp relative offsets in the kernel and shows what lives there.

SVR4 MIPS code addresses almost everything through $gp, so a disassembly is full of
`addiu $a1, $gp, -0x72f4` without saying what that is. This reads $gp and prints the
string, or the word, found at each offset.

Note that this kernel carries no PT_MIPS_REGINFO, so the segment header gives zero. The
real value is in its own .unixsyms table, under the symbol _gp. Reading it from the wrong
place gives offsets that land nowhere and look like a bad disassembly.

Usage:  gpstr.py <vmunix> <offset> [more...]      (decimal or 0x...)
        gpstr.py <vmunix> --gp=0x802ac800 <offset>
"""
import struct
import sys

NUL = bytes([0])


def main():
    path = sys.argv[1]
    blob = open(path, 'rb').read()
    phoff = struct.unpack('>I', blob[28:32])[0]
    phnum = struct.unpack('>H', blob[44:46])[0]
    loads, gp = [], 0
    for i in range(phnum):
        e = blob[phoff + i * 32: phoff + (i + 1) * 32]
        t, off, va, _pa, fsz = struct.unpack('>IIIII', e[:20])
        if t == 1:
            loads.append((off, va, fsz))
        if t == 0x70000000:
            gp = struct.unpack('>I', blob[off + 0x14:off + 0x18])[0]
    if not gp:
        try:
            sys.path.insert(0, __file__.rsplit('/', 1)[0] if '/' in __file__ else '.')
            from hwcompare import load_syms
            for s in load_syms(path):
                if s[0] == '_gp' and s[1]:
                    gp = s[1]
                    break
        except Exception:
            pass
    for a in sys.argv[2:]:
        if a.startswith('--gp='):
            gp = int(a.split('=')[1], 0)
    print('gp = 0x%08x' % gp)

    def rd(va, n):
        for off, base, sz in loads:
            if base <= va < base + sz:
                o = off + (va - base)
                return blob[o:o + n]
        return None

    for arg in sys.argv[2:]:
        if arg.startswith('--gp='):
            continue
        d = int(arg, 0)
        va = (gp + d) & 0xffffffff
        raw = rd(va, 32)
        if raw is None:
            print('  gp%+7d  0x%08x   (outside every LOAD)' % (d, va))
            continue
        nul = raw.find(NUL)
        txt = raw[:nul] if nul > 0 else b''
        readable = all(32 <= c < 127 for c in txt) and len(txt) > 0
        wd = struct.unpack('>I', raw[:4])[0]
        if readable:
            print('  gp%+7d  0x%08x   string %r' % (d, va, txt.decode()))
        else:
            print('  gp%+7d  0x%08x   word 0x%08x   bytes %s'
                  % (d, va, wd, raw[:8].hex()))


main()
