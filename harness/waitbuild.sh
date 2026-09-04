#!/bin/bash
# Waits for the MAME build to finish and says whether the binary came out.
#
# Never hide the build behind a tail: when it fails you need to see the error, and a tail
# of the last few lines shows the link step of a build that never got there.
W="${EWS_WORK}"
for i in $(seq 1 60); do
    if ! pgrep -f "make SOURCES" >/dev/null; then
        break
    fi
    sleep 15
done
date +%H:%M:%S
echo "--- last lines ---"
tail -n 12 "$W/build.log"
echo "--- errors ---"
grep -i -n "error\|Error [0-9]" "$W/build.log" | tail -n 10
echo "--- binary ---"
ls -la "$W/mame/ews4800"
