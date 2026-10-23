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

Use the compact identification from [Visual Identity](VISUAL-IDENTITY.md), with
the same metadata-owned version, build and purpose as `/VER`. Follow it with:

1. One plain sentence describing the operation.
2. `Usage:` and invocation forms, including `/HELP` and `/VER`.
3. Supported options, each with a short explanation.
4. One or more concrete examples.
5. Essential defaults, restrictions and safety behavior.

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

SQ, USQ, CR, UNCR, LZH and UNLZH use one screen each. Each lists the exact
source and optional destination-drive syntax, both query options, an example,
the logged-drive/current-user defaults, refusal to overwrite existing output,
source retention, and the absence of wildcards. The final line describes a
relevant naming rule or supported format. SQ also states its two-pass stability
requirement. Decoder examples use historical compressed extensions but do not
imply that input extensions determine decoding or the restored name.

These commands retain their existing short syntax for malformed input and add
the help hint. Their query entry is shared with `/VER`, before normal file-state
initialization. Version/build identification follows
[Utility Versioning](UTILITY-VERSIONING.md). Help output is generated during
build preparation, with no filesystem or environment lookup at runtime.

## Example screen

The SQ screen at initial help adoption is:

```text
SQ 1.0 (Build 002)
  - - -
 | BetterCP/M Utilities
 | Squeeze File Compression

Compress one file into historical squeezed format.

Usage: SQ [drive:]file [destination-drive:]
       SQ /HELP
       SQ /VER

  /HELP   Display this help.
  /VER    Display utility identification.

Example: SQ A:REPORT.TXT B:

Output defaults to the logged drive and current user area.
Existing output files are refused; the source is retained.
Wildcards are not supported.
REPORT.TXT becomes REPORT.TQT. Input is read twice; keep it unchanged.
```

## Qualification

For each adopting utility, test the complete help text, screen dimensions,
case/space/TAB handling, exact-token boundaries, repeated/mixed query requests,
maximum command-tail length, empty invocation, and malformed syntax. Verify
that query paths use console output only and preserve files, drive/user, FCBs,
workspace, command tail, caller stack and required registers. Execute the
transient commands under CP/M 2.2 as well as the CPU test harness. Continue the
utility's ordinary functional regression tests after adding query dispatch.
