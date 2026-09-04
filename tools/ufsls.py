#!/usr/bin/env python3
"""Reader for the big endian UFS of RAMFILSY, SVR4 on MIPS.

Nothing has to be mounted: the super block sits at 0x2000, magic 0x00011954
at +0x55C, and the inodes are UFS1: size at +8, direct blocks at +40.
Directory entries carry a 16 bit namlen (SVR4), not the u8 plus type of BSD.

Usage:
  ufsls.py <img> [path]                lists a directory, / by default
  ufsls.py <img> --cat <path>          writes the file to standard output
  ufsls.py <img> --map <path>          says at which offsets IN THE IMAGE each
                                       block of the file lives
  ufsls.py <img> --find <pattern>      searches the whole tree by name
  ufsls.py <img> --grep <text> [...]   says WHICH file contains each string
"""
import struct
import sys


class Ufs:
    def __init__(self, raw, sb=0x2000):
        self.raw = raw
        u = lambda o: struct.unpack_from('>i', raw, sb + o)[0]
        assert struct.unpack_from('>I', raw, sb + 0x55c)[0] == 0x11954, 'not UFS'
        self.iblkno, self.bsize, self.fsize = u(16), u(48), u(52)
        self.frag, self.cgoffset, self.cgmask = u(56), u(24), u(28)
        self.fpg, self.ipg, self.ncg = u(188), u(184), u(44)
        self.nindir = u(116)

    def cgstart(self, c):
        return self.fpg * c + self.cgoffset * (c & ~self.cgmask)

    def inode(self, ino):
        c, i = divmod(ino, self.ipg)
        off = (self.cgstart(c) + self.iblkno) * self.fsize + i * 128
        r = self.raw
        mode, nlink = struct.unpack_from('>HH', r, off)
        size = struct.unpack_from('>Q', r, off + 8)[0]
        db = list(struct.unpack_from('>12i', r, off + 40))
        ib = list(struct.unpack_from('>3i', r, off + 88))
        return mode, nlink, size, db, ib

    def blocks(self, ino):
        """List of (offset in image, length) for the blocks of the file."""
        mode, nlink, size, db, ib = self.inode(ino)
        out, left = [], size
        for b in db:
            if left <= 0:
                break
            n = min(left, self.bsize)
            out.append((b * self.fsize, n) if b else (None, n))
            left -= n
        if left > 0 and ib[0]:
            ptrs = struct.unpack_from('>%di' % self.nindir, self.raw,
                                      ib[0] * self.fsize)
            for b in ptrs:
                if left <= 0:
                    break
                n = min(left, self.bsize)
                out.append((b * self.fsize, n) if b else (None, n))
                left -= n
        if left > 0 and ib[1]:
            l1 = struct.unpack_from('>%di' % self.nindir, self.raw,
                                    ib[1] * self.fsize)
            for b1 in l1:
                if left <= 0 or not b1:
                    break
                ptrs = struct.unpack_from('>%di' % self.nindir, self.raw,
                                          b1 * self.fsize)
                for b in ptrs:
                    if left <= 0:
                        break
                    n = min(left, self.bsize)
                    out.append((b * self.fsize, n) if b else (None, n))
                    left -= n
        return out, size

    def read(self, ino):
        blks, size = self.blocks(ino)
        data = b''.join(self.raw[o:o + n] if o else b'\0' * n for o, n in blks)
        return data[:size]

    def readdir(self, ino):
        data = self.read(ino)
        off, out = 0, []
        while off + 8 <= len(data):
            d_ino, reclen, namlen = struct.unpack_from('>IHH', data, off)
            if reclen < 8 or off + reclen > len(data):
                break
            name = data[off + 8:off + 8 + namlen].split(b'\0')[0].decode('latin1')
            if d_ino:
                out.append((name, d_ino))
            off += reclen
        return out

    def lookup(self, path):
        ino = 2
        for part in [p for p in path.split('/') if p]:
            for name, i in self.readdir(ino):
                if name == part:
                    ino = i
                    break
            else:
                raise KeyError(path + '  (fails at "%s")' % part)
        return ino

    def walk(self, ino=2, prefix=''):
        for name, i in self.readdir(ino):
            if name in ('.', '..'):
                continue
            mode = self.inode(i)[0]
            p = prefix + '/' + name
            yield p, i, mode
            if (mode & 0xf000) == 0x4000:
                yield from self.walk(i, p)


def main():
    raw = open(sys.argv[1], 'rb').read()
    fs = Ufs(raw)
    a = sys.argv[2:]
    if a and a[0] == '--cat':
        sys.stdout.buffer.write(fs.read(fs.lookup(a[1])))
    elif a and a[0] == '--map':
        ino = fs.lookup(a[1])
        blks, size = fs.blocks(ino)
        print('%s  inode %d  %d bytes' % (a[1], ino, size))
        for o, n in blks:
            print('   image 0x%08x  %d bytes' % (o, n) if o else '   HOLE %d' % n)
    elif a and a[0] == '--grep':
        pats = [p.encode('latin1').decode('unicode_escape').encode('latin1')
                for p in a[1:]]
        for p, i, mode in fs.walk():
            if (mode & 0xf000) != 0x8000:
                continue
            try:
                d = fs.read(i)
            except Exception:
                continue
            hits = [(pt, d.find(pt)) for pt in pats if pt in d]
            if hits:
                print('%-46s %8d  %s' % (p, len(d),
                      ' '.join('%s@0x%x' % (h[0][:20], h[1]) for h in hits)))
    elif a and a[0] == '--find':
        for p, i, mode in fs.walk():
            if a[1].lower() in p.lower():
                print('%-60s inodo %-6d modo %06o  %d bytes'
                      % (p, i, mode, fs.inode(i)[2]))
    else:
        path = a[0] if a else '/'
        for name, i in fs.readdir(fs.lookup(path)):
            mode, nlink, size, _db, _ib = fs.inode(i)
            kind = 'd' if (mode & 0xf000) == 0x4000 else ('l' if (mode & 0xf000) == 0xa000 else '-')
            print('%s%06o %-24s inodo %-6d %10d' % (kind, mode & 0o7777, name, i, size))


if __name__ == '__main__':
    main()
