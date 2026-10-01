# Engineering Specification 176: Transitional Core WARM Removal

## Result

The transitional `WARM` implementation has been removed from the core CCP.
Unqualified `WARM` now follows normal transient lookup and runs `WARM.COM`, the
single implementation retained by the frozen command inventory. Interactive
users continue to have the canonical disk-independent Ctrl-C warm boot.

The removal deletes the post-CPX length dispatch, command recognizer, and
private keyword. It does not change BDOS Function 0, Ctrl-C handling, transient
return, or reconstruction behavior.

## Focused evidence

- `tools/build_ccp.py` assembles all relocation origins without errors.
- `tools/test_ccp.py` passes the retained CCP command and dispatch checks.
- A clean z80pack image builds with the smaller CCP.
- The completed-command probe invokes unqualified `WARM` and requires a fresh
  prompt, establishing that ordinary lookup reaches `WARM.COM` after removal
  of the core fallback.
- The default memory layout and 53 KiB TPA contract are unchanged.

## Disposition

This is one bounded Implementation Item 3 increment. Transitional core `DIR`
and `USER` remain separate cleanup work; this change makes no claim about their
removal or the final CPX/RSX interface qualification.
