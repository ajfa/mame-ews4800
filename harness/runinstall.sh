#!/bin/bash
# Full install of UX/4800 to a disk image, with the interval timer already corrected to
# 20 MHz. It stops as soon as the console says it finished, so the frame budget is a
# ceiling and not a cost.
set -e
cd "${EWS_WORK}"
# The previous disk is kept: it stays bootable but with a dirty root, because the run was
# killed at the final question, and it is useful as a reference.
[ -f ews4800-disk.chd ] && mv -f ews4800-disk.chd ews4800-disk.chd.dirty
./mame/chdman createhd -o ews4800-disk.chd -chs 4096,16,32 -ss 512 -c none -f >/dev/null 2>&1

export EWS_BUZFIX=1 EWS_PCHIST=1 EWS_PCHIST_EVERY=50000
export EWS_DISK="${EWS_WORK}/ews4800-disk.chd"
export EWS_ISO="${EWS_WORK}/ux4800-patched.iso"
export EWS_FRAMES=900000
# Hot key channel. The installer's final questions cannot be scheduled in advance because
# there is no way to know which frame they land on.
export EWS_KEYFILE="${EWS_WORK}/keys.in"
export EWS_STOPON="INSTALLATION COMPLETED"
export EWS_SHOTS=200000,300000,400000,500000,650000,800000,1000000,1250000
export EWS_KEYS="13000:1;14000:{ENTER};17000:3;18000:{ENTER};21000:2;22000:{ENTER};25000:yes;26000:{ENTER};37000:y;38000:{ENTER};46000:3;47000:{ENTER};49000:1;50000:{ENTER};53000:fmthard -c0 /dev/rsd/c0t1d0s6;54000:{ENTER};58000:exit;59000:{ENTER};63000:1;64000:{ENTER};67000:1;68000:{ENTER};70000:{SPACE};72000:{SPACE};74000:{SPACE};77000:n;78000:{ENTER};81000:n;82000:{ENTER};90000:@kbd3/F6;93000:i;94000:{ENTER};98000:192.168.1.10;99000:{ENTER};103000:yes;104000:{ENTER};107000:yes;108000:{ENTER};111000:yes;112000:{ENTER};116000:n;117000:{ENTER};120000:1;121000:{ENTER}"
: > "$EWS_KEYFILE"
bash install.sh
