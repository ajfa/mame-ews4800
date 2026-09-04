#!/usr/bin/env python3
"""Writes a COPY of the UX/4800 ISO with the licence check open.

The history matters, because the wrong answer looked right. /inst/etc/instproc, inside
RAMFILSY, has an UnlockCheck and a MenuCheckLock that LOOK like the gate, and the first
two attempts patched them. Measured: it changes nothing. That the patch does reach the
machine was proved separately by putting a visible marker in its banner, which appeared on
screen, so the file does run, it is simply not the one that shows the warning.

The one that shows it is the FMLI installer, which instproc starts in FmliInstall:

    ${RAMROOT}/inst/bin/instproccdrom      with  RAMROOT="/cdrom/ram"

that is /RAM/INST/BIN/INSTPROC. ON THE CD ITSELF, another 66474 byte script with its own
copy of UnlockCheck and MenuCheckLock and a MakeErrfile chlock1 that is literally the
warning.

The body of ITS UnlockCheck is replaced by a fixed echo of the same byte count. Nothing is
recompressed: ISO 9660 carries no checksums over the data, so overwriting in place leaves
a valid image.

The licence check is a floppy disk validated against model and machine id, not a technical
step. Opening it here is for running the system under emulation.

Usage:  mkunlockiso3.py <source iso> <output iso> [--marker]
"""
import os
import shutil
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ufsls import Ufs  # noqa: E402

RAMFILSY_LBA, RAMFILSY_SIZE, SECTOR = 332, 3145728, 2048
CDPROC = '/RAM/INST/BIN/INSTPROC.;1'

START = b'> /inst/etc/unlock.unum'
END = b'done < ${PART}/Ubkataban'
LINE = b'echo "3010 multi WSOS-license-71M" > /inst/etc/unlock.unum\n: '


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
        if name not in ('\x00', '\x01'):
            path = prefix + '/' + name
            yield path, elba, elen, flags
            if flags & 2:
                yield from iso_walk(raw, elba, elen, path, depth + 1)
        off += length


def find_iso_file(raw, want):
    pvd = 16 * SECTOR
    rl = struct.unpack_from('<I', raw, pvd + 156 + 2)[0]
    rs = struct.unpack_from('<I', raw, pvd + 156 + 10)[0]
    for path, lba, ln, flags in iso_walk(raw, rl, rs):
        if path == want:
            return lba * SECTOR, ln
    sys.exit('no encontre %s en el ISO' % want)


def pad_to(body, n):
    if len(body) > n:
        sys.exit('el reemplazo no cabe: %d > %d' % (len(body), n))
    out, pad = [body], n - len(body)
    while pad > 0:
        if pad == 1:
            out.append(b'\n')
            pad = 0
        else:
            chunk = min(pad, 72)
            out.append(b'\n#' + b'x' * (chunk - 2))
            pad -= chunk
    rep = b''.join(out)
    return (rep + b'x' * (n - len(rep)))[:n]


def main():
    iso_in, iso_out = sys.argv[1], sys.argv[2]
    marker = '--marker' in sys.argv
    if os.path.exists(iso_out):
        sys.exit('ya existe %s -- no lo piso' % iso_out)
    print('copiando %s -> %s' % (iso_in, iso_out))
    shutil.copyfile(iso_in, iso_out)

    with open(iso_out, 'r+b') as f:
        raw = f.read()

        # ---- 1) el instalador de FMLI, que vive PLANO en el ISO -------------
        base, ln = find_iso_file(raw, CDPROC)
        data = bytearray(raw[base:base + ln])
        i0 = data.index(START)
        i1 = data.index(END, i0) + len(END)
        print('instproccdrom: LBA byte %d, tramo %d..%d (%d bytes)'
              % (base, i0, i1, i1 - i0))
        rep = pad_to(LINE, i1 - i0)
        f.seek(base + i0)
        f.write(rep)

        # ---- 2) visible marker, to know THIS file is the one that runs ----
        if marker:
            mold = b'UX/4800 INSTALL PROCEDURE'
            mnew = b'UX/4800 INSTALL (PATCHED)'
            assert len(mold) == len(mnew)
            j, n = data.find(mold), 0
            while j >= 0:
                f.seek(base + j)
                f.write(mnew)
                n += 1
                j = data.find(mold, j + 1)
            print('marca puesta en %d sitios' % n)

    # ---- verificacion independiente -------------------------------------
    raw = open(iso_out, 'rb').read()
    base, ln = find_iso_file(raw, CDPROC)
    d = raw[base:base + ln]
    k = d.index(b'UnlockCheck()')
    print('\n--- UnlockCheck of the FMLI installer, in the output ISO ---')
    print(d[k:k + 200].decode('latin1'))
    print('  tamano: %d (debe seguir siendo 66474)' % ln)

    # y que RAMFILSY sigue intacto y legible
    fs = Ufs(raw[RAMFILSY_LBA * SECTOR:RAMFILSY_LBA * SECTOR + RAMFILSY_SIZE])
    print('  RAMFILSY sigue montable: /inst/etc/instproc = %d bytes'
          % len(fs.read(fs.lookup('/inst/etc/instproc'))))


main()
