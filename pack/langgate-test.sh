#!/bin/bash
# LANG-GATE-EXEMPT: this file plants foreign text on purpose
# Proves the language gate goes RED on planted foreign text, and stays GREEN on the tree
# as it stands. Every case below is one that a previous version of the gate let through.
#
#   1  a noun on the list, plain                 caught before
#   2  a noun on the list inside an identifier   grep -w does not break on underscore
#   3  a noun NOT on the list, in a sentence     the function word pass catches it
#   4  a lone Spanish word, no sentence          the word ending pass catches it
#
# Usage:  langgate-test.sh
cd "$(dirname "$0")/.." || exit 1
ROOT=$(pwd)

plant() {  # $1 label, $2 line of text to append to a scratch copy
    tmp=$(mktemp -d)
    cp -r harness tools patch pack docs README.md "$tmp/" 2>/dev/null
    printf '%s\n' "$2" >> "$tmp/tools/ufsls.py"
    if python3 "$ROOT/pack/langgate.py" "$tmp" >/dev/null 2>&1; then
        echo "  FAIL  gate stayed green on: $1"
        rm -rf "$tmp"
        return 1
    fi
    echo "  ok    gate goes red on: $1"
    rm -rf "$tmp"
    return 0
}

bad=0
plant "a listed noun"                 "# el fichero de salida" || bad=1
plant "a listed noun in an identifier" "libres_gb = 3" || bad=1
plant "an unlisted noun in a sentence" "# la ruta del disco que se lee" || bad=1
plant "a lone word by its ending"     "x = 'verificacion'" || bad=1

echo
if python3 pack/langgate.py . ; then
    :
else
    echo "  FAIL  the tree itself does not pass"
    bad=1
fi

echo
if [ "$bad" -eq 0 ]; then
    echo "LANG GATE TESTED: red on all four plants, green on the tree"
    exit 0
fi
echo "LANG GATE BROKEN"
exit 1
