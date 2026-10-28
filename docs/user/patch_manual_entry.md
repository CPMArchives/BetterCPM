## PATCH verified binary file patching

**PATCH 1.0 development candidate.** Newly built Utilities packages include PATCH
on the NOAH companion disk. Native/cross parity and cpmsim execution checks pass;
Model 4 qualification and paired release acceptance remain pending. The
[engineering specification](../engineering/PATCH-Specification.md) controls the
interface, and [implementation notes](../engineering/PATCH-Implementation.md)
record qualification limits.

PATCH applies verified byte replacements from a patch instruction file to a
binary input file, producing a separate output. The original input remains
unchanged. Every expected byte must agree with the original before PATCH creates
any output. The patched copy retains the input's length and is read back in full
before success is reported.

### Running PATCH

```text
PATCH FIX.PAT
PATCH FIX.PAT /INPUT=B3:PROGRAM.COM /OUTPUT=D0:PROGRAM.NEW
PATCH FIX.PAT /VERBOSE
```

The patch file can name the input and output. `/INPUT=` and `/OUTPUT=` override
those names independently. Both names must be available from the patch file or
the command line; PATCH does not guess them.

```text
PATCH patchfile [ /INPUT=filespec ] [ /OUTPUT=filespec ] [ /VERBOSE ]
```

| Option | Effect |
| --- | --- |
| `/INPUT=filespec` | Select the original input, overriding the patch file's INPUT directive. |
| `/OUTPUT=filespec` | Select a separate patched output, overriding the OUTPUT directive. |
| `/VERBOSE` | Display instructions and validation results, continuing through independently identifiable mismatches. |
| `/HELP` | Display help without file access. |
| `/VER` | Display the utility identity without file access. |

Option names are case-insensitive. Unknown or malformed options, conflicting
duplicate options and missing values are errors. The patch file is the only
positional operand. Exact HELP or VER queries ignore other arguments, with HELP
taking precedence. `/VERBOSE` is an operational option, not a VER query.

Each filename must identify one ordinary CP/M file, optionally with a single
BetterCP/M drive/user qualifier. Wildcards, DU lists and ranges are not accepted.
Unqualified names, including names inside the patch file, refer to the drive/user
logged when PATCH started; they are not relative to the patch file's location.
The output must differ from both the input and the instruction file after DU
resolution. Alternate spellings of the same identity do not bypass this rule.

If needed, qualify the executable separately, for example
`C0:PATCH A3:FIX.PAT`. The executable's location does not change filename defaults. With the primary
Utilities disk in B:, mount the NOAH companion in C: and keep D: as your work
disk. PATCH shares the companion because the primary 332K disk lacks space.

### Writing a patch file

Use a plain text file, conventionally named with a `.PAT` extension:

```text
; BetterCP/M PATCH file
; Format: OFFSET: OLD -> NEW

INPUT  PROGRAM.COM
OUTPUT PROGRAM.NEW

0120: CD 05 00 C9 -> 00 00
0122: 00 C9       -> 3E 02
02A4: 3E 01 15    -> 3E 02
```

The bytes here illustrate the language; they are not a correction for an actual
program. Use expected and replacement bytes appropriate to the exact file version
you intend to patch.

`INPUT` and `OUTPUT` are optional if supplied on the command line. Each may occur
at most once in the file, even when a command-line override is supplied. Blank
lines are ignored. A semicolon begins a comment, including after an instruction.
The explanatory header is recommended but not required.

Offsets are hexadecimal byte positions measured from the start of the stored
file: offset `0000` is its first byte. A trailing `H` or `h` is optional. These
are file offsets, not DDT load addresses. For a COM file loaded at 0100h, debugger
address 0220h normally corresponds to file offset 0120h; check the actual file
layout when translating a patch notice.

OLD and NEW contain nonempty sequences of two-digit hexadecimal bytes separated
by spaces or tabs. Letter case does not matter. NEW may be shorter than OLD but
cannot be longer. Whitespace around the colon and ASCII arrow `->` is allowed.
Each physical line may contain at most 255 characters, excluding its line ending.
Longer or malformed lines are errors, not truncated instructions. CRLF, bare CR
and bare LF are accepted. A Ctrl-Z terminates instruction text; following stored
padding may contain zeros or Ctrl-Z bytes, but no further statements. NUL bytes
before Ctrl-Z are errors. There is no
arbitrary limit on the number of instructions; large patch files may require
additional disk passes.

### Verification context and overlapping ranges

In the first instruction above, PATCH verifies all four original bytes
`CD 05 00 C9`, then replaces only the first two with `00 00`. The trailing OLD
bytes provide context and remain unchanged by that instruction.

The next instruction verifies the original `00 C9` at offset 0122 and replaces
those two bytes with `3E 02`. Together the first two instructions change the four
bytes at 0120 to `00 00 3E 02`.

Every check uses the unmodified input, so instruction order does not change the
result. Verification ranges may overlap. Replacement ranges must not overlap,
even if they would write identical values. Each complete OLD range must fit
inside the input. PATCH rejects any mismatch, duplicate write, overlapping write
or out-of-range instruction before creating output.

### Existing output files

After validating the complete patch, PATCH asks before replacing an existing
output. The message identifies the resolved destination drive/user and filename:

```text
PATCH: D0:PROGRAM.NEW exists.
Overwrite? (y/N/r/?)
```

| Response | Effect |
| --- | --- |
| `Y` | Authorize replacement of this output. |
| `N` or Enter | Abort without changes. |
| `R` | Enter a different output filename, optionally with one DU qualifier. |
| `?` | Display `Y Yes, N No (abort), R Rename, ? Help`, then repeat the same file's prompt. |

Choices accept either case. The default is No. Other keys repeat the question
without authorizing a write. Repeated help changes no files or choices. A renamed
destination is checked again for identity conflicts and existence; another
collision produces the same question.

For an authorized overwrite, PATCH writes and fully verifies a temporary copy
on the destination DU before moving the old output to a backup name and
installing the new file. The backup is deleted only after installation succeeds.
Allow free disk space for the complete new copy while the old output still
exists. The input and patch instruction file are never used as temporary or
backup destinations.

If installation fails, PATCH attempts to restore the previous destination. If
restoration fails too, it retains the backup and reports its exact DU/name and
the staged file's state. If only backup deletion fails after successful
installation, PATCH reports success with a warning naming the retained backup.
Keep reported recovery files until you have checked the final state.

CP/M replacement is not atomic. Power loss can leave backup or temporary files,
and can temporarily leave the requested destination name absent. PATCH cannot
promise cleanup after power loss or a BDOS/BIOS error that never returns.

### Cancellation and protection

Ctrl-C cancels at safe boundaries, including while answering a collision or
entering a new filename. PATCH cleans up uncommitted output where possible and
restores your logged drive/user. It completes any immediate backup/install/
restore recovery sequence before responding to cancellation.

An instruction file with no replacements is an error. An explicit replacement
that writes the same bytes is allowed; its changed-byte count is zero.

PATCH refuses to replace a read-only or system output, without clearing its
attributes. Choose a different output or manage protection separately. A new
output is an ordinary read/write, directory-visible file; it does not inherit
the input's or former output's attributes.

Keep the input and patch file mounted and unchanged until the command finishes.
PATCH fingerprints the complete stored patch on every scan and checks input
fingerprints between phases to detect changes. These checks support consistent
processing; they do not authenticate the author of a patch.

### Results and errors

PATCH preserves every stored 128-byte logical record, including Ctrl-Z bytes,
high-bit bytes and apparent padding. It never treats the binary input as text,
inserts bytes or shortens the output. Files and offsets beyond 64 KiB are
supported within the implementation's documented addressing limits.

After writing and closing the output, PATCH rereads and compares every byte
against the expected patched copy, including untouched regions. This is mandatory;
there is no NOVERIFY option. A successful summary identifies the input and output,
instruction count, replacement-byte count, actual changed-byte count, total
output bytes and full verification status. Writing a replacement equal to the original does not count as an actual
byte change.

Normal mode stops at the first validation failure. VERBOSE shows individual
instructions and validation results and continues checking independent
mismatches where parsing remains reliable. Any validation failure prevents all
output creation in either mode. VERBOSE never authorizes a partially valid patch.

Diagnostics identify the patch filename and physical line where applicable,
and offsets and expected/found bytes when relevant. Read, write, close, readback,
space, rename and cleanup failures are reported distinctly. A handled failure
after output creation triggers cleanup where possible and explicitly identifies
files that could not be removed or restored. An incomplete output is never
reported as successfully patched.

### Historical patch notices

PATCH reads its native instruction language. It does not read DDT transcripts,
Digital Research notices, assembler source, Unix diff patches or DOS DEBUG
scripts directly. It does not patch system tracks or search for byte patterns.

Historical corrections may be distributed separately as verified native PAT
files, with the original notice and exact target version identified. Translating
and qualifying those files is separate from implementing PATCH.
