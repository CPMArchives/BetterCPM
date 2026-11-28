# RomWBW four-drive acceptance

28 November 2026; macOS ARM64; pinned romwbw_emu 1.51 / RomWBW 3.5.1.
The previous seven automatic compatibility gaps are resolved. All eleven pinned
automatic groups now pass: **269 assertions, zero failures and zero errors**.
Manual, external, physical-hardware and release qualification remain separate.

## Memory and interface

The existing shared BDOS reconstructs the active allocation map whenever the
drive context changes, and publishes block ownership before leaving an unclosed
FCB. Four 80-byte DPH/binding records can therefore share one 256-byte active ALV.
They occupy 576 bytes, compared with the previous two-drive layout's 672 bytes.
No BDOS implementation change, banked allocation map, larger resident reservation
or TPA reduction is needed. Resident disk/BIO/file-loader sizes remain 462/597/145
bytes. The default maximum loadable COM remains **57,344 bytes**.

Function 181 remains block ABI 6 and advertises four logical drives. A stays
protected; B/C/D can each bind to a distinct matching HBIOS unit or be unbound.
Alias rejection covers all other live bindings. CONFIG's block submenu displays
its selected drive and supports B/C/D selection, binding, unbinding and saving.
BWCF version 3 stores all three saved mappings while preserving IOBYTE. Cold
boot restores them independently and skips unsuitable/duplicate bindings.
The installed system starts with B/C/D unbound. Earlier unpublished BWCF records
are rejected, including a checksummed version-2 fixture in the new acceptance.

## Independent compatibility

The COM binaries and their oracles are unchanged at suite revision
`a9a878fcd2e36698c7e856654a85847a004fdd20`. Their hashes are verified against
that revision's SHA256SUMS. B hosts the primary and user-area fixtures; C hosts
the distinct explicit-drive fixture. D has all 512 directory entries occupied
and all 2,048 allocation blocks allocated, including the required complete
128-record BTFULL.DAT and its record-127 marker. Host assertions validate the
full directory/allocation preconditions before starting the guest.

| Group | Passing assertions |
| --- | ---: |
| CPUTEST | 2 |
| ECOTEST | 1 |
| DISKTEST | 7 |
| CCPTEST | 12 |
| ENTRYTST | 25 |
| BIOSTEST | 5 |
| ERRTEST | 5 |
| DIRTEST | 49 |
| BDOSTEST | 56 |
| FILETEST | 68 |
| RANDTEST | 39 |
| Total | 269 |

DIRTEST 0200, FILETEST 0158/0169/0242/0278 and RANDTEST 0556/0557 now run with
their actual providers. The prior missing-provider exclusion code is removed;
the runner fails on any mismatch with its expected assertion counts, failure
or error. The historical two-drive blocked record remains unchanged.

## Additional checks and evidence

`mappings-result.json` records eleven focused checks: discovery count and invalid
index rejection, all mappings, interactive selection/binding of D, saved-map
persistence, duplicate-unit rejection without mutation, independent C unbinding,
cold alias refusal and legacy-record rejection. A BDOS-only probe alternates
163 writes to each of two still-open B/C files across logical extents. Independent
host extraction matches every byte in both 20,864-byte patterns.

The exact expanded image also passes the original 15 system checks, 17 install
checks (including host extraction of every manifest file), nine configuration
checks, 30 portable command queries and file/archive/batch smoke, native ZSM4/LINK,
and the 81-command integrated terminal lifecycle plus HELP through all three
personalities. Shared-profile (11), component-input (14) and registry (9) tests pass.

Result JSON files identify the exact tested image and checks. `build.json`
records its layout, bounds, modules, source contract and runner hashes;
`emulator.json` retains the pinned native emulator provenance. `compat-*.txt`
retains each original suite verdict. Other text files retain focused mapping,
boot and persistence sessions. Console text normalizes escapes, line endings,
trailing whitespace and workspace paths; raw captures stay in build directories.

Reproduce with `tools/build_romwbw.py`, then the RomWBW test/qualification tools
using the resulting `--image-dir`, pinned `--simulator`/`--rom` and fresh output
directories. The display qualifier takes the prepared `--workspace`; independent
compatibility and toolchain qualifiers additionally take the pinned `--suite`.
No platform release is assigned by this acceptance.
