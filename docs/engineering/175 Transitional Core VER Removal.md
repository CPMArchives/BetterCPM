# Engineering Specification 175: Transitional Core VER Removal

## Result

The transitional `VER` implementation has been removed from the core CCP.
Unqualified `VER` is owned by `RCP.CPX`; drive-qualified `A:VER` continues to
exercise the matching `VER.COM` fallback. This brings the implementation into
line with the frozen resident-command boundary without changing command syntax
or reported version information.

The removal deletes the post-CPX fallback dispatch, its command recognizer, and
its private keyword and message strings. The CCP still tries navigation, its
six retained monitor commands, and the CPX chain before transient lookup. The
remaining transitional `DIR`, `USER`, and `WARM` paths are unaffected by this
increment.

## Focused evidence

- `tools/build_ccp.py` assembles all three relocation origins with no errors.
- `tools/test_ccp.py` passes parsing, DU execution, navigation, resident DIR,
  and CPX dispatch.
- A clean z80pack image build completes with the smaller CCP.
- A private cpmsim probe verifies `VER` through `RCP.CPX` and `A:VER` through
  `VER.COM` on that image.
- The default memory layout and 53 KiB TPA contract are unchanged.

## Disposition

This closes only the explicit transitional core-`VER` item. Removal of the
other transitional command copies remains separate Item 3 work and requires
their applicable CPX and transient paths to remain independently usable.
