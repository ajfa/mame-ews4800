#!/bin/bash
# Installs UX/4800 R12.2 to a fresh disk image. About four hours, unattended except for
# two questions at the end, which this script answers through the hot key channel.
#
# The original ISO is never modified. Three patches are applied to a COPY:
#   the licence check, the spurious /home partitions, and a root slice that overruns the
#   disk by 148 blocks because the installer adds the pieces up instead of subtracting.
set -e

EWS_WORK="${EWS_WORK:-$HOME/ews4800}"
EWS_TOOLS="${EWS_TOOLS:-$(cd "$(dirname "$0")/.." && pwd)}"
BIN="${EWS_BIN:-$EWS_WORK/mame/ews4800}"
ISO_ORIG="${EWS_ISO_ORIG:-$EWS_WORK/ux4800.iso}"
ISO="$EWS_WORK/ux4800-patched.iso"
DISK="${EWS_DISK:-$EWS_WORK/ews4800-disk.chd}"
CHDMAN="${EWS_CHDMAN:-$EWS_WORK/mame/chdman}"

for f in "$BIN" "$CHDMAN" "$ISO_ORIG"; do
    [ -e "$f" ] || { echo "STOP: missing $f"; exit 1; }
done
if pgrep -x ews4800 >/dev/null; then
    echo "STOP: an ews4800 is already running."
    exit 1
fi

echo "=== space"
df -h "$EWS_WORK" | tail -1
free_gb=$(( $(df -Pk "$EWS_WORK" | awk 'NR==2 {print $4}') / 1024 / 1024 ))
if [ "$free_gb" -lt 3 ]; then
    echo "STOP: $free_gb GB free, the disk image alone grows past 260 MB and the"
    echo "installer needs room to work."
    exit 1
fi

if [ ! -f "$ISO" ]; then
    echo
    echo "=== patching a copy of the ISO, the original is left alone"
    cp "$ISO_ORIG" "$ISO"
    python3 "$EWS_TOOLS/tools/mkunlockiso3.py" "$ISO"
    python3 "$EWS_TOOLS/tools/nohomes.py" "$ISO"
    python3 "$EWS_TOOLS/tools/rootfit.py" "$ISO"
else
    echo "reusing $ISO"
fi

if [ -f "$DISK" ]; then
    echo
    echo "STOP: $DISK already exists. Move it aside if you mean to start over;"
    echo "a finished install is four hours of work and this script will not overwrite it."
    exit 1
fi

echo
echo "=== fresh 1 GB disk image"
"$CHDMAN" createhd -o "$DISK" -chs 4096,16,32 -ss 512 -c none -f

rm -rf "$EWS_WORK/fvtags"; mkdir -p "$EWS_WORK/fvtags"
RUN="$EWS_WORK/install"; rm -rf "$RUN"; mkdir -p "$RUN"
cp "$EWS_TOOLS/harness/install.lua" "$EWS_WORK/install.lua"

# The machine identification word. Without it the kernel takes another path and never
# writes to the console: black screen, no error. Measured value.
export EWS4800_SPOOF_ID="${EWS4800_SPOOF_ID:-0x101e}"
export EWS_BANKS="${EWS_BANKS:-1}"
export EWS_TAGDIR="$EWS_WORK/fvtags"
export EWS_BUZFIX=1
export EWS_KEYFILE="$EWS_WORK/keys.in"
: > "$EWS_KEYFILE"
export EWS_FRAMES="${EWS_FRAMES:-900000}"
export EWS_STOPON="INSTALLATION COMPLETED"
export EWS_SHOTS="200000,300000,400000,500000"
export EWS_KEYS="13000:1;14000:{ENTER};17000:3;18000:{ENTER};21000:2;22000:{ENTER};25000:yes;26000:{ENTER};37000:y;38000:{ENTER};46000:3;47000:{ENTER};49000:1;50000:{ENTER};53000:fmthard -c0 /dev/rsd/c0t1d0s6;54000:{ENTER};58000:exit;59000:{ENTER};63000:1;64000:{ENTER};67000:1;68000:{ENTER};70000:{SPACE};72000:{SPACE};74000:{SPACE};77000:n;78000:{ENTER};81000:n;82000:{ENTER};90000:@kbd3/F6;93000:i;94000:{ENTER};98000:192.168.1.10;99000:{ENTER};103000:yes;104000:{ENTER};107000:yes;108000:{ENTER};111000:yes;112000:{ENTER};116000:n;117000:{ENTER};120000:1;121000:{ENTER}"

[ "${EWS_X11:-0}" = "1" ] || export SDL_VIDEODRIVER=dummy

cd "$RUN"
"$BIN" \
    -rompath "$EWS_WORK/roms" \
    ews4800_310 \
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
echo "The installer stops twice near the end, around four hours in. The signal is the"
echo "disk image going quiet: watch  stat -c '%y' $DISK"
echo
echo "  first question,  extra installation tapes or floppies:"
echo "    printf 'no\\n{ENTER}\\n' >> $EWS_KEYFILE"
echo "  second, after Installation completed:"
echo "    printf 'go\\n{ENTER}\\n' >> $EWS_KEYFILE"
echo
echo "The second one matters: 'go' is what makes the system unmount its root cleanly."
echo "Answering it is the difference between a disk that boots and one that needs fsck."
echo
echo "Watch it hands off with:  $EWS_TOOLS/harness/watchinstall.sh"
