# BetterCP/M 1.2 topic HELP system

**Release target: BetterCP/M 1.2 (maintainer decision, 9 November 2026).**
This design originated during 1.1 planning. BetterCP/M 1.1 shipped TCAP 2.0
and deferred HELP. Implementation and qualification of the reader are pending.
The resumed design review covers the [proposed Markdown dialect and worked
subjects](../../specifications/HELP-MARKDOWN.md), including the delivered
TCAP behavior for paging and strong emphasis.
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
| 1 | Loose `TOPIC.H?P` | Open the first matching DU's plain, squeezed or crunched topic. |
| 2 | `HELP.LBR` | Open `TOPIC.H?P` if found inside. |
| 3 | `HELP.ARK` | Open `TOPIC.H?P` if found inside. |

For example, from `A0:` with `B0:` on PATH, loose `B0:PIP.HQP` wins
over PIP in `A0:HELP.LBR`. If there is no loose PIP, PIP in
`B0:HELP.LBR` wins over PIP in `A0:HELP.ARK`.

If all topic passes miss, display an archived `_INDEX.H?P`, checking LBR
before ARK. An LBR index therefore cannot hide a topic in ARK. If there
is no archived index either, print `No help for TOPIC was found.` with
the requested name substituted and return to CP/M.

Bare `HELP` displays the archived `_INDEX.H?P` if present. In an archive
without an index, bare `HELP` generates a menu from the available help
members. The menu presents logical subject names, so `PIP.HQP` appears as
`PIP`. Thus `_INDEX` is optional. A damaged or unreadable file or archive
requires a diagnostic distinct from a lookup miss.

Two tie cases remain open. If several encodings of the loose topic share a
DU, their precedence needs a rule. If several DUs contain the same archive
filename, lookup needs a rule for whether a member miss in the first such
archive continues to later copies of that archive.

## Reporting a topic's location and selecting a library

Source information is available on request through the proposed `/REPORT`
switch. The proposed `/LIBRARY=` switch selects the collection to search.

| Invocation | Behavior |
| --- | --- |
| `HELP PIP /REPORT` | Use the same lookup as `HELP PIP`. Print the selected loose filespec (for example, `C3:PIP.HQP`) or the archive filespec and actual member name (for example, `B0:HELP.LBR (PIP.HLP)`), then return to CP/M. |
| `HELP PIP /LIBRARY=A4:HELP.ARK` | Look up PIP exclusively in the named archive. Use the same syntax for a user-built collection such as `A4:TOOLS.LBR`. |
| `HELP PIP /L=A4:HELP.ARK /REPORT` | `/L=` is the short spelling of `/LIBRARY=`. Report the result of lookup in that archive only. |

`/REPORT` answers whether the requested topic was found. On a miss, print
`No help for PIP was found.` and return directly to CP/M, even when an
authored index is available. A match reports the first source chosen by
ordinary lookup in the specified scope. Reporting requires only enough
file or archive metadata to identify that source.

For ordinary reading with `/LIBRARY=`, the selected archive supplies the
topic and its usual index fallback. With no topic, show that archive's
authored index or generate its menu. If the specified archive cannot be
opened, identify it in the diagnostic and return to CP/M.

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
Completion of TCAP is a development dependency. Once shipped, HELP must
still be readable on a plain console when optional enhancements are absent.
[Terminal architecture, section 22](POST-1.0-TERMINAL-ARCHITECTURE-OUTLINE.md#22-optional-utility-presentation-and-ascii-fallback)

**Opening page for a sectioned topic.** Display the `#` title, render the
optional synopsis before the first `##`, then present the numbered `##`
section choices in source order, left to right, two per row at 40 columns
and four per row at 80 columns. Continue numbering across rows. Use up to 16 visible heading
characters per menu label and show the full heading inside the section.

**Navigation keys.** At a HELP prompt, `^C` or `Q` goes back one level,
exiting to CP/M from the top level. Within a multi-page section, `,` or
`<` goes to the previous page and `.` or `>` goes to the next.

**Proposed for review.** Use `###` for a local subheading. Add paragraphs,
simple lists, inline code, fenced examples that preserve spacing, and links
between subjects. A topic with no selectable sections could display immediately.
A command such as `HELP PIP SELECTORS` could go directly to a section.
Z-System's menus, preformatted examples, cross-file navigation and frames
informed these proposals. Compatibility with historical files, the final
Markdown grammar and the remaining navigation details are open.

## Evidence already available

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
2. Settle handling of repeated archive filenames along PATH and precedence
   if several encodings of a subject coexist in one DU or archive. Define the bare-`HELP`
   diagnostic when neither archive exists and errors for a damaged member
   or index and insufficient decoder TPA.
3. Freeze the Markdown subset, section and link naming, behavior for absent
   linked subjects, direct-section lookup, wrapping, menu selection and page
   boundaries. Use a short topic and a multi-section topic at narrow and wide
   console widths to review the result.
4. Integrate the reader and measure startup, member access, decoder workspace,
   forward and backward navigation on floppy-oriented media. Verify plain
   topics can run without reserving the Crunch workspace.
5. Review the final corpus, footer coverage, source-to-help conversion and
   disk placement. Qualify the reader, console fallback, read-only behavior,
   caller-state preservation and release media on cpmsim, TRS-80 Model 4 and
   the maintained TRS-80 Model II target.
