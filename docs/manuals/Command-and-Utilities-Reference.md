# BetterCP/M 1.1 Command and Utilities Reference

License: original prose/illustrations are CC BY 4.0; original reusable code examples are GPL-2.0-or-later. Third-party material retains its own terms. See [licensing and example boundaries](../LICENSING.md).

This edition describes BetterCP/M 1.1 for patched cpmsim, TRS-80 Model 4 and the 64 KiB Model II under trs80gp 2.5.8. Use matching System and Utilities downloads from the same release. Package identity and exact source/image hashes come from RELEASE.json and the release index. The prior 1.0 and 1.0.1 downloads and locks remain unchanged. See the [1.1 scope](../releases/1.1-SCOPE-AND-ACCEPTANCE.md) and [platform boundaries](../platform/SUPPORT-1.1.md); engineering receipts are not acceptance of differently hashed final media.

The normal combined arrangement is A: System, B: primary Utilities, C: Companion Utilities, D: work. Use writable copies of images. Each target has separate System and Utilities downloads; Model II uses BCM2SS IMDs. The [distribution inventory](../../metadata/distribution.json), target build reports and RELEASE.json define available programs, not a development build directory. Qualification is emulator-based; physical hardware is unverified.

<a id="notation"></a>

## 1.1 operating profile

The unloaded complete-record COM limit is 57,344 bytes on cpmsim and Model II. Model 4 retains a 54,272-byte exception because of its keyboard/video reservation. Optional RSXs consume TPA while loaded; complete unload restores the unloaded limit. Read STAT MEM and the current page-zero gateway boundary instead of assuming a hard-coded size. The first RSX also incurs 1,024 bytes of general manager overhead. TCAP full-path accounting includes the renderer, personality, facts, descriptors, cache/alignment, caller helper, shared BIOS state and call/stack allowances: at most 1,280 bytes for ADM3A/VT52 and 1,792 for ANSI; there is no additional permanent display reservation.

BetterCP/M 1.1 supplies integrated ADM3A, VT52 and ANSI personality/renderers implementing the independently versioned TCAP 2.0 direct API. Load one with `RSX LOAD ANSI`, unload it with `RSX UNLOAD ANSI`, and rediscover services after every layout mutation. No standalone screen backend is required by these integrated modules. Model 4 startup selects ADM3A; cpmsim and Model II start with the basic console. Separate ANSISCRN, M4SCRN and M2SCRN modules remain available to clients of SCRN/SCX, such as TED and DUMP paging. TYPE/TED/HELP have not been migrated to TCAP 2.0, and HELP is not shipped. TYPE, TED and HELP are examples, not the complete affected-utility set; see the [full impact audit](../engineering/TCAP-Utility-Impact-Audit.md). The abandoned, unreleased TCAP 1.0/template designs are historical, not compatibility modes. The supported protocols are fixed 80x24 seven-bit paths, not arbitrary host geometry. See the [direct ABI and caller helper contract](../engineering/TCAP-Direct-ABI.md).

For BetterCP/M 1.1.1, unqualified transient commands always search the current drive/user first. Numeric PATH supplies up to six ordered additional drive/user entries, default `$$: A0:`. Z-System syntax uses `$$` for the current DU, `$0` for user 0 on the current drive, and `A$` for the current user on drive A. A trailing colon is optional; `.` is no longer a PATH entry. Double literal dollars in SUBMIT source files. Use `PATH /A DU:` or `/ADD DU:` to append one entry, and `PATH /D DU:` or `/DEL DU:` to remove one. Duplicate additions, missing deletions and deletion of the final entry are rejected without changing the list. Use `PATH /H`, `/HELP` or `/VER`; `A0:PATH /DEFAULT` recovers the default. PATH is volatile: use the existing startup script to apply a preferred list after cold boot. Named directories and scripting are outside 1.1.

## Reading the entries

Each entry has Description, General Form, Quick Reference, Detailed Reference, Examples, Errors/Troubleshooting and See Also. General Form uses placeholders; Quick Reference contains invocations to type after substituting your actual files. Examples can change or erase work files when the command's purpose is mutation. Inspect the location and keep a copy first.

Square brackets in a grammar normally mean optional text; bracketed DU selectors, attribute expressions and historical tool options can be literal syntax. Read the entry before interpreting brackets. Ellipses mean repetition. A command prompt such as `A0>` is shown for context and is not typed. Ctrl-C means a control key; on the original Model 4, BREAK supplies ETX for these uses. A numeric convention belongs to the command: memory addresses and debugger values are hexadecimal; user numbers and many sizes/counts are decimal.

Unqualified transient programs are searched in the current drive/user, then A0. Explicitly qualified program names restrict lookup to that location. A program found in A0 normally runs with the original working DU retained. Its file operands have their own location rules: `B0:DUMP D3:IMAGE.COM` locates the program in B0 and the input in D3. Do not infer operand defaults from the program location.

An ordinary name is offered to built-in CCP commands and configured CPXs before transient lookup. `:DIR` or `.DIR` explicitly requests DIR.COM. There is no general automatic handoff from an unsupported resident option to a transient. Resident and transient entries are independently usable and cross-linked. RCP supplies resident DIR, ERA, REN, TYPE, COPY, MOVE, USER, CLS and VER. GET, GO, JUMP, PEEK/P, POKE and SAVE are built into the CCP. Only the supplied transient files are available without separately preparing other components.

<a id="query-conventions"></a>

## Help and identities

BetterCP/M-owned utilities follow their documented query rules: exact `/H` or `/HELP` requests help and takes precedence over `/VER`; query recognition generally ignores other operating arguments without opening files. Apparent query tokens inside PIP bracket strings or SEARCH quoted patterns remain literal data. Longer tokens such as `/HELPER` are not help. Read the individual entry for exceptions and supported forms.

`VER` identifies the running OS; `VER /V` reports subsystem detail; `:VER /BANNER` selects the transient startup banner. `:DIR /VER` identifies DIR.COM rather than resident DIR. Utility, module, subsystem, API and distribution versions are independent. ZSM4 and LINK retain their original command interfaces and do not acquire BetterCP/M `/HELP` or `/VER`.

Current main may describe development work beyond the lock. In particular, this reference uses FDB 1.0 (001) with its matching viewer, not development FDB 1.01 (002-dev). Optional 104/105 adapters and 56K fullram/checked profiles remain deferred. P2DOS is supplied but optional to load; neither startup script loads a clock provider or P2DOS.

The file-specification chapter and shared messages follow the command sections. A shared grammar is available only where a command accepts it. All references to engineering reports retain their recorded version/platform scope; a historical component result is not new release-wide qualification.


## Contents

- [Files, directories, and transfers](#files-directories-and-transfers)
  - [COPY — Resident](#copy-resident)
  - [COPY — Transient](#copy-transient)
  - [DIR — Resident](#dir-resident)
  - [DIR — Transient](#dir-transient)
  - [ERA — Resident](#era-resident)
  - [ERA — Transient](#era-transient)
  - [MOVE — Resident](#move-resident)
  - [PIP](#pip)
  - [REN — Resident](#ren-resident)
  - [REN — Transient](#ren-transient)
  - [SEARCH](#search)
  - [TYPE — Resident](#type-resident)
  - [TYPE — Transient](#type-transient)
- [Inspection, comparison, and verification](#inspection-comparison-and-verification)
  - [COMPARE](#compare)
  - [CRCKSUM](#crcksum)
  - [DUMP](#dump)
  - [MD5SUM](#md5sum)
  - [PATCH](#patch)
  - [STAT](#stat)
- [Command environment and execution](#command-environment-and-execution)
  - [BYE](#bye)
  - [CLS — Resident](#cls-resident)
  - [CLS — Transient](#cls-transient)
  - [GET](#get)
  - [GO](#go)
  - [JUMP](#jump)
  - [PEEK](#peek)
  - [POKE](#poke)
  - [SAVE](#save)
  - [USER — Resident](#user-resident)
  - [VER — Resident](#ver-resident)
  - [VER — Transient](#ver-transient)
- [Configuration, disks, and installation](#configuration-disks-and-installation)
  - [CONFIG](#config)
  - [DUP](#dup)
  - [FDB](#fdb)
  - [SYSGEN](#sysgen)
- [Batch processing and extensions](#batch-processing-and-extensions)
  - [CPX](#cpx)
  - [RSX](#rsx)
  - [SUBMIT](#submit)
  - [XSUB](#xsub)
- [Date and time](#date-and-time)
  - [TIME](#time)
- [Editing and development tools](#editing-and-development-tools)
  - [DASM](#dasm)
  - [DDT](#ddt)
  - [DLINK](#dlink)
  - [DSYM](#dsym)
  - [ED](#ed)
  - [LINK](#link)
  - [TED](#ted)
  - [ZSM4](#zsm4)
- [Archives and compression](#archives-and-compression)
  - [CR](#cr)
  - [LZH](#lzh)
  - [NOAH](#noah)
  - [SQ](#sq)
  - [UNCR](#uncr)
  - [UNLZH](#unlzh)
  - [USQ](#usq)
- [Platform tools and diagnostics](#platform-tools-and-diagnostics)
  - [ADMTST](#admtst)
  - [ANSITST](#ansitst)
  - [MOUNT](#mount)
  - [R](#r)
  - [VT52TST](#vt52tst)
  - [W](#w)

<a id="files-directories-and-transfers"></a>

## Files, directories, and transfers


<a id="copy-resident"></a>

### COPY — Resident

#### Description

Copies one or more files to another filename, drive, or user area. Provided by the supplied A0:RCP.CPX. It is available at the command prompt while RCP is loaded.

#### General Form

```text
COPY source destination
COPY destination=source
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Copy and retain the source | `COPY A0:README.TXT D0:` |

#### Detailed Reference


##### Resident COPY

Resident COPY accepts two equivalent command forms:

```text
COPY source destination
COPY destination=source
```

For example:

```text
A0>COPY README.TXT README.BAK
A0>COPY README.BAK=README.TXT
```

Both commands create `README.BAK` from `README.TXT`.

You can also copy files between drives:

```text
A0>COPY README.TXT B:
```

This copies `README.TXT` to drive B, retaining its original filename.

To copy a file into another user area:

```text
A0>COPY A3:REPORT.TXT B5:
```

The destination file is created on drive B, user area 5.


##### Copying Several Files

COPY accepts wildcard file specifications.

For example:

```text
A0>COPY *.ASM B:
```

copies the matching assembly-language source files to drive B.

BetterCP/M also supports extended drive/user selectors:

```text
A0>COPY B[-]:*.DOC C3:
```

This selects `.DOC` files across all user areas on drive B and copies them to drive C, user area 3.

You can combine several locations:

```text
A0>COPY [A0,B[5-7],C3]:*.COM D3:
```

The destination must identify a single drive/user area.

When several source files would produce the same destination filename, COPY rejects the conflicting selection rather than silently replacing one file with another.


##### Selecting Files by Attribute

Resident COPY supports file-attribute expressions.

For example:

```text
A0>COPY B[-]:*.DOC[$RW+!$SYS] C4:
```

This selects writable, non-system `.DOC` files from drive B's user areas.

Attribute expressions use the same conventions described in [Chapter 4](Users-Guide.md#chapter-4) and [DIR RESIDENT](#dir-resident).

They determine which files are selected; they do not automatically change the attributes of the source files.


##### Existing Destination Files

Resident COPY normally refuses to replace an existing destination file.

For example, if `B:README.TXT` already exists, an ordinary copy to that name will not silently overwrite it.

Resident COPY provides `/O` to permit replacement of existing writable destination files:

```text
A0>COPY README.TXT B: /O
```

Read-only destination files remain protected.

The option does not permit a copy operation to overwrite one of its own selected source files.

COPY cannot roll back a replacement: after the old writable target is deleted, a later failure may leave neither the old target nor a complete replacement. Preserve a separate copy of an important existing destination before using `/O`. COPY preserves the source file; it does not restore the old destination.


##### Copying to a New Filename

When copying a single file, you can specify a different destination name:

```text
A0>COPY REPORT.TXT B:REPORT.BAK
```

This creates `REPORT.BAK` on drive B.

For multiple-file selections, resident COPY retains the source filenames when the destination specifies only a drive/user area.

Wildcard destination templates are provided by the transient COPY utility.

#### Examples

```text
COPY A0:README.TXT D0:
```

Copy and retain the source. Substitute the locations and filenames appropriate to your session.

#### Errors/Troubleshooting

Resident COPY has no /B batch option and does not automatically hand off to COPY.COM. Use `:COPY` for transient options. It does not replace an existing destination.

#### See Also

[COPY TRANSIENT](#copy-transient) · [file specifications](#file-specifications)


<a id="copy-transient"></a>

### COPY — Transient

#### Description

Copies one or more files to another filename, drive, or user area. COPY.COM is supplied in user 0 on both System disks. Use :COPY or .COPY to bypass resident dispatch.

#### General Form

```text
COPY [global-options] source[source-qualifiers] destination[destination-qualifiers] [global-options]
COPY [global-options] destination[destination-qualifiers]=source[source-qualifiers] [global-options]
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Copy with verification | `:COPY A0:README.TXT D0: /V` |
| Use batch operation | `:COPY B3:*.ASM D0: /B` |

#### Detailed Reference


##### Transient COPY.COM

The transient utility provides additional file-copying capabilities.

Invoke it explicitly:

```text
A0>:COPY
```

or:

```text
A0>.COPY
```

The general command forms remain:

```text
COPY source destination
COPY destination=source
```

However, COPY.COM supports additional source-selection, destination-naming, and file-management options.


##### COPY.COM Options

| Option | Description |
|---|---|
| `/O` | Replace existing writable destination files |
| `/S` | Skip existing writable destination files |
| `/B` | Operate without file-collision prompts |
| `/V` | Verify copied files by reading and comparing their contents |
| `/BACKUP` | Clear the archive attribute after successful backup copying |
| `/HELP` | Display the full quick reference without copying files |
| `/VER` | Display utility identification without copying files |

The `/O` and `/S` options are mutually exclusive.

The `/B` and `/V` options can be combined with either.


##### Overwriting and Skipping Files

By default, transient COPY requests instructions when an existing writable destination file would be replaced.

The available responses include:

| Response | Meaning |
|---|---|
| Y | Replace this file |
| N | Skip this file |
| O | Replace this and subsequent writable collisions |
| S | Skip this and subsequent writable collisions |
| R | Supply a new destination filename |
| ? | Display help |

The O and S responses apply only to the current COPY operation.

They do not permanently change COPY's behavior.

Read-only destination files remain protected.


##### Renaming a Destination During Copying

If an existing destination file would be overwritten, the R response allows you to supply a different filename.

For example, suppose you're copying `REPORT.TXT` to drive B, but a file with that name already exists.

At the collision prompt, enter `R`.

COPY asks for a new name:

```text
New Name:
```

You might enter:

```text
REPORT2.TXT
```

COPY then uses that filename in the same destination drive/user area.

The replacement name must be an exact CP/M filename, without wildcards or a drive/user qualification.

If the new name also exists, COPY applies its normal collision handling to that name.


##### Batch-Oriented Copying

The `/B` option is intended for operations that should not stop for file-collision prompts.

For example:

```text
A0>:COPY B1:*.DAT C3: /B
```

If a writable destination already exists, COPY reports `FILE EXISTS` for that file and continues with the remaining files.

It does not automatically overwrite or skip the collision as a successful operation.

To specify the desired policy, combine `/B` with `/O` or `/S`.

To overwrite existing writable destinations:

```text
A0>:COPY B1:*.DAT C3: /B /O
```

To skip existing destinations:

```text
A0>:COPY B1:*.DAT C3: /B /S
```

Read-only destinations remain protected in both cases.

With `/O`, replacing a writable target can delete the old file before the new copy is complete. A later failure or abort does not restore it. `/V` detects verification failures but provides no rollback; preserve important existing destinations separately first.

The `/B` option is useful in SUBMIT files, but it applies only to COPY. It does not make other commands in the batch noninteractive.


##### Verifying Copied Files

Use `/V` to request verification:

```text
A0>:COPY REPORT.TXT B: /V
```

After copying the file, COPY reopens the source and destination and compares their contents.

A successful verification provides additional confidence that the destination contains the same data as the source.

If verification fails, COPY reports the problem and provides the appropriate recovery choices.

With `/B`, a failed copy or verification does not stop for an interactive retry prompt.

An incomplete destination is removed when possible, and COPY continues according to its error-handling rules.

For important backups, `/V` is recommended.


##### Wildcard Destination Templates

Transient COPY supports wildcard templates in destination filenames.

For example:

```text
A0>:COPY C3:*.DOC=A4:*.COM
```

This copies matching `.COM` files from A4 to C3, changing their file type to `.DOC`.

A more selective template might be:

```text
A0>:COPY C3:X?*.BAK=A4:FOOBAR.COM
```

This creates `XOOBAR.BAK`.

The destination template uses literal characters to replace source positions, question marks to retain corresponding characters, and a terminal asterisk to retain the remainder of a filename field.

The command validates the resulting destination names before copying.


##### Copying Files from Several User Areas

Transient COPY supports extended source selectors.

For example:

```text
A0>:COPY [A[-],B[-],C[-]]:*.COM D0:
```

This selects `.COM` files from all user areas on drives A, B, and C and copies them to D0.

The destination must still identify one drive/user area.

COPY checks the combined selection before beginning.

If different source files would produce the same destination filename, the operation is rejected.

Transient COPY.COM supports a maximum of 64 matched source files in a single invocation.

Larger selections must be divided into smaller operations.

If a selection exceeds the limit, COPY reports `COPY BATCH TOO LARGE` and does not begin writing.

Source files can also be selected by attribute. For example:

```text
A0>:COPY B[-]:*.COM[$ARC] D0:
```

This selects archive-marked `.COM` files using the attribute-expression conventions described under DIR.


##### Destination Attributes

Transient COPY allows destination attributes to be specified explicitly.

For example:

```text
A0>:COPY A0:*.COM D0:[$RW,!$ARC]
```

This requests writable destination copies with the archive attribute cleared.

Attributes not explicitly changed are preserved.

The destination attribute expression is different from a source-selection expression: it specifies the attributes to assign to completed destination files.

It does not override protection on an existing read-only destination.


##### Backup Operations

The `/BACKUP` option supports workflows using CP/M's archive attribute.

For example:

```text
A0>:COPY /V /BACKUP B[-]:*.DOC[$ARC] D0:
```

This selects `.DOC` files marked with the archive attribute, copies them to D0, verifies the copies, and clears the archive attribute on both source and destination after successful completion.

Files that are skipped, fail to copy, or are interrupted retain their source archive status.

The `/BACKUP` option does not automatically select archive-marked files. The `[$ARC]` expression performs that selection.

Similarly, `/BACKUP` does not automatically enable verification. Include `/V` when verification is desired.

**The archive attribute should not be assumed to identify every file changed since the last backup unless the software maintaining those files updates the attribute appropriately.**


##### Completion Information

Transient COPY reports successful copies and their allocated sizes.

For example:

```text
B1:FOO.COM -> D0:FOO.COM [2K]
```

For multiple files, it also reports totals for copied, skipped, and failed files.


#### Examples

Copy a file:

```text
A0>COPY README.TXT B:
```

Copy a file under another name:

```text
A0>COPY REPORT.TXT B:REPORT.BAK
```

Copy all assembly-language source files:

```text
A0>COPY *.ASM B:
```

Copy files across several user areas:

```text
A0>COPY B[-]:*.DOC C3:
```

Copy and verify:

```text
A0>:COPY /V *.COM B:
```

Copy without overwrite prompts, replacing existing writable files:

```text
A0>:COPY /B /O *.DAT B:
```

Back up archive-marked files:

```text
A0>:COPY /V /BACKUP B[-]:*.DOC[$ARC] D0:
```

Source selectors may identify multiple DUs; the destination identifies one DU. Attribute expressions use $RO, $RW, $SYS, $DIR and $ARC with ! (NOT), + (AND) and comma (OR). Operand qualifiers and free-standing options have different scopes. See [File specifications](#file-specifications).

#### Errors/Troubleshooting

##### Copy Errors and Recovery

COPY reports errors such as missing source files, unavailable destinations, insufficient disk space, read/write failures, and verification failures.

The transient utility attempts to remove incomplete destination files when an operation fails.

That cleanup does not restore an overwritten file. If replacement had already started, failure may leave neither the old target nor a complete replacement, even with `/V`. The source remains available, but an important old destination needs its own separate backup before `/O`.

If that cleanup cannot be completed, COPY reports the problem and stops rather than leaving an incomplete file without warning.

Previously completed copies remain available.


#### See Also

[COPY RESIDENT](#copy-resident) · [file specifications](#file-specifications)


<a id="dir-resident"></a>

### DIR — Resident

#### Description

Displays files in the current or a specified drive and user area. Provided by the supplied A0:RCP.CPX. It is available at the command prompt while RCP is loaded.

#### General Form

```text
DIR [filespec]
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| List the current location | `DIR` |
| Select one DU | `DIR B3:*.ASM` |

#### Detailed Reference


##### Resident DIR

The resident command accepts:

```text
DIR
DIR filespec
DIR DU:
DIR DU:filespec
```

For example:

```text
A0>DIR
A0>DIR *.COM
A0>DIR B:
A0>DIR B3:*.ASM
```

Without arguments, DIR displays the files in the current drive and user area.

A file specification restricts the listing to matching files. Wildcards may be used to select groups of files.

BetterCP/M also supports extended drive/user selectors:

```text
A0>DIR B[-]:*.COM
A0>DIR B[3-5]:*.ASM
A0>DIR [A0,B3]:*.DOC
```

Here, `B[-]:` selects all user areas on drive B, while `B[3-5]:` selects user areas 3 through 5.

The resident command displays each selected drive/user area separately and restores the original drive and user area when finished.

By default, system files are omitted.


##### Selecting Files by Attribute

DIR supports file-attribute expressions.

For example:

```text
A0>DIR *.COM[$ARC]
A0>DIR *.DOC[$RO]
A0>DIR B[-]:*.COM[$ARC+!$SYS]
```

The available attribute names are:

| Attribute | Meaning |
|---|---|
| `$RO` | Read-only |
| `$RW` | Writable |
| `$SYS` | System |
| `$DIR` | Not marked as a system file |
| `$ARC` | Archive |

Attribute expressions use `!` for NOT, `+` for AND, and a comma for OR.

For example:

```text
[$ARC+!$SYS]
```

selects files marked ARC but not SYS.

An explicit attribute expression replaces DIR's normal suppression of system files. A system file satisfying the expression can therefore appear in the listing.

Attribute selection does not change file attributes.

#### Examples

```text
DIR
```

List the current location. Substitute the locations and filenames appropriate to your session.

#### Errors/Troubleshooting

Resident DIR has no /WHEREIS, sorting, size-column or paging mode. A request for /WHEREIS reports `DIR: Use :DIR.`; invoke the transient explicitly.

#### See Also

[DIR TRANSIENT](#dir-transient) · [file specifications](#file-specifications)


<a id="dir-transient"></a>

### DIR — Transient

#### Description

Displays files in the current or a specified drive and user area. DIR.COM is supplied in user 0 on both System disks. Use :DIR or .DIR to bypass resident dispatch.

#### General Form

```text
DIR [options] [location:filespec[attributes]]
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Show a paged listing | `:DIR /P` |
| Find a program | `:DIR /WHEREIS ED.COM` |

#### Detailed Reference


##### Transient DIR.COM

The transient DIR utility provides additional display and file-selection options.

Invoke it explicitly with:

```text
A0>:DIR
```

or:

```text
A0>.DIR
```

Both forms bypass the resident command.

The general syntax is:

```text
DIR [options] [location:filespec[attribute-expression]]
```

The transient utility supports the same extended drive/user selectors and attribute expressions as resident DIR.

It also provides sorting, file sizes, attribute display, paging, and directory summaries.


##### DIR.COM Options

| Option | Description |
|---|---|
| `/WHEREIS` | Locate matching files across drives and user areas; see below |
| `/A` | Display file attributes |
| `/P` | Pause after each screenful |
| `/Z` or `/Z=K` | Display allocated space in kilobytes |
| `/Z=S` | Display allocated 128-byte records |
| `/Z=E` | Display directory entries used |
| `/C=1` | One-column display |
| `/C=2` | Two-column display |
| `/C=4` | Four-column display |
| `/S=N` | Sort by filename |
| `/S=T` | Sort by file type |
| `/S=Z` | Sort by allocated size |
| `/S=U` | Preserve directory order |

Sorting options `/S=N`, `/S=T`, and `/S=Z` may be followed by `+` for ascending or `-` for descending order.

For example:

```text
A0>:DIR /S=N
A0>:DIR /S=Z-
A0>:DIR /S=T+ *.COM
```

The first sorts by filename, the second displays the largest files first, and the third sorts matching files by file type.

`/S=U` preserves the disk's directory-search order and does not accept a direction suffix.

Name-ascending order is the default.


##### Locating Files with `/WHEREIS`

Use transient DIR to find every location containing a matching filename:

```text
A0>:DIR /WHEREIS ED.COM
```

`/WHEREIS` requires exactly one filespec. It searches directory names, not file contents, and does not change files or attributes. Wildcards and attribute expressions are supported.

A completely unqualified filespec searches all configured accessible drives and users 0 through 31. Configured drives may still have missing or unreadable media. An explicit drive/user selector restricts the search:

```text
A0>:DIR /WHEREIS B:ED.COM
A0>:DIR /WHEREIS B[-]:ED.COM
A0>:DIR /WHEREIS [A0,B[3-5]]:*.COM[$SYS]
```

`B:` uses the user area that was current when the command started. `B[-]:` searches every user area on B. The last example searches only A0 and B users 3–5 for system `.COM` files.

Unlike ordinary DIR, `/WHEREIS` includes SYS files by default. An attribute expression can restrict the results; `[$DIR]`, for example, selects only files without SYS.

Each logical file appears once per location, even if it occupies several directory extents. Results use `DU:FILENAME` form, such as `B3:ED.COM`, followed by a match count. Drives and users are visited in ascending order, with native directory order within each location. Even an exact filename search reports all matches in the selected scope.

With no matches, DIR reports `DIR: No matches found.`. Recoverable unavailable-drive or directory-read errors are reported and the search continues elsewhere when safe. A skipped failure or directory-capacity limit adds `Search incomplete.`; a zero-match result in that case does not establish that the file is absent everywhere.

This mode has no ordinary size, attribute-column, free-space, sorting, column-layout, or paging display. Do not combine `/WHEREIS` with `/A`, `/P`, `/Z`, `/C=`, `/S=`, or `/VER`; these combinations are rejected. Attribute predicates in the filespec remain valid. No `/B`, `/Y`, or `/Q` option is needed for unattended searches.

Ctrl-C during console output follows the normal warm-boot cancellation behavior. On normal completion or recoverable errors, DIR preserves the caller's drive/user context; fatal system faults can end the search. Resident DIR does not implement this mode and reports `DIR: Use :DIR.`; use `:DIR` as shown above.


##### Displaying File Sizes

Transient DIR displays the allocated space occupied by each file.

The default unit is kilobytes.

To display allocated 128-byte records:

```text
A0>:DIR /Z=S
```

To display the number of physical directory entries occupied by each file:

```text
A0>:DIR /Z=E
```

These values describe allocated storage or directory usage, not necessarily the exact logical length of the file.


##### Displaying Attributes

Use `/A` to include a three-character attribute field:

```text
A0>:DIR /A
```

The field contains the SYS, read-only, and ARC attributes, in that order.

For example:

| Display | Meaning |
|---|---|
| `---` | No attributes set |
| `-R-` | Read-only |
| `S--` | System |
| `--A` | Archive |
| `S-A` | System and archive |

The `/A` option displays attributes but does not select files based on them.

To select files by attribute, use an attribute expression.


##### Paging and Columns

For long listings, use:

```text
A0>:DIR /P
```

DIR pauses after each screenful.

Press Space or Return to continue, or Ctrl-C to stop the listing.

The transient utility normally chooses a suitable column layout automatically.

You can request a particular number of columns:

```text
A0>:DIR /C=1
```

A one-column display is particularly convenient when file sizes and attributes are shown.

If the requested number of columns cannot fit, DIR reports an error rather than silently changing the layout.


##### Directory Summaries

Transient DIR reports file counts and allocated-space totals.

When several user areas are selected, each is listed separately.

Each DU keeps its heading above the files. File sizes are right-aligned within their columns. Each listing ends with a combined summary, for example:

```text
---- 30 FILES, 184K TOTAL, 146K FREE ----
```

Free space is included for each selected user area. An empty listing uses two rows: `D0: NO FILE`, then a footer such as `---- 796K FREE ----`. Free space always uses KiB, regardless of the selected file-size unit.


#### Examples

Display all `.COM` files in user area 3 on drive B:

```text
A0>:DIR B3:*.COM
```

Display archived files, excluding system files:

```text
A0>:DIR *.*[$ARC+!$SYS]
```

Display the largest archived `.COM` files first, including their attributes:

```text
A0>:DIR /A /S=Z- B3:*.COM[$ARC]
```

Display a paged, one-column listing:

```text
A0>:DIR /C=1 /P
```

For ordinary directory listings, resident DIR is usually sufficient. Use transient DIR when you need sorting, sizes, paging, or more detailed information.

DIR supports file-attribute expressions.

For example:

```text
A0>DIR *.COM[$ARC]
A0>DIR *.DOC[$RO]
A0>DIR B[-]:*.COM[$ARC+!$SYS]
```

The available attribute names are:

| Attribute | Meaning |
|---|---|
| `$RO` | Read-only |
| `$RW` | Writable |
| `$SYS` | System |
| `$DIR` | Not marked as a system file |
| `$ARC` | Archive |

Attribute expressions use `!` for NOT, `+` for AND, and a comma for OR.

For example:

```text
[$ARC+!$SYS]
```

selects files marked ARC but not SYS.

An explicit attribute expression replaces DIR's normal suppression of system files. A system file satisfying the expression can therefore appear in the listing.

Attribute selection does not change file attributes.

#### Errors/Troubleshooting

Check the operand grammar and the selected drive/user area. For disk failures, preserve the source and any reported recovery files before retrying. See the [shared system messages](#system-messages) for command lookup, media, configuration and extension diagnostics.

#### See Also

[DIR RESIDENT](#dir-resident) · [file specifications](#file-specifications)


<a id="era-resident"></a>

### ERA — Resident

#### Description

Removes one or more files from disk. Provided by the supplied A0:RCP.CPX. It is available at the command prompt while RCP is loaded.

#### General Form

```text
ERA filespec[attributes]
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Erase an exact file | `ERA D0:OLD.TXT` |
| Select backup files | `ERA D0:*.BAK` |

#### Detailed Reference


##### Resident ERA

The resident command accepts file specifications and BetterCP/M's extended drive/user selectors.

For example:

```text
A0>ERA OLD.TXT
A0>ERA *.BAK
A0>ERA B3:*.TMP
A0>ERA B[-]:*.BAK
```

It also accepts attribute expressions:

```text
A0>ERA B[-]:*.DOC[$ARC]
```

The complete selection is checked before any files are erased.

Resident ERA protects read-only and system files. These remain protected even when an attribute expression explicitly selects them.

When an all-wildcard specification is used, ERA requests confirmation:

```text
ALL (Y/N)?
```

Only `Y` proceeds.

Resident ERA does not provide the extended confirmation, reporting, and destructive-erasure options available in the transient utility.

#### Examples

```text
ERA D0:OLD.TXT
```

Erase an exact file. Substitute the locations and filenames appropriate to your session.

#### Errors/Troubleshooting

Resident ERA protects read-only and system files, even when an attribute expression selects them. Only Y confirms an all-wildcard erase.

#### See Also

[ERA TRANSIENT](#era-transient) · [file specifications](#file-specifications)


<a id="era-transient"></a>

### ERA — Transient

#### Description

Removes one or more files from disk. ERA.COM is supplied in user 0 on both System disks. Use :ERA or .ERA to bypass resident dispatch.

#### General Form

```text
ERA [options] filespec[attributes]
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Review selected files | `:ERA D0:*.BAK` |
| Confirm each file | `:ERA /C D0:*.BAK` |

#### Detailed Reference


##### Transient ERA.COM

Invoke the transient utility explicitly:

```text
A0>:ERA
```

Its general syntax is:

```text
ERA [options] filespec[attributes]
```

For example:

```text
A0>:ERA OLD.DOC
A0>:ERA *.BAK
A0>:ERA B[-]:*.DOC
```

Unlike the resident command, transient ERA normally displays the files selected for deletion and requests confirmation.

For a single file, it may ask:

```text
TOM.DOC - Erase? Y/N
```

For multiple files, it displays a list of the selected files and a summary before asking whether to proceed.


##### ERA.COM Options

The documented erase controls are:

| Option | Description |
|---|---|
| `/Y` | Assume yes for ordinary confirmations |
| `/Q` | Suppress ordinary informational output |
| `/C` | Confirm each file |
| `/R` | Authorize erasure of selected read-only files |
| `/D` | Destructive erase |

These options affect how files are selected, confirmed, and removed.

Some options are intended for unattended operations, while others provide additional safeguards.


##### Confirmation

By default, transient ERA asks before deleting files.

For example:

```text
A0>:ERA *.BAK
```

displays the selected files and requests confirmation.

To request confirmation for each file:

```text
A0>:ERA /C *.BAK
```

ERA first obtains the ordinary group confirmation and then asks about individual files.

To suppress ordinary confirmation prompts:

```text
A0>:ERA /Y *.BAK
```

This is useful in SUBMIT files, but should be used carefully.


##### Read-Only and System Files

Transient ERA handles protected files in three stages:

1. **Selection:** the filespec and attribute expression must match the file.
2. **Admission:** every protected attribute present (SYS and RO) must be explicitly admitted by the same OR branch that matches the file.
3. **Read-only authorization:** an admitted RO file still needs `/R` or an interactive read-only confirmation before erasure.

A comma separates OR branches; `+` joins conditions within one branch. Positive `$SYS` and `$RO` admit their respective protected attributes. `!$DIR` and `!$RW` are equivalent admissions; additional negations follow the normal Boolean rules.

| Expression | Selection and protection admission |
|---|---|
| `[$SYS+$RO]` | Selects and admits both protected attributes in one matching branch |
| `[$SYS,$RO]` | Matches the file, but does not admit it: neither branch admits both attributes |
| `[$SYS+$RO,$ARC]` | Admits a SYS+RO file through the first branch; a SYS+ARC file without RO matches only the ARC branch and remains protected |

For example, to select and authorize erasure of SYS+RO `.DOC` files:

```text
A0>:ERA /R *.DOC[$SYS+$RO]
```

Without `/R`, an admitted read-only file receives a separate read-only confirmation. With `/Y` but without `/R`, ERA skips read-only files without asking. `/R` does not broaden selection or admission and does not admit SYS files by itself. `/Y` suppresses confirmations; it does not bypass these protection rules.

For read-only files without SYS, the familiar form remains:

```text
A0>:ERA /R *.DOC[$RO]
```

A file that also carries SYS needs SYS admitted in the same matching branch, as shown above. Check the selection carefully before authorizing an erase.


##### Quiet Operation

Use `/Q` to suppress ordinary informational output:

```text
A0>:ERA /Q *.BAK
```

This does not suppress required confirmation.

For unattended operation, combine it with `/Y`:

```text
A0>:ERA /Y /Q *.BAK
```


##### Destructive Erase

The transient ERA utility provides a destructive-erasure option:

```text
A0>:ERA /D SECRET.DAT
```

This attempts to overwrite the file's allocated data with zeroes before removing its directory information.

Destructive erase is intended to make recovery of the selected file's contents more difficult than ordinary deletion.

However, **it should not be treated as a guarantee of secure data destruction**.

Some allocation blocks may be shared with other live files. BetterCP/M preserves shared blocks rather than overwriting data belonging to another file.

Hardware characteristics and disk errors can also prevent complete overwriting.

Without `/Y`, destructive erase asks for confirmation even for one exact filename. For multiple files, it uses a destructive-erasure warning and confirmation; `/Q` hides the manifest but does not authorize erasure.

`/Y` suppresses the destructive confirmation as well as ordinary confirmations. Use it only after checking the selection carefully. It does not imply `/R`: selected read-only files are skipped with `/Y` unless `/R` is also supplied. Without `/Y` or `/R`, ERA asks for separate read-only authorization. Neither option broadens the selection or bypasses file-selection protection rules. ERA reports incomplete destructive operations.


##### Error Handling

If an erase operation fails, ERA may offer:

```text
R/S/A/?
```

The responses are:

| Response | Meaning |
|---|---|
| R | Retry |
| S | Skip the file |
| A | Abort the remaining operation |
| ? | Display help |

With `/Y`, ERA does not stop for this recovery prompt. It reports the failed file and continues when safe.


##### Completion Summary

Transient ERA reports the results of the operation.

For example:

```text
12 FILES ERASED, 2 SKIPPED, 1 FAILED, 47K FREED
```

The reported space freed represents allocated disk space released, rather than the exact logical lengths of the deleted files.


#### Examples

Erase a single file:

```text
A0>ERA OLD.TXT
```

Erase backup files in user area 3 on drive B:

```text
A0>ERA B3:*.BAK
```

Erase archived files with individual confirmation:

```text
A0>:ERA /C B[-]:*.DOC[$ARC]
```

Erase selected files without ordinary confirmation:

```text
A0>:ERA /Y *.BAK
```

Destructively erase a file:

```text
A0>:ERA /D SECRET.DAT
```

For ordinary file deletion, resident ERA is usually sufficient. Use transient ERA when you need its additional confirmation, selection, or destructive-erasure facilities.

#### Errors/Troubleshooting

Check the operand grammar and the selected drive/user area. For disk failures, preserve the source and any reported recovery files before retrying. See the [shared system messages](#system-messages) for command lookup, media, configuration and extension diagnostics.

#### See Also

[ERA RESIDENT](#era-resident) · [file specifications](#file-specifications)


<a id="move-resident"></a>

### MOVE — Resident

#### Description

Move files using RCP.CPX. The locked System disks do not supply MOVE.COM. Source deletion follows successful destination creation and close.

#### General Form

```text
MOVE source destination
MOVE destination=source
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Move a file to another user | `MOVE D0:REPORT.TXT D3:` |

#### Detailed Reference

MOVE is available as a resident command in BetterCP/M 1.0.

It provides a convenient way to reorganize files without separately copying them and deleting the originals.

Unlike COPY, MOVE removes the source file after successfully creating the destination.


##### Command Syntax

MOVE accepts two equivalent forms:

```text
MOVE source destination
MOVE destination=source
```

For example:

```text
A0>MOVE README.TXT B:
```

moves `README.TXT` from the current drive and user area to drive B.

You can also write:

```text
A0>MOVE B:README.TXT=README.TXT
```

Both commands have the same effect.


##### Moving Files Between User Areas

BetterCP/M allows files to be moved between user areas.

For example:

```text
A0>MOVE A3:REPORT.TXT B5:
```

moves `REPORT.TXT` from A3 to B5.

The original file is removed only after the destination has been successfully created.

This is particularly useful when reorganizing project files among user areas.


##### Moving Several Files

MOVE accepts wildcard specifications:

```text
A0>MOVE *.BAK B:
```

This moves matching backup files to drive B.

Extended drive/user selectors are also supported:

```text
A0>MOVE B[-]:*.DOC C3:
```

This selects `.DOC` files across all user areas on drive B and moves them to C3.

The destination must identify a single drive/user area.

If multiple source files would produce the same destination filename, MOVE rejects the conflicting selection.


##### Selecting Files by Attribute

MOVE supports BetterCP/M's shared file-selection expressions.

For example:

```text
A0>MOVE B[-]:*.DOC[$RW+!$SYS] C4:
```

This selects writable, non-system `.DOC` files from drive B's user areas.

Read-only source files are protected.

Attribute expressions determine which files are selected; they do not automatically override file protection.


##### Moving a File to a New Name

MOVE can assign a new filename when moving a single file.

For example:

```text
A0>MOVE REPORT.TXT B:REPORT.BAK
```

This moves the file to drive B and renames it `REPORT.BAK`.

The original `REPORT.TXT` is removed after the destination has been successfully written.


##### Existing Destination Files

MOVE does not overwrite existing destination files.

If a destination name already exists, MOVE reports the conflict rather than replacing the file.

Unlike transient COPY, resident MOVE does not provide an overwrite option.

If you need to replace an existing destination, handle that file separately before moving the new one.

Be careful when removing existing files, particularly when working with wildcard specifications.


##### How MOVE Handles Files

MOVE copies the file to its destination and removes the original only after the destination has been successfully written and closed.

This applies even when moving a file within the same drive/user area.

If the destination cannot be created or written successfully, MOVE does not intentionally erase the source.

However, an unexpected failure can interrupt a multi-file move after some files have already been transferred.

Earlier completed moves are not automatically reversed.


##### Moving Several Files Safely

When moving a large group of files, it's wise to check the source and destination directories first.

For example:

```text
A0>DIR B3:*.DOC
A0>DIR C4:*.DOC
```

This allows you to identify possible filename conflicts before moving the files.

You can then enter:

```text
A0>MOVE B3:*.DOC C4:
```

Afterward, examine the destination:

```text
A0>DIR C4:*.DOC
```

If MOVE reported an error, also examine the source to determine which files remain.


##### COPY or MOVE?

COPY and MOVE serve different purposes.

Use **COPY** when you want to create another copy of a file while retaining the original.

Use **MOVE** when you want to relocate a file and no longer need it in its original location.

For important files, copying and verifying them before manually deleting the originals may provide additional reassurance.

MOVE is convenient for routine file organization, but it should not be treated as a substitute for maintaining backups.


#### Examples

Move a file to another drive:

```text
A0>MOVE README.TXT B:
```

Move a file to another user area:

```text
A0>MOVE A3:REPORT.TXT B5:
```

Move a file and change its name:

```text
A0>MOVE REPORT.TXT B:REPORT.BAK
```

Move all backup files:

```text
A0>MOVE *.BAK B:
```

Move selected files from several user areas:

```text
A0>MOVE B[-]:*.DOC C3:
```

Move writable, non-system files:

```text
A0>MOVE B[-]:*.DOC[$RW+!$SYS] C4:
```

#### Errors/Troubleshooting

Existing destinations are refused. A multi-file move is not one atomic transaction. `COPY MADE; SOURCE NOT ERASED` means both copies may remain; inspect them before deleting either.

##### Source Deletion Failures

Occasionally, MOVE may successfully create the destination but be unable to remove the original.

In that case, it reports:

```text
COPY MADE; SOURCE NOT ERASED
```

This means that the destination copy was created, but the source remains in place.

You should examine both files before deciding whether to delete the original manually.


#### See Also

[COPY RESIDENT](#copy-resident) · [COPY TRANSIENT](#copy-transient) · [DIR RESIDENT](#dir-resident)


<a id="pip"></a>

### PIP

#### Description

Transfer files and character streams using BetterCP/M's DRI-compatible Peripheral Interchange Program. PIP.COM is supplied on both System disks. It retains destination-first syntax and historical bracket parameters, adding simple DU locations, expanded source DU selectors and utility queries.

#### General Form

```text
PIP
PIP destination=source[,source...]
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Copy program files | `PIP D:=A:*.COM` |
| Copy from all source users | `PIP A4:=B[-]:*.COM` |
| Copy from selected drives/users | `PIP A4:=[B[1-3],C7]:*.COM[V]` |
| Join text files | `PIP D:ALL.TXT=D:ONE.TXT,D:TWO.TXT` |
| Copy with verification | `PIP D:BACKUP.COM=A:PROGRAM.COM[V]` |

#### Detailed Reference


##### Assignment and interactive use

`PIP destination=source1,source2,...` executes one transfer. `PIP` alone enters a `*` prompt; enter assignments there without the word PIP. An empty command line exits. The historical `_` left arrow is also an assignment alias. Source-first `PIP SOURCE DEST` is not supported.

```text
PIP D:=A:*.COM
PIP D:NEW.ASM=A:OLD.ASM
PIP D:ALL.TXT=D:ONE.TXT,D:TWO.TXT
PIP LST:=D:REPORT.TXT
```

An exact destination filename can rename an exact source while copying. A drive destination with wildcard source retains each matching filename. Concatenation writes sources in the stated order. Distinguish object files from text before applying transformations: ordinary text uses 1Ah as end of text; COM files select object handling automatically. CP/M physical record padding is not a host byte-length field.


##### Expanded source DU selectors

For a file copy into a single destination DU, PIP accepts the shared [D.4 expanded DU grammar](#d4-extended-driveuser-selectors) on its one source operand. Lists, ranges (including descending and open-ended ranges), all-user `[-]`, compound drive/user scopes and inherited locations have the same meaning as in COPY and DIR. Repeated locations are visited once, in drive-major, user-minor order. Drives must be configured; this implementation accepts A–D and users 0–31.

```text
PIP A4:=B[-]:*.COM
PIP A4:=B[1,3,8-10]:*.COM[RV]
PIP A4:=[B[0-3],C7]:*.COM[V]
```

The first copies matching COM files from every user area on B into A4, preserving filenames. `[RV]` after the filename includes system files and verifies each copy; it is distinct from the location brackets before the colon. An exact filename, such as `B[1-3]:README.TXT`, can also select files across users. `[Gn]` is invalid on a selector source, including `[G0]`; put all user selection before the colon.

The destination must use a simple location naming one DU, such as `A4:` or `A:` (the caller's user on A). A selector destination is invalid even when it names only one DU. Expanded source selectors are not accepted for a renamed/exact-file destination, concatenation or device transfers. Those forms retain their historical operand rules.

**Duplicate destination filenames.** PIP enumerates the complete eligible selection before copying. If distinct selected source files have the same 8.3 name and would therefore produce the same destination filename, it rejects the whole selection, identifies both source DUs and names, and reports `No files copied.` For example, selecting both `B0:FOO.COM` and `B7:FOO.COM` produces:

```text
DUPLICATE DESTINATION NAME: B7:FOO.COM conflicts with B0:FOO.COM
No files copied.
```

`[W]` does not bypass this check. Repeating the same DU in a selector does not itself create a conflict. System files excluded without `[R]` do not participate in the selection or its duplicate-name check.

This rule differs from finding a destination that already exists before the command: PIP retains its normal replacement behavior. An existing writable destination is replaced without asking. A read-only destination requires confirmation unless `[W]` is supplied. The original destination remains until its replacement has transferred, optionally verified and closed successfully.

A selector operation accepts at most **64 matched source files**. Duplicate names, too many matches, a selected source that would copy onto itself, a `.$$$` destination-name conflict, unavailable drive letters, unsupported parameters, a read-only destination drive or an existing read-only staging file fail before any transfer-file mutation. Writable staging files follow normal PIP replacement behavior. Ordinary PIP errors still cancel the A0 SUBMIT queue. Preflight does not reserve media or directory contents: keep disks in place and do not change files during the operation. Later I/O failures can leave earlier copies completed; the operation is not a multi-file transaction. A directory search ending without matches cannot distinguish every media failure from an empty location.

##### Locations and bracket parameters

Use `B7:FILE.TXT` for an exact drive/user, `7:FILE.TXT` for a user on the captured drive, and a drive-only name for the caller's user. Explicit DU addressing and a contradictory `[Gn]` on the same source are invalid. Device names are recognized as devices rather than user syntax. PIP does not accept COPY's attribute predicates or backup switches.

Bracket parameters attach to the operand they qualify. Counts follow their historical decimal forms. Important parameters are:

| Parameter | Purpose |
| --- | --- |
| `B` | Block-mode input, for sources requiring buffering before output. |
| `Dn` | Delete characters beyond column n on a line. |
| `E` | Echo transferred input to the console. |
| `F` | Remove form-feed characters. |
| `Gn` | Select source user n, 0–31. |
| `H` | Process Intel HEX input with validation. |
| `I` | Ignore the final Intel HEX termination record as defined by the historical HEX path. |
| `L` / `U` | Translate alphabetic text to lower / upper case. |
| `N` / `N2` | Number output lines using the historical numbering forms. |
| `O` | Object transfer; preserve bytes that are text end markers, subject to the retained source-path exception below. |
| `P` / `Pn` | Paginate using the default / specified page length. |
| `Qstring` / `Sstring` | Stop after / start at a matched string; terminate each string with Ctrl-Z. |
| `R` | Include system files in wildcard selection. |
| `Tn` | Expand tabs at n-column stops. |
| `V` | Verify disk output by rereading the written data. |
| `W` | Permit read-only destination replacement without its ordinary protection question. |
| `Z` | Clear the high bit of transferred characters. |

Quoted query-like text inside bracket S/Q strings is data. PIP retains the DRI O-path distinction. On generic concatenation/device input, O preserves embedded 1Ah and reads to physical EOF. On a single character-transfer path with S/Q, B or case conversion, object mode follows the COM extension rather than O. Thus `PIP DEST.DAT=SOURCE.DAT[OU]` retains text EOF, while `PIP DEST.DAT=SOURCE.DAT[OU],SECOND.DAT` uses object EOF for the first source. O-only direct record copies preserve complete physical records. HEX H/I still terminates at Ctrl-Z. See the [retained dispatch exception](../engineering/PIP%20Specification.md#retained-dri-o-parameter-dispatch-exception).


##### Devices and output publication

Logical `CON:`, `RDR:`, `PUN:` and `LST:` follow configured IOBYTE routing. Physical aliases are platform capabilities: Model 4 supplies CRT console/list routing; patched cpmsim additionally supplies TTY, PTR, PTP and LPT paths. Unsupported user-defined endpoints are not synthesized. Physical aliases temporarily select routing and restore it on ordinary return. BAT input follows RDR and BAT output follows LST.

`NUL:` supplies 40 NUL bytes; `EOF:` supplies 1Ah. `PRN:` is formatted list output with numbering, eight-column tab expansion and 60-line pagination. INP/OUT are the retained patchable custom-device path; modifying those hooks is programming work, not ordinary device configuration.

Disk output uses a same-stem `.$$$` work file and final close/delete/rename sequence. A prior same-stem work file can be removed at setup; preserve recovery work before reusing its stem. Normal PIP attribute behavior follows its DRI baseline rather than COPY's ARC/backup policy. `[R]` controls system-file inclusion; `[W]` controls read-only replacement. Verify the resulting file before discarding a backup.

#### Examples

```text
PIP D:=A:*.COM
```

Copy program files. Substitute the locations and filenames appropriate to your session.

#### Errors/Troubleshooting

Check destination-first assignment, file/device spelling, free blocks and directory entries. A source DU plus contradictory [Gn] is rejected. Unsupported physical devices fail rather than being emulated. A read-only replacement prompts unless [W] applies. Preserve the original and any reported .$$$ work file after I/O or finalization failures; temporary-file use does not guarantee power-loss atomicity. Ordinary PIP errors cancel the authoritative A0 submit queue. Fatal cooked Ctrl-C warm boot may bypass normal cleanup.

#### See Also

[COPY RESIDENT](#copy-resident) · [COPY TRANSIENT](#copy-transient) · [file specifications](#file-specifications)


<a id="ren-resident"></a>

### REN — Resident

#### Description

Changes the names or file types of existing files without changing their contents. Provided by the supplied A0:RCP.CPX. It is available at the command prompt while RCP is loaded.

#### General Form

```text
REN source template
REN template=source
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Rename an exact file | `REN NEW.TXT=D0:OLD.TXT` |

#### Detailed Reference


##### Resident REN

Resident REN accepts two equivalent forms:

```text
REN source template
REN template=source
```

For example:

```text
A0>REN NEW.TXT=OLD.TXT
A0>REN OLD.TXT NEW.TXT
```

Both rename `OLD.TXT` to `NEW.TXT`.

BetterCP/M also supports wildcard rename templates:

```text
A0>REN *.DOC *.TXT
```

This changes the file type of matching `.DOC` files to `.TXT`, retaining their original names.

You can select files in another drive or user area:

```text
A0>REN *.TXT=B3:*.DOC
```

The files remain in `B3:` after being renamed.


##### Renaming Several Files

REN supports BetterCP/M's extended drive/user selectors.

For example:

```text
A0>REN B[-]:*.DOC *.TXT
```

renames matching files across all user areas on drive B.

You can also use attribute expressions:

```text
A0>REN B[-]:*.DOC[$RW] *.TXT
```

This selects writable `.DOC` files.

Read-only and system files are protected by the resident command, even when explicitly selected.


##### Rename Templates

Rename templates determine how the new filename is constructed.

A literal character replaces the corresponding character in the source name. A question mark retains a character from the corresponding position, while a terminal asterisk retains the remainder of that filename field.

For example:

```text
A0>REN X?*.BAK=B3:FOOBAR.DOC
```

produces `XOOBAR.BAK`.

The filename and file type are treated as separate fields.

A template cannot specify another drive or user area. Use COPY or MOVE when you want to change a file's location.


##### Existing Destination Names

REN never overwrites an existing file.

If the requested new name already exists, resident REN stops rather than replacing it.

Any files successfully renamed before the conflict remain renamed.

REN does not automatically undo earlier operations.

#### Examples

```text
REN NEW.TXT=D0:OLD.TXT
```

Rename an exact file. Substitute the locations and filenames appropriate to your session.

#### Errors/Troubleshooting

An existing destination is a conflict. Use a different name or resolve the existing file separately; selection does not override file protection.

#### See Also

[REN TRANSIENT](#ren-transient) · [file specifications](#file-specifications)


<a id="ren-transient"></a>

### REN — Transient

#### Description

Changes the names or file types of existing files without changing their contents. REN.COM is supplied in user 0 on both System disks. Use :REN or .REN to bypass resident dispatch.

#### General Form

```text
REN [options] source template
REN [options] template=source
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Preview a rename | `:REN /DRY D0:OLD.TXT NEW.TXT` |

#### Detailed Reference

##### Selection and templates

REN changes names in their existing drive/user; it does not move files. Both `REN source template` and `REN template=source` are accepted. The template has no drive/user qualifier. Source selectors can span multiple DUs and use attribute predicates. A literal template character replaces that position, `?` retains the corresponding source character, and terminal `*` retains the rest of its filename field. Filename and type are mapped separately.

For example, `:REN X?*.BAK=B3:FOOBAR.DOC` produces B3:XOOBAR.BAK. An existing destination name is never overwritten. Earlier successful renames are not automatically reversed after a later conflict. Predicate selection alone does not authorize protected-file renaming; the transient /P contract below controls it.


##### Transient REN.COM

The transient utility provides additional confirmation, preview, protection, and reporting options.

Invoke it explicitly:

```text
A0>:REN
```

It accepts the same two operand arrangements:

```text
REN source template
REN template=source
```


##### REN.COM Options

| Option | Description |
|---|---|
| `/C` | Confirm each eligible rename |
| `/Y` | Proceed without ordinary confirmation |
| `/N` | Display proposed mappings without renaming |
| `/DRY` | Preview the operation without changing files |
| `/P` | Permit renaming selected protected files |
| `/Q` | Suppress routine successful-operation messages |
| `/QQ` | Suppress most normal output |
| `/VER` | Display version information |


##### Previewing a Rename

When renaming several files, it's often useful to see what will happen before making changes.

Use `/DRY`:

```text
A0>:REN /DRY B[-]:*.DOC *.TXT
```

REN displays the proposed filename changes without modifying the files.

A visible dry run ends with:

```text
Dry run only: no files were renamed.
```

The `/DRY` option takes precedence over options that would otherwise authorize renaming.

This makes it particularly useful when experimenting with wildcard templates.


##### Confirming Renames

Use `/C` to request confirmation for each eligible file:

```text
A0>:REN /C *.DOC *.TXT
```

Use `/Y` when the operation should proceed without ordinary confirmation:

```text
A0>:REN /Y *.DOC *.TXT
```

Neither option overrides file protection.


##### Protected Files

By default, REN skips read-only and system files.

Transient REN provides `/P` to permit renaming explicitly selected protected files.

For example:

```text
A0>:REN /P *.DOC[$RO] *.TXT
```

This selects read-only `.DOC` files and permits their renaming.

The files retain their attributes after the rename.

The `/P` option does not broaden the file selection or override a read-only drive.


##### Name Conflicts

If a destination name already exists, transient REN can offer:

```text
File exists. N/S/A/?
```

The responses are:

| Response | Meaning |
|---|---|
| N | Enter a new name |
| S | Skip this file |
| A | Abort the remaining operation |
| ? | Display help |

A replacement name must be a valid filename without a drive/user qualification.

REN never silently overwrites an existing target.


#### Examples

Rename one file:

```text
A0>REN NEWNAME.TXT=OLDNAME.TXT
```

Change all `.DOC` files to `.TXT`:

```text
A0>REN *.DOC *.TXT
```

Preview renaming across all user areas on drive B:

```text
A0>:REN /DRY B[-]:*.DOC *.TXT
```

Rename selected read-only files:

```text
A0>:REN /P *.DOC[$RO] *.TXT
```

For ordinary renaming, resident REN is sufficient. Use transient REN when you need confirmation controls, previews, or protected-file handling.

#### Errors/Troubleshooting

##### Errors and Completion

If an operation fails, transient REN may offer Retry, Skip, or Abort.

Successful renames are not rolled back when a later operation fails.

On completion, REN reports the results, for example:

```text
12 FILES RENAMED, 2 SKIPPED, 1 FAILED
```


#### See Also

[REN RESIDENT](#ren-resident) · [file specifications](#file-specifications)


<a id="search"></a>

### SEARCH

#### Description

SEARCH.COM is supplied on the primary Utilities disk (normally B0). Search literal text and decoded hexadecimal byte patterns without changing files.

#### General Form

```text
SEARCH [options] "pattern" filespec [options]
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Find literal text | `B0:SEARCH "Error" D0:*.TXT /NOCASE /NOHEX` |

#### Detailed Reference

**SEARCH 1.0 (003)** is included on the locked primary Utilities disk. The component reports below retain their original paired-emulator scope; publication approval remains separate from the software lock.
The [engineering specification](../engineering/SEARCH%20Specification.md)
controls the design.

SEARCH finds literal text and byte sequences in files without changing them.
Use DIR /WHEREIS when you want to locate filenames instead of searching contents.


##### SEARCH syntax and options

```text
SEARCH [options] "pattern" filespec [options]
SEARCH "Error" A0:*.TXT /NOCASE /NOHEX
SEARCH "41 42" B[3-7]:*.COM /NOTEXT /P
SEARCH "4142" [A0,B[-],C[4,7-9]]:*.DAT
```

Put the quoted pattern first, followed by exactly one filespec. Put options before
the pattern or after the filespec. Quotes delimit the pattern; spaces and letter
case inside them are significant. Quoted `/VER` or `/HELP` is search data.
Options and filenames are case-insensitive. Repeating a flag has no extra effect.

| Option | Meaning |
| --- | --- |
| `/NOHEX` | Search only the literal TEXT interpretation. |
| `/NOTEXT` | Search only decoded HEX bytes; the pattern must be valid HEX. |
| `/NOCASE` | Ignore ASCII letter case in TEXT; HEX bytes remain exact. |
| `/P` | Pause result details one page at a time, moving forward only. |
| `/H`, `/HELP` | Display help without searching; takes precedence over `/VER`. |
| `/VER` | Display utility identification without searching. |

By default SEARCH tries **both** interpretations independently. `"4142"` searches
for the four literal characters `4142` and for the two bytes `41h 42h` (`AB`).
`"41 42"` searches for those five literal characters and the same two decoded
bytes. HEX accepts contiguous pairs of hexadecimal digits or pairs separated by
spaces; hex digit case is insignificant. Odd digit counts, `0x` prefixes, `H`
suffixes, commas and incomplete byte pairs are not valid HEX. Invalid HEX is
silently ignored when TEXT is enabled: `"hello"` is an ordinary TEXT search.
With `/NOTEXT`, invalid HEX is an error. `/NOHEX /NOTEXT` is invalid.

TEXT is literal: no regular expressions, content wildcards or backslash escapes.
It is case-sensitive unless `/NOCASE` is supplied. `/NOCASE` folds ASCII letters
only, leaving high-bit bytes unchanged; it has no effect with `/NOTEXT`.
An empty pattern is invalid. Each enabled interpretation is limited to 64 decoded
bytes. The entire command tail, including quotes, filespec and options, must fit
within 127 bytes; consequently a 64-byte HEX pattern cannot fit on the command
line. SEARCH does not silently shorten a pattern.

The locked release preserves command-tail letter case (compatibility
profile difference 0020), while default FCB filenames remain uppercase. SEARCH
therefore receives the original quoted pattern case in this profile. An environment
that uppercases command tails before launching SEARCH cannot recover the original
pattern spelling; in that environment use `/NOCASE` for ASCII text regardless of
case, or `/NOTEXT` with HEX to specify exact bytes. See the
[release conformance record](../engineering/Release-Conformance-2026-11-02.md).
A double quote ends the pattern; no embedded-quote escape is provided. A TAB
inside quotes is literal pattern data; outside quotes it separates arguments.


##### Selecting files for SEARCH

An unqualified filespec searches the caller's current drive and user area.
Filename `*` and `?` patterns use the shared CP/M 8.3 rules. Extended DU selectors
can select several locations:

```text
SEARCH "hello" B7:*.TXT /NOCASE
SEARCH "1A" B[-]:*.* /NOTEXT
SEARCH "Error" [A0,B[3-7],D[-]]:*.LOG /NOHEX
```

`B[-]` means all users 0–31 on B; `B[3-7]` means users 3 through 7 inclusive.
A bare drive inherits the caller's user, and a bare user inherits the caller's
drive. Compound terms inherit from the caller, never from the preceding term.
Overlapping selections do not repeat searches. Selected locations are visited
in drive order, then user order, with native directory order within each DU.
Unavailable locations are diagnosed; they are never silently mapped elsewhere.
Existing shared attribute-selection conventions apply. SEARCH does not adopt
WHEREIS's global scope or special default inclusion of system files.


##### SEARCH results and totals

TEXT results identify the file, `[TEXT]`, and a one-based line number. An ordinary
matching line is shown once even if it contains several occurrences. The first
occurrence on a line chooses its excerpt. Lines of up to 64 bytes are shown in
full; longer lines use a window of at most 192 source bytes, looking back up to
64 bytes before that occurrence. `[...]` marks omitted edges. Other distant
occurrences on the same line still count, even when outside the chosen excerpt. SEARCH still
searches the whole line and counts every occurrence, including overlaps.
CR/LF is one line break; bare CR and bare LF also end lines. A final unterminated
line is valid. Control bytes are rendered visibly rather than sent to the console.

HEX results identify the file, `[HEX]`, and a zero-based byte offset printed as
eight hexadecimal digits. TEXT and HEX results are independent, including when
both interpretations match at the same position. For example, a file beginning
with `4142 AB 4142` followed by CR/LF yields:

```text
A0:NOTES.TXT [TEXT] line 1: 4142 AB 4142
A0:NOTES.TXT [HEX] offset 00000005
Files searched: 1
Files matched: 1
Text matches: 2
Hex matches: 1
Total matches: 3
```

All successfully read 128-byte CP/M records are searched in full, including final
padding and `1Ah`. `1Ah` does not end TEXT searching. Matches may span records,
extents or line endings. A TEXT match spanning a line ending belongs to the line
where it starts. No bytes beyond record EOF are invented.

The final summary always includes files searched, files matched, TEXT matches,
HEX matches and their sum, including zeros. Files searched includes successfully
opened empty and partially read files. A file with either kind of match counts
once in files matched. No matches is a normal result when coverage is complete.


#### Examples

```text
B0:SEARCH "Error" D0:*.TXT /NOCASE /NOHEX
```

Find literal text. Substitute the locations and filenames appropriate to your session.

#### Errors/Troubleshooting

##### SEARCH paging and errors

At a `/P` prompt, Space or Enter advances one page. Ctrl-C suppresses subsequent
details and prompts, prints `DISPLAY INTERRUPTED` and `SEARCH CONTINUING...`,
and lets SEARCH finish every remaining selected file before printing totals.
It does not cancel the search. Error messages remain visible. The supported
console profile is 80 columns by 24 rows: output wraps explicitly at 79 columns,
with 23 content rows per page. No screen backend is required. There is no backward
paging. Ctrl-C during unpaged output also stops display while searching continues;
final totals remain available. Neither display-stop action cancels coverage.

Open, read and directory errors identify the affected location or file. SEARCH
continues elsewhere when safe and marks the final summary incomplete whenever
selected data could not be searched. Such totals describe observed data only;
zero matches after an error is not proof that all selected files lack the pattern.
Some platform disk-error paths prompt or warm boot without returning to SEARCH;
full recovery and final totals cannot be promised on those paths. Ctrl-C at an
OS `Bad Sector` prompt may warm boot; it is different from Ctrl-C at SEARCH's
own paging prompt. SEARCH needs an 8 KiB TPA budget on the qualified platforms.
Large directories can be slow because it replays directory searches after file
reads; a full 64-entry directory took about 23 seconds at an emulated 4 MHz.

SEARCH restores the caller's drive and user area on every handled exit. It does
not alter files or attributes, create temporary result files, search inside
archives, or replace text.

#### See Also

[file specifications](#file-specifications) · [system messages](#system-messages)


<a id="type-resident"></a>

### TYPE — Resident

#### Description

Displays the contents of text files on the console. Provided by the supplied A0:RCP.CPX. It is available at the command prompt while RCP is loaded.

#### General Form

```text
TYPE filespec
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Read a file | `TYPE A0:README.TXT` |

#### Detailed Reference


##### Resident TYPE

The basic form is:

```text
TYPE filespec
```

For example:

```text
A0>TYPE README.TXT
```

TYPE displays the contents of `README.TXT`.

BetterCP/M also supports extended file selection:

```text
A0>TYPE B3:README.TXT
A0>TYPE B[-]:*.TXT
A0>TYPE [A0,B3]:*.DOC
```

When several files are selected, TYPE displays them in sequence.

TYPE treats the conventional CP/M end-of-text character, Ctrl-Z (`1AH`), as the end of the text.

It does not modify the files being displayed.


##### Resident Paging

Resident TYPE supports forward paging with `/P`:

```text
A0>TYPE README.TXT /P
```

The display pauses after a screenful of text.

Press Space or `.` to advance.

Ctrl-C cancels the resident paged display.

The resident command provides simple forward paging rather than the more extensive navigation facilities of `TYPE.COM`.

#### Examples

```text
TYPE A0:README.TXT
```

Read a file. Substitute the locations and filenames appropriate to your session.

#### Errors/Troubleshooting

If output is not text, stop the display and use DUMP. Resident TYPE does not provide the transient utility's expanded navigation/options.

#### See Also

[TYPE TRANSIENT](#type-transient) · [file specifications](#file-specifications)


<a id="type-transient"></a>

### TYPE — Transient

#### Description

Displays the contents of text files on the console. TYPE.COM is supplied in user 0 on both System disks. Use :TYPE or .TYPE to bypass resident dispatch.

#### General Form

```text
TYPE [options] filespec
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Read with paging | `:TYPE /P A0:README.TXT` |

#### Detailed Reference


##### Transient TYPE.COM

Invoke the transient utility explicitly:

```text
A0>:TYPE README.TXT
```

The transient version provides bidirectional paging, navigation between files, and several display options.


##### TYPE.COM Options

| Option | Description |
|---|---|
| `/P` | Enable interactive paging and file navigation |
| `/7` | Strip the high bit from displayed characters |
| `/T` | Expand tabs to eight-column stops |
| `/CTL` | Display control characters using caret notation |
| `/VER` | Display version information |

Options may appear before or after the file specification.

For example:

```text
A0>:TYPE README.TXT /P
A0>:TYPE README.TXT /7
A0>:TYPE README.TXT /T
A0>:TYPE README.TXT /CTL
```


##### Paging and Navigation

With `/P`, transient TYPE provides the following controls:

| Key | Action |
|---|---|
| Ctrl-R or `,` | Previous page |
| Ctrl-C, `.` or Space | Next page |
| `<` | Beginning of current file, or previous file |
| `>` | Beginning of next file |
| Ctrl-Q | Quit |

The meaning of Ctrl-C here is specific to TYPE.COM's paging prompt. During ordinary output, normal CP/M console handling applies.

At the end of the final file, TYPE leaves the last page displayed until you quit.

You can move backward through earlier pages without a fixed page-history limit, although revisiting distant pages may be slow on floppy disks.


##### Displaying Control Characters

The `/CTL` option displays control characters in a readable form.

For example, a tab is displayed as `^I`, while a form feed appears as `^L`.

This can be useful when examining text files containing unexpected control characters.

The `/T` option expands tabs into spaces for display. When `/CTL` is used, its control-character display takes precedence over ordinary tab expansion.


##### Displaying Several Files

TYPE.COM can display files selected from several drive/user areas:

```text
A0>:TYPE B[-]:*.DOC /P
```

When several files are selected, the utility identifies each file as it is displayed.

You can use `<` and `>` to move between file boundaries.

This makes TYPE.COM useful for examining a collection of text files without returning to the command prompt after each one.


##### Limitations

TYPE is intended for ordinary text files.

It does not provide binary inspection, decompression, text searching, or editing.

For those operations, use an appropriate specialized utility.


#### Examples

Display a file:

```text
A0>TYPE README.TXT
```

Display a file with simple paging:

```text
A0>TYPE README.TXT /P
```

Use the transient viewer with backward paging:

```text
A0>:TYPE README.TXT /P
```

Display control characters:

```text
A0>:TYPE README.TXT /CTL
```

Display all `.DOC` files across drive B's user areas:

```text
A0>:TYPE B[-]:*.DOC /P
```

#### Errors/Troubleshooting

Check the operand grammar and the selected drive/user area. For disk failures, preserve the source and any reported recovery files before retrying. See the [shared system messages](#system-messages) for command lookup, media, configuration and extension diagnostics.

#### See Also

[TYPE RESIDENT](#type-resident) · [file specifications](#file-specifications)


<a id="inspection-comparison-and-verification"></a>

## Inspection, comparison, and verification


<a id="compare"></a>

### COMPARE

#### Description

COMPARE.COM is supplied on the Companion Utilities disk (normally C0). Compare binary files or selected ranges.

#### General Form

```text
COMPARE file1 file2 [options]
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Compare two files | `C0:COMPARE D0:ONE.COM D0:TWO.COM` |

#### Detailed Reference

**COMPARE 1.0 (005)** is included on the locked Companion Utilities disk.
This entry describes the implemented interface. Earlier component-specific
Model 4 deferrals remain in the engineering record; the November 2 native
conformance batch is bounded evidence, not a blanket COMPARE qualification.
Final release acceptance and fresh-package installation remain open. The [engineering specification](../engineering/COMPARE%20Specification.md)
records the approved design decisions and narrow display layout.

COMPARE compares exactly two files without changing either file, its directory
entry or its attributes. Use it to check a rebuilt program against a reference,
examine a patch, or verify a copied file. It compares binary bytes; use DIFF for
line-oriented text differences.


##### Starting a comparison

```text
COMPARE OLD.COM NEW.COM
COMPARE /SIDE A0:OLD.COM B7:NEW.COM
COMPARE /SUMMARY OLD.COM NEW.COM
COMPARE /FROM=0205H /FROM2=0208H /LEN=0100H /SIDE A.BIN B.BIN
```

With primary Utilities in B: and the NOAH companion in C:, use `C0:COMPARE`
if your command environment does not otherwise find it. Options may precede, separate or follow the filenames; option
names are case-insensitive. Supply exactly two filenames. Each may have its own
drive and user qualification. Omitted drive or user selections inherit those
of the caller. Comparing a file with itself is allowed. Wildcards, drive/user
lists or ranges, and extra filenames are rejected.


##### COMPARE options

| Option | Effect |
| --- | --- |
| `/LIST` | List individual differences; the default mode. |
| `/SIDE` | Display corresponding hexadecimal bytes side by side, eight per file per row. |
| `/SUM`, `/SUMMARY` | Show totals and the result without detailed output. |
| `/COUNT=n` | Limit the number of displayed `/LIST` entries; default 20. |
| `/ALL` | Display every differing position in `/LIST`. |
| `/FROM=hex[H]` | Start both files at this byte offset unless `/FROM2` overrides file 2. |
| `/FROM2=hex[H]` | Set file 2's starting offset independently. |
| `/LEN=hex[H]` | Examine at most this many comparison positions. |
| `/P` | Pause between pages in `/LIST` or `/SIDE`. |
| `/40` | Four compact bytes per file per row, with both offsets and the marker, in 38 columns. |
| `/VER` | Display the utility's version and revision without accessing files. |
| `/HELP` | Display command help without opening files. |

Choose one display mode. `/COUNT` and `/ALL` apply only to `/LIST` and cannot be
combined. `/P` cannot be combined with summary-only mode; `/40` requires `/SIDE`.
Repeated identical flags are harmless. Invalid combinations produce an error
before either file is opened. An exact `/VER` token takes precedence over other
arguments. Otherwise, an exact `/HELP` token shows help and ignores other
arguments without accessing files. `/VER` wins if both queries are present.

Offsets and `/LEN` values are hexadecimal, with one to eight digits and an
optional trailing `H`. Thus `/LEN=0100` means 256 positions. `/COUNT` accepts
decimal values from 1 through 65,535; zero and larger values are errors.
Use `/ALL` for unlimited listing. `/LEN=0` selects an empty range.


##### Bytes, ranges and results

COMPARE includes every byte in each 128-byte CP/M logical record, including
final-record padding. `1Ah` is an ordinary byte. No line endings, tabs or high
bits are translated. File lengths are full logical-record lengths in decimal
bytes; display offsets are zero-based hexadecimal positions and can exceed 64K.

Without range options, the comparison starts at zero in both files and continues
until both reach EOF. `/FROM` sets both starting offsets; `/FROM2` overrides the
second independently, regardless of switch order. `/FROM2=0300` alone starts
file 1 at zero and file 2 at `0300H`. `/LEN` limits comparison positions, rather
than limiting each file to an absolute ending offset.

A byte against the same byte matches. Two unequal bytes count as a byte mismatch;
a byte against EOF counts as an additional byte in the file containing it.
These categories are reported separately. Starting beyond EOF is permitted.
When neither side has data left, comparison stops without inventing differences.

The final summary gives full file lengths, mismatch and additional-byte totals,
and the selected range when applicable. `FILES IDENTICAL` requires established
equality of the complete files. `SELECTED RANGES IDENTICAL` describes only the
chosen regions; differences elsewhere may still exist. Unequal full lengths
are reported separately. An empty selected range does not establish full-file
identity. Independently offset comparisons always report selected-range results.


##### Reading comparison output

`/LIST` shows absolute offsets and unequal byte values. When starting offsets
differ, both offsets are shown. A missing byte is marked `---- EOF ----`.
The default limit of 20 entries, `/COUNT`, and `/ALL` control display only:
comparison continues and the final totals cover the complete selected range.

`/SIDE` shows matching rows as well as differing rows. A fixed `<>` marker
identifies rows containing any difference, including a byte against EOF.
Offsets use eight uppercase hexadecimal digits; bytes use two.

File 1 determines row boundaries. An unaligned start leaves leading byte slots
blank, and a partial final row leaves trailing slots blank. Corresponding bytes
in file 2 occupy the same horizontal slots, even if its offsets have different
alignment. Its row label is the conceptual address of slot zero, which may
precede the first byte actually shown. A negative conceptual row base appears
as `--------`; this is an alignment placeholder, not EOF. For example,
`/FROM=0007 /FROM2=0000` labels the first row `00000000` and `--------`.

When one file is exhausted and the other still has bytes, its first fully absent
row displays `---- EOF ----`; later exhausted rows may remain blank. Existing
bytes in a partial row remain visible, with unavailable slots left blank; no
EOF banner is overlaid on that row. In `/40`, the EOF label is shortened to `EOF`
and padded within the byte field.

`/40` removes spaces between the four byte values on each side. Two spaces
separate each offset from its byte field; the central marker occupies two
fixed columns. Data rows use 38 columns:

```text
00000004        54<>--------        20
00000008  47495441<>00000001  54414C20
```


#### Examples

```text
C0:COMPARE D0:ONE.COM D0:TWO.COM
```

Compare two files. Substitute the locations and filenames appropriate to your session.

#### Errors/Troubleshooting

##### Paging and errors

`/P` provides forward-only pages using ordinary console output. On a 24-row
console it reserves the bottom row for the prompt, leaving 23 content rows.
Press Space or Enter for the next page. Ctrl-C at the prompt stops detailed
display and further prompts, but comparison continues silently:

```text
DISPLAY INTERRUPTED
COMPARISON CONTINUING...
```

The complete final summary is then printed. Q and Esc at the prompt have the
same display-stop behavior. There is no backward paging or screen redraw, and
no particular terminal personality or monitor is required.

During non-paged output, Ctrl-C cancels the operation cleanly and reports
`COMPARISON INCOMPLETE`. No completed-comparison result is printed; any partial
statistics are explicitly labelled incomplete.

A file-open error identifies the affected file. A read failure prevents a
completed comparison result; partial totals must not be treated as complete.
Handled exits close opened files and restore the caller's drive and user area.

#### See Also

[file specifications](#file-specifications) · [system messages](#system-messages)


<a id="crcksum"></a>

### CRCKSUM

#### Description

CRCKSUM.COM is supplied on the primary Utilities disk (normally B0). Calculate checksums and verify saved lists.

#### General Form

```text
CRCKSUM [options] [filespec]
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Calculate checksums | `B0:CRCKSUM D0:*.COM` |

#### Detailed Reference

**CRCKSUM 1.0 (011)** ships on the primary Utilities disk. With that disk in B:,
run `B0:CRCKSUM /VER` to check your copy or `B0:CRCKSUM /H` for help.

CRCKSUM answers two related questions: what check values identify these files, and do the files still agree with an earlier list? It calculates eight values: the original CP/M CRCK calculation, corrected CRCK, CHEK, CRC-32, SUM8, SUM16, KERM6 and KERM12. You can display them, save a list, or check a directory against a saved reference. No input file is altered.


##### Getting started with CRCKSUM

```text
CRCKSUM
CRCKSUM B3:*.COM
CRCKSUM B[1,3,4-5]:*.COM
CRCKSUM A0:*.COM B3:*.TXT
CRCKSUM /CHECK B3:
CRCKSUM /CHECK B[1-3]:FILE.TXT
```

With no filespec, CRCKSUM selects `*.*` in your current logged drive/user area. A bare DU such as `B3:` also means `*.*`. Extended DU lists and ranges follow the common BetterCP/M rules. Separate filespecs may select different files in different locations. Overlapping selections do not process a physical file twice.

If CRCKSUM is on the Utilities Disk in B0: and your command environment does not find it automatically, use `B0:CRCKSUM`. The location of CRCKSUM.COM does not determine the locations of the files it checks.


##### CRCKSUM options

```text
CRCKSUM [options] [filespec ...] [options]
```

| Option | Effect |
| --- | --- |
| `/CRCK` | Select the original historical CRCK calculation. |
| `/CRCK5` | Select corrected CRCK. |
| `/CHEK` | Select CHEK-compatible CRC. |
| `/CRC32` | Select CRC-32/ISO-HDLC, the common ZIP/Ethernet variant. |
| `/SUM8` | Calculate the unsigned byte sum modulo 256. |
| `/SUM16` | Calculate the unsigned byte sum modulo 65536. |
| `/KERM6` | Calculate the Kermit type-1 six-bit checksum applied to the whole file. |
| `/KERM12` | Calculate the Kermit type-2 twelve-bit checksum applied to the whole file. |
| `/FILE=filespec` | Write one master list. A single destination DU may be supplied. |
| `/LOCAL=filename` | Write an individual list in each selected DU. Supply a filename only. |
| `/LEGACY` | Write historical CRCKLIST records and force historical CRCK alone. |
| `/CHECK` | Verify against a reference discovered in each selected DU. |
| `/CHECK=filename` | Verify against this exact list name in each selected DU. Supply a filename only. |
| `/40` | Display complete groups of two checksum columns within 40 columns. Saved lists are unchanged. |
| `/H`, `/HELP` | Display help without accessing files. |
| `/VER` | Display the utility's version and revision without accessing files. |

Option names are case-insensitive, and options may appear before, between or after filespecs. Without algorithm switches, calculation displays all eight values. Supplying switches selects their combination: `/CRCK /CHEK` displays those two. Explicit algorithm switches also determine output order: `/SUM16 /CRCK /KERM6` puts those three columns in that order. Repeating a switch neither moves nor duplicates its column. This order also applies to the narrow display and mismatch details. Successful verification reports `FILENAME.EXT: MATCH (all N checksums)`, counting the checksum fields verified from the matching list entry. When a value option is repeated, every occurrence must be valid and the last value is used. `/HELP` takes precedence over `/VER`; either query suppresses ordinary command processing.

`/LEGACY` always selects historical CRCK only. All other algorithm switches are ignored when `/LEGACY` is present, regardless of their order. You do not have to add `/CRCK` as well.

Calculation/list generation and verification are separate operations. Do not combine `/CHECK` with `/FILE=` or `/LOCAL=`. `/FILE=` and `/LOCAL=` may be used together.


##### Which calculation to use

Names caused some confusion even during the CP/M years. SIG/M's CRC utility version 5.0 continued to calculate the original CRCK value. The separately developed corrected CRCK 5.x calculation produces different answers. `/CRCK5` selects that corrected calculation; it does not mean a five-bit CRC.

Use `/CRCK` for original SIG/M catalog and CRCKLIST values. CHEK is another 16-bit CRC calculation, also found in the CP/M library and RCPM tools. CRC-32 gives a 32-bit result. None of these values authenticates a file or establishes that it came from a trusted author; they are file-integrity checks.

SUM8 adds the stored bytes modulo 256; SUM16 adds them modulo 65536. KERM6
and KERM12 use Kermit's six-bit and twelve-bit checksum arithmetic across the
whole file. KERM6 folds bits 6 and 7 of the sum into its low six bits; KERM12
retains the low twelve bits. Results are numeric hexadecimal, not Kermit's
printable packet encoding. No packet headers or data quoting are included.
These values therefore do not represent an individual transfer packet's check.

In the default layout, the four new fields follow CRC32 in the order SUM8, SUM16, KERM6, KERM12.
They contain two, four, two and three hex digits respectively, right-aligned
within fields wide enough for their headings. All eight algorithms are selected
by default; for example, `CRCKSUM B3:*.COM /SUM8 /KERM12` displays just those two.
`/LEGACY` continues to force only historical CRCK.

CRCKSUM includes every byte of each 128-byte CP/M logical record. Embedded Ctrl-Z bytes and padding at the end of the final record are included. Text line endings are not converted. `RECS` is the exact record count; multiply by 128 to obtain the byte count being checked. A host copy with stripped padding or translated line endings may therefore produce a different result.


##### Reading the CRC display and native lists

With all algorithms selected, the display and saved list use this layout
(the example is `123456789` padded with 119 Ctrl-Z bytes):

```text
; BetterCP/M CRC list
NAME     EXT  RECS  CRCK  CRCK5  CHEK  CRC32     SUM8  SUM16  KERM6  KERM12
-------- ---  ----  ----  -----  ----  --------  ----  -----  -----  ------
TEST     DAT     1  A687   5D45  E447  2F263492    F3   0DF3     36     DF3
```

The normal display uses a table like the native saved format. With `/CRCK /CRCK5 /CHEK /CRC32`, these two rows use actual values from SIG/M Volume 310:

```text
; BetterCP/M CRC list
NAME     EXT  RECS  CRCK  CRCK5  CHEK  CRC32
-------- ---  ----  ----  -----  ----  --------
ZMD146   LBR  1418  136B   A548  D24B  82A2F154
ZMDOVL2  LBR   372  B06D   6B36  C153  DE35205C
```

The name and extension occupy separate fixed fields with no dot. An extensionless file leaves EXT blank. Decimal record counts and hexadecimal values are right-aligned to their dash fields. Only selected algorithms appear. The RECS column grows when necessary, with a new consistent layout for that DU section.

The column header identifies the calculations; the dash runs establish their positions. CRC reads data by columns, so an empty extension cannot be confused with a record count. Keep the header, separator and rows aligned if editing a list. The reader accepts algorithm columns in any order, blank lines, comments beginning with `;`, and repeated section headers. Unknown or duplicate columns, missing values and malformed records are reported rather than guessed.

`/40` displays groups of two equal-width checksum columns. Each group contains its headings, eight-dash separators and values, with a blank line between groups. The filename and record count appear only in the first group; later groups align beneath the checksum columns. Algorithm selection and command-line order determine the groups. It changes screen presentation only. Saved lists retain the standard table, and `/LEGACY` retains its historical file layout.


##### Saving master and local lists

```text
CRCKSUM B3:*.COM /FILE=A0:MASTER.LST
CRCKSUM B[1-3]: /LOCAL=CRC.LST
CRCKSUM B[1-3]: /FILE=A0:MASTER.LST /LOCAL=CRC.LST
CRCKSUM B3:*.COM /CRCK /CHEK /LOCAL=CRC.LST
```

The first command saves one master list in A0:. The second writes CRC.LST in each of B1, B2 and B3. The third does both in the same run, reading each input file once. The fourth writes only historical CRCK and CHEK values.

Each DU is handled as a section. Files are alphabetized by name, then extension. Separate filespec operands establish first-encounter DU order; a bracketed selector follows the common canonical drive/user order. A master is the concatenation of the individual sections, with a blank line between them. Each section repeats its header and separator.

Saved sections do not record DU locations. Files with the same name in different DUs remain separate records. This makes local lists easy to move with their files, but a master list does not remember where each section originally lived. Keep that in mind when combining unrelated versions of the same filename.

An unqualified `/FILE=` destination uses the DU you were logged into when CRCKSUM started. `/LOCAL=` takes only a filename because the destination is each target DU. A DU qualifier on `/LOCAL=` is an error and stops the command before files are processed. For example, use `/LOCAL=CRC.LST`, not `/LOCAL=A0:CRC.LST`.

Output lists and temporary files are excluded from input selection. If master and local destinations name the same physical file, CRCKSUM writes that file once with the complete master contents; it does not attempt to keep a second local-only version under the same name.

If a destination exists, CRCKSUM displays its full identity:

```text
B3:CRC.LST exists. Overwrite? (Y/n/a/?)
```

Type `?` for `Y Yes, N No, A All, ? Help`; the same file's question is
then repeated. Help changes no files or choices. Enter still means Yes.

Y or Enter replaces that list. N leaves it alone and continues other requested outputs. A authorizes this and subsequent list replacements for this run. Ctrl-C cancels. CRCKSUM stages output before replacing a completed list. A failed or cancelled operation does not deliberately install a partial list under the final name; any recovery failure identifies the files left behind. Check the final output totals to see which lists were completed, declined or failed.


##### Writing a historical CRCKLIST

```text
CRCKSUM B3:*.* /FILE=CRCKLIST.CRC /LEGACY
CRCKSUM B[1-3]: /LOCAL=CRCKLIST.CRC /LEGACY
```

`/LEGACY` uses the historical layout for both console output and saved lists. It reproduces the original prefix, padded dotted filename, two TABs before `CRC =`, space-separated hexadecimal bytes and blank lines between entries:

```text
--> FILE:  ZMD146  .LBR          CRC = 13 6B

--> FILE:  ZMDOVL2 .LBR          CRC = B0 6D
```

TABs are expanded here for reading. Native headers, sizes and the other algorithms are omitted. CRC 5.0 and CRC 6.4 historical readers require the `--> FILE:  ` prefix; `/LEGACY` supplies it. Native output is single-spaced; legacy output deliberately remains double-spaced.


##### Checking files against their local list

```text
CRCKSUM /CHECK
CRCKSUM /CHECK B3:FILE.TXT
CRCKSUM /CHECK B[1-3]:*.COM
CRCKSUM /CHECK=REFERENCE.LST B[1-3]:
CRCKSUM /CHECK B3: /CRCK /CRC32
```

Every selected file is checked against one reference list in its own DU. The final example limits verification to recorded CRCK and CRC32 values. CRCKSUM does not fabricate values missing from a list: an entry containing neither selected algorithm is skipped and reported as such.

Bare `/CHECK` tries these names in order, independently in each target DU:

1. `CRC.LST`
2. `CRCKLIST.*`
3. `CRCKFILE.*`
4. `-CATALOG.*`

The first tier containing a candidate wins. If that tier contains several files, CRCKSUM reports ambiguity and asks you to select a name using `/CHECK=filename`. If none is found, it reports `No CRC list found` and continues to the next selected DU. It never searches your logged DU as a fallback. With no target operand, the logged DU is itself the target.

`/CHECK=REFERENCE.LST` means REFERENCE.LST in each target DU. It does not mean a single central reference for every target. A DU qualifier on `/CHECK=` is an explicit error and aborts the command before processing. To check a moved collection, place its reference beside its files and select that DU.

CRCKSUM displays the reference it selected. Once selected, a bad format, malformed list, absent checksum information or mismatch does not cause CRCKSUM to try a different reference. A catalog without checksum entries is not a usable reference. To use another file, name it explicitly.

CRCKSUM recognizes its native tables, historical CRCKLIST/CRCKFILE records, and original SIG/M catalogs containing CRC columns. Historical `CRC =` fields and original SIG/M catalog CRCs mean historical CRCK. Some early SIG/M catalogs contain only descriptions: their separate CRCKLIST or CRCKFILE is the verification reference. Reading a historical list does not require `/LEGACY`.


##### Sizes, repeated names and verification results

Size is checked first where available. Native RECS is exact. SIG/M whole-K sizes are rounded: a 3K entry permits 17 through 24 records, rather than requiring exactly 24. An incompatible size rejects that entry. A compatible size, or a list without sizes, always proceeds to checksum comparison.

A master can contain several entries for the same filename. CRCKSUM compares the target file with the size-compatible candidates. A file matches only if every selected value actually recorded in one candidate agrees. It never combines values from different entries to manufacture a match. A complete matching candidate verifies the file; differing alternatives are identified separately. The report identifies which algorithms were actually checked.

Wildcard checking reports both selected files absent from the reference and selected reference entries whose files are missing. The reference file itself is excluded from wildcard targets. Files outside your requested pattern do not count as failures.

Expect separate reports for:

- **MATCH:** one complete applicable reference entry agrees.
- **SIZE MISMATCH / CHECKSUM MISMATCH:** the reference does not agree with the actual file.
- **FILE NOT FOUND:** a selected reference entry names an absent file.
- **FILE NOT LISTED:** a selected existing file has no reference entry.
- **SKIPPED:** no selected algorithm is recorded for the applicable entry.
- **READ ERROR / LIST ERROR:** verification could not be completed reliably.

One compact final summary covers all selected DUs. For example:

```text
1 file calculated; 1 list written.
12 verified; 1 failed; 2 missing; incomplete.
```

Zero counters are omitted. File-specific errors remain beside the affected file. A successful check ends with a summary such as `1 verified.` A check with no verified files reports `No files verified; incomplete.` (with any nonzero error counts included). Cancellation ends with `; cancelled.` Individual matches can still appear when another file or malformed entry makes the overall job incomplete. No per-DU counter block or duplicate total follows the checksum rows.

Ctrl-C cancels and reports an incomplete operation. Completed independent output lists remain, but uncommitted output is discarded. CRCKSUM restores your original drive/user selection before returning.

#### Examples

```text
B0:CRCKSUM D0:*.COM
```

Calculate checksums. Substitute the locations and filenames appropriate to your session.

#### Errors/Troubleshooting

Check the operand grammar and the selected drive/user area. For disk failures, preserve the source and any reported recovery files before retrying. See the [shared system messages](#system-messages) for command lookup, media, configuration and extension diagnostics.

#### See Also

[file specifications](#file-specifications) · [system messages](#system-messages)


<a id="dump"></a>

### DUMP

#### Description

DUMP.COM is supplied on the primary Utilities disk (normally B0). Inspect bytes in bare or enhanced viewer modes.

#### General Form

```text
DUMP [options] filename
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| View a file | `B0:DUMP D0:IMAGE.COM` |

#### Detailed Reference

`/HELP` shows the compact utility quick reference. `/HELP` and `/VER` are
case-insensitive exact tokens, ignore other arguments, and return before file,
drive/user or screen-provider services; HELP takes precedence when both occur.

DUMP displays the bytes of one file in hexadecimal and readable ASCII. Use it to inspect binary programs, examine text control characters, or locate a particular byte sequence. DUMP reads the file without changing its contents or attributes. It does not disassemble instructions or edit files.


##### Quick start

To display a file continuously:

```text
B0:DUMP A0:README.TXT
```

Press Ctrl-C to stop. To browse a page at a time, first load a suitable screen backend as described under [Preparing the paged viewer](#preparing-the-paged-viewer), then enter:

```text
B0:DUMP A0:README.TXT /P
```

Press Space for the next page, Ctrl-R for the previous page, F to find text or bytes, G to go to a position, and Q to quit.


##### Command syntax and options

```text
DUMP file
DUMP file /P
DUMP file /40
DUMP file /FROM=offset
DUMP file /LEN=count
DUMP file /FROM=offset /LEN=count
DUMP file /P /40 /FROM=offset
DUMP /BARE file
DUMP /VER
```

If DUMP is on B0: and is not otherwise found by your command environment, use `B0:DUMP` in place of `DUMP`.

| Option | Purpose |
| --- | --- |
| `/P` | Browse interactively with paging, Find, and Go To. Requires a loaded screen backend. |
| `/40` | Show eight bytes per row in a layout that fits a 40-column screen. |
| `/FROM=offset` | Begin displaying at the exact hexadecimal byte position; earlier columns are blank. |
| `/BARE` | Use the original CP/M hex-only display and interruption behavior. |
| `/LEN=count` | Display at most this many bytes, in hexadecimal; optional H/h suffix. |
| `/HELP` | Show the compact help screen without opening a file. |
| `/VER` | Show DUMP’s version and revision, then return. Other arguments are ignored. |

Options may appear before or after the filename and are case-insensitive. `/P`, `/40`, `/FROM=`, and `/LEN=` may be combined. `/BARE` cannot be combined with them. Repeating a flag is harmless. For `/FROM=` and `/LEN=`, the last value wins, but every occurrence must be valid. Every `/FROM=` must also identify a byte within the file.

Supply exactly one filename. Enhanced modes accept a single drive/user-qualified name such as `B7:FILE.COM`. A drive-only name such as `B:FILE.COM` uses your current user area; an unqualified name uses your current drive and user. Wildcards, file selectors, multiple files, and multiple user areas are not accepted.

`/FIND=` is not available. Unknown options, missing operands, incompatible combinations, and invalid values produce a diagnostic and return to the command prompt.

`DUMP /VER` uses the standard BetterCP/M utility identification style:

```text
DUMP 1.0 (008)
  - - -
 | BetterCP/M Utilities
 | Hexadecimal File Display
```

The revision number changes with executable updates. Other DUMP commands do not display a sign-on banner.


##### Reading the display

Normal output shows 16 bytes per row:

```text
00001230  00 01 02 03 04 05 06 07  08 09 0A 0B 0C 0D 0E 0F  ................
```

The first eight digits give the hexadecimal position of the row’s first byte, measured from zero at the beginning of the file. Each pair of digits represents one byte. The final column shows the same bytes as ASCII characters. Printable characters, including spaces, appear directly; control characters and bytes outside printable ASCII appear as dots. A dot in that column can therefore represent either an actual period or a nonprintable byte; check the hexadecimal column to distinguish them.

The normal row occupies 76 columns. `/40` uses 37 columns and shows eight bytes per row:

```text
00001230  41424344 45464748  ABCDEFGH
```

Both layouts use eight-digit offsets, including for files larger than 64K. `/40` is selected when you run DUMP; it cannot be toggled while viewing.

CP/M stores files in 128-byte records. DUMP displays all bytes in those records, including padding after the useful text or data. The text end marker `1Ah` is displayed as an ordinary byte; it does not stop DUMP. No tabs, line endings, or embedded terminal controls are interpreted as display instructions.

Without `/P`, output continues to the end of the file or the `/LEN=` limit. Ctrl-C stops this output and is consumed, so it does not remain waiting at the command prompt. Other keys do not stop enhanced streaming output. An empty file displays `Empty file` and returns, including when `/P` was requested.


##### Starting at a particular position

`/FROM=` and the viewer’s G command take a hexadecimal byte position: one to eight digits, optionally followed by H. `1237`, `1237H`, and `00ff` are valid forms. A position is always hexadecimal, even when it contains only decimal digits.

```text
B0:DUMP A0:FILE.COM /FROM=1237H
```

This begins displaying byte `1237h`. The normal row address remains `00001230`; the first seven byte and ASCII positions are blank. `/40` also keeps aligned row addresses and columns, using multiples of eight. Bytes retain their usual columns.

The position must identify an existing byte. The position immediately after the file’s last byte is invalid, as is any explicit position in an empty file. An invalid `/FROM=` reports an error without displaying file data.

In the paged viewer, press G and enter a position. A successful Go To puts the containing row at the top. Press Enter on empty input or ESC to cancel without moving. Invalid input stays available for correction. To return to the beginning, press G, enter `0`, then press Enter.


##### Limiting the displayed range

```text
B0:DUMP A0:FILE.COM /FROM=7 /LEN=AH
```

This displays ten bytes, offsets `7h` through `10h`. `/LEN=` is hexadecimal,
with one to eight digits and an optional H/h suffix, just like `/FROM=`. It counts
bytes, including CP/M record padding, rather than lines. Excluded positions in
both edge rows are blank in hex and ASCII. A count past EOF displays only the
remaining bytes; even a start-plus-count beyond `FFFFFFFFh` stops at EOF without
wrapping. `/LEN=0` displays no bytes and does not enter the viewer. It still checks
the file and any explicit `/FROM=`; empty-file handling is unchanged.

With `/P /LEN=`, the range stays fixed. Paging stops at its boundaries; the
existing `Beginning of file` and `End of file` messages refer to those boundaries.
Go To accepts only offsets within it and does not restart the count. Find searches
only this range, and the entire match must fit. The first included byte is the
search anchor when the row starts before the range.

Without `/LEN=`, `/FROM=` selects only the initial position. You can still page
back or Go To zero and search the whole file. Initial leading blanks disappear
after successful repositioning; Go To and Find retain their usual containing-row
display. A new Find starts at the first included byte of the current page.


##### Preparing the paged viewer

`/P` needs a loaded screen backend. On Model 4 or trs80gp, the backend is M4SCRN:

```text
RSX LOAD M4SCRN
```

On cpmsim in a suitable ANSI host terminal, use ANSISCRN:

```text
RSX LOAD ANSISCRN
```

These examples assume the backend is available in your current command environment. Use its actual drive/user-qualified location if necessary. Check `RSX LIST` first; the supplied 1.1 startup does not load a standalone screen backend. Load M4SCRN explicitly for a SCRN client, M2SCRN on Model II, or ANSISCRN on cpmsim.

DUMP calls the screen backend directly. You do not need to select a particular ADM-3A, VT52, or ANSI personality for DUMP; an existing personality may remain loaded. Other applications may still require that personality. Loaded RSXs consume transient program memory until unloaded; see the User’s Guide for RSX management.

The backend must provide the required screen operations and report enough space: at least 76 columns for normal output or 37 for `/40`, with at least one data row and one bottom row. DUMP does not load a backend automatically, switch to `/40` automatically, or silently replace `/P` with continuous output.

Exactly one bottom row is shared by command hints, messages, and input prompts. All other rows display data. A 24-row screen therefore shows up to 23 data rows: 368 bytes in normal mode or 184 bytes with `/40`.

ANSISCRN supplies its documented 80-by-24 viewport; it does not automatically detect terminal resizing. Keep your host terminal large enough for that viewport. `/40` changes DUMP’s data layout, not the backend’s reported dimensions.


##### Moving through the file

| Key | Action |
| --- | --- |
| Space or Ctrl-C | Next page, including while a search is active. |
| Ctrl-R | Previous page, including while a search is active. |
| `.` | Next page; next occurrence when a search is active. |
| `,` | Previous page; previous occurrence when a search is active. |
| F | Enter a new Find pattern. |
| G | Go to a hexadecimal byte position. |
| Q | Quit DUMP. |

Ctrl-C means “next page” only at the viewer’s navigation prompt. In continuous output it stops DUMP. Within text-entry prompts, use the editing controls described below.

A page movement uses the screen’s data capacity. Page Up near the beginning moves to offset zero even if less than a full page precedes the current display. At the beginning, further Page Up requests leave the page unchanged and show `Beginning of file` in the bottom row.

The last page stays visible. If it already includes the end of the file, Page Down shows `End of file` without moving or quitting. Boundary messages do not ring a bell or require acknowledgment. Unrecognized navigation keys are ignored.


##### Finding bytes or text

Press F, enter the pattern, then choose H for hexadecimal bytes or A for ASCII text:

```text
Find: CD 05 00
Search as (H)ex or (A)SCII? H
```

For hex, `CD0500` and `CD 05 00` mean the same three bytes. Use complete byte pairs; spaces may separate pairs but cannot split a pair. For ASCII, type the text exactly as it occurs. Search is case-sensitive and preserves spaces: `Hello` differs from `HELLO`, and leading or trailing spaces are part of the pattern. To find control characters or binary bytes, choose hex.

A pattern may contain up to 32 bytes: 32 ASCII characters or 64 hex digits with optional spaces between byte pairs. The input line accepts at most 95 characters, enough for 32 hex bytes separated by single spaces. Additional insertion is refused with a message; existing text remains editable. Invalid hex or an overlong decoded pattern is diagnosed so you can re-enter it. An invalid H/A choice leaves the pattern available and asks again.

A new Find searches forward from the first byte of the current page, including that byte. It does not automatically start at the beginning of the file. To search the whole file, first use G to go to zero.

A successful search puts the row containing the match at the top and shows the exact byte position, for example `Match at 00001237`. The match position may be inside that row; highlighting the matching bytes is not provided.

After a Find, `.` searches for the next occurrence and `,` for the previous one. Matches may overlap: searching for `ABA` in `ABABA` finds offsets zero and two. Continuation starts strictly after or before the last match’s starting position, so it does not repeatedly return the same match.

Searches never wrap around. A new Find with no match shows `Pattern not found` and leaves the page unchanged, but the new pattern becomes active. A continuation reaching its boundary shows `No further matches` and preserves the page and search position. You can then search in the other direction.

Page movement or a successful Go To retains the pattern and establishes a new search starting position at the first byte of the displayed page. From there, `.` includes that byte in its forward search; `,` seeks the nearest match starting before it. Space, Ctrl-C, and Ctrl-R remain available for ordinary paging while the pattern is active. There is no separate clear-search command.

ESC cancels either Find prompt or a running search. Cancelling a new Find keeps the previous pattern, page, and search position. Empty Enter at the pattern prompt cancels. An all-space hex entry also cancels; an all-space ASCII pattern searches for those spaces.


##### Editing an input prompt

Find and Go To share the bottom row with the command hints. While either prompt is active, use:

| Key | Action |
| --- | --- |
| Ctrl-S | Move left one character. |
| Ctrl-D | Move right one character. |
| Ctrl-G | Delete the character under the cursor. |
| Ctrl-H or Backspace | Delete the character before the cursor. |
| Enter | Submit the input. |
| ESC | Cancel. |

Typing inserts at the cursor. Long input scrolls horizontally within the bottom row without overwriting the file display. A reverse-video character marks the insertion point; at the end of the text, it appears as an underscore. Movement and deletion past either end leave the input unchanged. Ctrl-G deletes text; it is not a cancellation key.

On Model 4, CLEAR and Shift-CLEAR generate ESC. Control-CLEAR generates DEL, which is a different character. In trs80gp, Home supplies CLEAR; on a MacBook without a Home key, use Fn-Left Arrow to generate Home.


##### Original CP/M display

Use `/BARE` for DRI-style hexadecimal-only output:

```text
B0:DUMP /BARE A:FILE.COM
```

```text
0000 00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F
0010 10 11 12 13 14 15 16 17 18 19 1A 1B 1C 1D 1E 1F
```

There is no ASCII column or command bar. The four-digit offsets wrap to zero after 64K. Every successful 128-byte record is displayed, including padding and `1Ah`.

Any pending key stops output at a row boundary. Unlike enhanced mode, `/BARE` does not consume that key: it remains available to the command environment. An empty file produces no data rows or empty-file message. A missing file reports `NO INPUT FILE PRESENT ON DISK`. A nonzero read result ends output without distinguishing EOF from a read error.

`/BARE` accepts an ordinary filename with optional drive qualification in your current user area. It rejects explicit user qualification such as `A0:FILE.COM`, as well as `/P`, `/40`, `/FROM=`, and `/LEN=`. The `B0:` prefix locating DUMP itself is independent of this operand restriction. You may put `/BARE` before or after the filename.


#### Examples

```text
B0:DUMP D0:IMAGE.COM
```

View a file. Substitute the locations and filenames appropriate to your session.

#### Errors/Troubleshooting

##### Messages and recovery

Messages in the paged viewer occupy the bottom row, temporarily replacing the hints. Prompts use that same row. Messages remain until the next recognized command; the file display does not scroll to make room for them.

| Situation | What to do |
| --- | --- |
| Missing file | Check its spelling, drive, and user area. An unqualified operand refers to your current drive/user, not necessarily DUMP’s location. |
| Unknown or incompatible option | Correct the command. `/VER` ignores other arguments; `/BARE` cannot be combined with enhanced options when no query is present. |
| Invalid position | Use a hexadecimal byte position within the file. In Go To, edit the retained input or cancel with ESC. |
| Missing screen support | Load the appropriate screen backend, or omit `/P` for continuous output. |
| Screen too narrow | Try `/40` if at least 37 columns are available; otherwise use a suitable display. |
| `Beginning of file` or `End of file` | The current page remains visible. Move in the other direction or press Q to quit. |
| `Pattern not found` or `No further matches` | Check the pattern and H/A interpretation, change direction, or use G to choose a new starting point. Search does not wrap. |
| `Read error at XXXXXXXX` | The offset identifies the failed read. A search was not completed; do not interpret this as “no match.” |

A later page-read failure keeps the last complete page and its search position. A search-read failure also preserves the previously committed pattern and position. If the first page cannot be read, DUMP reports the error and returns to the command prompt. Continuous output stops at a distinguishable read error and reports its position.

DUMP restores the caller’s drive and user area on its own normal, cancelled, and handled-error exits. Lower-level disk recovery prompts or system aborts may take control before DUMP can handle the failure. DUMP does not repair a damaged file or disk.

#### See Also

[file specifications](#file-specifications) · [system messages](#system-messages)


<a id="md5sum"></a>

### MD5SUM

#### Description

MD5SUM.COM is supplied on the primary Utilities disk (normally B0). Calculate MD5 digests and verify saved lists.

#### General Form

```text
MD5SUM [options] [filespec]
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Calculate file digests | `B0:MD5SUM D0:*.COM` |

#### Detailed Reference

**MD5SUM 1.0 (005)** ships on the primary Utilities disk. With that disk in B:,
run `B0:MD5SUM /VER` to check your copy or `B0:MD5SUM /H` for help.

MD5SUM calculates one MD5 digest for each selected file. Save the results, and you can later check whether the files still agree with that list. Its selection, master/local output, overwrite and checking behavior follows CRCKSUM. There is only one algorithm and one saved-list format.


##### Getting started with MD5SUM

```text
MD5SUM
MD5SUM B3:*.COM
MD5SUM B[1,3,4-5]:*.COM C7:*.TXT
MD5SUM B3: /LOCAL=MD5SUM.LST
MD5SUM /CHECK B3:
MD5SUM /CHECK B[1-3]:FILE.TXT
```

Without a filespec, MD5SUM selects `*.*` in your current logged DU. A bare DU also means all files there. Overlapping selections do not hash the same physical file twice. Separate operands establish first-encounter DU order; bracketed selectors follow the common canonical DU order. Files within a DU are alphabetized by name and extension.

If your command environment does not find the executable automatically, give its location, for example `B0:MD5SUM`. That does not change the target DU.


##### MD5SUM options

```text
MD5SUM [options] [filespec ...] [options]
```

| Option | Effect |
| --- | --- |
| `/FILE=filespec` | Write one master list; an explicit single destination DU is allowed. |
| `/LOCAL=filename` | Write a separate list in each target DU; supply a filename only. |
| `/CHECK` | Check against MD5SUM.LST in each target DU. |
| `/CHECK=filename` | Check against this exact list name in each target DU; supply a filename only. |
| `/40` | Fit console results and messages within 40 columns; saved lists are unchanged. |
| `/H`, `/HELP` | Display help without file access. |
| `/VER` | Display the utility's identity without file access. |

Options are case-insensitive and may appear before, between or after filespecs. Repeated value options must all be valid; the last value is used. A later bare CHECK does not erase an explicit CHECK filename. HELP takes precedence over VER, and either query ignores ordinary operands and options.

FILE and LOCAL may be combined. CHECK is a separate operation and cannot be combined with either. There are no algorithm-selection switches or LEGACY mode.


##### What the digest covers

MD5SUM includes every byte of every stored 128-byte logical record. Embedded Ctrl-Z, high-bit bytes and final-record padding all count. No text conversion takes place. Files larger than 64 KiB are processed as a stream.

A host MD5 program gives the same answer for exactly the same bytes. If a transfer strips CP/M padding or changes line endings, it changes the file being hashed. Keep the complete stored bytes when comparing a CP/M digest with a host digest. Accepting a text-mode entry in a list does not change this rule.

MD5 is useful for identifying files and detecting accidental changes. It does not establish authorship or protect against deliberately constructed collisions.


##### Reading and saving the results

Normal calculation output and saved entries use conventional md5sum notation:

```text
b42a83d49df3489b2324811d5ed28d76 *TEST.DAT
```

This example is the digest of `123456789` followed by 119 Ctrl-Z bytes, one complete logical record. The digest has 32 lowercase hexadecimal digits. One space and an asterisk separate it from the filename. The star identifies binary input; it is not a wildcard. Names are uppercase, with an ordinary dot before the extension. Extensionless names have no trailing dot.

There are no table headings, record counts, DU addresses or blank lines between groups in saved lists. MD5SUM accepts both the starred form and the conventional two-space form:

```text
b42a83d49df3489b2324811d5ed28d76  TEST.DAT
```

Both forms check the same complete stored file. Uppercase digest letters and lowercase filename letters are accepted too. Lists may have CRLF or LF endings and blank lines. Tagged output such as `MD5 (TEST.DAT) = ...`, host paths, escaped filenames and other algorithms are not accepted; unsupported or malformed entries are reported, not guessed.

The console identifies the current DU and ends with a compact summary. Those messages are not saved in the list. Use FILE or LOCAL to make a list rather than capturing the entire console display. With `/40`, the console puts the filename on one line and the intact digest on the next. Saved entries keep their conventional single-line form.


##### Master and local lists

```text
MD5SUM B3:*.COM /FILE=A0:MASTER.LST
MD5SUM B[1-3]: /LOCAL=MD5SUM.LST
MD5SUM B[1-3]: /FILE=A0:MASTER.LST /LOCAL=MD5SUM.LST
```

The first command writes one master in A0:. The second writes MD5SUM.LST separately in B1, B2 and B3. The third does both, reading each selected input only once. Without an explicit DU, FILE writes in the DU you were logged into when MD5SUM started.

A master is the uninterrupted concatenation of the local entry streams. It contains no group headers or source locations. Files sharing a name across DUs remain separate entries. A local list can move with its files; a master does not remember which original DU held a particular version.

LOCAL takes only a name because each target DU supplies its location. For example, use `/LOCAL=MD5SUM.LST`, not `/LOCAL=B3:MD5SUM.LST`. A DU qualifier is an error and stops the command before processing. Output lists and transaction files are excluded from input selection. If FILE and LOCAL resolve to the same physical file, it is written once with the complete master contents.

Before replacing a list, MD5SUM asks:

```text
B3:MD5SUM.LST exists. Overwrite? (Y/n/a/?)
```

Type `?` for `Y Yes, N No, A All, ? Help`; the same file's question is
then repeated. Help changes no files or choices. Enter still means Yes.

Y or Enter replaces this destination. N leaves it alone and continues other outputs. A authorizes this and later replacements in this run. Ctrl-C cancels. Output is staged before replacing a completed list. Handled failures or cancellation discard uncommitted output; recovery failures identify any files left behind. Completed independent local lists remain available even if another output fails.


##### Checking against a local list

```text
MD5SUM /CHECK
MD5SUM /CHECK B3:FILE.TXT
MD5SUM /CHECK B[1-3]:*.COM
MD5SUM /CHECK=REF.LST B[1-3]:
```

Bare CHECK looks for MD5SUM.LST in each target DU. It does not search other names or fall back to your logged DU. If no list is found, MD5SUM reports it and continues to the next selected DU. With no target operand, your logged DU is itself the target.

CHECK=REF.LST selects that exact filename independently in each target DU. It does not select a central reference for all targets. A DU qualifier, such as `/CHECK=A0:REF.LST`, is an error. Place a reference beside the files it describes and select that location.

The target filespec limits both existing files and reference names being checked. MD5SUM reports selected files absent from the reference and selected reference names whose files are missing. The reference itself is excluded from wildcard targets. Unselected filenames do not become failures merely because they occur elsewhere in the list. A malformed list still prevents an overall successful check.

Conventional MD5 entries contain no file size, so there is no size-only preliminary comparison. MD5SUM calculates and compares the digest. If a master contains several digests for the same name, one matching entry verifies the file; differing alternatives are identified separately. No second list is consulted for precedence. You remain responsible for organizing unrelated files that share a name.

Expect MATCH, MD5 MISMATCH, FILE NOT FOUND, FILE NOT LISTED, READ ERROR or LIST ERROR reports as appropriate. One combined summary follows all DUs, for example:

```text
1 file calculated; 1 list written.
12 verified; 1 failed; 2 missing; incomplete.
```

Zero secondary counters and per-DU total blocks are omitted. A successful check can end simply with `1 verified.` A check verifying no files is incomplete; it is never proof that everything is correct. Ctrl-C reports cancellation, discards uncommitted output and restores your original drive/user selection.


##### Exchanging lists with a host system

Export the target files without altering their stored bytes, and keep filename case consistent with the list. Saved CP/M lists may have trailing Ctrl-Z padding. If a host md5sum reader reports that padding as malformed input, remove only the trailing padding from the host copy of the list. Leave target-file padding intact: it contributes to the digest.

Some host readers require LF line endings or the two-space entry form. Convert those list details on the host if needed; target-file bytes must stay unchanged.

The common entry syntax permits exchange of these lists. MD5SUM does not reproduce every host command-line option or support host directory paths inside entries.

#### Examples

```text
B0:MD5SUM D0:*.COM
```

Calculate file digests. Substitute the locations and filenames appropriate to your session.

#### Errors/Troubleshooting

Check the operand grammar and the selected drive/user area. For disk failures, preserve the source and any reported recovery files before retrying. See the [shared system messages](#system-messages) for command lookup, media, configuration and extension diagnostics.

#### See Also

[file specifications](#file-specifications) · [system messages](#system-messages)


<a id="patch"></a>

### PATCH

#### Description

PATCH.COM is supplied on the Companion Utilities disk (normally C0). Apply a verified binary patch with guarded publication.

#### General Form

```text
PATCH patchfile [/INPUT=filespec] [/OUTPUT=filespec] [/VERBOSE]
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Read usage without patching files | `C0:PATCH /HELP` |

#### Detailed Reference

**PATCH 1.0 (003)** ships on the NOAH companion disk. With that disk in C:,
run `C0:PATCH /VER` to check your copy or `C0:PATCH /H` for help.

PATCH applies verified byte replacements from a patch instruction file to a
binary input file, producing a separate output. The original input remains
unchanged. Every expected byte must agree with the original before PATCH creates
any output. The patched copy retains the input's length and is read back in full
before success is reported.


##### Running PATCH

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
| `/H`, `/HELP` | Display help without file access. |
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


##### Writing a patch file

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


##### Verification context and overlapping ranges

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


##### Existing output files

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


##### Cancellation and protection

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


##### Historical patch notices

PATCH reads its native instruction language. It does not read DDT transcripts,
Digital Research notices, assembler source, Unix diff patches or DOS DEBUG
scripts directly. It does not patch system tracks or search for byte patterns.

Historical corrections may be distributed separately as verified native PAT
files, with the original notice and exact target version identified. Translating
and qualifying those files is separate from implementing PATCH.

#### Examples

```text
C0:PATCH /HELP
```

Read usage without patching files. Substitute the locations and filenames appropriate to your session.

#### Errors/Troubleshooting

##### Results and errors

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


#### See Also

[file specifications](#file-specifications) · [system messages](#system-messages)


<a id="stat"></a>

### STAT

#### Description

Displays information about disks, files, and logical devices, and provides supported facilities for examining or changing file attributes and device assignments. STAT.COM is supplied in A0 on both System disks.

#### General Form

```text
STAT [request]
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Inspect memory and maximum COM size | `STAT MEM` |
| Inspect free space | `STAT` |

#### Detailed Reference

STAT retains the familiar role of Digital Research's CP/M utility while adding support for BetterCP/M's extended drive/user specifications.


##### Basic Use

To examine the status of the current disk:

```text
A0>STAT
```

STAT displays disk information according to the supported CP/M conventions.

To examine a particular file:

```text
A0>STAT REPORT.TXT
```

A drive-qualified file specification can also be used:

```text
A0>STAT B:REPORT.TXT
```


##### Syntax and Status Reports

The supported forms are:

```text
STAT
STAT filespec [$S|$R/O|$R/W|$SYS|$DIR]
STAT d:
STAT d:=R/O
STAT DSK:
STAT d:DSK:
STAT USR:
STAT DEV:
STAT VAL:
STAT MEM
STAT CON:=device:
STAT RDR:=device:
STAT PUN:=device:
STAT LST:=device:
STAT target:
```

Here `d:` means a drive selection. Conventional operands also accept numeric user selectors such as `5:` and `C3:`. Temporary selections are restored before STAT returns. The alternatives inside square brackets on the filespec line are optional file options; type just the option you need, without those brackets or vertical bars.

In 1.1.1, STAT operands are case-insensitive, including drive letters: `STAT b:`
and `STAT B:` are equivalent. For 1.1, use uppercase drive letters. Bare STAT
lists logged-in drives under a `Logged-in drives:` heading; a drive-only
operand queries that drive directly. Warm boot resets the logged-in drive set,
so the list can change after a program exits through warm boot.


| Command | Information or action |
|---|---|
| `STAT` | Read/write status and free space for logged drives |
| `STAT B:` | Free space on B at the current user |
| `STAT DSK:` | Drive characteristics for logged drives |
| `STAT B:DSK:` | Drive characteristics for B, including record/block capacity and directory limits |
| `STAT USR:` | Current user and user areas containing files on the current drive |
| `STAT DEV:` | Current logical-device assignments |
| `STAT VAL:` | Valid file options and device assignments |
| `STAT B:=R/O` | Temporarily mark B read-only |

The drive read-only setting is cleared by the normal warm-start/reset path. STAT does not accept `B:=R/W`; use the normal reset procedure to clear the software lock. It does not override hardware write protection.


##### Memory Map

```text
A0>STAT MEM
```

`STAT MEM` displays the current memory map, including protected system regions and RSXs, the CCP and CPXs, transient space, and page zero. Address ranges and byte counts identify what occupies memory.

The final maximum-loadable-COM figure is rounded down to complete 128-byte load records. It can include the memory currently occupied by the reclaimable CCP and CPX command code. That figure describes how large a transient program can be loaded; it is not an additional free region to add to the map. Protected RSXs reduce that maximum. Use `RSX LIST` to identify optional services when investigating a memory shortage.


##### Extended Drive/User Selection

BetterCP/M extends STAT's file-inspection facilities to support explicit user areas and compound selections.

For example:

```text
A0>STAT B3:*.COM
```

examines matching files in drive B, user area 3.

To examine several user areas:

```text
A0>STAT B[3,5]:*.COM
```

To examine all user areas on drive B:

```text
A0>STAT B[-]:*.COM
```

Compound selections are also supported:

```text
A0>STAT [A0,C[3,5,7-11],5]:*.DAT
```

STAT processes the selected locations and identifies each result by its drive and user area.

Duplicate locations are visited only once.


##### Displaying File Sizes

STAT provides the `$S` option for displaying logical file sizes.

For example:

```text
A0>STAT B[3,5]:*.DAT $S
```

This examines matching files in the selected user areas and includes the additional size information.

The distinction between logical file size and allocated disk space is important. CP/M allocates storage in blocks, so a file's allocated space may exceed the amount of data it contains.


##### File Attributes

Use a file option to change attributes in one conventional drive/user location:

```text
A0>STAT REPORT.TXT $R/O
A0>STAT REPORT.TXT $R/W
A0>STAT B3:*.COM $SYS
A0>STAT B3:*.COM $DIR
```

`$R/O` sets read-only protection; `$R/W` clears it. `$SYS` sets the system attribute, while `$DIR` clears SYS so ordinary directory listings can show the file. Wildcards apply the change to all matching files and their extents. These operations do not provide an ARC-setting option.

Check the filespec before changing attributes, especially with wildcards. Disk write protection can prevent changes. In a `.SUB` source file, double each dollar sign, for example `STAT REPORT.TXT $$R/O`.


##### Logical Device Assignments

STAT examines and changes the live IOBYTE, which selects the logical console, reader, punch, and list devices:

```text
A0>STAT DEV:
A0>STAT LST:=CRT:
A0>STAT CRT:
A0>STAT VAL:
```

The second command maps list output to CRT. The third is an inverse query: it lists every logical device currently assigned to CRT, or reports that CRT is not assigned. Queries do not change assignments or test whether hardware is ready.

| Logical device | Accepted targets |
|---|---|
| `CON:` | `TTY:`, `CRT:`, `BAT:`, `UC1:` |
| `RDR:` | `TTY:`, `PTR:`, `UR1:`, `UR2:` |
| `PUN:` | `TTY:`, `PTP:`, `UP1:`, `UP2:` |
| `LST:` | `TTY:`, `CRT:`, `LPT:`, `UL1:` |

Several assignments may be supplied together, for example `STAT CON:=CRT: LST:=LPT:`. An inverse query accepts one target from this table, followed by a colon, with no additional operands. It reports matching logical devices in CON/RDR/PUN/LST order.

The available hardware routes depend on the BIOS. An accepted IOBYTE value does not create a device or guarantee that a particular interface is supported. `BAT:` selects the conventional batch console arrangement using reader input and list output where supported; it does not activate SUBMIT or XSUB.


##### Extended Selection Restrictions

BetterCP/M's compound drive/user selectors are supported for file inspection.

They are not accepted indiscriminately by every STAT operation.

In particular, extended selectors cannot be used with the conventional drive-wide operations or file-attribute modification forms.

For those operations, use the supported conventional single-location syntax.


##### STAT and CONFIG

STAT and CONFIG serve different purposes when managing device assignments.

**STAT changes the live IOBYTE.** Its changes affect the current operating environment.

**CONFIG manages the saved cold-boot IOBYTE.** Its saved value is established during a subsequent disk cold boot.

The two facilities complement one another.

For example, you can use STAT to test a supported device assignment before saving it as a startup default through CONFIG.


#### Examples

Examine the current disk:

```text
A0>STAT
```

Examine files in user area 3:

```text
A0>STAT B3:*.COM
```

Examine files across all user areas on drive B:

```text
A0>STAT B[-]:*.COM
```

Display file sizes for selected user areas:

```text
A0>STAT B[3,5]:*.DAT $S
```

For further information about drive/user specifications and file attributes, see [Chapter 4](Users-Guide.md#chapter-4).

#### Errors/Troubleshooting

Check the operand grammar and the selected drive/user area. For disk failures, preserve the source and any reported recovery files before retrying. See the [shared system messages](#system-messages) for command lookup, media, configuration and extension diagnostics.

#### See Also

[system messages](#system-messages) · [file specifications](#file-specifications)


<a id="command-environment-and-execution"></a>

## Command environment and execution


<a id="bye"></a>

### BYE

#### Description

Exit patched cpmsim. BYE.COM is supplied only on the cpmsim System disk. Finish and save your work before exiting.

#### General Form

```text
BYE [/Y]
BYE /VER
BYE /HELP
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Ask before exiting | `BYE` |
| Exit without confirmation | `BYE /Y` |

#### Detailed Reference

BYE exits the z80pack cpmsim emulator. It is supplied on the cpmsim system
disk and is specific to that platform.

```text
BYE [/Y]
BYE /VER
BYE /HELP
```

With no operational switch, BYE asks `Exit cpmsim? (Y/N) [N]: `. Press Y or y to
exit immediately. N, n, Enter, Escape or Ctrl-C cancels and returns to the
caller. Other keys repeat the prompt. No Enter is required after Y or N.

`/Y` bypasses confirmation, including in automated command sequences. Switches
are case insensitive and separated by spaces or TABs. Invalid arguments show
short syntax and return without prompting or shutting down. Repeated `/Y`
switches are accepted.

`/VER` displays utility identification. `/HELP` displays a compact reference.
These exact query tokens follow the common utility contract: they ignore other
arguments, never prompt or shut down, and `/HELP` takes precedence over `/VER`.

BYE requests shutdown by writing AAh and then 80h to cpmsim's hardware-control
port A0h. DI followed by HALT remains as a fallback. This does not invoke an OS
cache-flush service or save work belonging to another program.

#### Examples

```text
BYE
```

Ask before exiting. Substitute the locations and filenames appropriate to your session.

#### Errors/Troubleshooting

No, Enter, Escape or Ctrl-C cancels. BYE does not save another program's work or invoke a cache-flush service. It is not a Model 4 shutdown command.

#### See Also

[query conventions](#query-conventions)


<a id="cls-resident"></a>

### CLS — Resident

#### Description

Clear the console and home the cursor. Supplied by RCP.CPX.

#### General Form

```text
CLS
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Clear the display | `CLS` |

#### Detailed Reference


##### Syntax

```text
CLS
```


#### Examples

```text
A0>CLS
```

CLS clears the current display.

This is useful when the screen has become cluttered with directory listings, program output, or command messages.


The exact screen-clearing operation depends on the active console environment.

On systems using BetterCP/M's terminal-monitor facilities, the operation is performed through the appropriate display support.

The visible result is normally a cleared screen with the cursor positioned at the beginning of the display.

The underlying method may differ between supported computers and terminal environments.

For more information about terminal support, see [Chapter 9](Users-Guide.md#chapter-9).

#### Errors/Troubleshooting

Check the active console/backend/personality if the display does not clear correctly. Restore RCP with `CPX LOAD RCP` if the resident command is unavailable.

#### See Also

[CLS TRANSIENT](#cls-transient)


<a id="cls-transient"></a>

### CLS — Transient

#### Description

Clear the console and home the cursor. CLS.COM is buildable from matching source but is not selected System Disk content. This entry applies only after separately preparing and installing that file.

#### General Form

```text
CLS
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Clear the display | `:CLS` |

#### Detailed Reference


##### Syntax

```text
CLS
```


#### Examples

```text
A0>CLS
```

CLS clears the current display.

This is useful when the screen has become cluttered with directory listings, program output, or command messages.


The exact screen-clearing operation depends on the active console environment.

On systems using BetterCP/M's terminal-monitor facilities, the operation is performed through the appropriate display support.

The visible result is normally a cleared screen with the cursor positioned at the beginning of the display.

The underlying method may differ between supported computers and terminal environments.

For more information about terminal support, see [Chapter 9](Users-Guide.md#chapter-9).

#### Errors/Troubleshooting

Check the active console/backend/personality if the display does not clear correctly. A missing CLS.COM is expected on unmodified release media; use resident CLS.

#### See Also

[CLS RESIDENT](#cls-resident)


<a id="get"></a>

### GET

#### Description

Loads a file into memory without executing it. This command is built into the CCP and does not require RCP or a transient program.

#### General Form

```text
GET filename
GET address filename
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Load at the normal program origin | `GET D0:IMAGE.COM` |

#### Detailed Reference

GET is useful when examining or modifying program images, preparing machine-language routines for execution, or loading data into a particular memory location.

Unlike ordinary program execution, GET returns to the command prompt after loading the file.


##### Syntax

```text
GET filename
GET address filename
```

With one argument, GET loads the file beginning at address `0100H`.

With two arguments, the first specifies the hexadecimal memory address at which loading begins.


##### Examining Loaded Data

After loading a file, you can examine its contents with PEEK.

For example:

```text
A0>GET PROGRAM.COM
A0>PEEK 100
```

This displays memory beginning at address `0100H`.

You can also modify the loaded data with POKE.


##### Executing a Loaded Program

A program loaded at `0100H` can subsequently be executed with GO:

```text
A0>GET PROGRAM.COM
A0>GO
```

Alternatively, JUMP can transfer control to a specified address.


##### Memory Protection

GET checks whether the requested load would overwrite memory required by the active BetterCP/M command environment.

If the file cannot be loaded safely, GET rejects the operation.

This protection helps prevent accidental damage to resident operating-system components.

Nevertheless, GET is intended for users who understand the memory requirements of the programs or data being loaded.

#### Examples

Load a program at `0100H`:

```text
A0>GET PROGRAM.COM
```

Load a file at address `8000H`:

```text
A0>GET 8000 DATA.BIN
```

The address is hexadecimal.

Leading zeroes are optional.


#### Errors/Troubleshooting

Use only known memory contents and valid addresses. SAVE counts 256-byte pages in decimal; memory addresses and byte values use the syntax below. A malformed operand is rejected; an executed or modified arbitrary address can make the session unusable. Keep an unchanged program or media copy for recovery.

#### See Also

[GO](#go) · [JUMP](#jump) · [PEEK](#peek) · [POKE](#poke) · [SAVE](#save)


<a id="go"></a>

### GO

#### Description

Transfers control to address `0100H`, the conventional entry point for CP/M transient programs. This command is built into the CCP and does not require RCP or a transient program.

#### General Form

```text
GO [command tail]
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Run the loaded program | `GO` |

#### Detailed Reference

GO is useful when executing a program image that has already been loaded into memory.


##### Syntax

```text
GO [command tail]
```

The command tail is optional.


##### Using GO with GET

A common sequence is:

```text
A0>GET PROGRAM.COM
A0>GO
```

GET loads the program into memory.

GO then transfers control to it.

This allows a program to be loaded, examined, or modified before execution.


##### Relationship to JUMP

GO is equivalent to:

```text
JUMP 0100
```

Both transfer control to address `0100H`.

GO is provided as a convenient shorthand for the most common CP/M program entry point.


##### Program Environment

Before transferring control, BetterCP/M establishes the normal CP/M transient-program environment.

This includes the expected command tail, default File Control Blocks, and other program-entry conditions.

Ordinary CP/M programs therefore receive the familiar execution environment.


##### Caution

GO does not verify that memory at `0100H` contains a valid program.

If the memory contains unrelated data or an incomplete program image, execution may fail.

Use GO only when you know that an appropriate program has been loaded.

#### Examples

Execute the program currently loaded at `0100H`:

```text
A0>GO
```

Execute it with a command-line argument:

```text
A0>GO INPUT.DAT
```

The command tail is supplied to the program using the normal CP/M transient-program conventions.


#### Errors/Troubleshooting

Use only known memory contents and valid addresses. SAVE counts 256-byte pages in decimal; memory addresses and byte values use the syntax below. A malformed operand is rejected; an executed or modified arbitrary address can make the session unusable. Keep an unchanged program or media copy for recovery.

#### See Also

[GET](#get) · [JUMP](#jump) · [PEEK](#peek) · [POKE](#poke) · [SAVE](#save)


<a id="jump"></a>

### JUMP

#### Description

Transfers control to a specified memory address. This command is built into the CCP and does not require RCP or a transient program.

#### General Form

```text
JUMP address [command tail]
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Run at a chosen hexadecimal address | `JUMP 0100` |

#### Detailed Reference

JUMP extends the functionality of GO by allowing execution to begin at an address other than `0100H`.


##### Syntax

```text
JUMP address [command tail]
```

The address is hexadecimal.


##### Using JUMP with GET

JUMP can be used to execute a routine loaded at a nonstandard address.

For example:

```text
A0>GET 8000 ROUTINE.BIN
A0>JUMP 8000
```

This loads `ROUTINE.BIN` at address `8000H` and transfers control to that address.

The routine must be suitable for execution at the selected address.


##### Program Environment

Like GO, JUMP establishes the normal CP/M transient-program environment before transferring control.

This includes the standard command-tail and default FCB arrangements.


##### Address Range

JUMP accepts hexadecimal addresses from `0000H` through `FFFFH`.

However, **not every address is a valid or safe execution address**.

Some locations contain operating-system code, data, interrupt vectors, or other system structures.

Transferring control to an arbitrary address can cause the system to malfunction.

JUMP should therefore be used only when the contents and purpose of the target address are known.


##### Error Handling

If the address is missing or invalid, JUMP reports an error and returns to the command prompt.

It does not attempt to execute an invalid address specification.

#### Examples

Execute at `0100H`:

```text
A0>JUMP 100
```

Execute at `8000H`:

```text
A0>JUMP 8000
```

Execute at `0100H` with an argument:

```text
A0>JUMP 100 INPUT.DAT
```


#### Errors/Troubleshooting

Use only known memory contents and valid addresses. SAVE counts 256-byte pages in decimal; memory addresses and byte values use the syntax below. A malformed operand is rejected; an executed or modified arbitrary address can make the session unusable. Keep an unchanged program or media copy for recovery.

#### See Also

[GET](#get) · [GO](#go) · [PEEK](#peek) · [POKE](#poke) · [SAVE](#save)


<a id="peek"></a>

### PEEK

#### Description

Displays the contents of memory in hexadecimal and ASCII form. This command is built into the CCP and does not require RCP or a transient program.

#### General Form

```text
PEEK
PEEK address
PEEK first last
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Inspect the program origin | `PEEK 0100 011F` |

#### Detailed Reference

PEEK provides a convenient way to examine memory without modifying its contents. It is particularly useful when inspecting loaded programs, examining data structures, or checking the results of changes made with POKE.

The command can also be abbreviated to `P`.


##### Syntax

```text
PEEK
PEEK address
PEEK first last
```

Or, using the abbreviated form:

```text
P
P address
P first last
```

All addresses are hexadecimal.


##### Displaying Memory

To display memory beginning at address `0100H`, enter:

```text
A0>PEEK 100
```

PEEK displays 256 bytes beginning at the specified address.

The display includes hexadecimal byte values and their corresponding ASCII representations, making it possible to examine both machine-language instructions and ordinary character data.

For example:

```text
A0>P 8000
```

displays 256 bytes beginning at address `8000H`.


##### Displaying an Address Range

You can specify both the first and last addresses to display.

For example:

```text
A0>PEEK 100 1FF
```

This displays the inclusive range from `0100H` through `01FFH`.

The first address identifies the beginning of the range, while the second identifies its final byte.

PEEK does not wrap around from `FFFFH` to `0000H`.


##### Continuing a Memory Display

If you enter PEEK without an address:

```text
A0>PEEK
```

the first invocation begins at `0100H`.

Subsequent invocations continue from the byte following the previous display.

This allows you to examine consecutive regions of memory without repeatedly calculating addresses.

For example:

```text
A0>PEEK
A0>PEEK
A0>PEEK
```

displays successive portions of memory.


##### Paging Through Memory

PEEK supports interactive paging when displaying memory.

The following keys control navigation:

| Key | Action |
|---|---|
| Space | Display the next page |
| `.` | Display the next page |
| `>` | Display the next page |
| `,` | Display the previous page |
| `<` | Display the previous page |
| Ctrl-C | Return to the command prompt |

These controls allow you to move forward and backward through the displayed memory.


##### Using PEEK with GET

PEEK is especially useful after loading a program or data file with GET.

For example:

```text
A0>GET PROGRAM.COM
A0>PEEK 100
```

GET loads `PROGRAM.COM` into memory beginning at `0100H`.

PEEK then displays the first 256 bytes of the loaded image.

You can examine additional portions by specifying other addresses or continuing the display.


##### Using PEEK with POKE

PEEK can also be used to verify memory changes.

For example:

```text
A0>POKE 200 48 45 4C 4C 4F
A0>PEEK 200
```

The POKE command stores five bytes beginning at address `0200H`.

PEEK then displays the corresponding memory region.

The hexadecimal values represent the ASCII characters `HELLO`.


##### Using PEEK with GET and POKE

PEEK is particularly useful alongside the other resident memory commands.

For example:

```text
A0>GET PROGRAM.COM
A0>PEEK 100
A0>POKE 100 C3 00 80
A0>PEEK 100
```

This loads a program, examines its beginning, modifies three bytes, and displays the modified memory.

PEEK itself does not change memory.


##### Important Considerations

PEEK displays the contents of memory as they exist when the command executes.

It does not interpret the contents as program instructions or determine whether the data is meaningful.

Memory may contain executable code, program data, operating-system structures, or unused values.

PEEK itself does not modify memory, but the contents of some memory locations may change as programs or the operating system execute.

For disassembly and more advanced debugging operations, use an appropriate debugging utility such as DDT.

#### Examples

```text
PEEK 0100 011F
```

Inspect the program origin. Substitute the locations and filenames appropriate to your session.

#### Errors/Troubleshooting

Use only known memory contents and valid addresses. SAVE counts 256-byte pages in decimal; memory addresses and byte values use the syntax below. A malformed operand is rejected; an executed or modified arbitrary address can make the session unusable. Keep an unchanged program or media copy for recovery.

#### See Also

[GET](#get) · [GO](#go) · [JUMP](#jump) · [POKE](#poke) · [SAVE](#save)


<a id="poke"></a>

### POKE

#### Description

Stores hexadecimal byte values or literal text directly into memory. This command is built into the CCP and does not require RCP or a transient program.

#### General Form

```text
POKE address byte [byte ...]
POKE address "text
POKE address byte [byte ...] "text
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Write two hexadecimal bytes | `POKE 0100 00 C9` |

#### Detailed Reference

POKE provides a convenient way to modify memory without loading a separate debugger.

It can be used to patch a program image, enter small machine-language routines, or modify data that has been loaded with GET.

Unlike PEEK, **POKE changes memory contents**. Incorrect modifications can damage a loaded program or interfere with the operating system.


##### Syntax

```text
POKE address byte [byte ...]
POKE address "text
POKE address byte [byte ...] "text
```

The address and hexadecimal byte values are required in their respective forms.

The address specifies where writing begins.

Successive bytes are stored in consecutive memory locations.


##### Storing Hexadecimal Bytes

For example:

```text
A0>POKE 100 C3 00 80
```

stores three bytes beginning at address `0100H`:

| Address | Value |
|---|---|
| `0100H` | `C3H` |
| `0101H` | `00H` |
| `0102H` | `80H` |

These bytes form a Z80 absolute jump instruction to address `8000H`.

POKE stores the values exactly as specified. It does not interpret them as instructions while writing them.


##### Storing Text

POKE can also store literal text.

For example:

```text
A0>POKE 200 "Hello
```

stores the ASCII characters `Hello` beginning at address `0200H`.

A quotation mark introduces literal text. All remaining characters on the command line are stored as text.

A closing quotation mark is not required.


##### Combining Bytes and Text

You can combine hexadecimal byte values with literal text.

For example:

```text
A0>POKE 300 0D 0A "BetterCP/M
```

This stores a carriage return (`0DH`) and line feed (`0AH`), followed by the ASCII characters in `BetterCP/M`.

This is useful when constructing small data structures or preparing text containing control characters.


##### Examining the Results

Use PEEK to examine the memory after making a change.

For example:

```text
A0>POKE 200 "Hello
A0>PEEK 200
```

PEEK displays the modified memory, including the hexadecimal values and ASCII representation.


##### Modifying a Loaded Program

POKE can be used with GET and SAVE to modify a program image.

For example:

```text
A0>GET PROGRAM.COM
A0>POKE 120 00
A0>PEEK 120
A0>SAVE 10 MODIFIED.COM
```

This sequence:

1. Loads `PROGRAM.COM` into memory.
2. Changes the byte at address `0120H` to `00H`.
3. Displays the modified memory.
4. Saves ten 256-byte pages to `MODIFIED.COM`.

The example illustrates the procedure rather than a useful program modification. The address, replacement value, and number of pages must be appropriate to the actual program.


##### Input Validation

POKE checks the address and hexadecimal byte operands before modifying memory.

If an operand is invalid, the command rejects the operation without making a partial modification.

For example, an invalid hexadecimal byte does not cause POKE to write the preceding valid bytes and then stop.

This helps prevent accidental partial changes caused by mistyped commands.

However, POKE cannot determine whether a valid address and byte sequence are appropriate for the program being modified.


##### Memory Safety

POKE is intended for users who understand the memory locations they are changing.

Writing to the wrong address can corrupt program data, overwrite executable instructions, or interfere with operating-system structures.

A valid hexadecimal address is not necessarily a safe address to modify.

If you're experimenting with machine-language programs, work with known memory locations and keep copies of the original program files.

When modifying a loaded program, use PEEK to verify the changes before executing or saving it.


##### Using the Memory Commands Together

BetterCP/M provides a small collection of resident commands that can be used together for memory inspection, modification, loading, execution, and saving.

| Command | Purpose |
|---|---|
| GET | Load a file into memory |
| PEEK / P | Examine memory |
| POKE | Modify memory |
| GO | Execute at `0100H` |
| JUMP | Execute at a specified address |
| SAVE | Save memory to a file |

Together, these commands provide convenient facilities for simple memory-oriented tasks without requiring a separate debugger.

For more extensive debugging, including disassembly, breakpoints, and register examination, use a dedicated debugging utility such as DDT.

#### Examples

```text
POKE 0100 00 C9
```

Write two hexadecimal bytes. Substitute the locations and filenames appropriate to your session.

#### Errors/Troubleshooting

Use only known memory contents and valid addresses. SAVE counts 256-byte pages in decimal; memory addresses and byte values use the syntax below. A malformed operand is rejected; an executed or modified arbitrary address can make the session unusable. Keep an unchanged program or media copy for recovery.

#### See Also

[GET](#get) · [GO](#go) · [JUMP](#jump) · [PEEK](#peek) · [SAVE](#save)


<a id="save"></a>

### SAVE

#### Description

Saves a specified number of 256-byte memory pages to a disk file. This command is built into the CCP and does not require RCP or a transient program.

#### General Form

```text
SAVE pages filespec
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Save two 256-byte pages | `SAVE 2 D0:IMAGE.COM` |

#### Detailed Reference

SAVE is a core resident command retained from conventional CP/M.

It is particularly useful when working with programs or data that have been loaded or modified directly in memory.


##### Syntax

```text
SAVE pages filespec
```

The `pages` argument specifies the number of 256-byte pages to save.

The memory is saved beginning at address `0100H`, the conventional start of the CP/M Transient Program Area.


##### Calculating the Number of Pages

Each page contains 256 bytes.

To determine the number of pages required, divide the number of bytes by 256 and round upward.

For example:

| Bytes to save | Pages |
|---:|---:|
| 256 | 1 |
| 1,024 | 4 |
| 2,560 | 10 |
| 4,096 | 16 |
| 10,240 | 40 |

If the data does not occupy an exact number of pages, the final saved page includes any remaining bytes within that page.


##### Using SAVE with GET and POKE

SAVE can be used with BetterCP/M's memory commands.

For example, you might load a program with GET, modify several bytes with POKE, and then save the modified image under another filename.

```text
A0>GET PROGRAM.COM
A0>POKE 100 C3 00 80
A0>SAVE 10 MODIFIED.COM
```

This example illustrates the general procedure. The number of pages saved must be appropriate to the size of the program or data.

SAVE does not determine the logical size of the program automatically.


##### Resident Command

SAVE is implemented directly by the command processor.

It is not provided as an ordinary transient utility because loading a transient `SAVE.COM` could overwrite the very memory that SAVE is intended to preserve.


##### Important Considerations

SAVE writes the contents of memory as they exist when the command executes.

It does not determine whether those contents form a valid executable program.

If you save a memory region containing incomplete or unrelated data, the resulting file will contain that data.

Likewise, saving too few pages truncates the intended image, while saving too many pages includes additional memory contents.

#### Examples

Save ten pages:

```text
A0>SAVE 10 TEST.COM
```

This writes 2,560 bytes from memory beginning at `0100H` into `TEST.COM`.

Save forty pages to drive B:

```text
A0>SAVE 40 B:PROGRAM.COM
```

Save twenty pages to drive B, user area 3:

```text
A0>SAVE 20 B3:IMAGE.COM
```

BetterCP/M extends the conventional SAVE command by allowing drive/user-qualified destination file specifications.


#### Errors/Troubleshooting

Use only known memory contents and valid addresses. SAVE counts 256-byte pages in decimal; memory addresses and byte values use the syntax below. A malformed operand is rejected; an executed or modified arbitrary address can make the session unusable. Keep an unchanged program or media copy for recovery.

#### See Also

[GET](#get) · [GO](#go) · [JUMP](#jump) · [PEEK](#peek) · [POKE](#poke)


<a id="user-resident"></a>

### USER — Resident

#### Description

Select user 0–31 through the supplied RCP.CPX. No USER.COM is selected on the locked System disks.

#### General Form

```text
USER number
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Select user 17 | `USER 17` |

#### Detailed Reference

BetterCP/M retains the conventional CP/M USER command while extending the available range of user areas.


##### Syntax

```text
USER number
```

The number specifies a user area from 0 through 31.

For example:

```text
A0>USER 3
A3>
```

This selects user area 3 on drive A.

To select user area 17:

```text
A3>USER 17
A17>
```

The prompt changes to reflect the new user area.


##### Direct User-Area Selection

BetterCP/M also allows you to select a user area directly by entering its number followed by a colon.

For example:

```text
A0>3:
A3>
```

This is equivalent to:

```text
A0>USER 3
```

You can also select a drive and user area together:

```text
A3>B17:
B17>
```

This selects drive B, user area 17.


##### User Areas and File Access

Changing the current user area affects commands that do not explicitly specify another location.

For example, after selecting user area 3:

```text
A3>DIR
```

displays files in user area 3 on drive A.

To examine another user area without changing the current selection:

```text
A3>DIR B5:
```

The current drive and user area remain unchanged after the command.


##### Compatibility

The USER command is retained for compatibility with conventional CP/M usage.

BetterCP/M supports user areas 0 through 31, extending the traditional CP/M 2.2 range of 0 through 15.

USER is a resident command. There is no separate transient `USER.COM`.

For more information about drives and user areas, see [Chapter 4](Users-Guide.md#chapter-4).

#### Examples

```text
USER 17
```

Select user 17. Substitute the locations and filenames appropriate to your session.

#### Errors/Troubleshooting

Use a decimal user from 0 through 31. If RCP is unavailable, CCP navigation such as `17:` or `B17:` remains available.

#### See Also

[file specifications](#file-specifications) · [CPX](#cpx)


<a id="ver-resident"></a>

### VER — Resident

#### Description

Identify the running OS and subsystems. Supplied by RCP.CPX.

#### General Form

```text
VER
VER /V
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Identify the running system | `VER` |
| Show subsystem versions | `VER /V` |

#### Detailed Reference

VER is useful when checking the operating-system release, identifying the installed software, or reporting a problem.


##### Syntax

```text
VER
VER /V
VER /BANNER
```

The available forms provide different levels of information.


##### Displaying the System Version

Enter:

```text
A0>VER
```

VER displays the BetterCP/M system identification and release version.

This is the simplest way to determine which version of BetterCP/M is running.


##### Detailed Version Information

To display additional subsystem information:

```text
A0>VER /V
```

The `/V` option provides more detailed identification information about the operating-system environment.

This can be useful when comparing installations or determining whether a particular subsystem has been updated.

#### Examples

```text
VER
```

Identify the running system. Substitute the locations and filenames appropriate to your session.

#### Errors/Troubleshooting

Resident `VER /BANNER` reports `VER: Use :VER.`. Select `:VER /BANNER` explicitly. `/VER` identifies a utility; OS, subsystem, API and utility identities are independent.

#### See Also

[VER TRANSIENT](#ver-transient) · [query conventions](#query-conventions)


<a id="ver-transient"></a>

### VER — Transient

#### Description

Identify the running OS and subsystems. VER.COM is supplied on both System disks; the startup scripts explicitly invoke it for the banner.

#### General Form

```text
VER
VER /V
VER /BANNER
VER /VER
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Identify the running system | `:VER` |
| Show subsystem versions | `:VER /V` |
| Show the startup banner | `:VER /BANNER` |

#### Detailed Reference

VER is useful when checking the operating-system release, identifying the installed software, or reporting a problem.


##### Syntax

```text
VER
VER /V
VER /BANNER
```

The available forms provide different levels of information.


##### Displaying the System Version

Enter:

```text
A0>:VER
```

VER displays the BetterCP/M system identification and release version.

This is the simplest way to determine which version of BetterCP/M is running.


##### Detailed Version Information

To display additional subsystem information:

```text
A0>:VER /V
```

The `/V` option provides more detailed identification information about the operating-system environment.

This can be useful when comparing installations or determining whether a particular subsystem has been updated.


##### Displaying the Startup Banner

The transient VER utility provides the system identification banner used by the standard distribution's startup procedure.

Enter:

```text
A0>:VER /BANNER
```

The `/BANNER` option is provided by `VER.COM`.

If you attempt to use it with the resident command:

```text
A0>VER /BANNER
```

BetterCP/M reports:

```text
VER: Use :VER.
```

You can then invoke the transient utility explicitly.


##### Version Information for Individual Utilities

Most BetterCP/M utilities also support `/VER` to display their own version and build information.

For example:

```text
A0>:DIR /VER
```

identifies the transient DIR utility.

This is different from the VER command, which identifies the operating system itself.

For utility version conventions, see [Help and identities](#query-conventions).

#### Examples

```text
:VER
```

Identify the running system. Substitute the locations and filenames appropriate to your session.

#### Errors/Troubleshooting

Resident `VER /BANNER` reports `VER: Use :VER.`. Select `:VER /BANNER` explicitly. `/VER` identifies a utility; OS, subsystem, API and utility identities are independent.

#### See Also

[VER RESIDENT](#ver-resident) · [query conventions](#query-conventions)


<a id="configuration-disks-and-installation"></a>

## Configuration, disks, and installation


<a id="config"></a>

### CONFIG

#### Description

Examines and modifies BetterCP/M's system configuration, including startup commands, disk-drive definitions, disk formats, and the saved cold-boot IOBYTE. CONFIG.COM is supplied in A0 on both System disks.

#### General Form

```text
CONFIG
CONFIG /SHOW
CONFIG /DEFAULT
CONFIG /STARTUP="command"
CONFIG /STARTUP=""
CONFIG /IOBYTE=value
CONFIG /H
CONFIG /HELP
CONFIG /VER
CONFIG /PHYSICAL=n /field=value [/field=value ...]
CONFIG /LOGICAL=drive /PHYSICAL=n /FORMAT="description"
CONFIG /LOGICAL=drive /UNBIND
CONFIG /EDIT=drive /field=value [/field=value ...]
CONFIG /EDIT=drive /SLOT=n /ID=id /CODE=code
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Inspect without editing | `CONFIG /SHOW` |

#### Detailed Reference

CONFIG provides both an interactive menu and command-line operations.

It distinguishes between settings currently in use, changes prepared for saving, and settings already saved for subsequent cold boots.


##### Syntax

The principal forms are:

```text
CONFIG
CONFIG /SHOW
CONFIG /DEFAULT
CONFIG /STARTUP="command"
CONFIG /STARTUP=""
CONFIG /IOBYTE=value
CONFIG /H
CONFIG /HELP
CONFIG /VER
```

The disk-configuration forms are:

```text
CONFIG /PHYSICAL=n /field=value [/field=value ...]
CONFIG /LOGICAL=B /PHYSICAL=n /FORMAT="description"
CONFIG /LOGICAL=C /UNBIND
CONFIG /EDIT=B /field=value [/field=value ...]
CONFIG /EDIT=B /SLOT=n /ID=id /CODE=code
```

Use the slash-prefixed field names in the tables below. `B` and `C` are example logical drives; these operations accept B through D. Physical-profile selection accepts 0 through 3. The operation selector must come first. Names are case-insensitive and numeric values are unsigned decimal. Separate fields with whitespace. Do not combine these forms with `/SHOW`, startup/IOBYTE options, `/DEFAULT`, or `/VER`. Duplicate or unknown fields, extra operands and numeric overflow are rejected before changes begin.

`/H` and `/HELP` display the Utilities quick reference without reading disk
configuration or changing settings. An exact unquoted help token takes
precedence over `/VER` and other arguments. Query-looking text inside quoted
startup commands or format names remains data. Bare `CONFIG` opens the menus.


##### Interactive Configuration

Enter:

```text
A0>CONFIG
```

CONFIG displays a menu containing the available configuration operations:

```text
[ A ] Startup command

[ B ] Cold-boot IOBYTE

[ C ] Disk drive definitions
[ D ] Disk format definitions
[ E ] Create or edit a disk format

[ S ] Save current configuration on disk (SYSGEN)
```

Select the letter corresponding to the operation you want to perform.

Press Ctrl-C to leave the main menu.

CONFIG operates through the ordinary console and does not require a terminal-monitor extension.


##### Editing Startup and Numeric Fields

In the startup-command field and freeform decimal fields, typing inserts at the
cursor. Use Ctrl-S and Ctrl-D to move left and right, Ctrl-G to delete the
character under the cursor, and Ctrl-H/Backspace or DEL to delete the preceding
character. A reverse-video character marks the insertion point where supported;
otherwise an underscore marks it. Long command text scrolls within the line.

Enter submits the input. ESC or Ctrl-C cancels the field. On Model 4, CLEAR
supplies ESC; in trs80gp, use Home, or Fn-Left Arrow on a MacBook.

The startup replacement field starts empty. Empty Enter leaves the pending
command unchanged; use the startup menu's Clear operation to disable it.
Physical-drive byte fields keep their current value on empty Enter. Other
freeform numeric fields cancel an empty entry. Decimal syntax or overflow errors
leave the text available for correction; field-specific setting checks still
follow their existing rules.

Startup commands accept up to 126 characters and numeric fields up to five.
At the limit, additional insertion is refused while movement and deletion
remain available. These fields currently provide the basic editing keys above;
word movement, whole-line deletion and undo are not yet available here.
Editing does not save settings: use CONFIG's existing save operations and
confirmations when you want to change disk-boot defaults.


##### Displaying the Configuration

To examine the current configuration without changing it:

```text
A0>CONFIG /SHOW
```

This displays information about the active physical-drive profiles, logical-drive assignments, saved startup command, and saved drive defaults.

It also distinguishes between the live IOBYTE and the value saved for subsequent cold boots.

This is particularly useful when troubleshooting a configuration problem or determining whether temporary changes have been saved.


##### Startup Commands

BetterCP/M can execute a command automatically during a cold boot.

The standard distribution uses:

```text
SUBMIT STARTUP
```

This executes `STARTUP.SUB`, allowing the system to establish a preferred working environment.

To change the saved startup command:

```text
A0>CONFIG /STARTUP="SUBMIT STARTUP"
```

CONFIG requests confirmation before saving the change.

The new command takes effect during a subsequent cold boot. It is not executed immediately.

To disable automatic startup commands:

```text
A0>CONFIG /STARTUP=""
```

An empty startup command prevents BetterCP/M from automatically executing a command during cold startup.


##### Restoring the Default Startup Command

Enter:

```text
A0>CONFIG /DEFAULT
```

This prepares `SUBMIT STARTUP` as the pending startup command and opens the appropriate configuration menu.

The change is not automatically saved.

You can inspect or modify it before committing it to the system disk.

`/DEFAULT` affects the startup command; it does not restore every configuration setting to its original value.


##### Physical-Drive Configuration

CONFIG provides command-line facilities for changing physical-drive characteristics.

For example:

```text
A0>CONFIG /PHYSICAL=1 /TRACKS=80 /SIDES=2 /STEP=6
```

This requests an 80-track, double-sided configuration for physical drive 1, with the specified step timing.

`/PHYSICAL=n` must come first, followed by at least one field. Supply each field at most once; the field order is otherwise free. Unspecified fields retain their current values.

| Option | Accepted values | Units or meaning |
|---|---|---|
| `/PHYSICAL=` | 0–3 | Physical-drive index |
| `/TYPE=` | 5 or 8 | Drive type in inches |
| `/TRACKS=` | 35, 40, 77 or 80 | Track count |
| `/SIDES=` | 1 or 2 | Available sides |
| `/STEP=` | 6, 12, 20 or 30 | Milliseconds |
| `/SPINUP=` | 0–16 | Quarter-second units |
| `/SETTLE=` | 0–255 | Head-settling milliseconds |

Timing effects depend on the backend. CONFIG checks the proposed profile against A's current binding and rejects a change that cannot support the boot drive. After a successful update, incompatible non-system bindings are detached and their BDOS login state reset. If later cleanup fails, `Drive profile changed; binding cleanup incomplete.` means the profile did change and affected bindings need attention.

This form changes active settings only, requires no `DISK.FDB`, and neither prompts nor saves to disk. To retain the change across cold boot, use the separate save-all-current operation described below.


##### Logical-Drive Configuration

To associate a logical drive with a physical drive and disk format:

```text
A0>CONFIG /LOGICAL=C /PHYSICAL=1 /FORMAT="MM 80T DS DATA"
```

This assigns logical drive C to physical drive 1 using the named format.

The operands must appear in the order shown: `/LOGICAL=`, `/PHYSICAL=`, then `/FORMAT=`. Logical targets are B–D and physical indexes are 0–3. The quoted format must exactly match a catalogue display description, ignoring letter case and trailing space padding. It accepts 1–32 printable ASCII characters with at least one non-space character; quote escapes, prefixes, wildcards and row numbers are not accepted.

To edit the full release catalogue on the host, export the installed
`DISK.FDB` to BetterCP/M FDF v1 text. This preserves all 108 entries,
including the native 780K System layout:

```sh
python3 tools/fdfdecomp.py DISK.FDB my-formats.fdf
##### Edit my-formats.fdf; give each added FORMAT a unique ID and description.
python3 tools/fdfcomp.py my-formats.fdf my-disk.fdb
```

Install the new binary as `DISK.FDB` on a work disk and select the format by
its description. Keep a backup of the stock catalogue. Decompilation recovers
the descriptor fields; source comments are absent from the binary. The exporter
checks that the text reproduces the input bytes before saving it.

Named binding requires a valid `DISK.FDB`, using CONFIG's current-drive/A: catalogue lookup. Missing, corrupt, unknown, ambiguous or unsupported definitions leave the active binding unchanged.

CONFIG checks that the requested assignment is compatible with the selected drive.

To remove a logical-drive assignment:

```text
A0>CONFIG /LOGICAL=C /UNBIND
```

This disconnects logical drive C from its active assignment without erasing the disk.

BetterCP/M protects drive A from binding, unbinding and format edits. `/UNBIND` requires no catalogue. Successful binding/unbinding resets only the selected drive's BDOS login state. These operations change active settings without saving, formatting or erasing media; use save-all-current to make them cold-boot defaults.


##### Editing Disk-Format Definitions

CONFIG provides facilities for editing the characteristics of an active disk-format assignment.

For example:

```text
A0>CONFIG /EDIT=B /CKS=16
```

`/EDIT=B` through `/EDIT=D` must come first and requires at least one scalar or slot change. Scalar fields may follow in any order, once each. CONFIG starts from the active 64-byte binding, merges the named changes privately, and submits one validated update.

| Field | Meaning | Decimal storage range |
|---|---|---|
| `/PHYSICAL=` | Physical-drive index in the binding | 0–255; final binding must select 0–3 |
| `/SPT=` | 128-byte records per track | 0–65535 |
| `/BSH=`, `/BLM=`, `/EXM=` | Block shift, block mask, extent mask | 0–255 each |
| `/DSM=`, `/DRM=` | Last allocation-block number, last directory-entry number | 0–65535 each |
| `/AL0=`, `/AL1=` | Directory allocation masks | 0–255 each |
| `/CKS=`, `/OFF=` | Directory check size, reserved tracks | 0–65535 each |
| `/CYLINDERS=`, `/SECTORS=` | Cylinders, physical sectors per track | 0–255 each |
| `/SIZE=`, `/FLAGS=`, `/SIZEMAP=` | Maximum sector-size code, format flags, explicit size-map flag | 0–255 each |

These are storage limits, not a promise that every value or combination is valid. The physical geometry and backend rules still apply. Start with a valid binding; an unbound drive needs a complete valid definition before it can be used. Rejection before commit leaves active settings unchanged. A successful edit resets only that drive's BDOS login state.

To edit one sector-map entry:

```text
A0>CONFIG /EDIT=B /SLOT=1 /ID=200
A0>CONFIG /EDIT=B /SPT=35 /SLOT=1 /CODE=0
```

| Option | Accepted values | Meaning |
|---|---|---|
| `/SLOT=` | 1–32 | One-based slot in physical sector order |
| `/ID=` | 0–255 | Physical sector ID for that slot |
| `/CODE=` | 0–3 | Packed size code: 0=128, 1=256, 2=512, 3=1024 bytes |

A slot requires `/ID=`, `/CODE=`, or both. Neither value is accepted without `/SLOT=`. One slot is edited per invocation; scalar fields may accompany it after `/EDIT=`. Other slots and unspecified fields are preserved. The first explicit size edit seeds the other slots from the current uniform size. Duplicate IDs and inconsistent record/sector geometry are rejected. The examples show syntax; use values appropriate to the actual format.

Explicit size maps require `FDF.RSX`'s checked normalization service before applying the binding. FDF is separately buildable and is not selected System Disk content; install a compatible `A0:FDF.RSX` and load it with `RSX LOAD FDF` when this service is needed. Missing support or invalid maps leave the active binding unchanged.

These commands need no catalogue and make active changes without a confirmation or disk save. **Changing a binding definition does not format the disk.** An incorrect definition can make existing media inaccessible. Use the separate save-all-current operation to preserve validated changes across cold boot.


##### Saved IOBYTE

BetterCP/M retains CP/M's IOBYTE mechanism for selecting logical character devices.

STAT changes the live IOBYTE, while CONFIG can save a value for subsequent disk cold boots.

For example:

```text
A0>CONFIG /IOBYTE=85
```

The value is an unsigned decimal byte, 0–255.

CONFIG requests confirmation before saving it.

This operation does not change the IOBYTE currently in use.

The selected device assignments must be supported by the computer's BIOS.


##### Saving Configuration Changes

CONFIG distinguishes between saving pending cold-boot changes and saving all current settings as the new startup defaults.

For example, you may have temporarily changed a drive assignment while also preparing a new startup command.

Saving only the pending startup change allows you to retain your existing saved drive configuration.

Saving all current settings makes the active configuration the new startup default.

From the main menu choose **S**, then:

```text
[ A ] Save pending cold-boot changes only
[ B ] Save all current settings as startup defaults
BREAK (^C) returns without saving.
```

Choose **A** to retain saved drive defaults while saving pending cold-boot changes. Choose **B** to capture the active physical profiles and logical bindings as defaults as well. Follow the confirmation before the disk write. Active CLI disk changes survive leaving CONFIG but are lost on cold boot unless explicitly saved through **S**, **B**; they are not invocation-private pending edits.

CONFIG verifies saved configuration writes and reports failures.

**Keep a backup of a working system disk before making significant changes to saved configuration information.**


##### Version Information

Enter:

```text
A0>CONFIG /VER
```

CONFIG displays its version and build identification without modifying the system.

`/VER` ignores other command-line arguments.


##### Limitations

CONFIG is not a general-purpose preferences editor.

BetterCP/M 1.0 does not use CONFIG to manage resident extensions, terminal personalities, keyboard mappings, or clock providers.

Those facilities are managed through their respective commands and extensions.

For an introduction to configuration procedures, see [Chapter 7](Users-Guide.md#chapter-7).

#### Examples

```text
CONFIG /SHOW
```

Inspect without editing. Substitute the locations and filenames appropriate to your session.

#### Errors/Troubleshooting

With ANSISCRN/ANSI active, keep the host terminal at least 80 columns by 24 rows with a normal full-screen scrolling region. If newly drawn output is garbled after resizing, exit CONFIG normally, enlarge the window and restart it. The frozen launcher does not enforce this; see [terminal-size erratum](../releases/1.0-ERRATA.md#ansi-host-terminal-size).

##### Configuration Messages

CONFIG reports errors involving startup settings, drive definitions, disk formats, and saved configuration information.

###### Invalid Configuration Value

**Meaning:** A requested configuration value is outside its permitted range or is not supported by the selected field.

For example, a physical-drive profile may specify an unsupported number of tracks or sides.

**What to do:** Check the accepted values in the CONFIG reference.

Do not assume that a value accepted by one platform is suitable for another.

###### Incompatible Drive Assignment

**Meaning:** The requested disk-format definition is incompatible with the selected physical drive.

**What to do:** Verify the drive's physical characteristics and the disk-format definition.

A format that requires more tracks or sides than the drive supports cannot be assigned safely.

###### `Drive profile changed; binding cleanup incomplete`

**Meaning:** CONFIG changed a physical-drive profile but could not complete all associated logical-binding checks or adjustments.

The physical profile change has already occurred.

**What to do:** Examine the affected logical-drive assignments and correct any incompatible bindings.

Do not assume that the previous configuration remains completely intact.

###### Configuration Verification Failure

**Meaning:** CONFIG could not verify the installed system information needed for the requested configuration operation.

This can occur when the system image is damaged or CONFIG does not match the installed operating-system build.

**What to do:** Use the CONFIG utility supplied with the corresponding BetterCP/M system build.

If necessary, restore a known working system image.

###### Save Failure

**Meaning:** CONFIG could not successfully write or verify the requested saved configuration.

**What to do:** Check the disk and follow the reported recovery instructions.

A failed save should not be treated as evidence that the new configuration will be available after a cold boot.

For additional information, see [Section 16.1](#config), *CONFIG*.

Check the operand grammar and the selected drive/user area. For disk failures, preserve the source and any reported recovery files before retrying. See the [shared system messages](#system-messages) for command lookup, media, configuration and extension diagnostics.

#### See Also

[system messages](#system-messages) · [file specifications](#file-specifications)


<a id="dup"></a>

### DUP

#### Description

Formats disks, copies entire disks, and checks disks for physical read errors. DUP.COM is supplied in A0 on both System disks.

#### General Form

```text
DUP
DUP /FORMAT drive:
DUP /COPY source: destination:
DUP /CHECK drive:
DUP /VER
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Open the disk utility menu | `DUP` |

#### Detailed Reference

DUP is BetterCP/M's disk-management utility. Unlike the COPY command, which operates on individual files, DUP works directly with the physical organization and contents of a disk.

It provides three principal operations:

| Operation | Purpose |
|---|---|
| FORMAT | Prepare a disk using its assigned disk format |
| COPY | Copy the contents of one disk to another |
| CHECK | Examine a disk for unreadable sectors |

All three operations are available through DUP's interactive menu or directly from the command line.

**Formatting and disk copying can destroy existing data.** Always verify the selected drives before confirming either operation.


##### Syntax

```text
DUP
DUP /FORMAT drive:
DUP /COPY source: destination:
DUP /CHECK drive:
DUP /VER
```

For example:

```text
A0>DUP
A0>DUP /FORMAT B:
A0>DUP /COPY A: B:
A0>DUP /CHECK C:
```

The command-line forms use the same operations, validations, and safeguards as the interactive menu.

There is no command-line option for bypassing destructive-operation confirmations.


##### Interactive Operation

To start DUP interactively, enter:

```text
A0>DUP
```

DUP displays its main menu:

```text
A  Format a disk
B  Copy a disk
C  Check a disk for errors
```

Select the desired operation by entering its letter.

DUP then asks for the appropriate drive or drives.

Press Ctrl-C to exit the main menu. At a drive-selection prompt, Ctrl-C returns to the menu.

The current DUP interface supports logical drives A through D.


##### Drive and Format Selection

DUP uses the disk-format definition already assigned to each logical drive.

It does not provide a separate disk-format selection menu.

If you need to change a drive's format, use CONFIG before starting DUP.

For example:

```text
A0>CONFIG
```

You can then select the appropriate disk format and associate it with the desired logical drive.

DUP uses that assignment when formatting, copying, or checking the disk.

The available formats and operations depend on the computer's BIOS and disk hardware.

A format listed in the system's catalog is not necessarily supported for every operation on every platform.

DUP reports unsupported operations rather than substituting another format.


##### Protected System Drive

BetterCP/M protects physical drive 0 against destructive DUP operations.

Physical drive 0 cannot be used as the destination for FORMAT or COPY.

This protection follows the physical drive even if logical drive letters have been reassigned.

The protected drive may still be read by CHECK or used as the source of a disk-copy operation.

This safeguard helps prevent accidental destruction of the running system disk.


##### Formatting a Disk

To format a disk interactively, start DUP and select option A.

DUP asks you to identify the logical drive to format.

Alternatively, enter:

```text
A0>DUP /FORMAT B:
```

This requests formatting of drive B using its currently assigned format.

DUP validates the drive and format before proceeding.

If the operation is supported, it displays a warning that the destination disk's contents will be destroyed and requests confirmation.

Only `Y` proceeds.

**Formatting destroys the previous contents of the destination disk.**

Make sure the correct disk is inserted and that its existing contents are no longer needed.


###### Format Verification

DUP verifies formatting by reading back the formatted tracks.

If formatting and verification complete successfully, DUP reports the number of tracks processed and displays:

```text
Format complete.
```

If a write or verification error occurs, DUP stops the operation and reports the problem.

An interrupted format may leave the disk only partly formatted.

Do not treat such a disk as ready for normal use.


###### Interrupting Formatting

Ctrl-C can interrupt formatting between disk operations.

An operation already in progress may finish before the interruption takes effect.

If formatting is interrupted, the destination disk may require formatting again before it can be used reliably.


##### Copying a Disk

DUP's COPY operation duplicates the contents of an entire disk.

Unlike the file-oriented COPY command, it copies the sector data represented by the source disk's format, including system areas, directories, file data, and unused space.

This makes it useful for preparing duplicate disks and maintaining complete disk backups.

To copy a disk interactively, start DUP and select option B.

DUP asks for the source and destination drives.

Alternatively, enter:

```text
A0>DUP /COPY A: B:
```

This requests a copy from drive A to drive B.

The source is read, while the destination is written.

**The destination's previous contents will be replaced.**


###### Two-Drive Requirement

DUP requires two different physical drives for disk copying.

It does not support copying between two disks by repeatedly exchanging them in a single drive.

The destination must also satisfy the system's drive-protection restrictions.

In particular, physical drive 0 cannot be used as the destination.


###### Copying Between Different Formats

DUP examines the format assignments of the source and destination.

If they match, DUP can copy the source without first reformatting the destination.

If they differ, DUP reports that the destination will be formatted to match the source.

The operation proceeds only if the required formatting and copying operations are supported.

DUP requests confirmation before replacing the destination's contents.

Check both the logical and physical drive assignments before proceeding.


###### Copy Verification

DUP verifies copied data by reading it back from the destination and comparing it with the source data.

A successful operation reports:

```text
Copy complete; destination verified.
```

This indicates that the data copied by DUP has been verified.

If a read, write, or comparison error occurs, DUP reports the failure.

An interrupted or failed copy may leave the destination partly written.

Do not rely on such a disk as a complete backup.


###### What DUP Copies

DUP copies the sector contents represented by the source disk's configured format.

This includes the system area, directory information, file data, and unused disk space.

It is not a magnetic flux-level copying utility.

It does not reproduce physical characteristics outside the represented sector data, such as weak sectors or special deleted-data address marks.

For ordinary BetterCP/M and compatible CP/M disks, the operation provides a verified sector-data copy.


###### Temporary Format Changes

When copying between different disk formats, DUP may temporarily change the destination's active format assignment.

It restores the previous assignment when the operation completes.

However, restoring the assignment does not restore the destination disk's former physical format.

After copying, use CONFIG to assign the copied format before accessing the destination normally.

If you intend to use that format regularly, save the appropriate configuration as the new startup default.


##### Checking a Disk

DUP's CHECK operation examines a disk for physical read errors without modifying its contents.

It is useful when investigating suspected media problems, checking an unfamiliar disk, or determining whether the sectors of a disk can be read reliably.

To check a disk interactively, start DUP and select option C.

DUP asks you to select the drive to examine.

Alternatively, enter:

```text
A0>DUP /CHECK B:
```

This checks the disk in drive B using its currently assigned format.

Unlike FORMAT and COPY, CHECK does not require confirmation because it performs no writes.


###### What CHECK Examines

CHECK reads the sectors represented by the disk-format definition assigned to the selected drive.

If a sector cannot be read successfully, DUP reports the error and its location.

Ordinary read errors do not necessarily stop the check. DUP continues examining the remaining sectors whenever it can safely do so.

When a physical sector contains several logical CP/M records, an unreadable sector is counted once rather than once for each record it contains.


###### Check Results

When CHECK completes, DUP displays:

```text
Check complete. Unreadable sectors: n
```

The value of `n` indicates the number of physical sectors that could not be read successfully.

For example:

```text
Check complete. Unreadable sectors: 0
```

indicates that all sectors examined during the check were readable.

A nonzero count indicates that one or more sectors could not be read.


###### What CHECK Does Not Do

CHECK examines physical readability. It does not repair disks or validate the logical consistency of the filesystem.

In particular, CHECK does not:

- Repair unreadable sectors.
- Reconstruct damaged files or directories.
- Restore deleted files.
- Compare the disk with another disk.
- Verify that individual files contain the expected data.

A disk can pass CHECK while still containing damaged or incorrect files.

If important data may have been corrupted, compare it with a known good copy or restore it from a backup.


###### Interrupting a Check

Press Ctrl-C to interrupt CHECK.

Because CHECK performs no writes, interrupting it does not change the disk.

DUP reports:

```text
Check stopped. No disk contents changed.
```

An interrupted check is incomplete and should not be treated as evidence that the entire disk is readable.


###### Drive Not Ready

If DUP reports that a drive is not ready, check that the correct disk is inserted and that the drive is available.

On an emulator, verify that the appropriate disk image is attached.


###### Write Protection

If a destination disk is write-protected, DUP cannot format it or write copied data to it.

Check the disk's write-protection setting before retrying.

Do not remove write protection unless you're certain the destination disk is the one you intend to modify.


###### Unsupported Operations

Some disk formats can be described by BetterCP/M's format catalog but cannot be formatted or copied using a particular hardware backend.

DUP reports unsupported operations rather than silently substituting another format.

If an operation is rejected, examine the drive configuration and consult the platform documentation.


###### Interrupted Operations

DUP recognizes Ctrl-C during physical disk operations.

An operation already in progress may finish before the interruption takes effect.

The consequences depend on the operation:

| Operation | Effect of interruption |
|---|---|
| FORMAT | Destination may be partly formatted |
| COPY | Destination may be partly written |
| CHECK | Operation stops without changing disk contents |

An interrupted FORMAT or COPY should be repeated from a reliable source after the cause of the interruption has been corrected.


##### Restoring Temporary Drive Assignments

When DUP temporarily changes a destination drive's format assignment during copying, it attempts to restore the previous assignment before returning to the command prompt.

If restoration fails, DUP displays:

```text
Cannot restore destination configuration. Press a key to retry.
```

Press a key to retry the restoration.

DUP retains the information needed to restore the previous assignment and does not knowingly return to normal operation while the temporary assignment remains installed.

Do not reset the computer merely to dismiss this message. Follow the recovery prompt unless a hardware failure makes further recovery impossible.


##### Memory Requirements

DUP requires approximately 51K of available transient program memory.

If resident extensions have reduced the available TPA below this requirement, DUP reports insufficient memory and does not begin the requested operation.

You may be able to recover the required memory by unloading resident extensions that are no longer needed.

For information about managing extensions, see [Chapter 8](Users-Guide.md#chapter-8).


##### Version Information

To display DUP's version and build identification, enter:

```text
A0>DUP /VER
```

DUP displays its identification and returns to the command prompt without performing a disk operation.


#### Examples

Start the interactive disk utility:

```text
A0>DUP
```

Format drive B:

```text
A0>DUP /FORMAT B:
```

Copy the contents of drive A to drive B:

```text
A0>DUP /COPY A: B:
```

Check drive C for unreadable sectors:

```text
A0>DUP /CHECK C:
```

Display version information:

```text
A0>DUP /VER
```

For an introduction to disk formats, system disks, and backup procedures, see [Chapter 10](Users-Guide.md#chapter-10), *Working with Disks*.

#### Errors/Troubleshooting

##### DUP Messages

DUP reports errors encountered while formatting, copying, and checking disks.

###### `Format complete.`

**Meaning:** DUP completed the requested formatting operation and its verification.

This is a successful completion message.

###### `Copy complete; destination verified.`

**Meaning:** DUP copied the represented sector contents and verified the destination against the source data.

This is a successful completion message.

###### `Check complete. Unreadable sectors: n`

**Meaning:** DUP completed a physical readability check.

The number `n` identifies the unreadable physical sectors encountered.

For example:

```text
Check complete. Unreadable sectors: 0
```

indicates that the examined sectors were readable.

It does not establish that the filesystem or individual files are logically correct.

###### `Format aborted. Disk is only partly formatted.`

**Meaning:** Formatting was interrupted after the operation began.

The destination disk may not be usable until it is formatted again.

**What to do:** Correct the cause of the interruption and repeat formatting when safe.

###### `Operation stopped. Destination may be partly written.`

**Meaning:** A disk-copy operation was interrupted.

The source remains unchanged, but the destination may contain only part of the intended copy.

**What to do:** Do not rely on the destination as a complete backup. Repeat the operation from a reliable source.

###### `Check stopped. No disk contents changed.`

**Meaning:** A disk check was interrupted.

CHECK is read-only, so the disk was not modified by the operation.

However, the check is incomplete.

###### `Cannot restore destination configuration. Press a key to retry.`

**Meaning:** DUP could not restore a temporary destination-drive assignment after a disk-copy operation.

DUP retains the information required for restoration and requests another attempt.

**What to do:** Follow the prompt and retry.

Avoid resetting the system merely to dismiss the message, since the temporary configuration may still be active.

###### Disk Error Status

DUP may report a numeric disk status together with the affected cylinder, side, sector, or record.

The following status information is useful when interpreting those reports.

| Status | Meaning |
|---|---|
| `1` | Request failed or drive did not respond |
| `2` | Unsupported operation or disk address |
| `FEh` | Read-back data did not match |
| Bit 7 | Drive not ready |
| Bit 6 | Disk write-protected |
| Bit 4 | Sector or track not found |
| Bit 3 | CRC error |
| Bit 2 | Data transfer failed |
| Other | Disk I/O failure |

The bit descriptions identify conditions reported through the disk interface. They are not necessarily mutually exclusive.

For additional information, see [Section 16.4](#dup), *DUP*.

##### Errors and Recovery

DUP reports errors encountered during disk operations.

These may include a drive that is not ready, write protection, missing sectors, read errors, unsupported operations, or verification failures.

Where possible, DUP identifies the physical location associated with the error.

For example, it may report the cylinder, side, sector, or record involved.


###### Read and Verification Errors

A read error indicates that DUP could not obtain the requested data reliably.

A verification error indicates that data read back from the destination did not match the expected contents.

For FORMAT and COPY, errors that make continued operation unsafe cause DUP to stop.

The destination may be incomplete and should not be treated as successfully prepared.


#### See Also

[system messages](#system-messages) · [file specifications](#file-specifications)


<a id="fdb"></a>

### FDB

#### Description

Edit and inspect disk-format catalogues using locked FDB 1.0 (001). FDB.COM and its matching FDBVIEW.OVL are supplied in A0 on both System disks. The current development 1.01 workbench is outside this reference.

#### General Form

```text
FDB
FDB file.FDB
FDB in.FDB out.FDF
FDB in.FDF out.FDB
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Show help without opening files | `FDB /HELP` |
| Export a catalogue | `FDB DISK.FDB ROUND.FDF` |

#### Detailed Reference

FDB.COM and its matching FDBVIEW.OVL ship in user 0 on both System disks,
with CONFIG.COM and the 108-entry DISK.FDB. Copy both FDB files into the same
drive and user area when using a work disk. The viewer must match the COM;
missing or damaged viewers are refused without changing pending work.

`FDB /VER` displays the component identity and compact BetterCP/M Utilities
identification. `FDB /H` and `FDB /HELP` display the same short help screen.
These exact tokens are case-insensitive, accept space or TAB separators, and
ignore other arguments. Help takes precedence over `/VER`. Queries return
without opening a catalogue, changing drives/users, or setting up the console;
they also work in the normal Model 4 50 KiB configuration. Longer tokens such
as `/VERIFY` and `/HELPER` are not queries.

The help screen lists the positional command forms as well as the switches:

| Command | Action |
| --- | --- |
| `FDB` | Open DISK.FDB in the workbench. |
| `FDB file.FDB` | Open a named catalogue in the workbench. |
| `FDB in.FDB out.FDF` | Export a catalogue as FDF text. |
| `FDB in.FDF out.FDB` | Compile FDF text to a catalogue. |

Listing, comparison, editing, drive application, and selective import/export
are interactive workbench operations.

The interactive workbench needs the standard 53 KiB TPA. On Model 4, the
normal startup loads screen personalities; before starting FDB, release them:

```
RSX UNLOAD ADM3A
```

After quitting FDB, run `SUBMIT STARTUP` with the unmodified shipped startup
script, or cold-boot, to restore the normal console. That script loads integrated ADM3A as one queued sequence before clearing the screen. If your startup
script is customized, use your normal console startup sequence. If other
extensions also consume memory, unload unneeded extensions or use a clean
boot. FDB refuses insufficient memory without changing files.

Run `FDB` to open the working catalogue. F opens a catalogue; N starts an empty
one. I imports one definition or an entire .FDB or .FDF. L lists entries with
filtering and paging. D displays one format; P compares independent catalogue,
editor or active-drive sources. Pages 1–4 show geometry, sector maps, CP/M
parameters and effective layout. Q returns from a viewer or menu; BREAK cancels
fields or returns while preserving the working format.

A captures B–D into the editor; B loads a named catalogue entry; C starts a
blank definition; E resumes pending work. Edit related fields, inspect the
result and press V to validate. S offers applying to B–D, putting the working
format in the catalogue, or writing the catalogue. Applying changes the active
drive only; it does not format media or save cold-boot defaults. Cylinder
formats retain catalogue units, with equivalent runtime units used when needed.
Drive A is protected. Confirmation is required before application.

O exports one or all entries to .FDB or .FDF. Exporting one entry into an
existing catalogue preserves unrelated entries. S saves the complete working
catalogue. Review the displayed destination and replacement confirmation.
Replacement writes and verifies a temporary file before backup/rename. Keep at
least 10 KiB and two directory entries free for a maximum-size catalogue
replacement, in addition to the existing file. On failure, retain any .BAK or
.$$$ recovery files until the original or verified replacement is recovered.
Use a writable copy of release media for edits.

The command form `FDB DISK.FDB ROUND.FDF` decompiles a catalogue;
`FDB ROUND.FDF ROUND.FDB` compiles it. An unsupported required extension or a
lossy export is refused. CONFIG uses the catalogue on the current drive or A:;
use `/LOGICAL=B /PHYSICAL=1 /FORMAT="display name"` to bind a supported format
by name. The physical drive's declared track/side capabilities must fit it.

For Model 4 System installation, follow the
[qualified named-binding procedure](../platform/MODEL4-SHIPPED-INSTALLATION.txt).
The workbench does not itself install a system or format media.

#### Examples

```text
FDB /HELP
```

Show help without opening files. Substitute the locations and filenames appropriate to your session.

#### Errors/Troubleshooting

FDB 1.01 uses the grouped main menu. Follow its displayed choices and use Q or BREAK to exit. The older Working catalogue/Choice presentation belongs to locked 1.0 binaries. Keep the viewer matched to the shipped FDB.COM.

Interactive FDB needs the unloaded 53K environment. On Model 4 unload ADM3A and any separately loaded backend. After FDB exits, restore with the unmodified `SUBMIT STARTUP` or cold boot. Queries work at normal startup allocation. Keep the matching viewer and retain any reported .BAK/.$$$ files after save failures.

#### See Also

[CONFIG](#config) · [DUP](#dup) · [SYSGEN](#sysgen)


<a id="sysgen"></a>

### SYSGEN

#### Description

Installs BetterCP/M onto a prepared system disk or saves an installed operating system as a system-image file. SYSGEN.COM is supplied in A0 on both System disks.

#### General Form

```text
SYSGEN
SYSGEN source: destination:
SYSGEN [drive:]package destination:
SYSGEN source: [drive:]package
SYSGEN source:
SYSGEN /VER
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Export the installed system | `SYSGEN A: D:BACKUP.SYS` |

#### Detailed Reference

SYSGEN is used when preparing a bootable BetterCP/M disk, replacing an installed operating system, or preserving a working system configuration.

Unlike DUP, which can format and copy entire disks, SYSGEN works specifically with the operating system's reserved system area.

It can obtain the operating system from another bootable disk or from a `SYSTEM.SYS` package.

SYSGEN also provides the reverse operation: reading the installed operating system from a disk and saving it as a package file for later use.

**SYSGEN does not format disks or copy ordinary files.** It installs or saves the operating system itself.


##### Syntax

BetterCP/M 1.0 supports the following forms:

```text
SYSGEN
SYSGEN source: destination:
SYSGEN [drive:]package destination:
SYSGEN source: [drive:]package
SYSGEN source:
SYSGEN /VER
```

The principal operations are:

| Form | Operation |
|---|---|
| `SYSGEN` | Install from drive A, prompting for a destination |
| `SYSGEN A: B:` | Install from one system disk onto another |
| `SYSGEN SYSTEM.SYS B:` | Install from a system-image package |
| `SYSGEN A:` | Save the installed system from A as `SYSTEM.SYS` |
| `SYSGEN A: B:BACKUP.SYS` | Save the installed system under a specified filename |
| `SYSGEN /VER` | Display version information |

Source drives may be A through D. Installation destinations may be B through D, subject to physical-drive restrictions.


##### Interactive Installation

To start SYSGEN interactively, enter:

```text
A0>SYSGEN
```

SYSGEN uses drive A as the source system and prompts:

```text
Destination drive [ B - D ], or BREAK (^C) to exit:
```

Select the destination drive.

For example, entering `B` requests installation onto drive B.

SYSGEN then examines the source and destination to determine whether the operation can be performed safely.

If the destination is suitable, SYSGEN displays the installation details and requests confirmation before writing.

Press Ctrl-C at the destination prompt to exit without modifying any disk.


##### Installing from Another System Disk

To specify both drives directly, use:

```text
SYSGEN source: destination:
```

For example:

```text
A0>SYSGEN A: B:
```

This reads the installed BetterCP/M system from drive A and installs it onto drive B.

Another example is:

```text
A0>SYSGEN C: D:
```

This installs the system from drive C onto drive D.

The source and destination must refer to different physical drives.

Using different logical drive letters is not sufficient if both letters refer to the same physical device.

SYSGEN checks the physical assignments and refuses an installation that would use the same physical drive as both source and destination.


##### Installing from SYSTEM.SYS

SYSGEN can also install BetterCP/M from a system-image package.

For example:

```text
A0>SYSGEN SYSTEM.SYS B:
```

This reads `SYSTEM.SYS` from the current drive and user area and installs its operating-system image onto drive B.

A drive-qualified package name can also be used:

```text
A0>SYSGEN C:SYSTEM.SYS B:
```

This reads the package from drive C.

The package filename need not be `SYSTEM.SYS`. Any valid, explicitly specified CP/M 8.3 filename can be used.

For example:

```text
A0>SYSGEN B:BASE090.SYS C:
```

This installs the saved system image contained in `BASE090.SYS` onto drive C.

Package filenames do not support wildcard specifications, compound drive/user selectors, or explicit user-area qualifications.

An unqualified package name refers to the current drive and user area.


##### System-Image Packages

A BetterCP/M system-image package contains the operating-system image together with information needed to identify and install it correctly.

The standard package is named:

```text
SYSTEM.SYS
```

A valid BetterCP/M 1.0 package contains a header followed by the operating-system image.

SYSGEN checks the package before installation.

It verifies that the expected header and system-image structure are present, that the complete package can be read, and that the image is suitable for the destination.

If the package is invalid or incompatible, SYSGEN refuses the operation before writing to the destination.

A structurally valid package is not necessarily free from every possible form of corruption. Use system images obtained from a trusted source.


##### Preparing the Destination Disk

Before using SYSGEN, the destination disk must already have a suitable format.

SYSGEN does not format disks.

If the disk needs to be formatted, use CONFIG to establish the appropriate disk-format assignment and DUP to perform the formatting.

For example:

```text
A0>CONFIG
A0>DUP /FORMAT B:
A0>SYSGEN SYSTEM.SYS B:
```

This illustrates the general preparation sequence.

The correct format depends on the computer and the system image being installed.

The destination must provide a compatible bootstrap arrangement and sufficient reserved space for BetterCP/M.


##### Compatible Disk Formats

SYSGEN does not require the source and destination disks to have identical filesystem capacities.

For example, it may be possible to install BetterCP/M onto a disk with a larger filesystem than the source, provided the destination has compatible bootstrap geometry and sufficient reserved system space.

BetterCP/M 1.0 requires at least 160 reserved 128-byte logical records for the installed system.

This corresponds to 20,480 bytes of reserved system space.

A destination may have more reserved space, but SYSGEN writes only the required system records.

If the reserved area is too small, SYSGEN reports:

```text
Destination reserved system area is too small (160 records required).
```

If the destination's bootstrap geometry is incompatible, SYSGEN refuses the installation.

It does not attempt to convert the disk into a different format.


##### Protected System Drive

BetterCP/M protects physical drive 0 against SYSGEN destination writes.

This protection follows the physical drive, regardless of its logical drive letter.

For example, assigning physical drive 0 to another logical letter does not make it an acceptable SYSGEN destination.

If the requested destination resolves to physical drive 0, SYSGEN reports:

```text
Physical drive 0 is protected as the running system disk.
```

This safeguard helps prevent accidental replacement of the operating system from which the computer is currently running.


##### Confirming Installation

Before writing to the destination, SYSGEN displays the installation information and requests confirmation.

The warning includes:

```text
The destination system area will be replaced.
Files outside the reserved system tracks will be preserved.
Proceed (Y/N)?
```

Only `Y` begins installation.

Any other response cancels the operation without modifying the destination.

The confirmation is required whether SYSGEN was started interactively or with command-line arguments.

BetterCP/M 1.0 does not provide an option for bypassing this confirmation.


##### Preserving Existing Files

SYSGEN replaces the operating system in the reserved system area.

It does not erase or rewrite ordinary filesystem records.

This means that a compatible disk containing existing files can receive a new BetterCP/M system without necessarily losing those files.

For example, a disk containing application programs and data files may be suitable for system installation if it has the required reserved system area.

SYSGEN preserves records outside the system area it installs.

However, this protection does not mean that every disk is suitable.

A disk with no compatible system area, or with insufficient reserved space, cannot be made bootable merely by running SYSGEN.


##### Installation and Verification

SYSGEN reads the complete source image before beginning destination writes.

It also prepares the image for the destination's configuration.

During installation, SYSGEN writes the system records and verifies each one by reading it back and comparing the data.

The boot record is written last.

When the operation completes successfully, SYSGEN reports:

```text
System installed and verified. The destination is bootable.
```

This indicates that the operating-system image was installed and verified.

It does not mean that the disk contains every utility or supporting file required for your preferred working environment.

Those files must be copied separately.

For example, a complete system disk may also require the appropriate command utilities, resident extensions, and `STARTUP.SUB`.


##### Saving an Installed System to a Package

SYSGEN can also read the operating system from a disk and save it as a `SYSTEM.SYS` package.

This is useful for preserving a working configuration, maintaining several system versions, or preparing an image for installation onto another compatible disk.

To save the installed system from drive A:

```text
A0>SYSGEN A:
```

SYSGEN reads the system area from drive A and creates `SYSTEM.SYS` in the current drive and user area.

You can specify another filename and destination drive:

```text
A0>SYSGEN A: B:BASE090.SYS
```

This saves the installed system from drive A as `BASE090.SYS` on drive B.

The resulting package can later be installed using:

```text
A0>SYSGEN B:BASE090.SYS C:
```


##### What a Saved Package Contains

A saved system package includes the installed BetterCP/M operating system and its saved configuration information.

This includes the saved startup command, cold-boot IOBYTE, and saved drive configuration.

It does not include unsaved changes made only to the running system.

It also does not include ordinary files from the source disk.

For example, changes made to `STARTUP.SUB` are not captured in the system-image package because that file resides in the ordinary filesystem.

To preserve both the operating system and its supporting files, use a complete disk backup.


##### Replacing an Existing Package

If the requested output filename already exists, SYSGEN asks:

```text
Replace existing package (Y/N)?
```

Only `Y` permits replacement.

Read-only and system files are protected against replacement.

SYSGEN verifies the package before reporting successful export.

A successful operation displays:

```text
Package exported and verified.
```


##### Interrupting Installation

SYSGEN recognizes Ctrl-C during installation.

At the interactive destination prompt, Ctrl-C exits without modifying the disk.

During installation, Ctrl-C is checked between disk operations.

An operation already in progress may finish before the interruption takes effect.

If installation is interrupted after writing has begun, the destination system area may be incomplete.

The disk may no longer boot.

SYSGEN does not automatically restore the previous operating system after a partial installation.

Correct the cause of the interruption and repeat installation from a valid source.


###### Invalid System Package

If a system-image package is invalid or cannot be installed on the selected destination, SYSGEN may report:

```text
The system package is invalid or cannot represent the destination.
```

Check that the package is a valid BetterCP/M system image and that it is compatible with the destination.


###### Incompatible Bootstrap Geometry

If the destination's bootstrap geometry is unsuitable, SYSGEN reports:

```text
Destination bootstrap geometry is not supported by this system package.
```

Use CONFIG to examine the destination's format assignment.

SYSGEN cannot convert an incompatible disk format into a bootable one.


###### Insufficient Reserved Space

If the destination does not provide enough reserved system space, SYSGEN reports:

```text
Destination reserved system area is too small (160 records required).
```

A disk with insufficient reserved space cannot accept the BetterCP/M 1.0 system image.


###### Read and Write Failures

If a source read fails, SYSGEN stops before beginning destination installation.

If a destination write or verification fails after installation has begun, the destination may contain an incomplete system.

Do not assume that such a disk is bootable.


##### Memory Requirements

Saving an installed system to a package requires at least 36K of available transient program memory.

If resident extensions have reduced the available TPA below this requirement, SYSGEN refuses the export operation.

Unload unnecessary extensions before retrying.


##### Version Information

To display SYSGEN's version and build identification:

```text
A0>SYSGEN /VER
```

The utility displays its identification and returns to the command prompt without performing an installation or export.


##### SYSGEN, DUP, and SYSBUILD

BetterCP/M provides three utilities with related but distinct purposes.

| Utility | Purpose |
|---|---|
| **DUP** | Format disks, copy entire disks, and check physical readability |
| **SYSGEN** | Install BetterCP/M onto prepared media or save an installed system image |
| **SYSBUILD** | Construct a system-image package from operating-system build products |

For ordinary system maintenance, DUP and SYSGEN provide the facilities needed to prepare and install BetterCP/M disks.

SYSBUILD is primarily intended for developers and system builders preparing new operating-system images.

For an introduction to disk preparation, installation, and backup procedures, see [Chapter 10](Users-Guide.md#chapter-10), *Working with Disks*.

#### Examples

Start interactive installation:

```text
A0>SYSGEN
```

Install from drive A onto drive B:

```text
A0>SYSGEN A: B:
```

Install from a system-image package:

```text
A0>SYSGEN SYSTEM.SYS B:
```

Install from a package on another drive:

```text
A0>SYSGEN C:SYSTEM.SYS B:
```

Save the installed system from drive A:

```text
A0>SYSGEN A:
```

Save the installed system under a specified filename:

```text
A0>SYSGEN A: B:BASE090.SYS
```

Restore a saved system image:

```text
A0>SYSGEN B:BASE090.SYS C:
```

Display version information:

```text
A0>SYSGEN /VER
```


#### Errors/Troubleshooting

##### SYSGEN Messages

SYSGEN reports conditions encountered while installing BetterCP/M or saving system-image packages.

###### `Physical drive 0 is protected as the running system disk.`

**Meaning:** The requested installation destination resolves to physical drive 0.

BetterCP/M protects this drive against SYSGEN destination writes.

**What to do:** Select another suitable physical drive.

Changing the logical drive letter does not bypass this protection.

###### `Source and destination refer to the same physical drive.`

**Meaning:** A disk-source installation would read and write through the same physical drive.

SYSGEN requires different physical drives for disk-to-disk installation.

**What to do:** Select a different destination.

###### `The selected drive is undefined or unavailable.`

**Meaning:** SYSGEN could not obtain a valid drive assignment for the requested source or destination.

**What to do:** Examine the drive configuration and correct the assignment before retrying.

###### `Destination reserved system area is too small (160 records required).`

**Meaning:** The destination does not provide enough reserved system space for BetterCP/M 1.0.

SYSGEN requires at least 160 reserved 128-byte logical records.

**What to do:** Use a disk format with a sufficiently large reserved system area.

SYSGEN cannot create additional reserved space by itself.

###### `Destination bootstrap geometry is not supported by this system package.`

**Meaning:** The destination's bootstrap geometry is incompatible with the system image being installed.

**What to do:** Use a compatible destination format or a system image appropriate to the destination.

SYSGEN does not perform disk-format conversion.

###### `The system package is invalid or cannot represent the destination.`

**Meaning:** The system-image package failed validation or cannot be installed safely using the destination's configuration.

**What to do:** Check the package and destination format.

If necessary, obtain a valid system package or recreate it from a known working installation.

###### `The destination system area will be replaced.`

**Meaning:** SYSGEN is requesting confirmation before installation.

The accompanying message explains that files outside the reserved system tracks will be preserved.

Only `Y` authorizes installation.

###### `System installed and verified. The destination is bootable.`

**Meaning:** SYSGEN completed installation and verified the written system records.

This is a successful completion message.

It does not mean that all ordinary utility files or startup-support files have been copied to the destination.

###### `Installation stopped. The destination may not boot.`

**Meaning:** Installation was interrupted after system-area writing began.

The destination may contain an incomplete operating system.

The filesystem area remains outside SYSGEN's write range.

**What to do:** Repeat installation from a valid source after correcting the cause of the interruption.

###### `Package exported and verified.`

**Meaning:** SYSGEN successfully saved and verified an installed operating-system image as a package file.

The package contains the operating system and its saved configuration, but not ordinary files from the source disk.

###### `Replace existing package (Y/N)?`

**Meaning:** The requested package filename already exists.

Only `Y` authorizes replacement.

Read-only and system files remain protected.

###### SYSGEN Recovery Files

During package export, SYSGEN may use:

```text
SYSGEN.$$$
SYSGEN.BAK
```

If an export fails, one or both files may remain.

These are recovery files, not necessarily disposable temporary files.

**What to do:** Examine the reported failure and preserve the files until you've determined whether they contain a valid package or the previous version.

For additional information, see [Section 16.5](#sysgen), *SYSGEN*.

##### Interrupted Package Export

SYSGEN takes precautions to avoid replacing an existing package with an incomplete one.

It first writes the new package to a temporary file, verifies it, and then publishes it under the requested filename.

During replacement, it may use the temporary filenames:

```text
SYSGEN.$$$
SYSGEN.BAK
```

These names are reserved for recovery.

If a package export fails, one or both files may remain.

**Do not delete these files without first examining the failed operation.** They may contain a recoverable package or the previous version of the file.

SYSGEN reports publication failures and identifies the files that should be inspected.

The export procedure reduces the risk of losing an existing package, but it cannot guarantee recovery from every possible disk or power failure.


##### Installation Errors

SYSGEN reports errors encountered while reading the source, validating the destination, writing system records, or verifying the installed image.

Common causes include incompatible disk formats, insufficient reserved system space, unavailable drives, write protection, and read or write failures.


#### See Also

[system messages](#system-messages) · [file specifications](#file-specifications)


<a id="batch-processing-and-extensions"></a>

## Batch processing and extensions


<a id="cpx"></a>

### CPX

#### Description

Displays, loads, and unloads Command Processor Extensions. CPX.COM is supplied in A0 on both System disks.

#### General Form

```text
CPX LIST
CPX LOAD name
CPX UNLOAD name
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Inspect configured packages | `CPX LIST` |
| Restore standard resident commands | `CPX LOAD RCP` |

#### Detailed Reference

A Command Processor Extension, or CPX, adds commands to BetterCP/M's command environment.

A CPX remains available between commands in the active command environment. Its command code can be reclaimed by transient programs and is reconstructed on warm boot. This allows frequently used commands to be provided at the prompt without loading a separate `.COM` file each time.

The standard BetterCP/M command environment includes `RCP.CPX`, which supplies familiar commands such as DIR, ERA, REN, TYPE, COPY, and MOVE.

The CPX manager allows additional command packages to be installed or removed.


##### Command Forms

The principal CPX management commands are:

```text
CPX LIST
CPX LOAD name
CPX UNLOAD name
```

The `name` argument is an unqualified CPX filename stem, with optional `.CPX`. Blank names, drive qualifiers, wildcards and other extensions are rejected.

For example:

```text
A0>CPX LOAD TOOLS
```

requests the command package `TOOLS.CPX`.


##### Listing CPXs

To examine the configured command processor extensions, enter:

```text
A0>CPX LIST
```

BetterCP/M displays information about the configured CPX packages.

This is useful when determining which command packages are available or investigating a missing resident command.

An important distinction is that **a configured CPX is not necessarily a successfully loaded CPX**.

BetterCP/M may retain an extension's configured entry even when the corresponding file cannot be loaded.

Consequently, the presence of a name in `CPX LIST` does not by itself establish that its commands are available.


##### Loading a CPX

To load an additional command package, enter:

```text
CPX LOAD name
```

For example:

```text
A0>CPX LOAD TOOLS
```

BetterCP/M attempts to load the specified extension.

The file must be available as `A0:TOOLS.CPX` and compatible with the running system. Keep configured carriers in A0 for reconstruction after warm boot or transient execution.

If loading succeeds, the commands supplied by the extension become available through the normal command environment.

For example, if `TOOLS.CPX` provides a command named `TOOLS`, that command can be invoked directly:

```text
A0>TOOLS
```

The actual commands provided depend on the extension.


##### Loading Several CPXs

BetterCP/M maintains an ordered **four-entry reconstruction profile**. The standard RCP entry occupies one slot, leaving three for additional packages. A configured entry still occupies its slot if its carrier is missing or fails validation.

`CPX LOAD name` appends a new name after the existing entries. Loading an already configured name is a successful no-op: it neither adds another entry nor changes the order. A fifth distinct entry is rejected without changing the profile.

Successfully reconstructed CPXs are consulted in profile order after the CCP's built-in commands and before transient lookup. The first CPX that handles a command wins. Appending a package therefore does not give it precedence over an earlier package providing the same command. `CPX LIST` shows the configured order.

`CPX UNLOAD name` removes the named entry and shifts later entries left, preserving their relative order. Unloading an absent name is a successful no-op. To deliberately reorder packages, remove and reload the affected entries in the desired order, keeping the four-entry limit in mind.

If you need to execute a particular transient utility regardless of the resident command environment, use BetterCP/M's explicit transient-execution prefix:

```text
A0>:DIR
```

This bypasses resident command lookup.

For more information about command search and execution, see [Chapter 5](Users-Guide.md#chapter-5).


##### Unloading a CPX

To remove an optional command package, enter:

```text
CPX UNLOAD name
```

For example:

```text
A0>CPX UNLOAD TOOLS
```

After the extension has been removed, its commands are no longer available as resident commands.

Corresponding transient programs, if present, remain available through the ordinary program-search mechanism.

Unloading a CPX can be useful when you no longer need its commands or want to change the resident command environment.


##### Removing the Standard Command Package

RCP is part of the selected standard environment, but the current CPX profile manager does not reserve or lock its entry. `CPX UNLOAD RCP` is allowed. Removing it takes away commands supplied by RCP, including resident DIR, ERA, REN, TYPE, COPY, MOVE, CLS and VER. Built-in CCP commands and available transient utilities remain usable; a transient is available only if its file has been installed.

For example, the System Disk supplies `DIR.COM` but does not supply `CLS.COM`. To restore the normal command package, keep `A0:RCP.CPX` available and enter `CPX LOAD RCP`. It is appended in the usual way, so check the resulting order with `CPX LIST`.


##### CPXs and Available Memory

Command Processor Extensions occupy memory in the active command environment, but their command code is reclaimable, along with the CCP, when a transient program starts. BetterCP/M shuts down the active CPX chain before transferring control and reconstructs the command environment on warm boot.

Keeping a CPX configured makes its commands available at the prompt without permanently subtracting its command-code size from the maximum transient program size. RSXs, by comparison, occupy protected memory while applications run.

Use `STAT MEM` to see the current CCP, CPX, and RSX regions and the maximum loadable COM size. The maximum can include the reclaimable CCP and CPX regions shown in the map.


#### Examples

##### CPX Examples

List configured command extensions:

```text
A0>CPX LIST
```

Load an optional extension:

```text
A0>CPX LOAD TOOLS
```

Unload an optional extension:

```text
A0>CPX UNLOAD TOOLS
```

Request a transient utility rather than a resident command:

```text
A0>:DIR /WHEREIS ED.COM
```

For an introduction to CPXs and their relationship to the command environment, see [Chapter 8](Users-Guide.md#chapter-8), *Resident Extensions*.

#### Errors/Troubleshooting

##### Resident Extension Messages

Resident extensions may report errors when being loaded, unloaded, or restored.

###### CPX Load Failure

An optional CPX that fails validation may produce:

```text
CPX?
```

The system continues with the remaining usable command extensions.

The affected commands are unavailable until the extension is repaired or removed.

###### RSX Load Failure

**Meaning:** The requested RSX could not be installed.

Possible causes include a missing or damaged extension file, an incompatible extension, insufficient memory, or an unavailable dependency.

**What to do:** Check that the extension file exists and that its required supporting components are installed.

For example, a terminal personality requires a compatible screen backend.

###### RSX Unload Failure

**Meaning:** The requested extension could not be removed.

One possible cause is that another resident extension still depends on it.

**What to do:** Examine the installed extensions:

```text
A0>RSX LIST
```

Unload dependent extensions before removing their supporting components.

###### Insufficient Resident Memory

**Meaning:** The requested extension cannot be installed because insufficient suitable memory is available.

**What to do:** Unload unnecessary extensions and retry.

Resident extensions reduce the memory available to transient programs.

For additional information, see [Chapter 8](Users-Guide.md#chapter-8), *Resident Extensions*, and [Chapter 17](#batch-processing-and-extensions), *Batch and Extension Commands*.

##### Recovering from an Unusable CPX

If an optional CPX file fails validation, BetterCP/M may display:

```text
CPX?
```

The operating system continues to the command prompt with its remaining usable extensions.

Commands supplied by the rejected CPX are unavailable.

The rejected extension may nevertheless remain in the configured profile.

For example:

```text
A0>CPX LIST
```

may still show the extension.

To remove an unusable optional CPX, enter:

```text
A0>CPX UNLOAD BAD
```

where `BAD` is the name of the affected extension.

Alternatively, replace the damaged file with a valid copy.

Until the problem is corrected, the warning may recur when BetterCP/M restores the command environment.

A missing optional CPX file may simply be skipped without producing the same warning.


#### See Also

[system messages](#system-messages) · [file specifications](#file-specifications)


<a id="rsx"></a>

### RSX

#### Description

Lists, loads, and unloads Resident System Extensions (RSXs). RSX.COM is supplied in A0 on both System disks.

#### General Form

```text
RSX LIST
RSX LOAD [DU:]name
RSX UNLOAD name
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Inspect active extensions | `RSX LIST` |
| Load cpmsim clock support | `RSX LOAD ZPRTC` |

#### Detailed Reference

Resident System Extensions provide services that remain available while other programs execute. Unlike Command Processor Extensions, which add commands to the command environment, RSXs extend the services available to applications and the operating system.

BetterCP/M uses RSXs for several purposes, including terminal emulation, clock support, batch input, and other optional system facilities.

The RSX utility allows you to manage these extensions without rebuilding the operating system.

An explicit source such as `RSX LOAD B3:NAME.RSX` loads only from that drive/user. An unqualified name searches the current drive/user, then A0. `B:NAME` uses the current user on B. Once loaded, the original carrier disk may be removed: warm boots and later RSX loads/unloads use retained RAM data. Keep the matched-build `R3PACK.RSX` and `R3CACHE.RSX` manager runtimes in A0; these are system support files, not extensions to load with `RSX LOAD`. See [Section 8.2](Users-Guide.md#chapter-8--manage-extensions-and-program-memory) for installation details.


##### Syntax

The principal command forms are:

```text
RSX LIST
RSX LOAD [DU:]name
RSX UNLOAD name
```

The `name` argument identifies the extension to be loaded or unloaded. The `.RSX` extension is normally omitted.

For example:

```text
A0>RSX LOAD ADM3A
```

loads the ADM-3A terminal personality from `ADM3A.RSX`.


##### Listing Installed RSXs

To display the currently installed Resident System Extensions, enter:

```text
A0>RSX LIST
```

BetterCP/M displays the installed extensions.

This is useful when determining which system services are available, checking whether a particular extension is loaded, or investigating memory usage.

For example, you might use RSX LIST to determine whether a terminal personality or clock provider is installed before running an application that requires it.


##### Loading an RSX

To load an extension, enter:

```text
RSX LOAD [DU:]name
```

For example:

```text
A0>RSX LOAD FREHDCLK
```

loads the FreHD clock provider.

Once successfully loaded, the provider makes its supported clock services available to programs using BetterCP/M's clock interface.

Another example is:

```text
A0>RSX LOAD VT52
```

which loads the VT52 terminal personality.

Some extensions require other resident components to be loaded first.

The extension's documentation identifies these requirements.


##### Extension Dependencies

Some RSXs depend on services provided by other extensions. The 1.1 ADM3A,
VT52 and ANSI modules combine personality and renderer and need no separate
screen backend. On every target, select ADM3A with `RSX LOAD ADM3A` and remove
it with `RSX UNLOAD ADM3A`; unload it before selecting VT52 or ANSI.

Standalone SCRN/SCX clients retain their separate dependencies. TED requires
ANSI plus ANSISCRN on cpmsim, M4SCRN on Model 4, or M2SCRN on Model II.
DUMP paging requires the appropriate SCRN backend. This does not migrate
these utilities to TCAP 2.0.

##### Unloading an RSX

To remove an installed extension, enter:

```text
RSX UNLOAD name
```

For example:

```text
A0>RSX UNLOAD ADM3A
```

removes the ADM-3A terminal personality.

Once the extension has been removed, its services are no longer available.

Unloading an extension also releases the memory occupied by that extension when the resident manager can reclaim it.


##### Unloading Dependent Extensions

When several extensions depend on one another, remove them in the reverse order from which they were loaded.

For example:

```text
A0>RSX UNLOAD ADM3A
A0>RSX UNLOAD M4SCRN
```

This removes the terminal personality before removing its supporting screen backend.

Attempting to remove a supporting extension while another component still requires it may be rejected.

If RSX reports that an extension cannot be unloaded, examine the installed extensions and their dependencies before trying again.


##### Changing Terminal Personalities

Only one terminal personality can be active at a time.

To change from ADM-3A to VT52 while retaining the same screen backend:

```text
A0>RSX UNLOAD ADM3A
A0>RSX LOAD VT52
```

The screen backend need not be reloaded if it remains installed and supports the new personality.

To verify the new environment, run the corresponding terminal test utility:

```text
A0>VT52TST
```

For further information about terminal personalities, see [Chapter 9](Users-Guide.md#chapter-9), *Terminal Support*.


##### Clock Providers

BetterCP/M provides loadable clock providers through the RSX system.

For example, on a TRS-80 Model 4 with FreHD:

```text
A0>RSX LOAD FREHDCLK
A0>TIME
```

Under z80pack:

```text
A0>RSX LOAD ZPRTC
A0>TIME
```

These providers allow TIME and compatible applications to obtain the current date and time.

Both providers supplied with BetterCP/M 1.0 are read-only.

You can identify the active provider with:

```text
A0>TIME /PROVIDER
```

For more information, see [Chapter 11](Users-Guide.md#chapter-11), *Date and Time*, and [TIME](#time), *TIME*.


##### P2DOS Clock Compatibility

The optional-to-load `P2DOS.RSX` implements compatibility with the P2DOS date-and-time interface. Its matched carrier is supplied in A0 on both System Disks; the following example loads it after the native provider.

For example:

```text
A0>RSX LOAD ZPRTC
A0>RSX LOAD P2DOS
```

The first command loads the native clock provider.

The second installs the P2DOS-compatible interface.

The P2DOS extension uses BetterCP/M's native clock service rather than communicating directly with the underlying clock hardware.

Consequently, its capabilities depend on the installed provider.

With the standard read-only providers, clock-setting requests are not supported.


##### Batch Input Support

BetterCP/M's XSUB facility uses a resident extension named `BATCHIO`.

This extension allows compatible programs to receive submitted input through the CP/M buffered console-input interface.

BATCHIO may remain resident after the batch procedure has finished.

To check whether it is installed:

```text
A0>RSX LIST
```

To remove it explicitly:

```text
A0>RSX UNLOAD BATCHIO
```

This releases the resident batch-input facility when it is no longer needed.

For additional information, see [XSUB](#xsub), *XSUB*.


##### RSXs and Program Memory

Resident System Extensions occupy memory that would otherwise be available to transient programs.

Loading an extension can therefore reduce the available Transient Program Area (TPA).

For example, a terminal monitor may be useful while running a full-screen editor but unnecessary when running an ordinary command-line utility.

If a program reports insufficient memory, examine the installed RSXs:

```text
A0>RSX LIST
```

You may be able to unload extensions that are no longer needed.

Some utilities have substantial memory requirements. DUP, for example, requires approximately 51K of available transient memory.

Unloading unnecessary extensions may provide sufficient space for such programs.


##### Warm Boots and Extension Persistence

BetterCP/M preserves supported resident extensions across ordinary warm boots.

For example, suppose you load a terminal monitor:

```text
A0>RSX LOAD M4SCRN
A0>RSX LOAD VT52
```

You can then run a compatible full-screen application.

When the application terminates and control returns to the command processor, the terminal monitor remains available.

There is ordinarily no need to reload it after every program.

A cold boot starts a new session. Use the supplied script and editing procedure in [Section 7.3](Users-Guide.md#chapter-7--inspect-change-and-save-configuration) to arrange automatic loading; normal carrier placement and dependencies are described in [Section 8.2](Users-Guide.md#chapter-8--manage-extensions-and-program-memory).


#### Examples

List installed RSXs:

```text
A0>RSX LIST
```

Load a terminal screen backend:

```text
A0>RSX LOAD M4SCRN
```

Load an ADM-3A terminal personality:

```text
A0>RSX LOAD ADM3A
```

Change to VT52:

```text
A0>RSX UNLOAD ADM3A
A0>RSX LOAD VT52
```

Load the FreHD clock provider:

```text
A0>RSX LOAD FREHDCLK
```

Load z80pack clock support:

```text
A0>RSX LOAD ZPRTC
```

Load P2DOS-compatible clock services using the supplied A0:P2DOS.RSX after loading a native clock provider:

```text
A0>RSX LOAD P2DOS
```

Remove the batch-input extension:

```text
A0>RSX UNLOAD BATCHIO
```

Unload a terminal monitor:

```text
A0>RSX UNLOAD VT52
A0>RSX UNLOAD M4SCRN
```

For an introduction to resident extensions and their use, see [Chapter 8](Users-Guide.md#chapter-8), *Resident Extensions*.

For detailed information about developing RSXs, consult the [BetterCP/M RSX and CPX Programmer's Guide](../programmers/RSX%20and%20CPX%20Programmer%27s%20Guide.md).

#### Errors/Troubleshooting

##### Resident Extension Messages

Resident extensions may report errors when being loaded, unloaded, or restored.

###### CPX Load Failure

An optional CPX that fails validation may produce:

```text
CPX?
```

The system continues with the remaining usable command extensions.

The affected commands are unavailable until the extension is repaired or removed.

###### RSX Load Failure

**Meaning:** The requested RSX could not be installed.

Possible causes include a missing or damaged extension file, an incompatible extension, insufficient memory, or an unavailable dependency.

**What to do:** Check that the extension file exists and that its required supporting components are installed.

For example, a terminal personality requires a compatible screen backend.

###### RSX Unload Failure

**Meaning:** The requested extension could not be removed.

One possible cause is that another resident extension still depends on it.

**What to do:** Examine the installed extensions:

```text
A0>RSX LIST
```

Unload dependent extensions before removing their supporting components.

###### Insufficient Resident Memory

**Meaning:** The requested extension cannot be installed because insufficient suitable memory is available.

**What to do:** Unload unnecessary extensions and retry.

Resident extensions reduce the memory available to transient programs.

For additional information, see [Chapter 8](Users-Guide.md#chapter-8), *Resident Extensions*, and [Chapter 17](#batch-processing-and-extensions), *Batch and Extension Commands*.

##### Extension Errors

An RSX may fail to load because its file is missing, damaged, incompatible, or unsuitable for the current system.

A load may also fail because the required supporting services are unavailable.

If an extension fails to load, check that its file is present and that any required supporting extensions have already been installed.

For example, a terminal personality requires a suitable screen backend.

If an extension cannot be unloaded, another resident component may still depend on it.

Remove the dependent extension first.


##### Recovering from Extension Problems

If an RSX causes problems, begin by examining the installed extensions:

```text
A0>RSX LIST
```

If the affected extension can be safely removed, unload it.

For example:

```text
A0>RSX UNLOAD VT52
```

If the problem began after adding an extension to `STARTUP.SUB`, remove the corresponding startup command and test the extension manually.

A cold boot can restore the configured startup environment, but it will also execute the configured startup procedure again.

If that procedure contains an unsuitable extension-loading command, the problem may recur until the startup file is corrected.


#### See Also

[system messages](#system-messages) · [file specifications](#file-specifications)


<a id="submit"></a>

### SUBMIT

#### Description

Executes a sequence of commands stored in a text file. SUBMIT.COM is supplied in A0 on both System disks.

#### General Form

```text
SUBMIT filename [parameters]
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Run a supplied script | `SUBMIT STARTUP` |

#### Detailed Reference

SUBMIT allows frequently used command sequences to be saved and executed without entering each command individually.

It retains the familiar CP/M batch-processing conventions, including `.SUB` files and positional parameter substitution.


##### Syntax

```text
SUBMIT filename [parameters]
```

The filename identifies a SUBMIT command file. The `.SUB` extension is normally omitted when invoking the utility.

For example:

```text
A0>SUBMIT BACKUP
```

executes the commands contained in `BACKUP.SUB`.


##### Creating a SUBMIT File

A SUBMIT file is an ordinary text file containing commands.

Each command appears on a separate line.

For example, a file named `BACKUP.SUB` might contain:

```text
DIR *.ASM
:COPY *.ASM B:
DIR B:*.ASM
```

To execute it:

```text
A0>SUBMIT BACKUP
```

SUBMIT arranges for the commands to be executed in sequence.

The commands are interpreted by the normal BetterCP/M command environment.

Consequently, a SUBMIT file can contain resident commands, transient programs, and commands provided by installed CPXs.


##### Parameters

SUBMIT files can accept parameters supplied when the file is invoked.

Parameters are referenced using a dollar sign followed by a number.

For example, suppose `BUILD.SUB` contains:

```text
ASM $1
LOAD $1
$1
```

Enter:

```text
A0>SUBMIT BUILD TEST
```

SUBMIT substitutes `TEST` for `$1`, producing the equivalent of:

```text
ASM TEST
LOAD TEST
TEST
```

This allows the same command file to be used with different programs.


##### Multiple Parameters

A SUBMIT file can refer to several parameters.

For example, `COPYFILE.SUB` might contain:

```text
:COPY $1 $2
```

You could invoke it with:

```text
A0>SUBMIT COPYFILE REPORT.TXT B:REPORT.TXT
```

The resulting command would be:

```text
:COPY REPORT.TXT B:REPORT.TXT
```

Parameter substitution is textual. SUBMIT does not interpret filenames or options while performing the substitution.

For a literal dollar sign in the `.SUB` source, write `$$`. For example, write `[$$ARC]` so the executed command receives `[$ARC]`. A bare `$ARC` causes `Parameter Error`. See [Chapter 6](Users-Guide.md#chapter-6), *Literal Dollar Signs in Command Files*, for a complete backup example.

The resulting command is interpreted by the command processor or utility that executes it.


##### Queue Location and Limits

SUBMIT reads the `.SUB` source in the invoking user area, using the filename's drive qualifier when supplied. It always writes the shared command/input queue as `A0:$$$.SUB`. A0 must be writable and have room for the queue, even if the script and all working files are on another drive. Queue access restores the caller's drive/user context; commands may change drive or user without relocating the queue.

The CCP consumes command lines from this queue. XSUB uses the same queue for buffered program input. Run one submitted procedure at a time; starting another procedure replaces the shared queue rather than creating an independent job.

- The nine ordinary positional parameters are `$1` through `$9`; `$0` refers to the submitted command-file name from the invocation.
- Parameters are separated by blanks. There is no quoting language for grouping a parameter containing spaces, and no named variables or defaults. A missing referenced parameter expands to empty text, so check that all required arguments are supplied. Invalid dollar references produce `Parameter Error`.
- Each expanded command is limited to 125 bytes, after parameter, `$$`, and caret-control expansion. An overlong command produces `Command Too Long`.
- The complete expanded procedure must fit the 2K aggregate command buffer, including its bookkeeping. This is not a 2K source-file allowance; a procedure with many short lines can also reach the limit and produce `Command Buffer Overflow`. Split a long procedure into smaller separately submitted jobs.
- Empty source lines are omitted. `^A` through `^Z` in the source produce the corresponding control bytes; literal dollar signs require `$$`.

The queue is deleted at normal exhaustion, after a bad submitted command, on console abort, and after malformed-queue or queue read/close failures. An ordinary supported warm boot can reconstruct the command environment and continue pending batch lines. Cancelling a procedure does not undo work already completed. With XSUB, queue exhaustion or an unusable queue returns buffered-input requests to the keyboard.


##### Command Execution

SUBMIT commands execute in the normal BetterCP/M command environment.

A command may load a transient program, invoke a resident command, or use an installed extension.

Ordinary warm boots preserve the batch-processing mechanisms needed to continue supported SUBMIT operations.

A cold boot establishes a new operating session rather than continuing a previous batch.


##### Interactive Commands

A command executed from a SUBMIT file does not automatically become noninteractive.

For example, transient `COPY.COM` may ask whether an existing writable destination file should be replaced. Resident COPY instead refuses the collision unless `/O` is supplied. Use `:COPY` to select the transient utility explicitly.

If the batch is intended to run unattended, use the command's supported options to specify the desired behavior.

For example:

```text
:COPY B1:*.DAT C3: /B /O
```

uses COPY's batch option and requests replacement of existing writable destination files.

The `/B` option belongs to COPY. It does not change SUBMIT's behavior or make other commands noninteractive.


##### Startup Files

BetterCP/M uses SUBMIT for its standard startup procedure.

The default cold-start command is:

```text
SUBMIT STARTUP
```

This executes `STARTUP.SUB`.

[Section 7.3](Users-Guide.md#chapter-7--inspect-change-and-save-configuration) lists the supplied scripts in order. cpmsim displays the banner only; Model 4 already loads integrated ADM3A, clears the screen, then displays the banner. Edit `A0:STARTUP.SUB` to customize that sequence.

The startup command is executed during a cold boot, not during an ordinary warm boot.

For information about configuring startup behavior, see [Chapter 7](Users-Guide.md#chapter-7).


#### Examples

Execute a command file:

```text
A0>SUBMIT BACKUP
```

Execute a command file with one parameter:

```text
A0>SUBMIT BUILD TEST
```

Execute a command file with two parameters:

```text
A0>SUBMIT COPYFILE REPORT.TXT B:REPORT.TXT
```

For an introduction to batch processing, see [Chapter 6](Users-Guide.md#chapter-6).

#### Errors/Troubleshooting

##### Errors and Interruptions

Errors during batch execution may interrupt the procedure or affect subsequent commands.

The exact behavior depends on the command and the error encountered.

A failed command does not necessarily undo earlier successful operations.

For example, if a batch copies several files and encounters an error partway through, some destination files may already have been created.

Before restarting an interrupted batch, examine the results to determine which operations have completed.


#### See Also

[system messages](#system-messages) · [file specifications](#file-specifications)


<a id="xsub"></a>

### XSUB

#### Description

Allows compatible programs to receive input from a SUBMIT file through the CP/M buffered console-input interface. XSUB.COM is on the primary Utilities disk. Use an explicit companion location, such as `B0:XSUB B0:`, to load BATCHIO.RSX from the Utilities disk. The System disk must contain the matching R3PACK.RSX and R3CACHE.RSX runtimes. The locked 1.0 release still requires the [copy-to-A0 workaround](../releases/1.0-ERRATA.md#xsub-companion-must-be-copied-to-a0).

#### General Form

```text
XSUB [DU:]
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Enable using the Utilities companion in B0 | `B0:XSUB B0:` |
| Enable using current DU, then A0 | `XSUB` |

#### Detailed Reference

Ordinary SUBMIT processing supplies commands to the command processor.

Some programs, however, request additional input after they have started.

For example, an editor or utility might ask for a filename or an option.

XSUB extends batch processing by allowing submitted input to be supplied to such programs.


##### How XSUB Works

XSUB provides a resident input facility that cooperates with SUBMIT.

When a compatible program requests buffered console input, XSUB can supply the next submitted input line.

This allows certain interactive procedures to be automated.

For example, a program that normally asks:

```text
Source file:
Destination file:
```

may be able to receive those responses from the batch file.

XSUB does not automatically support every interactive program.

Programs that read the keyboard directly, use private input routines, or bypass the supported BDOS console-input interface may still require ordinary keyboard input.


##### Using XSUB

The activation command is:

```text
XSUB
```

Place it before the program to be automated. `XSUB.COM` and its matched `BATCHIO.RSX` are supplied on the **Utilities Disk**. At A0, invoke `B0:XSUB B0:` to use that companion directly. An explicit DU restricts lookup to that location; without one, XSUB searches the current DU, then A0. The COM lookup location does not implicitly select the companion location. No all-drive scan is performed. Keep matching `R3PACK.RSX` and `R3CACHE.RSX` on A0. Once loaded, BATCHIO no longer requires its original carrier. The disk-cache update needs writable A0 space when installing, and readable A0 cache files for later RSX set changes. Its five `$$RSX00.RSC` through `$$RSX04.RSC` names are reserved; do not remove active cache files. Cleanup reclaims them automatically when modules are unloaded. Ordinary warm boots do not read them.

Before running the example, make `ED.COM`, `TYPE.COM`, and `SUBMIT.COM` available on the command search path, mount Utilities as B0, and retain matching `R3PACK.RSX`/`R3CACHE.RSX` runtimes in A0. Keep A0 writable for the shared queue, and use a writable working drive/user where `XDEMO.TXT` does not already exist.

Save this complete procedure as `XDEMO.SUB` in the working location:

```text
B0:XSUB B0:
ED XDEMO.TXT
IHELLO FROM XSUB^L^Z
E
:TYPE XDEMO.TXT
```

Type the caret sequences `^L` and `^Z` as two ordinary source characters each; SUBMIT converts them to control bytes. Run:

```text
A0>SUBMIT XDEMO
```

XSUB activates BATCHIO. ED then receives `IHELLO FROM XSUB`, followed by the expanded controls, as its first buffered command line. Inline `I` inserts the text, Ctrl-L adds a line ending, and Ctrl-Z ends the inline insertion. ED receives `E` as its next command, saves the new file, and exits. The command processor resumes the remaining queue and TYPE displays:

```text
HELLO FROM XSUB
```

The response lines belong immediately after the program invocation because each BDOS Function 10 request consumes the next queue line. They are not separate CCP commands while the program is reading them. Supply exactly the responses the program will consume; leftover responses can otherwise be interpreted as commands, and extra input requests can consume intended later commands.

This example deliberately uses ED's inline insertion command. ED's interactive `I` mode reads individual characters through Function 1, which XSUB does not supply. XSUB supports **BDOS Function 10 buffered console input**, not arbitrary keyboard input.


##### Returning to Keyboard Input

When the submitted input has been exhausted, XSUB allows the program to continue receiving input from the keyboard.

For example, a program may receive its initial responses automatically and then continue interactively.

This is useful when only the repetitive portion of an operation needs to be automated.

A malformed or unusable submitted-input queue is discarded before returning to ordinary console input.


##### Resident BATCHIO Support

BetterCP/M's XSUB facility uses a resident component named `BATCHIO`.

This component may remain installed after the batch has finished.

Under the supported warm-boot conditions, an idle BATCHIO provider can retire automatically.

However, some program-termination paths may leave it resident.

You can examine installed RSXs with:

```text
A0>RSX LIST
```

To remove BATCHIO explicitly:

```text
A0>RSX UNLOAD BATCHIO
```

This releases its resident memory when it is no longer needed.


##### Memory Considerations

Like other resident extensions, BATCHIO occupies memory that would otherwise be available to transient programs.

Unloading it when no longer needed can restore available program memory.

The exact amount recovered depends on the other resident extensions installed.


##### Limitations

XSUB is intended for programs that use compatible buffered console-input services.

It is not a general keyboard-recording or keyboard-simulation utility.

It does not guarantee automation of programs that communicate directly with keyboard hardware or use unsupported input methods.

For ordinary command sequences that do not require input to running programs, SUBMIT alone is sufficient.

For an introduction to XSUB and batch processing, see [Chapter 6](Users-Guide.md#chapter-6).

#### Examples

```text
XSUB
```

Enable submitted buffered input. Substitute the locations and filenames appropriate to your session.

#### Errors/Troubleshooting

`Xsub Load Error` means activation failed: check the selected companion DU, matching System runtimes and available memory. From A0 with Utilities on B0, use `B0:XSUB B0:`. `/HELP` and `/VER` do not activate the provider. The locked 1.0 binaries retain their documented copy-to-A0 workaround.

Check the operand grammar and the selected drive/user area. For disk failures, preserve the source and any reported recovery files before retrying. See the [shared system messages](#system-messages) for command lookup, media, configuration and extension diagnostics.

#### See Also

[system messages](#system-messages) · [file specifications](#file-specifications)


<a id="date-and-time"></a>

## Date and time


<a id="time"></a>

### TIME

#### Description

Displays the current date and time, identifies the installed clock provider, and provides an interface for requesting clock-setting operations. TIME.COM is supplied in A0 on both System disks.

#### General Form

```text
TIME
TIME /PROVIDER
TIME /SET LL HH HR MN SC
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Read the loaded provider | `TIME` |
| Identify its capabilities | `TIME /PROVIDER` |

#### Detailed Reference

TIME uses BetterCP/M's resident clock services. It does not communicate directly with individual clock devices.

BetterCP/M 1.0 includes read-only clock providers for FreHD and z80pack.


##### Syntax

```text
TIME
TIME /PROVIDER
TIME /SET LL HH HR MN SC
```

The first form displays the date and time. The second identifies the installed clock provider. The third requests a clock-setting operation.


##### Displaying the Date and Time

Enter:

```text
A0>TIME
```

TIME obtains the current date and time from the installed provider.

A provider must be loaded before TIME can obtain clock information.

On a TRS-80 Model 4 equipped with FreHD:

```text
A0>RSX LOAD FREHDCLK
A0>TIME
```

Under z80pack/cpmsim:

```text
A0>RSX LOAD ZPRTC
A0>TIME
```

If no clock provider is installed, TIME reports that the required service is unavailable.


##### Identifying the Provider

Enter:

```text
A0>TIME /PROVIDER
```

TIME displays information about the installed clock provider, including its identity, interface version, and capabilities.

The two providers supplied with BetterCP/M 1.0 are:

| Provider | Extension | Capabilities |
|---|---|---|
| FreHD | `FREHDCLK.RSX` | Read-only |
| z80pack | `ZPRTC.RSX` | Read-only |

The provider information can help determine which clock service is active and whether it supports setting the clock.


##### Setting the Clock

TIME includes the following SET syntax:

```text
TIME /SET LL HH HR MN SC
```

The arguments are five two-digit hexadecimal bytes representing BetterCP/M's native clock record.

| Argument | Meaning |
|---|---|
| `LL` | Low byte of the day count |
| `HH` | High byte of the day count |
| `HR` | Hour, packed BCD |
| `MN` | Minute, packed BCD |
| `SC` | Second, packed BCD |

The day count is measured from the CP/M clock epoch of December 31, 1977, with day 1 corresponding to January 1, 1978.

For example:

```text
A0>TIME /SET 01 00 12 34 56
```

requests January 1, 1978, at 12:34:56.

The hour, minute, and second are represented in packed binary-coded decimal. Thus, hexadecimal byte `12` represents decimal 12, not decimal 18.

TIME checks the arguments before requesting the operation.

Malformed hexadecimal values, invalid BCD digits, and out-of-range time fields are rejected.


##### Clock-Setting Limitations

**Neither clock provider supplied with BetterCP/M 1.0 supports setting the clock.**

Consequently, a valid SET request is rejected as unsupported when either `FREHDCLK.RSX` or `ZPRTC.RSX` is installed.

The existing clock value remains unchanged.

The SET interface is implemented for compatibility with the native clock service and for use with providers that support writable clocks.


##### P2DOS Compatibility

The optional-to-load `P2DOS.RSX` on both System Disks supplies the P2DOS-compatible clock interface. Its carrier is already in A0; load the appropriate native clock provider before the example below.

To use it under z80pack:

```text
A0>RSX LOAD ZPRTC
A0>RSX LOAD P2DOS
```

P2DOS obtains its clock services through the installed native provider.

Because the supplied providers are read-only, P2DOS-compatible requests to set the clock are also unsupported.

The P2DOS extension is not required for ordinary use of TIME.

For additional information about clock providers and their capabilities, see [Chapter 11](Users-Guide.md#chapter-11).

#### Examples

```text
TIME
```

Read the loaded provider. Substitute the locations and filenames appropriate to your session.

#### Errors/Troubleshooting

##### Date and Time Messages

TIME reports errors when no clock provider is available, when a provider cannot obtain valid time information, or when an unsupported clock-setting operation is requested.

###### Clock Service Unavailable

**Meaning:** TIME cannot access an installed clock provider.

**What to do:** Load the appropriate provider for the platform.

For example:

```text
A0>RSX LOAD FREHDCLK
```

or:

```text
A0>RSX LOAD ZPRTC
```

Then retry:

```text
A0>TIME
```

###### Clock Read Failure

**Meaning:** The installed provider could not obtain a valid date and time.

Possible causes include unavailable hardware, an emulator-interface problem, or invalid clock data.

**What to do:** Check the platform's clock configuration.

TIME cannot correct an inaccurate or unavailable underlying clock.

###### Clock Setting Unsupported

**Meaning:** TIME accepted a SET request, but the installed clock provider does not support changing the clock.

Both BetterCP/M 1.0 providers, `FREHDCLK.RSX` and `ZPRTC.RSX`, are read-only.

**What to do:** Adjust the clock through the hardware or host environment, if supported.

The TIME utility's SET syntax does not make a read-only provider writable.

###### Invalid SET Arguments

**Meaning:** The arguments supplied to TIME's SET operation are malformed or outside the accepted ranges.

The command requires five hexadecimal bytes:

```text
TIME /SET LL HH HR MN SC
```

These represent the native clock record, not an ordinary calendar-date string.

**What to do:** Check the hexadecimal values and the required date-and-time representation.

For additional information, see [Section 16.3](#time), *TIME*.

Check the operand grammar and the selected drive/user area. For disk failures, preserve the source and any reported recovery files before retrying. See the [shared system messages](#system-messages) for command lookup, media, configuration and extension diagnostics.

#### See Also

[system messages](#system-messages) · [file specifications](#file-specifications)


<a id="editing-and-development-tools"></a>

## Editing and development tools


<a id="dasm"></a>

### DASM

#### Description

DASM.COM is supplied on the primary Utilities disk. Analyze Z80 binary input and produce staged source and saved analysis.

#### General Form

```text
DASM
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Start analysis | `B0:DASM` |

#### Detailed Reference

`/HELP` shows the compact utility quick reference. `/HELP` and `/VER` are
case-insensitive exact tokens, ignore other arguments, and return before file,
drive/user or screen-provider services; HELP takes precedence when both occur. DSYM
uses the same help/query convention. DASM's interactive H command still provides
its full command reference.

DASM is the maintained Richard Conn 1.5 Z80 disassembler adaptation. It inspects
loaded bytes, records symbols/comments and code/data classifications, saves
analysis and generates Zilog source for the supplied ZSM4/LINK tools. It does
not execute the input program. DSYM converts a verified final-address link
report into symbols DASM can import; DLINK captures that report using the
unchanged packaged LINK 1.3. The on-disk guide is `DASM.TXT`.


##### Starting DASM and setting logical bounds

Keep Utilities on B: and work on a writable disk. Run `B0:DASM`, then use H for
the interactive command summary. `B0:DASM /HELP` and `B0:DASM /VER` display
usage or identification without creating files. DSYM and DLINK also accept
noncreating `/VER` queries. ZSM4 and LINK retain their original third-party
interfaces and versions; these queries have not been added to them.

At DASM's prompt, read an exact file with a command such as `RPROGRAM.COM`.
File operands support drives A..P and users 0..31, for example
`RA7:PROGRAM.COM`; unqualified operands use the caller's original drive/user.
DASM keeps at most 8,192 input bytes in memory and refuses an empty input.
It has no disk-backed analysis paging or full-64-KiB input residency.

CP/M records do not reveal the logical byte length of a program. After loading,
use `Nhex` to select its measured logical length; without N, every physical
record byte is input, including trailing `00h`, `1Ah` or `FFh`. Do not infer the
length by stripping those values: they can be real program data. DASM addresses,
lengths and range bounds are hexadecimal. `N5` means five logical bytes.

`Ohex` selects a logical origin, normally `0100h`. Range ends are exclusive;
an end-only bound may be `10000h`, but addresses cannot exceed `FFFFh` and an
interval cannot cross the address-space boundary. Thus `100,105` denotes five
bytes. Non-0100h origins generate PHASE/DEPHASE source: LINK still produces
packed bytes at 0100h, which must not be assumed runnable there.


##### DASM analysis and source output

| Command | Purpose |
| --- | --- |
| `H` / `?` | Interactive help / statistics. |
| `Lstart,end` / `QLstart,end` | List instructions; quiet listing feeds staged source output without the normal console listing. |
| `Dstart,end` | Dump bytes in a bounded range. |
| `C` / `Caddress,type` | Inspect control classifications / set a classification listed below. |
| `A` / `B` | Inherited data recognition / automatic symbol generation. |
| `DS` | Inspect the symbol table. |
| `Eaddress,.NAME` / `K.NAME` | Add / delete a symbol. |
| `;address,text` | Add a printable comment; `;address,` deletes it and `;` lists comments. |
| `Iaddress,[+|-]delta` | Safely rebase symbols at/above an address. |
| `Sname.ASM` | Begin staged source output. |
| `Pstart,end` | Emit the source prologue and equates for the selected interval. |
| `Z` | Finish and publish the staged ASM output. |
| `G` | Return to CP/M. |

A control point selects how subsequent bytes are interpreted, up to the next
control point or the selected end:

| Type | Interpretation |
| --- | --- |
| B | Byte data, using quoted strings where appropriate. |
| E | End-of-program marker. |
| H | Byte data in hexadecimal. |
| I | Instructions. |
| S | Storage region; exact source output still retains its initialized bytes. |
| W | Word data. |

Bare/continuation forms of L, D and F retain DASM's existing workflow; use H
for their syntax. Classify embedded data and review symbols before generating
source. Successful assembly alone does not prove a faithful disassembly.

`R` and `S` with `.SYM`, `.CTL` and `.DOC` import/export symbols, controls and
comments individually. `Rname.DSY` imports DSYM's canonical output.
`Sname.ALL` saves a versioned, checksummed session descriptor and uniquely named
components; `Rname.ALL` validates the complete graph before replacing live
analysis. Loading a session requires the same binary drive/user/name and
matching logical bytes. Keep the descriptor and its referenced components
together; the descriptor alone is not the saved analysis.


#### Examples

##### A ZSM4/LINK round trip
For a **five-byte** PROGRAM.COM produced from PROGRAM.MAC, use this sequence
from the writable work drive. Change the length and exclusive end for your
actual program, and choose fresh output names:

```text
B0:ZSM4 PROGRAM=PROGRAM
B0:DLINK PROGRAM
B0:DSYM PROGRAM.LOG
B0:DASM
RPROGRAM.COM
N5
RPROGRAM.DSY
SREBUILD.ASM
P100,105
QL100,105
Z
G
B0:ZSM4 REBUILD=REBUILD.ASM
B0:LINK REBUILD[A]
```

Check `Errors: 0` and all LINK diagnostics. Compare every byte of the declared
logical interval against the original; check CP/M record padding separately.
A one-byte absolute image requires an explicit `1Ah` padding byte outside the
logical interval to work around LINK's one-byte-output behavior. Do not execute
arbitrary disassembly inputs or assume output for a different logical origin
is runnable at 0100h.


#### Errors/Troubleshooting

##### DASM limits and recovery
DASM requires an active exclusive transient-memory ceiling of at least B200h
and always retains its fixed 8-KiB input limit. Resident extensions consume
headroom. DLINK gives its child a ceiling of A000h and needs room through
B810h for its own storage and margin; DSYM requires 2A92h. These limits refer
to active program memory, not the machine's total installed RAM.

ASM output remains staged until Z. Interrupting a listing invalidates pending
source output, so Z cannot publish it as complete. Ctrl-C offers confirmed
cancellation; on Model 4 use the BREAK key for ETX. An ordinary key stopping a
listing also invalidates the pending output. A declined Ctrl-C cancellation
does not make an interrupted listing complete.

Replacement retains a uniquely named backup. On errors, preserve the reported
`.$$$` stages and BAK copies until you have identified a complete file. A failed
session save can leave named `DSA00000.SYM`, `.DOC` and `.CTL` generation
components while the old descriptor graph remains usable. Do not delete files
referenced by the descriptor you intend to reload. CP/M renames do not provide
power-loss durability or atomic replacement of multiple files.

The [DASM qualification report](../engineering/DASM%20Qualification.md) records
normal RAM Model 4/trs80gp and z80pack component results and their exact media.
Physical hardware and whole-Utilities-release acceptance are separate. Original
imports, maintained source and build recipes accompany the images in
`BetterCPM-DASM-SOURCE.tar.gz`; retain that companion and `DASMCOPY.TXT` when
redistributing.

#### See Also

[DLINK](#dlink) · [DSYM](#dsym) · [LINK](#link) · [ZSM4](#zsm4)


<a id="ddt"></a>

### DDT

#### Description

Debug 8080 code using the supplied DDT adaptation on the primary Utilities disk. It retains the CP/M 2.2 debugger language and 8080 assembler/disassembler; it is not a Z80 debugger.

#### General Form

```text
DDT [file.COM | file.HEX]
DDT /VER
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Load a program for inspection | `B0:DDT PROGRAM.COM` |
| Identify without entering the debugger | `B0:DDT /VER` |

#### Detailed Reference

Run `B0:DDT` to inspect or enter an 8080 program, or `B0:DDT PROGRAM.COM` to load a program first. A HEX file is also accepted. `B0:DDT /VER` displays the BetterCP/M utility identity without starting the debugger. The locked utility identity is DDT 1.0 (005).

The debugger retains CP/M 2.2 DDT's command language. Addresses and numbers are hexadecimal. Commands execute when Enter is pressed.

| Command | Purpose |
| --- | --- |
| `Aaddress` | Enter 8080 assembly instructions; a dot ends entry. |
| `Dstart,end` | Display memory in hexadecimal and ASCII. |
| `Fstart,end,byte` | Fill an inclusive memory range. |
| `Gaddress,bp1,bp2` | Run with optional breakpoints. `G0` returns to CP/M. |
| `Hvalue,value` | Show hexadecimal sum and difference. |
| `Ifilename` then `R` | Select and read a COM or HEX input. |
| `Lstart,end` | List memory as 8080 instructions. |
| `Mstart,end,destination` | Move memory using DDT's existing forward-copy behavior. |
| `Saddress` | Substitute bytes; empty Enter advances, a dot finishes. |
| `Tcount` / `Ucount` | Trace or run a counted number of instructions without trace display. |
| `X` / `Xregister` | Examine machine state or replace a register/flag value. |

The usual omitted-operand and continuation forms remain available. This is an 8080 debugger: the program's use of Z80 code for editing does not add Z80 mnemonics to the debugger or extend its instruction-stepping model. Keep executable test programs and file copies separate from valuable work when modifying their memory.

Line input uses the shared editor with a 32-character limit. Ctrl-S/D move the cursor, Ctrl-A/F move by words, Ctrl-H or DEL erase left, and Ctrl-G erases under the cursor. Ctrl-U, Ctrl-X and Ctrl-Y clear the provisional line. Enter submits even an empty line. Unassigned control keys, including TAB, do not enter command text; type the original command's spaces or commas. Excess characters sound the bell and remain unaccepted until space is made.

Escape abandons the active interactive command and returns to the main `-` prompt. It does not undo earlier accepted assembly or substitution changes. Ctrl-C retains its historical warm-boot meaning. The original dot terminator remains available within assembly and substitution; it is not replaced by Escape. The existing address/register prefix stays visible while editing, with an underscore at end of input and a horizontally scrolling 24-cell field.

DDT relocates below the current BDOS gateway and reduces the debuggee's available memory. This build reserves 20 pages (5120 bytes), compared with the historical debugger's 16 pages. It does not require a loaded screen backend or a monitor personality. Its file is 6528 bytes. The exact 4864-byte historical reference is preserved as a separate engineering baseline and is not the Utilities Disk program.

BetterCP/M cpmsim command/input checks and Model 4/trs80gp screen/physical-keyboard checks pass. The Model 4 campaign verifies cursor editing, scrolling, CLEAR cancellation without committing an operand, A/L and G0/BREAK return on disposable current-system disks. DDT also passes release-placement checks from Utilities B: beside normal System A:, including Model 4 M4SCRN/ADM3A. For example, `B:DDT TINY.COM` loads the debuggee from your current A: drive and returns there after G0 or Ctrl-C. Release scope and exact artifacts are governed by the non-documentation lock.


##### Interactive command language

DDT prompts with `-`. Addresses, counts, data and register values use hexadecimal notation. Commas separate operands. The embedded assembler and disassembler use 8080 mnemonics, even on the Z80 processor. Default debuggee entry is 0100h; loading a file and executing it are separate actions.

| Command | Purpose |
| --- | --- |
| `Aaddress` | Assemble 8080 instructions interactively; `.` ends assembly. |
| `Dstart,end` | Display memory; the continuation form retains DDT's next address. |
| `Fstart,end,byte` | Fill a memory interval. |
| `G` / `Gaddress` | Execute from the current / supplied PC; optional breakpoint operands follow DDT syntax. |
| `Hvalue1,value2` | Display hexadecimal sum and difference. |
| `Ifilespec` | Set the input command/default FCB used by a subsequent read. |
| `Lstart,end` | Disassemble 8080 instructions. |
| `Mstart,end,destination` | Move a memory interval. |
| `R` / `Roffset` | Read the selected COM/HEX input, optionally relocated by an offset. |
| `Saddress` | Substitute bytes interactively; `.` finishes. |
| `T` / `Tcount` | Trace instructions with register display. |
| `U` / `Ucount` | Execute instructions without per-step trace display. |
| `X` / `Xregister` | Display registers / replace a selected register value. |

The historical execution model uses RST 7 breakpoints and restores replaced instructions. Do not overwrite the debugger's relocated resident area or assume the entire machine RAM is debuggee space. BDOS forwarding and ordinary CP/M page-zero conventions remain in effect. Use G0 to return to the command environment; use the CCP's SAVE command afterward only when you know the desired memory interval and page count.


##### Input editing

The adaptation adds shared line editing without changing the debugger command language. Ctrl-S/D move left/right; Ctrl-A/F move by words; Ctrl-H or DEL erases left; Ctrl-G erases under the cursor. Ctrl-U/X clears provisional input; Enter submits it. Escape discards the current provisional input and returns to the main prompt. It does not undo earlier accepted assembly or substitution changes. Ctrl-C invokes warm boot.

The 32-byte command buffer has a bounded visible field with horizontal scrolling. There is no persistent debugger history or full-screen debugger interface. `/VER` is processed before debugger relocation or input loading. Further execution, continuation and breakpoint grammar follows the supplied CP/M 2.2 DDT behavior; see the [DDT adaptation contract](../engineering/DDT%20Specification.md) for the exact retained scope.

#### Examples

```text
B0:DDT PROGRAM.COM
```

Load a program for inspection. Substitute the locations and filenames appropriate to your session.

#### Errors/Troubleshooting

Numbers and addresses are hexadecimal. DDT relocates below the BDOS gateway and reduces debuggee memory. Use only controlled code when executing G/T/U. Ctrl-C or G0 returns through warm boot. Escape abandons a provisional interactive input without undoing previously accepted A/S changes. Do not assume DDT file operands accept BetterCP/M DU selectors.

#### See Also

[DASM](#dasm) · [GET](#get) · [SAVE](#save)


<a id="dlink"></a>

### DLINK

#### Description

DLINK.COM is supplied on the primary Utilities disk. Run the verified packaged B0:LINK.COM in a bounded child workspace and capture its complete report.

#### General Form

```text
DLINK base
DLINK output module [module...]
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Link and capture checked output | `B0:DLINK PROGRAM` |

#### Detailed Reference

```text
B0:DLINK PROGRAM
B0:DLINK RESULT ONE TWO
B0:DSYM PROGRAM.LOG
B0:DSYM A7:PROGRAM.LOG C7:
```

`DLINK base` links `base.REL`. With explicit modules, the first operand is the
output base and the remaining operands are input modules. The output base has
no extension; inputs may omit `.REL`. All modules and outputs must share the
output user area, although their drives may differ. Unqualified operands use
the caller's original drive/user. Outputs `base.COM`, `base.SYM` and `base.LOG`
must all be absent before starting.

DLINK loads only the verified packaged **B0:LINK.COM**. It provides a bounded
child workspace, captures the report in a unique `DLGnnnnn.$$$` stage and
publishes the LOG after checked orderly completion. It does not enable LINK's
legacy A disk-scratch option. Jobs needing more child workspace fail safely.
Inspect LINK diagnostics; COM/SYM files left by a failed job are unverified.
DLINK's `/VER` identifies the wrapper, not a new version of LINK.


DASM requires an active exclusive transient-memory ceiling of at least B200h
and always retains its fixed 8-KiB input limit. Resident extensions consume
headroom. DLINK gives its child a ceiling of A000h and needs room through
B810h for its own storage and margin; DSYM requires 2A92h. These limits refer
to active program memory, not the machine's total installed RAM.

ASM output remains staged until Z. Interrupting a listing invalidates pending
source output, so Z cannot publish it as complete. Ctrl-C offers confirmed
cancellation; on Model 4 use the BREAK key for ETX. An ordinary key stopping a
listing also invalidates the pending output. A declined Ctrl-C cancellation
does not make an interrupted listing complete.

Replacement retains a uniquely named backup. On errors, preserve the reported
`.$$$` stages and BAK copies until you have identified a complete file. A failed
session save can leave named `DSA00000.SYM`, `.DOC` and `.CTL` generation
components while the old descriptor graph remains usable. Do not delete files
referenced by the descriptor you intend to reload. CP/M renames do not provide
power-loss durability or atomic replacement of multiple files.

The [DASM qualification report](../engineering/DASM%20Qualification.md) records
normal RAM Model 4/trs80gp and z80pack component results and their exact media.
Physical hardware and whole-Utilities-release acceptance are separate. Original
imports, maintained source and build recipes accompany the images in
`BetterCPM-DASM-SOURCE.tar.gz`; retain that companion and `DASMCOPY.TXT` when
redistributing.

#### Examples

```text
B0:DLINK PROGRAM
```

Link and capture checked output. Substitute the locations and filenames appropriate to your session.

#### Errors/Troubleshooting

Check the operand grammar and the selected drive/user area. For disk failures, preserve the source and any reported recovery files before retrying. See the [shared system messages](#system-messages) for command lookup, media, configuration and extension diagnostics.

#### See Also

[DASM](#dasm) · [DSYM](#dsym) · [LINK](#link) · [ZSM4](#zsm4)


<a id="dsym"></a>

### DSYM

#### Description

DSYM.COM is supplied on the primary Utilities disk. Convert a complete successful DLINK report to DASM symbol interchange.

#### General Form

```text
DSYM [DU:]base.LOG [destination-DU:]
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Convert a checked linker report | `B0:DSYM PROGRAM.LOG` |

#### Detailed Reference

`DSYM [DU:]base.LOG [destination-DU:]` writes a new `base.DSY`, using the
complete report's final addresses directly. It refuses an existing destination,
a bare `.SYM`, failed-link diagnostics, truncated reports and conflicting
symbols. Use a complete DLINK LOG: a plausible symbol file is not proof of a
successful link. The default public export significance is six characters;
DSYM cannot recover source spelling already lost by LINK. DASM interchange
names may contain up to 12 characters; DSYM permits 255 unique normalized
records, coalesces exact duplicates and preserves distinct aliases.

DASM requires an active exclusive transient-memory ceiling of at least B200h
and always retains its fixed 8-KiB input limit. Resident extensions consume
headroom. DLINK gives its child a ceiling of A000h and needs room through
B810h for its own storage and margin; DSYM requires 2A92h. These limits refer
to active program memory, not the machine's total installed RAM.

ASM output remains staged until Z. Interrupting a listing invalidates pending
source output, so Z cannot publish it as complete. Ctrl-C offers confirmed
cancellation; on Model 4 use the BREAK key for ETX. An ordinary key stopping a
listing also invalidates the pending output. A declined Ctrl-C cancellation
does not make an interrupted listing complete.

Replacement retains a uniquely named backup. On errors, preserve the reported
`.$$$` stages and BAK copies until you have identified a complete file. A failed
session save can leave named `DSA00000.SYM`, `.DOC` and `.CTL` generation
components while the old descriptor graph remains usable. Do not delete files
referenced by the descriptor you intend to reload. CP/M renames do not provide
power-loss durability or atomic replacement of multiple files.

The [DASM qualification report](../engineering/DASM%20Qualification.md) records
normal RAM Model 4/trs80gp and z80pack component results and their exact media.
Physical hardware and whole-Utilities-release acceptance are separate. Original
imports, maintained source and build recipes accompany the images in
`BetterCPM-DASM-SOURCE.tar.gz`; retain that companion and `DASMCOPY.TXT` when
redistributing.

#### Examples

```text
B0:DSYM PROGRAM.LOG
```

Convert a checked linker report. Substitute the locations and filenames appropriate to your session.

#### Errors/Troubleshooting

Check the operand grammar and the selected drive/user area. For disk failures, preserve the source and any reported recovery files before retrying. See the [shared system messages](#system-messages) for command lookup, media, configuration and extension diagnostics.

#### See Also

[DASM](#dasm) · [DLINK](#dlink) · [LINK](#link) · [ZSM4](#zsm4)


<a id="ed"></a>

### ED

#### Description

Edit text with the supplied CP/M 2.2 context-editor reimplementation. ED.COM is on both System disks. It accepts one exact filename and simple DU addressing, not the shared multi-file selector grammar.

#### General Form

```text
ED filespec [output-DU:]
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Edit a work file | `ED D0:NOTES.TXT` |
| Use a separate output location | `ED D0:NOTES.TXT D3:` |

#### Detailed Reference


##### Files and editing buffer

ED reads source text into an in-memory editing buffer and writes completed text to a work file. File size need not equal buffer capacity: use append/write operations to advance through larger sources. Text already written out cannot be reread merely by moving the buffer pointer backwards. An optional output DU identifies work/output location, not a second filename.

Simple forms include `FILE.TXT`, `B:FILE.TXT`, `B7:FILE.TXT`, and `7:FILE.TXT`. Users range from 0 through 31. Wildcards, lists, ranges and attribute predicates are rejected. Unlike many utilities, successful explicit output-location completion can leave the corresponding output DU selected. Do not assume unconditional restoration to the caller's DU.


##### Commands

Counts and signed movement retain ED's decimal semantics; omitted, zero, negative and `#` counts have command-specific meanings. Do not substitute the hexadecimal conventions of DDT or PEEK. String-entry case affects historical translation behavior and is not globally uppercased. Ctrl-Z ends insert/string input in its defined context.

| Command | Operation |
| --- | --- |
| `nA` | Append source lines to the editing buffer; `#A` appends as much as fits. |
| `B` / `-B` | Move to the beginning / end of the buffer. |
| `nC` / `-nC` | Move forward / backward by characters. |
| `nD` / `-nD` | Delete characters forward / backward. |
| `E` | Finish remaining source, publish the edit and exit. Use alone. |
| `nFstring` | Find a string using ED's string terminator. |
| `H` | Save and restart from the head. Use alone. |
| `I` | Enter insert mode; Ctrl-Z returns to command input. |
| `J` | Juxtapose strings using ED's search/insert grammar. |
| `nK` / `-nK` | Delete lines in the specified direction. |
| `nL` / `-nL` | Move by lines within buffered text. |
| `nMcommands` | Repeat a command macro. |
| `N` | Find the next occurrence while advancing source through the buffer. |
| `O` | Abandon the current edit and restart from the original. Use alone. |
| `nP` | Move/type pages. |
| `Q` | Quit without committing the edit. Use alone. |
| `Rfilespec` | Read library text at the current position. |
| `nSfind^Zreplace^Z` | Substitute where ^Z denotes a typed Ctrl-Z string separator. |
| `nT` | Type lines; `0T` types from the start of the current line to the pointer. |
| `U` / `-U` | Enable / disable uppercase translation. |
| `V` / `-V` | Enable / disable verification display; `0V` reports buffer use. |
| `nW` | Write lines out of the buffer. |
| `nX` | Transfer lines to the temporary library facility. |
| `nZ` | Delay. |
| `n:` | Move to a global source line number within accessible buffered text. |
| `:nT` / `:nK` | Derive type/delete range from the current global line to line n. |

String commands have their own search, juxtaposition and macro rules; the [ED specification](../engineering/ED%20Specification.md#27-search-substitute-juxtaposition-and-macro-commands) records the precise CP/M 2.2 compatibility boundary. Source counts include lines already written, but absolute addressing does not reload them.


##### Finishing, restarting and retaining work

Use E, H, O or Q alone rather than embedding them in a compound command. E and H perform the historical work/original/backup transition; no additional unsaved-changes prompt is added. Q abandons current unpublished editing; O restarts against the original according to ED's file lifecycle. Read-only inputs and output collisions retain their own protections.

If final publication cannot rename a file, BetterCP/M stops and reports the retained work rather than blindly continuing the DRI rename sequence. Keep the work file and any BAK until the edited text is recovered. H does not restart after that failure. Disk-full, directory-full and buffer-full are different conditions; writing buffer text cannot repair unavailable disk space. See [ED behavior and failure rules](../engineering/ED%20Specification.md) for library naming, command limits and documented DRI corrections.

#### Examples

For a new `D0:NOTES.TXT`, enter `I`, type the desired text, then press Ctrl-Z to return to command mode. Use `B` followed by `#T` to inspect buffered text, and enter `E` alone to finish and save. For an existing file use `#A` first to append as much source text as fits. Use `Q` alone to abandon an edit; no extra unsaved-changes question is added.

#### Errors/Troubleshooting

Command errors use the historical BREAK diagnostic. Correct the command rather than assuming it completed. On `Rename failed. Edited text retained in work file.`, stop: preserve the source, .BAK and edited work file and inspect which publication step failed. H does not restart after a failed publication. Buffer exhaustion is distinct from disk-full and directory-full failures.

#### See Also

[TED](#ted) · [PIP](#pip) · [file specifications](#file-specifications)


<a id="link"></a>

### LINK

#### Description

Use the supplied Digital Research LINK 1.3 relocatable linker. It is on the primary Utilities disk and retains its original interface and identity; BetterCP/M /HELP and /VER have not been added.

#### General Form

```text
LINK output=module[,module...][A]
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Build an absolute executable | `B0:LINK PROGRAM[A]` |

#### Detailed Reference

[Command and Utilities Reference](#zsm4) · [ZSM4](#zsm4)

The Utilities Disk carries unmodified Digital Research LINK 1.3. It combines
relocatable objects such as ZSM4's `.REL` output into a CP/M `.COM` program.

With Utilities on B: and `PROGRAM.REL` on your logged writable drive:

```text
B:LINK PROGRAM[A]
```

`[A]` selects the absolute CP/M executable output. To combine modules and choose
an output stem:

```text
B:LINK CHECK=MAIN,PART[A]
```

This writes `CHECK.COM`. Resolve all external symbols before running it. LINK
prints `CODE SIZE`, `DATA SIZE` and `COMMON SIZE`; an `UNDEFINED SYMBOLS` report
means the output is not a successful executable, even if a COM file was written.
Native output is rounded to CP/M records with `1Ah` padding.

LINK retains its native `LINK 1.3` identity; BetterCP/M `/HELP` and `/VER` have
not been added. Copyright remains with Digital Research. `LINKCOPY.TXT` contains
the retained CP/M permission and clarification. In the Utilities ZIP, `source/Toolchain-Provenance.json` identifies the shipped
executable. The upstream record is at
`licenses/third_party/dri-link/provenance.json`. See also the
[guide to third-party records](../LICENSING.md#third-party-records).

#### Examples

```text
B0:LINK PROGRAM[A]
```

Build an absolute executable. Substitute the locations and filenames appropriate to your session.

#### Errors/Troubleshooting

Check the operand grammar and the selected drive/user area. For disk failures, preserve the source and any reported recovery files before retrying. See the [shared system messages](#system-messages) for command lookup, media, configuration and extension diagnostics.

#### See Also

[ZSM4](#zsm4) · [DLINK](#dlink) · [DSYM](#dsym) · [DASM](#dasm)


<a id="ted"></a>

### TED

#### Description

TED.COM is supplied on the primary Utilities disk (normally B0). Edit text using the supplied full-screen editor.

#### General Form

```text
TED [filespec]
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Edit a work file | `B0:TED D0:NOTES.TXT` |

#### Detailed Reference

`/HELP` shows the compact utility quick reference. `/HELP` and `/VER` are
case-insensitive exact tokens, ignore other arguments, and return before file,
drive/user or screen-provider services; HELP takes precedence when both occur.

TED edits one text document using command, screen and browse modes. It retains
TED's editing behavior with an agreed subset of WordStar command sequences.
There is no undo, persistent block marking, WordStar document formatting or
Ctrl-Q command prefix. The on-disk guide is `TED.TXT`.


##### Starting TED

TED requires an 80-by-24 screen backend and the ANSI terminal module. Before
starting it, use `RSX LIST` to check what is loaded:

| Target | Screen backend | Terminal module |
| --- | --- | --- |
| Model 4 / trs80gp | M4SCRN | integrated ANSI |
| Model II / trs80gp | M2SCRN | integrated ANSI |
| z80pack / cpmsim with an ANSI host terminal | ANSISCRN | integrated ANSI |

Load the missing SCRN backend with `RSX LOAD M4SCRN`, `RSX LOAD M2SCRN`, or `RSX LOAD ANSISCRN` for the selected target. TED still uses SCRN; the integrated ANSI module alone does not replace that client interface.
Unload a conflicting terminal module, such as ADM3A, before `RSX LOAD ANSI`.
TED does not load these modules itself. Keep the module configuration fixed
while editing and keep the host terminal large enough for the 80-by-24 viewport.

```text
B0:TED A0:PROGRAM.MAC
B0:TED
B0:TED /HELP
B0:TED /VER
```

The first command reads an existing file; the second starts without a filename.
`/HELP` and `/VER` display usage or identification without opening a document.
File operands accept one exact 8.3 name, optionally qualified with drive A
through P and user 0 through 31, such as `A7:PROGRAM.MAC`. Wildcards are not
accepted. An explicitly supplied unqualified filename uses the drive/user from
which TED was launched, independently of the Utilities Disk's location.


##### TED modes and screen keys

At `TED>`, enter `S` to start screen editing. Empty Ctrl-C also enters screen
mode; Ctrl-C following a command executes it and then enters screen mode.
Ctrl-Z returns from screen editing to command mode. Ctrl-B or Ctrl-N enters
browse mode; Return, Ctrl-C or Ctrl-Z returns from browse to screen editing.
Enter `EX` at `TED>` to leave TED. Discarding modified text requires an explicit
Yes; the default is No.

These bindings apply in **screen mode**:

| Key | Action |
| --- | --- |
| Ctrl-S / Ctrl-D | Left / right within the line. |
| Ctrl-E / Ctrl-X | Up / down. |
| Ctrl-R / Ctrl-C | Page up / down. |
| Ctrl-A / Ctrl-F | Previous / next word within the line. |
| Ctrl-T | Delete the range traversed by next-word movement. |
| Ctrl-H or Backspace | Backspace, with the mode-dependent behavior below. |
| Ctrl-G, DEL or Ctrl-] | Delete the character to the right; no effect at line end. |
| Ctrl-I or TAB | Insert a literal TAB. |
| Return | Split the line at the cursor. |
| Ctrl-J | Insert an empty line below. |
| Ctrl-P | Duplicate the current line. |
| Ctrl-Y or Ctrl-^ | Delete the current line. |
| Ctrl-V | Toggle insert/overwrite; TED starts in overwrite mode. |
| Ctrl-Q / Ctrl-O | Previous / next tab stop. |
| Ctrl-L | Toggle between line beginning and end. |
| Ctrl-U | Toggle between screen top and bottom. |
| Ctrl-B or Ctrl-N | Enter browse mode. |
| Ctrl-Z | Return to command mode. |
| Ctrl-_ | Redraw. |
| Ctrl-K | Begin a block/file command, listed below. |

Ctrl-W, Ctrl-@ and Ctrl-\ are unused. Escape cancels an active prefix or prompt.
The Model 4's raw arrow codes collide with TED control commands, including
insertion, deletion and the Ctrl-K prefix. Use Ctrl-E/X/S/D for navigation.
The current Model 4 console has no physical chord for Ctrl-underscore; that
ASCII redraw binding remains available where the console can supply it.

In overwrite mode, Backspace blanks the preceding character. In insert mode,
it removes that character and shifts following text left. At the start of a
line it joins the preceding line. Moving beyond a short line enters virtual
columns without adding spaces; typing there supplies the necessary spaces.
Tabs display to eight-column stops but remain TAB bytes in the file. Long lines
scroll horizontally. TED does not wrap words, indent automatically or trim
trailing spaces.

Word operations stop at line boundaries. Separators are space, TAB and
`. , : ; ! ?`; hyphens and underscores remain word characters. Word-right skips
the remainder of the current word and following separators; word-left scans
left over separators to the beginning of the preceding/current word.


##### TED block and file sequences

Press Ctrl-K, release it, then the indicated letter. Upper/lowercase letters
and the corresponding Ctrl-letter are accepted. These sequences invoke TED's
existing whole-line operations and file argument prompts.

| Sequence | Action |
| --- | --- |
| Ctrl-K C | Copy: prompt for first/last source lines and the line to copy after. |
| Ctrl-K V | Move: prompt for first/last source lines and the line to move after. |
| Ctrl-K Y | Delete: prompt for first/last source lines. |
| Ctrl-K R | Read a file through TED's R argument prompt. |
| Ctrl-K W | Write through TED's W argument prompt, including ranges and append. |
| Ctrl-K S | Save to the default filename and continue editing. |
| Ctrl-K X | Save, then exit only after successful publication. |
| Ctrl-K Q | Quit, with default-No confirmation before discarding changes. |

Line ranges include both numbered endpoints. There are no block marks or
character-block selections. Ctrl-K replaces TED's former insert-above binding;
move up one line and use Ctrl-J where appropriate. Ctrl-K D is not assigned.
For an unnamed document, supply the required filename through the W prompt.


##### TED command mode, search and replacement

Line numbers are decimal and one-based; position columns start at zero.
Enter these commands at `TED>`, without the prompt text:

| Example | Action |
| --- | --- |
| `P 10 5` | Position at line 10, visual column 5. |
| `S 10` | Position at line 10 and enter screen editing. |
| `/text/` | Find a forward, case-sensitive literal match within a line. |
| `/text/(1,20)+1` | Search lines 1..20, then move one line after the match. |
| `SU /old/new/` | Substitute matching text. |
| `SU M /old/new/` | Ask before each substitution. |
| `SU 3 /old/new/` | Replace up to three matches. |
| `M 2 4 8` | Copy lines 2..4 after line 8. |
| `MD 2 4 8` | Move lines 2..4 after line 8. |
| `D 2 4` | Delete lines 2..4. |
| `R (5) OTHER.TXT (2,4)` | Insert source lines 2..4 after document line 5. |
| `W 2 4 PART.TXT` | Write whole lines 2..4 to PART.TXT. |
| `W OTHER.TXT $` | Safely append to OTHER.TXT; `0` selects replacement. |
| `W` | Save the whole document to its default filename. |
| `F` / `FR` | Show the default filename / free memory above the static image. |
| `PR 2 4` | Print selected lines through the console. |
| `CL` / `EX` | Clear / exit, with an abandonment safeguard. |

Search does not wrap or cross line endings. Use `P 1` before searching from
the beginning. There is no repeat-find key. Confirmations use immediate Y/N:
Y approves, N or Enter declines, and ESC or Ctrl-C cancels. Invalid responses
retain the question and its displayed default `[N]`; no Enter is needed after
Y or N. In confirmed substitution, No skips one match and Cancel stops the
remaining substitutions. An empty replacement deletes matches, while an empty
search is refused.

R inserts after the specified line, or appends to the document if that position
is omitted. It also selects the default filename. An alternate filename or
line-range W does not silently change that default or clear unsaved-document
state. Default W retains the full drive/user identity selected by the latest R.

Command-field editing differs from screen editing: Ctrl-E recalls the previous
command, Ctrl-G recalls and enters it, Ctrl-D recalls one byte, Ctrl-U or
Ctrl-^ clears the field, TAB supplies spaces, and Backspace/DEL deletes left.
Ctrl-Z submits EX with its normal abandonment safeguard. These are TED's
command-field facilities, not additional screen bindings.


#### Examples

```text
B0:TED D0:NOTES.TXT
```

Edit a work file. Substitute the locations and filenames appropriate to your session.

#### Errors/Troubleshooting

##### TED text preservation, saves and recovery

TED preserves literal tabs, trailing spaces, mixed CRLF/LF/CR line endings and
an absent final newline. An unchanged full-document write preserves physical
EOF padding too. Whole-line transfers add only the separators required at new
boundaries. Unsupported control/high-bit bytes, embedded EOF markers and lines
over 4,095 bytes are refused with line/offset diagnostics. Input is limited to
8,191 data records (1,048,448 bytes) and available disk space. Numeric line
operands remain bounded to 16 bits; the file-size limit does not remove that
command-language limit.

Saves write and verify a unique stage before replacement. The old target is
retained as `TEBnnnnn.BAK`; TED does not erase it to create the new file.
Replacement and read-only/system protection require explicit authorization.
Allow space for checkpoints, the output stage and retained backups. A failed
or cancelled save leaves TED active rather than treating the document as saved.

If saving fails, record the exact workspace, stage and backup names reported.
Keep those files until you have checked which copy is complete. Inspect an
ambiguous rename failure before retrying; do not delete the only complete copy.
Retained backups are yours to clean up after verification.

`WORK A0:` selects a workspace drive/user. `RECOVER A0:TEWnnnnn.$$$` validates
and copies a retained checkpoint after confirmation; replace the placeholder
with the actual name TED reported. The recovery source is retained. Recovery
restores the last committed checkpoint: the latest dirty line can still be
only in RAM. It is not autosave or undo. An older checkpoint may lack a newly
chosen filename, so specify a filename when saving recovered text. Normal exit
removes only a verified session-owned checkpoint; ambiguous stages/backups are
retained for inspection.

TED checks its active transient-memory ceiling before using its private stack.
Loaded extensions reduce available memory. Component qualification covers the
recorded normal RAM z80pack and Model 4/trs80gp configurations; physical hardware,
ROM/XIP and checked-profile application qualification are separate. See the
[TED qualification report](../engineering/TED%20Qualification.md) for exact
images and console limitations. Complete source and native-build material
accompany the host package in `BetterCPM-TED-SOURCE.tar.gz`; retain that companion
and `TEDCOPY.TXT` when redistributing.

#### See Also

[file specifications](#file-specifications) · [system messages](#system-messages)


<a id="zsm4"></a>

### ZSM4

#### Description

Use the supplied ZSM4 4.7 macro assembler. It is on the primary Utilities disk and retains its original interface and identity; BetterCP/M /HELP and /VER have not been added.

#### General Form

```text
ZSM4 output=source
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Assemble a source module | `B0:ZSM4 PROGRAM=PROGRAM` |

#### Detailed Reference

[Command and Utilities Reference](#zsm4) · [LINK](#link)

The Utilities Disk carries unmodified ZSM4 4.7 for Z80-compatible CP/M systems.
It reads assembly source and produces Microsoft/DRI-format relocatable objects.
This is Hector Peraza's tool, with the earlier contributors acknowledged in its
source; its original interface and version remain intact.

Put `PROGRAM.MAC` on the writable work disk in D:. With primary Utilities in B:, use the following sequence.

```text
D:
B:ZSM4 PROGRAM=PROGRAM
B:LINK PROGRAM[A]
PROGRAM
```

The explicit left-hand name selects the output stem; the right-hand name
selects the source. Includes resolve on the output drive. Use `CSEG` for
relocatable code. `ORG 100H` alone can introduce an unwanted 256-byte gap when
linked; the compression native-build procedure documents its special `.PHASE`
preparation. Keep source and output on a work disk, not the Utilities disk.
Assembly reports `Errors: 0` on success. Inspect diagnostics before linking;
batch continuation alone is not proof that assembly succeeded.

`/HELP` and `/VER` are BetterCP/M-owned command conventions and have not been
added to this third-party executable. ZSM4 displays its native V4.7 banner.
The complete upstream manual, source, tests and Makefile accompany the Utilities
images in `ZSM4-SOURCE.tar.gz`; see `zsm4-source/docs` after unpacking on the host.

ZSM4 is GPL-2.0-or-later. The disk contains `ZSM4COPY.TXT`; distribute the full
source companion with these images. In the Utilities ZIP, `source/Toolchain-Provenance.json`
identifies the shipped executable. The upstream record is at
`licenses/third_party/zsm4/provenance.json`. See also the
[guide to third-party records](../LICENSING.md#third-party-records).

#### Examples

```text
B0:ZSM4 PROGRAM=PROGRAM
```

Assemble a source module. Substitute the locations and filenames appropriate to your session.

#### Errors/Troubleshooting

Check the operand grammar and the selected drive/user area. For disk failures, preserve the source and any reported recovery files before retrying. See the [shared system messages](#system-messages) for command lookup, media, configuration and extension diagnostics.

#### See Also

[LINK](#link) · [DLINK](#dlink) · [DSYM](#dsym) · [DASM](#dasm)


<a id="archives-and-compression"></a>

## Archives and compression


<a id="cr"></a>

### CR

#### Description

Crunch. Supplied on the primary Utilities disk. The source remains in place; existing output is refused.

#### General Form

```text
CR [drive:]file [destination-drive:]
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Show command-specific help | `B0:CR /HELP` |

#### Detailed Reference

[Command and Utilities Reference](#archives-and-compression) · [UNCR](#uncr)

CR writes a CRUNCH 2.x-format file in one input pass while keeping the source.
Use UNCR to restore it. It writes the supported significant revision `20h`
with an additive checksum; there is no format-version or checksum-mode switch.

##### Syntax

```text
CR [drive:]file [destination-drive:]
CR /H
CR /HELP
CR /VER
```

Give one exact 8.3 source name and an optional destination drive such as `B:`.
Both use your current user area. Output defaults to the logged drive, not the
source or command's drive. Wildcards, paths, explicit user/DU file operands,
output filenames and other switches are not accepted. `/HELP` and `/VER` ignore other arguments. See the
[shared command rules](#archives-and-compression)
for program lookup, filename syntax and drive defaults.

##### Help

`CR /HELP` displays a compact purpose/Usage corner followed by an unframed
Options list, then returns without accessing files. Examples, defaults and
restrictions are described below. Letter case and surrounding spaces or TABs
do not matter.
An exact `/H` or `/HELP` token anywhere in the command ignores other arguments and
shows help. If `/VER` is also present, help takes precedence in either order.
Longer tokens such as `/HELPER` are syntax errors. Empty or malformed commands
show short syntax and `Use CR /HELP for help.`

The help screen is:

```text
CR 1.0 (007)
  - - -
 | CRUNCH compression
 |
 |   Usage: CR [drive:]file [destination-drive:]

   Options:
     /H /HELP    Display this help.
     /VER        Display utility identification.
```

##### Version identification

`CR /VER` shows the utility identity and returns to the command prompt without
opening files or starting compression/expansion. `/ver` and mixed letter case
work too. For the current build:

```text
CR 1.0 (007)
  - - -
 | BetterCP/M Utilities
 | CRUNCH File Compression
```

Version and build numbers come from the standard utility metadata. The build
counter advances with published executable changes; it does not reset at a new
version. An exact `/VER` token anywhere in the command shows identification and ignores
other arguments, unless `/H` or `/HELP` is also present, in which case help is shown.
Normal file
processing does not print this identification banner.

##### Output name and supported files

| Source | Output |
| --- | --- |
| `REPORT.TXT` | `REPORT.TZT` |
| `CODE.ABC` | `CODE.AZC` |
| `SHORT.A` or `SHORT.AB` | `SHORT.AZ` |
| `CODE.AZC` | `CODE.ZZZ` |
| `NOEXT` | `NOEXT.ZZZ` |

CR replaces the middle extension character with Z. A missing extension or an
existing middle Z selects `.ZZZ`; `.ZZZ` input is refused even with another
destination drive. This fallback differs from LZH's successive Y naming rule.
CR stores the original filename, including three padded extension slots, for UNCR.

```text
CR A:REPORT.TXT B:
UNCR B:REPORT.TZT C:
```

This leaves the original on A:, the crunched file on B: and the restored
`REPORT.TXT` on C:, all in your current user area. An existing C: output is refused.

##### Completion and messages

Success prints `CR: complete.` and returns to the prompt. Source files stay
in place; existing outputs are refused. Processing uses a temporary on the
destination drive. See [file handling and recovery](#archives-and-compression)
for record padding, free space, read/write/close/rename errors and interrupted
operations. A final file is published only after successful processing and closes.

| Message | Meaning/recovery |
| --- | --- |
| `CR: cannot crunch .ZZZ names.` | This input extension has no supported next name. Check that you chose the intended original file. |
| `CR: encoding failed.` | An encoding/configuration/capacity failure occurred; retain the source. |

CR uses one pass and resets its compression dictionary at capacity. It does not
promise the same compressed bytes, size or heuristics as a historical encoder.
Its output is an individual CRUNCH file, not an archive. All input-record bytes,
including `1Ah`, are preserved for restoration.

##### Related documentation

- [UNCR command](#uncr)
- [Common operating rules](#archives-and-compression)
- In the Documentation ZIP, see `docs/engineering/CR-UNCR Specification.md`.

#### Examples

```text
B0:CR /HELP
```

Show command-specific help. Substitute the locations and filenames appropriate to your session.

#### Errors/Troubleshooting

Check the operand grammar and the selected drive/user area. For disk failures, preserve the source and any reported recovery files before retrying. See the [shared system messages](#system-messages) for command lookup, media, configuration and extension diagnostics.

#### See Also

[NOAH](#noah) · [query conventions](#query-conventions)


<a id="lzh"></a>

### LZH

#### Description

Compress in CP/M CrLZH format. Supplied on the primary Utilities disk. The source remains in place; existing output is refused.

#### General Form

```text
LZH [drive:]file [destination-drive:]
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Show command-specific help | `B0:LZH /HELP` |

#### Detailed Reference

[Command and Utilities Reference](#archives-and-compression) · [UNLZH](#unlzh)

LZH writes a CP/M CrLZH file in one input pass while keeping the original.
Use UNLZH to restore it. LZH emits the newer `20h` CrLZH variant with additive
checking. It creates an individual compressed file, not a general LHA archive.

##### Syntax

```text
LZH [drive:]file [destination-drive:]
LZH /H
LZH /HELP
LZH /VER
```

Give one exact 8.3 source name and an optional destination drive such as `B:`.
Both use your current user area. Output defaults to the logged drive, not the
source or command's drive. Wildcards, paths, explicit user/DU file operands,
output filenames and other switches are not accepted. `/HELP` and `/VER` ignore other arguments. See the
[shared command rules](#archives-and-compression)
for program lookup, filename syntax and drive defaults.

##### Help

`LZH /HELP` displays a compact purpose/Usage corner followed by an unframed
Options list, then returns without accessing files. Examples, defaults and
restrictions are described below. Letter case and surrounding spaces or TABs
do not matter.
An exact `/H` or `/HELP` token anywhere in the command ignores other arguments and
shows help. If `/VER` is also present, help takes precedence in either order.
Longer tokens such as `/HELPER` are syntax errors. Empty or malformed commands
show short syntax and `Use LZH /HELP for help.`

The help screen is:

```text
LZH 1.0 (007)
  - - -
 | CrLZH compression
 |
 |   Usage: LZH [drive:]file [destination-drive:]

   Options:
     /H /HELP    Display this help.
     /VER        Display utility identification.
```

##### Version identification

`LZH /VER` shows the utility identity and returns to the command prompt without
opening files or starting compression/expansion. `/ver` and mixed letter case
work too. For the current build:

```text
LZH 1.0 (007)
  - - -
 | BetterCP/M Utilities
 | CrLZH File Compression
```

Version and build numbers come from the standard utility metadata. The build
counter advances with published executable changes; it does not reset at a new
version. An exact `/VER` token anywhere in the command shows identification and ignores
other arguments, unless `/H` or `/HELP` is also present, in which case help is shown.
Normal file
processing does not print this identification banner.

##### Output name and supported files

| Source | Output |
| --- | --- |
| `REPORT.TXT` | `REPORT.TYT` |
| `CODE.ABC` | `CODE.AYC` |
| `CODE.AYC` | `CODE.AYY` |
| `CODE.AYY` | `CODE.YYY` |
| `SHORT.A` or `SHORT.AB` | `SHORT.AY` |
| `SHORT.YY` | `SHORT.YYY` |
| `NOEXT` | `NOEXT.YYY` |

These are the historical CrLZH naming rules. Replace the middle slot with Y;
if it is already Y, replace the last slot; if the last two are YY, select YYY.
A missing extension also becomes YYY. An existing `.YYY` input is refused even
with a different destination drive. The original name, including three padded
extension slots, is stored inside for UNLZH.

```text
LZH A:REPORT.TXT B:
UNLZH B:REPORT.TYT C:
```

This keeps `A:REPORT.TXT`, creates `B:REPORT.TYT` and restores
`C:REPORT.TXT`. All file operands use your current user area; C: must not already
contain the restored name.

##### Completion and messages

Success prints `LZH: complete.` and returns to the prompt. Source files stay
in place; existing outputs are refused. Processing uses a temporary on the
destination drive. See [file handling and recovery](#archives-and-compression)
for record padding, free space, read/write/close/rename errors and interrupted
operations. A final file is published only after successful processing and closes.

| Message | Meaning/recovery |
| --- | --- |
| `LZH: cannot compress .YYY names.` | This extension is the end of the historical naming sequence. Check that you chose the intended original file. |
| `LZH: encoding failed.` | An encoding/configuration/capacity failure occurred; retain the source. |

There is no switch to write the old `10h` variant, select a CRC mode or choose a
compression level. Output need not be byte-identical to an old encoder. LZH preserves
all input-record bytes, including `1Ah`; no text conversion is performed.

##### Related documentation

- [UNLZH command](#unlzh)
- [Common operating rules](#archives-and-compression)
- In the Documentation ZIP, see `docs/engineering/LZH-UNLZH Specification.md`.

#### Examples

```text
B0:LZH /HELP
```

Show command-specific help. Substitute the locations and filenames appropriate to your session.

#### Errors/Troubleshooting

Check the operand grammar and the selected drive/user area. For disk failures, preserve the source and any reported recovery files before retrying. See the [shared system messages](#system-messages) for command lookup, media, configuration and extension diagnostics.

#### See Also

[NOAH](#noah) · [query conventions](#query-conventions)


<a id="noah"></a>

### NOAH

#### Description

Manage LBR and ARC-compatible ARK/ARC archives. Supplied on the Companion Utilities disk. Keep NOAH.COM and its matching NOAH.OVL together, select their drive/user before starting, and qualify archive/work operands separately.

#### General Form

```text
NOAH /LIST archive [member-patterns]
NOAH /TEST archive [member-patterns]
NOAH /EXTRACT archive [destination-DU:]
NOAH /ADD archive sources
NOAH /REMOVE archive member-patterns
NOAH /COMPACT archive
NOAH /HELP
NOAH /VER
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| List an archive | `NOAH /LIST D:FILES.ARK` |
| Test its contents | `NOAH /TEST D:FILES.ARK` |

#### Detailed Reference

NOAH manages CP/M LBR libraries and ARC-compatible `.ARK`/`.ARC` archives.
It is supplied on the Companion Utilities disk for each platform, retaining
the historical BetterCPM-NOAH image name. Mount it in C: alongside the primary
Utilities disk in B:.
Keep `NOAH.COM` and its matching `NOAH.OVL` together. Change to their disk/user
before starting NOAH, then qualify the archive and source operands with their
writable work disks. Overlay lookup uses that invocation DU, then A0:.

```text
C:
NOAH /LIST D:FILES.ARK
NOAH /TEST D:FILES.ARK
NOAH /EXTRACT D:FILES.ARK D:
NOAH /ADD D:FILES.ARK D:*.TXT
NOAH /ADD /SQ D:TEXTS.ARK D:*.TXT
NOAH /ADD /CR D:BINARY.ARK D:*.BIN
NOAH /REMOVE D:FILES.ARK *.BAK
NOAH /COMPACT D:FILES.ARK
```

The same operations work with LBR. ADD requires one exact archive target;
LIST, TEST, EXTRACT, REMOVE and COMPACT accept archive selectors and member
patterns. `/CAPACITY=n` sets LBR directory capacity on ADD/COMPACT. Unknown new
extensions require `/FORMAT=LBR` or `/FORMAT=ARK`; existing files are recognized
by contents and are never converted by FORMAT.

ARC ADD stores members without compression unless `/SQ` or `/CR` is explicit.
These select native ARC methods 4 and 8 and preserve the original member name.
LBR compression retains its standalone SQ/CR representation and marked filename.
Standalone `/SQ`, `/CR` and `/EXPAND` remain available; `/EXTRACT /EXPAND` decodes
one inner layer in LBR. ARC extraction decodes its archive-managed method.
Input bytes include CP/M's final physical-record padding when no exact logical
length is available; 00h, 1Ah and high-bit bytes are ordinary input data.

`/Y` approves ordinary replacement/removal and explicit COMPACT. It never
overrides read-only/system protection; `/R` and `/SYS` enable separate protected
questions. `/Q` (or `/QUIET`) suppresses routine progress, retaining choices,
warnings, errors and the operation summary. Successful commands omit redundant
internal accounting. File sizes and counts are decimal. LIST does not test
contents; TEST reports CRC results and incomplete coverage explicitly.
`/L` aliases `/LIST`, `/A` aliases `/ADD`, and `/H` aliases `/HELP`.
`/VER` displays identification; `/V` is not a version alias. Escape or Ctrl-C cancels at safe boundaries.

NOAH's ordinary replacement prompt offers `Y/N/A/C/?`, default No. Type `?`
for `Y Yes, N No, A All, C Cancel, ? Help`. Safe failure recovery offers
`R/S/A/?`, default Skip; its help is `R Retry, S Skip, A Abort all, ? Help`.
Each explanation returns to the same file/member or failed source/archive.
Repeated help changes no files or choices. Simple protection/removal/COMPACT
Yes/No confirmations and paging retain their existing controls.

Ordinary ARC updates preserve retained headers/payloads and the entire suffix
after the end marker. COMPACT trims only excess 00h/1Ah padding and refuses an
opaque suffix. It does not recompress retained members. No-match REMOVE leaves
the archive unchanged, including combined COMPACT.

Every new archive/update is staged, reopened and verified before publication.
Keep any reported TMP/BAK recovery files until the final state is understood.
Uncertain rollback stops the batch and reports the affected paths. There is no
automatic recovery/resume command or power-loss atomicity guarantee.

The frozen selection limit is 512 candidates; actual transaction capacity also
depends on active TPA and codec/source-plan requirements. Low-memory requests
fail safely. The interactive browser, ZIP and LZH/CrLZH selectors remain deferred.
Current qualification and media status are recorded in the
[engineering integration record](../engineering/NOAH%20ARC%20Write%20Integration.md).

#### Examples

```text
NOAH /LIST D:FILES.ARK
```

List an archive. Substitute the locations and filenames appropriate to your session.

#### Errors/Troubleshooting

Check the operand grammar and the selected drive/user area. For disk failures, preserve the source and any reported recovery files before retrying. See the [shared system messages](#system-messages) for command lookup, media, configuration and extension diagnostics.

#### See Also

[file specifications](#file-specifications) · [system messages](#system-messages)


<a id="sq"></a>

### SQ

#### Description

Squeeze. Supplied on the primary Utilities disk. The source remains in place; existing output is refused.

#### General Form

```text
SQ [drive:]file [destination-drive:]
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Show command-specific help | `B0:SQ /HELP` |

#### Detailed Reference

[Command and Utilities Reference](#archives-and-compression) · [USQ](#usq)

SQ writes a squeezed file while keeping the original. It reads the source
twice, first to analyze it and then to produce the compressed stream. Keep the
source unchanged until SQ finishes. Use USQ to restore it.

##### Syntax

```text
SQ [drive:]file [destination-drive:]
SQ /H
SQ /HELP
SQ /VER
```

Give one exact 8.3 source name and an optional destination drive such as `B:`.
Both use your current user area. Output defaults to the logged drive, not the
source or command's drive. Wildcards, paths, explicit user/DU file operands,
output filenames and other switches are not accepted. `/HELP` and `/VER` ignore other arguments. See the
[shared command rules](#archives-and-compression)
for program lookup, filename syntax and drive defaults.

##### Help

`SQ /HELP` displays a compact purpose/Usage corner followed by an unframed
Options list, then returns without accessing files. Examples, defaults and
restrictions are described below. Letter case and surrounding spaces or TABs
do not matter.
An exact `/H` or `/HELP` token anywhere in the command ignores other arguments and
shows help. If `/VER` is also present, help takes precedence in either order.
Longer tokens such as `/HELPER` are syntax errors. Empty or malformed commands
show short syntax and `Use SQ /HELP for help.`

The help screen is:

```text
SQ 1.0 (007)
  - - -
 | Squeeze compression
 |
 |   Usage: SQ [drive:]file [destination-drive:]

   Options:
     /H /HELP    Display this help.
     /VER        Display utility identification.
```

##### Version identification

`SQ /VER` shows the utility identity and returns to the command prompt without
opening files or starting compression/expansion. `/ver` and mixed letter case
work too. For the current build:

```text
SQ 1.0 (007)
  - - -
 | BetterCP/M Utilities
 | Squeeze File Compression
```

Version and build numbers come from the standard utility metadata. The build
counter advances with published executable changes; it does not reset at a new
version. An exact `/VER` token anywhere in the command shows identification and ignores
other arguments, unless `/H` or `/HELP` is also present, in which case help is shown.
Normal file
processing does not print this identification banner.

##### Output name and supported files

| Source | Output |
| --- | --- |
| `REPORT.TXT` | `REPORT.TQT` |
| `CODE.ABC` | `CODE.AQC` |
| `SHORT.A` or `SHORT.AB` | `SHORT.AQ` |
| `NOEXT` | `NOEXT.QQQ` |

SQ replaces the middle extension character with Q. A name already containing Q
in that slot, such as `REPORT.TQT`, is refused even if you choose another drive.
The stored original name has no drive or padding spaces.

```text
SQ A:REPORT.TXT B:
USQ B:REPORT.TQT C:
```

These commands leave `A:REPORT.TXT` and `B:REPORT.TQT` in place and restore
`C:REPORT.TXT`. C: must not already contain that name in your current user area.

##### Completion and messages

Success prints `SQ: complete.` and returns to the prompt. Source files stay
in place; existing outputs are refused. Processing uses a temporary on the
destination drive. See [file handling and recovery](#archives-and-compression)
for record padding, free space, read/write/close/rename errors and interrupted
operations. A final file is published only after successful processing and closes.

| Message | Meaning/recovery |
| --- | --- |
| `SQ: input name already squeezed.` | The middle extension character is Q. Check that you selected the original source. |
| `SQ: cannot reopen input for second pass.` | The close/reopen needed for pass two failed. Check source media and accessibility. |
| `SQ: input changed between passes.` | SQ detected different input. Keep a stable source and run again. No final compressed file is published. |
| `SQ: encoding failed.` | An encoding/configuration/capacity failure occurred; retain the source. |

SQ's pass comparison is not a guarantee against every possible source change.
It stores every CP/M record byte; it does not stop at text `1Ah`. Squeezed output
is compatible with the supported SQ format but is not promised to match an old
encoder byte for byte.

##### Related documentation

- [USQ command](#usq)
- [Common operating rules](#archives-and-compression)
- In the Documentation ZIP, see `docs/engineering/SQ-USQ Specification.md`.

#### Examples

```text
B0:SQ /HELP
```

Show command-specific help. Substitute the locations and filenames appropriate to your session.

#### Errors/Troubleshooting

Check the operand grammar and the selected drive/user area. For disk failures, preserve the source and any reported recovery files before retrying. See the [shared system messages](#system-messages) for command lookup, media, configuration and extension diagnostics.

#### See Also

[NOAH](#noah) · [query conventions](#query-conventions)


<a id="uncr"></a>

### UNCR

#### Description

Restore a supported crunched file. Supplied on the primary Utilities disk. The source remains in place; existing output is refused.

#### General Form

```text
UNCR [drive:]file [destination-drive:]
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Show command-specific help | `B0:UNCR /HELP` |

#### Detailed Reference

[Command and Utilities Reference](#archives-and-compression) · [CR](#cr)

UNCR restores supported CRUNCH significant revision `20h` files and verifies
their additive checksum. It keeps the compressed input. Both files written by
BetterCP/M CR and supported historical 2.x streams can be read, including streams
using dictionary resets and reassignment. CRUNCH 1.x is not supported.

##### Syntax

```text
UNCR [drive:]file [destination-drive:]
UNCR /H
UNCR /HELP
UNCR /VER
```

Give one exact 8.3 source name and an optional destination drive such as `B:`.
Both use your current user area. Output defaults to the logged drive, not the
source or command's drive. Wildcards, paths, explicit user/DU file operands,
output filenames and other switches are not accepted. `/HELP` and `/VER` ignore other arguments. See the
[shared command rules](#archives-and-compression)
for program lookup, filename syntax and drive defaults.

##### Help

`UNCR /HELP` displays a compact purpose/Usage corner followed by an unframed
Options list, then returns without accessing files. Examples, defaults and
restrictions are described below. Letter case and surrounding spaces or TABs
do not matter.
An exact `/H` or `/HELP` token anywhere in the command ignores other arguments and
shows help. If `/VER` is also present, help takes precedence in either order.
Longer tokens such as `/HELPER` are syntax errors. Empty or malformed commands
show short syntax and `Use UNCR /HELP for help.`

The help screen is:

```text
UNCR 1.0 (007)
  - - -
 | CRUNCH expansion
 |
 |   Usage: UNCR [drive:]file [destination-drive:]

   Options:
     /H /HELP    Display this help.
     /VER        Display utility identification.
```

##### Version identification

`UNCR /VER` shows the utility identity and returns to the command prompt without
opening files or starting compression/expansion. `/ver` and mixed letter case
work too. For the current build:

```text
UNCR 1.0 (007)
  - - -
 | BetterCP/M Utilities
 | CRUNCH File Expansion
```

Version and build numbers come from the standard utility metadata. The build
counter advances with published executable changes; it does not reset at a new
version. An exact `/VER` token anywhere in the command shows identification and ignores
other arguments, unless `/H` or `/HELP` is also present, in which case help is shown.
Normal file
processing does not print this identification banner.

##### Output name and supported files

The output uses the header's original name. For example, `REPORT.TZT` normally
restores as `REPORT.TXT`; renaming the input does not change the stored name.
The input need not have Z in its extension, but its contents must be CRUNCH.

UNCR accepts historical padding in the three extension slots and ignores later
header metadata. It validates the resulting plain 8.3 name before creating
output. Unsafe or high-bit filename characters are refused. It does not restore
metadata as timestamps, attributes, user areas or drives. There is no command
option to select a replacement output filename.

```text
UNCR B:REPORT.TZT C:
```

This keeps `B:REPORT.TZT` and restores the embedded original name on C:.
With A: logged on, omitting `C:` sends the restored file to A:, independently
of the input's B: prefix. An existing restored name is never replaced.

##### Completion and messages

Success prints `UNCR: complete.` and returns to the prompt. Source files stay
in place; existing outputs are refused. Processing uses a temporary on the
destination drive. See [file handling and recovery](#archives-and-compression)
for record padding, free space, read/write/close/rename errors and interrupted
operations. A final file is published only after successful processing and closes.

| Message | Meaning/recovery |
| --- | --- |
| `UNCR: unsupported crunch variant.` | The significant revision or checking mode is unsupported. Older CRUNCH 1.x and non-additive checking modes are refused. |
| `UNCR: header exceeds 127 bytes.` | The stored name/metadata field exceeds the supported bound. |
| `UNCR: invalid or truncated crunched file.` | Wrong signature, malformed codes/repeats or premature end. Check the format or obtain another copy. |
| `UNCR: checksum mismatch.` | Restored data failed verification; no final output is published. |

UNCR is not a squeezed-file, CrLZH or general archive reader. The `.TZT` or other
Z-style extension is only a convention; it does not prove that a file is supported.

##### Related documentation

- [CR command](#cr)
- [Common operating rules](#archives-and-compression)
- In the Documentation ZIP, see `docs/engineering/CR-UNCR Specification.md`.

#### Examples

```text
B0:UNCR /HELP
```

Show command-specific help. Substitute the locations and filenames appropriate to your session.

#### Errors/Troubleshooting

Check the operand grammar and the selected drive/user area. For disk failures, preserve the source and any reported recovery files before retrying. See the [shared system messages](#system-messages) for command lookup, media, configuration and extension diagnostics.

#### See Also

[NOAH](#noah) · [query conventions](#query-conventions)


<a id="unlzh"></a>

### UNLZH

#### Description

Restore a supported CP/M CrLZH file. Supplied on the primary Utilities disk. The source remains in place; existing output is refused.

#### General Form

```text
UNLZH [drive:]file [destination-drive:]
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Show command-specific help | `B0:UNLZH /HELP` |

#### Detailed Reference

[Command and Utilities Reference](#archives-and-compression) · [LZH](#lzh)

UNLZH restores the supported old `10h` and new `20h` CP/M CrLZH variants with
additive checksums. It detects the variant from the header; no switch is needed.
The compressed input remains in place, and output is published only after its
checksum and file closes succeed.

##### Syntax

```text
UNLZH [drive:]file [destination-drive:]
UNLZH /H
UNLZH /HELP
UNLZH /VER
```

Give one exact 8.3 source name and an optional destination drive such as `B:`.
Both use your current user area. Output defaults to the logged drive, not the
source or command's drive. Wildcards, paths, explicit user/DU file operands,
output filenames and other switches are not accepted. `/HELP` and `/VER` ignore other arguments. See the
[shared command rules](#archives-and-compression)
for program lookup, filename syntax and drive defaults.

##### Help

`UNLZH /HELP` displays a compact purpose/Usage corner followed by an unframed
Options list, then returns without accessing files. Examples, defaults and
restrictions are described below. Letter case and surrounding spaces or TABs
do not matter.
An exact `/H` or `/HELP` token anywhere in the command ignores other arguments and
shows help. If `/VER` is also present, help takes precedence in either order.
Longer tokens such as `/HELPER` are syntax errors. Empty or malformed commands
show short syntax and `Use UNLZH /HELP for help.`

The help screen is:

```text
UNLZH 1.0 (007)
  - - -
 | CrLZH expansion
 |
 |   Usage: UNLZH [drive:]file [destination-drive:]

   Options:
     /H /HELP    Display this help.
     /VER        Display utility identification.
```

##### Version identification

`UNLZH /VER` shows the utility identity and returns to the command prompt without
opening files or starting compression/expansion. `/ver` and mixed letter case
work too. For the current build:

```text
UNLZH 1.0 (007)
  - - -
 | BetterCP/M Utilities
 | CrLZH File Expansion
```

Version and build numbers come from the standard utility metadata. The build
counter advances with published executable changes; it does not reset at a new
version. An exact `/VER` token anywhere in the command shows identification and ignores
other arguments, unless `/H` or `/HELP` is also present, in which case help is shown.
Normal file
processing does not print this identification banner.

##### Output name and supported files

The restored name comes from the header. `REPORT.TYT` may restore as
`REPORT.TXT`; changing the input's extension does not change that stored name.
Input need not have Y in its extension, but must contain the supported CrLZH
format. Ordinary LHA/`.LZH` archives are a different format and are not supported.

UNLZH accepts trailing blanks in historical three-slot extensions and ignores
later header metadata. It validates the resulting plain 8.3 name, refusing paths,
drive/user prefixes, wildcards and high-bit filename characters. It does not
restore metadata as attributes or timestamps, or offer an output-name override.
Some historical files have high-bit header names and are therefore refused even
when their compressed data is valid.

```text
UNLZH B:REPORT.TYT C:
```

This keeps `B:REPORT.TYT` and restores its original name on C: in your current
user area. While logged onto A:, `UNLZH B:REPORT.TYT` instead restores on A:.
An existing original name is never replaced.

##### Completion and messages

Success prints `UNLZH: complete.` and returns to the prompt. Source files stay
in place; existing outputs are refused. Processing uses a temporary on the
destination drive. See [file handling and recovery](#archives-and-compression)
for record padding, free space, read/write/close/rename errors and interrupted
operations. A final file is published only after successful processing and closes.

| Message | Meaning/recovery |
| --- | --- |
| `UNLZH: unsupported CrLZH variant.` | Revision or checking mode is unsupported. Only `10h`/`20h` with additive checking are accepted. |
| `UNLZH: header exceeds 127 bytes.` | The stored name/metadata exceeds the supported bound. |
| `UNLZH: invalid or truncated CrLZH file.` | Wrong format, malformed encoded data or premature end. Check the format or obtain another copy. |
| `UNLZH: checksum mismatch.` | Restored content failed verification; no final output is published. |

UNLZH does not browse an archive or decode squeezed/CRUNCH files. Use USQ or
UNCR for those formats. `1Ah`, binary bytes and overlapping compressed matches
are restored without text conversion.

##### Related documentation

- [LZH command](#lzh)
- [Common operating rules](#archives-and-compression)
- In the Documentation ZIP, see `docs/engineering/LZH-UNLZH Specification.md`.

#### Examples

```text
B0:UNLZH /HELP
```

Show command-specific help. Substitute the locations and filenames appropriate to your session.

#### Errors/Troubleshooting

Check the operand grammar and the selected drive/user area. For disk failures, preserve the source and any reported recovery files before retrying. See the [shared system messages](#system-messages) for command lookup, media, configuration and extension diagnostics.

#### See Also

[NOAH](#noah) · [query conventions](#query-conventions)


<a id="usq"></a>

### USQ

#### Description

Restore a squeezed file. Supplied on the primary Utilities disk. The source remains in place; existing output is refused.

#### General Form

```text
USQ [drive:]file [destination-drive:]
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Show command-specific help | `B0:USQ /HELP` |

#### Detailed Reference

[Command and Utilities Reference](#archives-and-compression) · [SQ](#sq)

USQ restores one squeezed file and checks its stored additive checksum before
publishing the result. It leaves the compressed file in place. The restored
filename comes from the header, not from replacing Q in the input extension.

##### Syntax

```text
USQ [drive:]file [destination-drive:]
USQ /H
USQ /HELP
USQ /VER
```

Give one exact 8.3 source name and an optional destination drive such as `B:`.
Both use your current user area. Output defaults to the logged drive, not the
source or command's drive. Wildcards, paths, explicit user/DU file operands,
output filenames and other switches are not accepted. `/HELP` and `/VER` ignore other arguments. See the
[shared command rules](#archives-and-compression)
for program lookup, filename syntax and drive defaults.

##### Help

`USQ /HELP` displays a compact purpose/Usage corner followed by an unframed
Options list, then returns without accessing files. Examples, defaults and
restrictions are described below. Letter case and surrounding spaces or TABs
do not matter.
An exact `/H` or `/HELP` token anywhere in the command ignores other arguments and
shows help. If `/VER` is also present, help takes precedence in either order.
Longer tokens such as `/HELPER` are syntax errors. Empty or malformed commands
show short syntax and `Use USQ /HELP for help.`

The help screen is:

```text
USQ 1.0 (007)
  - - -
 | Squeeze expansion
 |
 |   Usage: USQ [drive:]file [destination-drive:]

   Options:
     /H /HELP    Display this help.
     /VER        Display utility identification.
```

##### Version identification

`USQ /VER` shows the utility identity and returns to the command prompt without
opening files or starting compression/expansion. `/ver` and mixed letter case
work too. For the current build:

```text
USQ 1.0 (007)
  - - -
 | BetterCP/M Utilities
 | Squeezed File Expansion
```

Version and build numbers come from the standard utility metadata. The build
counter advances with published executable changes; it does not reset at a new
version. An exact `/VER` token anywhere in the command shows identification and ignores
other arguments, unless `/H` or `/HELP` is also present, in which case help is shown.
Normal file
processing does not print this identification banner.

##### Output name and supported files

For a squeezed file containing the original name `REPORT.TXT`, output is
`REPORT.TXT` on the destination drive. The input may have any valid 8.3 name;
USQ checks the squeezed signature and decoding tree rather than its extension.

The complete embedded name must be a safe plain 8.3 filename. Drive/user
prefixes, paths, wildcards, high-bit characters, padded spaces and appended
metadata are not accepted by this command. USQ does not restore file attributes
or timestamps, and you cannot override the stored name on the command line.

```text
USQ B:REPORT.TQT C:
```

This keeps `B:REPORT.TQT` and restores `C:REPORT.TXT` if that is the stored
name. If C: already contains `REPORT.TXT`, USQ refuses to replace it. While
logged onto A:, `USQ B:REPORT.TQT` instead selects A: as the destination.

##### Completion and messages

Success prints `USQ: complete.` and returns to the prompt. Source files stay
in place; existing outputs are refused. Processing uses a temporary on the
destination drive. See [file handling and recovery](#archives-and-compression)
for record padding, free space, read/write/close/rename errors and interrupted
operations. A final file is published only after successful processing and closes.

| Message | Meaning/recovery |
| --- | --- |
| `USQ: invalid or truncated squeezed file.` | Wrong format, invalid header/tree/repeat data, an overlong stored name, or premature end. Obtain a sound copy or confirm the format. |
| `USQ: checksum mismatch.` | Decoded content failed verification; no restored filename is published. |
| `USQ: unsafe embedded filename.` | The stored name is outside this command's filename rules. Renaming the input does not change it. |

USQ reads squeezed SQ files. It does not decode CRUNCH, CP/M CrLZH or archive
containers. Embedded `1Ah` is ordinary data. Historical files with otherwise
valid compressed data can still be refused because of their stored filename.

##### Related documentation

- [SQ command](#sq)
- [Common operating rules](#archives-and-compression)
- In the Documentation ZIP, see `docs/engineering/SQ-USQ Specification.md`.

#### Examples

```text
B0:USQ /HELP
```

Show command-specific help. Substitute the locations and filenames appropriate to your session.

#### Errors/Troubleshooting

Check the operand grammar and the selected drive/user area. For disk failures, preserve the source and any reported recovery files before retrying. See the [shared system messages](#system-messages) for command lookup, media, configuration and extension diagnostics.

#### See Also

[NOAH](#noah) · [query conventions](#query-conventions)


<a id="platform-tools-and-diagnostics"></a>

## Platform tools and diagnostics


<a id="admtst"></a>

### ADMTST

#### Description

Exercise the ADM3A terminal personality. Supplied on both System disks. Load the matching screen backend, then ADM3A, with no other personality active.

#### General Form

```text
ADMTST
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Run the diagnostic | `ADMTST` |

#### Detailed Reference

Run `ADMTST` and follow its displayed screen/input exercises. Compare cursor movement, erase, wrapping, modes and replies with the promised ADM3A behavior. A successful keyboard check does not by itself establish visual or audible correctness.

On Model 4 startup already selects integrated ADM3A. Unload it before loading another personality. On cpmsim and Model II load the selected integrated personality directly. Separate SCRN/SCX clients still need their documented backend.

See the [terminal tasks](Users-Guide.md#chapter-9) and [monitor development reference](../programmers/Monitor%20RSX%20Development.md) for the test boundaries.

#### Examples

```text
ADMTST
```

Run the diagnostic. Substitute the locations and filenames appropriate to your session.

#### Errors/Troubleshooting

If the display is wrong, check backend/personality order, host terminal dimensions and application terminal selection. Unload the personality before its backend; restore the supplied environment with the unmodified SUBMIT STARTUP or cold boot.

#### See Also

[RSX](#rsx)


<a id="ansitst"></a>

### ANSITST

#### Description

Exercise the ANSI terminal personality. Supplied on both System disks. Load the matching screen backend, then ANSI, with no other personality active.

#### General Form

```text
ANSITST
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Run the diagnostic | `ANSITST` |

#### Detailed Reference

Run `ANSITST` and follow its displayed screen/input exercises. Compare cursor movement, erase, wrapping, modes and replies with the promised ANSI behavior. A successful keyboard check does not by itself establish visual or audible correctness.

On Model 4 startup already selects integrated ADM3A. Unload it before loading another personality. On cpmsim and Model II load the selected integrated personality directly. Separate SCRN/SCX clients still need their documented backend.

See the [terminal tasks](Users-Guide.md#chapter-9) and [monitor development reference](../programmers/Monitor%20RSX%20Development.md) for the test boundaries.

#### Examples

```text
ANSITST
```

Run the diagnostic. Substitute the locations and filenames appropriate to your session.

#### Errors/Troubleshooting

If the display is wrong, check backend/personality order, host terminal dimensions and application terminal selection. Unload the personality before its backend; restore the supplied environment with the unmodified SUBMIT STARTUP or cold boot.

#### See Also

[RSX](#rsx)


<a id="mount"></a>

### MOUNT

#### Description

MOUNT.COM is supplied only on the cpmsim System disk and requires the pinned patched runtime.

#### General Form

```text
MOUNT drive: host-image
MOUNT /UNMOUNT selector:
MOUNT /LIST [selector:]
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| List attached images | `MOUNT /LIST` |
| Attach a work image | `MOUNT B: WORK.DSK` |

#### Detailed Reference

`MOUNT.COM` is supplied on the cpmsim System disk in user 0. It requires
an emulator built with the guest MOUNT interface; it is not a Model 4 tool.

```text
MOUNT B: IMAGE.DSK
MOUNT B: "/path/with spaces/Disk Image.dsk"
MOUNT /U B:
MOUNT /UNMOUNT [B,C,D]:
MOUNT /L
MOUNT /LIST [A,C,D]:
MOUNT /VER
MOUNT /HELP
MOUNT /H
```

Bare `MOUNT` lists all supported drives, as does `/L` without a selector.
Unmounting always requires an explicit drive or list. Options can precede
or follow the selector. Mounting accepts one drive and one image only.
Host path case is preserved; relative paths resolve from the emulator's
working directory. The image must be a readable, nonempty regular raw file.
MOUNT does not convert formats or infer filesystem compatibility: the BIOS
selects the raw layout when accessing the disk. The legacy host geometry table
is not used as a size limit for FDF media. Listings show the full path, raw
format, and host read/write availability.

A replacement is checked before the current attachment changes. An image
already attached to another drive is rejected, including hard-link and
symlink aliases. Attachments last for this emulator session and do not change
the launcher's disk links. Restarting the emulator restores its launch media.
The command resets the affected BDOS drive state through existing function 37.

Changing or ejecting A: prompts:

```text
** WARNING: Changing A: while the system is running may cause
disk errors or loss of unsaved data. Continue? [y/N]
```

Only Y/y proceeds. Any other response cancels the entire command, including
all drives in a multi-drive unmount, with:

```text
Operation cancelled. No changes made.
```

There is no open-file tracking or additional safety interlock. You are
responsible for completing writes and choosing suitable media. Replacing A:
does not boot a new OS; Ctrl-C is a warm boot, not a machine reset. Normal
command return may also invoke a warm boot. System disk dependencies can
therefore cause errors immediately after changing A:. Use an emulator reset
and its boot sequence when you intend to boot the replacement disk.

#### Examples

```text
MOUNT /LIST
```

List attached images. Substitute the locations and filenames appropriate to your session.

#### Errors/Troubleshooting

Finish file operations before changing attachments or transferring files. Host path/name case matters. R/W do not accept host paths or wildcards. MOUNT neither converts images nor boots a replacement OS; changing A: may immediately break warm-boot/overlay reads.

#### See Also

[system messages](#system-messages)


<a id="r"></a>

### R

#### Description

R.COM is supplied only on the cpmsim System disk and requires the pinned patched runtime.

#### General Form

```text
R host-file [CP/M-filespec]
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Import a host file | `R "My assembly source.asm" D0:SOURCE.ASM` |

#### Detailed Reference

The cpmsim System disk also includes R.COM and W.COM in user 0.
`R` reads a host file into CP/M; `W` writes a CP/M file to the host.
Both report version `1.0 (006)` and support `/VER`, `/H`, and `/HELP`.

```text
R "My assembly source.asm" B3:SOURCE.ASM
W B3:SOURCE.ASM "My updated assembly source.asm"
```

Host filenames preserve case and refer to files in the emulator working
directory; R/W do not accept host paths or wildcards. Quote names containing
spaces. A long host source name requires an explicit CP/M 8.3 destination.
MOUNT, R and W are omitted from Model 4 media.

P2DOS.RSX is supplied in A0 for optional compatibility with Functions 200/201.
Load the platform’s native clock provider before `RSX LOAD P2DOS`; startup
loads neither. T104C3/T104Z8 are deferred and are not supplied in the 1.0 RC.

#### Examples

```text
R "My assembly source.asm" D0:SOURCE.ASM
```

Import a host file. Substitute the locations and filenames appropriate to your session.

#### Errors/Troubleshooting

Finish file operations before changing attachments or transferring files. Host path/name case matters. R/W do not accept host paths or wildcards. MOUNT neither converts images nor boots a replacement OS; changing A: may immediately break warm-boot/overlay reads.

#### See Also

[system messages](#system-messages)


<a id="vt52tst"></a>

### VT52TST

#### Description

Exercise the VT52 terminal personality. Supplied on both System disks. Load the matching screen backend, then VT52, with no other personality active.

#### General Form

```text
VT52TST
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Run the diagnostic | `VT52TST` |

#### Detailed Reference

Run `VT52TST` and follow its displayed screen/input exercises. Compare cursor movement, erase, wrapping, modes and replies with the promised VT52 behavior. A successful keyboard check does not by itself establish visual or audible correctness.

On Model 4 startup already selects integrated ADM3A. Unload it before loading another personality. On cpmsim and Model II load the selected integrated personality directly. Separate SCRN/SCX clients still need their documented backend.

See the [terminal tasks](Users-Guide.md#chapter-9) and [monitor development reference](../programmers/Monitor%20RSX%20Development.md) for the test boundaries.

#### Examples

```text
VT52TST
```

Run the diagnostic. Substitute the locations and filenames appropriate to your session.

#### Errors/Troubleshooting

If the display is wrong, check backend/personality order, host terminal dimensions and application terminal selection. Unload the personality before its backend; restore the supplied environment with the unmodified SUBMIT STARTUP or cold boot.

#### See Also

[RSX](#rsx)


<a id="w"></a>

### W

#### Description

W.COM is supplied only on the cpmsim System disk and requires the pinned patched runtime.

#### General Form

```text
W CP/M-filespec [host-file]
```

#### Quick Reference

| Task | Invocation |
| --- | --- |
| Export a CP/M file | `W D0:SOURCE.ASM "My updated assembly source.asm"` |

#### Detailed Reference

The cpmsim System disk also includes R.COM and W.COM in user 0.
`R` reads a host file into CP/M; `W` writes a CP/M file to the host.
Both report version `1.0 (006)` and support `/VER`, `/H`, and `/HELP`.

```text
R "My assembly source.asm" B3:SOURCE.ASM
W B3:SOURCE.ASM "My updated assembly source.asm"
```

Host filenames preserve case and refer to files in the emulator working
directory; R/W do not accept host paths or wildcards. Quote names containing
spaces. A long host source name requires an explicit CP/M 8.3 destination.
MOUNT, R and W are omitted from Model 4 media.

P2DOS.RSX is supplied in A0 for optional compatibility with Functions 200/201.
Load the platform’s native clock provider before `RSX LOAD P2DOS`; startup
loads neither. T104C3/T104Z8 are deferred and are not supplied in the 1.0 RC.

#### Examples

```text
W D0:SOURCE.ASM "My updated assembly source.asm"
```

Export a CP/M file. Substitute the locations and filenames appropriate to your session.

#### Errors/Troubleshooting

Finish file operations before changing attachments or transferring files. Host path/name case matters. R/W do not accept host paths or wildcards. MOUNT neither converts images nor boots a replacement OS; changing A: may immediately break warm-boot/overlay reads.

#### See Also

[system messages](#system-messages)


<a id="file-specifications"></a>

## File specifications and attributes

Simple DU locations identify drive and/or user; selectors can identify sets of DUs. The syntax parser's A–P range does not mean the release has sixteen configured drives: the locked BIOS supplies A–D. User areas are 0–31 where supported. File attributes and selector sets are separate features, and each command's grammar controls.

| Command family | Location/selection contract |
| --- | --- |
| DIR, ERA, REN, TYPE, COPY and resident MOVE | Shared selector and attribute forms where detailed in the entry. COPY/MOVE destinations identify a single DU; mapping and protection rules still apply. |
| SEARCH, checksums and STAT | Extended selection only in the forms described by that command; options and destination lists differ. |
| DUMP, TED and ED | Exact single-file operands; no general multi-DU selection. Their accepted DU ranges and forms are command-specific. |
| PIP | Destination-first assignment; simple DU and expanded source selectors for copying into one destination DU. Historical trailing bracket parameters, not the shared `$RO` predicate language; see PIP for preflight and duplicate-name rules. |
| SQ/USQ, CR/UNCR, LZH/UNLZH | Exact filename, optional drive-only source, drive-only destination, caller's current user. `B0:SQ` qualifies the program, not its operand grammar. |
| CPX/RSX LOAD and UNLOAD | Unqualified carrier stems, with their own optional extension rules. Carrier lookup uses A0, not ordinary transient search. |
| FDB | Locked workbench filename behavior and current user; applying B–D does not format or save startup defaults. |
| DDT, LINK and ZSM4 | Retained tool-specific historical syntax; do not assume the shared selectors or utility query conventions. |

The following detailed notation was formerly User's Guide Appendix D. Command-specific restrictions take precedence over this catalogue of available forms.


BetterCP/M retains the familiar CP/M 2.2 file-naming conventions while extending the ways in which files can be selected and managed.

In conventional CP/M, a file is identified by its name, file type, drive, and user area. BetterCP/M preserves these conventions and adds facilities for selecting files across multiple user areas, combining drive/user specifications, and filtering files according to their attributes.

These extensions are particularly useful when working with large collections of files, performing backups, or managing files distributed across several user areas.

This appendix describes BetterCP/M's file specifications, wildcard conventions, drive/user selectors, and file attributes. It also explains how these facilities are used by commands such as DIR, ERA, REN, COPY, MOVE, TYPE, and STAT.

For an introduction to working with files, see [Chapter 4](Users-Guide.md#chapter-4), *Working with Drives and Files*. For the exact syntax accepted by individual utilities, consult the command entries in this reference.

##### D.1 File Names and File Types

BetterCP/M uses the standard CP/M 8.3 filename convention.

A filename consists of a name containing up to eight characters and an optional file type containing up to three characters.

The name and type are separated by a period.

For example:

```text
REPORT.TXT
PROGRAM.COM
SOURCE.ASM
BACKUP.BAK
```

The portion before the period is the filename. The portion after the period is the file type, sometimes called the extension.

A file type is optional.

For example:

```text
README
```

is a valid filename without a file type.

##### Letter Case

BetterCP/M treats filenames without regard to letter case.

For example:

```text
REPORT.TXT
report.txt
Report.Txt
```

all identify the same CP/M filename.

For consistency, this manual generally displays filenames in uppercase.

##### File Types

CP/M does not require every file type to have a particular meaning, but several conventions are widely used.

| File type | Common purpose |
|---|---|
| `.COM` | Executable transient program |
| `.ASM` | Assembly-language source |
| `.HEX` | Intel hexadecimal object file |
| `.SUB` | SUBMIT command file |
| `.TXT` | Text file |
| `.DOC` | Documentation |
| `.BAK` | Backup copy |
| `.SYS` | System-related file |
| `.RSX` | BetterCP/M Resident System Extension |
| `.CPX` | BetterCP/M Command Processor Extension |

These conventions help identify a file's intended purpose, but the file type alone does not guarantee that its contents have the expected format.

For example, renaming a text file to `.COM` does not make it an executable program.

##### Filename Restrictions

File specifications must conform to CP/M's filename rules.

Names longer than eight characters or file types longer than three characters are invalid.

BetterCP/M's file-selection facilities also distinguish between literal filenames and wildcard patterns.

Characters used as wildcard operators cannot be treated as ordinary filename characters in a file-selection expression.

When a command rejects a filename, check its length, punctuation, and any wildcard characters.

##### D.2 Drive and User-Area Specifications

CP/M organizes files by drive and user area.

A drive is identified by a letter, such as `A:` or `B:`.

A user area is identified by a number.

BetterCP/M supports user areas 0 through 31.

##### Drive Specifications

To identify a file on drive B:

```text
B:REPORT.TXT
```

If the user area is omitted, the current user area is used.

For example, if the current user area is 3, the specification:

```text
B:REPORT.TXT
```

refers to `REPORT.TXT` on drive B, user area 3.

##### User-Area Specifications

BetterCP/M allows a user area to be specified directly with the drive.

For example:

```text
B3:REPORT.TXT
```

identifies `REPORT.TXT` on drive B, user area 3.

A user-area specification can also be used without a drive letter:

```text
3:REPORT.TXT
```

This refers to user area 3 on the current drive.

##### Drive/User Abbreviations

BetterCP/M uses the term **drive/user**, abbreviated **DU**, for a particular drive and user-area combination.

For example:

| Specification | Meaning |
|---|---|
| `A0:` | Drive A, user area 0 |
| `A3:` | Drive A, user area 3 |
| `B0:` | Drive B, user area 0 |
| `B17:` | Drive B, user area 17 |
| `3:` | User area 3 on the current drive |
| `B:` | Drive B, current user area |

When no drive or user area is specified, the current drive/user is used.

##### Changing the Current Drive/User

You can change the current drive and user area directly at the command prompt.

For example:

```text
A0>B:
B0>
```

selects drive B.

To select user area 3:

```text
B0>3:
B3>
```

To select both at once:

```text
B3>C5:
C5>
```

These commands change the current working location.

By contrast, supplying a drive/user qualification to a file-management command normally selects files in that location without changing the current drive/user.

For example:

```text
A0>DIR B3:*.COM
```

lists matching files in B3 and then returns to the original prompt.

##### D.3 Wildcard File Specifications

Wildcards allow a command to select several files using a single specification.

BetterCP/M supports the familiar CP/M wildcard characters:

| Character | Meaning |
|---|---|
| `?` | Match one filename position |
| `*` | Match the remainder of a filename or file-type field |

The name and file-type fields are matched separately.

##### Question-Mark Wildcards

A question mark matches one position in the filename or file type.

For example:

```text
TEST?.COM
```

can match names such as:

```text
TEST1.COM
TEST2.COM
TESTA.COM
```

A pattern containing several question marks can match several corresponding positions.

For example:

```text
FILE??.TXT
```

selects filenames matching the indicated positions.

##### Asterisk Wildcards

An asterisk matches the remaining positions in its field.

For example:

```text
*.COM
```

selects files with the `.COM` type.

Similarly:

```text
REPORT.*
```

selects files named `REPORT` with different file types.

The familiar specification:

```text
*.*
```

selects all filenames and file types, subject to any attribute restrictions imposed by the command.

##### BetterCP/M's Bounded Wildcard Rules

BetterCP/M uses a consistent set of bounded 8.3 wildcard rules in its extended file-selection facilities.

An asterisk must occupy the remainder of the filename or file-type field.

For example, these patterns are valid:

```text
F?*.DAT
F***.DAT
```

Repeated terminal asterisks are treated as equivalent to one asterisk.

However, characters cannot follow an asterisk within the same field.

Consequently, these patterns are invalid:

```text
F*A.DAT
F**?.DAT
```

BetterCP/M reports:

```text
Invalid filespec.
```

This restriction avoids ambiguous wildcard interpretation and provides consistent behavior among the utilities using the shared file-selection facilities.

##### Wildcards and Protected Files

Wildcards select filenames; they do not automatically override file protection.

For example:

```text
ERA *.BAK
```

does not imply permission to erase read-only or system files.

The treatment of protected files depends on the command and any explicit attribute-selection or protection options.

For details, consult the ERA, REN, COPY, and MOVE references in [File commands](#files-directories-and-transfers).

##### D.4 Extended Drive/User Selectors

PIP accepts these selectors for one file-source operand copied into a single destination DU. Its trailing bracket parameters remain PIP-specific. See [PIP — Expanded source DU selectors](#expanded-source-du-selectors) for the 64-file preflight limit and duplicate destination filename policy.

BetterCP/M extends conventional CP/M file specifications by allowing commands to select files from several drive/user areas in a single operation.

These extended specifications are called **drive/user selectors**, or **DU selectors**.

They are supported by the enhanced file-management utilities, although not every command accepts every form.

##### Selecting One User Area

A conventional BetterCP/M file specification identifies one drive/user area:

```text
B3:*.COM
```

This selects matching `.COM` files in drive B, user area 3.

##### Selecting Several User Areas

A bracketed list selects several user areas on the same drive.

For example:

```text
B[1,3,5]:*.COM
```

selects `.COM` files in user areas 1, 3, and 5 on drive B.

A range can be specified with a hyphen:

```text
B[3-7]:*.ASM
```

This selects user areas 3 through 7.

Lists and ranges can be combined:

```text
B[1,3,8-10]:*.DOC
```

This selects user areas 1, 3, 8, 9, and 10.

##### Selecting All User Areas

The special selector `[-]` selects all supported user areas on a drive.

For example:

```text
B[-]:*.COM
```

selects `.COM` files from user areas 0 through 31 on drive B.

The notation:

```text
B[*]:*.COM
```

is not an alternative spelling and is invalid.

Use `[-]` when you want all user areas.

##### Descending and Open-Ended Ranges

BetterCP/M's extended selector language also supports descending and open-ended ranges.

For example:

```text
B[5-3]:*.DAT
```

selects user areas 3, 4, and 5.

The direction of the range does not change the order in which files are processed.

Open-ended ranges allow one endpoint to be omitted, using the beginning or end of the supported user-area range.

These facilities are useful when selecting groups of user areas without listing every number individually.

##### Selecting Several Drives

Compound selectors allow locations on different drives to be combined.

For example:

```text
[A0,B3]:../user/%2A.DOC
```

selects `.DOC` files from A0 and B3.

More elaborate selections are also possible:

```text
[A0,B[3-5],C[4,5,9]]:*.COM
```

This selects matching files from A0, B3 through B5, and C4, C5, and C9.

##### Inherited Drive and User Areas

A compound selector can contain terms that omit either the drive or the user area.

An omitted drive inherits the drive that was current when the command began.

An omitted user area inherits the original current user area.

For example:

```text
[A0,B[3-5],5]:*.COM
```

The final `5` refers to user area 5 on the original current drive.

This behavior allows convenient selections without repeatedly specifying the same drive.

##### Duplicate Locations

If a compound selector names the same drive/user area more than once, BetterCP/M processes that location only once.

For example:

```text
[B3,B[3-5]]:*.COM
```

does not cause B3 to be processed twice.

Selected locations are normally processed in drive-major, user-minor order.

##### Unsupported Drives

The available logical drives depend on the computer and its configuration.

BetterCP/M's current supported drive bindings ordinarily use drives A through D.

An extended selector does not make an unavailable drive accessible.

Different utilities may handle an unavailable selected drive differently. For example, one may reject the entire operation, while another may report the unavailable location and continue examining the remaining locations.

Consult the command reference for the applicable behavior.

##### D.5 File Attributes

CP/M stores several file attributes in directory entries.

These attributes affect how files are displayed, protected, or selected by utilities.

BetterCP/M retains the traditional attributes and provides extended facilities for selecting files according to their attribute settings.

The principal attributes are:

| Attribute | Meaning |
|---|---|
| RO | Read-only |
| RW | Writable |
| SYS | System |
| DIR | Directory-visible, meaning SYS is clear |
| ARC | Archive |

RO and RW describe opposite states of the read-only attribute.

Similarly, SYS and DIR describe opposite states of the system attribute.

ARC is an independent attribute.

##### Read-Only Files

A file marked read-only is protected against ordinary modification or deletion.

This can help prevent accidental changes to important programs or data.

For example, a utility may refuse to erase a read-only file unless the user explicitly authorizes the operation.

BetterCP/M's enhanced ERA utility provides additional safeguards for read-only files.

##### System Files

The SYS attribute identifies a file as a system file.

In conventional CP/M, system files are normally omitted from ordinary directory listings.

BetterCP/M retains this convention.

For example:

```text
A0>DIR
```

normally omits SYS files.

An explicit attribute expression can select them:

```text
A0>DIR *.*[$SYS]
```

This displays matching system files.

The SYS attribute does not necessarily mean that a file is part of the operating system itself. It is a directory attribute that may also be used by applications or utilities.

##### Archive Attribute

The ARC attribute is commonly associated with backup operations.

BetterCP/M's COPY utility can use ARC to select files and manage their backup status.

For example:

```text
A0>:COPY /V /BACKUP B[-]:*.DOC[$ARC] D0:
```

This selects archive-marked `.DOC` files, copies and verifies them, and clears ARC on the source and destination after successful completion.

However, ARC should not automatically be interpreted as a reliable record of every file changed since the previous backup.

That depends on whether the software modifying files maintains the attribute appropriately.

##### Displaying Attributes

The transient DIR utility provides `/A` to display file attributes.

For example:

```text
A0>:DIR /A
```

The attributes appear as a three-character field in SYS, RO, ARC order.

| Display | Meaning |
|---|---|
| `---` | No attributes set |
| `S--` | System |
| `-R-` | Read-only |
| `--A` | Archive |
| `SR-` | System and read-only |
| `S-A` | System and archive |
| `-RA` | Read-only and archive |
| `SRA` | All three attributes set |

A hyphen indicates that the corresponding attribute is clear.

The `/A` option displays attributes; it does not change them or select files according to their values.

For attribute-based selection, use an attribute expression.

##### D.6 Attribute Expressions

BetterCP/M allows several file-management commands to select files according to their attributes.

An attribute expression is enclosed in square brackets immediately following the file specification.

For example:

```text
*.COM[$ARC]
```

selects `.COM` files whose ARC attribute is set.

##### Attribute Names

The supported attribute predicates are:

| Predicate | Selects |
|---|---|
| `$RO` | Read-only files |
| `$RW` | Writable files |
| `$SYS` | System files |
| `$DIR` | Files without SYS set |
| `$ARC` | Files with ARC set |

The aliases `$R/O` and `$R/W` are also accepted for `$RO` and `$RW`.

##### Logical Operators

Attribute expressions support three logical operators:

| Operator | Meaning |
|---|---|
| `!` | NOT |
| `+` | AND |
| `,` | OR |

For example:

```text
*.COM[$ARC+!$SYS]
```

selects `.COM` files that have ARC set and SYS clear.

Another example:

```text
*.DOC[$RO,$SYS]
```

selects `.DOC` files that are read-only or marked as system files.

To select files without ARC:

```text
*.*[!$ARC]
```

##### Operator Precedence

When several operators appear in an expression, BetterCP/M evaluates them in the following order:

1. NOT (`!`)
2. AND (`+`)
3. OR (`,`)

For example:

```text
[$RO,$SYS+$ARC]
```

selects files that are read-only, or files that have both SYS and ARC set.

It does not require read-only files to have ARC set.

Parentheses are not supported in attribute expressions.

##### Attribute Selection Does Not Change Attributes

An attribute expression normally selects files; it does not modify their attributes.

For example:

```text
A0>DIR *.COM[$ARC]
```

displays matching archive-marked files without changing them.

Similarly:

```text
A0>COPY *.COM[$ARC] B:
```

selects archive-marked files for copying but does not clear ARC on the source merely because the files were selected.

Attribute modification requires a command or option that explicitly performs it.

##### Attribute Selection and File Protection

Selecting a protected file does not necessarily authorize modifying or deleting it.

For example:

```text
A0>ERA *.DOC[$RO]
```

explicitly selects read-only files, but transient ERA may still require additional authorization before erasing them.

The `/R` option permits erasure of selected read-only files:

```text
A0>:ERA /R *.DOC[$RO]
```

Likewise, transient REN requires `/P` when renaming protected files.

The exact protection rules depend on the command.

For ERA, selection, protection admission and read-only authorization are separate. All protected attributes present must be admitted by the same matching OR branch: `[$SYS+$RO]` admits a SYS+RO file, while `[$SYS,$RO]` does not. `/R` only authorizes admitted RO files; it neither broadens the selection nor admits SYS. `/Y` without `/R` skips RO files unattended.

Consult [ERA RESIDENT](#era-resident) for the complete ERA rules.

##### D.7 Destination Attribute Specifications

Some BetterCP/M utilities allow attributes to be assigned to destination files.

This is different from selecting source files by attribute.

Transient COPY.COM provides destination attribute specifications.

For example:

```text
A0>:COPY A0:*.COM D0:[$RW,!$ARC]
```

This requests destination copies that are writable and have ARC clear.

The source files are selected normally, while the destination expression specifies the attributes to apply after copying.

##### Source and Destination Expressions

Consider:

```text
A0>:COPY B2:*.DOC[$ARC] C0:[!$ARC] /V
```

The source expression:

```text
[$ARC]
```

selects files whose archive attribute is set.

The destination expression:

```text
[!$ARC]
```

requests that ARC be cleared on the completed copies.

The source files retain their original attributes unless another option explicitly changes them.

##### Destination Attribute Rules

Destination attribute specifications use comma-separated assignments.

They are not general Boolean selection expressions.

For example:

```text
[$RW,!$ARC]
```

is valid as a destination attribute specification.

Conflicting assignments, such as requesting both RO and RW, are invalid.

Attributes not explicitly changed are preserved.

Destination attribute settings do not override protection on an existing read-only destination file.

##### The /BACKUP Option

COPY's `/BACKUP` option provides additional handling of the archive attribute.

For example:

```text
A0>:COPY /V /BACKUP B[-]:*.DOC[$ARC] D0:
```

After a successful copy and any requested verification, COPY clears ARC on both source and destination.

Skipped, failed, or interrupted copies retain their source ARC status.

The `/BACKUP` option takes precedence over a destination request to set ARC.

For more information, see [COPY RESIDENT](#copy-resident), *COPY*.

##### D.8 Compatibility and Command-Specific Restrictions

BetterCP/M's extended file-selection facilities are intended to provide consistent behavior across commands, but not every command supports every feature.

For example, DIR, ERA, REN, COPY, MOVE, and TYPE support extended source selection.

STAT supports compound drive/user selectors for file inspection, but not for every attribute-modification or drive-wide operation.

Some utilities also impose restrictions on the number of selected files or the destinations they accept.

##### Source and Destination Restrictions

Commands that operate on several source files may require a single destination drive/user area.

For example:

```text
A0>COPY B[-]:*.DOC C3:
```

is valid because the destination identifies one location.

A destination selector resolving to several user areas is not accepted by COPY.

Similarly, REN changes filenames within their existing drive/user areas. It does not use destination drive/user specifications to relocate files.

##### Resident and Transient Differences

Some commands provide additional capabilities in their transient versions.

For example, transient COPY supports wildcard destination templates and destination attribute assignments.

Resident COPY provides a smaller set of operations.

When a command has both resident and transient forms, consult its reference entry to determine which features are available in each.

Use the colon or period prefix to request the transient version explicitly.

##### File-Selection Errors

BetterCP/M checks file specifications before carrying out operations.

Invalid filenames, malformed wildcard patterns, and unsupported selectors produce errors.

Commands that modify files generally validate the requested selection before beginning, helping prevent partial operations caused by malformed input.

However, validation does not guarantee that every subsequent file operation will succeed.

Disk errors, insufficient space, file protection, and destination conflicts may still interrupt an operation after some files have been processed.

For this reason, use particular care with wildcard operations that modify or delete many files.

##### Further Reference

For detailed command behavior, consult:

- [File commands](#files-directories-and-transfers) — File and Directory Commands
- [Disk/configuration commands](#configuration-disks-and-installation) — System Utilities
- [Appendix E](Users-Guide.md#appendix-e) — BetterCP/M and CP/M 2.2 Compatibility Notes

<a id="system-messages"></a>

## Shared system messages

BetterCP/M reports errors and other operating conditions through messages displayed at the console.

Some messages originate in the command processor, while others are produced by individual utilities or resident extensions. A message may indicate a simple mistake, such as an incorrectly entered command, or a more serious problem involving disk access, system configuration, or program execution.

This appendix provides a reference to the principal messages encountered when using BetterCP/M 1.0. It explains their meanings, identifies likely causes, and suggests appropriate corrective actions.

The messages are grouped by subject rather than alphabetically. Related messages often have similar causes, and grouping them makes it easier to identify the underlying problem.

**Messages shown in quotation marks or code blocks are intended to reproduce documented BetterCP/M wording.** Where a utility may produce several related messages, the description explains the condition without implying that every variation has identical wording.

For general troubleshooting procedures, see [Chapter 12](Users-Guide.md#chapter-12), *Troubleshooting*. For command-specific restrictions and recovery options, consult the command entries in this reference.

##### F.1 Command Processor Messages

##### `?`

**Meaning:** BetterCP/M could not locate or recognize the requested command.

For example:

```text
A0>MYPROG
?
```

The command processor first checks its resident commands and installed CPXs. If no command handles the name, it searches for a corresponding transient `.COM` program.

For an unqualified command, BetterCP/M searches the current drive/user area and then `A0:`.

If no executable program is found, the command fails.

**What to do:** Check the spelling of the command and verify that the corresponding `.COM` file exists.

For example:

```text
A0>DIR *.COM
A0>DIR A0:*.COM
```

If the program is in another location, specify its drive and user area explicitly.

A qualified command such as `B3:MYPROG` searches only the specified location; it does not fall back to `A0:`.

##### `CPX?`

**Meaning:** An optional Command Processor Extension could not be loaded or failed validation.

BetterCP/M continues to the command prompt with the remaining usable extensions.

Commands supplied by the rejected CPX are unavailable.

The extension may remain in the configured CPX list even though it did not load successfully.

**What to do:** Examine the configured extensions:

```text
A0>CPX LIST
```

If the affected extension is optional, remove its configured entry:

```text
A0>CPX UNLOAD BAD
```

Replace `BAD` with the affected extension's name.

Alternatively, replace the damaged extension file with a valid copy.

The warning may recur when the command environment is restored until the problem is corrected.

##### `DIR: Use :DIR.`

**Meaning:** The requested DIR operation requires the transient `DIR.COM` utility.

For example:

```text
A0>DIR /WHEREIS ED.COM
DIR: Use :DIR.
```

The resident DIR command recognizes that the requested option belongs to the transient version.

It does not automatically execute that version.

**What to do:** Repeat the command with a colon or period prefix:

```text
A0>:DIR /WHEREIS ED.COM
```

The same convention applies to other resident commands with transient-only options.

##### `VER: Use :VER.`

**Meaning:** The requested VER operation is available through the transient utility rather than the resident command.

For example:

```text
A0>VER /BANNER
VER: Use :VER.
```

**What to do:** Invoke the transient version:

```text
A0>:VER /BANNER
```

##### Invalid Command Syntax

A command may report an error when its arguments are missing, malformed, or supplied in an unsupported order.

The exact message depends on the command.

**What to do:** Check the relevant command entry in this reference.

Pay particular attention to required operands, option placement, filename qualifications, and whether the command has resident and transient versions.

##### F.2 File and Directory Messages

##### `Invalid filespec.`

**Meaning:** A file specification contains invalid syntax.

Possible causes include an invalid filename, a malformed wildcard pattern, or an unsupported drive/user selector.

For example:

```text
F*A.DAT
```

is invalid under BetterCP/M's bounded wildcard rules because characters follow the asterisk within the filename field.

**What to do:** Correct the specification.

A terminal asterisk must occupy the remainder of its filename or file-type field.

For example:

```text
F*.DAT
```

is valid.

##### `NO FILE`

**Meaning:** No files matched the requested selection.

This may occur when the named file does not exist or when a wildcard or attribute expression matches no files.

**What to do:** Check the current drive and user area, the filename, and any attribute restrictions.

For example:

```text
A0>DIR B3:*.COM
```

can help determine whether matching files exist in the expected location.

##### `File Not Found`

**Meaning:** A requested file or matching selection could not be found.

STAT may report this condition when examining an empty selected location.

**What to do:** Verify the drive/user specification and filename.

Remember that files in different user areas are distinct, even when they have identical names.

##### `FILE EXISTS`

**Meaning:** A destination file already exists and the requested operation does not authorize replacing it.

For example, COPY with `/B` but without `/O` or `/S` reports this condition for an existing writable destination.

**What to do:** Determine whether the destination should be preserved, skipped, renamed, or replaced.

For COPY, the appropriate options include:

```text
/B /O
/B /S
```

The first permits replacement of existing writable files. The second skips them.

Read-only destination files remain protected.

##### `COPY MADE; SOURCE NOT ERASED`

**Meaning:** MOVE successfully created the destination file but could not remove the original.

Both files may now exist.

**What to do:** Examine the source and destination before taking further action.

If the destination is complete and correct, you may delete the source manually.

Do not assume that the original was removed.

##### `Invalid /VER usage.`

**Legacy message:** An older build rejected `/VER` combined with other arguments. Current BetterCP/M-owned utilities ignore those other arguments.

The common `/VER` contract ignores other arguments. If a utility provides `/HELP` too, an exact `/HELP` token takes precedence. Older binaries may still emit this historical diagnostic; use the current build.

**What to do:** Use the current utility build. Extra arguments with `/VER` are accepted.

For example:

```text
A0>COPY /VER
```

If the utility has a resident and transient version, use the appropriate invocation form.

##### F.3 Disk and Filesystem Messages

Disk-related errors may originate in BDOS, the BIOS, or a utility performing disk operations.

The exact wording depends on the operation and the platform.

##### Disk Read Error

**Meaning:** The system could not reliably read the requested disk data.

Possible causes include damaged media, an incorrect disk-format assignment, a drive problem, or an unavailable disk.

**What to do:** Check that the correct disk is inserted and that its assigned format matches its actual organization.

Use CONFIG to inspect the current drive settings:

```text
A0>CONFIG /SHOW
```

If the disk remains readable, preserve important files before attempting further modifications.

##### Disk Write Error

**Meaning:** A requested disk write failed.

Possible causes include write protection, a full disk, damaged media, or a hardware problem.

**What to do:** Check the disk's write-protection setting and available space.

If the error occurs during a destructive disk operation, do not assume that the destination remains complete or usable.

##### Disk Full

**Meaning:** The disk cannot accommodate the requested file data or directory entries.

CP/M disks have limits on both data allocation and directory capacity.

A disk may run out of directory entries even when some data blocks remain free.

**What to do:** Remove unnecessary files, copy files to another disk, or use a suitable disk with greater capacity.

##### Read-Only Disk

**Meaning:** The operating system is refusing writes to the selected disk.

This may result from an explicit read-only condition or from disk-change protection.

**What to do:** Determine why the disk is read-only before attempting further writes.

If removable media were changed, use the appropriate disk-reset or warm-boot procedure.

Do not force writes to a disk whose directory state may be inconsistent with the operating system's cached information.

##### Unavailable Drive

**Meaning:** The requested logical drive is not configured or cannot be accessed.

**What to do:** Examine the drive assignments with CONFIG.

A logical drive may have been unbound, assigned to an unavailable physical drive, or configured with an unsuitable format.

##### F.4 DUP Messages

These diagnostics are maintained with [DUP](#dup).

##### F.5 SYSGEN Messages

These diagnostics are maintained with [SYSGEN](#sysgen).

##### F.6 Configuration Messages

These diagnostics are maintained with [CONFIG](#config).

##### F.7 Resident Extension Messages

These diagnostics are maintained with [CPX](#cpx), [RSX](#rsx).

##### F.8 Date and Time Messages

These diagnostics are maintained with [TIME](#time).

##### F.9 Common Interactive Prompts

Some BetterCP/M utilities provide interactive prompts when an operation requires a decision.

The available responses depend on the utility and the operation.

##### Yes/No Confirmation

Many potentially destructive operations require explicit confirmation.

For example, SYSGEN asks:

```text
Proceed (Y/N)?
```

Only `Y` authorizes the operation.

Other responses cancel it.

Do not assume that command-line invocation bypasses confirmation. DUP and SYSGEN retain their destructive-operation safeguards even when invoked with complete command-line arguments.

##### COPY File-Collision Prompt

When COPY encounters an existing writable destination file, the transient utility may offer:

```text
Y/N/O/S/R/?
```

| Response | Meaning |
|---|---|
| Y | Replace this file |
| N | Skip this file |
| O | Replace this and subsequent writable collisions |
| S | Skip this and subsequent writable collisions |
| R | Enter a new destination filename |
| ? | Display help |

The O and S policies apply only to the current COPY invocation.

##### REN Name-Collision Prompt

When transient REN encounters an existing destination filename, it may offer:

```text
File exists. N/S/A/?
```

| Response | Meaning |
|---|---|
| N | Enter a new filename |
| S | Skip the file |
| A | Abort the remaining operation |
| ? | Display help |

REN never overwrites an existing destination.

##### Retry, Skip, or Abort

Some utilities offer recovery choices when an individual file operation fails.

For example:

```text
R/S/A/?
```

The responses are:

| Response | Meaning |
|---|---|
| R | Retry the operation |
| S | Skip the affected file |
| A | Abort the remaining operation |
| ? | Display help |

The availability of these choices depends on the utility.

Noninteractive modes may follow a predetermined error policy instead of displaying a recovery prompt.

##### Help at Prompts

When `?` appears among the available responses, entering it displays an explanation of the choices.

Requesting help does not itself retry, skip, abort, or authorize an operation.

The utility returns to the same decision after displaying the help text.

##### F.10 Interpreting Error Messages

When an error occurs, the most useful first step is to determine which component reported it.

A command-processor error usually concerns command recognition or program execution.

A file-management error may involve filenames, attributes, destination conflicts, or disk space.

A disk utility error may involve physical media, drive configuration, or unsupported operations.

A resident-extension error may involve missing files, incompatible components, dependencies, or memory limitations.

The following table provides a quick guide.

| Symptom | Likely area to investigate |
|---|---|
| Command not recognized | Command name, `.COM` file location, CPX availability |
| File not found | Filename, drive/user area, wildcard or attribute selection |
| Destination already exists | COPY, MOVE, or REN collision handling |
| File cannot be modified | Read-only or system attributes |
| Disk cannot be read | Media, drive configuration, disk format |
| Disk cannot be written | Write protection, capacity, media errors |
| Program has insufficient memory | Loaded resident extensions, available TPA |
| Full-screen display is incorrect | Terminal personality, screen backend, application configuration |
| TIME cannot display the clock | Clock provider or underlying clock source |
| System fails after configuration changes | Saved drive settings, startup command, system image |
| System disk will not boot | Bootstrap compatibility, incomplete installation, damaged media |

##### When an Operation Fails Partway Through

Some BetterCP/M operations process several files or disk records in sequence.

If an error occurs, earlier operations may already have completed.

For example, a multi-file COPY may have created several destination files before encountering an error.

A multi-file REN may have renamed some files before encountering a name conflict.

An interrupted DUP copy may leave the destination partly written.

An interrupted SYSGEN installation may leave the destination's system area incomplete.

**Do not assume that an interrupted operation has been automatically undone.**

Examine the affected files or disks before retrying.

##### Preserving Evidence of a Problem

If an error appears to be reproducible, record its exact wording.

Also note the command entered, the current drive and user area, and any relevant configuration information.

For problems involving resident extensions, the output of `CPX LIST` or `RSX LIST` may be useful.

For disk-related problems, record the drive assignments and disk format.

When reporting a compatibility problem, identify the application, BetterCP/M version, and computer or emulator.

See [Appendix E](Users-Guide.md#appendix-e) for additional guidance on compatibility reporting.

<a id="command-summary"></a>

## Command locator

Commands are indexed by function above. Each entry contains its own syntax and invocation examples. For memory commands, P is an alias for PEEK. User/drive navigation such as B3: is performed directly by the CCP.
