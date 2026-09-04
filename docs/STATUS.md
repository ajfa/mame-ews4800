# NEC EWS4800/310 in MAME: what works and what does not

The upstream MAME driver `src/mame/nec/ews4800.cpp` was a 176 line skeleton with
`TODO: everything` and only the boot ROM mapped. This tree contains a driver written by
reverse engineering the machine, and the harness used to drive it.

The machine now boots NEC's UX/4800 R12.2 UNIX from a hard disk image to a console login
prompt and accepts an interactive root session.

## Works

| | Detail |
|---|---|
| Boot ROM and POST | Passes, including the LR4370 system controller test |
| SCSI (NCR 53C94) | Disk and CD-ROM, with the slot DMA engine |
| Console | 1280x1024 bitmap console, 1 bpp, framebuffer at physical `0x10000000` |
| Keyboard | Z85C30 channel B, 4800 baud, odd parity; full US punctuation |
| Interval timer | 20 MHz, giving the 100 Hz system tick the kernel expects |
| Install to disk | All 53 packages of the R12.2 media, unattended |
| Boot from disk | `NEC Operating System UX/4800 Release12.2 Rev.A` |
| Root login | `Console Login: root` gives a csh prompt |
| Clean shutdown | `shutdown -y -g0 -i0` unmounts cleanly; next boot is clean |

## Does not work

| | Why |
|---|---|
| X11 / desktop | No graphics adapter node; see below. All five X servers fail in `open()` |
| Mouse | Not implemented (SCC channel A) |
| Floppy | Present but only exercised for the licence disk |
| Network | The kernel starts STREAMS TCP but there is no emulated interface |

## Why X11 cannot come up with this media

This is a structural result, not a missing setting.

The kernel does not probe for the graphics adapter. It looks it up by name in a device
tree that `idbuild` compiles from text files, and the entry that would create the
controller is commented out in `/etc/conf/pdevice.d/bcon`. So `getbootcons()` returns 0
and the framebuffer driver refuses to open.

There is a second path, a hardware probe, taken when the machine identifies as the real
/310. It reads `[ga_base + 0x00F00E00]` with `ga_base = 0xD0000000`. That address cannot
work in this kernel:

    sbd_init        stores 0xC0000000, and sets ga_base = 0xD0000000
    setup_kptbl     maps kseg2 from 0xC0000000 up to a ceiling of 0xD0000000
    bcon_dset       reads [ga_base + 0x00F00E00] with a plain load, no mapping call
    setup_wired_tlb only invalidates TLB entries, it never wires one

The ceiling lands exactly where `ga_base` begins, so the read takes a TLB exception and
the machine parks at `0x80000184`, the general exception vector. Measured, not inferred:
with unmapped-access logging enabled the read never reaches the bus.

The media carries nine kernels. Only `vmunix.06`, `.07` and `.08` contain graphics
adapter controllers, and those three are PCI machines: their `sbd_init` does not contain
`0xD0000000` at all. So no kernel on this media both targets this machine family and has
a working adapter node.

Three ways forward, none of them a configuration tweak:

1. Obtain the real /310 media, whose kernel would carry an on-board adapter node and a
   base its own `setup_kptbl` maps.
2. Emulate one of the PCI adapters the other kernels expect (`GA_V1`, `GA_C4`, `GA_TE2`,
   `GA_C3`, `GA_MEGA`) and boot one of those kernels.
3. Stay on the console, which works completely.

## Notable findings

**The interval timer runs at 20 MHz, not 1 MHz.** A guessed constant in the driver made
the system tick 5 Hz instead of 100, so everything the kernel waited for took twenty
times too long. Three independent confirmations: the kernel never reprograms the timer,
`drv_usectohz` divides by 1000000 and multiplies by a literal 100, and the guest clock
ran at a ratio of 20.0 against the host. Fixing it took the install from eleven hours to
three.

**The slot DMA engine starts on `0x07`, not on `0x20`/`0x30`.** Those two set the
direction and are remembered; the start is a separate write. Writing only the direction
worked as long as every transfer fitted in one chunk, and broke on the first scattered
one. The write counts gave it away: 802 direction writes against 803 starts.

**The OS protection lock is one shell script.** `/sbin/pirc` gates the whole check on
`[ -x /sbin/picheckos ]`, so removing the execute bit disables it without patching a
single byte of any binary. That is the vendor's own path for "not installed".

**The installed kernel uses a US key table, not JIS.** The driver declared the JIS row,
which is what the CD kernel carries. Twelve measured points, no contradictions.

## Instrumentation

The driver honours several environment variables, all off by default:

| Variable | Effect |
|---|---|
| `EWS_KBDLOG=1` | Logs the scan code sent for every key press and release |
| `EWS_UNMAPLOG=1` | Logs every access to unmapped memory, with address and PC |
| `EWS_SCSILOG=1` | Logs SCSI register traffic with the writing PC |
| `EWS4800_SPOOF_ID` | Machine identification word |
| `EWS4800_GAID` | Value returned by the graphics adapter identification register |

`logerror()` output needs MAME's `-oslog`, otherwise these install without failing and
print nothing.

## Verification

Everything above was observed on screen and captured, not inferred. The install, the
boot, the root login and the clean shutdown were each run end to end more than once, the
last boot starting from the previous clean shutdown.
