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

Together with the earlier safe and controlled allocation/DPB passes, BIOSTEST's
46-entry catalog is now accounted for as:

- 19 physical required passes;
- 11 non-guaranteed observations;
- 16 manual, provider-dependent, optional-profile, or out-of-scope procedures;
- zero remaining failures in the returning baseline.

On 2026-09-02 item 0457 was completed manually with the blank B: fixture. The
ordinary 128-byte transfer passed, the operator made B: write-protected, the
protected physical write returned nonzero, and a final write succeeded after
B: was made writable again. BIOSTEST reported:

> `0457  P  R  128-byte transfer passed; physical fault returned nonzero`

Boot reconstruction and character-device procedures retain their explicit
setup and evidence requirements.

## Fixture rule

Controlled blank-disk checks must use `build/trs80/blank-790k.dmk`, not the
populated cross-drive conformance image. BIOSTEST correctly reports allocation
checks 0425 and 0426 as failures when a populated fixture is presented as blank.
That distinction is evidence that the tests observe real allocation state.
