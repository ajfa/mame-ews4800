#!/usr/bin/env python3
# LANG-GATE-EXEMPT: this file names foreign words as data
"""Translates the two comment blocks added while debugging into English.

The repository is English throughout: README, comments, strings, file names and commit
messages. The driver was already English except for two blocks written during a debugging
session, plus the note on the JIS key that carries the underscore.

Usage:  englishify.py <ews4800.cpp>
"""
import sys

CHANGES = [
    (
        "\t// EWS_KBDLOG=1: que codigo sale de VERDAD por cada tecla.  Sin esto no se\n"
        "\t// puede separar \"natkeyboard pulsa otra tecla\" de \"la tabla del huesped no\n"
        "\t// es la que yo lei\", que son arreglos opuestos.\n",
        "\t// EWS_KBDLOG=1 logs the scan code actually sent for every key. Without it\n"
        "\t// there is no way to tell \"the natural keyboard pressed a different key\"\n"
        "\t// from \"the guest table is not the one I read\", and those need opposite\n"
        "\t// fixes.\n",
    ),
    (
        "\t// EWS_UNMAPLOG=1: cada acceso a memoria NO MAPEADA, a logerror (hace missing\n"
        "\t// -oslog para verlo).  Es lo que dice QUE registros pide el driver del\n"
        "\t// framebuffer, en vez de deducir la direccion.\n",
        "\t// EWS_UNMAPLOG=1 sends every access to unmapped memory to logerror (MAME\n"
        "\t// needs -oslog to show it). This is what says which registers the frame\n"
        "\t// buffer driver asks for, instead of deducing the address.\n",
    ),
]


def main():
    p = sys.argv[1]
    s = open(p, encoding='utf-8').read()
    # the section sign is the only non-ascii left in the file; a published repo
    # should not depend on the encoding of a comment
    s = s.replace('§', 'sec. ')
    done = 0
    for old, new in CHANGES:
        if old in s:
            s = s.replace(old, new, 1)
            done += 1
    open(p, 'w', encoding='utf-8', newline='\n').write(s)
    print('translated %d block(s)' % done)

    # gate: no accented characters and no obvious Spanish keywords left
    suspect = ['que codigo', 'huesped', 'direccion', ' asi ', ' esto ', 'tecla']
    bad = [w for w in suspect if w in s]
    odd = sorted({c for c in s if ord(c) > 126})
    if bad or odd:
        print('CHECK: %s  non-ascii=%s' % (bad, odd))
        return 1
    print('gate    english only, ascii only')
    return 0


sys.exit(main())
