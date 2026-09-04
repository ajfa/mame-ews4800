#!/bin/bash
# LANG-GATE-EXEMPT: this file names foreign text as data
# Language gate. The matching itself is in langgate.py, which documents the four green
# lights earlier versions of this gate gave on a tree that was not clean.
#
# This file is only the entry point, and it is deliberately thin: the previous version
# carried the matching inline in shell and awk, where a heredoc ate the word boundaries
# and the gate passed on a tree full of Spanish.
#
# langgate-test.sh proves the gate FAILS on planted foreign text. A gate nobody has seen
# go red is not a gate.
cd "$(dirname "$0")/.." || exit 1
exec python3 pack/langgate.py .
