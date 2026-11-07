# TCAP private native-reference package

This follow-up packages the private manager/owner experiment into installable
Model 4 reference media. It does not allocate the proposed public TCAP ABI,
activate TCAP in a production profile, migrate TYPE/TED/HELP, deliver HELP, or
assign a release. Physical hardware and native-assembler parity remain separate
qualification work.

## Terminal workflow

A legacy application retains its configured terminal protocol. The user chooses
and loads the corresponding monitor personality. For example:

```text
RSX LOAD M4SCRN
RSX LOAD ADM3A
ADMAPP
RSX UNLOAD ADM3A
RSX LOAD ANSI
ANSIAPP
RSX UNLOAD ANSI
RSX UNLOAD M4SCRN
```

M4SCRN is the shared screen backend; ADM3A and ANSI are protocol personalities.
The backend can remain loaded across the switch. The small ADMAPP and ANSIAPP
fixtures address the same row/column using their respective protocols, emit
markers through ordinary BDOS console output, and return through real warm boot.
No TCAP provider is required for either legacy application. VT52 remains an
available personality; this media campaign specifically exercises ADM3A and ANSI.

The separate XTCAP carrier is the existing private experiment appended to ANSI.
Loading it later for TCAP probes is an explicit test operation. It does not
silently replace the user's ADM3A personality. These probes bind known private
entry offsets and do not claim public Discover/Admit conformance.

## Package and installation boundary

The package uses the private `XTNP` version 1 header and 240 protected 128-byte
records. It is deliberately incompatible with ordinary `BCSY`/OFF=2 packages.
A matching `INSTALL.COM` is generated from the existing SYSGEN source with private
layout constants, package magic and a checksum gate before the first write. No
production utility source is changed. The reference disk includes matching
R3PACK, R3CACHE, SCRN, personalities, owner and RSX command utility.

| Region | First physical sector | Capacity |
| --- | ---: | ---: |
| ROM-loaded bootstrap | 0 | 512 bytes |
| Stage one | 1 | 512 bytes |
| Resident system | 2 | 15 sectors |
| Native reloader, without obsolete selector tail | 17 | 2 sectors |
| Control overlay | 19 | 2 sectors |
| Entry, carrier, mover, resolver helpers | 21, 23, 25, 27 | 2 sectors each |
| Relocatable command environment | 29 | 13 sectors |
| Remaining protected space | 42 | 18 sectors |
| CP/M directory and allocation area | 60 | OFF=3, DSM=384 |

The fixed resident span remains 7,612 bytes, including the 1 KiB permanent
reservation from the preceding experiment. Loaded resident capacity is 7,680
bytes; unloaded record-aligned TPA remains 53,248 bytes (52 KiB). Optional owner
allocation remains 2,560 bytes with its existing cache-footer page. No new
permanent TCAP allocation is introduced by packaging.

The native package starts with a canonical cylinder-form A: binding. The
installer's normal destination normalization must reproduce those exact sealed
bytes. Its CRC gate rejects differently patched packages instead of installing a
system whose bootstrap pin would fail. This reference installer supports the
qualified matching geometry; it is not a general profile conversion tool.

An existing OFF=2 filesystem must not be reinterpreted or expanded in place.
The qualification destination is independently formatted with OFF=3 before
installation. File preservation applies to that matching filesystem, not to an
OFF=2-to-OFF=3 migration. Distribution tooling and production configuration-save
support for sealed reference images remain separate integration work.

## Destination admission fix

Full-machine installation exposed an existing Model 4 configuration bug:
`DC_VALIDATE` loaded the reserved-surface adapter field into A, then branched on
stale flags from the physical-device comparison. A valid zero adapter was
rejected, and the requested physical device was overwritten before lookup.
The production configuration source now tests that field through B, preserving
A. A shorter equivalent bit test pays for both extra instruction bytes; the
control overlay still fits exactly 1,024 bytes. No interface or memory-map change
is required. Model II's separate control implementation is unchanged.

`tools/test_model4_config_admission.py` executes the actual configuration entry
for all four physical devices, zero/nonzero adapter values and both incoming
zero-flag states (32 cases). It traps the following resident lookup/rejection,
checking both admission and preservation of the requested device. The native
installation campaign additionally exercises the complete configured destination
path through ordinary BDOS/BIOS.

## Cold chain and warm reconstruction

The ROM-loaded bootstrap is the trusted starting point. Its final 128-byte area
holds a CRC16 routine and a pinned stage-one check; the saved startup record at
bytes 128–383 remains separate. Stage one checks the entire 15-sector resident
load, including padding, before entering BIOS BOOT. The bootstrap error message
is moved out of the startup-record area as part of this private generated source.

The resident root then applies the existing matching-system gates to the native
reloader, command environment and selected helpers. These CRCs detect corruption;
they are not authentication against malicious media. SHA-256 manifests identify
the exact package, sources and executable artifacts for reproducibility. The
matching identity conservatively freezes source, metadata and local assembly/tool
inputs, including version expansion helpers and the selected development-display
state. The build rejects changes to those inputs during assembly. Rebuilding
removes a previous full-machine qualification result before emitting new media.

The reference workflow explicitly loads/unloads legacy personalities before
loading XTCAP. TSCOPE executes private Begin/End, TBEGIN returns through the real
warm path with a live scope and no intervening console output, and TCHECK checks
idle state and the preserved first global validity value. Finally all optional
providers are removed and the original unloaded TPA is checked. The earlier
516-case campaign retains its more detailed stale-token, reservation-failure,
publication-order and cache reconstruction assertions.

## Reproduction and evidence

From the repository root, using the pinned environment described in the
[prototype instructions](../../tools/prototypes/tcap/README.md):

```sh
build/tcap-feasibility/venv/bin/python tools/prototypes/tcap/manager_integration.py --native-package
python3 tools/prototypes/tcap/qualify_native_package.py
```

The first command builds and runs the earlier 516 checks, then emits the private
package under `build/tcap-manager-integration/native-package/`. Building a package
is reported separately from qualifying it. The second command requires the local
Model 4 emulator and writes `qualification.json` only after all assertions pass.
It removes a stale result before starting. Explicit guest checkpoints replace
fixed keyboard delays; each phase runs through stock CP/M SUBMIT processing and
waits for a key before advancing. Batch windows close automatically.

Qualification covers source-media cold boot and personality switching, private
scope/warm/unload probes, installing the protected area with the actual transient
installer, verifying preservation of the entire file area, and repeating the
workflow from the installed system's cold boot. CPU checksum checks exercise
stage-one, resident and installer boundary corruptions; full-machine damaged
stage-one, resident/padding, reloader and command media must not reach a prompt.

Generated disks and executables are build outputs, not committed production
artifacts. Reviewed reports and transcripts are retained alongside the design;
rebuild before installation, and use only disposable matching reference media.

The [evidence index](evidence/tcap-native-package/README.md) retains the source
closure and integration results, package manifest, configuration regression
record, full-machine qualification report and guest transcripts. Production
configuration verification is recorded separately from private TCAP acceptance.

## Recorded result

The [final qualification](evidence/tcap-native-package/qualification.json) passed
on 2026-11-07. The matching identity is
`e32a02030e7159e505876fe772ab4092`, with 1,485 frozen source/metadata/tool inputs.

| Check | Result |
| --- | --- |
| Earlier manager/native/owner campaign | 516 checks passed |
| Bootstrap/resident/installer checksum CPU cases | 29 cases passed |
| Configuration admission | 32 cases passed in each of default and reference builds |
| Default production build | 6,588-byte resident; 1,024-byte control overlay |
| Source and installed-system workflows | Both passed all 15 operations |
| Installation | All 240 protected records verified; entire file area unchanged |
| Corrupted stage one, resident, resident padding, reloader and CCP | All stopped before a command prompt |
| Complete optional-provider unload | Unloaded 52 KiB TPA restored |

The private package retains a 7,612-byte resident, 339-byte stage one and
461-byte bootstrap. `SYSTEM.SYS` is 30,848 bytes including its header, and the
matching installer is 6,489 bytes. No additional permanent TCAP bytes are charged
beyond the preceding 1 KiB reservation.

## Public-contract follow-up

The [public TCAP ABI/admission contract](TCAP-Public-ABI.md) now defines the
implementation target. This package remains private XTCP evidence; its token-only
dispatcher, MCON 1.3, carrier metadata and measured sizes do not implement BMET 3,
MCON 1.4 or the public envelope. It must not advertise public TCAP by changing IDs.
Utility migrations and release assignment remain deferred.
