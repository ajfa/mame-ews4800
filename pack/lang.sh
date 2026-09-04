#!/bin/bash
# Language gate: the repository is English throughout, from the first commit, and that
# covers comments, strings and identifiers.
#
# Two lessons are built into this file.
#
# First, it was written inline in check.sh, where a heredoc ate the word boundaries and
# the line continuations, and it reported clean on a tree that was full of Spanish. A gate
# that passes when it should not is worse than no gate, so it lives in its own file where
# what runs is what you read.
#
# Second, the word list lives in spanish-words.txt rather than in this script, because an
# identifier rename pass ran over the list itself and turned one entry into "out" and
# another into "inp". The gate then matched every English file in the tree. Data that
# happens to be foreign must not sit where a rename can reach it.
#
# A file that legitimately carries such words as data marks itself with LANG-GATE-EXEMPT
# on a line of its own, and the gate skips it.
cd "$(dirname "$0")/.." || exit 1

LIST="pack/spanish-words.txt"
[ -f "$LIST" ] || { echo "  FAIL  missing $LIST"; exit 1; }

hits=$(grep -rli -w -f "$LIST" \
       --include='*.sh' --include='*.py' --include='*.lua' --include='*.cpp' \
       harness tools patch pack 2>/dev/null | sort -u)

remaining=""
for f in $hits; do
    grep -q 'LANG-GATE-EXEMPT' "$f" || remaining="$remaining$f"$'\n'
done
remaining=$(echo "$remaining" | grep -v '^$' || true)

if [ -n "$remaining" ]; then
    echo "  FAIL  $(echo "$remaining" | wc -l) file(s) still carry foreign text:"
    echo "$remaining" | sed 's/^/          /'
    exit 1
fi
echo "  ok    English only"
exit 0
