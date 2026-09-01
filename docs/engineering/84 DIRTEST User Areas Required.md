# Engineering Specification 84: DIRTEST User Areas Required

## Status

All seven directly executable required DIRTEST User Areas cases are physically
qualified on the TRS-80 Model 4 target.

## Result

Each case ran independently under `trs80gp` using private writable A: and B:
disk copies:

```text
0559  P  R  User0/user1 search=00; next=01
0560  P  R  Set/restored user=01; next=00
0561  P  R  Same FCB user0/user1=00; next=01
0562  P  R  User0 absent/user1 found=FF; next=00
0563  P  R  Made user1/user0 lookup=00; next=FF
0564  P  R  Scoped delete/result mask=00; next=0F
0566  P  R  Public result/directory entries=00; next=02
```

All seven cases pass with zero failures or errors. They verify that the current
user participates in ordinary file identity, Function 32 coherently sets and
reports user state, an ordinary FCB contains no user selector, lookup does not
fall back across user areas, Make records current-user ownership, Delete and
Rename remain confined to the current user, and complete-directory search is
distinct from ordinary public lookup.

Case 0564 performs several complete-directory mutation and verification
passes. Its first fixed-window capture ended after cleanup but before the
result was printed. A preserved disposable disk showed no leaked temporary
entries, and an extended capture produced the clean result above. This was a
test-runner timing limit, not a BDOS hang or correctness failure.

Engineering Specification 85 adds the resident `USER` command and records the
successful CCP-integration workflow for case 0567. Diagnostic 0565 remains to
close the User Areas group.
