# BetterCP/M 1.2 maintained platforms

| Platform | Supported baseline | Unloaded TPA | Qualification and operation |
| --- | --- | ---: | --- |
| cpmsim RAM | Patched z80pack cpmsim, default full-RAM profile | 57,344 bytes | [Qualification](../engineering/CPMSIM-1.1-DEFAULT.md) · [Installation](CPMSIM-INSTALLATION.md) |
| TRS-80 Model 4 | Model 4 in trs80gp, existing keyboard/video reservation | 54,272 bytes | [Layout exception](../engineering/1.1-ENGINEERING-SPECIFICATION.md#unloaded-transient-program-area) · [Installation](MODEL4-INSTALLATION.md) |
| **TRS-80 Model II** | Radio Shack/Tandy Model II, 64 KiB, trs80gp 2.5.8, eight-inch single-sided BCM2SS IMDs | **57,344 bytes** | [Acceptance](../engineering/evidence/2026-11-07-model2-acceptance/qualification.json) · [Installation](MODEL2-INSTALLATION.md) · [Port and build notes](MODEL2-PORT.md) |

Model II is an official, maintained platform for the 1.2 development line.
The qualification covers the emulated Model II. Physical hardware, Models 12,
16 and 16B, hard drives, double-sided floppies, formatting, serial/printer
hardware and a clock provider are outside this support commitment. The default
console and CRT LIST route, absent-device behavior, and optional ADM3A, VT52
and ANSI personalities are qualified. The packaged TIME utility reports the
normal absent-provider status. The existing 1.0.x releases retain their own
platforms and packages.

## Reused Model II engineering evidence

* On the unloaded system a 57,344-byte COM ran through RET, JP 0 and BDOS
  Function 0. A 57,472-byte COM was rejected and the next command executed.
  CPX reconstruction, optional RSX load/use/unload, terminal positioning,
  service discovery, numeric PATH and submitted input passed in trs80gp.
* SYSGEN installed the system on a disk with erased system tracks. The
  installed disk and DUP copy each matched all 625,920 decoded bytes of the
  source. The copy booted alone and passed DUP /CHECK with zero unreadable
  sectors. CONFIG confirmed both live and saved IOBYTE 149. The primary and
  companion Utilities disks contain 27 and 10 files respectively.
* All 30 native compatibility cases passed. Eleven returning groups printed
  269 passes, zero failures and zero errors. Supplemental native checks covered
  file and media protection, physical-error operator choices, changing a
  logged disk and resetting it, the final allocation block, full directory,
  keyboard editing, and CONFIG persistence and rejection. The native release,
  compatibility and PATH batches retained 173 CRT captures.
* Controlled tests exercised the assembled Model II system with keyboard,
  sector and controller faults supplied independently. They captured the
  individual suite rows, including four additional DISKTEST allocation cases
  in its required group. They checked input buffers and display behavior,
  documented disk structures and BIOS calls, and CONFIG recovery from a
  write that had already damaged a startup sector. The FD1791/DMA instruction
  tests reproduced the original single-attempt defect and verified the
  corrected behavior across 32 cases.

The pinned CP/M 2.2 catalogue contains 627 cards. Of its **430 REQUIRED** cards,
273 passed in returning suite groups on the controlled Model II system, 36 in
controlled CONSTEST, and 118 through external checks. Three document differences
from strict DRI behavior. Card 0020 expects an uppercased command tail.
BetterCP/M preserves the original spelling and uppercases the default FCB.
Cards 0493 and 0494 expect single-drive/current-user lookup. BetterCP/M uses
the configured numeric PATH for unqualified commands and honors explicit DU
qualification. Optional profiles, observations, nonguaranteed cases and
out-of-scope entries have separate dispositions. [Card ledger](../engineering/evidence/2026-11-07-model2-acceptance/cards.tsv) · [Guest evidence](../engineering/evidence/2026-11-07-model2-acceptance/guest.json)

## Maintenance

The normal combined System build includes Model II. Use
`python3 -B tools/build_distribution.py --target trs80m2` for that platform
alone. The publisher checks the immutable image and archive before reuse;
the Utilities builder checks the matching System hash and private carrier
identity. The 1.2 release uses the focused acceptance policy linked below.

For changes to the shared CCP, BDOS, BIOS, private service ABI, disk layout,
screen backend or packaged utilities, run the relevant Model II checks on the
resulting media. Identify the actual paired System/Utilities hashes in the
release record. Use the controller, console and external tests when changing
those boundaries. For 1.2, reuse the retained engineering evidence and perform
only the [focused automated checks and manual smoke](../releases/1.2-SCOPE-AND-ACCEPTANCE.md).
NDR, annotated PATH, HELP and NOAH 1.0 (021) are included in the frozen scope.
The measurements and campaigns above are historical engineering evidence,
not a claim that the new 1.2 media repeated them.
