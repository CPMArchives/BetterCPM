# Cromemco sign-on correction — 28 November 2026

PASS on the rebuilt engineering candidate identified in `system-result.json`.
The original image omitted VER.COM and had no cold-start command. Resident
VER reports that the banner requires transient VER; the colon forces transient
lookup, so the missing file caused `:VER /BANNER` to fail as well.

The corrected builder includes VER.COM, STARTUP.SUB and README.TXT, and sets
the cold-start command to `SUBMIT STARTUP`. STARTUP.SUB runs `:VER /BANNER`.
The guest test requires the exact generated banner headed
`BetterCP/M 1.3 - Cromemco`, checks the explicit command, and verifies that
automatic startup does not recur across warm boots or transient execution.

The same candidate passed geometry checks, independent extraction of 140-record
files on B–D, 56 KiB TPA overwrite/reconstruction, ECHO RSX lifecycle, active
system-file integrity, and damaged/foreign carrier refusal. The test waits for
the upstream UART's delayed host input timer before supplying its first key.

`engineering-build.tar.gz` retains this candidate, prepared input hashes and
assembly listings. `system-artifacts.tar.gz` retains tested media, extractions
and guard cases; `transcript.txt` provides a newline-normalized readable console trace; exact raw bytes remain in the archive.
The executed test script is retained separately. `manifest.json` hashes the
artifacts; the original engineering checkpoint remains in the parent folder.

Hard disks and full release qualification remain deferred. This correction
only adds the missing banner utility and startup behavior to initial testing.
