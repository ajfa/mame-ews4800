# Using UX/4800 on the emulated EWS4800/310

What you get once the disk boots, where the media came from, and the things
that cost time. The driver side is in the [README](../README.md) and
[docs/STATUS.md](STATUS.md).

## Where the media is

The whole of EWS-UX, as far as an extended search could tell, survives online
in one place: <https://tenox.pdp-11.net/os/ewsux/>. It holds three files and no
more.

| file | what it is |
| --- | --- |
| `EWS-UX_7.2_install_manual.pdf` | installation manual for the earlier R7.2 |
| `nec_ews4800_430_ux.img.lz` | a disk image from an EWS4800/430, a different model |
| `UX4800 WSOS Media R12.2(01).rar` | the R12.2 installation ISO, which is what this driver installs from |

Nothing else turned up: not archive.org, not TUHS, not bitsavers, not the
Japanese FTP archives at Akita or meshnet that carried ported freeware. If you
want more EWS-UX than that, the realistic routes are Yahoo Auctions Japan,
the VCFed thread where the /430 was sold, the Japanese communities (5ch UNIX,
fj.sys.ews4800), and writing to tenox.

Two things about that ISO are worth knowing before you start.

It is **multi-machine media**: nine kernels (`vmunix.00` to `vmunix.08`), nine
IOP boot images and a `ramfilsys`, with a table of 18 models. The boot block
normalises the machine id and picks the pair for it.

And it is **not /310 media**. None of the nine kernels dispatches on the /310's
own id; R12.2 dropped it. The kernel's own model name table still says
`0x1020 = EWS4800/310(LC),320(EX/SX/VX)` and `0x101e = EWS4800/330`, and NEC's
own media normalises `0x1020` to `0x101e`, which is why the run scripts export
`EWS4800_SPOOF_ID=0x101e`. Without that the kernel takes another path and never
writes a character to the console: a black screen and no error message.

The boot ROM pair is the machine's own firmware and is not in this repository.

## Getting in

The disk boots to:

```
NEC Operating System UX/4800 Release12.2 Rev.A
The system is ready.
Console Login: root
1 nec root>
```

`root` has no password on a fresh install. The prompt counts commands, so
`1 nec root>` becomes `2 nec root>`.

The kernel running is the one built during installation, R12.2 Rev.A, not the
R12.1 Rev.E that boots off the CD. All 53 packages install, including `xfnd`,
`xserver`, `dtclients`, `dtadmin` and `dtxtfonts`, about 261 MB on disk. X11
still does not come up, and the reason is structural rather than a missing
setting; `docs/STATUS.md` has it.

## The licence lock, and the chmod that opens it

A freshly installed system checks its licence and will not let you work. There
are two binaries from `osunum.c R12` involved, `/etc/.nec/.picheck` and
`/sbin/picheckos`, but a ten line shell script governs both, `/sbin/pirc`, and
everything in it hangs off `[ -x /sbin/picheckos ]`. So:

```
chmod 444 /sbin/picheckos
```

Neither binary then runs. It is reversible, changes not one byte of any binary,
and it is the path NEC themselves left for "not installed".

The catch is that you cannot do it from a system that will not let you in. The
way through is the CD's maintenance shell with the installed disk mounted:

```
3) Maintaining -> 1) Maintaining shell mode
/etc/fs/ufs/fsck  -y /dev/rsd/c0t1d0s0
/etc/fs/ufs/mount    /dev/sd/c0t1d0s0 /mnt
chmod 444 /mnt/sbin/picheckos
/sbin/umount /mnt
```

## Two SVR4 habits that look like breakage

**`mount` is not on the PATH.** In SVR4 the filesystem commands live under the
filesystem type: `/etc/fs/ufs/fsck`, `/etc/fs/ufs/mkfs`, `/etc/fs/ufs/mount`.
That came out of reading the installer's own `hd_setup`, not out of guessing.

**`ls -l /etc/.nec` prints `total 0`.** Everything in there starts with a dot,
so it needs `ls -la`. Easy to read as an empty directory and go looking
elsewhere.

## Shutting down, which matters

Shut the guest down from inside. Killing the emulator leaves the root
filesystem dirty and the next boot stops with `ckroot: warning, return value 36`
followed by `SYSTEM WILL REBOOT`; getting out of that needs an `fsck` from the
CD maintenance shell.

```
/sbin/shutdown -y -g0 -i0
```

Then wait until the disk image stops being written before stopping the
emulator. Watching the file's timestamp is enough; when it has not changed for
three minutes the unmount is done. This sequence was run end to end and the
boot after it came up clean, with no `ckroot` warning and no filesystem check.

With `-video none` MAME answers neither SIGTERM nor SIGINT, so `kill -9` is the
only way to stop it, which is exactly why the guest has to be shut down first.

## Mistakes worth not repeating

**Killing the emulator at the installer's last `Choice ?`.** That is how the
first installed disk ended up in the `ckroot` reboot loop. The install was
finished in every way that mattered and the root filesystem still had not been
unmounted. Answer the closing prompts.

**Carving files out of the CHD to read them.** With compression set to none the
hunks are raw and `grep -abo` finds strings, which works for small files:
`.picheck` at 28 KB came out whole. `picheckos` at 123 KB came out as garbage,
because it runs past UFS's direct blocks and is fragmented. Patching that blind
would have corrupted the disk. The cheap test that a carve is sound is whether
the disassembly makes sense.

**Two hypotheses about the keyboard, both refuted by measurement rather than by
argument.** It was not a burst-typing problem: a single key with eight seconds
of silence around it failed the same way. It was not modifier ordering either;
the `EWS_KBDLOG=1` instrument showed shift arriving before the key with correct
codes. The actual cause was two separate things, an unreachable `_` key in the
driver's own port definition, and a keyboard table dumped from the wrong
kernel: the CD's R12.1 kernel uses a different row from the installed R12.2 one,
which is US, not JIS.

**An invented constant that cost twenty hours per install.** The timer clock
was a guess, and the comment in the driver said so: *"The counter's clock is
unknown; 1 MHz is a guess"*. It is 20 MHz. Installation took about 25 hours with
the machine sitting 97 per cent of the time in `idle()`; it takes about four
now. If an emulated machine is unaccountably slow, look for the clock you made
up rather than blaming the interpreter.

**`logerror()` prints nothing without `-oslog`.** Every instrument in this
driver installs cleanly, fails at nothing, and stays silent without it.
