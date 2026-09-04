#!/bin/bash
# Boots the CD straight to the maintenance root shell:
#   1) English  ->  3) Maintaining  ->  1) Maintaining shell mode
#
# From there the guest is driven through EWS_KEYFILE and looked at with `!shot <label>`,
# the on demand screen dump. Dumps at fixed frame numbers are no use for driving a shell,
# because you have to look AFTER each command and there is no way to know in advance which
# frame that falls on.
#
# Note: the RAM disk has no cat. The installer carries its own at /inst/bin/scat.
set -e
cd "${EWS_WORK}"
export EWS_BUZFIX=1
export EWS_DISK="${EWS_WORK}/ews4800-disk.chd"
export EWS_ISO="${EWS_WORK}/ux4800-patched.iso"
export EWS_KEYFILE="${EWS_WORK}/keys.in"
: > "$EWS_KEYFILE"
export EWS_FRAMES="${EWS_FRAMES:-900000}"
# Do not use ${VAR:-...} here. The closing brace of {ENTER} confuses the expansion and the
# key comes out as "{ENTER}}", which types a stray brace. Harmless in a menu, not harmless
# on a root command line.
if [ -z "$EWS_KEYS" ]; then
    EWS_KEYS='13000:1;14000:{ENTER};17500:3;18000:{ENTER};21000:1;21500:{ENTER}'
fi
export EWS_KEYS
export EWS_SHOTS="${EWS_SHOTS:-16000,20000,24000}"
bash install.sh
