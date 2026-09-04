#!/bin/bash
# Boots the installed UX/4800 disk image to Console Login: and leaves the guest running.
#
# Headless on purpose. With -video none there is no window to focus and no warning screen
# to dismiss, and the run does not depend on which window the desktop has in front.
# Screens are read by dumping the frame buffer, see below.
set -e

EWS_WORK="${EWS_WORK:-$HOME/ews4800}"
EWS_TOOLS="${EWS_TOOLS:-$(cd "$(dirname "$0")/.." && pwd)}"
BIN="${EWS_BIN:-$EWS_WORK/mame/ews4800}"
DISK="${EWS_DISK:-$EWS_WORK/ews4800-disk.chd}"
ISO="${EWS_ISO:-$EWS_WORK/ux4800.iso}"

for f in "$BIN" "$DISK" "$ISO"; do
    if [ ! -e "$f" ]; then
        echo "STOP: missing $f"
        echo "build-ubuntu.sh makes the binary, install-ubuntu.sh makes the disk,"
        echo "and the ISO is yours to supply."
        exit 1
    fi
done

if pgrep -x ews4800 >/dev/null; then
    echo "STOP: an ews4800 is already running. Shut the guest down first, see README.txt."
    exit 1
fi

RUN="$EWS_WORK/run"
rm -rf "$RUN"; mkdir -p "$RUN"
rm -rf "$EWS_WORK/fvtags"; mkdir -p "$EWS_WORK/fvtags"

cp "$EWS_TOOLS/harness/install.lua" "$EWS_WORK/install.lua"

export EWS_BUZFIX=1
export EWS_BOOTDEV=2 EWS_BOOTID=1
export EWS_KEYFILE="$EWS_WORK/keys.in"
: > "$EWS_KEYFILE"
export EWS_FRAMES="${EWS_FRAMES:-150000}"
export EWS_SHOTS="${EWS_SHOTS:-5000,10000,15000,20000,30000}"

# No X server is needed. WSLg or a desktop dropping the display has killed long runs
# before; the dummy video driver removes the dependency entirely.
[ "${EWS_X11:-0}" = "1" ] || export SDL_VIDEODRIVER=dummy

cd "$RUN"
echo "booting, Console Login: appears around frame 15000, about eight minutes"
"$BIN" \
    -rompath "$EWS_WORK/roms" \
    ews4800_310 \
    ${EWS_RAM:+-ramsize $EWS_RAM} \
    -scsi:0 cdrom -cdrm "$ISO" \
    -scsi:1 harddisk -hard "$DISK" \
    -rs232a terminal \
    -video none -sound none -nothrottle -window -nomaximize \
    -debugger none -debug \
    ${EWS_OSLOG:+-oslog} \
    -autoboot_script "$EWS_WORK/install.lua" -autoboot_delay 0 \
    > "$RUN/run.out" 2>&1 &

echo "pid $!, log $RUN/run.out"
echo
echo "to type into the guest:      printf 'root\\n{ENTER}\\n' >> $EWS_KEYFILE"
echo "to look at the screen:       printf '!shot now\\n' >> $EWS_KEYFILE"
echo "                             python3 $EWS_TOOLS/tools/fbpng.py \\"
echo "                                 $EWS_WORK/fvtags/fbnow.bin screen.png"
echo
echo "to shut the guest down CLEANLY, which you must do before stopping MAME:"
echo "  printf '/sbin/shutdown -y -g0 -i0\\n{ENTER}\\n' >> $EWS_KEYFILE"
echo "  then wait until the disk image stops being written, see README.txt"
