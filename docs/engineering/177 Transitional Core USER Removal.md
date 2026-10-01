# Engineering Specification 177: Transitional Core USER Removal

## Result

The transitional `USER` implementation has been removed from the core CCP.
Unqualified `USER n` is owned by `RCP.CPX`; a drive-qualified command such as
`A:USER n` continues to exercise the matching `USER.COM` fallback. BDOS
Function 32 remains the sole owner of the current user number.

The removal deletes the post-CPX length dispatch, decimal parser, state-setting
wrapper, and private keyword. Direct user navigation such as `5:` remains CCP
syntax and is unaffected.

## Focused evidence

- `tools/build_ccp.py` assembles all relocation origins without errors.
- `tools/test_ccp.py` passes parsing, DU execution, navigation, retained
  commands, and CPX dispatch.
- A clean z80pack image builds with the smaller CCP.
- A private cpmsim probe requires `USER 5` to produce an `A5>` prompt and
  `A:USER 7` to produce an `A7>` prompt.
- The default memory layout and 53 KiB TPA contract are unchanged.

## Disposition

This is one bounded Implementation Item 3 increment. Transitional core `DIR`
remains separate cleanup work; this change makes no claim about final CPX/RSX
interface qualification.
