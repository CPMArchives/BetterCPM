# Engineering Specification 178: Transitional Core DIR Removal

## Result

The transitional resident `DIR` implementation has been removed from the core
CCP. Unqualified `DIR` is owned by `RCP.CPX`; a drive-qualified command such as
`A:DIR` continues to exercise the matching `DIR.COM` fallback. This completes
the removal of ordinary command copies from the frozen six-command CCP.

The removal deletes the unreachable recognizer, directory search and formatting
code, private FCB and scratch state. PEEK retains the shared CR/LF string under
a command-neutral name. Common FCB parsing and drive/user qualification helpers
remain because the retained monitor commands and transient loader use them.

## Focused evidence

- `tools/build_ccp.py` assembles all relocation origins without errors.
- `tools/test_ccp.py` passes parsing, DU execution, navigation, retained
  monitor commands, PEEK formatting, and CPX dispatch.
- A clean z80pack image builds with the smaller CCP and its recalculated base.
- A private cpmsim probe requires unqualified `DIR` to list `RCP.CPX` and
  drive-qualified `A:DIR` to list `DIR.COM`.
- The default memory layout and 53 KiB TPA contract are unchanged.

## Disposition

The transitional core-command cleanup is complete. Implementation Item 3
remains open for the outstanding frozen CPX/RSX interface and lifecycle
qualification; this increment does not broaden or close that work.
