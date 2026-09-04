#!/usr/bin/env python3
"""Finds ELF headers around an offset inside a disk or CD image.

Used to locate the start of the binary a string belongs to, once grep -abo has found the
string itself.

Usage:  findelf.py <image> <offset> [window]
"""
import sys


def main():
    path = sys.argv[1]
    off = int(sys.argv[2], 0)
    win = int(sys.argv[3], 0) if len(sys.argv) > 3 else 2 * 1024 * 1024

    start = max(0, off - win)
    with open(path, 'rb') as f:
        f.seek(start)
        buf = f.read(win + 65536)

    hits = []
    i = 0
    while True:
        i = buf.find(b'\x7fELF', i)
        if i < 0:
            break
        hits.append(start + i)
        i += 4

    print('ELF headers between %d and %d:' % (start, start + len(buf)))
    for h in hits:
        rel = off - h
        mark = '  <-- %d bytes before the target' % rel if 0 < rel < 0x200000 else ''
        print('  %d  (0x%x)%s' % (h, h, mark))
    if not hits:
        print('  none')


main()
