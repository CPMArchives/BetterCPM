# Engineering Specification 01: Baseline Bring-Up

Status: Draft 0.1
Date: 2026-08-31

## 1. Purpose

This specification defines the first executable BetterCP/M milestone on the baseline development platform.

The milestone proves that the development tools can construct a bootable disk image, that `cpmsim` can execute BetterCP/M-owned code from that image, and that BetterCP/M machine-dependent code can perform minimal console output and raw-sector input.

It does not define the final operating-system memory map, resident-system image, CP/M logical disk format, BIOS, BDOS, CCP, or transient-program environment.

## 2. Normative language

`shall` identifies a requirement. `should` identifies a preferred choice that may be changed with a recorded reason. `may` identifies a permitted choice.

## 3. Baseline platform

The reference platform shall be z80pack Release 1.39 at repository revision `91fd28eb04e675c2127df88ed3f40675e15282e2`.

The baseline invocation shall provide:

- one 64 KiB Z80 address space;
- deterministic zero-filled memory when the reference emulator supports the `-m 00` option;
- a development disk image named `drivea.dsk`; and
- the standard `cpmsim` console and raw-disk interfaces described below.

The development disk image shall be separate from reference CP/M images and shall be reproducibly generated from repository inputs.

## 4. Milestone boundaries

The bring-up image shall contain two executable stages:

1. **Stage zero:** the 128-byte platform boot record.
2. **Stage one:** a larger diagnostic image loaded by stage zero.

Stage zero is a `cpmsim` platform implementation. Stage one is also diagnostic platform code at this milestone. Neither interface is yet a portable BetterCP/M boot interface.

Addresses and layouts marked *bring-up only* shall not constrain the later resident-system memory specification.

## 5. Development disk layout

For this milestone, `drivea.dsk` shall use the validated raw geometry:

- 77 tracks;
- 26 sectors per track;
- 128 bytes per sector; and
- 256,256 bytes total.

Sector numbering is one-based. Raw image offsets shall be calculated as:

```text
((track * 26) + sector - 1) * 128
```

The bring-up allocation shall be:

| Location | Purpose |
| --- | --- |
| Track 0, sector 1 | 128-byte stage-zero boot record |
| Track 0, sector 2 onward | Contiguous stage-one diagnostic image |
| Remaining sectors | Zero-filled and unassigned |

The number of stage-one sectors shall be an assembly-time constant consumed by stage zero and checked by the image-building tool. Stage one shall initially fit within the remaining 25 sectors of track 0 so that stage zero need not implement track advancement for the first milestone.

The image-building process shall fail if either stage exceeds its assigned space.

## 6. Entry state

The platform loads exactly 128 bytes from the beginning of `drivea.dsk` into `0000h` through `007Fh` and transfers control to `0000h`.

Stage zero shall not depend on initial general-purpose or alternate-register values, interrupt state, interrupt mode, stack pointer, or RAM contents outside the loaded boot record.

Before using the stack, a stage shall explicitly establish its stack pointer.

Stage zero shall disable maskable interrupts before relying on an interrupt-free environment. It shall not enable interrupts during this milestone.

## 7. Stage-zero requirements

Stage zero shall:

1. begin execution at `0000h`;
2. establish every processor value on which it depends;
3. load the configured number of stage-one sectors from track 0, beginning at sector 2;
4. place stage one contiguously beginning at `0100h`;
5. test the raw-disk status after each read;
6. transfer control to `0100h` only after all reads succeed; and
7. enter a stable failure loop if a read fails.

The `0100h` load address is **bring-up only**. It deliberately resembles a CP/M transient-program origin but does not establish a BetterCP/M program-loading or resident-memory decision.

Stage zero should avoid stack use. If stack use is necessary, its stack region shall be explicitly documented and shall not overlap unread stage-one data or the destination range.

Stage zero may emit a single diagnostic character before loading and a distinct single character on failure, provided that doing so does not prevent it from fitting in 128 bytes.

Unused bytes in the boot record shall be zero-filled. The assembled stage-zero binary shall be exactly 128 bytes.

## 8. Raw-disk operation

Stage zero shall use the baseline `cpmsim` disk ports:

| Port | Operation |
| ---: | --- |
| 10 | Select drive |
| 11 | Select track |
| 12 | Sector number, low byte |
| 13 | Command (`0` = read, `1` = write) |
| 14 | Status |
| 15 | DMA address, low byte |
| 16 | DMA address, high byte |
| 17 | Sector number, high byte |

For this milestone, stage zero shall select drive 0 and track 0, set both bytes of the sector number, set both bytes of the DMA destination, issue one read command per sector, and examine status before advancing.

The implementation shall document the observed success and failure status values from the pinned emulator. If the baseline platform specification or emulator source already defines them unambiguously, that definition shall be cited in the source comments and acceptance record.

## 9. Stage-one requirements

Stage one shall:

1. begin execution at `0100h`;
2. establish a private diagnostic stack near the top of memory without assuming its initial contents;
3. output the exact line `BetterCP/M stage 1` followed by carriage return and line feed;
4. demonstrate a second raw-sector read into a non-overlapping scratch buffer;
5. verify the returned bytes against deterministic data placed in the disk image by the build process;
6. output `disk read ok` followed by carriage return and line feed on success; and
7. output `disk read failed` followed by carriage return and line feed on failure.

After reporting its result, stage one shall enter a stable halt or polling loop. It shall not return into stage zero.

The stage-one stack address, scratch-buffer address, and verification-data sector are bring-up-only values and shall be collected in one documented platform constants module rather than dispersed as literal values.

## 10. Console operation

The diagnostic console implementation shall use:

| Port | Operation |
| ---: | --- |
| 0 | Console input status |
| 1 | Console data input/output |

Only console output is required by this milestone. Stage-one message code shall call one local character-output routine so that direct port access is confined to the diagnostic platform module.

No CP/M console semantics or compatibility-visible BIOS entry point is established by this routine.

## 11. Source and generated artifacts

The repository shall distinguish handwritten sources from generated artifacts.

At minimum, the milestone shall provide:

- stage-zero assembly source;
- stage-one assembly source;
- one platform constants source;
- a reproducible build procedure;
- a reproducible disk-image construction procedure;
- automated size and layout checks; and
- a scripted or precisely documented reference-emulator run.

Generated binaries and disk images should be placed in a build directory excluded from normal source control. Release artifacts may later be attached to tagged releases.

ZSM4 is the canonical BetterCP/M assembler. The project shall pin and redistribute a verified ZSM4 source and binary release under its GNU GPL v2 terms. Canonical BetterCP/M source shall use standard Zilog mnemonics and shall avoid assembler aliases, synthetic instructions, and macros disguised as processor instructions.

Digital Research LINK 1.3 is the canonical BetterCP/M linker. It is redistributable as Digital Research CP/M development material under the nonexclusive CP/M grant clarified on 9 July 2022. The project shall preserve its Digital Research attribution, the applicable grant notice, provenance, and a cryptographic hash of the distributed binary. The selected binary shall be verified with ZSM4 `.REL` output.

The build runner remains to be selected by the Source and Build Conventions specification. The selection shall be made before implementation begins and shall support automated, non-interactive builds with symbol listings or maps sufficient to verify addresses and sizes.

The assembler shall be freely redistributable. Its license shall permit the project to redistribute the assembler with BetterCP/M development materials and shall not impose noncommercial-use, per-user licensing, or similar field-of-use restrictions. Any runtime components required to execute the redistributed assembler shall satisfy the same requirement. License texts and required notices shall be preserved with redistributed copies.

## 12. Diagnostic behavior

Development diagnostics may be conditionally assembled or omitted from later production images.

Diagnostic code shall not be treated as a permanent System Service, BIOS extension, or application interface.

The first milestone should favor deterministic output and simple failure states that can be recognized by an automated harness.

## 13. Acceptance criteria

The milestone is complete when all of the following are demonstrated from a clean checkout:

1. The documented build procedure completes without manual binary editing.
2. The stage-zero artifact is exactly 128 bytes.
3. The stage-one artifact fits within its declared sector allocation.
4. The generated `drivea.dsk` is exactly 256,256 bytes.
5. The boot record and stage-one image occupy their specified raw sectors.
6. The pinned `cpmsim` enters stage zero at `0000h`.
7. Stage zero loads stage one at `0100h` and transfers control to it.
8. The emulator output contains exactly one success sequence:

   ```text
   BetterCP/M stage 1
   disk read ok
   ```

9. A deliberately corrupted or unavailable verification sector produces the defined failure message or stable stage-zero failure behavior, as appropriate to the injected fault.
10. Repeating the clean build produces byte-identical stage-zero, stage-one, and disk-image artifacts.

## 14. Explicit non-decisions

This specification does not decide:

- the final resident-system base address;
- the final TPA upper boundary;
- the CCP size or restoration mechanism;
- the final system-image format;
- the portable boot-boundary contract;
- the internal Hardware-Abstraction interface;
- the compatibility-visible BIOS implementation;
- the initial CP/M logical disk format;
- the BDOS implementation or interface translation; or
- the cold-start and warm-start state model beyond this diagnostic milestone.

Those decisions shall be made in later Phase 2 specifications using evidence from this bring-up where relevant.

## 15. Open items before implementation

The following narrow items must be resolved before code is committed for this milestone:

1. Pin the verified ZSM4 source and binary version and record its GNU GPL v2 redistribution obligations.
2. Pin the verified Digital Research LINK 1.3 binary and record its provenance, hash, attribution, and the CP/M redistribution grant clarified on 9 July 2022.
3. Select the build runner and host-language tool used to construct `drivea.dsk`.
4. Confirm the pinned `cpmsim` disk-status success and error encodings from source or a deterministic experiment.
5. Choose the bring-up-only stage-one stack, scratch buffer, and verification sector values.
6. Record the exact reference-emulator command line.

Resolution of these items shall update this specification or the Source and Build Conventions specification; they shall not remain implicit in implementation code.
