# BetterCP/M source comment conventions

Comments explain the source as it exists. They should describe purpose, state,
assumptions, constraints, and non-obvious behavior for a reader familiar with
Z80 assembly and CP/M. Do not add structure merely for visual symmetry or
annotate routine instructions with a restatement of the opcode.

There are four visual forms:

1. A single file header, beginning in column 1, uses `; *` and an asterisk
   border. Reserve this style for the file as a whole.
2. Major functional divisions use `; =` and an equals-sign border. A short
   description may explain the division. All title and description text must
   fit within the fixed width of the border. Reflow description text across
   additional lines as necessary; never allow it to extend beyond the closing
   `=`. If a word must be divided at the boundary, hyphenate it rather than
   overflow the border. Leave blank lines around the section.
3. Real subdivisions use `; -` and a dashed border with a concise title.
   Subsections are optional.
4. Explanatory prose begins with two spaces before `;`. Use it for behavior,
   rationale, and constraints that do not fit an inline note. Blank lines
   normally separate these blocks from code.

Every source label should have a brief functional description. Labels and
instructions take inline comments with the semicolon in column 41 when the
code fits. If a long operand extends beyond that column, place the comment
after the complete operand. Descriptions are short phrases, normally beginning
with lowercase. Explain a label's role rather than repeating its name.

A blank line normally precedes a label that begins a distinct logical unit.
Do not split a tightly coupled operation or a consecutive table/storage layout
just to create blank lines.

The parser's boundary matters more than alignment. A semicolon inside an
assembler string literal is data. Never insert a comment by searching for the
first semicolon on a line without recognizing quoted strings and doubled quote
escapes. A comments-only pass must preserve instructions, operands, labels,
directives, constants, data definitions, and their order. Verify this
mechanically before promotion.

The hierarchy is `*` for the file, `=` for major sections, `-` for
subsections, column 3 for explanatory prose, and column 41 for inline notes
when the complete source field ends before it. The aim is to reveal existing
structure, not to maximize comment count.
