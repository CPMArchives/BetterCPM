# ZSM4 — Native macro assembler

[Utilities Manual](utilities_manual.md#native-assembler-and-linker) · [LINK](LINK.md)

The Utilities Disk carries unmodified ZSM4 4.7 for Z80-compatible CP/M systems.
It reads assembly source and produces Microsoft/DRI-format relocatable objects.
This is Hector Peraza's tool, with the earlier contributors acknowledged in its
source; its original interface and version remain intact.

Put `PROGRAM.MAC` on the writable work disk in D:. With primary Utilities in B:, use the following sequence.

```text
D:
B:ZSM4 PROGRAM=PROGRAM
B:LINK PROGRAM[A]
PROGRAM
```

The explicit left-hand name selects the output stem; the right-hand name
selects the source. Includes resolve on the output drive. Use `CSEG` for
relocatable code. `ORG 100H` alone can introduce an unwanted 256-byte gap when
linked; the compression native-build procedure documents its special `.PHASE`
preparation. Keep source and output on a work disk, not the Utilities disk.
Assembly reports `Errors: 0` on success. Inspect diagnostics before linking;
batch continuation alone is not proof that assembly succeeded.

`/HELP` and `/VER` are BetterCP/M-owned command conventions and have not been
added to this third-party executable. ZSM4 displays its native V4.7 banner.
The complete upstream manual, source, tests and Makefile accompany the Utilities
images in `ZSM4-SOURCE.tar.gz`; see `zsm4-source/docs` after unpacking on the host.

ZSM4 is GPL-2.0-or-later. The disk contains `ZSM4COPY.TXT`; distribute the full
source companion with these images. In the Utilities ZIP, `source/Toolchain-Provenance.json`
identifies the shipped executable. The upstream record is at
`licenses/third_party/zsm4/provenance.json`. See also the
[guide to third-party records](../LICENSING.md#third-party-records).
