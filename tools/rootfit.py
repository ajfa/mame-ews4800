#!/usr/bin/env python3
"""Fixes the 148 block overrun of the united root partition.

The installer works the root size out by ADDING the pieces it merges:

    unitedrootsize=\\
    `ignore expr ${rootsize} + ${homesize} + ${usrsize_0} + ${varsize_0}`

and with the sizes fmthard -p -c0 returns for this disk the sum overshoots:

    fmthard: Partition (0) specified as 1994700 blocks starting at 102000
             does not fit. The full disk contains 2096552 blocks.
    (102000 + 1994700 = 2096700 against 2096552, so 148 too many)

This is a cylinder rounding mismatch, NOT a disk that is too small: the formula is
computed to fill the disk, so making the disk bigger reproduces the overshoot at any size.
The sum is replaced by a SUBTRACTION with margin:

    unitedrootsize=`expr ${disksize_0} - ${swapsize} - ${stndsize} - 1000`

The span is located BY POSITION, from unitedrootsize= to the second backtick, and padded
with spaces to exactly the same number of bytes, so that nothing depends on literals that
get mangled passing through layers of quoting.
"""
import struct
import sys

ISO = sys.argv[1]
SECTOR = 2048
CDPROC = '/RAM/INST/BIN/INSTPROC.;1'
BACKTICK = bytes([0x60])
NEW = b'unitedrootsize=`expr ${disksize_0} - ${swapsize} - ${stndsize} - 1000`'


def iso_walk(raw, lba, size, prefix='', depth=0):
    if depth > 8:
        return
    off, end = lba * SECTOR, lba * SECTOR + size
    while off < end:
        length = raw[off]
        if length == 0:
            off = (off // SECTOR + 1) * SECTOR
            continue
        elba = struct.unpack_from('<I', raw, off + 2)[0]
        elen = struct.unpack_from('<I', raw, off + 10)[0]
        flags, nlen = raw[off + 25], raw[off + 32]
        name = raw[off + 33:off + 33 + nlen].decode('latin1')
        if name not in (chr(0), chr(1)):
            p = prefix + '/' + name
            yield p, elba, elen, flags
            if flags & 2:
                yield from iso_walk(raw, elba, elen, p, depth + 1)
        off += length


raw = open(ISO, 'rb').read()
pvd = 16 * SECTOR
rl = struct.unpack_from('<I', raw, pvd + 156 + 2)[0]
rs = struct.unpack_from('<I', raw, pvd + 156 + 10)[0]
for path, lba, ln, flags in iso_walk(raw, rl, rs):
    if path == CDPROC:
        base, clen = lba * SECTOR, ln
        break
else:
    sys.exit('could not find %s' % CDPROC)

data = raw[base:base + clen]
n = 0
with open(ISO, 'r+b') as f:
    start = 0
    while True:
        k = data.find(b'unitedrootsize=', start)
        if k < 0:
            break
        b1 = data.find(BACKTICK, k)
        b2 = data.find(BACKTICK, b1 + 1)
        span = b2 - k + 1
        if len(NEW) > span:
            sys.exit('does not fit: new=%d span=%d' % (len(NEW), span))
        f.seek(base + k)
        f.write(NEW + b' ' * (span - len(NEW)))
        print('replaced at offset %d (%d bytes)' % (k, span))
        n += 1
        start = k + 1

print('formulas replaced: %d' % n)
raw = open(ISO, 'rb').read()
d = raw[base:base + clen]
k = d.find(b'unitedrootsize=')
print('now reads: %r' % d[k:k + 90].decode('latin1'))
