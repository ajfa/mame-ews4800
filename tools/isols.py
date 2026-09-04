#!/usr/bin/env python3
"""Walks the whole ISO 9660 tree of the UX/4800 CD, and extracts files from it.

Listing only the root is not enough: the real installer lives in subdirectories, and so do
the nine kernels, which is what makes it possible to compare them.

Usage:  isols.py <iso> [--find <pattern>] [--extract <path> <output>]
"""
import struct
import sys


def dir_entries(raw, lba, size):
    off, end = lba * 2048, lba * 2048 + size
    while off < end:
        length = raw[off]
        if length == 0:
            off = (off // 2048 + 1) * 2048
            continue
        ext_lba = struct.unpack_from('<I', raw, off + 2)[0]
        ext_len = struct.unpack_from('<I', raw, off + 10)[0]
        flags = raw[off + 25]
        nlen = raw[off + 32]
        name = raw[off + 33:off + 33 + nlen].decode('latin1')
        if name not in (chr(0), chr(1)):
            yield name, ext_lba, ext_len, flags
        off += length


def walk(raw, lba, size, prefix='', depth=0):
    if depth > 8:
        return
    for name, elba, elen, flags in dir_entries(raw, lba, size):
        path = prefix + '/' + name
        yield path, elba, elen, flags
        if flags & 2:
            yield from walk(raw, elba, elen, path, depth + 1)


def main():
    raw = open(sys.argv[1], 'rb').read()
    pvd = 16 * 2048
    assert raw[pvd + 1:pvd + 6] == b'CD001'
    root_lba = struct.unpack_from('<I', raw, pvd + 156 + 2)[0]
    root_len = struct.unpack_from('<I', raw, pvd + 156 + 10)[0]

    if '--extract' in sys.argv:
        i = sys.argv.index('--extract')
        want, out = sys.argv[i + 1], sys.argv[i + 2]
        for path, lba, ln, flags in walk(raw, root_lba, root_len):
            if path.upper().rstrip(';1') == want.upper().rstrip(';1') or path == want:
                open(out, 'wb').write(raw[lba * 2048:lba * 2048 + ln])
                print('%s -> %s (%d bytes, LBA %d, byte %d)'
                      % (path, out, ln, lba, lba * 2048))
                return
        print('not found: %s' % want)
        return

    pat = None
    if '--find' in sys.argv:
        pat = sys.argv[sys.argv.index('--find') + 1].lower()

    for path, lba, ln, flags in walk(raw, root_lba, root_len):
        if pat and pat not in path.lower():
            continue
        kind = 'DIR ' if flags & 2 else '    '
        print('  %s%-52s LBA %-8d %10d' % (kind, path, lba, ln))


main()
