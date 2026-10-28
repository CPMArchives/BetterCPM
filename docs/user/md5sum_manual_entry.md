## MD5SUM file digests and verification lists

**MD5SUM 1.0 development candidate.** MD5SUM is included in newly built candidate Utilities images. Focused native-build and cpmsim checks pass; Model 4 execution and paired release acceptance remain pending. This is not a released-disk qualification claim. The [engineering specification](../engineering/MD5SUM-Specification.md) controls the design.

MD5SUM calculates one MD5 digest for each selected file. Save the results, and you can later check whether the files still agree with that list. Its selection, master/local output, overwrite and checking behavior follows CRCKSUM. There is only one algorithm and one saved-list format.

### Getting started with MD5SUM

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

### MD5SUM options

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
| `/HELP` | Display help without file access. |
| `/VER` | Display the utility's identity without file access. |

Options are case-insensitive and may appear before, between or after filespecs. Repeated value options must all be valid; the last value is used. A later bare CHECK does not erase an explicit CHECK filename. HELP takes precedence over VER, and either query ignores ordinary operands and options.

FILE and LOCAL may be combined. CHECK is a separate operation and cannot be combined with either. There are no algorithm-selection switches or LEGACY mode.

### What the digest covers

MD5SUM includes every byte of every stored 128-byte logical record. Embedded Ctrl-Z, high-bit bytes and final-record padding all count. No text conversion takes place. Files larger than 64 KiB are processed as a stream.

A host MD5 program gives the same answer for exactly the same bytes. If a transfer strips CP/M padding or changes line endings, it changes the file being hashed. Keep the complete stored bytes when comparing a CP/M digest with a host digest. Accepting a text-mode entry in a list does not change this rule.

MD5 is useful for identifying files and detecting accidental changes. It does not establish authorship or protect against deliberately constructed collisions.

### Reading and saving the results

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

### Master and local lists

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
B3:MD5SUM.LST exists. Overwrite? (Y/n/a)
```

Y or Enter replaces this destination. N leaves it alone and continues other outputs. A authorizes this and later replacements in this run. Ctrl-C cancels. Output is staged before replacing a completed list. Handled failures or cancellation discard uncommitted output; recovery failures identify any files left behind. Completed independent local lists remain available even if another output fails.

### Checking against a local list

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

### Exchanging lists with a host system

Export the target files without altering their stored bytes, and keep filename case consistent with the list. Saved CP/M lists may have trailing Ctrl-Z padding. If a host md5sum reader reports that padding as malformed input, remove only the trailing padding from the host copy of the list. Leave target-file padding intact: it contributes to the digest.

Some host readers require LF line endings or the two-space entry form. Convert those list details on the host if needed; target-file bytes must stay unchanged.

The common entry syntax permits exchange of these lists. MD5SUM does not reproduce every host command-line option or support host directory paths inside entries.
