#!/usr/bin/env python3
"""Parse the .unixsyms section the CD's EWS-UX kernels carry.

Layout (worked out from vmunix.01):
    header at the section start
        +0x00  pointer to the first symbol entry   (section addr + 0x40)
        +0x04  size
        +0x10  pointer to the string table
        ...
    entries, 16 bytes each: [name_off:4][value:4][size:4][info:4]
    strings, NUL-separated, indexed by name_off

Usage:
    unixsyms.py <vmunix> [regex]      list symbols (optionally filtered)
    unixsyms.py <vmunix> --addr 0xVA  nearest symbol to an address
"""
import re
import struct
import sys


def load(path):
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
        raise SystemExit('no .unixsyms')

    def foff(va):
        return off + (va - addr)

    first, _, _, _, strtab = struct.unpack_from('>IIIII', raw, off)
    syms = []
    p = foff(first)
    end = foff(strtab)
    while p + 16 <= end:
        name_off, value, size, info = struct.unpack_from('>IIII', raw, p)
        p += 16
        if not name_off:
            continue
        b = foff(strtab) + name_off
        e = raw.index(b'\0', b)
        syms.append((raw[b:e].decode('latin1'), value, size, info))
    return syms


def main():
    syms = load(sys.argv[1])
    if len(sys.argv) > 2 and sys.argv[2] == '--addr':
        target = int(sys.argv[3], 0)
        best = max((s for s in syms if s[1] <= target),
                   key=lambda s: s[1], default=None)
        if best:
            print(f'{target:#010x} = {best[0]}+{target - best[1]:#x} '
                  f'(sym {best[1]:#010x} size {best[2]:#x})')
        return
    pat = re.compile(sys.argv[2], re.I) if len(sys.argv) > 2 else None
    n = 0
    for name, value, size, info in syms:
        if pat and not pat.search(name):
            continue
        print(f'  {value:08x}  size {size:6d}  {name}')
        n += 1
    print(f'{n} de {len(syms)} símbolos')


main()
