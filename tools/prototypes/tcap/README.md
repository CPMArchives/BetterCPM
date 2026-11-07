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
