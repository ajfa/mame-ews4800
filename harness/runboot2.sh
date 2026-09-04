#!/bin/bash
# Boots the freshly installed disk, with a larger frame budget and far more screen dumps
# than a plain boot script: there is no way to know which frame Console Login: lands on,
# so it is better to look often than to guess the number.
set -e
cd "${EWS_WORK}"
export EWS_BUZFIX=1
export EWS_BOOTDEV=2 EWS_BOOTID=1
export EWS_DISK="${EWS_WORK}/ews4800-disk.chd"
export EWS_ISO="${EWS_WORK}/ux4800-patched.iso"
export EWS_KEYFILE="${EWS_WORK}/keys.in"
: > "$EWS_KEYFILE"
export EWS_PCHIST=1 EWS_PCHIST_EVERY=50000
export EWS_FRAMES="${EWS_FRAMES:-150000}"
export EWS_SHOTS="${EWS_SHOTS:-5000,10000,15000,20000,30000,40000,50000,65000,80000,100000,120000,150000}"
bash install.sh
