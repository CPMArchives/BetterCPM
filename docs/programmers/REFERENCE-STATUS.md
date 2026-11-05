# Programmer and porting reference status

This ledger accompanies the [Programmer's Guide](../manuals/Programmers-Guide.md) and [Practical Porting Guide](../manuals/Practical-Porting-Guide.md). It records the documentation expansion separately from software release acceptance. Original prose is CC BY 4.0; original reusable examples are GPL-2.0-or-later. See [licensing](../LICENSING.md).

## Baseline and authority

| Identity | Role |
| --- | --- |
| `30b24a021cc3a90eb725cc3d1760dfe0dc31daa8` | Locked software/artifact source. |
| `2842d0eb0732683d9280a38d576c3dba423cb893` | Accepted qualification merge through PR #609. |
| `d43c2a89de3d20880027cad59f9ec98167c60b7d` | Main snapshot inspected for this documentation synthesis. Core/BIOS/system/CPX/RSX/platform source and inspected build-entry recipes match locked source; FDB development and metadata must not be substituted. |
| This working documentation revision | New manuals, API chapters, examples and navigation. Not a replacement software build or a newly qualified archive set. |

The [non-documentation lock](../releases/non-documentation-lock-1.0/README.md), exact artifacts and focused final contracts control scope. Dated surveys/milestones remain historical. No tagging, publication or five-package replacement is authorized by this writing. The Documentation ZIP will need its own actual revision/provenance at the separate packaging stage.

## Coverage delivered in this expansion

| Area | Where | Treatment |
| --- | --- | --- |
| Application construction/execution | Programmer's Guide chapters 1–5 and four examples | Native workflow, memory/stack, console, sequential records, random access and cleanup. |
| CP/M 2.2 interface coverage | [CPM22-API](CPM22-API.md) | All 41 selectors 0–40 including reserved 38/39; all 17 BIOS vectors; page zero/FCB/DMA/IOBYTE/DPH/DPB; baseline versus locked-result distinctions. |
| BetterCP/M service coverage | [BETTERCPM-API](BETTERCPM-API.md) | All assigned 176–183 boundaries; detailed profile/version/disk/registry/TIME requests; optional P2DOS; reserved/test namespace; carrier/monitor/PDS ownership. |
| Extension development | Programmer's Guide chapters 7–10 | CPX worked payload and carrier recipe; RSX source walkthrough, movement/rebinding and provider development. |
| Libraries | Programmer's Guide chapter 11 and existing detailed references | Input integration and provisional source-level archive reuse; no unapproved stable SDK claim. |
| Practical porting | Porting Guide stages 1–10 | Assessment, baseline build, boot, BIOS, disk/configuration, memory/ROM/reconstruction, optional services, media/install, evidence and recovery. |

“Coverage” means the subject has a usable chapter/reference path. It does not claim every private implementation detail is a stable public API, every hardware port has been carried out, or every example has release-wide execution qualification. Explicit links continue into focused technical records for detailed controller, codec and screen records.

## Reconciliation of existing references

| Retained reference | Current reading rule |
| --- | --- |
| [RSX and CPX Programmer's Guide](RSX%20and%20CPX%20Programmer%27s%20Guide.md) | Stage-6 migration is complete; 176/177/182 replace provisional numbers. BCPX live header is eight bytes. Final 7.4 lifecycle and focused carrier/transaction records control over earlier “still to specify” narration. |
| [Monitor RSX Development](Monitor%20RSX%20Development.md) | Later production portable ANSI/full-control admission supersedes earlier conversion-pending checkpoints. Distinguish legacy MCON1.0 host starter from MCON1.1/1.2 + SCRN dependency. |
| [BIOS-DISK-CONFIG](BIOS-DISK-CONFIG.md) | Preserve ABI-5 fields and operation contracts. Its September subsystem identities, “790K default,” incomplete saved path and obsolete save-menu labels are historical. BCPM780 named binding and CONFIG/SYSGEN saved-state path are implemented in locked software. |
| [CONFIG-DUP](CONFIG-DUP.md) | User operation is canonical in the Command Reference. Frozen completion/export contracts supersede earlier implementation increments; timings remain dated hardware/emulator measurements. |
| [BUILD-DISK](BUILD-DISK.md) | Native artifact descriptions remain useful. Use the qualified Source-package preparation/install recipe for the coherent current kit; do not mix symbol snapshots or treat this as the complete host release rebuild guide. |
| [Shared Input Library](Shared%20Input%20Library.md) | Source-level hooks/events/storage rules apply; old consumer build numbers are historical, not current utility identities. New UI reuse does not authorize changing old keys. |
| [Archive Read Library](Archive%20Read%20Library.md) | Initial LBR increment only. Its “not supplied,” single-operation NOAH and pending-write descriptions are not current command inventory. Later matching includes/specifications define provisional source-level reader/writer/codec contracts. |

Architecture 1–14 supply concepts; 19–22, 25, 27–29 and final focused carrier/screen records supply current interface details. Architecture 15 is an initial open-question record; 17 NDR, 26 developer direction and 32 vision are not new 1.0 features. Broader PDS machinery in 4/18 is bounded by 29. The two documents numbered 16 have different roles: resident-command boundary versus proposed optional SAFEFS. Neither creates automatic handoff or a supplied SAFEFS module.

## Known contradictions resolved for these manuals

- Production BRSX is v2 only. Historical descriptions do not establish a supported v1 load path; checked v3 belongs to deferred profile work.
- CPX initialization/shutdown is implemented with eight-byte live headers and the final failure/reconstruction rules. Open-ended command-context/recursive-dispatch frameworks are not invented.
- Function 182 is the registry; 208 is not an alias. Unknown metadata-1.0 records reject before publication; an old “skip defect remains” note does not describe the corrected final path.
- STATEFUL movement and prepared commit are implemented; STATE_PRESERVING export/import is reserved. Do not infer general fallible provider callbacks during disk-free RSX commit.
- TIME and optional P2DOS are independent of hardware providers. Supplied providers are read-only. Older “104/105 included” architecture wording is superseded by the lock's deferral.
- PDS is fixed HISTORY only. An old shadow-policy design does not reserve new 1.0 state or implement automatic handoff.
- Current main's FDB 1.01 and metadata are development. Released FDB remains 1.0 (001) with its matching viewer and existing menu/memory behavior.
- Hardware capability, device readiness, catalogue admission, emulator execution and physical qualification are separate claims.

## Example verification and its limits

The documentation examples are HELLO.MAC, RECORDS.MAC, TIMEQ.MAC and PING.MAC under [examples](examples/). They use ordinary BDOS, native service lookup or a CPX payload contract; they are not added to source/utility manifests or frozen disks. All four sources passed cross-assembly with z80asm 2.1 after the documented ASEG/ORG conversion, with zero errors. The emitted sizes were HELLO 175 bytes, RECORDS 790 bytes, TIMEQ 472 bytes and PING 49 bytes, including emitted reservations. PING was also assembled at 8000h and 8101h: the production relocation helper found slots 2, 14 and 27 and reproduced the alternate image exactly. Native ZSM4/LINK execution, real BDOS/device execution, lifecycle fault injection and release-media trials of these new examples have not been run; the checks do not establish those results.

The [machine-readable check record](examples/VERIFICATION.json) records source/output hashes, assembler identity, conversion and scope. No generated executable is selected for release media.

Expected execution observations for later native/packaged trials:

| Example | Success observation | Required negative case |
| --- | --- | --- |
| HELLO | One message, clean warm return | A loaded-module environment must not violate its stack/TPA bounds. |
| RECORDS | Fresh DEMO.DAT contains 00h–7Fh, closed and reread correctly; default DMA restored | Pre-existing file is not replaced; create/write/read/close errors do not claim success or erase an output. |
| TIMEQ | Prints one validated five-byte native sample | Absent/incompatible service and failed GET do not dereference/publish invalid data; never SET. |
| PING | Exact PING prints PONG and carry set | Different length/keyword declines; buffer/SP/IX/IY remain intact, including after relocation. |

## Further expansion, separate from 1.0 blockers

More language bindings, larger applications, a complete portable personality starter, further controller/hardware walkthroughs, a general stable archive SDK, broader private-ABI stabilization, and native/real-hardware trials of the new examples remain independent development/documentation work. Their absence does not reopen the frozen 1.0 feature/platform boundary.

A real error in instructions about locked behavior must still be corrected as documentation. A required binary behavior change instead needs an explicit affected-lock decision and qualification. Never implement the change silently to make a new tutorial work. Preserve BCPM-AUD-003/AUD-007 dispositions, compatibility observations, XSUB carrier workaround, ANSI size requirement, optional FDB memory workflow and the emulator-only scope of release receipts.
