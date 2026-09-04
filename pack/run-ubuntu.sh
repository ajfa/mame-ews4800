#!/bin/bash
# Boots the installed UX/4800 disk image to Console Login: and leaves the guest running.
#
# A window by default, because the point of an emulated workstation is to look at it.
# --headless runs it with no window, which is how the automated runs work: nothing to
# focus, nothing to dismiss, and screens read by dumping the frame buffer instead.
set -e

WINDOW=yes
for a in "$@"; do
    case "$a" in
        --headless) WINDOW=no ;;
        --window)   WINDOW=yes ;;
        *) echo "unknown flag: $a"; exit 1 ;;
    esac
done

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

# The machine identification word. WITHOUT THIS THE SYSTEM DOES NOT BOOT: the driver
# reports a different machine, the kernel takes another path and never writes a single
# character to the console, so you get a black screen and no error. Measured value.
export EWS4800_SPOOF_ID="${EWS4800_SPOOF_ID:-0x101e}"
export EWS_BANKS="${EWS_BANKS:-1}"
# install.lua writes its screen dumps to $HOME/ews4800/fvtags unless told otherwise.
export EWS_TAGDIR="$EWS_WORK/fvtags"
export EWS_BUZFIX=1
export EWS_BOOTDEV=2 EWS_BOOTID=1
export EWS_KEYFILE="$EWS_WORK/keys.in"
: > "$EWS_KEYFILE"
export EWS_FRAMES="${EWS_FRAMES:-150000}"
export EWS_SHOTS="${EWS_SHOTS:-5000,10000,15000,20000,30000}"

cd "$RUN"
echo "booting, Console Login: appears around frame 15000, about eight minutes"

if [ "$WINDOW" = yes ]; then
    # -video soft, not the default opengl: a virtual machine without 3D acceleration
    # has no OpenGL, and MAME then dies with "video_init: Initialization failed".
    # Software rendering is plenty for a 1280x1024 monochrome console.
    #
    # MAME shows two screens before it starts. -skip_gameinfo removes the machine
    # information one. The red warning screen, raised because the driver is marked
    # MACHINE_NOT_WORKING, has NO option in 0.288: -showusage lists only
    # -skip_gameinfo and -confirm_quit. Press any key and it goes.
    #
    # Never fullscreen: -window -nomaximize.
    echo "a red warning screen comes first: press any key. Then type into the window."
    exec "$BIN" \
        -rompath "$EWS_WORK/roms" \
        ews4800_310 \
        ${EWS_RAM:+-ramsize $EWS_RAM} \
        -scsi:0 cdrom -cdrm "$ISO" \
        -scsi:1 harddisk -hard "$DISK" \
        -rs232a terminal \
        -sound none -video soft -window -nomaximize -skip_gameinfo -numscreens 2 \
        -debugger none -debug \
        ${EWS_OSLOG:+-oslog} \
        -autoboot_script "$EWS_WORK/install.lua" -autoboot_delay 0
fi

# Headless. No X server is needed at all: a desktop dropping the display has killed
# long runs before, and the dummy driver removes the dependency entirely.
export SDL_VIDEODRIVER=dummy
"$BIN" \
    -rompath "$EWS_WORK/roms" \
    ews4800_310 \
    ${EWS_RAM:+-ramsize $EWS_RAM} \
    -scsi:0 cdrom -cdrm "$ISO" \
    -scsi:1 harddisk -hard "$DISK" \
    -rs232a terminal \
    -video none -sound none -nothrottle \
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
