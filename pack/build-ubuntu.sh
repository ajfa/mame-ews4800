#!/bin/bash
# Builds MAME with the EWS4800/310 driver on Ubuntu.
#
# Sizing is by MEMORY, not by core count: MAME needs about 2.5 GB per compile job, so a
# 4 GB machine builds with one job however many cores it reports. Getting this wrong ends
# in the out of memory killer several hours in.
#
# The build is never hidden behind a tail: if it fails you need to see the error.
set -e

EWS_WORK="${EWS_WORK:-$HOME/ews4800}"
MAME_TAG="${MAME_TAG:-mame0288}"
SRC="$EWS_WORK/mame"
HERE="$(cd "$(dirname "$0")/.." && pwd)"

echo "=== space and memory"
df -h "$HOME" | tail -1
free -m | sed -n '1,2p'

free_kb=$(df -Pk "$HOME" | awk 'NR==2 {print $4}')
free_gb=$(( free_kb / 1024 / 1024 ))
if [ "$free_gb" -lt 15 ]; then
    echo
    echo "STOP: $free_gb GB free, the source tree and build need about 15 GB."
    echo "Free some space or set EWS_WORK to a larger filesystem."
    exit 1
fi

# jobs = min(cores, available memory / 2.5 GB), never zero
avail_mb=$(free -m | awk '/^Mem:/ {print $7}')
[ -z "$avail_mb" ] && avail_mb=$(free -m | awk '/^Mem:/ {print $4}')
by_mem=$(( avail_mb / 2560 ))
cores=$(nproc)
JOBS=$by_mem
[ "$JOBS" -gt "$cores" ] && JOBS=$cores
[ "$JOBS" -lt 1 ] && JOBS=1
echo
echo "cores $cores, available ${avail_mb} MB  ->  building with -j$JOBS"
if [ "$JOBS" -eq 1 ]; then
    echo "one job: expect a long build, several hours is normal on a small VM."
fi

echo
echo "=== build dependencies"
missing=""
for p in git build-essential python3 libsdl2-dev libsdl2-ttf-dev libfontconfig1-dev \
         libpulse-dev qtbase5-dev; do
    dpkg -s "$p" >/dev/null 2>&1 || missing="$missing $p"
done
if [ -n "$missing" ]; then
    echo "missing:$missing"
    echo "installing (needs sudo):"
    sudo apt-get update
    sudo apt-get install -y $missing
else
    echo "all present"
fi

echo
echo "=== source"
mkdir -p "$EWS_WORK"
if [ ! -d "$SRC/.git" ]; then
    git clone --depth 1 --branch "$MAME_TAG" https://github.com/mamedev/mame.git "$SRC"
else
    echo "reusing $SRC"
fi

echo
echo "=== driver"
cp "$HERE/patch/ews4800.cpp" "$SRC/src/mame/nec/ews4800.cpp"
echo "installed src/mame/nec/ews4800.cpp ($(wc -l < "$SRC/src/mame/nec/ews4800.cpp") lines)"

echo
echo "=== compiling, this is the long part"
cd "$SRC"
make SOURCES=src/mame/nec/ews4800.cpp SUBTARGET=ews4800 REGENIE=1 NOWERROR=1 -j"$JOBS"

echo
if [ -x "$SRC/ews4800" ]; then
    echo "built $SRC/ews4800"
    "$SRC/ews4800" -help 2>&1 | head -2
else
    echo "STOP: the binary is not there, look at the output above."
    exit 1
fi
