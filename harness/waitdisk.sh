#!/bin/bash
# Waits until the disk image is TOUCHED, or until the emulator exits.
#
# This is the signal that the clean unmount happened after a shutdown: marking the super
# block clean is a write. Without it the root stays dirty and the next boot stops with
# "ckroot: warning, return value 36".
W="${EWS_WORK}"
CHD="$W/ews4800-disk.chd"
MINS="${MINS:-20}"
base=$(stat -c %Y "$CHD" 2>/dev/null || echo 0)
for i in $(seq 1 "$MINS"); do
    sleep 60
    m=$(stat -c %Y "$CHD" 2>/dev/null || echo 0)
    if [ "$m" != "$base" ]; then
        echo "DISK TOUCHED"
        break
    fi
    if ! pgrep -x ews4800 >/dev/null; then
        echo "EMULATOR EXITED"
        break
    fi
done
date +%H:%M:%S
stat -c "disk image %s bytes, touched %y" "$CHD"
tail -n 5 "$W/install/run.out"
pgrep -x ews4800 >/dev/null && echo "emulator running" || echo "emulator stopped"
ls "$W/fvtags/"*.bin
