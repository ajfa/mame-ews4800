#!/usr/bin/env python3
"""Compares the nine CD kernels on what decides the graphics adapter.

For each one:
  - whether it carries nec_ctlr_bcon_* controllers, the node vmunix.01 lacks
  - which ga_base sbd_init gives itself, the lui immediate
  - how far up kseg2 setup_kptbl maps, the ceiling

In vmunix.01 the ceiling lands exactly where ga_base begins, so [ga_base + 0xF00E00] is
unmappable by construction. What this looks for is a kernel where that is not the case.
The answer is that the three kernels which do carry adapter nodes are PCI machines and do
not contain 0xD0000000 at all.

The ga_base and ceiling columns are heuristics over instruction patterns and can miss.
Treat the controller column as the reliable one and confirm the rest with kdis.py.

Usage:  gacmp.py <vmunix> [more...]
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
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


def read_at(blob, loads, va, n):
    for off, base, sz in loads:
        if base <= va < base + sz:
            o = off + (va - base)
            return blob[o:o + n]
    return None


def find_lui(blob, loads, start, n, after_imm):
    """Immediate of the first lui seen after an addiu at, zero, after_imm."""
    data = read_at(blob, loads, start, n * 4)
    if not data:
        return None
    seen = False
    for i in range(0, len(data) - 4, 4):
        w = struct.unpack('>I', data[i:i + 4])[0]
        # addiu $at, $zero, imm  ->  op 0x09, rs 0, rt 1
        if (w >> 26) == 0x09 and ((w >> 21) & 0x1f) == 0 and ((w >> 16) & 0x1f) == 1 \
                and (w & 0xffff) == after_imm:
            seen = True
        if seen and (w >> 26) == 0x0f:          # lui
            return w & 0xffff
    return None


def main():
    print('%-12s %-22s %-14s %s' % ('kernel', 'bcon ctlr', 'ga_base', 'kseg2 ceiling'))
    for path in sys.argv[1:]:
        blob = open(path, 'rb').read()
        loads = segments(blob)
        syms = {s[0]: s[1] for s in load_syms(path) if s[1]}

        ctlrs = sorted(n for n in syms if n.startswith('nec_ctlr_bcon'))
        ctlr_txt = ('%d: %s' % (len(ctlrs), ctlrs[0])) if ctlrs else 'NONE'

        ga = None
        if 'sbd_init' in syms:
            hi = find_lui(blob, loads, syms['sbd_init'], 400, 0x101e)
            if hi is not None:
                ga = hi << 16

        ceiling = None
        if 'setup_kptbl' in syms:
            data = read_at(blob, loads, syms['setup_kptbl'], 120 * 4)
            if data:
                for i in range(0, len(data) - 8, 4):
                    w = struct.unpack('>I', data[i:i + 4])[0]
                    w2 = struct.unpack('>I', data[i + 4:i + 8])[0]
                    # lui $at, hi ; ori $at, $at, lo
                    if (w >> 26) == 0x0f and ((w >> 16) & 0x1f) == 1 \
                            and (w2 >> 26) == 0x0d and ((w2 >> 21) & 0x1f) == 1:
                        ceiling = ((w & 0xffff) << 16) | (w2 & 0xffff)
                        break

        print('%-12s %-22s %-14s %s'
              % (os.path.basename(path), ctlr_txt,
                 ('0x%08x' % ga) if ga is not None else '?',
                 ('0x%08x' % ceiling) if ceiling is not None else '?'))


main()
