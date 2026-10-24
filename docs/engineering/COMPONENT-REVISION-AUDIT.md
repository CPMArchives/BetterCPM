# Component revision migration audit

Status: review increment; 2026-10-24. No numbering or executable changes.

## Evidence and scope

Audited current main `380826044379324f8eb5a50d4f7e6e1e70434f7c`, including merged policy PR #487. The original local checkout is still at `6cfa762` with its earlier policy edits; it was not reset. Current source changes were applied to a separate inspection copy using the GitHub comparison. Direct Git fetch failed DNS resolution. This report and JSON are new repository deliverables, not a claim that the old checkout is synchronized.

The companion `COMPONENT-REVISION-AUDIT.json` records every selected identity, source roots, builders and conservative file-level dependency candidates. Candidates expose review work; they are not safe to use directly for revision enforcement. In particular, Python import closure overincludes unused builder functions, and constructed paths can escape static discovery.

## Inventory and migration baseline

The inventory has five subsystems, 36 existing utility-registry entries, MOVE and WARM, and eight additional independently loadable modules: 51 identity records. RCP is included among the 36 existing rows. No revision is assigned by this audit.

| Component | Placement | Current version | Existing counter | Primary source | Builder |
| --- | --- | --- | --- | --- | --- |
| utility:STAT | System | 1.0 | 003 | `src/utilities/stat.mac` | `tools/build_stat.py` |
| utility:COPY | System | 1.0 | 007 | `src/cpx/rcp.mac` | `tools/build_rcp_transients.py` |
| utility:DIR | System | 1.0 | 008 | `src/cpx/rcp.mac` | `tools/build_rcp_transients.py` |
| utility:CONFIG | System | 1.0 | 016 | `src/utilities/config.mac` | `tools/build_config.py` |
| utility:DUP | System | 1.0 | 007 | `src/utilities/dup.mac` | `tools/build_dup.py` |
| utility:TIME | System | 1.0 | 003 | `src/utilities/time.mac` | `tools/build_time.py` |
| utility:SYSGEN | System | 1.0 | 008 | `src/utilities/sysgen.mac` | `tools/build_disk_utilities.py` |
| utility:SUBMIT | System | 1.0 | 003 | `src/utilities/submit.mac` | `tools/build_batch.py` |
| utility:XSUB | Utilities | 1.0 | 003 | `src/utilities/xsub.mac` | `tools/build_batch.py` |
| utility:CPX | System | 1.0 | 004 | `src/utilities/cpx.mac` | `tools/build_cpx_utility.py` |
| utility:RSX | System | 1.0 | 004 | `src/utilities/rsx.mac` | `tools/build_rsx_utilities.py` |
| utility:USER | Unassigned/deferred | 1.0 | 006 | `src/cpx/rcp.mac` | `tools/build_rcp_transients.py` |
| utility:CLS | Unassigned/deferred | 1.0 | 007 | `src/cpx/rcp.mac` | `tools/build_rcp_transients.py` |
| utility:VER | System | 1.0 | 008 | `src/cpx/rcp.mac` | `tools/build_rcp_transients.py` |
| utility:RCP | System | 1.0 | 015 | `src/cpx/rcp.mac` | `tools/build_rcp_cpx.py` |
| utility:SYSBUILD | Native build | 1.0 | 003 | `src/utilities/sysbuild.mac` | `tools/build_disk_utilities.py` |
| utility:RESPACK | Native build | 1.0 | 003 | `src/utilities/respack.mac` | `tools/build_disk_utilities.py` |
| utility:RLMBUILD | Native build | 1.0 | 003 | `src/utilities/rlmbuild.mac` | `tools/build_disk_utilities.py` |
| utility:ERA | System | 1.0 | 005 | `src/utilities/era.mac` | `tools/build_era.py` |
| utility:REN | System | 1.0 | 009 | `src/utilities/ren.mac` | `tools/build_ren.py` |
| utility:TYPE | System | 1.0 | 007 | `src/utilities/type.mac` | `tools/build_type.py` |
| utility:PIP | System | 1.0 | 029 | `src/utilities/pip.mac` | `tools/build_pip.py` |
| utility:ADMTST | System | 1.0 | 004 | `src/utilities/admtst.mac` | `tools/build_adm3a.py` |
| utility:VT52TST | System | 1.0 | 004 | `src/utilities/vt52tst.mac` | `tools/build_vt52.py` |
| utility:ANSITST | System | 1.0 | 003 | `src/utilities/ansitst.mac` | `tools/build_ansi.py` |
| utility:ED | System | 1.0 | 003 | `src/utilities/ed.mac` | `tools/build_ed.py` |
| utility:DUMP | Utilities | 1.0 | 004 | `src/utilities/dump.mac` | `tools/build_dump.py` |
| utility:DDT | Utilities | 1.0 | 002 | `src/utilities/ddt.mac` | `tools/build_ddt.py` |
| utility:SQ | Utilities | 1.0 | 004 | `src/utilities/sq.mac` | `tools/build_sq.py` |
| utility:USQ | Utilities | 1.0 | 004 | `src/utilities/usq.mac` | `tools/build_usq.py` |
| utility:CR | Utilities | 1.0 | 004 | `src/utilities/cr.mac` | `tools/build_cr.py` |
| utility:UNCR | Utilities | 1.0 | 004 | `src/utilities/uncr.mac` | `tools/build_uncr.py` |
| utility:LZH | Utilities | 1.0 | 004 | `src/utilities/lzh.mac` | `tools/build_lzh.py` |
| utility:UNLZH | Utilities | 1.0 | 004 | `src/utilities/unlzh.mac` | `tools/build_unlzh.py` |
| utility:NOAH | Unassigned/deferred | 1.0 | 004 | `src/utilities/noah.mac` | `tools/build_noah.py` |
| utility:BYE | System | 1.0 | 001 | `src/platform/z80pack/bye.mac` | `tools/build_z80pack_bye.py` |
| utility:MOVE | Unassigned | Unassigned | None | `src/cpx/rcp.mac` | `tools/build_rcp_transients.py` |
| utility:WARM | Development/unassigned | Unassigned | None | `src/utilities/warm.mac` | `tools/build_warm.py` |
| subsystem:BDOS | System | 1.10 | None | `src/bdos/unified.mac` | `tools/build_bdos.py` |
| subsystem:BIOS | System | 1.14 | None | `src/bios/bios.mac` | `tools/build_bios.py` |
| subsystem:CCP | System | 2.0 | None | `src/ccp/ccp.mac` | `tools/build_ccp.py` |
| subsystem:CPX | System | 2.0 | None | `src/system/extens.mac` | `tools/build_system.py` |
| subsystem:RSX | System | 2.0 | None | `src/system/r3carr.mac` | `tools/build_rsxloader.py` |
| module:ZPRTC | System | 0.2 | None | `src/rsx/zprtc.mac` | `tools/build_zprtc_rsx.py` |
| module:FREHDCLK | System | 0.2 | None | `src/rsx/frehdclk.mac` | `tools/build_frehd_time_rsx.py` |
| module:ADM3A | System | 1.1 | None | `src/rsx/adm3a.mac` | `tools/build_adm3a.py` |
| module:VT52 | System | 1.3 | None | `src/rsx/vt52.mac` | `tools/build_vt52.py` |
| module:ANSI | System | 1.1 | None | `src/rsx/ansi.mac` | `tools/build_ansi.py` |
| module:M4SCRN | System | 1.7 | None | `src/rsx/screen/model4.mac` | `tools/build_screen_backends.py` |
| module:ANSISCRN | System | 1.7 | None | `src/rsx/screen/ansi-host.mac` | `tools/build_screen_backends.py` |
| module:BATCHIO | Utilities | 1.0 | None | `src/rsx/batchio.mac` | `tools/build_batch.py` |

Existing counters are migration baselines, not pre-approved numbers for changed binaries. Metadata-only import preserves them; when banners or carrier metadata alter executable bytes, affected existing components advance once for the publication change set. Newly tracked subsystems/modules begin at 001 when adopted, without manufacturing earlier revision history. Implementation versions remain unchanged unless behavior or compatibility warrants a change.

ZSM4 and LINK are external dependencies. They receive no BetterCP/M versions, revisions or query patches. Retain upstream versions and exact artifact/provenance checksums only. Their current presence on Utilities media does not make them BetterCP/M components. SYSINFO/BIOSINFO/DISKINFO/MEMINFO remain a separate project.

## File-level ownership and dependency findings

| File or input | Identity owner / consumers | Migration treatment |
| --- | --- | --- |
| `src/bdos/unified.mac` | BDOS | Production core; current implementation is 1.10, API 1.2. `dispatch.mac` / `dirsvc.mac` are not automatically production dependencies merely because they share the directory. |
| `src/bios/bios.mac`, `disk.mac`, `tables.mac`; selected platform BIOS/includes | BIOS | Record actual target selection; boot/initialization belongs to BIOS. |
| `src/bios/config.mac` and platform CONFIG overlay | BIOS control overlay, consumed by CONFIG and system construction | Distinguish the executable overlay from editable CONFIG.BIN data. Symbol links from BDOS/extensions/disk are real build inputs. |
| `src/ccp/ccp.mac`; platform CCP reload files; `src/system/command-stage1.mac`, `command-stage2.mac` | CCP | Include checked command-loader builder and selected layout. |
| `src/system/extens.mac` | Mixed BDOS adapters, CPX control, RSX control and version descriptor | Attribute selected sections to BDOS/CPX/RSX and emitted shared bytes to all affected owners; do not give the file a new independent counter. |
| `src/system/gateway.mac`, `fileload.mac`, `part8-*`, `part9-*`, `part10-*` | Mixed command loading / extension dispatch / RSX reconstruction | Maintain explicit multi-owner edges by emitted section and builder; command-loading changes implicate CCP, RSX transaction changes RSX, CPX admission CPX. Final section split remains an implementation review item. |
| `src/system/r3*.mac`, RSX planner/slots/mover/resolver/scheduler files; platform `rsxsel.mac` | RSX facility | R3PACK and each helper get individual checksums, no extra revision sequences. Some helpers are combined into one slot: file count is not slot count. |
| `src/cpx/rcp.mac`, selected `src/cpx/*.inc` | RCP and transient fallbacks | DIR/USER/CLS/VER/COPY/MOVE builders retain complete command bodies. A change to another embedded command can change their binary even when its entry point is unused. |
| `tools/build_rcp_transients.py:copy_source` and COPY-only fragments | COPY, not automatically RCP/MOVE | Source transformation must be recorded per output, not per shared Python file alone. DIR has its own transformation too. |
| `src/utilities/common/ui/*.inc`; `tools/shared_ui.py` | Actual selected UI consumers | Record the functions, options and expanded modules selected; DDT uses events/input/wordstar, not every UI include. |
| `src/codec/*`, `src/archive/*`, codec/file adapters | Consuming compression/archive commands | Shared libraries get no independent counter; selected codecs/file adapters affect each consuming executable. NOAH remains deferred. |
| `third_party/dri-ddt/DDT0MOV.ASM`, `DDT1ASM.ASM`, `DDT2MON.ASM`; `tools/ddt_source.py` | DDT adaptation | Include original assembly and translation/preparation; preserve historical reproduction and reference binary separately. Existing DDT source hash report is not a complete dependency closure. |
| `src/bdos/versions.inc`, utility manager version includes | Actual emitted consumers | Generate selected identity fields from registry. Present resident descriptor contains several subsystem versions, creating genuine cross-component byte dependencies. |
| `metadata/utility-versions.tsv`, `metadata/subsystem-versions.tsv` | Selected rows/fields and generated descriptor consumers | Hash canonical projections rather than entire metadata files. RCP transients currently emit several utility banners, so selecting only their own row would be incorrect until generation is narrowed. |
| `src/system/layout.inc`, `tools/system_layout.py`, `tools/build_profiles.py`, selected hardware/BIOS includes | Layout/profile consumers | Canonical selected configuration and toolchain identity go into fingerprints and build records. |
| `tools/checked_build_contract.py`, `checked_carriers.py`, checked pack builders | Checked carriers and embedded stamp consumers | Current stamp covers src/tools/metadata/third_party broadly; even test-only changes can propagate into bytes. Narrow its semantic closure before promising independent tracking in checked profiles; preserve runtime compatibility validation. |
| `metadata/DISK.FDF`, disk catalogs, distribution README/startup scripts | Disk/build inventory | Exact checksums, no executable revision unless the input is compiled into executable bytes. |
| Native prepared sources and generated linkage includes | Producing/consuming components | Capture upstream source hashes and generated content; derived addresses from listings must resolve back to producer inputs. Do not blindly exclude every build/ path. |
| SYSTEM.SYS / RESIDENT.BIN / ROM or disk assemblies | Aggregate products | Reference constituent identities/checksums. No new independent helper counters. Preserve artifact-specific provenance on reuse. |

## Conflicts and required migration actions

1. **RCP:** registry 1.0 (015) conflicts with `version=(0, 2)` in `tools/build_rcp_cpx.py` (and native carrier generation must agree). This is module implementation version, not BCPX format or ABI. Proposed canonical implementation is existing central 1.0; update carrier fields in the same executable revision change set. Do not rewrite old carriers or receipts.
2. **MOVE:** currently deliberately uses RCP identity. It is independently invoked, so the eventual registry needs its own row; select its initial implementation version explicitly rather than copying a fabricated prior counter. Keep current fallback status visible.
3. **WARM:** no central identity. Establish initial implementation version and revision 001 when migrated; first add consistent query handling if required by the utility contract.
4. **BYE:** earlier inventory is obsolete: current main already has 1.0 (001) in the utility table. Preserve that baseline; its custom `version_text()` path needs the common formatter.
5. **Modules:** preserve existing implementation versions listed above; centralize hard-coded builder values and initialize tracking at adoption. Module callable-service ABI versions and carrier schemas remain separate. Do not alter carrier layout merely to store a revision; first determine a compatible embedding or manifest representation.
6. **Subsystems:** central metadata lacks revision fields. Current BDOS is 1.10, not 1.9; other assignments remain BIOS 1.14, CCP/CPX/RSX 2.0. Current generated core descriptor still reports the old milestone. Implement accepted development wording without changing frozen core 1.0.
7. **Formatting:** unify `tools/utility_versions.py`, `codec_version.py`, `build_ddt.py`, and `build_z80pack_bye.py`. Checked output currently replaces independent counters with compatibility stamps; it must preserve component identification while keeping runtime binding separate.
8. **Native preparation:** DDT already shares preparation functions; other native paths and standalone carrier construction require explicit parity checks. Prepared source media must carry identities and input records without requiring Git.

## Selected-input and development fingerprint design for implementation

Use a component/target/profile record with sorted repository-relative paths and SHA-256 values, selected registry fields, effective build options, tool identities and imported generated-link inputs. Canonical JSON serialization supplies a full fingerprint. Keep the assigned revision record outside its own hashed inputs; exclude its recorded fingerprint, output hashes, timestamps, current HEAD and final manifests from that fingerprint. Resolve producer-generated linkage through an acyclic build graph. Detect cycles and unknown inputs rather than silently ignoring them.
Compare relevant input records with the assigned baseline even in a clean working tree: committed-but-unassigned work remains -dev. Missing native provenance is unknown/development, never silently clean. Unrelated working-tree changes do not affect a selected component. Record repository commit and dirty input hashes in build records, outside the executable identity. Preserve previous per-variant baselines and cached artifact provenance when another variant advances the shared sequence.
For executable comparison, prepare both candidates with the same assigned identity and the same development-display treatment so the -dev label cannot itself prove a substantive executable change. If selected source changed but bytes are equal, accept a new equivalence/input record at the existing revision. The current revision number then produces final bytes once, with no recursive bump. Baseline acceptance must be explicit publication work, never an ordinary compile side effect.

## Coverage limits and implementation gates

This completes the inventory and migration review increment, not the executable dependency implementation. The JSON enumerates file-level candidates, including shared inputs, but mixed resident sections, function-selected expansions and checked-contract closure still need refinement during implementation. Test fixtures/prototypes/experimental RSXs are outside the selected release set; their hashes stay with their test/build records. If promoted for distribution, register them before publication. Source/build tools themselves remain provenance inputs rather than receiving new guest utility counters.

Before executable migration, review the RCP canonical value, MOVE/WARM initial versions, mixed resident attribution and narrowing of checked dependencies. Then implement registry-only import with preserved counters; selected-input capture and development records; shared formatting and native preparation; and artifact-driven disk manifests. Each executable migration change set advances only outputs demonstrated to change.

Validation for this increment: all 51 records have existing source roots and builder paths; all 36 central utility rows are represented exactly once; module/subsystem values are checked against current builders/metadata; the JSON parses; no source, counter, generated version include, binary or frozen qualification record was edited. Static graph candidates are explicitly not qualified dependency baselines.
