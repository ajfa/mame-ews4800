# NEC EWS4800/310 driver for MAME

A MAME driver for the NEC EWS4800/310, a MIPS R4000 workstation, written by reverse
engineering the machine. It boots NEC's UX/4800 R12.2 UNIX from a hard disk image to a
console login prompt and gives an interactive root session.

The upstream driver was a 176 line skeleton with `TODO: everything` and only the boot ROM
mapped.

## What you need

This repository contains **no NEC software and no ROM images**. You supply your own:

- the boot ROM pair, `g8ppg__0100.a01f2` and `g8ppg__0200.a01f`
- the UX/4800 R12.2 installation media as an ISO image

Everything here is code and documentation.

## Quick start

    export EWS_WORK=$HOME/ews4800          # working directory: images, disks, logs
    export EWS_TOOLS=$PWD                  # this checkout
    pack/build-ubuntu.sh                   # fetch and build MAME with the driver
    pack/install-ubuntu.sh                 # install UX/4800 to a disk image, ~4 h
    pack/run-ubuntu.sh                     # boot from that disk to Console Login:

Read `pack/README.txt` first. It documents the memory and disk the build needs, and how
to shut the guest down without corrupting the disk image.

## State

Boots to a root shell on the console. X11 does not come up, and the reason is structural
rather than a missing setting. See `docs/STATUS.md`.

## Layout

    docs/STATUS.md      what works, what does not, and why
    patch/              the driver, as a file and as a patch against MAME 0.288
    harness/            scripts that drive the guest without a window
    tools/              analysis tools used to reverse engineer the machine
    pack/               build and run scripts for Ubuntu

## Driving the guest

The driver is used headless, with `-video none`. There is no window to focus and nothing
to dismiss. Screen contents are read by dumping the frame buffer and converting it to a
PNG, so the console can be inspected without a display server.

Keys are fed through a hot channel: write a line into the file named by `EWS_KEYFILE` and
the guest types it. This matters because the installer asks a question whose frame number
cannot be predicted, and MAME with `-video none` answers neither SIGTERM nor SIGINT.

The line `!shot <label>` in that same file dumps the screen on demand, which is what makes
it possible to drive a shell: you have to look after each command, not at a frame number
chosen in advance.

## Instrumentation

All off by default, all set through the environment:

| Variable | Effect |
|---|---|
| `EWS_KBDLOG=1` | Logs the scan code sent for every key press and release |
| `EWS_UNMAPLOG=1` | Logs every access to unmapped memory, with address and PC |
| `EWS_SCSILOG=1` | Logs SCSI register traffic with the writing program counter |
| `EWS4800_SPOOF_ID` | Machine identification word |
| `EWS4800_GAID` | Value returned by the graphics adapter identification register |

MAME needs `-oslog` for any of the logging to appear. Without it they install without
failing and print nothing.

## License

BSD-3-Clause, the same license as the upstream MAME driver this derives from. See
`LICENSE`.
