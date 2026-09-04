#!/usr/bin/env python3
"""Suppresses the spurious /home3 to /home7 partitions, and restores the fmthard call.

Measured: on a 1 GB disk with the united partition type, the installer generates a vtocinfo
whose first SIX lines are correct, root, swap, stand, save, backup and boot, and then adds
five lines of rubbish:

    b  0  00  6286800   4190100  ufs  /home3     <- base OUTSIDE the disk
    c  0  00  <empty>   4190100  ufs  /home4     <- EMPTY base, so six fields
    d/e/f  the same

The empty base is what breaks fmthard -l -s with "Syntax error": the line has six fields
instead of seven. The emptiness comes from homeNbase=`ignore expr ...`, where ignore
swallows the failure of expr and returns an empty string.

This disables the `if [ ${homeNsize} -gt 0 ]` guards for home3 to home7, replacing the
variable with a padded zero so the byte count is unchanged, which stops those lines being
emitted and leaves the vtocinfo with the six good ones.
"""
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ufsls import Ufs

ISO = sys.argv[1]
BASE, SZ, SECTOR = 332 * 2048, 3145728, 2048
CDPROC = '/RAM/INST/BIN/INSTPROC.;1'


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

# ---- 1) restore fmthard in the instproc inside RAMFILSY --------------------
fs = Ufs(raw[BASE:BASE + SZ])
ino = fs.lookup('/inst/etc/instproc')
blks, _ = fs.blocks(ino)
data = fs.read(ino)
SCAT = b'scat ${CDPAR}/vtocinfo' + b' ' * 20
FMT = b'fmthard -l -s ${CDPAR}/vtocinfo  ${RSIX_0}'
assert len(SCAT) == len(FMT)
j = data.find(SCAT)
with open(ISO, 'r+b') as f:
    if j >= 0:
        pos = 0
        for boff, blen in blks:
            if pos <= j < pos + blen:
                f.seek(BASE + boff + (j - pos))
                f.write(FMT)
                print('fmthard restored')
                break
            pos += blen
    else:
        print('fmthard was already there, no scat found')

# ---- 2) disable the home3 to home7 guards in the INSTPROC on the CD --------
raw = open(ISO, 'rb').read()
for path, lba, ln, flags in iso_walk(raw, *(lambda p: (struct.unpack_from('<I', raw, p + 156 + 2)[0],
                                                       struct.unpack_from('<I', raw, p + 156 + 10)[0]))(16 * SECTOR)):
    if path == CDPROC:
        cbase, clen = lba * SECTOR, ln
        break
else:
    sys.exit('could not find %s' % CDPROC)

cdata = bytearray(raw[cbase:cbase + clen])
total = 0
with open(ISO, 'r+b') as f:
    for n in (3, 4, 5, 6, 7):
        old = ('if [ ${home%dsize} -gt 0 ] ; then' % n).encode()
        new = ('if [ 0%s -gt 0 ] ; then' % (' ' * 11)).encode()
        assert len(old) == len(new), (len(old), len(new))
        start = 0
        while True:
            k = cdata.find(old, start)
            if k < 0:
                break
            f.seek(cbase + k)
            f.write(new)
            total += 1
            start = k + 1
print('guards disabled: %d (10 expected)' % total)

# ---- verification ---------------------------------------------------------
raw = open(ISO, 'rb').read()
d = raw[cbase:cbase + clen]
print('  home3 to home7 guards still active: %d'
      % sum(d.count(('if [ ${home%dsize} -gt 0 ]' % n).encode()) for n in (3, 4, 5, 6, 7)))
print('  home2 untouched: %d' % d.count(b'if [ ${home2size} -gt 0 ]'))
fs = Ufs(raw[BASE:BASE + SZ])
print('  instproc: %d bytes, fmthard present: %s'
      % (len(fs.read(fs.lookup('/inst/etc/instproc'))),
         FMT in fs.read(fs.lookup('/inst/etc/instproc'))))
