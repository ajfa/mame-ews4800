#!/bin/bash
# Watches a running install and EXITS as soon as something needs a decision, so the run
# does not have to be polled by hand.
#
# The size of the disk image is NOT a sign of activity: with compression set to none the
# hunks sit at fixed offsets, so rewriting a hunk that already exists leaves the file
# exactly as large. Only appending new ones grows it. The signal to use is the
# modification time. Getting this wrong produced a false alarm at frame 82000 on a disk
# that was being written normally.
#
# Exit codes:
#   0  the emulator exited, look at install/run.out
#   3  the disk has not been touched for STALL seconds, so the installer wants a key
#   4  the console said something worth stopping for
W="${EWS_WORK}"
CHD="$W/ews4800-disk.chd"
OUT="$W/install/run.out"
STALL="${STALL:-900}"           # 15 minutes untouched
FLOOR="${FLOOR:-150000000}"     # only counts once the package copy is under way
HARD="${HARD:-2400}"            # 40 minutes untouched is odd in any phase
log() { echo "[$(date +%H:%M)] $*"; }
lastm=$(stat -c %Y "$CHD" 2>/dev/null || echo 0)
lastreport=0
while true; do
    sleep 60
    if ! pgrep -x ews4800 >/dev/null; then
        log "EMULATOR EXITED"
        tail -n 25 "$OUT"
        exit 0
    fi
    m=$(stat -c %Y "$CHD" 2>/dev/null || echo 0)
    sz=$(stat -c %s "$CHD" 2>/dev/null || echo 0)
    [ "$m" != "$lastm" ] && lastm=$m
    quiet=$(( $(date +%s) - lastm ))
    now=$(date +%s)
    if [ $(( now - lastreport )) -ge 600 ]; then
        lastreport=$now
        log "alive: $(( sz / 1048576 )) MB, quiet ${quiet}s, $(grep -c . "$OUT")L  $(tail -n1 "$OUT")"
    fi
    if grep -qi "INSTALLATION COMPLETED\|SYSTEM WILL REBOOT\|PANIC" "$OUT" 2>/dev/null; then
        log "THE CONSOLE SAID SOMETHING"
        grep -in "INSTALLATION COMPLETED\|SYSTEM WILL REBOOT\|PANIC" "$OUT" | tail -5
        exit 4
    fi
    if { [ "$quiet" -ge "$STALL" ] && [ "$sz" -ge "$FLOOR" ]; } || [ "$quiet" -ge "$HARD" ]; then
        log "DISK QUIET ${quiet}s at $(( sz / 1048576 )) MB"
        tail -n 8 "$OUT"
        exit 3
    fi
done
