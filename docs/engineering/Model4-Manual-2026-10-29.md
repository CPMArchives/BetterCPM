# Model 4 manual validation — 2026-10-29

Status: partial execution; release acceptance remains pending.

The maintainer confirmed freshly downloaded candidate images mounted A–D in
trs80gp. Downloaded package SOURCE commit: 021f53143292e80f2739b7c99f3e6e180816d6fd.
The later platform-split candidate 6ee4f26 has byte-identical disk images, as
recorded in Utilities Platform Packages 2026-10-29.md. No new binaries are
covered by these observations. Emulator version and direct mounted-path/hash
binding remain to be captured. Observations are from maintainer screenshots
and explicit confirmation; they are not an automated runtime campaign.

## Observed results

- PASS (contents only): DIR [a,b,c,d]: shows system files on A, primary
  utilities including CRCKSUM/MD5SUM on B, NOAH/PATCH/COMPARE on C,
  and NO FILE on D. Screenshot 2.08.40 PM.
- PASS (startup extensions only): RSX LIST shows M4SCRN and ADM3A.
  TPA available is **50K**, corrected by the maintainer. Screenshot 2.09.37 PM.
- OPEN formatting finding: TPA available runs directly after ADM3A : BDOS 255.
- PASS (version queries only): CRCKSUM 1.0 (006-dev), MD5SUM 1.0 (002-dev),
  NOAH 1.0 (019), PATCH 1.0 (001-dev), COMPARE 1.0 (002-dev),
  DUMP 1.0 (007), DASM/DSYM/TED 1.0 (002-dev).
  Screenshots 2.20.11, 2.26.00 and 2.28.04 PM.
- PASS (query dispatch only): /VER /HELP /BOGUS displays help without an
  invalid-option error for DUMP, DASM, DSYM, TED, NOAH, PATCH, CRCKSUM and
  MD5SUM. Screenshots 2.30.06, 2.31.42, 2.33.16, 2.34.44, 2.41.31,
  2.43.01, 2.44.07 and 2.44.41 PM respectively. DUMP /HELP alone also
  displays help (2.29.08 PM). These checks do not prove full query-state,
  media preservation, screen-fit or functional qualification.
- FAIL: COMPARE 1.0 (002-dev) /VER /HELP /BOGUS prints only identification
  and returns to CCP. Screenshots 2.37.54 and 2.38.54 PM; maintainer confirms
  /HELP alone displays help. Expected HELP precedence over VER and bad tokens.

## Still pending

All functional, prompt, cancellation, native-parity, binary/media preservation,
large-file and fresh-install assertions in Model 4 Release Checklist.md remain
pending unless explicitly covered above. M4-01 and M4-02 are partial, not
blanket PASS. Earlier deferred/blocked records are retained unchanged.
:VER /BANNER was requested; its screenshot has not yet been assessed here.

## Screenshot references

Evidence remains in the conversation and original uploaded screenshots. File
identities for version batches: libfile_c751f5c662148191b6c8181410d7ae08,
libfile_e2fedb8554108191b30ac5d8f19983fd, libfile_afb7ebf0f68081919717025403de28bd.
COMPARE failure: libfile_77165d8989708191b0563e9f6672fc6c,
libfile_9c61b77239148191bbd39c814951f762.

## COMPARE fix verification (host and cpmsim, not Model 4)

Root cause: START queried OPVER before OPHELP. Reordered the exact-token
queries so HELP wins independent of token order. COMPARE advances to 1.0
(003-dev); no other component revision changes. The observed 002 failure
above is retained.

- PASS: 92 compiled COMPARE cases, including exact help-output equality for
  /VER /HELP /BOGUS and three other order/case variants. Query cases call
  console-only BDOS; harness checks caller stack, drive/user, default DMA,
  read-only behavior, comparisons, paging, cancellation and 64-KiB boundaries.
- PASS: ZSM4/LINK native build under cpmsim, all 6658 COM body bytes identical
  to cross build; native summary comparison executes successfully.
- Fixed COM SHA-256: 8388454c4a5affbf6dccb2e8e75bf16fa17a22d1481251e22e3dd42a12b4ada4.
- Commands: python3 tools/build_compare.py; python3 tools/test_compare.py;
  python3 tools/build_native_compare.py.

Existing downloaded candidates still contain COMPARE 002. No release images
were replaced or promoted by this fix. A rebuilt candidate must identify 003
and repeat the affected packaged cpmsim and manual Model 4 query checks.
Functional Model 4 coverage remains pending.

## Further manual execution — COMPARE 002

PASS (same-file summary only): C:COMPARE A:README.TXT A:README.TXT /SUMMARY.
Both lengths, positions examined and byte pairs compared: 3584. Mismatches
and additional bytes in either file: 0. FILES IDENTICAL. Screenshot
2026-10-29 2.51.30 PM, libfile_7a6ad1373dac819182e0de1445af5268.
This is partial M4-11 coverage on the original candidate, not revision 003.

PASS (bounded different-file summary): C:COMPARE A:README.TXT A:STARTUP.SUB
/SUMMARY /LEN=80. Lengths 3584 and 128; 128 positions/pairs examined,
127 mismatches, no additional selected-range bytes. FULL FILE LENGTHS DIFFER;
SELECTED RANGES DIFFER. Screenshot 2.53.34 PM,
libfile_91b7529199408191b497d8cab45ea079. Initial mistyped operand was
rejected; corrected command produced this result. Prior instruction predicted
FILES DIFFER, but bounded comparisons correctly use SELECTED RANGES DIFFER.

PASS (narrow unaligned comparison, observed): C:COMPARE A:README.TXT
A:STARTUP.SUB /SIDE /40 /FROM=7 /FROM2=0 /LEN=9. Four-byte rows begin
at 00000004, 00000008 and 0000000C, with the first selected pair at the last
slot of the first row. Summary: offsets 7 and 0, limit 9, positions/pairs 9,
mismatches 8, additional bytes 0 in either file; selected ranges differ.
Screenshot 3.11.00 PM, libfile_ce2e8ab63fac8191a56a5123094fb606.
Partial M4-11 coverage, COMPARE 002; pager/cancellation remain pending.

PASS (paging pause/advance and normal completion, maintainer reported):
C:COMPARE A:README.TXT A:STARTUP.SUB /SIDE /40 /P. Screenshots 3.15.29,
3.15.44 and 3.15.57 PM show successive pauses with Space/Enter next and
Ctrl-C/Q/Esc stop. Maintainer reports advancing through 30-odd pages and
reaching the end. Q-stop was not exercised and remains PENDING; no cancellation
PASS is inferred. Screenshot refs: libfile_45004d3a2ad48191aa943750f3b9e917,
libfile_a3322d9164b4819180fdd7c1e8c42fa7,
libfile_d011793ef48081919d22b65bf3b777e2.

PASS (first-page pager quit): maintainer quit at the first screen of the
same /SIDE /40 /P command. Screenshot 3.22.12 PM,
libfile_81994aff7fdc819187abd9b2538d0b4b shows DISPLAY INTERRUPTED,
COMPARISON CONTINUING..., then full summary: 3584 positions, 128 byte pairs,
127 mismatches, 3456 additional bytes in file 1 and 0 in file 2; FILES DIFFER.
This supersedes the pending first-page quit item above, not nonpaged Ctrl-C
or other pager-key coverage. Tested COMPARE remains 002.

PASS (DUMP 007 basic bounded display and return): B:DUMP A:STARTUP.SUB
/LEN=40 produces four 16-byte rows at 00000000/10/20/30 and returns to B0>.
Bytes show RSX LOAD M4SCRN, RSX LOAD ADM3A, CLS, :VER /BANNER with CR/LF,
then 1A and zero padding. Screenshot 3.24.32 PM,
libfile_bc5a46c432ec8191b8808a7c51c4f212. Partial M4-03 coverage.

PASS (DASM 002 launch only): DASM A:VER.COM displays current identity,
Richard Conn engine attribution and interactive H/? guidance. Screenshot
3.28.03 PM, libfile_926d1c7dde148191aab0af1585bbddbf. This does not establish
that the command-tail filename was loaded or disassembled. Exit pending.

PASS (DASM 002 exit): G at the interactive # prompt returns to B0>.
Screenshot 3.29.31 PM, libfile_afa38826193481918b751a848feb4efd.
Together with the launch observation this covers basic DASM launch/exit only.

BLOCKED (TED 002 normal launch in default ADM3A session): B:TED reports
TED requires SCRN 1.1, 80x24; select ANSI with M4SCRN/ANSISCRN.
Screenshot 3.30.57 PM, libfile_e94be5f7021081919ab5e6c4bc09bae5.
M4SCRN was loaded, but default ADM3A personality conflicts with TED's documented
ANSI requirement. No editor launch/exit PASS. Retest with ANSI pending.

PASS (TED 002 launch with required personality): after A:RSX UNLOAD ADM3A
and A:RSX LOAD ANSI, TED reaches TED>. Screenshot 3.34.17 PM,
libfile_0eea7cc7fd94819195d2647b89d8a5eb. Earlier ADM3A rejection remains
historical prerequisite evidence. Exit and screen editing are not yet passed.

PASS (TED 002 exit, maintainer reported): EX at TED> returns to B0>.
Combined with the ANSI-session launch above, basic launch/exit passes.
Screen editing, saved-file integrity and broader functional checks are not
inferred from this empty-session check.

Checksum run observed: CRCKSUM 006 and MD5SUM 002 calculate A:STARTUP.SUB,
1 record, 1 file each. Screenshot 3.37.47 PM,
libfile_f2e7d4325bf48191a0408008a41f7330. Independent host reference extracted
with cpmcp from build/review-systems-v5/trs80gp/system.raw using its diskdefs:
cpmcp exports 53 logical bytes; zero-fill to one 128-byte stored record
(as shown by the prior DUMP and candidate packaging). CRCK 73B2, CRCKS E958, CHEK 143C, CRC32 2A5741FF,
SUM8 3B, SUM16 0C3B, KERM6 3B, KERM12 C3B;
MD5 35766c8f12f4e49cd793173edc257665. Screenshot text extraction is ambiguous
for some digits; exact visual/transcribed equality remains to be confirmed
before a complete all-algorithm reference PASS is asserted.

PASS (small stored-record checksum references): maintainer confirms all eight
CRCKSUM values and the MD5 digest above match the Model 4 display exactly.
This resolves the digit-reading uncertainty for this fixture. Covers default
algorithm calculation on one 128-byte STARTUP.SUB record only; lists, prompts,
large files and other outstanding checksum assertions remain pending.

PASS (CRCKSUM 006 order/duplicate behavior only): /SUM16 /CRCK /SUM16
/KERM6 /40 shows SUM16 0C3B, CRCK 73B2, KERM6 3B in that order, once each.
Screenshot 3.42.16 PM, libfile_e0bb9cbf746881919224f823de1c28b0.
OPEN presentation correction approved by maintainer: /40 should retain columns,
wrap excess checksum columns onto aligned continuation rows, rather than stack
one labeled value per line. Saved list format remains unchanged. Implementation
and affected revision/retest are pending; current presentation is not accepted.

PASS (CRCKSUM 006 local list generation and verification, one fixture):
A:PIP D:STARTUP.SUB=A:STARTUP.SUB, then B:CRCKSUM D:STARTUP.SUB
/LOCAL=CRC.LST and B:CRCKSUM D:STARTUP.SUB /CHECK=CRC.LST.
One file calculated, one list written; D0:CRC.LST verification reports MATCH
for all eight algorithms and one file verified. Screenshot 3.49.42 PM,
libfile_27a316ffc4ac8191b5a5c76343a87127. No broader list/error/prompt or
media-preservation PASS is inferred.

OPEN CRCKSUM verification-report correction approved by maintainer:
successful verification should read `STARTUP.SUB: MATCH (all 8 checksums)`.
The number must reflect the checksum columns actually present in the checked
list (for example, three columns produce `MATCH (all 3 checksums)`), not the
eight algorithms supported by CRCKSUM. Preserve the saved list format.
Implementation, affected revision, regression checks and Model 4 revalidation
remain pending; the existing CRCKSUM 006 results above do not validate this
future change. MD5SUM requires no corresponding report change because it uses
one algorithm; the maintainer explicitly leaves MD5SUM unchanged.

OPEN DIR.COM presentation correction approved by maintainer: move free-space
reporting from the separate trailing per-drive block into each DU's report.
Retain the existing separate DU heading above each listing (for example,
`A0:`). The maintainer considered and rejected moving the DU into the footer
or prefixing every file row. Right-align the numeric file sizes within their
existing fixed-width size fields, so the K suffixes line up (for example,
`ADM3A    RSX   2K : ADMTST   COM  12K`). Move padding before the number
instead of after the K; retain the file-column positions and row width.
Retain ` : ` as the column delimiter, consistent with resident DIR.
For populated listings use `---- 30 FILES, 184K TOTAL, 146K FREE ----`;
the maintainer approved inline four-hyphen separators with one space on each
side of the totals text, preserving a screen row instead of adding a separate
horizontal-rule line. For an empty
listing retain `NO FILE` followed by the free-space line. Repeat the drive's
shared free-space value for each selected user area, including user ranges;
no additional `ON DRIVE` qualifier or explanatory text is wanted. Remove the
redundant trailing free-space block. This is an output-placement correction;
free-space calculation is unchanged. Implementation, affected revision,
regression checks and applicable platform revalidation remain pending.

PASS (MD5SUM 002 local list generation and verification, one fixture):
B:MD5SUM D:STARTUP.SUB /LOCAL=MD5.LST, then
B:MD5SUM D:STARTUP.SUB /CHECK=MD5.LST. Screenshot 8.17.15 PM,
libfile_f8a677e4c4988191822e70401eeb7e36, reports one file calculated,
one list written, reference D0:MD5.LST, STARTUP.SUB MATCH and one verified.
This records successful local-list round trip only; no new precise digest
transcription or broader error/prompt/media-preservation PASS is inferred.

PASS (MD5SUM 002 changed-content rejection, one fixture): after
A:PIP D:STARTUP.SUB=A:README.TXT, verification against D0:MD5.LST reports
recorded and actual digests, STARTUP.SUB MD5 MISMATCH, and
`No files verified; 1 failed; incomplete.` Screenshot 8.22.06 PM,
libfile_d1946c1bd300819189ab75668db27d0e. The final command copies
A:STARTUP.SUB back to D:STARTUP.SUB and returns to the prompt without a
visible error; restored-byte verification remains pending. Exact actual-digest
transcription is not inferred from OCR.

PASS (restored fixture verification): screenshot 9.33.22 PM,
libfile_de532c192f6881918be60cc84edeafbf, shows a further PIP copy from
A:STARTUP.SUB to D:, followed by MD5SUM 002 /CHECK=MD5.LST and CRCKSUM 006
/CHECK=CRC.LST for D:STARTUP.SUB. Both report MATCH and one verified.
This resolves the pending restored-content check for the fixture using both
saved lists; it does not establish whole-media preservation.

PASS (MD5SUM 002 missing reference handling): /CHECK=ABSENT.LST for
D:STARTUP.SUB reports no MD5 list found, no files verified, one DU/reference
error and incomplete. Screenshot 9.36.38 PM,
libfile_ba2c36a42894819195be5fdad93f9594.

FAIL (CRCKSUM 006 missing-reference diagnostic): the same missing-list check
reports reference D0:ABSENT.LST, `LIST ERROR, line 4294967295`, then
STARTUP.SUB FILE NOT LISTED and no files verified, one unlisted, one list error,
incomplete. Same screenshot. It does not falsely report a verification pass,
but the nonexistent list has no meaningful line number and the unlisted-file
report is misleading after reference-open failure. OPEN stabilization fix:
report the missing/unreadable reference clearly without a bogus line number or
cascading FILE NOT LISTED diagnosis; affected revision/regression and Model 4
revalidation remain pending.

PASS (MD5SUM 002 overwrite prompt/default acceptance, maintainer report):
repeating B:MD5SUM D:STARTUP.SUB /LOCAL=MD5.LST prompted for overwrite;
the maintainer pressed Enter and the program wrote the file. No screenshot
was captured. This agrees with the documented `(Y/n/a/?)` default Yes.
Records prompt appearance and default acceptance only; explicit No, All,
help, cancellation and post-operation list verification remain pending.

PASS (MD5SUM 002 overwrite prompt help): screenshot 9.41.37 PM,
libfile_a97928bea2988191932988075fe793a2, shows /LOCAL=MD5.LST encountering
existing D0:MD5.LST, accepting ?, displaying `Y Yes, N No, A All, ? Help`,
and repeating the same destination's overwrite question. The screenshot ends
at that repeated prompt; No-response outcome and file preservation are not
yet established.

PASS (MD5SUM 002 explicit No response): screenshot 9.42.14 PM,
libfile_3a11219bb30481919f4a4e4f27f4b428, continues the help/repeated prompt
with N and reports one file calculated, one list declined. The requested
subsequent /CHECK=MD5.LST command is not shown; retained-list verification
and byte-for-byte preservation remain pending.

PASS (MD5SUM 002 retained-list usability after No): screenshot 9.43.38 PM,
libfile_43dfd86c9ec8819198eedeb46ba4cc22, shows D:STARTUP.SUB
/CHECK=MD5.LST resolving D0:MD5.LST and reporting MATCH, one verified.
The declined list remains usable and matches the fixture; this is not an
independent byte-for-byte before/after comparison of the list.

PASS (MD5SUM 002 overwrite-prompt cancellation and retained-list usability):
following the instructed Ctrl-C at the existing MD5.LST overwrite prompt,
screenshot 9.46.38 PM, libfile_e3cdfcb8482081918e520d0861e4c38c, shows return
to the command prompt and subsequent /CHECK=MD5.LST reporting MATCH and
one verified. The control character itself is not echoed in the screenshot.
No byte-for-byte list or temporary-file cleanup comparison is inferred.

PASS (CRCKSUM 006 overwrite help, No and retained-list usability): screenshot
9.48.55 PM, libfile_ffb42dd78450819184b8afc8162d8168, shows existing
D0:CRC.LST, ? displaying Y/N/A/help choices and repeating the same prompt,
then N yielding one file calculated and one list declined. Subsequent
D:STARTUP.SUB /CHECK=CRC.LST reports MATCH and one verified. No independent
byte-for-byte list preservation or whole-media comparison is inferred.

PASS (CRCKSUM 006 overwrite-prompt cancellation and retained-list usability):
following instructed Ctrl-C, screenshot 10.05.40 PM,
libfile_f7eb3b0526308191b0b2d75c4f402b20, shows return from the existing
CRC.LST overwrite prompt to CP/M. An initial mistyped verification command
is rejected with ?, then the corrected D:STARTUP.SUB /CHECK=CRC.LST reports
MATCH and one verified. The control character is not echoed. This does not
establish byte-for-byte list preservation or temporary-file cleanup.

PASS (MD5SUM 002 /40 console layout, one fixture): screenshot 10.13.19 PM,
libfile_874dde4881ec8191b45b35d660271678, shows D:STARTUP.SUB /40 with
STARTUP.SUB on its own line, the digest on the next line, and one file
calculated. The digest is presented as a single line; no precise new digest
transcription or actual 40-column terminal-mode validation is inferred.

PASS (CRCKSUM 006 changed-size rejection and restored verification):
screenshot 10.28.52 PM, libfile_5f381840cda88191baea3accf3630629, shows
README.TXT copied over D:STARTUP.SUB; /CHECK=CRC.LST reports candidate at
line 4, expected one record versus actual 28 records, SIZE MISMATCH, no files
verified, one failed, incomplete. The subsequent restore copy returns to CP/M.
Screenshot 10.30.03 PM, libfile_626895fcba208191952a11e595047235, then
shows MATCH and one verified against CRC.LST. This covers size-change
rejection; equal-length changed-content checksum mismatch remains untested.

PASS (CRCKSUM 006 default overwrite acceptance): screenshot 10.32.55 PM,
libfile_9af7bc0861fc81918ed53370106248e2, shows existing D0:CRC.LST,
the overwrite prompt with no printable response following the instructed
Enter, then one file calculated and one list written. This covers default Yes
acceptance; All across multiple destinations remains pending.

PASS (CRCKSUM 006 selected-algorithm local list, three columns): screenshot
10.35.26 PM, libfile_291cbdf6268081919dd4127670cab215, shows
D:STARTUP.SUB /CRCK /SUM16 /KERM6 /LOCAL=THREE.LST producing those three
checksum columns in selection order, one file calculated and one list written.
/CHECK=THREE.LST resolves D0:THREE.LST and reports MATCH CRCK SUM16 KERM6,
one verified. This is baseline evidence for subset-list verification; the
approved future `MATCH (all 3 checksums)` wording is not yet implemented.

## Stabilization implementation after this manual session

The findings above remain historical results for the mounted candidate binaries.
The following replacements are implemented locally, not yet packaged or tested
in Model 4. Earlier OPEN entries now have implementations awaiting platform
revalidation; their original evidence is preserved.

- CRCKSUM 1.0 revision 007: /40 wraps the native table into aligned groups,
  retaining filename/record count on the first row and leaving saved lists
  unchanged. Successful verification uses the dotted filename and
  `: MATCH (all N checksums)`, counting the matching entry's checked checksum
  mask. Missing/unopenable references report `Cannot open reference list`, a
  DU/reference error and incomplete, without stale line numbers or cascading
  FILE NOT LISTED after the initial open failure. Help and manuals updated.
- DIR 1.0 revision 010: retains DU headings and ` : ` delimiters, right-aligns
  file sizes within each DU's measured columns, and reports
  `---- N FILES, nK TOTAL, nK FREE ----` (singular FILE where appropriate).
  Free space appears for every DU, including empty listings, and the trailing
  once-per-drive block is removed. Alternate S/E file-size units retain K free.
- RSX 1.0 revision 006: a newline separates the last enumerated service from
  `TPA available`. A dispatch branch was widened to accommodate the code growth.
- COMPARE revision 003 remains the previously implemented HELP-precedence fix.
- MD5SUM behavior and expanded assembly source remain unchanged. Its builder
  excludes the CRC-only additions from shared source; comparison with the
  pre-fix expanded assembly was exact. No MD5SUM revision advance.

Replacement binary identities (SHA-256):

| Component | Bytes | SHA-256 |
| --- | ---: | --- |
| CRCKSUM 007 | 22279 | 94ab2baca93dc49da201cc5743f6dc30c17030b99b9cce7e6350f1dc2daf9170 |
| DIR 010 | 9798 | bb2394fcdb0329b7f39c2bbe945564882f3602a2c4e988a9b005baefe73aaef9 |
| RSX 006 | 1012 | 1aaa034df6f87824e5c49002266e7d595dc6d86d42380b6fe9bd4cf6ce4f7918 |
| COMPARE 003 | 6658 | 8388454c4a5affbf6dccb2e8e75bf16fa17a22d1481251e22e3dd42a12b4ada4 |

Affected verification:

- `tools/test_crc.py`: compiled command/routine suite PASS, including subset
  counts, default and ordered /40 table output, unchanged saved-list bytes,
  missing reference and failed-open diagnostics, plus existing regressions.
- `tools/build_native_crc.py`: 22279-byte cross/native parity and native CP/M
  command fixtures PASS using the final help text.
- `tools/test_release_presentation.py`: compiled DIR output across K/S/E,
  attributes, users 0/12, populated/empty DUs, aligned numeric cells and inline
  free space PASS; RSX LIST zero/one/two-entry newline checks PASS.
- Existing DIR column-fit, metrics and sort checks PASS. Native RCP-derived
  builder confirms DIR's 9798-byte cross/native parity.
- Broader `tools/test_utility_versions.py` stopped on an unrelated stale STAT
  /VER binary (`BetterCP/M STAT 1.0 (Build 002)`); no whole-suite pass claimed.
- The older `tools/build_native_rsx.py` first lacked its default inputs; after
  supplying the available paths/building prerequisite carriers, cpmsim could
  not execute cpmrecv and interrupted the harness. No native RSX parity or
  runtime platform pass claimed from that attempt. No trs80gp launch attempted.

Before acceptance: package a new candidate tied to the implementation commit,
then manually retest changed CRCKSUM/DIR/RSX/COMPARE binaries against their exact
versions and image identities. No NOAH runtime result has yet been recorded.

## 30 October: candidate identity correction

Screenshots 7.25.41 AM (libfile_8846a20560cc8191837f4397286a1a69) and
7.26.05 AM (libfile_a69d3aff4fb48191832111b1692b8f7f), repeated after explicit
remount/reboot at 7.47.19 AM (libfile_024894ec0b9481918e63bda5b9c8d641) and
7.47.40 AM (libfile_907a541b85408191920a281f85d31475), display DIR 009-dev,
RSX 005-dev, CRCKSUM 006-dev and COMPARE 002-dev.

Investigation established that candidate e01592c contains the stabilization
code but stale identification banners. The fixes advanced the legacy TSV,
while authoritative metadata/component-registry.json retained the earlier
revisions. The previous implementation section's revision labels describe
intended revisions, not the banners actually emitted by those recorded hashes.
Those hashes and observations remain historical evidence. Do not infer older
code, wrong user mount paths, or a runtime stabilization failure solely from
these stale banners. Earlier advice attributing this to mounting was incorrect.

Correct the authoritative utility revisions to DIR 010, RSX 006, CRCKSUM 007
and COMPARE 003; regenerate/check all projections and rebuild. Add executed
/VER checks for these four binaries to the focused presentation regression.
The corrected banners pass their compiled-code query paths. Previous image
identity is superseded for further manual validation once a corrected candidate
is provided; all affected Model 4 revalidation remains pending.

## 30 October: corrected candidate loaded; empty DIR presentation update

Screenshots 8.14.07 AM (libfile_1317af565f548191be2d6446df070b03) and
8.14.28 AM (libfile_fbb5bf4884148191b60ab71b50e9b626) confirm DIR 010-dev,
RSX 006-dev, CRCKSUM 007-dev and COMPARE 003-dev after the maintainer replaced
the extracted packages and restarted/remounted in trs80gp. These are the
expected identities for replacement candidate bfe45564609ae41d30d5abad696114442e0a2d22.
This confirms version queries only, not full runtime qualification.

Pending DIR.COM stabilization update (maintainer-approved): an empty DU must
place NO FILE on the DU heading line and frame its free-space footer:

```text
D0: NO FILE
---- 796K FREE ----
```

The maintainer reports the current output as `D0:`, a blank line, `NO FILE`,
then `796K FREE`. The approved layout saves **two screen rows**. Free-space
values remain dynamic. Implementation and affected regression/Model 4
presentation revalidation remain pending; do not mark this revised format passed.

### Corrected-candidate presentation retests

- DIR 010-dev: maintainer confirms right-justified file sizes and free space
  in the populated-DU combined footer. PASS for these presentation checks only.
  The approved empty-DU layout above remains pending.
- RSX 006-dev: maintainer confirms `A:RSX LIST` puts TPA available on its own
  line below the loaded RSXs. PASS for the line-break check, by maintainer
  report. Screenshot 9.50.57 AM (libfile_b5e01a677ff48191bac9e5aafa26a549)
  also records RSX LIST; this is not COMPARE help evidence.
- COMPARE 003-dev: mixed `/VER /HELP /BOGUS` help-precedence retest requested;
  result not yet established.

PASS (COMPARE 003-dev help precedence): screenshot 9.52.21 AM,
libfile_8fc6edddb66481918b1f4f5c3f79a320, shows the exact command
`C:COMPARE /VER /HELP /BOGUS` displaying the COMPARE help screen, including
usage and options. This supersedes the pending status above for this specific
retest. The previous assistant response inspected the older RSX screenshot;
that was an evidence-selection error, not a missing maintainer test.

PASS (CRCKSUM 007-dev /40 wrapped table, one fixture): screenshot 9.56.41 AM,
libfile_5a3715b83ee48191b208b9d7a2602976, shows
`B:CRCKSUM A:STARTUP.SUB /40`. Headings, separator groups and values wrap
under the first checksum column; filename and record count appear once.
One record, one file calculated. Visible values match the historical fixture:
CRCK 73B2, CRCK5 E958, CHEK 143C, CRC32 2A5741FF, SUM8 3B,
SUM16 0C3B, KERM6 3B, KERM12 C3B. This passes the specific narrow-table
presentation retest, not the remaining list/error cases.

CORRECTION — CRCKSUM 007-dev /40 presentation FAIL: the preceding PASS was
incorrect. Preserve it as historical assessment, superseded by this correction.
The maintainer identifies two defects: wrapped groups use different column
positions/widths, and output emits all headings, then all separators, then all
values. Required presentation is complete heading/separator/value blocks for
each group, with shared column positions across blocks and every line within
40 columns. Filename/record fields appear in the first block; subsequent
blocks align checksum columns beneath those of the first. The maintainer's
illustration expresses grouping intent but is explicitly too wide, not a
literal accepted 40-column layout. Implementation and runtime retest pending.
The newly pasted STARTUP.SUB values differ from the earlier screenshot;
do not apply the earlier fixture oracle to this paste without checking bytes.

LOCKED /40 presentation (maintainer approval): two checksum columns per block,
each eight characters wide, separated by two spaces, beginning at column 20
and column 30 (one-based). This gives a maximum line width of 37 characters.
Each block emits its own headings, separators and values; retain a blank line
between blocks. Filename, extension and record count appear in the first block
only. Later blocks indent to the same checksum column positions. Eight dashes
mark each checksum column. Preserve command-line algorithm selection and order:
group the selected algorithms in that order, two per block, rather than forcing
the example's default order. An odd final group contains one checksum column.
This specification is approved; implementation and qualification remain pending.

PASS (CRCKSUM 007-dev eight-checksum MATCH wording): screenshot 10.25.19 AM,
libfile_67e8a47cbf6881918194556ab2bc4a32, records PIP copying STARTUP.SUB
from A: to D:, `/LOCAL=CRC.LST` reporting one file calculated and one list
written, then `/CHECK=CRC.LST` resolving D0:CRC.LST and reporting
`STARTUP.SUB: MATCH (all 8 checksums)` and `1 verified.` The count for a
selected subset remains to be retested on this revision.

PASS (CRCKSUM 007-dev selected-list checksum count): screenshot 10.29.31 AM,
libfile_6ee8a008f5bc8191bb29beb83ae1a019, shows D:STARTUP.SUB with
`/CRCK /SUM16 /KERM6 /LOCAL=THREE.LST`, one file calculated and one list
written. `/CHECK=THREE.LST` resolves D0:THREE.LST and reports
`STARTUP.SUB: MATCH (all 3 checksums)` and `1 verified.` Together with the
preceding eight-checksum case, this passes the tested dynamic-count wording.

PASS (CRCKSUM 007-dev missing explicit reference list): screenshot 10.33.17 AM,
libfile_41bd341bae088191be532b7c3cd19e0b, shows the corrected command
`B:CRCKSUM D:STARTUP.SUB /CHECK=ABSENT.LST`, reference D0:ABSENT.LST,
`Cannot open reference list`, and
`No files verified; 1 DU/reference error; incomplete.` No bogus line number
or cascading FILE NOT LISTED diagnostic appears. An earlier mistyped command
is rejected as invalid and is not the reference-open test result.

PASS (NOAH 019-dev, candidate bfe4556, single-member LBR smoke checks):
- 10.37.25 AM, libfile_0144dfcfa3d0819197871b9e22308ebf:
  from C0:, `/ADD D:TEST.LBR D:STARTUP.SUB` creates the LBR, reports
  verified/published, one completed source, zero failed, outcome success.
- 10.38.03 AM, libfile_8ef8a6be0910819197685b2e2bec8d08:
  `/LIST D:TEST.LBR` lists STARTUP.SUB as 00000080 hex bytes (128), one
  member, outcome success; explicitly does not claim contents/CRCs tested.
- 10.38.39 AM, libfile_e8fb7b4611d481919bc487161f7fb11c:
  `/TEST D:TEST.LBR` reports STARTUP.SUB CRC verified, two known CRC regions
  verified, zero unavailable/ambiguous, outcome success.
All three screenshots visually inspected. Extraction and byte roundtrip,
ARK/compression, remove/compact and failure-path coverage remain pending.

### Pending NOAH presentation stabilization — approved first attempt

The maintainer accepts the ADD/LIST/TEST functional results but rejects the
cluttered normal output. Approved first revision: decimal user-facing counts
and sizes, concise per-file results and one operation summary. Remove normal
success-path internal bookkeeping (hex counters, accepted-source/candidate
counts, repeated disposition/outcome totals and zero recovery-artifact counts).
Proposed normal output, approved as a first attempt for review:

```text
Added STARTUP.SUB to D0:TEST.LBR
1 file added.
```

```text
Archive D0:TEST.LBR
NAME         BYTES
STARTUP.SUB     128
1 file listed.
```

```text
STARTUP.SUB: CRC OK
1 file verified.
```

Retain explicit errors, incomplete verification/CRC coverage limitations,
skipped/failed operations, and actionable nonzero recovery-artifact information.
LIST must not imply integrity verification. Preserve the functional passes
above. Implementation, output review and affected regression/runtime retests
remain pending; no new option or diagnostic-mode feature is implied.

PASS (NOAH 019-dev LBR extraction to another user area): screenshots
10.45.38 AM (libfile_19e3ffcccef48191a52fa20c2c114477) and
10.46.07 AM (libfile_a3684d7a147c819181fa6e3c64fd1a01) show
D1:STARTUP.SUB extracted and verified, outcome success, followed by DIR D1:
listing STARTUP.SUB. This establishes extraction and destination user-area
placement. Independent CRCKSUM comparison against D0:CRC.LST is not shown
and remains pending; do not infer it from NOAH's internal CRC verification.

Validation instruction correction: screenshot 10.54.34 AM,
libfile_81d6f75f1d7c8191b7c8bb44b76859a5, shows cpmsim and trs80gp rejecting
`B:CRCKSUM D1:STARTUP.SUB /CHECK=D0:CRC.LST` as invalid. The assistant supplied
unsupported syntax: /CHECK accepts a filename only, resolved in the target DU;
a DU qualifier is explicitly rejected by the documented contract and regression
suite. This is expected parser behavior, not evidence of a platform or NOAH
extraction defect. Independent extraction verification remains pending: copy
D0:CRC.LST to D1:CRC.LST, then check D1:STARTUP.SUB with /CHECK=CRC.LST.

PASS (NOAH extraction independently checked with CRCKSUM 007-dev): screenshot
11.08.03 AM, libfile_0183767a1058819192ed5714a2823f46, shows COPY moving
D0:CRC.LST to D1:CRC.LST, then
`B:CRCKSUM D1:STARTUP.SUB /CHECK=CRC.LST`, reference D1:CRC.LST,
`STARTUP.SUB: MATCH (all 8 checksums)` and `1 verified.` This completes the
single-member LBR ADD/LIST/TEST/EXTRACT checksum roundtrip on Model 4. The
screenshot does not independently establish a successful cpmsim roundtrip.

PASS (NOAH 019-dev single-member uncompressed ARK creation/integrity):
screenshot 11.11.42 AM, libfile_25b96ed1b9008191a09075d05348ae9b,
shows ARC update verified and published, one completed candidate and outcome
success, followed by `/TEST D:TEST.ARK` listing STARTUP.SUB, CRC verified,
and outcome success. ADD command itself is above the visible crop; command
context is the requested `/ADD D:TEST.ARK D:STARTUP.SUB`. Compressed ARK
and independent extraction roundtrip are not established by this result.

PASS (NOAH 019-dev explicit /SQ ARK creation, one tiny fixture): screenshot
11.15.38 AM, libfile_9a29917176288191a01e200541c54400, shows
`NOAH /ADD /SQ D:SQUEEZE.ARK D:STARTUP.SUB`, warns explicit compression
increased stored size, then reports ARC update verified/published and outcome
success. The requested separate `/TEST D:SQUEEZE.ARK` is not visible;
its result remains pending. Size increase alone is not a defect for this small
fixture with explicitly requested compression.

PASS (NOAH 019-dev squeezed ARK integrity): screenshot 11.16.42 AM,
libfile_dc4c14e521a4819180f44d60e4e0d24c, shows
`NOAH /TEST D:SQUEEZE.ARK`, STARTUP.SUB CRC verified, outcome success.
Maintainer also confirms the test passed. Presentation remains rejected:
apply the approved concise NOAH output revision to compressed ARK operations
as well as LBR and uncompressed ARK. Retain actionable compression-size
warnings, errors and integrity limitations. Functional success does not close
the pending presentation fix or establish an extraction roundtrip for this ARK.

PASS (NOAH 019-dev squeezed ARK extraction to D2:): screenshot 11.27.09 AM,
libfile_8fda892a2f6881919a29135a4a8ed79a, shows
`NOAH /EXTRACT D:SQUEEZE.ARK D2:`, D2:STARTUP.SUB extracted and verified,
and outcome success. Independent CRCKSUM verification is not visible and
remains pending; normal-output cleanup remains pending as already approved.

PASS (NOAH 019-dev squeezed ARK extraction independently checked): screenshots
11.29.57 AM (libfile_81c5bac6a2108191a55d96a5f672b3c5) and
12.30.00 PM (libfile_31edfdfbf8e881918a8e9f2a40d1e01b) show the reference
copied into D2:, followed by CRCKSUM 007-dev checking D2:STARTUP.SUB against
D2:CRC.LST and reporting MATCH (all 8 checksums), 1 verified. The later image
also shows COPY's existing-destination help/re-prompt and overwrite, and an
initial mistyped checksum command rejected before the corrected command passes.
This completes the tested single-member squeezed ARK roundtrip. Presentation
cleanup and other NOAH operation/format coverage remain pending.

Pending COPY.COM stabilization: maintainer clarifies the main `/HELP` screen
needs updating, not merely overwrite-prompt `?` help. Reconcile it with the
implemented options /O, /S, /B, /V, /BACKUP and /HELP, /VER query conventions,
and the agreed Utilities help presentation. No new command-line options are
requested. Source of supported operational flags: src/cpx/copy-options.inc;
reference: users_guide.md COPY.COM Options.

PASS (NOAH 019-dev crunched ARK creation/integrity smoke check): screenshot
12.38.24 PM, libfile_3238f3ae833081918e2d034f7e185ba4, shows ARC update
verified/published and outcome success, followed by `/TEST D:CRUNCH.ARK`,
STARTUP.SUB CRC verified and outcome success. The ADD command line is cropped;
context is the requested `/ADD /CR D:CRUNCH.ARK D:STARTUP.SUB`. Independent
extraction/checksum roundtrip remains pending.

COPY help evidence: screenshot 12.31.59 PM,
libfile_6bd5888e0bbc819181b8c9d998ef59d2, shows `:COPY /HELP` printing only
the terse COPY syntax with /O, /S, /B and /V. This supports the pending main
help-screen consistency update, including documenting /BACKUP and query options.

### NOAH option aliases proposed during manual validation

The normal-output cleanup is already recorded above as an approved pending
NOAH presentation stabilization fix; it is not implemented yet.
Maintainer requests these additional NOAH synonyms, retaining existing names:
/L for /LIST, /A for /ADD, /QUIET for /Q, /H for /HELP, and /V for /VER.
Retain existing /T and /X aliases, all other option meanings and existing
ambiguity/protection rules. Reconcile parser, help and manual; affected query
precedence and alias checks plus changed-binary runtime validation are needed.
Do not silently apply /V as version system-wide: COPY already uses /V for
read-back verification. A universal alias policy is not yet resolved; /VER
remains the unambiguous version spelling. No repository-wide alias rollout
is authorized by this NOAH-specific proposal alone.

Alias decision superseding the /V proposal above: maintainer rejects inconsistent
/V-as-version behavior across utilities. Do not add NOAH /V as a /VER alias;
retain /VER for version queries and existing /V operational meanings (including
COPY verification). Reserve /H universally for help in BetterCP/M-owned command
interfaces, as an alias for /HELP. Audit existing /H uses before implementation
and surface any conflict rather than silently changing an established operation.
This is a pending consistency update, not a claim that /H already works across
the current candidate. Third-party commands retaining their historical syntax
are outside an automatic rewrite. NOAH /L, /A and /QUIET aliases remain pending.

Maintainer confirms pending task grouping:
- NOAH updates: approved concise output cleanup plus /L = /LIST,
  /A = /ADD, /QUIET = /Q and /H = /HELP. Retain /T and /X.
  Do not add /V as a version alias; /VER remains unchanged.
- Later utility-wide consistency task: add /H as /HELP alias to all
  BetterCP/M-owned utilities, after auditing conflicts, and update help/manuals
  with affected regression checks. Record for later execution; not an immediate
  expansion of this manual validation step or a claim of current support.

PASS (NOAH 019-dev crunched ARK extraction): screenshot 12.41.22 PM,
libfile_55bc094117e081918b0eca0869063878, shows D3:STARTUP.SUB extracted
and verified from D:CRUNCH.ARK, outcome success. Independent CRCKSUM result
is not visible and remains pending.

Maintainer directs: finish the NOAH manual checks, then push pending work,
then implement the marked stabilization updates. Preserve qualification scope
and repeat affected checks for changed binaries; do not merge on their behalf.

PASS (NOAH 019-dev crunched ARK extraction independently checked): screenshot
12.53.26 PM, libfile_9b40e8fc05e08191b99994ceb968506a, shows COPY of
D0:CRC.LST to D3:CRC.LST and CRCKSUM 007-dev checking D3:STARTUP.SUB against
D3:CRC.LST: MATCH (all 8 checksums), 1 verified. Completes the tested
single-member crunched ARK roundtrip; no broader format/fixture claim implied.

Screenshot 12.56.34 PM, libfile_e1cec01cdcd081919849b4a074f162b8, shows
`NOAH /LIST D:TEST.LBR` still listing STARTUP.SUB, outcome success, following
the requested declined-removal test. The removal prompt/decline itself is not
visible, so this records member presence only; decline response awaits maintainer
confirmation. Maintainer again flags verbose output: the approved NOAH cleanup
includes REMOVE/decline summaries and subsequent LIST output, not only ADD/TEST.

PASS (NOAH 019-dev declined LBR removal): maintainer explicitly confirms
 declining the `/REMOVE D:TEST.LBR STARTUP.SUB` confirmation. Combined with
12.56.34 PM screenshot showing STARTUP.SUB still listed, this closes the
pending decline confirmation above. Evidence combines maintainer report of
response with screenshot of subsequent member presence; no byte-identity claim.

NOAH 019-dev compaction observations: 12.59.32 PM screenshot
libfile_f52bfbc126908191bf051758425b8de4 shows `/COMPACT D:TEST.LBR`
rebuilding and reporting verified/published, outcome success. 1.00.29 PM
screenshot libfile_56137f5cfb448191aa22d8973a9088d1 shows subsequent LIST
still containing STARTUP.SUB. Thus compaction completes with an active member;
these images do not establish approved removal, empty-archive compaction or
post-compaction TEST. Do not label removal failed without evidence that its
confirmation was accepted. Request exact REMOVE command and Y response.

Additional NOAH 019-dev evidence:
- 1.01.59 PM, libfile_6cb4933723dc81918e2b177cde7628fc: post-compaction
  TEST verifies STARTUP.SUB CRC and reports success. This establishes integrity
  of the populated compacted LBR, not an empty archive.
- 1.11.15 PM, libfile_59f6afe7cd248191b417f9c46521eb7a: exact
  `/REMOVE D:TEST.LBR STARTUP.SUB`, listed member and explicit Y confirmation,
  LBR update verified/published and outcome success. PASS for approved removal
  execution; subsequent LIST must confirm member absence.

PASS (NOAH 019-dev approved LBR removal, member absence): 1.15.16 PM
screenshot libfile_69bbcc21c8e081919840836cec2b4bcd shows subsequent
`/LIST D:TEST.LBR` with no member rows and zero listed members. Combined
with the explicit Y/update evidence at 1.11.15 PM, removal is established.
An empty LIST currently emits warning/no-work and a generic warnings/skips/CRC
coverage message; include this misleading empty-list presentation in the
approved NOAH cleanup. Do not treat it as evidence of archive corruption.
Empty-archive COMPACT and TEST remain pending.

PASS (NOAH 019-dev empty LBR COMPACT and structural TEST): 1.22.08 PM
screenshot libfile_a2cd2d789050819193a8d0e7f0d7769a shows explicit Y to
COMPACT, verified/published update and success. 1.24.14 PM screenshot
libfile_07dbff3b60d88191b358a5c2832166da shows subsequent TEST checking
structure/readability with zero member rows, a verified known CRC region and
zero unavailable/ambiguous regions. Empty selection yields warning/no-work;
retain this as observed status, with its misleading generic warning text in
the pending presentation cleanup. No member payload was verified in this empty
archive; this closes only the empty-archive structural/compaction smoke check.

PASS (NOAH 019-dev repeated replacement help and N choice): screenshot
1.26.55 PM, libfile_9aaae6daef9c81918716628c4c6d2933, shows
`/EXTRACT D:TEST.ARK D1:`, two successive ? responses each displaying
Y/N/A/C/? help and returning to the same D1:STARTUP.SUB replacement prompt,
then N producing replacement declined/skipped, zero extracted and one skipped.
Post-decline file checksums have not yet been rechecked. Verbose outcome/skip
reporting remains within the approved presentation cleanup.

PASS (post-prompt destination integrity): 1.28.48 PM screenshot
libfile_4b16b24bd3108191bc99d34ca07cc6c8 shows CRCKSUM 007-dev checking
D1:STARTUP.SUB against D1:CRC.LST: MATCH (all 8 checksums), 1 verified.
This establishes retained file integrity after the observed repeated-help/N
sequence. The requested C cancellation prompt/result is not visible; cancellation
itself remains pending confirmation and must not be inferred from MATCH alone.

PASS (NOAH 019-dev replacement C cancellation): 1.30.56 PM screenshot
libfile_19316f6dcb7c81919bd972b9525565de shows `/EXTRACT D:TEST.ARK D1:`,
? help returning to the same D1:STARTUP.SUB prompt, then C and
`NOAH: Extraction cancelled.` with `Outcome: cancellation.` The earlier
1.28.48 PM checksum preceded this cancellation and must not be claimed as
post-cancellation integrity evidence. That final integrity check remains pending.

PASS (post-C-cancellation destination integrity): 1.32.30 PM screenshot
libfile_9fc3bd40e69c8191aab4b1d1b6e6acc2 shows CRCKSUM 007-dev checking
D1:STARTUP.SUB against D1:CRC.LST after the observed C cancellation:
MATCH (all 8 checksums), 1 verified. This closes the cancellation integrity
check without reusing the earlier pre-cancellation result.

## Reduced remaining manual acceptance scope — 2026-10-30

The maintainer cannot spend days on manual validation and directs that only a
few of the most important checks remain. The remaining manual campaign is:

1. PATCH: apply a small valid patch and independently verify output bytes.
2. PATCH: reject mismatched input and verify existing files are preserved.
3. DSYM: convert a valid matching sample and inspect generated symbols.
4. After stabilization fixes, boot the updated packaged images and inspect
   DIR's empty listing, CRCKSUM /40, NOAH output and COPY help.

No further NOAH checks are required on the current candidate for this reduced
campaign. Existing results remain limited to the specific operations, fixtures
and revisions recorded above. Unexecuted recovery, protection, large-file,
boundary and other original checklist assertions remain untested; they are not
converted to PASS. This scope decision supersedes the remaining manual workload,
not historical evidence or final artifact identity and packaging requirements.

Pending implementation remains DIR empty-DU presentation, CRCKSUM /40 grouped
tables, NOAH output cleanup and aliases, and COPY help. Utility-wide /H remains
a separately recorded later consistency task. These changes have not been
implemented or validated by this documentation update.

## Stabilization implementation — 2026-10-30

The five recorded correction groups are implemented in the source commit
containing [the stabilization record](Release-Stabilization-2026-10-30.md):
DIR 011, CRCKSUM 008, NOAH 020 (output and aliases), and COPY 009.
That record identifies exact local binary hashes, automated checks and limits.
Historical pending entries do not qualify these changed binaries on Model 4.
New packages and the agreed reduced manual acceptance checks remain pending.
Utility-wide /H remains deferred.
