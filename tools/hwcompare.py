#!/usr/bin/env python3
"""Compares the nine kernels on the CD by hardware divergence.

For each vmunix.NN:
  (a) the I/O map it expects: a histogram of the lui rX, 0xXXXX instructions whose
      immediate lands in device KSEG1, 0xa000 to 0xbfff, grouped by 16 MB
      window, with the symbol that contains the instruction;
  (b) which graphics, console and keyboard symbols are present.

Usage:  hwcompare.py <kernel dir> [--io | --gfx | --detail NN]
"""
import os
import re
import struct
import sys


def load_syms(path):
    """Copy of the .unixsyms parser; unixsyms.py runs main() when imported."""
    raw = open(path, 'rb').read()
    (_, _, _, _, _, e_shoff, _, _, _, _, e_shentsize, e_shnum,
     e_shstrndx) = struct.unpack_from('>HHIIIIIHHHHHH', raw, 16)
    secs = [struct.unpack_from('>IIIIIIIIII', raw, e_shoff + i * e_shentsize)
            for i in range(e_shnum)]
    strh = secs[e_shstrndx]

    def nm(o):
        b = strh[4] + o
        return raw[b:raw.index(b'\0', b)].decode()

    for s in secs:
        if nm(s[0]) == '.unixsyms':
            off, addr = s[4], s[3]
            break
    else:
        return []

    first, _, _, _, strtab = struct.unpack_from('>IIIII', raw, off)
    syms = []
    p = off + (first - addr)
    end = off + (strtab - addr)
    while p + 16 <= end:
        name_off, value, size, info = struct.unpack_from('>IIII', raw, p)
        p += 16
        if not name_off:
            continue
        b = end + name_off
        e = raw.index(b'\0', b)
        syms.append((raw[b:e].decode('latin1'), value, size, info))
    return syms

# canonical machine id by file index, from the table at 0x80191a80
IDX2ID = {0: 0x1010, 1: 0x101e, 2: 0x1011, 3: 0x1017, 4: 0x1027,
          5: 0x1028, 6: 0x1029, 7: 0x1030, 8: 0x1032}

GFX_RE = re.compile(
    r'(fb|frame_?buf|grf|graph|bitmap|bm_|blit|vram|crt|video|pixel|plane|'
    r'lut|colormap|cmap|dac|bt4|bt45|bt47|kbd|keyboard|mouse|ps2|wskbd|'
    r'cons|tty0|screen|disp)', re.I)


def sections(raw):
    (e_shoff,) = struct.unpack_from('>I', raw, 32)
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from('>HHH', raw, 46)
    secs = [struct.unpack_from('>IIIIIIIIII', raw, e_shoff + i * e_shentsize)
            for i in range(e_shnum)]
    strh = secs[e_shstrndx]

    def nm(o):
        b = strh[4] + o
        return raw[b:raw.index(b'\0', b)].decode()
    return [(nm(s[0]), s[3], s[4], s[5], s[1]) for s in secs]  # name,addr,off,size,type


def text_segs(raw):
    out = []
    for name, addr, off, size, typ in sections(raw):
        if typ != 1 or not addr or not size:      # SHT_PROGBITS with an address
            continue
        if name not in ('.text', '.init', '.fini'):
            continue
        out.append((addr, raw[off:off + size]))
    if not out:                                    # fallback: every PROGBITS
        for name, addr, off, size, typ in sections(raw):
            if typ == 1 and addr and size:
                out.append((addr, raw[off:off + size]))
    return out


def symtab(path):
    syms = sorted(load_syms(path), key=lambda s: s[1])
    addrs = [s[1] for s in syms]
    return syms, addrs


def nearest(syms, addrs, va):
    import bisect
    i = bisect.bisect_right(addrs, va) - 1
    if i < 0:
        return '?'
    return syms[i][0]


def scan_io(raw):
    """lui rX, imm with imm in 0xa000..0xbfff -> {16M window: [(va, imm)]}"""
    hits = []
    for base, data in text_segs(raw):
        n = len(data) // 4
        w = struct.unpack(f'>{n}I', data[:n * 4])
        for i in range(n):
            x = w[i]
            if (x >> 26) != 0x0F:                  # lui
                continue
            imm = x & 0xFFFF
            if not (0xa000 <= imm <= 0xffff):
                continue
            hits.append((base + i * 4, imm << 16))
    return hits


def main():
    d = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else '--all'
    only = sys.argv[3] if len(sys.argv) > 3 else None

    for idx in range(9):
        nn = f'{idx:02d}'
        if only and only != nn:
            continue
        path = os.path.join(d, f'vmunix.{nn}')
        if not os.path.exists(path):
            continue
        raw = open(path, 'rb').read()
        syms, addrs = symtab(path)
        mid = IDX2ID[idx]
        print(f'\n{"="*72}\n=== vmunix.{nn}   machine id 0x{mid:04x}   '
              f'({len(raw)} B, {len(syms)} simbolos)\n{"="*72}')

        if mode in ('--all', '--io'):
            hits = scan_io(raw)
            win = {}
            for va, phys in hits:
                k = phys & 0xFFF00000            # 1 MB window
                win.setdefault(k, []).append(va)
            print(f'  -- I/O map ({len(hits)} device lui, '
                  f'{len(win)} windows of 1MB) --')
            for k in sorted(win):
                vas = win[k]
                names = sorted({nearest(syms, addrs, v) for v in vas})
                shown = ' '.join(names[:8]) + (' ...' if len(names) > 8 else '')
                print(f'   0x{k:08x}  x{len(vas):-4d}  {shown}')

        if mode in ('--all', '--gfx'):
            g = sorted({s[0] for s in syms if GFX_RE.search(s[0])})
            print(f'  -- graphics, console and keyboard symbols ({len(g)}) --')
            for i in range(0, len(g), 6):
                print('     ' + '  '.join(f'{x:<20}' for x in g[i:i + 6]))


if __name__ == '__main__':
    main()
