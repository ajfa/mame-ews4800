#!/usr/bin/env python3
"""Copies the curated file set into the repo tree and strips machine-local paths.

The working tree carries hundreds of one-shot probe scripts from months of reverse
engineering. Only a curated subset belongs in a published repository, and none of it may
carry absolute paths, user names or host names.

Substitutions are deliberate and auditable:

    a Windows drive mount ending in /ews4800  ->  ${EWS_TOOLS}
    /home/<user>/ews4800        ->  ${EWS_WORK}
    $HOME/ews4800               ->  ${EWS_WORK}

The script exits non-zero if anything that looks machine local survives, so it doubles as
the pre-publication gate.

Usage:  sanitize.py <source dir> <repo dir>
"""
import os
import re
import shutil
import sys

# (subdirectory in the repo, file names)
CURATED = {
    'harness': [
        'install.lua', 'runinstall.sh', 'runboot2.sh', 'runmaint.sh',
        'watchinstall.sh', 'waitshot.sh', 'waitdisk.sh', 'waitbuild.sh',
        'getkernels.sh',
    ],
    'tools': [
        'hwcompare.py', 'unixsyms.py', 'isols.py',
        'fbpng.py', 'fbascii.py', 'fbcorr.py',
        'kdis.py', 'gpstr.py', 'disall.py', 'findelf.py',
        'keytabl.py', 'gacmp.py',
        'pcnames.py', 'pcpage.py', 'pcdiff.py', 'unmapsum.py',
        'mkunlockiso3.py', 'nohomes.py', 'rootfit.py', 'ufsls.py',
    ],
}

# Order matters: the longest, most specific pattern has to win.  An earlier
# version matched only the first two path components, so
# a three deep drive mount became ${EWS_TOOLS}/<dir>/ews4800: the gate passed,
# because no drive mount survived, but the path was broken. A gate that only asks
# "did the bad string disappear" does not ask "is the result correct".
SUBSTITUTIONS = [
    (re.compile(r'/mnt/[a-z]/(?:[A-Za-z0-9_.\-]+/)*ews4800'), '${EWS_TOOLS}'),
    (re.compile(r'/home/[A-Za-z0-9_.\-]+/ews4800'), '${EWS_WORK}'),
    (re.compile(r'"\$HOME"/ews4800'), '${EWS_WORK}'),
    (re.compile(r'\$HOME/ews4800'), '${EWS_WORK}'),
]

# Anything still matching these after substitution fails the gate.
FORBIDDEN = [
    re.compile(r'/mnt/[a-z]/', re.I),
    # a leftover fragment glued to the variable means the substitution was partial
    re.compile(r'\$\{EWS_(?:TOOLS|WORK)\}/(?:Claude|Users|home)'),
    re.compile(r'/home/(?!\$)[A-Za-z0-9_.\-]+'),
    re.compile(r'[Cc]:\\\\?Users'),
    re.compile(r'@[A-Za-z0-9.\-]+\.(com|net|org)\b'),
]


def scrub(text):
    for rx, rep in SUBSTITUTIONS:
        text = rx.sub(rep, text)
    return text


def main():
    src, dst = sys.argv[1], sys.argv[2]
    failures, copied, absent, kept = [], 0, [], 0

    for sub, names in CURATED.items():
        dst_path = os.path.join(dst, sub)
        os.makedirs(dst_path, exist_ok=True)
        for name in names:
            src_path = os.path.join(src, name)
            if not os.path.exists(src_path):
                absent.append(name)
                continue
            out_path = os.path.join(dst_path, name)
            # NEVER clobber. This script is a one time bootstrap: it copies from the
            # working tree, so running it again after the copies have been edited throws
            # the edits away. That happened once, to a whole round of translations. The
            # repository is the source of truth from the first copy onwards.
            if os.path.exists(out_path) and '--force' not in sys.argv:
                kept += 1
                continue
            with open(src_path, encoding='utf-8', errors='replace') as f:
                text = f.read()
            clean = scrub(text)
            with open(os.path.join(dst_path, name), 'w', encoding='utf-8',
                      newline='\n') as f:
                f.write(clean)
            copied += 1
            for rx in FORBIDDEN:
                for m in rx.finditer(clean):
                    failures.append('%s/%s: %r' % (sub, name, m.group(0)))

    print('copied  %d, kept %d already present' % (copied, kept))
    if absent:
        print('MISSING %d: %s' % (len(absent), ' '.join(absent)))
    if failures:
        print()
        print('GATE FAILED, machine-local data survives:')
        for f in sorted(set(failures)):
            print('  %s' % f)
        return 1
    print('gate    clean')
    return 0


sys.exit(main())
