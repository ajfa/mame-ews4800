#!/bin/bash
# Extracts the other kernels from the CD.
#
# The nine kernels on the media do NOT carry the same device tree. vmunix.01, the one that
# boots here, has no bcon controller at all, while vmunix.06, .07 and .08 have six each.
# Any question about the graphics adapter has to be asked of THOSE, not of .01. Reading
# the wrong kernel is how the key table was misread once already.
set -e
W="${EWS_WORK}"
T="${EWS_TOOLS}"
for K in 00 02 03 04 05 06 07 08; do
    python3 "$T/tools/isols.py" "$W/ux4800.iso" --extract "/VMUNIX.$K;1" "$W/vmunix.$K"         > /dev/null 2>&1 || echo "  failed $K"
done
ls -la "$W"/vmunix.*
