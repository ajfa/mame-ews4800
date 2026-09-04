#!/bin/bash
# Waits for a given screen dump to appear, or for the emulator to exit.
# Usage:  SHOT=400000 waitshot.sh
W="${EWS_WORK}"
SHOT="${SHOT:-400000}"
BIN="$W/fvtags/fb${SHOT}.bin"
for i in $(seq 1 40); do
    if [ -f "$BIN" ]; then
        sleep 5   # let the write finish
        echo "SCREEN $SHOT READY"
        break
    fi
    if ! pgrep -x ews4800 >/dev/null; then
        echo "EMULATOR EXITED"
        break
    fi
    sleep 60
done
date +%H:%M:%S
tail -n 4 "$W/install/run.out"
stat -c "disk image %s bytes, touched %y" "$W/ews4800-disk.chd"
