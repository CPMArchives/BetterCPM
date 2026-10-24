# Checked cpmsim prototype: completion and acceptance record

Date: 23 October 2026. Status: implementation and bounded qualification complete;
approved by the maintainer on 23 October 2026. This is the separately authorized follow-up to
approved [Part 13](Part13-Final-Assessment-and-Roadmap.md), not another assessment
part. The first engineering assessment remains closed.

The approval accepts implementation snapshot
`8e0fcc48b57665ae9355ea643b930daf15407f6b` and the completion record at
`9703b84aef351412f34a0cf0835cd3d89d5b966a`, including the measured stack margins
and documented scope. The qualified products and their private IDs are unchanged.
Normal-build integration and other-target adoption remain separate work.

## Result

The checked full-RAM cpmsim prototype is complete within its agreed scope. It
retains **56 KiB of unloaded application TPA**, or **53 KiB with ANSISCRN + ADM3A**:
the full 3 KiB gain over the equivalent legacy layout. The remaining stack and
failure-path work found and repaired a real cpmsim screen-output stack overflow.
The repair consumes no additional resident memory or RSX allocation.

The frozen implementation and qualification tools are commit
`8e0fcc48b57665ae9355ea643b930daf15407f6b` on `prototype/cpmsim-completion`.
This branch has not been merged into main. The accepted core 1.0 remains
`3b2d2d7f4fe0472438465165f11fb550d79c8662`; this work does not change that baseline
or declare the full 1.0 distribution finished.

Main was observed at `c18ff9c2f79f432ae1f3c6b4dfcb5f2ead7a5233` when completing
this record, including the separate compression-qualification merge. Those
main-only changes have not been integrated into or qualified by this snapshot.

| Qualified layout | Private compatibility ID | Unloaded COM capacity | With ANSISCRN + ADM3A |
| --- | --- | ---: | ---: |
| cpmsim-fullram | `25532937c320b7975df520ec184031cb` | 57,344 bytes / 56 KiB | 54,272 bytes / 53 KiB |
| cpmsim-legacy-checked | `f5851ceca322f726611592c1cafd3d74` | 54,272 bytes / 53 KiB | 51,200 bytes / 50 KiB |

Capacities are above 0100h and rounded to whole 128-byte records. Clean startup
loads neither screen module; the pair is loaded explicitly in qualification.
The four-provider capacity is unchanged. Streaming still saves 7,168 bytes of
temporary RCP-reconstruction workspace against Part 9; that is not another TPA
gain.

## The defect and repair

The initial broader campaign reached 38 of the BDOS stack's 40 bytes. Inspection
of that call chain identified additional legal renderer states worth exercising.
A program positioned the ADM3A cursor on row 21, enabled reverse video, and
then encountered a final BIOS read failure during disk login. Emitting the
ordinary `Bad Sector` message overflowed the private BDOS stack.

The host observer stopped at the first overflowing PUSH: 42 bytes used, SP
F010h below the full-RAM stack's F012h lower boundary. The saved instruction
history shows the write into the adjacent console-input state. For this specific
call chain, the following raw-output CALL would have taken usage to 44 bytes.
The observer's deliberate-overflow self-test is separate from this real OS
failure. The affected ANSISCRN source was identical in the accepted core 1.0
and the pre-repair prototype, so the defect was not introduced by raising the
cpmsim memory ceiling.

The cause was unnecessary nesting in the cpmsim-specific renderer. Its private
`B_EMIT` helper saved BC, DE and HL and called the generic MONRAW path for every
ANSI output byte. The common output case now writes directly to cpmsim console
port 1 and returns as a leaf. The special 1Ch basic-console clear operation
retains the original fallback. Public basic operations still use MONRAW; the
portable terminal personalities and the Model 4 backend are unchanged.

This removes eight stack bytes from ordinary emitted-byte paths. The reproduced
ADM3A reverse-video failure now uses 36/40 bytes, including bottom-row reverse
scrolling. ANSI reverse-video and scrolling-region error cases reach 38/40.
The ANSISCRN executable grows from 1,357 to 1,365 bytes, within its unchanged
1,536-byte allocation. No stack reservation was shrunk or enlarged.

The assembled new leaf and retained original fallback were compared for every
byte at two relocation bases: **512 comparisons passed**, checking output bytes,
A/Z/C, preserved BC/DE/HL/IX and balanced SP. This includes 1Ch's clear sequence.
Existing screen-backend tests also passed at both relocation bases, covering
cells, reverse attributes, scrolling, line operations and invalid arguments.
The BDOS, gateway, second-stage streaming loader and active resolver binaries
remain byte-identical to Part 12. Binding IDs, dependent checksums and the
ANSISCRN carrier naturally change in the new products.

## Stack ownership and observed use

Qualification adds a host-side instruction observer to a copied cpmsim. It
observes PC/SP before and after each executed instruction without patching guest
code or adding guest frames. Ownership follows actual stack-selection
instructions and saved-stack restoration, rather than classifying arbitrary
addresses as stacks. A lower-bound crossing stops the run and saves the last
64 stack-changing instructions. Independent runs use the ordinary pinned
simulator without the observer.

| Owner / observed region | Bytes in reservation or observation band | Greatest observed use, both layouts |
| --- | ---: | ---: |
| Private BDOS stack | 40 | 38 |
| System reconstruction stack | 32 | 24 |
| Relocated CCP stack | 128 | 24 |
| Stage-one borrowed tail | 64 | 10 |
| Raw bootstrap / reload borrowed page-zero tail | 128 | 10 |
| Streaming command stack workspace | 768 | 26 |
| Early manager unused overlay tail | 283 | 10 |
| Copied reader tail above its live state | 235 | 16 |
| Relocated manager stack | 256 | 24 |
| CONFIG stack band | 512 | 22 |
| SYSGEN observation band | 512 | 18 |

These rows are not additive resident costs. Borrowed tails and observation
bands are identified as such; SYSGEN's band is not a new independent allocation.
The relocated manager measurement includes the six-byte handoff frame.

Source inspection corroborates the observed ownership transitions:

- Ordinary BDOS saves the caller SP, adopts `UB_STKTOP`, and restores the caller
  on ordinary return. Extension dispatch precedes that switch: manager calls
  may invoke ordinary BDOS without recursively adopting the same private stack.
- `EX_RLOAD` moves the saved IX/request/return frame to the early manager tail
  below the fixed BDOS jump. The manager's later handoff relocates that frame to
  its reserved workspace. Early refusal, normal return and rollback paths were
  exercised with an active stateful module.
- Cold/warm reconstruction adopts the system stack. Raw reload explicitly uses
  SP=0100h; stage one and the streaming stage use their own borrowed workspace.
  The stage-one deepest write overlaps bytes of a bootstrap ID that has already
  been validated and is no longer live. Reload reconstructs those bytes before
  their next use. The copied reader's stack stays above its live state.
- CCP derives its stack from the live relocated CCP base. CONFIG and SYSGEN
  select transient-owned stacks after their checked entry gates.
- The demonstrated disk-error path retains its interrupted disk-call frames and
  saved registers while calling the selected monitor. For the ADM3A rendition
  transition, source accounting gives 26 bytes at monitor entry and ten more
  through personality/attribute/string calls to the repaired leaf: 36 bytes,
  matching execution. The former leaf added eight more bytes.

The BDOS margin is still only two bytes in the deepest exercised ANSI cases.
These are measured paths supported by source inspection, not a mathematical
maximum for every possible program or provider. No observed overrun remains
in the final campaigns. Preserve the current allocations and repeat this review
when changing disk/console nesting or admitting additional callback behavior.

The supported monitor contract is single-context and non-reentrant: callbacks
must not invoke BDOS, recursively route console output, mutate the profile or
use console services from an interrupt. Boot disables interrupts; these cpmsim
runs inject no interrupt source. NMI and native interrupt-driven callers are
not qualified by these results.

## Final acceptance evidence

All final campaigns use clean builds from the frozen implementation. Full-RAM
was built twice; all **35 selected repeat artifacts are byte-identical**. The
conservative private input closure contains **1,040 files**, including tools and
tests. A test edit therefore changes the private ID even when resident code is
unchanged. Each System Disk selects 30 files, excluding HELLO.RSX, HELLO.CPX and
STATEFUL.RSX. Test fixtures are installed only in disposable disk copies.

| Campaign | Final result |
| --- | --- |
| Completion paths, instrumented | 77 rows per layout: 75 OS cases plus two deliberate observer self-tests |
| Same completion paths, ordinary simulator | 75 OS cases per layout; all recorded functional outcomes match the instrumented runs |
| Commit observation | 194 completed windows per layout; no disk command observed from commit entry through publication return |
| Utility admission | 57 CONFIG/SYSGEN/STAT gate cases, seven CONFIG preflight cases, three unmigrated-tool refusals and live cross-profile checks per layout |
| Command reconstruction and boundaries | 11 live cases per layout, including exact-capacity COM loading and next-record refusal |
| Checked packages / installation | 22 assembled fixture cases plus 15 full-RAM and 15 legacy live cases |
| Renderer regression | 512 byte/relocation comparisons plus four existing backend runs |

Completion coverage includes 12 disk operations under Ignore and Ctrl-C with
basic output and the ADM3A screen pair; additional lower-row, reverse-video and
scrolling cases with ADM3A, VT52 and ANSI; console editing and printer echo;
stateful load/move/duplicate/unload/refusal; and eight failed preparations with
missing, truncated or corrupt packed overlays followed by successful recovery.
Failed preparations retain the live module's mutated state and TPA. Successful
commits are observed only after preparation; the observer separately proves it
can detect a forbidden disk command.

The disk probe replaces one BIOS transfer vector with a self-restoring error
leaf. It tests BDOS behavior after driver retries have failed, not the controller's
retry implementation. Ignore means continue despite an error; it does not certify
stale data. In the failed-directory-read MAKE case, the subsequent checksum
check correctly takes the independent read-only warm-boot exit instead of
resuming the caller. That outcome is explicitly checked.

The package campaigns repeat exact export, cold boot after installation,
filesystem preservation, and unchanged destinations on the selected rejected
inputs. They do not establish power-failure-atomic installation. Raw sector
copiers can still bypass private bindings. A rejected streamed object can leave
unlinked prospective bytes, which are neither published nor executed.

The accompanying acceptance bundle contains clean images and packages, manifests,
source inputs, tools, listings, transcripts, observer provenance, the pre-repair
overflow witness, final results and SHA-256 hashes. See
[reproduction instructions](CPMSIM-PROTOTYPE-REPRODUCTION.md).

## What remains separate

There is no known blocker to this bounded cpmsim prototype's completion. Normal
build adoption remains a separate decision: reconcile current main and replace
the guarded assessment staging transformations with explicit profile/layout
inputs. Model 4, ROM/XIP, native packaging and physical installation-recovery
qualification remain separate target work. Datestamping, named registers,
provider-capacity expansion and further memory optimization are later work.

This completion record closes the first follow-up priority in Part 13. It does
not start another implementation phase or another numbered assessment part.
