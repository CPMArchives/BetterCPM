# Engineering assessment Part 13: final synthesis and roadmap

Date: 23 October 2026. Status: approved by the maintainer on 23 October 2026;
the first engineering assessment is closed. Parts 1–12 were approved.
This part changed documentation only. The maintainer subsequently authorized
the separately scoped cpmsim prototype-completion work defined below.

Subsequent completion record: [checked cpmsim prototype](CPMSIM-PROTOTYPE-COMPLETION.md).
That separately authorized work closes roadmap priority 1, including a repaired
cpmsim renderer stack overflow and a frozen acceptance build. The assessment
findings and remaining adoption priorities below retain their original scope.

## 1. Conclusion

**Keep the target-specific build approach. The checked cpmsim prototype
recovers 3,072 bytes of application TPA while retaining the tested features,
capacities and compatibility checks.** Its maximum record-aligned COM is
57,344 bytes (56 KiB) unloaded and 54,272 bytes (53 KiB) with ANSISCRN + ADM3A.
The accepted core provides 53 and 50 KiB in those same cpmsim configurations.

The comparative work helped identify an unnecessary common memory ceiling,
the value of explicit capacities, and the need to distinguish resident memory
from reconstructible commands and temporary workspace. BetterCP/M also has
strengths worth preserving: its protected COM reader can load through the
reclaimable command environment, and its RSX machinery supports live state
and failure recovery. The evidence supports improving these mechanisms rather
than reproducing NZ-COM's architecture wholesale.

The assessment also found concrete design weaknesses: insufficient private
artifact binding for multiple layouts, an unenforced CPX payload checksum,
fixed-address utility dependencies, limited provider capacity, and small
resident stack margins. The selected cpmsim prototype addresses the first
three. Provider capacity and complete stack qualification remain open.

**We are close to completing the bounded cpmsim prototype.** The integrated
implementation exists and the reported functional campaigns pass. Remaining
work is targeted stack/failure-path qualification, any necessary repairs,
and a final reproducible acceptance snapshot. That is separate from adopting
the design in normal release builds or implementing it on Model 4 and ROM
targets. No completion percentage or fixed number of work sessions is justified.

## 2. Baselines and scope closure

The accepted core 1.0 remains
`3b2d2d7f4fe0472438465165f11fb550d79c8662`, as recorded in
[CORE-1.0-BASELINE.md](../releases/CORE-1.0-BASELINE.md). Completion of this
assessment does not retag that core, change the displayed distribution
version, or complete the outstanding 1.0 documentation and utilities disk.

The final assessed prototype is the approved Part 12 branch at
`cb5ac7d1d3211b78096d27c563e602af35dc90c8`. Its implementation commit is
`9c07c3a780cb7852a27dc51092dbd08a7288f975`; subsequent commits clarify the
report and record approval. Part 12 identifies the actual tested products and
their private compatibility IDs. Documentation commits do not change those
IDs. This synthesis is based on that snapshot, not a newly rebuilt main.

Main was observed at `569825d63f0f8d59db61ba86c41bb69434e49291`, the codec-help
merge. This documentation branch neither integrates nor qualifies main-only
changes. Reconciliation belongs to adoption work.

The work expanded from comparison into implementation and qualification.
That expansion produced useful evidence, but it should have been identified
as a separate workstream earlier. The maintainer has now directed closure
with this synthesis. The former proposal to make stack stress “Part 13” is
superseded; there is no further numbered assessment part scheduled.

Closure means the findings, limits and follow-up decisions are recorded. It
does not turn incomplete investigations into completed proofs:

| Assessment area | Established result | Coverage limit / disposition |
| --- | --- | --- |
| Usable memory | Explicit accounting; live NZ-COM reconfiguration; a measured 3 KiB cpmsim TPA gain retained through Part 12 | No new Model 4 or ROM full-RAM qualification; future-default costs unknown |
| Code and execution efficiency | Resolver/helper lifetimes traced; compact checksum repair and streaming alternatives compared; temporary-memory costs measured | No comprehensive BDOS/BIOS instruction or redundancy audit, matched disk-latency benchmark, or general speed ranking |
| Placement, modularity and capacities | Reclaimable versus protected responsibilities identified; profile design demonstrated; four-provider constraint exposed | Smaller active resolver, expanded capacities and default feature packaging deferred |
| Engineering weaknesses and recovery | Private binding, carrier integrity and utility hazards corrected in the selected path; mixed-product and failure campaigns recorded | Whole-system stack bounds, all transaction peaks and interrupted physical installation remain unproved |
| Comparative interpretation | Identified NZ-COM binaries, live controls, executed loader analysis and MM mapping evidence inform specific choices | Exact matching NZCPR source and complete capability parity remain unavailable; no overall “best engineered OS” verdict |

## 3. What the memory comparison actually says

All quantities below are bytes available above 0100h, rounded to whole
128-byte records. A runtime address boundary and the largest ordinary COM
accepted by a loader are distinct measurements. “Unloaded” means no optional
RSXs; it does not mean the OS has no command environment.

| Configuration | Record-aligned runtime boundary | Ordinary COM evidence / qualification |
| --- | ---: | --- |
| DRI CP/M 2.2, classic cpmsim host | 60,160 bytes / 58.75 KiB | Reference boundary carried forward in Part 4; no new measurement in this synthesis |
| NZ-COM MATCH on that classic host | 54,272 bytes / 53 KiB | Largest successful ordinary COM 51,840 bytes; next record rejected |
| NZ-COM NOIOP on that classic host | 55,808 bytes / 54.5 KiB | Largest successful ordinary COM 53,376 bytes; next record rejected |
| BetterCP/M core 1.0, cpmsim unloaded | 54,272 bytes / 53 KiB | Full-boundary COM loading established by the accepted baseline |
| BetterCP/M checked full-RAM cpmsim, unloaded | 57,344 bytes / 56 KiB | Exact maximum COM and next-record rejection exercised in the prototype campaigns |
| Same full-RAM prototype, ANSISCRN + ADM3A | 54,272 bytes / 53 KiB | Loaded profile and application-boundary campaign recorded in Parts 11–12 |
| MM CP/M 2.2 / BIOS 2.32, retained Model 4 distribution | 56,064 bytes / 54.75 KiB | Distribution layout plus retained prior RAM capture; attempted fresh launch failed |
| BetterCP/M core 1.0, Model 4 shipped screen pair | 51,456 bytes / 50.25 KiB | Allocation-derived startup result, not a new live Model 4 measurement |
| RomWBW supplied NZ-COM descriptor | 49,152 bytes / 48 KiB | Static descriptor if active; no RomWBW hardware boot measured |

The comparator is NZ-COM loader 1.2 with the NZCPR/NZDOS modules from RomWBW
v3.6.0 commit `f53d5e339e3d9d6928d00e2a1997a8a2a51563ab`. NZDOS matches the
standalone ZSDOS module byte for byte. MATCH relocates the supplied layout
for the classic cpmsim host; it does not mean feature matched. The same CPU
emulator controls one variable, while BIOS, disk geometry, startup services
and functionality differ. ZDDOS was not separately benchmarked.

Parts 2–3 demonstrate that NZ-COM can recover 1,536 bytes by removing its IOP
reservation and restore the larger configuration dynamically. They also
explain the ordinary COM limit using the executed NZCPR binary: its retained
CCP, guard page and EOF read account for a 2,432-byte gap below the runtime
boundary. A separate test overwrites the CCP during execution and returns
successfully. Neither result is a universal application-compatibility ranking.

The full-RAM BetterCP/M prototype remains 2,816 bytes (2.75 KiB) below the
DRI reference. Core 1.0 on Model 4 is 1.75 KiB below MM when unloaded, or
4.5 KiB below it with the shipped screen pair. These gaps compare different
feature sets. The 48–58.75 KiB range provides deployment context; it is not
an efficiency target or a reason to stop recovering memory.

MM also corrects an important earlier premise: F400h–FFFFh contains usable
RAM hidden by the hardware-access mapping. Brief keyboard/video mapping is
a credible Model 4 direction. BetterCP/M's net recovery there is still
unmeasured; the cpmsim result does not establish it.

## 4. Keep the memory benefits separate

| Item | Final evidence | What it buys |
| --- | --- | --- |
| Higher cpmsim resident ceiling | +3,072 bytes; 53 to 56 KiB unloaded | More application space or space for loaded services |
| Streaming command reconstruction | 5,504-byte temporary envelope; RCP reload uses 7,168 fewer bytes than Part 9's whole-carrier buffering | More temporary reconstruction headroom; **no additional application TPA** |
| Checked RSX transaction workspace | 4,096-byte upper reservation versus 3,840 before checks; lower preparation/snapshot data additional | Compatibility and recovery machinery; temporary cost, not a 4 KiB idle TPA deduction |
| First active RSX | 1,024-byte shared manager/resolver charge plus module allocation | Application-time discovery and lifecycle support; not wholly disposable overhead |
| CCP + RCP allocations | 12,800 bytes in the accepted baseline, reclaimable | Command-time footprint and reconstruction work; shrinking them alone does not raise protected TPA |
| Previously spare cpmsim BIOS/disk bytes | All 159 consumed by Part 7's checks within existing allocations | Checks without new permanent allocation; these bytes are no longer an available packing gain |

Streaming adds 129 executable bytes over Part 9's second stage, reaching
1,301 bytes, and incurs greater processing overhead in the functional runner.
It is a temporary-memory tradeoff, not a speed improvement. It also uses
896 more temporary bytes for the tiny HELLO.CPX fixture than Part 9.
HELLO.CPX and HELLO.RSX are separate development fixtures, and neither is
distributed. STATEFUL.RSX is also excluded from the clean System Disk.

No resident stack reservation was reduced to obtain these gains. In Part 12,
the BDOS binary, gateway binary and streaming executable remain byte-identical
to Part 11. The unchanged allocation sizes do not imply unlimited growth room:
resident spare space is exhausted, CONFIG ends 20 bytes before its stack,
and several helper slots have little slack.

## 5. What is already working in the prototype

Parts 11–12 integrate fresh full-RAM and legacy checked builds from source,
with matching resident code, command carriers, runtime helpers, utilities and
packages. Thirty-five repeat artifacts match byte for byte. Each clean System
Disk selects 30 distribution files.

The recorded campaigns cover cold boot, command reconstruction, application
boundaries, screen modules, module state preservation, checked package and
disk installation, exact export, and selected damaged/foreign-product
refusals. Successful installations preserve filesystem bytes and cold-boot;
the tested rejected inputs leave the destination unchanged. Public operations
remain usable across the two layouts; private utilities check their binding.
Unmigrated native packaging tools refuse in this selected build path.

These are useful, concrete results. They are not universal protection against
old raw-sector copiers, cryptographic authentication, or atomic upgrades.
SYSGEN requires matching critical destination files; it does not install all
optional files. An interrupted physical write can still leave an unbootable
system. Streaming may leave partial bytes in unlinked prospective memory
after rejection; those bytes are not published or executed. Such limits must
remain in the prototype's documented contract.

## 6. Prioritized follow-up roadmap

The rows below define separate workstreams. They are recommendations for
subsequent authorization, not additional parts of this assessment.

| Order | Workstream | Completion or decision criterion |
| --- | --- | --- |
| 1 | Finish the bounded checked cpmsim prototype — completed subsequently | [Completion record](CPMSIM-PROTOTYPE-COMPLETION.md): targeted qualification, demonstrated defect repaired, frozen reproducible snapshot ready for maintainer acceptance |
| 2 | Integrate the accepted design into normal build tooling | Reconcile current main; replace assessment-only staging transformations with an explicit profile/layout interface; retain consistent private binding and supported legacy behavior |
| 3 | Qualify adoption by target | Separate Model 4, ROM/XIP and native-build/package work; actual target execution, supported media/configuration coverage and documented installation recovery |
| 4 | Recover Model 4 upper RAM | Prototype mapping-safe code/state/stack placement and coordinated screen access; measure net TPA after all costs; preserve boot, console, disk and recovery behavior |
| 5 | Budget future defaults and extension capacity | Choose the clock/stamping/NDR decomposition; measure complete allocations and core costs; resolve the four-provider limit before promising a default configuration |
| 6 | Pursue smaller focused optimizations and comparisons | Reassess the 768-byte active resolver hypothesis, command/reload costs and resident code sharing against measured net gains and preserved guarantees |

Target adoption is not one all-or-nothing release gate: each supported target
needs its own decision. The Model 4 upper-RAM experiment may proceed alongside
target integration when its prerequisites are ready. Ordinary Model 4 adoption
and recovery of its upper RAM are distinct goals.

### Bounded cpmsim prototype completion

**Remaining technical gate:** establish adequate stack space and correct
ownership on the selected profiles' legal call paths. Part 12 observed 34 of
40 BDOS bytes used during export, and 24 of 32 system-stack bytes in assembled
utility-entry fixtures. These are observations, not proven worst cases and
not evidence of an overflow. Retain the reservations while checking the
small resident stacks, disk-error/recovery exits, early RSX handoff, stage-1
bootstrap and CCP stack paths not independently qualified in Part 12.

Combine source call-depth/ownership analysis with targeted execution and
sentinels. Cover legal monitor/service nesting, and check the relevant
rollback and publication transitions where coverage is incomplete. Do not
require recursive BDOS/routed-console callbacks or interrupt console use
that the existing monitor contract forbids. Record the supported cpmsim
interrupt assumptions rather than importing a native hardware qualification
claim. If a defect requires more memory, report the net effect; preserving
56 KiB is a goal, not a reason to hide a necessary correction.

**Final acceptance gate:** after any repairs, build one frozen source snapshot
twice; reuse the relevant Parts 11–12 campaigns for both checked layouts,
repeat affected boundary/failure checks, confirm distribution exclusions,
and publish its exact products, results, supported scope and remaining limits.
Do not repeatedly broaden testing without a new failure or unresolved concern.

The prototype is complete when these gates have a defensible recorded result
and no known blocker remains within that bounded scope. Native/ROM support,
new features, a smaller manager, whole-core runtime relocation and production
build refactoring are not prerequisites for that declaration. A newly exposed
architectural defect should be reported as a blocker requiring a separate
decision, rather than silently creating more assessment parts.

### Future defaults and further optimization

The objective remains larger applications and more simultaneous RSX services,
including desired datestamping and named registers. Extra TPA alone does not
remove the current four-provider limit. A separately packaged screen backend,
personality, clock, NDR and stamping service would require five slots. That is
a possible packaging choice, not a frozen design. The NDR's 128-byte data map
is not its complete memory cost; clock access is not filesystem timestamping.

Keep three budgets: unloaded TPA, actual shipped-startup TPA, and the measured
prospective-default TPA. For the existing Model 4 screen pair plus a separate
512-byte clock, the earlier conditional budget remains
`50,944 + G - N - S - C` bytes: G is net platform recovery, N and S are complete
rounded NDR and incremental stamping allocations, and C is extra core/registry
cost. None of those future costs is supplied by this assessment. Recalculate
from the actual layout and round to records if allocation granularities change.

The smaller resolver proposal is a **256-byte gross hypothesis**, based on
the baseline 738-byte resolver plus its frame/gateway fitting in 768 bytes.
It has no validated net saving. Transactions still need larger helpers, and
the recovered page may already contain a live provider. Increased provider
capacity could consume the margin. Retain it as a focused follow-up, together
with measured code sharing and command-I/O questions, without treating any
candidate savings as additive promises.

## 7. Evidence index and final boundary

| Parts | Evidence used in this synthesis |
| --- | --- |
| 1 | Baseline reconciliation, core selection, distribution/runtime boundaries |
| 2–3 | Memory maps, optional-service charges, live NZ-COM configuration/COM tests, executed loader diagnosis, MM addendum, resolver/capacity analysis |
| 4 | Common-source target profiles, private dependency inventory, Model 4 mapping design and conditional budgets |
| [5](Part5-Cpmsim-Full-RAM-Prototype.md) | Initial 3 KiB full-RAM prototype and essential layout/runtime checks |
| [6](Part6-Profile-Compatibility-Design.md)–[7](Part7-Checked-Cpmsim-Profiles.md) | Compatibility design, checked helpers, resolver preservation and cost accounting |
| [8](Part8-Carrier-Binding.md)–[9](Part9-Command-Loader.md) | Carrier binding, exposed CPX integrity gap, compact repair and verified second-stage alternative |
| [10](Part10-Streaming-Loader.md) | Streaming memory policy, failure behavior and measured tradeoffs |
| [11](Part11-Checked-Packages.md) | Fresh integrated products, package/install/export checks and reproducibility |
| [12](Part12-Utilities-and-Stacks.md) | Utility gates, cross-profile behavior, distribution exclusions and bounded stack observations |

Parts 1–4 are the previously delivered reports; the standalone Part 13 report
includes their narrative reference extracts and source hashes with this
synthesis. Later repository reports link their reproduction instructions.
This part performs documentation, arithmetic and reference consistency checks
only. It runs no new emulator campaign and makes no fresh performance claim.

**The first engineering assessment ends here.** The next optional task is
bounded cpmsim prototype completion under the criteria above, with a review
pause after each authorized increment. No further implementation is started
by this closure.
