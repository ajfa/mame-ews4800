#!/usr/bin/env python3
# LANG-GATE-EXEMPT: this file names foreign words as data
"""Renames Spanish identifiers to English across the tree.

The rule is that the repository is English throughout, and that covers variable and
function names, not only comments. Doing it with a table rather than by hand keeps it
reviewable and repeatable.

Word boundaries matter: `fallos` must not turn `fallos_previos` into something odd, and
`prueba` appears both as a function and inside strings.

Usage:  rename_ids.py <file> [more...]
"""
import re
import sys

TABLA = [
    ('fallos', 'failures'), ('fallo', 'failure'),
    ('nucleos', 'cores'), ('libres_kb', 'free_kb'), ('libres_gb', 'free_gb'),
    ('por_mem', 'by_mem'), ('disp_mb', 'avail_mb'), ('falta', 'missing'),
    ('espanol', 'spanish'), ('sucio', 'dirty'), ('hechos', 'done'),
    ('sospechosas', 'suspect'), ('raros', 'odd'), ('malas', 'bad'),
    ('cambios', 'changes'), ('viejo', 'old'), ('nuevo', 'new'),
    ('prueba', 'expect'), ('calc', 'calc'), ('got', 'got'),
    ('ventanas', 'windows'), ('quien', 'who'), ('detalle', 'detail'),
    ('total', 'total'), ('salida', 'out'), ('entrada', 'inp'),
    ('lineas', 'lines'), ('linea', 'line'), ('ancla', 'anchor'),
    ('texto', 'text'), ('limpio', 'clean'), ('copiados', 'copied'),
    ('faltan', 'absent'), ('origen', 'src_path'), ('destino', 'dst_path'),
    ('nombres', 'names'), ('nombre', 'name'), ('sanear', 'scrub'),
    ('SUSTITUCIONES', 'SUBSTITUTIONS'), ('PROHIBIDO', 'FORBIDDEN'),
    ('CURATED', 'CURATED'), ('CAMBIOS', 'CHANGES'), ('TABLA', 'TABLE'),
    ('PALABRAS', 'WORDS'), ('hits', 'hits'),
    ('base', 'base'), ('techo', 'ceiling'), ('syms', 'syms'),
    ('addrs', 'addrs'), ('loads', 'loads'), ('blob', 'blob'),
    ('leer', 'read_at'), ('segments', 'segments'), ('busca_lui', 'find_lui'),
    ('tras_imm', 'after_imm'), ('visto', 'seen'), ('ctlrs', 'ctlrs'),
    ('ctlr_txt', 'ctlr_txt'), ('pcs', 'pcs'), ('ops', 'ops'),
    ('win', 'win'), ('roto', 'broken'), ('bueno', 'fixed'),
]


def main():
    for p in sys.argv[1:]:
        s = open(p, encoding='utf-8').read()
        before = s
        for old, new in TABLA:
            if old == new:
                continue
            s = re.sub(r'\b%s\b' % re.escape(old), new, s)
        if s != before:
            open(p, 'w', encoding='utf-8', newline='\n').write(s)
            print('renamed  %s' % p)
        else:
            print('no change %s' % p)


main()
