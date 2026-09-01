# Engineering Specification 82: DIRTEST Search Continuation Required

## Status

All required DIRTEST Search Continuation cases are physically qualified on the
TRS-80 Model 4 target.

## Result

Each case ran independently under `trs80gp` using private writable A: and B:
disk copies:

```text
0542  P  R  Enumerated extents=02; next=00
0543  P  R  Visible matching extents=02; next=00
0545  P  R  Search first/next=00; next=01
0546  P  R  Query between searches=00; next=01
```

All four required cases pass with zero failures or errors. The slice verifies
that Search First and Search Next enumerate matching directory entries rather
than collapsing a multi-extent file to one filename, that matching extents
remain separately visible, that the caller-owned search FCB remains usable
through continuation, and that a harmless state-query BDOS call does not
terminate the enumeration.

Engineering Specification 83 records cases 0541, 0544, 0547, 0548, and 0549.
They describe non-guaranteed lifecycle, lowercase-FCB, enumeration-order, and
invalid-drive behavior rather than requirements of the portable CP/M 2.2
contract.
