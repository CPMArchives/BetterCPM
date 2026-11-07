# TCAP transaction and command-return experiment

Status: isolated feasibility evidence, 7 November 2026. Follows the
[placement experiment](TCAP-Placement-Results.md), after PR #656. The public
TCAP engineering proposal remains a draft. No production source, utility,
distribution image or release assignment changes in this experiment.

## Result and activation boundary

The private coordinator now reaches **actual transaction and command-return
entries**, rather than relying on a fixture wrapper in front of the commit
engine or a replacement warm-entry recovery routine:

- A non-mutating busy query runs inside staged copies of `RF_ENTRY` and
  `RC_ENTRY`. Emphasis, takeover, combined and recovery-required states return
  private status 16 before request/context bookkeeping, scheduling, movement or
  publication. Request pointers survive permitted legacy Monitor register use.
- Recovery runs after CCP stack establishment and before `CPX_INITIALIZE`, before
  the normal CCP prompt on resident-command returns, and after both reloaders
  establish their safe stacks. It repairs rendering, then uses actual cooked
  BDOS CR/LF to synchronize the cooked column before retiring ownership.
- Rendering failure stops in the optional owner's fatal loop before subsequent
  disk activity, diagnostics or prompts. Ownership remains recovery-required.
  This is a fatal disposition, not a successful prompt baseline or live retry.
- Operation 5 retains its existing parser-reset meaning and still executes.
  Private operations 25/26/27 are experimental controls, not public allocations.
  Existing ADM-3A, VT52 and ANSI personalities reject them without output or
  module/backend mutation in the executed probes.

**Production activation remains blocked.** The structurally valid experimental
carrier deliberately declares an **unallocated private MCON 1.3 requirement**,
not compatible MCON 1.2. The shipped metadata validator rejects it without
publishing facts. This is an executed fail-closed gate, not a completed positive
admission protocol. The fixture installs the owner directly only to execute the
matched staged code. No installable carrier is emitted by this campaign.

A future positive gate must establish that the core route guard, manager guard,
command/reloader recovery paths and owner agree on a versioned contract. An
owner service ID, a successful unknown-operation probe, or a BIOS hook alone is
insufficient: an old command carrier could still bypass recovery. A checked build
identity could bind these artifacts, but this campaign neither issues such an
identity nor qualifies a checked profile. Do not weaken the existing minor-version
rejection to activate this owner. The boot-global non-reusing validity allocator
also remains required; fixture validity is not a production replacement.

## Measured placement

| Component | Baseline bytes | Experimental bytes | Budget / consequence |
| --- | ---: | ---: | --- |
| Finalizer | 982 | 991 | 1,012-byte gateway-safe overlay |
| Commit | 1,007 | 1,012 | Exactly fills its overlay |
| CCP | 5,599 | 5,610 | Allocation stays 5,632 bytes; 495/504 relocation words |
| Model 4 reloader | 932 | 932 | Exactly fills existing carrier |
| Maintained stage 2 source | 1,301 | 1,302 | Reference-layout fixture bindings; below 2,024-byte payload budget |
| Optional owner payload | 2,205 in placement experiment | 2,221 | Allocation stays 2,304 bytes; 231/232 relocation words |

The fixed resident core is still the placement experiment's 6,588-byte image,
with its 757-byte BIOS and unchanged boundaries. These figures do not reserve
space for the missing validity allocator or positive admission protocol.

The commit guard initially exceeded its overlay. Two carry-clears before
`ADD HL,DE` are redundant because ADD defines carry; the malformed-input return
uses `OR FFh` to preserve A=FFh/NZ in one fewer byte. Range-checked short branches
supply the remaining savings. Existing full commit/scheduler/mover regression
runs against that experimental engine, including retained movement, prepared
snapshots, failure rejection and generation publication.

The Model 4 reloader initially exceeded its exact carrier. Its five-byte call is
paid for by one range-checked short branch and four single-byte reductions:
A=1/NZ return via XOR/INC; reuse of known zero A in the allocation alignment
check; reuse of BC=0 after completed LDIR to clear `CRLEFT`; and omission of a
carry-clear immediately after an equal subtraction proved carry zero. These are
specialized transformations, not a general optimizer. The full reloader tests
below exercise successful and failed carrier loading beyond the entry hook.

## Executed evidence

Reproduce with [the campaign instructions](../../tools/prototypes/tcap/README.md#transaction-and-command-return-follow-up).
The [recorded report](evidence/tcap-system-paths/report.json) includes cases,
source and assembler hashes, dimensions and explicit limitations. The
[generated staged-source patch](evidence/tcap-system-paths/system-paths.patch)
shows the actual assembly transformations, including expanded private bindings
and range-checked branches; it is a review artifact, not a production patch.

Four runs use Model 4 and ANSI-host backends, each with the owner at 9000h and
A101h. Each repeats the previous 39 owner/recovery checks and executes 64 new
named checks. The latter cover all current non-idle transaction states, legacy
scratch registers, real empty-profile publication/unbinding, all five states at
four command-return boundaries, rendering failure, and cooked Control-C through
BIOS WBOOT into each real reloader entry. Independent pyte rendering and Model 4
video-memory checks remain in the previous behavioral checks.

The same run also executes:

- The existing full commit/scheduler/mover regression, with the basic Monitor
  binding initialized as boot would initialize it.
- Ten full Model 4 reloader cases using the experimental CCP carrier: two bare
  placements, one/two synthetic CPXs, malformed optional carrier, required-CCP
  failure, three optional read failures and an optional reset failure. Existing
  reloader assertions check relocation, chain contents and optional/fatal behavior.
- 108 legacy control probes: three real personalities, two actual backends, six
  pending-parser values and three private operations.
- Actual carrier normalization followed by metadata rejection of the unsupported
  experimental MCON requirement, preserving the facts record.

| Observed stack depth | Model 4 path | ANSI-host path |
| --- | ---: | ---: |
| Client | 18 | 28 |
| Earlier injected warm fixture | 12 | 20 |
| CCP stack | 16/128 | 24/128 |
| Model 4 reloader stack | 14/64 | 22/64 |
| Stage 2 stack | 14/768 | 22/768 |
| BDOS private stack | 26/40 | 34/40 |

Every observed SP assignment stays inside its configured region. These are
observed depths, not whole-system maxima. Disk/file-service doubles in the full
reloader regression do not qualify filesystem stack depths.

## Limits and next gate

Entry-path tests replace the *following* initialization, prompt or first disk
operation with an explicit stop; recovery itself and the paths into it execute.
The ten full reloader cases continue through controlled read/file/reset services,
with synthetic CPXs. They are not live disk or native-machine evidence.

Stage 2 is assembled with fixture-only checked-helper addresses in the reference
Model 4 layout; its CRC/identity helpers are not executed here. There is no claim
of a complete checked cpmsim system. The host fixture still substitutes the
hardware output leaf in the shared reference BIOS. Native assembly parity,
protected ROM, maintained Model II and hardware timing remain unqualified.

The next activation gate is a versioned, matching system/owner/command-carrier
contract plus the global validity allocator, followed by full candidate request
validation and whole-system recovery/failure qualification. TYPE/TED/HELP
migrations, HELP delivery and release assignment remain deferred. The terminal
personality/backend separation and ordinary CP/M byte path remain unchanged.
