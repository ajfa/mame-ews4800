#!/usr/bin/env python3
"""Dumps bcon_keytabl from a kernel: the key code to character map.

This is the table the guest uses to translate what the keyboard sends, so it is the truth
about which code has to be sent for each character. Only digits, letters, space and return
had been measured; the punctuation was assigned by analogy and came out wrong.

Six bytes per entry, indexed by code. The columns are the modifier variants, unshifted,
shifted, control and so on. All of them are printed and the data is left to say which is
which.

Check which kernel you are reading. The installed system and the one on the CD do not
carry the same table, and reading the wrong one produces a key map that looks right and
types the wrong characters.

Usage:  keytabl.py <vmunix> [symbol|0xaddress] [entries]
"""
import struct
import sys

sys.path.insert(0, __file__.rsplit('/', 1)[0] if '/' in __file__ else '.')
from hwcompare import load_syms  # noqa: E402


def main():
    path = sys.argv[1]
    what = sys.argv[2] if len(sys.argv) > 2 else 'bcon_keytabl'
    n = int(sys.argv[3], 0) if len(sys.argv) > 3 else 0x80

    blob = open(path, 'rb').read()
    phoff = struct.unpack('>I', blob[28:32])[0]
    phnum = struct.unpack('>H', blob[44:46])[0]
    loads = []
    for i in range(phnum):
        e = blob[phoff + i * 32: phoff + (i + 1) * 32]
        t, off, va, _pa, fsz = struct.unpack('>IIIII', e[:20])
        if t == 1:
            loads.append((off, va, fsz))

    if what.startswith('0x'):
        base = int(what, 16)
    else:
        base = None
        for s in load_syms(path):
            if s[0] == what:
                base = s[1]
                break
        if base is None:
            print('no such symbol %r' % what)
            return 1

    def rd(va, ln):
        for off, b, sz in loads:
            if b <= va < b + sz:
                o = off + (va - b)
                return blob[o:o + ln]
        return None

    data = rd(base, n * 6)
    if data is None:
        print('0x%08x is outside every LOAD' % base)
        return 1

    print('%s = 0x%08x, %d entries of 6 bytes' % (what, base, n))
    print('code    bytes            as text')
    for i in range(n):
        e = data[i * 6:(i + 1) * 6]
        if len(e) < 6 or not any(e):
            continue
        txt = ''.join(chr(c) if 32 <= c < 127 else '.' for c in e)
        print('  0x%02x  %s  %s' % (i, e.hex(), txt))
    return 0


sys.exit(main())
