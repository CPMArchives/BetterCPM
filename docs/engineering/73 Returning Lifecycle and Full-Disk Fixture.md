# Engineering Specification 73: Returning Lifecycle and Full-Disk Fixture

## Status

Implemented and physically qualified on the TRS-80 Model 4 target.

## Fixture

The compatibility build now reproducibly generates
`BetterCPM-Conformance-Drive-D-Full.dmk`. It contains the suite's canonical
full-disk profile:

- `BTFULL.DAT`, 128 records, with `FULL-127` at record 127;
- `BTREL.DAT`, one record; and
- `BTFILL.DAT`, occupying all remaining allocation blocks.

The command runner accepts `--drive-d` and, like its other mounted media,
copies this image before allowing a compatibility program to modify it.

## Result

The six required returning RANDTEST lifecycle cases pass physically:

```text
0550  P  R  Prereq=00; lifecycle=00
0551  P  R  Prereq=02; lifecycle=00
0553  P  R  Prereq=02; lifecycle=00
0555  P  R  Prereq=03; lifecycle=00
0556  P  R  Prereq=01; lifecycle=00
0557  P  R  Prereq=01; lifecycle=00
```

The first 0556 attempt, made without a D: fixture, failed setup with
`Prereq=FF`; it was not a BDOS lifecycle failure. With the required full D:
fixture mounted, both full-disk cases passed. This verifies that a completed
extent survives a later extension failure and that failed growth does not
claim a new logical record.

Cases 0368 and 0369 are terminal file-read-only procedures and remain separate
from this returning slice.

