# BetterCP/M Compression Utilities — Common Engineering Specification

## Status and implementation boundary

The maintainer froze compression features for release 1.0 on 2026-10-23.
SQ/USQ, CR/UNCR and LZH/UNLZH are six independent Z80 commands using the common
codec ABI, with safe temporary output, historical naming, `/VER` and the adopted
short-corner `/HELP`. Final feature baseline: `00e6785`, merged in `569825d`;
each command identifies as version 1.0 Build 003. The exact final binary hashes
and historical exchange results are retained in the
[qualification record](Compression%20Historical%20Interoperability.md).

Individual commands are the release 1.0 scope. A unified interface, new algorithm
versions, additional format support and convenience features remain post-1.0.
Qualification defects may still require corrections and retesting. The
[1.0 release checklist](../releases/1.0-ROADMAP.md#compression-utilities--10-feature-freeze-and-release-checklist)
tracks the remaining native build, BetterCP/M platform and final disk gates.
Utilities images remain provisional pending those separate acceptance checks.

The assembly-time macro library has no OS dependencies. The command owns CP/M
file policy, buffering, filenames, temporary files and publication. Native ZSM4
assembly and command execution on every BetterCP/M platform are not established
by the host assembler and stock CP/M 2.2 tests.

Related specifications: [SQ/USQ](SQ-USQ%20Specification.md),
[CR/UNCR](CR-UNCR%20Specification.md), [LZH/UNLZH](LZH-UNLZH%20Specification.md).
Operating instructions: [Utilities Manual](../user/utilities_manual.md#compression-utilities).

## Source and macro structure

- [codec.inc](../../src/codec/codec.inc): common constants and prefix definitions.
- [codec.mac](../../src/codec/codec.mac): configuration checks, callback dispatch,
  state/status handling; emit `CODEC_CODE` once.
- `src/codec/<algorithm>.inc`: definitions and workspace contract; emits nothing.
- `src/codec/<algorithm>.mac`: callable code under `<ALGORITHM>_CODE`; emit once
  after including the common definitions and algorithm definitions.
- [codecfile.mac](../../src/utilities/common/codecfile.mac): shared command parser,
  CP/M byte callbacks, record buffering and cleanup. Commands supply `UC_*`
  storage and messages, then emit `CODEC_FILE_IO` and `CODEC_FILE_CLEANUP` once.

Macros emit ordinary callable routines; they do not run the algorithm while
assembling. The caller allocates a separate context. Code and constant tables
are immutable and may serve several contexts. Do not invoke the same context
recursively or concurrently. Distinct contexts can be initialized and processed
independently, provided callbacks and source positions are likewise independent.

Build with z80pack `z80asm -e32` (32 significant symbol characters). Neither
include files nor macro definitions select an origin, allocate a context or end
the containing assembly. Public library entry labels and common helpers are
emitted once per program; internal helper labels are not a supported interface.

## Common Z80 ABI v1

Every entry receives `IX = context`. Preserve IX, IY, AF', BC', DE', HL' and
stack balance. AF/BC/DE/HL are caller-saved. No alternate-register instructions,
IY scratch use, recursion or private stack switching occur in the codec. The
standalone command, separately, saves its entry SP and uses a 256-byte stack.

All offsets are decimal and relative to IX. Words are little endian, without an
alignment requirement. The caller guarantees an accessible, nonwrapping 16-byte
prefix even when declaring an invalid size. For a valid operation, the entire
declared allocation must exist and must not wrap 64K; `CX_SIZE` cannot establish
RAM ownership. The size includes the prefix, not just algorithm workspace.

| Offset | Bytes | Field | Contract |
| ---: | ---: | --- | --- |
| 0 | 1 | `CX_ABI` | Caller sets 1. |
| 1 | 1 | `CX_OPTIONS` | Caller sets 0. |
| 2 | 1 | `CX_PHASE` | Codec-owned state. |
| 3 | 1 | `CX_STATUS` | Codec-owned status. |
| 4 | 1 | `CX_DETAIL` | Codec-owned diagnostic/callback reason. |
| 5 | 1 | `CX_RESERVED` | Caller sets 0. |
| 6 | 2 | `CX_READ` | Required callback address. |
| 8 | 2 | `CX_WRITE` | Required by encoders and decoder RUN. |
| 10 | 2 | `CX_REWIND` | Required by SQ; unused by other algorithms. |
| 12 | 2 | `CX_USER` | Opaque caller-owned pointer, available to callbacks. |
| 14 | 2 | `CX_SIZE` | Total accessible context allocation. |

Caller-owned prefix configuration and encoder name fields remain stable for the
operation. INIT validates ABI, options, reserved byte, capabilities and size,
then resets algorithm state. An undersized prefix returns `CS_SPACE` without
writing any context byte. Other failures with an accessible prefix latch.

| Value | Phase |
| ---: | --- |
| 0 | `CP_RESET` — caller's initial state |
| 1 | `CP_READY` — INIT succeeded |
| 2 | `CP_DATA` — processing/header/scan stage established |
| 3 | `CP_DONE` — verified completion |
| 4 | `CP_FAILED` — original failure remains latched until INIT |

Ordinary success is NC, A=0. Failure is C, A=status; detail is in `CX_DETAIL`.
GET alone returns C/`CS_END` at verified normal completion. RUN and END return
NC at normal completion. Repeated completed processing calls perform no I/O;
GET repeats `CS_END`, RUN/END succeed. A wrong-phase processing entry latches
`CS_STATE`, with the actual phase as detail. INIT can recover a failed context.

| Hex | Status | Meaning |
| --- | --- | --- |
| 00 | `CS_OK` | Success |
| 01 | `CS_END` | GET's verified end |
| 02 | `CS_FORMAT` | Wrong signature |
| 03 | `CS_VARIANT` | Unsupported format revision/checking selector |
| 04 | `CS_TRUNC` | Physical EOF before verified stream end |
| 05 | `CS_CORRUPT` | Invalid tree/code/repeat/internal bounds |
| 06 | `CS_CHECK` | Checksum mismatch or SQ pass comparison failure |
| 07 | `CS_READ` | READ failed |
| 08 | `CS_WRITE` | WRITE failed |
| 09 | `CS_NOREWIND` | Required rewind capability unavailable |
| 0A | `CS_REWIND` | REWIND failed |
| 0B | `CS_SPACE` | Context/header/counter capacity exceeded |
| 0C | `CS_STATE` | Entry called in wrong phase |
| 0D | `CS_CONFIG` | Invalid ABI/options/reserved/callback/name configuration |

Common configuration details 1..5 mean ABI, options, reserved byte, READ and
WRITE respectively. Algorithms assign additional details in their `.inc` files.
Callback failures store the original callback reason in detail. Not every
algorithm uses every status.

### Callback signatures and indirect calls

Callbacks receive IX unchanged and obey the same register-preservation ABI.
A callback may clobber the primary registers. Codec routines save their live
values across dispatch. No global input/output pointer is required.

| Callback | Input | Success | Event/failure |
| --- | --- | --- | --- |
| READ | IX=context | NC, A=next byte | C/A=0 physical EOF; C/A=1..255 read error |
| WRITE | IX=context, A=byte | NC accepted | C/A=0..255 write error |
| REWIND | IX=context | NC, source restored to original start | C/A=0..255 rewind error |

`CX_CALL_READ/WRITE/REWIND` load the callback address into HL and tail-jump via
`JP (HL)`; the callback's RET returns to the original caller. WRITE's incoming
A/flags reach the callback. Dispatch alone does not translate errors or EOF.
READ EOF is normal for encoder input; for decoders it is truncation until the
encoded end and required checksum have been consumed.

READ advances one byte per success. WRITE acceptance is not a file commit:
flush, close and publication are caller responsibilities. SQ's REWIND must also
reset caller-side buffering and restore the identical source snapshot. Decoder
GET and END do not require WRITE; decoder RUN checks it before consuming data.
INIT and HEAD never produce decoded output. Decoded-byte counters include
GET/END bytes, not only bytes accepted by WRITE.

### Context and standalone image sizes

| Algorithm | Context bytes, including prefix | Build 003 COM bytes |
| --- | ---: | ---: |
| SQ | 3524 | 8123 |
| USQ | 1440 | 5398 |
| CR | 25207 | 29443 |
| UNCR | 26582 | 31206 |
| LZH | 11943 | 17225 |
| UNLZH | 6646 | 12215 |

COM sizes are build snapshots, not fixed ABI constants or universal minimum RAM
claims. Images include their allocated context, FCBs, buffers and private stack;
loading at 0100h must fit below the current BDOS/loader boundary. Additional
loaded extensions reduce available TPA. The codec alone allocates none of this.
Use each `*_CONTEXT_SIZE`, never the COM size, for an embedded caller.

## Embedding a decoder

The following layout shows a USQ caller. `MY_READ` and `MY_WRITE` are supplied
by the containing program and obey the callback table above. They can recover
their stream state through `CX_USER`; they must preserve the index/alternate
registers. The same prefix and calling convention apply to every algorithm.

```asm
        INCLUDE codec.inc
        INCLUDE codec.mac
        INCLUDE usq.inc
        INCLUDE usq.mac

DECODE:
        LD IX,MY_CONTEXT
        CALL USQ_INIT
        RET C
        CALL USQ_HEAD
        RET C
        CALL USQ_RUN
        RET                     ; NC only after verified completion

        ; Emit outside the caller's execution fall-through.
        CODEC_CODE
        USQ_CODE
MY_CONTEXT:
        DB CX_ABI_VERSION,0,CP_RESET,CS_OK,0,0
        DW MY_READ,MY_WRITE,0,MY_STREAM_STATE,UQ_CONTEXT_SIZE
        DS UQ_CONTEXT_SIZE-CX_PREFIX_SIZE
```

The caller must check returned carry and stage output if a failure must not
expose partially decoded bytes: RUN can write many bytes before a checksum
fails. Successful RUN is not equivalent to flushing or committing that staged
output. A GET-based caller tests C/A=CS_END for verified finish; other carry
statuses are failures. END is useful after consuming a prefix, but still reads
and verifies the rest rather than abandoning the input unchecked.

For encoding, set the bounded algorithm NAME before INIT; call `SQ_INIT`,
`SQ_SCAN`, `SQ_RUN`, or `CR_INIT`, `CR_RUN`, or `LZH_INIT`, `LZH_RUN`, checking
carry after each call. SQ needs both a READ stream and REWIND; the other encoders
need READ and WRITE only. The command programs are complete examples of staged
output and error cleanup, beyond this byte-stream sketch.

## Standalone command contract

File processing in all six commands accepts:

```text
COMMAND [drive:]file [destination-drive:]
```

Drive letters A..P and plain 8.3 names are case-insensitive. Source drive defaults
to the logged drive; destination independently defaults to the logged drive,
not the source or program's drive. Both use the current user area. Accept spaces
or TAB between operands, and a trailing filename dot as no extension. Reject
empty basenames, overlong fields, spaces within names, wildcards, paths, explicit
user/DU operands, quotes, extra operands, other switches and destination filenames.
Standalone `/VER` is the additional identification form. No overwrite switch,
wildcard iteration or interactive prompts exist.

The parser reads the bounded command tail at 0080h; it does not trust default
FCBs. It uppercases letters and accepts digits plus `!#$%&'()-@^_{}~` in fields.
No high-bit filename character is normalized into an ASCII character.

Encoders derive a destination extension and embed a canonical original name
before OPEN can change FCB attribute bits. Decoders use the validated header
name, not the input extension. USQ validates the complete raw name; UNCR and
UNLZH take the stem through the first dot and up to three extension slots,
trim their trailing blanks and ignore subsequent metadata. They still reject
unsafe names. No decoder restores attributes, timestamps, user areas or drives.

### Standalone /VER and /HELP

All six commands accept case-insensitive standalone `/VER`, with space/TAB
padding. Exact `/VER` tokens combined with any other operand/token print
`Invalid /VER usage.` without running the command. Longer tokens such as
`/VERIFY` remain normal parser errors. Standalone `/HELP` uses the same early
path and prints the compact purpose/Usage corner and unframed Options list.
Help retains the metadata title and omits the `/VER` branding, repeated query
syntax, examples and detailed operating rules; those remain in the manual.
Exact `/HELP` mixed with other input reports `Invalid /HELP usage.`; exact `/VER` takes precedence in either
order. `/HELPER` is a normal syntax error. Empty/malformed invocations print
short syntax plus `Use NAME /HELP for help.` See the common
[help standard](../../specifications/UTILITY-HELP.md).

Each command's independent 1.0 Build 003 identity is owned by
`metadata/utility-versions.tsv`. Builders use `tools/codec_version.py` to expand
`codecver.inc` from metadata plus the shared `version.inc` query. `/VER` output is four
CR/LF-terminated ASCII lines: `NAME version (Build nnn)`, `  - - -`,
` | BetterCP/M Utilities`, and ` | purpose`. Normal output has no version banner.
The counter has a minimum of three digits, with no truncation above 999.

Startup saves entry SP and selects its 256-byte private stack before the query.
The low 128 stack bytes hold a bounded, TAB-normalized copy of the command tail;
the query frames use the upper half. The original tail remains unchanged.
Handled requests return directly through restored entry SP, before flags, FCBs,
codec workspace, source/destination drives or files are initialized. The only
BDOS operation is function 9 for the identity/help/error string. No function 25/26,
provider query, warm boot or codec callback is used on this path. This is command
startup code; the algorithm macro ABI remains unchanged.

### CP/M record adapter

Use BDOS at 0005h: functions 9 (messages), 15/16 (open/close), 17 (search first),
19 (delete), 20/21 (sequential read/write), 22 (make), 23 (rename), 25 (logged
drive) and 26 (DMA). No direct BIOS/disk calls or user-area changes occur.
Each source/output buffer is 128 bytes; directory searches have separate DMA
storage. READ result 0 provides a record, 1 is EOF, other values are errors.
WRITE succeeds only on result 0; open/close/make/rename/delete check FFh failure.

All bytes of successful input records are data, including 1Ah and existing
padding. SQ reads those records twice; CR/LZH and each decoder read once.
The library has byte-stream length, but CP/M 2.2 has record length: final partial
output records are padded with 1Ah; exact multiples do not add another record.
A zero-byte decoded result is an empty file. Decoders stop at verified encoded
end; adapter read-ahead may have fetched the containing record. This differs
from the library's promise not to consume beyond its current byte/checksum.

### Safe output lifecycle

1. Parse and construct/validate names. Refuse source/destination identity and
   an existing final destination. Decoder HEAD validates before any MAKE;
   SQ additionally completes its first pass and rewind before MAKE.
2. Search candidates in the destination drive/current user; skip existing
   files and the final name. MAKE only an absent candidate. Track ownership
   only after successful MAKE. All five 36-byte FCBs are initialized explicitly.
3. Encode/decode into the temporary. Require encoded completion and checksum
   verification, flush the final record, then successfully close output and input.
4. Search for the final name again, then rename the owned temporary to it.
   Only successful rename relinquishes temporary ownership and prints completion.
5. On a handled failure, attempt closes and delete only the owned temporary.
   Preserve source, existing destination and preexisting temporary files. Report
   cleanup failure if a close/delete fails. Reset DMA to 0080h, restore entry SP
   and RET to the caller on success and handled errors.

| Command | Temporary candidates |
| --- | --- |
| SQ | `SQU00000.$$$` through `SQU99999.$$$` |
| USQ | `USQ00000.$$$` through `USQ99999.$$$` |
| CR | `CRU00000.$$$` through `CRU99999.$$$` |
| UNCR | `UCR00000.$$$` through `UCR99999.$$$` |
| LZH | `LZU00000.$$$` through `LZU99999.$$$` |
| UNLZH | `ULZ00000.$$$` through `ULZ99999.$$$` |

This is a single-task CP/M policy. Search plus MAKE/RENAME is not atomic and
cannot guarantee safety against concurrent writers. Power loss or nonreturning
BDOS/BIOS aborts may leave a partial or complete temporary. Cleanup does not
promise recovery from such aborts. No application-level cancellation polling,
progress display, compression-ratio report or portable shell exit-code protocol
is implemented. Additive checksums detect some damage; they are not authentication.
Compression may expand a file, and output needs free space even on a failure path.

## Build and validation

Run `python3 tools/build_<command>.py` for each lowercase command name. Defaults
use `~/bin/z80asm`, producing COM and listing files in `build/utilities/`.
`python3 tools/build_utilities_disk.py --build` rebuilds and packages all owned
Utilities components; it verifies readback, filesystem and native DMK conversion.
It does not qualify every utility on every target platform.

`tools/test_codec.py` checks common ABI handling. Each format specification lists
library, fault-injection command and stock CP/M 2.2 tests. These execute assembled
Z80 code with z80pack sources, host C compiler, and (for disk tests) cpmtools and
expect on disposable media. Historical archives are external, authenticated
fixtures, not newly vendored source. Source-level and host-model checks must not
be described as independent historical-encoder byte identity or full release
acceptance. Reproduce tests against the exact binary being released.


## Historical executable interoperability qualification

The [historical interoperability campaign](Compression%20Historical%20Interoperability.md)
now qualifies both directions under stock CP/M 2.2 using unmodified historical
executables and preserved input files. Its evidence distinguishes successful
record comparisons, intentional filename refusals, historical empty-file skips
and a confirmed CRUNCH 2.4 producer defect. It supplements the format's library
and native command regressions; it does not broaden supported format variants.


## Version/help-entry qualification

`python3 tools/test_codec_versions.py` executes the six built commands on the
full Z80 core. The final rerun checks 344 version/help/parser cases, case/space/TAB handling,
127-byte tails, metadata-driven four-digit builds, deterministic rebuilds,
console-only handled paths, untouched files/FCBs/context/tail, stack balance,
index/alternate registers and code immutability. The shared command test model
now leaves 0100h intact for a full 127-byte tail, rather than appending a CR over
the program's first instruction.

`python3 tools/test_codec_versions_cpm.py` executes 90 commands under stock
CP/M 2.2 on disposable disks, verifying every line of all six identities and compact help screens,
invalid mixed requests, ordinary rejection of longer/unknown option tokens,
return to prompt, unchanged files and no temporary output. Existing fault-
injection and SQ/USQ, CR/UNCR, LZH/UNLZH native round-trip tests remain required.
The final historical qualification record now identifies the Build 003 binary
hashes. A later rebuild is covered only if its bytes match; changed artifacts
require relevant retesting. Final query logs are retained with the refreshed
historical evidence bundle.
