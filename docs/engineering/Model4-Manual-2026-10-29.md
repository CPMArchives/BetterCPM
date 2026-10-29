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
