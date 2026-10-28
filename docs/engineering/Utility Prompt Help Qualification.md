# Utility inline prompt-help compliance

Date: 2026-10-28. Implements the maintainer-authorized compliance update for
NOAH, CRCKSUM and MD5SUM under the established
[interactive prompt convention](Interactive%20Prompt%20Convention.md).

## Behavior

CRCKSUM and MD5SUM use `Overwrite? (Y/n/a/?)`. Help prints
`Y Yes, N No, A All, ? Help`, then repeats the complete DU/name and question.
Enter still authorizes this replacement; All still applies to later existing
list destinations in the same invocation. No or Ctrl-C retain their meanings.
The shared output engine implements both utilities' correction.

NOAH ordinary output/member replacement uses `Y/N/A/C/?`, default No; its help
is `Y Yes, N No, A All, C Cancel, ? Help`. Safe recovery uses `R/S/A/?`, default
Skip, with `R Retry, S Skip, A Abort all, ? Help`. Recovery callers supply an
explicit source/output/archive context callback. Repainting never selects a new
item or performs a retry. The write-source callback preserves IX around its
context rendering. Paging still uses the raw input function; only the choice
binding handles help. Simple protected/destructive Y/N questions remain simple.

Help is consumed before the choice controller accepts an action, keeping the
last choice, defaults, counters, transaction state and All policy unchanged.
`/Y` remains noninteractive and `/Q` retains required prompts/help. Rename,
View, Expand, Delete and other new actions are outside this change. No PATCH
specification or implementation is modified.

MD5SUM's console row buffer is reduced from 256 to 128 bytes; reference lines
retain their separate 256-byte buffer. Generated MD5 digest/name rows are at
most 46 characters and verification rows fit within 128. This keeps the primary
Utilities allocation at 18K while adding help. Saved formats are unchanged.
NOAH.TXT retains CRLF and its final Ctrl-Z; its inline-help note precedes that
terminator. The path's whitespace attribute recognizes CP/M CRLF explicitly.

## Current revisions and evidence

| Component | Revision | COM bytes | SHA-256 |
| --- | --- | --- | --- |
| CRCKSUM 1.0 | 006 | 22,189 | `ce4ce0711f893b6a9e4b2491f3644424b8e6caccdc1efde24e3499d2a9c7041d` |
| MD5SUM 1.0 | 002 | 18,316 | `692a83f1e21911987cdabba8747463a306ac5b46e6d91b7c8bc47d00a5576022` |
| NOAH 1.0 | 018 | 19,068 | `076c5486cf5638811258df6297ea122e046f885eecfd27f30bf878c87f10a51c` |

NOAH also requires its newly matched overlay. The JSON record beside this note
binds both files and exact packaged cpmsim image identities. Historical component
qualification records are preserved; their PASS verdicts do not automatically
qualify these changed binaries.

Focused verification:

- 16 checksum prompt scenarios compare repeated help plus Y/N/Enter/All/Ctrl-C
  against the same operation without help. They check identical files/writes,
  full-context reprompt counts, All persistence and 40-column display.
- 29 NOAH scenarios compare repeated help plus replacement and recovery choices
  against the same operation without help. They cover extraction and ADD member
  collisions, source/codec/output/whole-archive failure contexts, Retry, Skip,
  Enter, Abort, Escape, Ctrl-C, quiet behavior, unattended behavior and unchanged
  protection prompts. Files, attributes and publication actions agree.
- Existing 129 CRCKSUM and 87 MD5SUM compiled fixtures pass. NOAH's existing
  write, source-failure and quiet groups pass (90 cumulative command cases).
- Stock CP/M 2.2 ZSM4/LINK reproduces CRCKSUM and MD5SUM exactly. NOAH's changed
  resident and CLI modules also match native assembly byte-for-byte, including
  expected record padding; the matching overlay is built from the current phase
  sources.
- Exact packaged cpmsim primary B: and NOAH companion C: pass two help requests
  followed by No for each utility. The prompts repeat the same target. Original
  targets, reference lists, source archive and complete B:/C: images remain
  unchanged. This is actual guest execution in addition to the controlled model.
- Candidate construction checks readback, filesystem integrity and Model 4
  DMK/raw conversion. Both checksum source-closure/acceptance-refusal checks pass.
  Registry projections, registry cases, Python syntax and whitespace checks pass.

```sh
python3 tools/test_utility_prompt_help.py
python3 tools/test_utility_prompt_native.py
python3 tools/build_native_crc.py
python3 tools/build_native_md5sum.py
python3 tools/build_utilities_disk.py --build --output build/prompt-help-utilities
python3 tools/test_utility_prompt_media.py \
  --image-dir /path/to/BetterCPM/build/z80pack \
  --utilities build/prompt-help-utilities \
  --report build/prompt-help-development/cpmsim
```

The primary 332K candidate remains 26 files with 2K free. NOAH remains on its
existing companion volume. Measured reports and transcripts are under
`build/prompt-help-development` and the individual native/compiled test output
locations. Use fresh output directories when rerunning the media campaign.

## Qualification limits

No Model 4 runtime test is claimed for these revisions. The known sandbox
LaunchServices restriction remains, and the checksum utilities' existing Model 4
validation deferral is retained. NOAH's earlier Model 4 results apply to their
recorded binaries, not automatically to revision 018. No new qualification waiver
or runtime PASS is invented for NOAH. No qualified baseline, acceptance receipt
or frozen release is promoted. Saved-list and archive algorithms are unchanged;
the new byte identities reflect prompt code, context callbacks and revisions.
