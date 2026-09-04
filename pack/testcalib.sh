#!/bin/bash
# Checks the job sizing arithmetic of build-ubuntu.sh against forced memory figures.
#
# This is the number that decides whether a small virtual machine finishes the build or
# meets the out of memory killer several hours in, and it cannot be tested by running the
# real build on a large host. So the arithmetic is exercised on its own.
#
# Rule: jobs = min(cores, available MB / 2560), never below one.
calc() {
    avail_mb=$1
    cores=$2
    by_mem=$(( avail_mb / 2560 ))
    JOBS=$by_mem
    [ "$JOBS" -gt "$cores" ] && JOBS=$cores
    [ "$JOBS" -lt 1 ] && JOBS=1
    echo "$JOBS"
}

failures=0
expect() {
    got=$(calc "$1" "$2")
    if [ "$got" = "$3" ]; then
        printf '  ok    %6s MB, %2s cores -> -j%s\n' "$1" "$2" "$got"
    else
        printf '  FAIL  %6s MB, %2s cores -> -j%s, expected -j%s\n' "$1" "$2" "$got" "$3"
        failures=$((failures + 1))
    fi
}

echo "=== job sizing"
expect   3500  2  1      # the 4 GB virtual machine, the case that matters
expect   2000  4  1      # tight, must not round down to zero
expect    500 16  1      # almost nothing free, still one job
expect   7800 16  3      # the development host
expect  32000  4  4      # plenty of memory, cores are the limit
expect  32000  1  1      # single core
echo
[ "$failures" -eq 0 ] && echo "CALIBRATION OK" || echo "CALIBRATION FAILED, $failures cases"
exit "$failures"
