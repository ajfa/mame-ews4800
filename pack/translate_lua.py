#!/usr/bin/env python3
# LANG-GATE-EXEMPT: this file names foreign text as data
"""Translates install.lua line by line, by line NUMBER.

Line targeted rather than a rewrite: install.lua is the working harness, it drives every
run, and rewriting working code to change its comments would risk a bug for no gain. Each
entry replaces one whole line, and the script refuses to touch a line whose current text
does not contain the expected fragment, so a shifted file is reported instead of being
corrupted.

Usage:  translate_lua.py <install.lua>
"""
import sys

# line number: (fragment that must be present, replacement line)
LINES = {
 3:  ('EWS_KEYS', '--   EWS_KEYS  = "frame:text;frame:text;..."  what to type and when'),
 4:  ('EWS_SHOTS', '--   EWS_SHOTS = "f1,f2,..."                   frames to dump the screen at'),
 6:  ('fvtags', '-- The screen dump goes to fvtags/fb<frame>.bin, 2 MB from physical'),
 21: ('etapas', '-- keyboard stages, to separate "the key never arrives" from "the installer ignores it"'),
 34: ('watchpoints', '-- Watchpoints (EWS_BZWATCH=1) on the two bcon softc fields that'),
 48: ('velocidad', '-- They cost about 3x in speed because the field lives in main RAM and force'),
 49: ('escritura', '-- every write to be checked, so they are ARMED LATE: EWS_BZWATCH_AT, default'),
 50: ('9000', '-- 9000, already measured with buzz=0, leaves the boot running at full speed.'),
 59: ('watchpoint', '    -- the watchpoint is installed but silent, which is what used to happen.'),
 69: ('pitido', '-- what the buzzer routine itself READS, exactly where it blows up.'),
 71: ('80029908', '--   80029908  lw t1,100(t0)      ; t1 = softc[0x64]  <- the one that reads FF000000'),
 72: ('80029910', '--   80029910  sh zero,0(t1)      ; fails here, in the delay slot'),
 73: ('EXPRESIONES', '-- Registered through MEMORY EXPRESSIONS (d@, which the debugger treats as'),
 74: ('virtual', '-- virtual) rather than register names, so it does not depend on how MAME'),
 75: ('breakpoint', '-- names t0 and t1 on MIPS3. A breakpoint costs nothing until it fires.'),
 78: ('CONSTANTE', '    -- is a word of code). Since bcon is CONSTANT and already measured'),
 79: ('0x802bcff8', '    -- (0x802bcff8 = bcon_vs), the fields are read at literal addresses:'),
 85: ('bcon_buzinit', '    -- and the same field on the way out of bcon_buzinit, to see what it really set'),
 91: ('grifo', '-- The SCSI tap USED TO BE HERE and was removed. install_write_tap'),
 92: ('64 bits', '-- from Lua does not work on this machine: the r4000 space is 64 bit, the'),
 93: ('mascara', '-- first mask is 0xff00000000000000 and sol2 raises "integer value will be'),
 100:('teclas', '-- key script'),
 116:('tecla en', 'for f, t in pairs(KEYS) do print(string.format("  key at %d: %q", f, t)) end'),
 119:('DONDE', '-- to find out WHERE the time goes when the machine advances but slowly:'),
 121:('magnitud', '-- orders of magnitude more than it would cost on the real machine, so either'),
 155:('SIGTERM', '-- answers neither SIGTERM nor SIGINT, so the only way out was to kill it. With'),
 156:('linea', '-- this, writing one line into the file from outside is enough.'),
 176:('shell', '    -- an interactive shell: you have to look AFTER each command, and there is no'),
 198:('caliente', '    print(string.format("[frame %d] hot key %q: %s", _G.frames, first,'),
 244:('volcada', '    print(string.format("[frame %s] screen dumped (%d lit samples)", tag, nz))'),
 252:('zumbador', '    -- arm the buzzer watchpoints when the time comes'),
 264:('clase', '    -- that is: for OUR machine class (14) the kernel installs the buzzer at'),
 266:('clase 14', '    -- stays 0 because class 14 without a node never assigns it, and type 0'),
 268:('bcon_buzinit', '    -- bcon_buzinit+0x50, and only for classes 1 to 4). Result: garbage'),
 269:('0xFF000000', '    -- 0xFF000000 -> TLB fault -> PANIC.'),
 271:('softc', '    -- softc[0x64] is given the address the kernel itself installed for'),
 272:('0xBE4A0050', '    -- this machine (0xBE4A0050, physical 0x3E4A0050, ALREADY MAPPED in ews4800.cpp'),
 275:('reparacion', '    -- works. It is a repair of the rig, not a claim about the hardware:'),
 293:('TEXTO', '    -- The PC is read as TEXT, not through .value.'),
 295:('64 bits', '    -- cpu.state["PC"].value returns the 64 bit PC, and for any kernel or ROM'),
 296:('direccion', '    -- address that is 0xFFFFFFFF8........, which does NOT fit in'),
 329:('funcion', '    -- release a function key pressed six frames earlier'),
 358:('estado', '    -- save state so that each step does not repeat 20 minutes of booting'),
 366:('consola dijo', '        print(string.format("[frame %d] the console said %q: stopping here",'),
}


def main():
    p = sys.argv[1]
    lines = open(p, encoding='utf-8', errors='replace').read().split('\n')
    done, bad = 0, []
    for n, (must, new) in sorted(LINES.items()):
        i = n - 1
        if i >= len(lines):
            bad.append('%d: past end of file' % n)
            continue
        if must not in lines[i]:
            bad.append('%d: expected %r, found %r' % (n, must, lines[i][:60]))
            continue
        lines[i] = new
        done += 1
    open(p, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines))
    print('%s: %d lines replaced' % (p, done))
    for b in bad:
        print('    SKIPPED %s' % b)
    return 1 if bad else 0


sys.exit(main())
