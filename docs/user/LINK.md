# LINK — Native relocatable linker

[Utilities Manual](utilities_manual.md#native-assembler-and-linker) · [ZSM4](ZSM4.md)

The Utilities Disk carries unmodified Digital Research LINK 1.3. It combines
relocatable objects such as ZSM4's `.REL` output into a CP/M `.COM` program.

With Utilities on B: and `PROGRAM.REL` on your logged writable drive:

```text
B:LINK PROGRAM[A]
```

`[A]` selects the absolute CP/M executable output. To combine modules and choose
an output stem:

```text
B:LINK CHECK=MAIN,PART[A]
```

This writes `CHECK.COM`. Resolve all external symbols before running it. LINK
prints `CODE SIZE`, `DATA SIZE` and `COMMON SIZE`; an `UNDEFINED SYMBOLS` report
means the output is not a successful executable, even if a COM file was written.
Native output is rounded to CP/M records with `1Ah` padding.

LINK retains its native `LINK 1.3` identity; BetterCP/M `/HELP` and `/VER` have
not been added. Copyright remains with Digital Research. `LINKCOPY.TXT` contains
the retained CP/M permission and clarification. The host package records the
exact archive origin, binary hash and redistribution basis in
`Toolchain-Provenance.json`; see also the repository's
[provenance](../../third_party/dri-link/provenance.json).
