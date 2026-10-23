# Utility Help Screens

## Common contract

BetterCP/M-owned utilities adopting this standard accept standalone,
case-insensitive `/HELP`. Surrounding spaces and TABs are allowed. Recognition
uses the bounded command tail and exact tokens: `/HELPER`, `/HELP.X` and
`X/HELP` are ordinary parser input, not help requests. An exact `/HELP` token
combined with any operand or another token prints `Invalid /HELP usage.` and
returns without command operations. An exact `/VER` token takes precedence
anywhere in a mixed request, including `/HELP /VER`; the version contract
therefore reports `Invalid /VER usage.` in either order.

Help and invalid query requests return to the caller before file operations,
drive/user inquiry or changes, DMA changes, codec/provider initialization, or
terminal-backend setup. They may use console string output only. They preserve
the command tail and the caller's return path. Adopted third-party utilities
are outside this contract. Existing owned utilities adopt it individually;
this document does not claim that every current utility implements `/HELP`.

## Content and presentation

Use the short implied corner from [Visual Identity](VISUAL-IDENTITY.md).
The first line is `NAME version (Build nnn)`, using the same metadata-owned
identity as `/VER`, followed by `  - - -`. Help omits the BetterCP/M Utilities
branding line and the separate HELP heading. Use a concise purpose phrase.

The exact layout is:

- Purpose: one leading space, `|`, one space, then the purpose.
- Corner spacer: ` |` on its own line, with no trailing spaces.
- Syntax: ` |   Usage: NAME [options] [operands]`, using the command's actual
  accepted operand order. Omit `[options]` when only standalone queries exist.
- One empty line ends the corner. Do not extend the vertical line alongside
  the options list.
- `   Options:` begins the list, indented three spaces.
- Each option begins with five spaces; align descriptions in a second column.
  `/HELP       Display this help.` and
  `/VER        Display utility identification.` are the common final entries.
  With operational switches, separate those final queries with one blank line;
  with only these two queries, no extra separator is needed.

Do not repeat query invocation forms under Usage or add an Example section.
Examples, naming rules, detailed defaults, restrictions and safety explanations
belong in the manual. The purpose and syntax should make the operation clear.

Use CR/LF-terminated plain ASCII text. No ANSI sequences, color, cursor control,
terminal personality, decorative full borders or interactive paging are needed.
Simple utilities must fit one 80-column, 24-line screen, reserving a line for
the returned prompt: at most 23 printed lines, with at most 79 characters per
line to avoid terminal wrap. Use blank lines to separate related groups.
Longer utilities should define a separate topic-help design before adoption.
Help is a quick reference; full procedures and detailed error recovery belong
in the manual. Normal successful commands do not print the help banner.

An empty invocation prints short syntax followed by `Use NAME /HELP for help.`
Utilities requiring operands should use this same short response for malformed
syntax. A specific diagnostic should precede it when the parser can identify
the error reliably. Runtime/file failures retain their specific diagnostics.
Do not replace a useful diagnostic with a full help screen.

## Initial adoption: compression commands

SQ, USQ, CR, UNCR, LZH and UNLZH use one compact screen each: identity,
short purpose, exact source/optional destination-drive syntax, and the two
standalone queries. They have no operational switches, so Usage does not show
`[options]`. Their manual pages retain examples, drive/user defaults, naming and
format rules, source retention, overwrite refusal and other safety details.

These commands retain their existing short syntax for malformed input and add
the help hint. Their query entry is shared with `/VER`, before normal file-state
initialization. Version/build identification follows
[Utility Versioning](UTILITY-VERSIONING.md). Help output is generated during
build preparation, with no filesystem or environment lookup at runtime.

## Example screen

The SQ screen using this layout is:

```text
SQ 1.0 (Build 003)
  - - -
 | Squeeze compression
 |
 |   Usage: SQ [drive:]file [destination-drive:]

   Options:
     /HELP       Display this help.
     /VER        Display utility identification.
```

A utility with more switches would use the following layout. TOOL and its
operational switches are illustrative, not implemented compression options:

```text
TOOL 1.0 (Build 002)
  - - -
 | File processing utility
 |
 |   Usage: TOOL [options] [drive:]file

   Options:
     /A          Process all matching files.
     /B          Select binary mode.
     /D drive:   Select the destination drive.
     /L          List files without processing.
     /Q          Suppress progress messages.
     /T          Test input without writing output.

     /HELP       Display this help.
     /VER        Display utility identification.
```

## Qualification

For each adopting utility, test the complete help text, screen dimensions,
case/space/TAB handling, exact-token boundaries, repeated/mixed query requests,
maximum command-tail length, empty invocation, and malformed syntax. Verify
that query paths use console output only and preserve files, drive/user, FCBs,
workspace, command tail, caller stack and required registers. Execute the
transient commands under CP/M 2.2 as well as the CPU test harness. Continue the
utility's ordinary functional regression tests after adding query dispatch.
