# Engineering Specification 91: BIOSTEST Returning Baseline

## Decision

BetterCP/M now treats BIOSTEST's returning, automatable BIOS requirements as a
closed physical baseline on the TRS-80 Model 4. The remaining catalog entries
are procedures requiring operator intervention, external device providers,
retained boot evidence, an optional declared profile, or private implementation
knowledge; they are not unimplemented core BIOS entry points.

## Corrected trace oracle

The guarded disk trace originally reported failures in items 0449, 0456, and
0458 even though direct filesystem and allocation tests passed. Instrumented
runs established that BetterCP/M retained valid resident DPH/DPB objects, found
the correct deleted directory slot, and completed the same lifecycle when the
trace shim returned transparently.

The fault was in BIOSTEST's oracle. Its READ and WRITE wrappers shared a single
`WRSTATUS` byte while tracing disk operations that could cross both wrappers.
The second wrapper could replace the first wrapper's saved return value before
it reached BDOS. Compatibility-suite commit `32a7071` preserves each return
status on the Z80 stack while updating its counter and removes the shared byte.
This changes no BetterCP/M code and weakens no assertion.

## Physical result

The corrected suite was rebuilt natively with ZSM4, installed on the generated
conformance disk, and exercised under `trs80gp` with a generated blank 790K B:
fixture. Focused guarded results are:

- 0449 passes: persistent track, sector, DMA, and write context was traced;
- 0456 passes: both application and directory DMA addresses were observed;
- 0458 passes: BIOS WRITE types 0, 1, and 2 were observed.

Together with the earlier safe and controlled allocation/DPB passes and the
completed boot procedures, BIOSTEST's 46-entry catalog is now accounted for as:

- 29 physical required passes;
- 11 non-guaranteed observations;
- 6 provider-dependent, optional-profile, or out-of-scope procedures;
- zero remaining failures in the returning baseline.

On 2026-09-02 item 0457 was completed manually with the blank B: fixture. The
ordinary 128-byte transfer passed, the operator made B: write-protected, the
protected physical write returned nonzero, and a final write succeeded after
B: was made writable again. BIOSTEST reported:

> `0457  P  R  128-byte transfer passed; physical fault returned nonzero`

On 2026-09-02 the retained-evidence boot sequence also completed physically:

- 0464: cold BOOT resumed the CCP with reconstructed public state;
- 0465: WBOOT resumed the CCP on the requested drive;
- 0466: WBOOT reconstructed both deliberately damaged gateway opcodes.

`BTBOOT.DAT` retained the evidence across the nonreturning transitions. It is
deleted only after the final aggregate report.

## Controlled console result

The Model 4 virtual keyboard supplied one uppercase `K` to BIOSTEST's guarded
console sequence. Seven further public-interface requirements passed:

- 0439: BDOS Function 4 delivered graphic and control bytes to PUNCH;
- 0445: Functions 3, 4, and 5 retained their fixed logical dispatch across
  multiple IOBYTE values;
- 0448: character operations preserved the DMA selection and sentinels;
- 0468: CONST reported empty, ready twice without consuming the key, then
  empty after input;
- 0469: CONIN returned the controlled zero-parity `K` byte;
- 0470: CONOUT, LIST, and PUNCH accepted both graphic and control-C bytes;
- 0473: a direct BIOS TAB remained raw while BDOS formatted its TAB output.

These checks patch and restore the public BIOS vectors around the operation;
they therefore verify observable layering rather than private implementation.

## Remaining procedures

The six unrun catalog entries are now sharply bounded:

- 0471 is a required two-stage READER/provider procedure;
- 0435 and 0472 are optional profiles not currently claimed by BetterCP/M;
- 0423, 0459, and 0467 are explicitly out of scope.

## Fixture rule

Controlled blank-disk checks must use
`build/trs80/BetterCPM-BIOSTEST-Blank-790K.dmk`, not a bootable or populated
image. BIOSTEST correctly reports allocation checks 0425 and 0426 as failures
when a populated fixture is presented as blank. In the rejected run, its
reported `DPB AL0/AL1=C000; ALV[0/1]=E000` precisely identified the block-2
`HELLO.COM` allocation. That distinction is evidence that the tests observe
real allocation state.
