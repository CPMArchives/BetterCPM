# Engineering Specification 86: DIRTEST Completion

## Status

The complete 72-item DIRTEST catalog is physically accounted for on the
TRS-80 Model 4 target.

## Final User Areas diagnostic

Case 0565 ran independently under `trs80gp` using private writable A: and B:
disk copies:

```text
0565  O  N  User-change continuation=00; next=01
Summary: 1 pass, 0 fail, 0 error, 1 observations
```

BetterCP/M retained the active enumeration across the tested user change and
Search Next returned directory slot one. CP/M 2.2 does not guarantee this
continuation behavior, so the result is recorded as evidence rather than a
compatibility requirement.

The User Areas group is closed with eight required passes and one diagnostic
observation.

## Catalog accounting

| Group | Required pass | Diagnostic observed | Out of scope | Total |
| --- | ---: | ---: | ---: | ---: |
| Search | 9 | 2 | 0 | 11 |
| Delete | 9 | 1 | 1 | 11 |
| Rename | 10 | 4 | 4 | 18 |
| File Attributes | 12 | 2 | 0 | 14 |
| Search Continuation | 4 | 5 | 0 | 9 |
| User Areas | 8 | 1 | 0 | 9 |
| **Total** | **52** | **15** | **5** | **72** |

All 52 required cases pass. All 15 non-guaranteed cases have been observed.
The five explicitly out-of-scope cases inspect private DRI mechanisms,
wildcard Rename, timestamps, or directory compaction and are intentionally not
executed as BetterCP/M compatibility requirements.

Three required cases use terminal or external procedures: read-only Delete
0370, read-only Rename 0371, and CCP/BDOS user-state integration 0567. All
three have been physically executed and pass.

DIRTEST therefore closes with zero required failures, zero errors, and no
applicable item left unaccounted for.

