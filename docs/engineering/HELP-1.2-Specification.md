# BetterCP/M 1.2 topic HELP system

**Release target: BetterCP/M 1.2 (maintainer decision, 9 November 2026).**
This design originated during 1.1 planning. BetterCP/M 1.1 shipped TCAP 2.0
and deferred HELP. The first development build includes the transient reader
and a starter collection. It has run on BetterCP/M 1.1.1 under cpmsim.
The [Markdown dialect and worked subjects](../../specifications/HELP-MARKDOWN.md)
describe the input format.
[BetterCP/M 1.1 release notes](../releases/RELEASE-NOTES-1.1.md)

## Reader, content and utility independence

- `HELP.COM` is a general, read-only transient reader. It runs in the TPA,
  returns to the caller's DU and incurs zero unloaded resident-memory cost.
  Topic lookup and display require no HELP-specific CCP, CPX, RSX or PDS
  allocation. The CCP may locate `HELP.COM` through PATH. HELP itself uses
  the same effective PATH to look up topics and archives.
- BetterCP/M supplies curated help for operating the system and using its
  packaged utilities. Include system concepts and procedures that span
  commands, such as when SUBMIT also needs XSUB. The manuals carry the full
  treatment. The reader obtains subject names, text and navigation from data
  so the same executable can present an entirely user-authored collection.
- A utility handles its own `/H` and `/HELP` and prints its built-in quick
  reference even on a disk with no HELP facility. It neither calls, links
  to nor probes for HELP. Each utility help screen ends with the literal
  line below, substituting the uppercase command name. Resident and transient
  forms have distinct quick references and may refer to the same system
  topic. For example, both `DIR /H` and `:DIR /H` refer to `HELP DIR`.

```text
For detailed help, see HELP NAME
```

Every printed footer must resolve to a topic in the supplied library.
At release review, account for packaged programs with native interfaces
that currently lack a BetterCP/M help screen, including ZSM4 and LINK.
HELP's own `/H`, `/HELP` and `/VER` follow the utility query contract and
must work before any help-file or archive access. [Utility help contract](../../specifications/UTILITY-HELP.md)

## Subject files and libraries

One CP/M `.HLP` file is the unit an author writes, a user installs, and a
library stores as a named member. Subject files can be kept individually.
The standard collection is `HELP.LBR`. HELP also recognizes `HELP.ARK`.
Users can select any mix of supplied, third-party or locally written subjects
and build their own LBR with NOAH. Adding, replacing, extracting or removing a subject is an ordinary
LBR operation. Authors can distribute a collection containing none of the OS
topics. HELP only needs read access.

The subject is the same in plain, individually squeezed and individually
crunched forms. For PIP these are `PIP.HLP`, `PIP.HQP` and `PIP.HZP`.
The notation `PIP.H?P` below denotes those forms. The reader design calls
for reusing the existing Z80 LBR and ARK readers, CP/M file adapter and
decoders. For an ARK member, decode the archive method to recover the member
contents. A `.HLP` member then contains text. A `.HQP` or `.HZP` member
still needs USQ or UNCR, respectively. HELP includes the required routines.
Validate live decoder memory and paging behavior before choosing
the encoding for release media. [LBR reader](../../src/archive/lbr.mac) · [ARK reader](../../src/archive/ark.mac)
· [USQ](../../src/codec/usq.inc) · [UNCR](../../src/codec/uncr.inc)

## Default topic lookup

For `HELP TOPIC`, make these passes in order. Each pass starts at the
caller's current drive/user (DU), then follows the configured PATH in
order. Resolve symbolic entries against the caller's original DU and skip
entries that would repeat that DU. HELP applies this policy to its own
file opens. [Numeric PATH](Numeric-PATH-1.1.md#using-path)

| Pass | Search across PATH | Result |
| --- | --- | --- |
| 1 | Loose `TOPIC.H?P` | Open the topic in the first DU containing a supported encoding. |
| 2 | First `HELP.LBR` on PATH | If it contains the topic, open it. Otherwise proceed to the ARK pass. |
| 3 | First `HELP.ARK` on PATH | If it contains the topic, open it. Otherwise proceed to the index fallback. |

Within one DU or one archive, prefer `.HLP`, then `.HQP`, then `.HZP`.
For example, a loose `PIP.HQP` in an earlier DU wins over a loose
`PIP.HLP` in a later DU. Only the first archive of each default name
participates in lookup, including index fallback.

For example, from `A0:` with `B0:` on PATH, loose `B0:PIP.HQP` wins
over PIP in `A0:HELP.LBR`. If there is no loose PIP and the first LBR
is on `B0:`, PIP in that LBR wins over PIP in `A0:HELP.ARK`.

If all topic passes miss, display an archived `_INDEX.H?P`, checking LBR
before ARK. An LBR index therefore cannot hide a topic in ARK. If there
is no archived index either, print `No help for TOPIC was found.` with
the requested name substituted and return to CP/M. A damaged or unreadable
file or archive requires a diagnostic distinct from a lookup miss.

## Opening an archive with bare HELP

Bare `HELP` skips loose files and searches the effective PATH for the first
`HELP.LBR`. Only if that search finds no LBR does it search for the first
`HELP.ARK`. Once an archive is selected, display its `_INDEX.H?P` if present.
Otherwise generate the topic menu immediately from that archive's members,
even if a different archive contains an authored index. If neither default
archive exists, report the missing archive and return to CP/M.

List the `.HLP`, `.HQP` and `.HZP` members by basename, once per topic.
Use archive member order, assigning a topic its place on first occurrence.
Selecting an entry opens the preferred encoding of that topic in this
archive. For example, given `DIR.HLP`, `COPY.HLP`, `LIST.HLP`, `COMMAND.HZP`,
`STAT.HLP`, `WIZ.HQP` and `CMD2.HLP`, the 80-column menu reads

```text
0. DIR              1. COPY             2. LIST             3. COMMAND
4. STAT             5. WIZ              6. CMD2
```

Here, pressing `5` opens the archive member `WIZ.HQP` even if a loose
`WIZ.HLP` exists on PATH. At 40 columns the same choices run two per row.

## Reporting a topic's location and selecting a source

`/R` and `/REPORT` are equivalent. In 1.2, a successful report contains
only the location of the selected topic. `/S=filespec` and
`/SOURCE=filespec` name an exact CP/M file. An `.LBR` or `.ARK` selects
a collection. An `.HLP`, `.HQP` or `.HZP` selects an individual topic
in that specific encoding.

| Invocation | Behavior |
| --- | --- |
| `HELP PIP /REPORT` | Use the same lookup as `HELP PIP`. Print the selected loose filespec (for example, `C3:PIP.HQP`) or the archive filespec and actual member name (for example, `B0:HELP.LBR (PIP.HLP)`), then return to CP/M. |
| `HELP PIP /SOURCE=A4:HELP.ARK` | Look up PIP exclusively in the named archive. The same syntax accepts a custom collection such as `A4:TOOLS.LBR`. |
| `HELP /S=A4:TOOLS.LBR` | Open this archive's authored index, or generate a menu from its members. |
| `HELP /S=A4:PIP.HQP` | Open that exact loose file, even if `A4:PIP.HLP` exists. The filename supplies the topic name. |
| `HELP PIP /S=A4:HELP.ARK /R` | Report the actual member selected in the named archive. |
| `HELP /S=A4:PIP.HQP /R` | Report `A4:PIP.HQP` if found. |

On a miss, print
`No help for PIP was found.` and return directly to CP/M, even when an
authored index is available. A match reports the first source chosen by
ordinary lookup in the specified scope. Reporting requires only enough
file or archive metadata to identify that source.

For ordinary reading with an explicit archive, that archive supplies the
topic, its usual index fallback, and the targets of links. If an explicit
source cannot be opened, identify its filespec and return to CP/M.

For a redundant topic operand, the first build accepts
`HELP PIP /S=A4:PIP.HQP`. If the operand differs from the loose file's
basename, as in `HELP COPY /S=A4:PIP.HQP`, report the mismatch.

## Authoring and presentation

The design direction is a small, documented, human-editable ASCII Markdown
subset. An author should be able to write a subject in TED and package it
with NOAH. The online manuals use a broader GitHub Markdown vocabulary.
Reuse suitable passages and examples. Allow conversion and editorial
selection for the console, and make the supplied library reproducible from
maintained sources. Review current behavior before carrying older examples
forward. [User's Guide](../manuals/Users-Guide.md) ·
[Command and Utilities Reference](../manuals/Command-and-Utilities-Reference.md)

**Settled markup rule.** Authors write standard strong emphasis as
`**read-only**`. HELP interprets it. The active console profile determines
whether to render bold, its supported standout style, or ordinary text
without the delimiters. Literal examples preserve their characters. TCAP
owns capability discovery and safe rendition changes; HELP owns parsing,
navigation and pagination. Preserve ordinary console behavior and restore
normal rendition after HELP-owned emphasis and on exit. TCAP 2.0 offers
strong begin/end; its end operation selects normal rendition and cannot
restore arbitrary inherited attributes.
HELP renders readable plain text when optional enhancements are absent.
[Terminal architecture, section 22](POST-1.0-TERMINAL-ARCHITECTURE-OUTLINE.md#22-optional-utility-presentation-and-ascii-fallback)

**Opening page for a sectioned topic.** Display the `#` title, render the
optional synopsis before the first `##`, then present the selectable `##`
section choices in source order, left to right, two per row at 40 columns
and four per row at 80 columns. Assign keys across rows. Use up to 16 visible heading
characters per menu label and show the full heading inside the section.

**Navigation keys.** At a HELP prompt, `^C` or `Q` goes back one level,
exiting to CP/M from the top level. Within a multi-page section, `,` or
`<` goes to the previous page and `.` or `>` goes to the next.

**Full-screen browsing.** With known geometry and TCAP clear and absolute
positioning, HELP reserves the first and last rows. The top row shows the
topic title, `subject - section`, or `Help topics` for a generated archive
menu. A heading too wide to fit, or containing a selectable link, also
appears in the body so its complete contents remain accessible.
The footer lists the available selection keys, the applicable paging
directions and `Q Back` or `Q Exit`. On a diagnostic it uses a compact key
legend and the remaining width for the message. HELP leaves the bottom-right
cell free to avoid scrolling and clears the display on normal full-screen exit.

The fixed layout requires at least three rows and twelve columns. Smaller
or unknown geometry, unavailable TCAP and refused cursor positioning select
the sequential reader. A provider with a clear-screen operation can still
clear between pages in that mode. Utility queries and location reports use
ordinary command output.

**Menu keys in the first build.** Assign choices `0` through `9`, then `A` through
`Z`, skipping `Q` to preserve its navigation meaning. A single keystroke
opens a choice. This gives 35 keys per menu page. For a longer menu, use the
paging keys and assign keys afresh to the visible choices on each page.

**Subject links.** From an archive member, try the originating archive
first, then ordinary topic lookup on a miss. An explicitly selected archive
keeps links within that archive. From a loose file, including one opened
with `/S=`, use ordinary topic lookup for the linked subject.

**Direct section access.** `HELP PIP SELECTORS` opens `## Selectors`
directly in the selected PIP topic. Match the full Level 2 heading
case-insensitively, including all words of a multiword heading. The 16-character
menu label is only for display. A link in another help file can target the
same section with `[PIP selectors](PIP.HLP#selectors)`.
Resolve the subject using the link's normal source rules, then locate the
section inside that copy.

**Markup in the first build.** Use `###` for a local subheading. The reader
renders paragraphs, simple lists, inline code and fenced examples that
preserve spacing. A topic with no selectable sections displays immediately.
Z-System's menus, preformatted examples, cross-file navigation and frames
informed these proposals. Compatibility with historical files, the final
Markdown grammar and the remaining navigation details are open.

## Evidence already available

### First executable build

From the repository root, run `python3 tools/build_help.py --disk`. The
builder requires z80pack's `z80asm`. The optional data disks also require
`cpmcp`. The outputs in `build/help/` are `HELP.COM`, `HELP.LBR` and
`BetterCPM-1.2-HELP` images in DSK (cpmsim), DMK (Model 4) and IMD
(Model II) formats. Mount the appropriate data disk as B on a running
system, type `B:`, then `HELP`. The source collection contains COPY, DIR,
HELP, NOAH, PATH and PIP plus an authored index. New loose subjects can be
tried immediately with `HELP /S=filespec`. A custom directory of ASCII
`.HLP` sources can be packaged with `--subjects directory`.
[Reader source](../../src/utilities/help.mac) · [Topic sources](../../src/help/)

`python3 tools/qualify_help.py --system disk.raw --simulator cpmsim --console`
boots copies of cpmsim media. Supply the System image with its matching
`diskdefs`. The console checks also use `pyte`. The guest exercises PATH
and source selection, report-only misses, both types of index, single-key
menus, direct sections, cross-file links, backward paging, and nested
Ctrl-C. Independent fixtures cover plain, squeezed and crunched subjects
and ARK methods 1 through 9, including compressed help files inside a
compressed ARK member. The data images are compared byte-for-byte after
the plain-console run. Rendered checks cover the shipped 80-column ADM3A,
ANSI and VT52 providers, a 40-column ANSI fixture, and sequential fallback
with missing geometry, missing positioning, or a refused position operation.
The cpmsim 1.2 NDR candidate also resolved `/S=HFILES:HELP.LBR` and a
named PATH entry. Released NOAH verified the CRCs of all seven starter
library members on the mountable cpmsim disk. Extracting the COM and LBR
from the Model 4 and Model II images reproduced the development binaries
with ordinary CP/M record padding.

The reader holds one decoded subject in the available TPA. Compressed input
and its decoder workspace must also fit during decoding. HELP reports
insufficient memory when a topic exceeds the applicable limit. Plain files
can use the whole topic buffer. Navigation retains up to 16 parent views
with their source, section and page. Following a link releases the previous
topic's buffer and returning reopens its source. Without usable TCAP facts,
the initial layout assumes 80 columns and 24 rows and uses plain text.
At page boundaries, further travel in that direction keeps the current page.
A directly requested section is the top level for that invocation.

The broader reference corpus, quick-help footers across the distribution,
Model 4 and Model II execution checks, and release-media integration are
still outstanding.

### Earlier prototypes

The 1.0.1 cpmsim storage experiment used four real subjects (COPY, PIP, XSUB
and FILES) and a 40-subject growth fixture plus index. The latter used 82 KiB
as loose plain files, 40 KiB in the prototype indexed `HELP.HLP`, 40 KiB as
plain LBR members, 34 KiB squeezed in LBR, and 28 KiB crunched in LBR.
These are data allocations on the tested 332 KiB format. Both large plain
containers used two CP/M directory entries. All archived members round-tripped.
The advantage of LBR is that ordinary tools can manage the individual files.

The cpmsim reader trial exercised embedded data and a separate indexed
`A0:HELP.HLP`, including paging and damaged data. That location and format
were experimental. The trial did not exercise a production LBR reader.
Separately assembling the reusable LBR reader, adapter, common codec routines,
USQ and UNCR yielded 3,651 bytes of code before HELP integration. The current
USQ and UNCR contexts require 1,440 and 26,582 bytes respectively. Memory
figures for the finished reader and costs of backward paging remain unmeasured.

The detailed inventory, trial reports and prototype sources are preserved at
local workstream commit `dc77e16a` on `feature/help-1.1`, under
`docs/engineering/HELP-1.1-*` and `tools/prototypes/help/`. The 1.0 to 1.0.1
inventory found changes in the explanatory quick-help text of three shipped
transients (PIP, RSX and XSUB), and implementation-specific screens for the
nine resident RCP commands.

## Resuming HELP work for 1.2

1. Review the [delivered TCAP 2.0 direct ABI](TCAP-Direct-ABI.md). Establish what HELP can rely on for
   geometry, unknown dimensions, semantic standout, plain output, cancellation
   and state restoration. Use the shared facility across supported platforms.
2. Define diagnostics for a missing default archive, an archive with no
   index or topics, a damaged member or index, and insufficient decoder TPA.
3. Freeze the Markdown subset, section fragment spelling, behavior for
   missing link targets, wrapping and page boundaries.
   Use a short topic and a multi-section topic at narrow and wide
   console widths to review the result.
4. Measure startup and member access on floppy-oriented media. Assess
   whole-topic buffering and return-to-parent read costs with a larger corpus.
5. Review the final corpus, footer coverage, source-to-help conversion and
   disk placement. Qualify the reader, console fallback, read-only behavior,
   caller-state preservation and release media on cpmsim, TRS-80 Model 4 and
   the maintained TRS-80 Model II target.
