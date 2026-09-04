#!/usr/bin/env python3
"""Disassembles one UX/4800 kernel function, by name or by address.

The kernel is a static ELF32 MIPS big endian image and readelf calls it stripped, but it
carries its own table in .unixsyms, which is what hwcompare.load_syms reads. That table is
used for two things here: finding the function, and NAMING the branch targets and absolute
accesses, which is what makes the output readable.

Usage:  kdis.py <vmunix> <name|0xaddress> [instructions]
"""
import struct
import sys

from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_BIG_ENDIAN

sys.path.insert(0, __file__.rsplit('/', 1)[0] if '/' in __file__ else '.')
from hwcompare import load_syms  # noqa: E402


def segments(blob):
    phoff = struct.unpack('>I', blob[28:32])[0]
    phnum = struct.unpack('>H', blob[44:46])[0]
    out = []
    for i in range(phnum):
        e = blob[phoff + i * 32: phoff + (i + 1) * 32]
        t, off, va, _pa, fsz = struct.unpack('>IIIII', e[:20])
        if t == 1:
            out.append((off, va, fsz))
    return out


def main():
    path, what = sys.argv[1], sys.argv[2]
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 60

    blob = open(path, 'rb').read()
    loads = segments(blob)
    syms = sorted([(s[0], s[1]) for s in load_syms(path) if s[1]],
                  key=lambda s: s[1])
    byname = {nm: ad for nm, ad in syms}
    addrs = [a for _n, a in syms]

    if what.startswith('0x'):
        start = int(what, 16)
    else:
        if what not in byname:
            print('no such symbol %r' % what)
            return 1
        start = byname[what]

    def name_of(a):
        lo, hi = 0, len(addrs) - 1
        if not addrs or a < addrs[0]:
            return None
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if addrs[mid] <= a:
                lo = mid
            else:
                hi = mid - 1
        nm, ad = syms[lo]
        return nm if a == ad else '%s+0x%x' % (nm, a - ad)

    def read(va, ln):
        for off, base, sz in loads:
            if base <= va < base + sz:
                o = off + (va - base)
                return blob[o:o + ln]
        return None

    data = read(start, n * 4)
    if data is None:
        print('vaddr 0x%08x is in no LOAD segment' % start)
        return 1

    md = Cs(CS_ARCH_MIPS, CS_MODE_MIPS32 | CS_MODE_BIG_ENDIAN)
    print('=== %s  (0x%08x) ===' % (name_of(start) or what, start))
    pend = {}          # register -> high half of a lui, to resolve lui plus addiu
    for ins in md.disasm(data, start):
        extra = ''
        op = ins.op_str
        if ins.mnemonic == 'lui':
            try:
                r, v = op.split(',')
                pend[r.strip()] = int(v.strip(), 0) << 16
            except ValueError:
                pass
        elif ins.mnemonic in ('addiu', 'ori', 'lw', 'sw', 'lbu', 'lb', 'sb',
                              'lhu', 'lh', 'sh'):
            # either rX, imm(rBase) or rD, rS, imm
            try:
                if '(' in op:
                    imm = op.split(',')[-1].split('(')[0].strip()
                    base = op.split('(')[1].rstrip(')').strip()
                else:
                    imm = op.split(',')[-1].strip()
                    base = op.split(',')[-2].strip()
                v = int(imm, 0)
                if base in pend:
                    a = (pend[base] + v) & 0xffffffff
                    extra = '   ; 0x%08x %s' % (a, name_of(a) or '')
            except (ValueError, IndexError):
                pass
        if ins.mnemonic.startswith(('b', 'j')) and '0x' in op:
            try:
                t = int(op.split('0x')[-1].split()[0], 16)
                nm = name_of(t)
                if nm:
                    extra = '   ; %s' % nm
            except ValueError:
                pass
        print('  %08x  %-8s %s%s' % (ins.address, ins.mnemonic, op, extra))
    return 0


sys.exit(main())
