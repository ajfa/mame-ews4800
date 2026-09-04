#!/usr/bin/env python3
# LANG-GATE-EXEMPT: this file names foreign text as data
"""Second pass over install.lua: the accented comment lines the word list did not catch.

The word gate missed these because they carry technical terms and accents rather than the
common words it looks for. That is a real hole, and check.sh now also refuses any non
ASCII in the tree, so a line like this cannot slip through again.

Usage:  translate_lua2.py <install.lua>
"""
import sys

LINES = {
 1:  '-- Installs UX/4800 to disk, driving the installer menu.',
 7:  '-- 0x10000000, which at 256 bytes per line and one bit per pixel is the console.',
 8:  '-- Convert it with fbpng.py.',
 35: '-- decide the buzzer. The softc is static, bcon_vs at 0x802bcff8, measured:',
 39: '-- And they go by PHYSICAL address: the CPU map in ews4800.cpp is physical',
 40: '-- (0x1e000000, 0x1fc00000, 0x10000000 and so on) and MAME MIPS3 translates BEFORE',
 41: '-- reaching the bus, so a watchpoint never sees a 0x8 or 0xA address. KSEG0 and',
 42: '-- KSEG1 are the SAME physical address here, and that is the only one that fires:',
 45: '-- nobody touches the physical one, so "it never fires" was a fault of the',
 46: '-- instrument, not of the machine.)',
 56: '    -- wpset takes the CONDITION before the action:',
 68: '-- EWS_BZTRAP=1: instead of waiting for someone to WRITE the field, watch',
 77: '    -- NOT NESTED: MAME misparses d@(d@X+N), it returned 0C0AB5F0 for gatype, which',
 151:'-- EWS_KEYFILE: the HOT key channel.',
 174:'    -- `!shot [label]`: screen dump ON DEMAND. Dumps used to go at fixed frame',
 259:'    -- EWS_BUZFIX repairs the kernel inconsistency that kills the machine',
 260:'    -- as soon as the installer beeps, and it beeps on any error.',
 262:'    -- Measured on the machine, not assumed:',
 267:'    -- reads softc[0x64], which NOBODY ever writes (the only kernel writer is',
 273:'    -- No address is invented and gatype is not touched, so the',
 276:'    -- root cause remains that we tell the kernel we are a /330.',
 337:'        -- "@port/field" presses an ioport field (function keys have no',
 338:'        -- character, so they cannot go through the natural keyboard)',
}


def main():
    p = sys.argv[1]
    lines = open(p, encoding='utf-8', errors='replace').read().split('\n')
    done = 0
    for n, new in sorted(LINES.items()):
        i = n - 1
        if i < len(lines) and lines[i].lstrip().startswith('--'):
            lines[i] = new
            done += 1
        else:
            print('    SKIPPED %d: not a comment line, %r' % (n, lines[i][:50]))
    open(p, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines))
    print('%s: %d lines replaced' % (p, done))


main()
