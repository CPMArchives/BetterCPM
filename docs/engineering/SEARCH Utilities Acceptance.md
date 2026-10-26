# SEARCH 1.0 Utilities integration

**2026-10-27: SEARCH 1.0 revision 001, paired-image acceptance.** This is the first
assigned SEARCH baseline. The earlier 001-dev candidate remains historical
qualification evidence; its checksum is not substituted for this executable.
The [specification](SEARCH%20Specification.md) remains authoritative.

## Exact program and media

`SEARCH 1.0 (001)` is **8,036 bytes**, SHA-256
`aca7362a046488c0dd0880e00bf7d03ecaaf875a09e6fc3ae8ee0830bf7271bd`.
Removing the two development suffixes accounts for the eight-byte size change.
No SEARCH matching, parsing, traversal or display behavior changed. Its builder
now also emits the prepared native source and its program/source checksums.

[SEARCH-Utilities-Acceptance.json](SEARCH-Utilities-Acceptance.json) binds actual
execution to these pairs:

| Target | System image SHA-256 | Utilities image SHA-256 |
| --- | --- | --- |
| z80pack/cpmsim | `b9a616bafec41dc4c3206e5054712c88ead80624fde0e56b5899c09d1be7c7d1` | `98041729962f77b0ea7300077696e679384a487785b57823781c43256c7a2d19` |
| Model 4/trs80gp | `578bc34cb377537e47a7e9bb1f019b20ffd9b98abc36e8acee74dfb56056eb43` | `9722108bfc189f7847accfdbc160ed2de0b40ea4acccb8f08a212b5035106850` |

SEARCH is loaded from the actual Utilities B volume. ZSM4 4.7 and LINK 1.3 from
that same volume assemble and link the prepared SEARCH source on both platforms;
every program byte matches the cross build. Native CP/M record padding is checked
separately. Both Utilities images remain byte-for-byte unchanged. Selected files
on the disposable work volumes are read back unchanged; native builds and SUBMIT
legitimately create their own work files.

The independent inventory verifies all **24 primary Utilities members**, exact
logical bytes, users, extent/allocation consistency and record padding on both
formats. There are 21 free 2 KiB blocks on the simulator disk and 254 on the
Model 4 data disk. Five corrupted membership/allocation/payload cases are rejected.
The separate NOAH companion volumes are independently inventoried too.

## Qualification and input baseline

The final assigned executable passes the assembled matcher, parser, traversal
and complete-command suites. Ten resource/error paths fit the program plus caller
return slot even with 256 extra simulated service-stack bytes; maximum combined
use is 326/512 bytes with the guard intact. Stock CP/M native builds, complete
command fixtures and an 8 KiB advertised TPA budget pass. Its full 64-entry disk
takes approximately 22.6 seconds at an emulated 4 MHz.

The installed Utilities tests pass queries, independent TEXT/HEX results and
totals, user 3/31 scope, full search after physical Ctrl-C paging suppression,
read-only fixtures, directory traversal and native parity. The work-directory
cases use 48 selected files on cpmsim and 80 on Model 4. Both targets pass the
8 KiB TPA/entry-stack fence and a 64/512-byte native stack watermark with guards
intact. This fence uses a resident observer and BDOS relay; it does not relocate
the operating system or claim that a physical machine needs only 8 KiB of RAM.

The baseline catalog records cross and native inputs separately for z80pack and
trs80gp, including exact assembler/linker identities. Subsequent selected-input
changes return to `-dev`; the baseline is not a substitute for execution evidence.
The prepared native source equals the source actually compiled on both targets.

The known limits remain: 80×24 consoles, quadratic directory replay, no physical
hardware or arbitrary interrupt/third-party BIOS stack proof, and Model 4 command
text supplied through SUBMIT. A real BIOS failure on a truncated separate data
drive reaches the OS Bad Sector prompt; Ctrl-C warm boots without SEARCH totals.
This differs from SEARCH's own paging Ctrl-C. Unobservable BDOS failures cannot
be reconstructed by the application; distinguishable returning errors retain
explicit incomplete accounting.

## Packaging and acceptance boundary

`build_utilities_disk.py --build` now builds and includes SEARCH.COM. Supplying
`--search-acceptance` requires the exact binary and both image hashes, successful
native parity and unchanged Utilities/fixture results. A changed image, program,
failed platform, missing System binding or missing preservation/parity proof is
rejected. Missing evidence leaves SEARCH pending rather than inventing a PASS.

The host Utilities package includes prepared `SEARCH-NATIVE.MAC`, build provenance,
the acceptance JSON and its checksum-verified evidence archive. Copy the native
source to CP/M as `SEARCH.MAC`; run `ZSM4 SEARCH=SEARCH`, then `LINK SEARCH[A]`.
The existing complete-repository `BetterCPM-TED-SOURCE.tar.gz` supplies corresponding
SEARCH sources, generators, shared inputs, tests, documentation and licenses.
Packaging verifies every selected SEARCH source in that archive; no redundant
third source snapshot is needed.

The [previous qualification](SEARCH%20Qualification.md) describes the historical
candidate. This acceptance concerns SEARCH and the named emulator pairs. It does
not publish a whole Utilities release, change the System images, qualify ROM/XIP,
or transfer historical component receipts to a different image hash. Other
components' [renewed media evidence](Utilities%20SEARCH%20Media%20Refresh.md)
is recorded separately with its actual scope.

## Reproduction

Build the owned Utilities artifacts, then stage new media in a new output folder:

```text
python3 tools/build_utilities_disk.py --build --output /path/to/candidate
python3 tools/test_utilities_inventory.py --artifacts /path/to/repository \
  --images /path/to/candidate --output /path/to/inventory.json
python3 tools/test_search_media.py --qualification --utilities /path/to/candidate \
  --image-dir /path/to/z80pack/runtime --model4-image /path/to/System.dmk \
  --report /path/to/disposable-search-campaign
python3 tools/collect_search_acceptance.py --campaign /path/to/disposable-search-campaign \
  --inventory /path/to/inventory.json --output /path/to/receipts
python3 tools/build_utilities_disk.py --output /path/to/accepted-candidate \
  --search-acceptance /path/to/receipts/SEARCH-Utilities-Acceptance.json
```

Pass the other exact-image component receipts when available. The final candidate
must reproduce the tested image bytes; its image reports and Utilities-SHA256SUMS
identify the generated package. No merge or public release is performed here.
