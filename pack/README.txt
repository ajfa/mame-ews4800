NEC EWS4800/310 in MAME
=======================

This pack builds MAME with a driver for the NEC EWS4800/310 and boots NEC UX/4800 R12.2
UNIX from a disk image to a console login prompt.

It contains NO NEC software. You supply the boot ROM pair and the UX/4800 ISO.


WHAT YOU NEED ON THE MACHINE
----------------------------
  Ubuntu, 64 bit
  about 15 GB free disk
  at least 2 GB RAM to build, 4 GB is comfortable
  the ROM pair in $EWS_WORK/roms:  g8ppg__0100.a01f2 and g8ppg__0200.a01f
  the installation ISO at $EWS_WORK/ux4800.iso

The build is sized by MEMORY, not by cores. MAME needs about 2.5 GB per compile job, so a
4 GB machine builds with a single job no matter how many cores it reports. build-ubuntu.sh
works that out for you. On one job, expect several hours.


ORDER
-----
  export EWS_WORK=$HOME/ews4800
  export EWS_TOOLS=/path/to/this/checkout

  pack/build-ubuntu.sh        builds MAME, long
  pack/install-ubuntu.sh      installs UX/4800 to a fresh disk image, about 4 hours
  pack/run-ubuntu.sh          boots that disk to Console Login:

Every script refuses to start rather than half work: missing ROM, missing ISO, not enough
disk, or an emulator already running.


HOW YOU DRIVE IT
----------------
There is no window. The emulator runs with -video none, so nothing needs focus and no
warning screen has to be dismissed.

Type into the guest by appending a line to the key file:

  printf 'root\n{ENTER}\n' >> $EWS_WORK/keys.in

Look at the screen on demand:

  printf '!shot now\n' >> $EWS_WORK/keys.in
  python3 $EWS_TOOLS/tools/fbpng.py $EWS_WORK/fvtags/fbnow.bin screen.png

One line per key or per string. The guest types it within a second.


SHUTTING DOWN, WHICH MATTERS
----------------------------
The guest must be shut down from inside. Killing the emulator leaves the root file system
dirty, and the next boot stops with "ckroot: warning, return value 36" followed by
"SYSTEM WILL REBOOT". Recovering from that needs an fsck from the CD maintenance shell.

  printf '/sbin/shutdown -y -g0 -i0\n{ENTER}\n' >> $EWS_WORK/keys.in

Then wait until the disk image stops being written. Watch the timestamp:

  stat -c '%y' $EWS_WORK/ews4800-disk.chd

When it has not changed for three minutes the unmount is done and the emulator can be
stopped:

  pkill -9 -x ews4800

Note that -video none makes MAME answer neither SIGTERM nor SIGINT, so kill -9 is the only
way to stop it, which is exactly why the guest has to be shut down first.

This sequence was run end to end and the following boot came up clean, with no ckroot
warning and no file system check.


IF THE DISK IMAGE DOES GET DIRTY
--------------------------------
Boot the CD to the maintenance shell, Maintaining then Maintaining shell mode, and:

  /etc/fs/ufs/fsck -y /dev/rsd/c0t1d0s0

mount is not on the path in that shell. On this System V it lives per file system type, at
/etc/fs/ufs/mount. There is no cat either, the installer carries its own at
/inst/bin/scat.


WHAT WORKS
----------
Boot ROM and power on test, SCSI disk and CD-ROM with the slot DMA engine, the 1280x1024
bitmap console, the keyboard, the interval timer, installing all 53 packages, booting from
the installed disk, root login, and clean shutdown.


WHAT DOES NOT
-------------
X11 does not come up. The reason is structural and is written up in docs/STATUS.md: the
kernel finds its graphics adapter by name in a device tree that is compiled from
configuration, that entry is commented out, and the alternative hardware probe reads an
address this kernel never maps. None of the five X servers on the media reaches the
hardware at all, they all fail in open().

Mouse, floppy and networking are not implemented.
