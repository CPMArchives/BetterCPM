# PIP completion qualification

Qualified 14 October 2026. BetterCP/M PIP 1.0 Build 026 is 14,257 bytes.
The native ZSM4/LINK build and cross build are byte-identical.

## Behavior and reference

The pinned DRI PIP 1.5 binary remains the behavioral reference. All 18 PIP
unit campaigns pass. Real cpmsim comparisons pass for wildcard files,
multi-extent concatenation, reader lists, text extraction, Intel HEX reader
input, physical PRN/PTP/PTR endpoints and CRT output. Interruption and SUBMIT
failure tests preserve the original destination and clean staging files.
The Model 4 media test passes verified disk transfer, CRT output, unavailable
device rejection and standalone /VER.

PRN supplies DRI numbering, eight-column tab expansion and page formatting.
The documented DRI single-file S/Q object-EOF distinction is retained.
Ordinary copies retain DRI attribute behavior; COPY-specific ARC semantics
are not imposed on PIP.

Physical aliases temporarily select the appropriate IOBYTE field through
standard BDOS character calls, then restore it. DRI cooked console input is
retained: its fatal Ctrl-C warm boot cannot return through ordinary cleanup.
Unsupported devices are rejected before transfer or destination mutation.

## Platform and memory contract

The Model 4 provides CRT console and CRT list routing. cpmsim additionally
provides host TTY, PTR, PTP and LPT routing; PRN is formatted LPT output.
Unsupported user-defined devices remain unavailable. BAT output follows
logical LST and BAT input follows logical RDR. cpmsim AUX EOF status is not
misused as a readiness indication.

BIOS API 1.6 adds the bounded character capability query at BIOS+63.
Existing vectors and BDOS remain unchanged. The Model 4 BIOS occupies
693 of 757 allocated bytes, leaving 64 bytes for the planned monitor hooks.
The combined 757-byte candidate is native/cross byte-identical; 5,376 routing
and monitor audit cases pass. Unloaded TPA remains 53K.

The cpmsim ROM image has 5,456 immutable bytes and a 2,412-byte RAM template.
After initializer and cold-boot entry, 524 bytes remain spare. All 786
classified references and 805 discovered layout words pass relocation
checks; the real relocated ROM cold-boot/CPX/RSX lifecycle test passes.

## Reproduction and media

Use the existing tools/test_pip_*.py campaigns, build_native_pip.py,
test_native_memory_candidates.py, test_iobyte_routing_audit.py,
test_iobyte_boot.py and test_z80pack_rom_boot.py. Media campaigns operate on
private copies. The larger compatibility fixture uses 80 cylinders of the
same 18-sector, 256-byte CCS layout, with 128 directory entries; it avoids
capacity limits from keeping both implementations and test drivers together.
It is a qualification fixture, not the distribution format.

Production PIP is emitted at build/utilities/PIP.COM and included by the
System Disk manifest. Final distribution qualification is performed by
tools/build_distribution.py for both platforms.

Both final System Disk builds pass boot and manifest qualification:

| Platform | Files | Free allocation space | Pending utility |
| --- | ---: | ---: | --- |
| cpmsim | 22 | 178K | ED.COM |
| trs80gp | 21 | 626K | ED.COM |

These counts include completed PIP and the existing platform-specific runtime
files. Monitor-provider implementation remains separate work.
