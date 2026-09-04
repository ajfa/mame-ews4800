#!/usr/bin/env python3
# LANG-GATE-EXEMPT: this file names foreign text as data
"""Replaces the remaining foreign comment blocks with English, one exact match at a time.

Targeted replacement rather than a full rewrite, because the code around these comments
works and has been exercised; a rewrite of working code to change a comment is a risk with
no upside. Every entry is an exact string, so a miss is reported instead of being applied
somewhere unintended.

Usage:  translate_comments.py <file> ...
"""
import sys

CHANGES = {
'tools/hwcompare.py': [
    ('"""Paso 1 del plan: comparar los nueve kernels del CD por DIVERGENCIA DE HARDWARE.',
     '"""Compares the nine kernels on the CD by hardware divergence.'),
    ('Para cada vmunix.NN:',
     'For each vmunix.NN:'),
    ('  (a) el mapa de I/O que espera: histograma de los `lui rX, 0xXXXX` con',
     '  (a) the I/O map it expects: a histogram of the lui rX, 0xXXXX instructions whose'),
    ('      immediate en KSEG1 de dispositivos (0xa000-0xbfff), agrupado por',
     '      immediate lands in device KSEG1, 0xa000 to 0xbfff, grouped by 16 MB'),
    ('      ventana de 16 MB, con el sÃ­mbolo que contiene la instrucciÃ³n;',
     '      window, with the symbol that contains the instruction;'),
    ('  (b) los sÃ­mbolos de grÃ¡ficos / consola / teclado presentes.',
     '  (b) which graphics, console and keyboard symbols are present.'),
    ('Uso:  hwcompare.py <dir-cdkern> [--io | --gfx | --detail NN]',
     'Usage:  hwcompare.py <kernel dir> [--io | --gfx | --detail NN]'),
    ('    """copia del parser de .unixsyms (unixsyms.py ejecuta main() al importarse)"""',
     '    """Copy of the .unixsyms parser; unixsyms.py runs main() when imported."""'),
    ('# id canonico por indice de fichero (FINDINGS Â§33.3, tabla 0x80191a80)',
     '# canonical machine id by file index, from the table at 0x80191a80'),
    ('        if typ != 1 or not addr or not size:      # SHT_PROGBITS con direccion',
     '        if typ != 1 or not addr or not size:      # SHT_PROGBITS with an address'),
    ('    """lui rX,imm con imm en 0xa000..0xbfff -> {ventana16M: [(va, imm)]}"""',
     '    """lui rX, imm with imm in 0xa000..0xbfff -> {16M window: [(va, imm)]}"""'),
],
}


def main():
    total = 0
    for path in sys.argv[1:]:
        key = path.replace('\\', '/')
        for k in CHANGES:
            if key.endswith(k):
                s = open(path, encoding='utf-8', errors='replace').read()
                done, missed = 0, []
                for old, new in CHANGES[k]:
                    if old in s:
                        s = s.replace(old, new, 1)
                        done += 1
                    else:
                        missed.append(old[:48])
                open(path, 'w', encoding='utf-8', newline='\n').write(s)
                print('%s: %d replaced' % (path, done))
                for m in missed:
                    print('    MISSED %r' % m)
                total += done
    print('total %d' % total)


main()
