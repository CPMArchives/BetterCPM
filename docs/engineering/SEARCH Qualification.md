# SEARCH 1.0 candidate qualification

**2026-10-26–27: component checks PASS; Utilities Disk acceptance pending.**
The tested executable remains `SEARCH 1.0 (001-dev)`. This record does not assign
an accepted input baseline, publish a release, or reuse another component's
paired-image acceptance. The [specification](SEARCH%20Specification.md) remains
authoritative. No production SEARCH code or executable bytes changed in this
qualification increment.

Candidate: **8,044 bytes**, SHA-256
`a771b4fcf0b0b04133f3c8d54eb3d9917f66b366a11e95d049a51dc32aa77862`.
The [retained evidence](search-qualification/2026-10-26/platforms.json) binds the
platform checks to this binary and identifies their input System images. The
preceding implementation record retains native/cross parity and full behavioral
coverage; this increment addresses its resource, directory and media-error gaps.

## Resource budget

An **8 KiB TPA payload above 0100h** passed the native paging/suppression case on
stock CP/M 2.2, BetterCP/M cpmsim and BetterCP/M Model 4. The image, including its
512-byte private stack and 16-byte guard, occupies 8,044 of those 8,192 bytes.
A resident observer restores the original SEARCH entry bytes before execution,
places a BDOS jump relay at 2100h, advertises it through address 0006h, and sets
the incoming stack to 2100h. The original kernel/BIOS remain at their original
addresses; the observer resides at 8000h. Thus this is an effective TPA/entry-stack
budget test on the real platform services, not a relocated 8 KiB operating system
or a claim that the physical machine needs only 8 KiB of RAM.

Native stack watermarks observed **64 of 512 bytes** used on all three platforms,
with the guard intact. Stock CP/M additionally passed help, version, invalid
command, HEX-only and case-insensitive TEXT paths under this TPA fence. The CPU
command suite previously observed 70 bytes. Ten resource cases pass with an
additional **256 bytes** of simulated service-stack use, with maximum combined
use **326 bytes**, guard intact and no writes above image plus the two-byte
caller return slot. The adapter cases include queries, validation, results,
paging, suppression, open/read/close/directory errors and excerpt-read failure.

These are measured exercised paths, not an absolute stack-depth proof for every
third-party BIOS, interrupt handler or resident extension. Arbitrary providers
must preserve ordinary BDOS contracts and fit their caller-stack use in the
remaining reserve. The exact absolute minimum TPA is not advertised; 8 KiB is the
tested budget. The program does not grow storage with directory or file size.

## Directory cost

The CPU fixtures measure directory-service calls independently of host timing:

| Qualifying entries | Search First calls | Search Next calls | Primary reads |
| ---: | ---: | ---: | ---: |
| 8 | 16 | 57 | 8 |
| 32 | 64 | 993 | 32 |
| 64 | 128 | 4,033 | 64 |
| 128 | 256 | 16,257 | 128 |

A stock CP/M 2.2 floppy with all **64 directory entries** occupied was searched
completely, without changing its data image. At an explicitly configured 4 MHz,
8/32/64 files took approximately **1.0/6.9/23.0 seconds** from command submission
to the returning prompt. These are cpmsim host elapsed measurements, including
command/loading overhead; they are not physical floppy timings. Unlimited-speed
runs are recorded separately and must not be mistaken for 4 MHz results.

BetterCP/M cpmsim additionally passed 56 selected files on a nearly full directory;
Model 4 passed 80 selected files on its 128-entry System volume alongside existing
files. Directory order, extent collapsing and constant storage remain intact.
The quadratic replay cost is accepted as a documented candidate limitation;
no timing requirement is specified. Large directories can take substantial time,
and physical-drive timings remain hardware dependent.

## Media errors and console scope

Stock CP/M was tested with an out-of-image allocation; BetterCP/M cpmsim with a
valid directory and a truncated separate data-drive image. Both reached the real
BIOS/BDOS **Bad Sector** interaction. Ctrl-C there caused an OS warm boot, without
SEARCH totals. Stock returned to A; BetterCP/M returned to B. These are externally
abandoned calls, so SEARCH's normal cleanup and complete-total guarantees do not
apply. Both damaged data images remained unchanged. This is emulated media-failure
evidence, not a physical damaged-disk test.

A BDOS implementation may also ignore a physical error and return apparent
success, or disguise a directory failure as normal end-of-search. SEARCH cannot
identify hidden failures through ordinary BDOS. A distinguishable returning
failure remains an essential diagnostic with incomplete observed totals; the
hostile adapter regression suite passes those paths. No BIOS interception or
new service is introduced to work around an unobservable platform result.

Model 4 command strings are supplied by startup SUBMIT. Independent boots isolate
the results, directory and resource cases; actual BREAK/Ctrl-C matrix input tests
SEARCH's pager. The earlier two-key checks cover Enter and Ctrl-C. Broad arbitrary
interactive command typing is not claimed. The supported console remains 80×24.
All selected fixture contents are read back unchanged; the Model 4 whole disk is
not immutable because SUBMIT creates and removes its spool.

## Reproduction and candidate packaging

Build SEARCH, then run:

```text
python3 tools/qualify_search_resources.py
python3 tools/qualify_search_native.py --report build/search-native-qualification
python3 tools/test_search_media.py --qualification \
  --image-dir /path/to/qualified/z80pack/runtime \
  --model4-image /path/to/qualified/Model4-System.dmk \
  --report build/search-platform-qualification
python3 tools/test_search_scan.py
python3 tools/test_search.py
```

The native script defaults to a configured 4 MHz; `--mhz 0` records an explicitly
unlimited-speed run. Its default 8 KiB fence is exercised by the observer, while
the uninstrumented SEARCH command supplies directory timings. Platform images
are copied before staging; all tests use disposable media.

`tools/package_search_candidate.py --output /path/to/SEARCH-candidate.zip
--qualification /path/to/platform/evidence.json` produces a separate review
package containing the exact executable/build record, native source, qualification
record, complete tracked repository sources/documentation/licenses and per-file
hashes. It rejects a mismatched binary/build/source or absent platform PASS and
refuses to replace an existing package. The archive is deterministic for equal
inputs and every extracted member is checked before writing.

Final Utilities Disk integration remains a release gate: adding SEARCH changes
both image hashes and invalidates existing paired-image receipts for other
components. New paired images and their acceptance must be produced together;
a SEARCH-only review package does not satisfy that whole-disk gate. No frozen
image, manifest membership or component baseline is changed by this increment.
