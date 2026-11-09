# BetterCP/M 1.2 help-file format

**Design draft for review, 9 November 2026.** A subject is a human-editable
ASCII Markdown file. The same markup applies to a loose file and to a
decoded LBR or ARK member. The opening-page rule and the navigation keys below are
settled. The remaining dialect and interaction details are under review.
See the [system specification](../docs/engineering/HELP-1.2-Specification.md)
for topic lookup, the utility footer and the bare-`HELP` index and menu rules.

## Worked subjects

[PIP.HLP](../docs/engineering/examples/help/PIP.HLP) has a one-line synopsis, three
sections and a local subheading. [COPY.HLP](../docs/engineering/examples/help/COPY.HLP)
shows a short subject. Both are reachable by ordinary subject name and from
the links in the sample [_INDEX.HLP](../docs/engineering/examples/help/_INDEX.HLP).
The examples use the [command reference](../docs/manuals/Command-and-Utilities-Reference.md#pip).

## What an author writes

| Construct | Proposed meaning |
| --- | --- |
| `# Title` | First nonblank line. The title is display text. The CP/M file or archive member basename supplies the subject name for lookup. |
| Content between the title and the first `##` | Optional synopsis on the section menu. An author can give a command form in a fenced block, write a brief description or omit the synopsis. Keep longer explanations under a section heading. |
| Paragraphs | Blank lines separate paragraphs. Join adjacent prose lines with a space and wrap to the usable width. |
| `## Heading` | A named, selectable section. The reader builds a menu from section headings in source order. A section ends at the next `##` or end of subject. |
| `### Heading` | A local heading displayed as part of its section. |
| `- item` or `1. item` | A simple one-level list. Preserve ordered-list numbers and indent wrapped continuations. |
| Inline code between single backticks | Display its contents literally. Wildcards, brackets, underscores and asterisks in commands keep their CP/M meaning. |
| Three backticks on a line | Start or end a literal block. Accept an optional `text` tag on the opening fence so examples can be copied from the manuals. Preserve line breaks and spaces. Markup and heading recognition are suspended until the closing fence. |
| `**text**` | Standard Markdown strong emphasis in prose. On a plain console display the enclosed words. |
| `[label](COPY.HLP)` | Selectable reference to a logical subject in the active library. This target can resolve to the plain, squeezed or crunched representation. A missing linked subject identifies the missing target and leaves the originating topic available. |

On CP/M media, use ASCII and CR/LF; recognize a text EOF (1Ah) or the
logical end of the loose file or decoded member. Markdown is interpreted
after decoding, so a 1Ah inside compressed bytes has no text meaning.
Repository sources may use LF; convert to CP/M text when preparing media.
Use visible ASCII punctuation literally unless it forms a supported, complete
construct. In particular, brackets in `B[-]:*.COM` do not make a link.
Pipe tables, HTML and terminal control sequences are outside the proposed
dialect. Aligned material can be represented by a fenced block.

## Reading the examples

**Opening page.** For a subject with sections, display the `#` title, render
the optional synopsis before the first `##`, then list every `##` heading in
source order. HELP supplies the numbers and fills each row left to right:
two choices per row on a 40-column display and four on an 80-column display.
Use 20-column slots and continue numbering on the next row. Short labels
keep the same layout; a partial final row contains only the remaining choices.

For layout, use the first 16 visible characters of each section heading as
its menu label. The selection number and separator are outside that count.
For example, `Some really, really, long title that doesn't fit` appears as
`Some really, rea`. Display the complete heading when the section opens.
Two sections whose first 16 characters coincide retain distinct menu numbers.

Example at 80 columns:

```text
PIP - File and device transfer

PIP destination=source[,source...]

1  Syntax           2  Selectors        3  Examples
```

The same menu at 40 columns:

```text
1  Syntax           2  Selectors
3  Examples
```

| Request | Proposed result |
| --- | --- |
| `HELP PIP` | Show the Level 1 title, then the command synopsis, then a menu of all Level 2 headings: **Syntax**, **Selectors**, **Examples**. Omitting the synopsis yields a title-and-menu opening. Section bodies appear upon selection. |
| `HELP PIP SELECTORS` | Open **Selectors** directly and display **Duplicate names** within it. |
| `HELP COPY` | Display the topic immediately. Its link to PIP is available without creating an empty section menu. |
| `HELP` using the sample index | Render the authored index as a normal subject with two selectable links. `HELP PIP` also finds PIP independently of the index. |

Use the complete `##` heading as the direct-section name. Compare the remaining
command-tail words case-insensitively, treating runs of spaces or tabs as
one separator. This also permits `## File attributes` to be addressed as
`HELP DIR FILE ATTRIBUTES`. Require section names to be unique after that
normalization. Menu numbers are local to the display; examples and references
may use a section's name even after its menu position changes.

## Navigation keys

| Key at a HELP navigation prompt | Action |
| --- | --- |
| `^C` or `Q` | Return one level. At the top level, exit to the CP/M command prompt. |
| `,` or `<` | Display the previous page of the current section. |
| `.` or `>` | Display the next page of the current section. |

Paging within a section leaves its parent unchanged. For example, start at
the library menu, open PIP, select Examples and advance two pages. The first
`Q` returns to the PIP section menu, the second to the library menu, and the
third to CP/M. Handle Ctrl-C as a navigation key at these prompts so a nested
view can return to its parent.

## TCAP 2.0 findings

The delivered [direct ABI](../docs/engineering/TCAP-Direct-ABI.md) supplies
usable rows/columns and a strong-emphasis operation through the
[shared client helper](../src/utilities/common/tcap2.inc). The shipped profiles
advertise a fixed 80×24 viewport. ADM-3A and ANSI choose reverse video for
strong text; VT52 chooses plain. Zero dimensions mean unknown. Output routing
and provider ownership are checked by the helper. A refused discovery or
unsupported style must leave readable text.

Emit the text itself through ordinary console output. End a HELP-owned strong
span before a paging prompt or return and resume it if more styled text
follows. Strong-end selects normal rendition. The interface provides no
snapshot or nested restoration of arbitrary attributes set by another program.
Keep literal examples intact across page breaks and count visible rows after
wrapping; formatting delimiters occupy zero columns. Narrow displays and
unknown geometry still need an explicit pager policy.

## Choices to review before freezing the format

Direct addressing of a section by name and the role of `###` within the section
remain under review. Other review points are menu-number entry, link selection
on a plain terminal, return position after following a link, the top level
for a direct command-line request, behavior at the first and last page,
long literal lines on a narrow display and the handling of malformed input.
On a compressed subject a generated section menu requires a scan of the
decoded headings. Measure that cost alongside direct jumps and backward paging
before committing to a buffering strategy.
