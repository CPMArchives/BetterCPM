# Resident feature guidance — 1.0

Maintainer decision, 2026-10-13: automatic resident-to-transient handoff is
post-1.0. Its suppression state and controls are also deferred. Explicit
colon/period invocation remains the 1.0 route to transient utilities.

RCP Build 008 adds a common pre-operation switch gate. It emits:

```text
Resident command does not support this feature. Use :DIR.
```

The matched command name replaces DIR. It returns handled without changing
DU, DMA, file contents or protected runtime state. It does not launch or search
for a transient. Exact space-delimited tokens match anywhere in the argument
span; slash characters inside operands do not trigger the gate. The gate
recognizes the switch sets documented in the user guide, including valid DIR
parameter values. Unknown/malformed tokens retain existing parsing behavior.
It does not claim to recognize every unsupported operand feature. Standalone
/VER takes precedence; mixed /VER retains its existing usage diagnostic.

The implementation shares version-banner address calculation across dispatch
entries and omits the unused standalone UV_CHECK wrapper from resident RCP.
Standalone utilities retain their existing source expansion and version logic.
IX/IY and the argument span are preserved by the gate.

Measured payload: 7,161 bytes, allocation 7,168 (previously 6,785/6,912).
The 256-byte allocation increase applies only to reclaimable command memory.
Relocations decrease from 744 to 742; the existing 1,536-byte carrier header
remains sufficient. No descriptor/ABI, CCP, reloader, BDOS, BIOS or protected
layout change is required. Unloaded transient capacity remains 53 KiB plus
one byte. No automatic-handoff prototype is incorporated into production.

Validation: test_resident_feature_hints.py runs leading/trailing options,
standalone versions, unknown/malformed input and register-preservation checks
at three relocation origins. Resident TYPE, shared selector, utility identity
and carrier format regressions cover ordinary behavior. Native ZSM4/LINK assembly produces 7,161 byte-identical bytes. A disposable
cpmsim campaign exercises all five command families and resident /VER with a
byte-identical disk image afterward; transcript:
`/private/tmp/resident-hints-cpmsim-20261013/transcript.txt`. The matching Model 4 campaign passes all five families and /VER, also
leaving its disk image byte-identical; captures:
`/private/tmp/resident-hints-model4-20261013/screens.txt`. Its first trial
dropped the initial command during boot input; increased settling time and
a repeated DIR check resolved the harness issue.
