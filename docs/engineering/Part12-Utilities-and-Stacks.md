# Engineering assessment Part 12: utility dependencies and stack ownership

Date: 23 October 2026. Status: approved by the maintainer on 23 October 2026.
The maintainer approved Part 11 and authorized this part. Accepted core 1.0
remains `3b2d2d7f4fe0472438465165f11fb550d79c8662`.

## 1. Decision

**Close the identified cpmsim utility compatibility gaps, retain the existing
stack reservations, and investigate the small resident stacks before native
or ROM adoption.** The checked full-RAM profile still provides **56 KiB unloaded
and 53 KiB with ANSISCRN + ADM3A**. The checked legacy control remains **53 KiB
and 50 KiB**, respectively. This part adds no resident allocation and claims no
additional application TPA.

The most consequential new measurement is **34 bytes used out of the BDOS
stack's 40-byte reservation** during live SYSGEN export. Six bytes remained
untouched in that workload. This is not evidence of an overflow, but it is too
little evidence to justify shrinking that stack. Assembled utility entry tests
also reach **24 of the 32 system-stack bytes** before a private stack is adopted.
The larger transient stacks show much more spare space in the tested paths;
reducing them would principally affect temporary loading headroom, not the
unloaded application's TPA.

This is a bounded qualification result, not a declaration that every utility,
stack path, interrupt combination or target is qualified. No Astra-specific
architectural review was needed to establish these findings.

## 2. Utility dependency inventory and changes

| Utility or path | Dependency and disposition |
| --- | --- |
| CONFIG | Compiled system base, generated resident-validation and cold-IOBYTE records. New exact-build gate runs after its private stack is established, before INIT or private access. |
| SYSGEN | Compiled system base and checked package contract. New entry gate precedes INIT; Part 11 package/destination checks remain. |
| STAT MEM | Compiled ECB and memory-region addresses. New gate protects MEM only; ordinary CP/M reports remain usable across profiles. |
| Standalone CLS | Inherited RCP's absolute BIOS+66 call. Checked transient builder now obtains MONCALL from the live page-zero BIOS vector, matching the existing monitor-console helper. |
| RCP.CPX | Retains fixed private references and its existing carrier binding. Its executable body and allocation are unchanged by this utility repair. |
| RSX / CPX management | Functions 177/176, public request structures and checked loader admission. No new per-build utility lock. Cross-profile enumeration and module operations pass. |
| TIME and monitor test utilities | Service discovery/calls, not compiled resident layout. Remain dependent on their advertised BetterCP/M service contracts. |
| DUP, TYPE and screen helpers | Disk-service or live BIOS-vector interfaces, including BetterCP/M MONCALL where used. Address-independent between these profiles does not make these paths generic DRI CP/M features. |
| DIR, COPY, ERA, REN, PIP, ED, SUBMIT and ordinary STAT operations | Public CP/M calls, plus the documented BetterCP/M service/BIOS dependencies of individual features. No new exact-build guard on ordinary operations. This part does not requalify their complete application behavior. |
| SYSBUILD, RESPACK, RLMBUILD | Development packaging tools emitted by the common builder, outside the System Disk manifest. Their old native output formats have not been migrated. In checked cpmsim builds they now refuse operation before file access; /VER remains available. |

The dependency review includes shared includes and generated RCP transient
bodies, not just utility filenames. CLS was the additional fixed-address case
found that way. The replacement is limited to transient generation; resident
RCP source and the release builders remain unchanged.

MONCALL remains a **private BIOS 1.7 interface**. Resolving it through WBOOT
removes CLS's fixed-address dependency; it does not create a portable CP/M
screen API or qualify incompatible future BIOS versions. The same ABI
dependency already exists in the shared screen helpers. These tests establish
interoperation between the two checked layouts with that interface intact.

The new private gate first checks the page-zero WBOOT opcode and expected BIOS
address. Only then does it read the resident's 16-byte private ID and compare
it with the utility's embedded ID. A foreign layout or ID produces a diagnostic
and warm boot without entering the private operation. This is conservative:
an intercepted WBOOT vector can cause a refusal even if the underlying core
matches. It is accidental-mismatch protection, not authentication.

CONFIG was already close to its code limit. Its final cpmsim build now carries
only the cpmsim resident/IOBYTE validation records, reuses its compatibility
diagnostic, and keeps the full **3E00h–3FFFh, 512-byte stack reservation**.
CONFIG grows from 15,564 to **15,596 bytes** and ends at **3DECh**, leaving
20 bytes before that reservation. SYSGEN grows from 6,638 to **6,726 bytes**.
Changed transient versions identify themselves with a private P12 build ID;
released utility build numbers are not advanced for this experiment.

Old or renamed utilities do not acquire these gates retroactively. In
particular, the OS still cannot stop an arbitrary old raw disk copier. Do not
interpret the new utilities' rejection behavior as universal OS-level policing.

## 3. Stack ownership and observed use

The ordinary BDOS dispatcher saves the caller SP and switches to its own
40-byte stack. Extended services take a separate path so an RSX transaction can
invoke ordinary BDOS without borrowing that same stack recursively. Warm boot
establishes the system stack before reconstruction. The CCP owns a separate
128-byte stack inside its reconstructible allocation.

RSX management has two further transitions: the early extension handoff uses
the manager-tail stack, then relocates its three-word frame into the transaction
workspace. The copied overlay reader saves that SP and uses its own stack next
to its private state. The transaction's effective high address is capped at
7000h, so the measured fixture uses 6000h–6FFFh workspace, reader state at
6600h–6614h and manager frame/stack at 6F00h–6FFFh.

| Owner / tested operation | Reservation or probe band | Highest observed usage |
| --- | --- | ---: |
| System gateway, warm boot then command reload | 32 bytes; E218h–E237h full RAM, D618h–D637h legacy | 12 bytes live |
| Utility entry before private stack | Same 32-byte system stack | 24 bytes in assembled entry fixtures |
| Unified BDOS, SYSGEN export workflow | 40 bytes; F012h–F039h full RAM, E412h–E439h legacy | 34 bytes live |
| Streaming reconstruction | 0D00h–0FFFh, 768 bytes | 26 bytes live |
| RSX copied reader | 6615h–66FFh, 235 bytes available after state | 16 bytes live |
| RSX manager, STATEFUL load / unload | 6F00h–6FFFh, 256 bytes including relocated frame | 24 / 20 bytes live |
| CONFIG /SHOW | 3E00h–3FFFh, 512 reserved bytes | 22 bytes live |
| SYSGEN export | 3E00h–3EFFh, a 256-byte measurement band below SP=3F00h | 18 bytes live |

SYSGEN's row describes the marked measurement band, not a newly declared
256-byte allocation. Its image and package scratch lie below that band; its
main input buffer begins at 4000h. No stack reservation was changed.

The monitor contract expressly forbids callbacks from recursively invoking
routed console operations or BDOS, and does not support console use from
interrupt handlers. Future stress tests must distinguish legal internal call
nesting from violations of that existing contract.

The live measurements run on the unmodified qualified cpmsim system tracks.
Small disposable COM probes adopt their own stack, fill the selected unused
bands with A5h or 5Ah, execute the workload and inspect changed bytes. They
print directly through the host console port to avoid deepening the measured
BDOS stack. Both fill patterns and both layouts produce the same results.
CONFIG and SYSGEN measurements include the subsequent warm-boot/command-load
workflow, so the BDOS value is the maximum observed over that sequence.

These are changed-byte watermarks: they establish observed use, not an
exhaustive maximum or a proof against every overwrite. The entry fixtures
separately track actual PUSH/CALL depth, including the transient return word;
their public BDOS endpoint is controlled. Neither method delivers interrupts.
The CCP stack, stage-1 bootstrap stack, early RSX handoff and every disk-error
exit do not receive independent high-water qualification here. Stage 1 uses
SP=0500h in an already validated bootstrap carrier tail; later stage-2 code,
stack, header cache and record buffer have distinct ownership.

## 4. Qualification evidence

The final source closure contains **1,036 files**. Qualified profiles are:

| Profile | Private compatibility ID | Unloaded maximum COM |
| --- | --- | ---: |
| cpmsim-fullram | `0ed03e03f6e45d339f7d8dc993287c5c` | 57,344 bytes |
| cpmsim-legacy-checked | `adc1047d9666a1cb78b592368c3a6d82` | 54,272 bytes |

- Per profile: 57 assembled gate cases cover matching builds, wrong BIOS/opcode and corruption of each of the 16 ID bytes; seven CONFIG preflight cases cover quoted /VER, long input and malformed requests; three native packaging tools refuse before file operations.
- Cross-profile live checks reject foreign CONFIG, SYSGEN and STAT MEM. Ordinary foreign STAT reporting, RSX management, CPX load/execute/unload and CLS continue successfully. The HELLO.CPX used here is a test fixture only.
- Ten live stack workflows per profile cover two marker patterns across warm boot, STATEFUL load/unload, CONFIG inspection and SYSGEN export.
- The Part 11 eleven-entry loader/application campaign passes on both fresh profiles, including maximum-COM boundaries, module-state preservation, screen pair and damaged-loader refusal.
- The Part 11 package fixtures and both live installation/export/refusal campaigns pass with the new utilities. Successful installs preserve filesystem bytes and cold-boot; tested rejected inputs leave the destination unchanged.
- Thirty-five repeat-build artifacts match byte for byte. Clean System Disks contain 30 manifest-selected files and exclude HELLO.RSX, HELLO.CPX and STATEFUL.RSX.

The BDOS binary, system gateway binary and 1,301-byte streaming executable are
byte-identical to Part 11. The resident carrier remains 6,588 bytes; private
IDs and dependent checksums change. RCP.CPX remains 8,756 bytes. Earlier loader
instruction fixtures remain applicable to the identical executable; this part
reruns the live loader/application campaign on the fresh complete products.

The branch is `assessment/part12-utilities-stacks`, based on approved Part 11
commit `6e512fa5b9747f84fd653083f0c1a4d9c94613ec`. Main was observed at
`9023313b1dc9610e3532a29bcc5747b40753a25f`, containing separate codec work.
That main-only work is not overwritten or folded into this qualification.
Reproduction commands and interpretation limits are in
[Part12-Reproduction.md](Part12-Reproduction.md).

## 5. Remaining gates and next bounded part

The identified private-utility entry and obsolete-packaging hazards are closed
in this selected build path. The stack inventory is now concrete, with a
specific small-margin target; it is not a completed whole-system stack proof.

**Proposed Part 13:** stress and trace the small resident system/BDOS stacks,
including monitor-service nesting and disk-error exits. Establish whether the
six-byte observed BDOS margin is sufficient; repair any demonstrated defect
without reducing application TPA where feasible. Pause after that bounded
assessment. If a repair requires an architectural change, seek a separate
architectural critique rather than inferring safety from a successful smoke
run.

Keep native/ROM adoption, native packaging migration, physical installation
interruption/recovery, and the separate Model 4 F400h–FFFFh hardware-window
banking investigation explicitly pending. The long-term goal remains larger
applications and more simultaneous RSX features, including future datestamping
and named registers. Approval of this part does not approve a final release.
