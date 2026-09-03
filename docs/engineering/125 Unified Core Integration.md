# Unified core production integration

## Scope

The boot-image build now uses `src/bdos/unified.mac` for standard BDOS calls.
Neither `dispatch.mac` nor `directory.mac` is linked into the resident image.
The old sources and legacy unit harnesses remain reference material; current
core verification uses `test_unified_bdos.py` and `test_system.py`.

This completes integration, not full historical CP/M conformance certification.
Earlier physical compliance results belong to the previous implementation and
must be rerun on this one. DPB/geometry coverage beyond the tested machine,
disk-error recovery, and complete console/FCB edge-case coverage remain part
of that regression; merely having every function selector is not proof of it.

## Runtime boundary

Selectors 200 and above enter the protected extension dispatcher before the
standard core acquires its private stack. The extension dispatcher has its own
128-byte stack, allowing RSX loading to invoke standard filesystem calls without
destroying the outer control frame. Functions 200, 202, 204, 205 and 206 retain
their previous contracts; unclaimed extension selectors return zero. Installed
RSXs still intercept calls before the fixed core through the movable gateway.

The protected file-reader entry points at D60C, D612 and D624 are now small
adapters, not a second filesystem. They invoke unified Select/Open/Read and
preserve the caller's current drive, user and DMA address. Module files are
read from A0 regardless of the transient's DU. Private core state addresses are
resolved from the exact current assembler listing into a generated `core.inc`;
no fixed-address copy of that state is maintained.

BIOS-owned descriptors and CSV/ALV workspaces are assembled separately at
DA00h. The BIOS selects those descriptors directly. Version text continues to
be generated from `metadata/subsystem-versions.tsv`, with BDOS implementation
1.2/API 1.1 and BIOS implementation 1.1/API 1.0.

## Measured memory

| Component | Bytes |
| --- | ---: |
| Unified standard BDOS, including private state and stack | 3,373 |
| Extension controls, version descriptor, adapters and private stack | 631 |
| BIOS disk descriptors and CSV/ALV workspaces | 408 |
| Protected filename stream reader | 216 |
| RSX manager | 875 |
| Gateway / ECB / initial CPX reconstruction records | 248 |
| Command-environment reloader | 796 |
| BIOS code / local state | 1,089 |
| Sum of component images | 7,636 |

The standard core has 211 bytes free beneath its 3,584-byte ceiling. Extension
support is explicitly additional, not part of the claimed core saving. The
component total excludes address-space gaps and separately reserved buffers,
history and module allocations. The resident file still spans C000h..F340h
(13,121 bytes) in the development layout; TPA remains approximately 47K.
Packing/rebasing the complete protected layout is a separate task. No larger
TPA is claimed from this integration alone.

## Corrections found at the integration boundary

- Restore Backspace's output byte and cooked input echo for BS/TAB/CR/LF.
- Preserve the requested CR position after random I/O; only sequential I/O
  advances it.
- Restore modulo-32 BDOS user selection and account for those users when
  scanning live directory entries.
- Check dirty Close protection and failed lookup before committing an entry.
- Restore the file-read-only diagnostic and terminal warm-boot path for writes.
- Reject physical login failures rather than treating them as directory end.
- Preserve IX on nonlocal error exits from arbitrarily deep helper calls.
- Explicitly clear carry after a successful shared physical-position mapping.

Integration fixtures now respect the S2 modified-bit protocol. Tests that
change media behind the BDOS cache explicitly invalidate that cache. These
changes do not relax public return/status or disk-content assertions.

## Verification

Core and public-gateway tests cover all 39 defined selectors within 0..40,
stack/register restoration, cooked input, directory and record transfers,
protected-reader DU/DMA preservation, extended hooks and WBOOT-to-CCP dispatch.
Native CP/M builds must match cross builds for the core, support units, BIOS
and file reader. Emulator lifecycle tests exercise CPX load/unload, fallback,
post-reconstruction directory writes, ordered two-RSX dispatch, warm-boot
persistence, first-member removal and TPA restoration.

Completed on the final image: unified core, public gateway, BIOS, service
inventory, subsystem versions, CPX/RSX format validation, native parity,
CPX manager, CPX/WBOOT physical writes, RSX manager, BASIC/transient command
completion, visible Ctrl-C warm boot, and the Model 4 DIR/HELLO boot test.
The generated DMK SHA-256 is
`b6227cdb70811a54770a09aef488d89ea4cbc70e4fc4095ae79ae55457e9aac9`.

Run the production build sequence in README, including the two new native
support checks:

```
python3 tools/build_native_bdos.py --component extensions
python3 tools/build_native_bdos.py --component tables
```
