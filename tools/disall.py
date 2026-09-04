#!/usr/bin/env python3
"""Dumps the whole text segment of an ELF32 MIPS big endian file as disassembly.

Usage:  disall.py <elf> [output.asm]
"""
import struct
import sys

from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_BIG_ENDIAN


def main():
    path = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else None
    blob = open(path, 'rb').read()
    phoff = struct.unpack('>I', blob[28:32])[0]
    phnum = struct.unpack('>H', blob[44:46])[0]
    loads, gp = [], 0
    for i in range(phnum):
        e = blob[phoff + i * 32: phoff + (i + 1) * 32]
        t, off, va, _pa, fsz = struct.unpack('>IIIII', e[:20])
        if t == 1:
            loads.append((off, va, fsz))
        if t == 0x70000000:
            gp = struct.unpack('>I', blob[off + 0x14:off + 0x18])[0]

    off, va, sz = loads[0]
    md = Cs(CS_ARCH_MIPS, CS_MODE_MIPS32 | CS_MODE_BIG_ENDIAN)
    fh = open(out, 'w') if out else sys.stdout
    print('# gp = 0x%08x' % gp, file=fh)

    # The LOAD segment starts at the ELF header, not at code, and capstone STOPS at the
    # first byte it cannot decode. Without resuming after each gap only the opening
    # instructions come out: the first attempt produced 29 lines for a 76 KB text.
    def walk(data, base):
        i = 0
        while i < len(data):
            got = False
            for ins in md.disasm(data[i:], base + i):
                got = True
                yield ins
                i = ins.address - base + ins.size
            if not got:
                i += 4

    for ins in walk(blob[off:off + sz], va):
        extra = ''
        # resolve gp relative operands to a readable absolute address
        if '$gp' in ins.op_str:
            try:
                imm = ins.op_str.split(',')[-1].split('(')[0].strip()
                v = int(imm, 0)
                extra = '   ; gp%+d = 0x%08x' % (v, (gp + v) & 0xffffffff)
            except ValueError:
                pass
        print('%08x  %-8s %s%s' % (ins.address, ins.mnemonic, ins.op_str, extra), file=fh)
    if out:
        fh.close()
        print('wrote %s' % out)


main()
