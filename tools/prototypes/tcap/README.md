# Private TCAP feasibility campaign

Experimental XTCP 0.1 slice, not the proposed public TCAP request ABI. This is
an isolated CPU/model campaign; it never edits production source or packages a
release. Generated binaries, listings, a private environment and reports live
under `build/tcap-feasibility/`. The baseline BIOS is rebuilt in `build/bios/`
for its matching Model 4 symbols. No distribution image/manifest is changed.

From the repository root:

```sh
python3 -m venv build/tcap-feasibility/venv
build/tcap-feasibility/venv/bin/python -m pip install -r tools/requirements-monitor-tests.txt
build/tcap-feasibility/venv/bin/python tools/prototypes/tcap/campaign.py
```

The default assembler is `~/bin/z80asm`; pass `--assembler` for a compatible
alternative. Existing repository assembler/profile validation still applies.
The command removes a stale generated report before work and exits nonzero on
assembly/assertion failure. On success, `report.json` separately records CPU
checks as PASS and production feasibility as blocked when appropriate. A PASS
is not a production acceptance decision.

`owner.inc` is appended to an in-memory copy of the real ANSI personality.
The private dispatcher uses A=2 begin, 3 takeover, 4 end, 7 describe, with DE
pointing to a 16-byte token. These are private experimental conventions, not
candidate/public 1.0 conformance. It omits full request validation, Discover/Admit,
public Recover/Release, a boot-global identity allocator and registry admission.
The fixture supplies owner validity and a configured reverse mapping.

`coordinator.mac` is linked out of line against each relocated owner. It provides
safe-stack rendering-plus-real-BDOS-CR/LF recovery, a routing observer around the
actual BIOS CONOUT router, and a busy guard before the actual commit engine.
These are fixture bridges, not installed production hooks. Its fatal HALT is
recognized explicitly by the runner's unsupported-HALT exception; arbitrary
emulator exceptions remain failures. A simulated reset/retry after that halt is
a fixture operation, not a claim of live machine recovery from a fatal stop.

The host fixture retains the shared BIOS router but substitutes the basic
hardware-output leaf with the host port convention; it is not a full cpmsim BIOS.
Model 4 output is checked in video RAM; host output is independently rendered by
pyte. Real BDOS consumes ^P/^C and performs column/echo handling. Keyboard status,
input and a nonreturning safe-stack warm entry are deterministic injected fixtures.
No live reloader, protected-ROM or native-display campaign is claimed.

The campaign attempts the normal BRSX builder. The current naïve extension fails
the fixed relocation-directory limit. It records the exact error and emits no
loadable XTCAP.RSX; raw code is rebased for CPU experiments only. Do not load it
as a production provider or widen the carrier header to make this report green.

See the [measured report](../../../docs/engineering/TCAP-Feasibility-Results.md)
for current findings, resource limits and the remaining integration work.

## Carrier and packed-placement follow-up

Use the same pinned environment, then run:

```sh
build/tcap-feasibility/venv/bin/python tools/prototypes/tcap/placement.py
```

This retains the original failed slice for comparison and builds a private XTCP
0.2 candidate with indexed owner state and assembler-checked relative branches.
It moves the coordinator/guard into the optional personality, stages source
copies under `build/tcap-placement/packed-core/`, and rebuilds a complete reference
Model 4 resident image. Seven equivalent recovered BIOS bytes pay for the seven-byte
private routing hook. Production `src/` and layout files are not edited.

The normal BRSX builder and real carrier/metadata/snapshot validators now accept
the generated `build/tcap-placement/XTCAP.RSX` with the existing header. The private
MCON probe 25 has no public allocation or production coordinator/version admission;
**do not install this carrier or staged core in production profiles**.

`placement-report.json` is written only after all checks pass; a stale copy is
removed before the run. `packed-core.patch` is the reviewable staged source diff.
The campaign checks behavioral cases, parser parity against the original, actual
STATEFUL movement, legacy IOBYTE/status/fallback, independent video scrolling and
existing CAPS/physical-fetch regressions. Idle publication rebinding and warm entry
remain explicit fixtures, not claims of a complete real-manager/reloader install.

The [measured follow-up](../../../docs/engineering/TCAP-Placement-Results.md)
distinguishes the two resolved feasibility gates from remaining production,
ROM/native and whole-system stack qualification work. Utility migrations and
release assignment remain deferred.

## Transaction and command-return follow-up

```sh
build/tcap-feasibility/venv/bin/python tools/prototypes/tcap/system_paths.py
```

This third isolated campaign stages guards inside the actual finalizer and
commit entries, and recovery inside CCP initialization/prompt and both reloader
entries. It fits the original overlay/carrier budgets, repeats the behavioral
checks, runs the existing full commit regression, and exercises ten full Model 4
reloader cases with controlled services and synthetic CPXs. See the
[results and precise limits](../../../docs/engineering/TCAP-System-Paths-Results.md).

Outputs remain under `build/tcap-system-paths/`. Private MCON controls 25/26/27
and the unallocated experimental MCON 1.3 requirement are not public ABI changes.
The production metadata validator must reject this owner: positive system/version
admission and global validity allocation remain unresolved. The campaign emits
no installable carrier. Do not install its staged core, commands or loader.
Utilities and release assignment remain deferred.

## Matching-system and global-validity follow-up

```sh
build/tcap-feasibility/venv/bin/python tools/prototypes/tcap/matching_validity.py
```

This fourth private campaign combines a permanent matched-system root, positive
metadata admission, a saturating boot-global validity allocator and prepared
validity publication through the real commit path. It verifies stale-token
rejection after unload/same-address reload and measures the permanent RAM and
boot-volume cost. See the [results and integration boundaries](../../../docs/engineering/TCAP-Matching-Validity-Results.md).

Outputs remain under `build/tcap-matching-validity/`. The private root consumes
512 permanent bytes; its reference boot volume uses OFF=3/DSM=384 and is
incompatible with existing OFF=2 system disks. No production source or media is
modified. The CPU artifact gate is invoked explicitly by the campaign; file-reader
front doors and full finalizer/context record construction still need integration.
This is not an installable TCAP system or a public ABI allocation. Utility
migrations and release assignment remain deferred.

## Native manager and load-front-door integration

```sh
build/tcap-feasibility/venv/bin/python tools/prototypes/tcap/manager_integration.py
```

This fifth campaign runs actual context producers/finalizer and native/file-backed
loading front doors, including cache-footer-aware movement and global validity
publication. It uses the existing C CPU/filesystem fixture, which requires a C
compiler and the local `~/projects/git/z80pack/z80core` source checkout in addition
to the environment above. Generated files stay under `build/tcap-manager-integration/`.
See the [results, footprint and remaining boundaries](../../../docs/engineering/TCAP-Native-Manager-Integration.md).

The native candidate reserves 1 KiB permanently, uses fifteen resident boot sectors
and retains the experimental OFF=3/DSM=384 boot-volume layout. Its native selector
is permanent; the old image-builder selector tail is not a compatible package.
No production source, utility, installed media or release assignment changes.
This is not an installable distribution or a completed public TCAP request ABI.

## Installable native-reference package

```sh
build/tcap-feasibility/venv/bin/python tools/prototypes/tcap/manager_integration.py --native-package
python3 tools/prototypes/tcap/qualify_native_package.py
```

This optional follow-up emits a private OFF=3 Model 4 disk, `XTNP` SYSTEM.SYS,
and matching INSTALL.COM under `build/tcap-manager-integration/native-package/`.
The installer refuses ordinary OFF=2 packages and checks sealed system bytes
before writing. Only independently formatted OFF=3 destinations are supported;
this is not an in-place filesystem conversion. The production layout is unchanged; a companion Model 4 configuration fix
restores existing destination admission within the same overlay size. Utility
migrations and release assignment remain deferred.

The full-machine qualifier requires the local trs80gp executable and its macOS
application services. It operates only on disposable generated images and closes
its batch windows. Stock SUBMIT records and explicit blocking guest checkpoints
avoid timing-dependent keyboard scripts. The ADM3A app / unload / ANSI app switch
uses ordinary BDOS output and a shared M4SCRN backend; separate private XTCP probes
exercise warm reconstruction and unload. `qualification.json` exists only after
all qualification assertions pass. See the [package report](../../../docs/engineering/TCAP-Native-Package-Results.md)
for the trust chain, disk layout and remaining production boundaries.
