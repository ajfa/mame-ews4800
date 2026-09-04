#!/usr/bin/env python3
# LANG-GATE-EXEMPT: this file names foreign text as data
"""Language gate: the tree is English throughout, in comments, strings and identifiers.

Four lessons are built into this file, each one a green light an earlier version of this
gate gave on a tree that was not clean.

1. It was written inline in check.sh, where a heredoc ate the word boundaries and the line
   continuations, and it reported clean on a tree full of Spanish. A gate that passes when
   it should not is worse than no gate, so it lives in its own file where what runs is
   what you read.

2. The word list lived in the script, and an identifier rename pass ran over the list
   itself, turning one entry into "out" and another into "inp". The gate then matched
   every English file in the tree. Data that happens to be foreign must not sit where a
   rename can reach it, so the list is in spanish-words.txt.

3. grep -w does NOT break on an underscore, because underscore is a word character. The
   identifier libres_gb sailed through a gate whose list already contained libres, so the
   noun pass treats underscore as a SEPARATOR: its boundary is [^A-Za-z0-9], underscore
   included. Writing that boundary as [^A-Za-z0-9_] reproduces the original bug exactly,
   and did, which is why langgate-test.sh plants libres_gb as a case of its own.

4. A list of NOUNS is always one noun short. The previous list missed ruta, disco, tamano,
   bloques, inodo, hueco and tramo, and 44 lines of Spanish shipped. Nouns are open ended,
   function words are not, so pass 2 matches FUNCTION words and flags any line carrying
   two or more distinct ones. No Spanish sentence of more than three words avoids that,
   while an English line stays under the threshold: a shell line with -o and -y on it
   scores one, not two.

A file that legitimately carries foreign text as data marks itself with LANG-GATE-EXEMPT
on one of its first five lines.

Usage:  langgate.py [tree root]        exit 0 clean, 1 dirty
"""
import os
import re
import sys

EXTS = ('.sh', '.py', '.lua', '.cpp', '.md', '.txt', '.patch')
DIRS = ('harness', 'tools', 'patch', 'pack', 'docs')
ROOT_FILES = ('README.md',)
WORDLIST = os.path.join('pack', 'spanish-words.txt')

# pass 2: function words. Closed class, so this list cannot go out of date.
FUNC = """de la el en se es al lo su un una y o no que con por para del los las como mas
pero si ya me te le nos les mi tu sus esta este esto ese esa eso aqui alli donde cuando
porque pues sino sobre entre hasta desde hacia segun sin tras cada todo toda todos todas
otro otra otros otras mismo misma tan tanto muy solo ni ha han hay ser son era fue""".split()

# pass 3: Spanish morphology, for a lone word with no sentence around it
ENDINGS = ('cion', 'ciones', 'miento', 'mente', 'ando', 'iendo', 'ados', 'adas', 'aron',
           'amos', 'imos', 'aba', 'aban', 'arios', 'encia', 'ancia', 'idad', 'ismo')

# English words that end the same way and are not evidence of anything
ENDING_OK = {'commands', 'demands', 'expands', 'brands', 'islands', 'operands', 'stands',
             'threads', 'loads', 'reads', 'heads', 'leads', 'roads', 'downloads',
             'uploads', 'spreads', 'overloads', 'payloads', 'quads', 'monads',
             # names that belong to the guest media and are never translated
             'ubkataban'}


def bounded(words, split_on_underscore):
    """Compile an alternation of words with a boundary on each side.

    split_on_underscore=True makes underscore a separator, so libres_gb is caught. That is
    what the noun pass wants. The function word pass does not: words that short would
    match inside ordinary identifiers, so there underscore stays part of the word.
    """
    body = '|'.join(sorted(set(words), key=len, reverse=True))
    edge = '[A-Za-z0-9]' if split_on_underscore else '[A-Za-z0-9_]'
    return re.compile(r'(?<!' + edge + r')(' + body + r')(?!' + edge + r')', re.I)


def walk(root):
    for d in DIRS:
        base = os.path.join(root, d)
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [x for x in dirnames if x not in ('.git', '__pycache__')]
            for fn in sorted(filenames):
                if fn.endswith(EXTS):
                    yield os.path.join(dirpath, fn)
    for fn in ROOT_FILES:
        p = os.path.join(root, fn)
        if os.path.exists(p):
            yield p


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else '.'
    listpath = os.path.join(root, WORDLIST)
    if not os.path.exists(listpath):
        print('  FAIL  missing %s' % WORDLIST)
        return 1
    words = [w.strip() for w in open(listpath, encoding='utf-8') if w.strip()]
    rx_list = bounded(words, True)      # nouns: underscore separates
    rx_func = bounded(FUNC, False)      # function words: underscore does not
    rx_end = re.compile(r'(?<![A-Za-z])([a-z]{3,}(?:%s))(?![A-Za-z])' % '|'.join(ENDINGS), re.I)

    problems = []
    for path in walk(root):
        rel = os.path.relpath(path, root).replace(os.sep, '/')
        if rel == WORDLIST.replace(os.sep, '/'):
            continue
        lines = open(path, encoding='utf-8', errors='replace').read().split('\n')
        if any('LANG-GATE-EXEMPT' in l for l in lines[:5]):
            continue
        for n, line in enumerate(lines, 1):
            hit = rx_list.search(line)
            if hit:
                problems.append((rel, n, 'word list: %s' % hit.group(1), line))
                continue
            func = sorted(set(h.lower() for h in rx_func.findall(line)))
            if len(func) >= 2:
                problems.append((rel, n, 'function words: %s' % ','.join(func), line))
                continue
            for m in rx_end.finditer(line):
                if m.group(1).lower() not in ENDING_OK:
                    problems.append((rel, n, 'Spanish ending: %s' % m.group(1), line))
                    break

    if problems:
        print('  FAIL  %d line(s) read as foreign text:' % len(problems))
        for rel, n, why, line in problems[:40]:
            print('          %s:%d  [%s]  %s' % (rel, n, why, line.strip()[:70]))
        if len(problems) > 40:
            print('          ... and %d more' % (len(problems) - 40))
        return 1
    print('  ok    English only (word list, function words, word endings)')
    return 0


sys.exit(main())
