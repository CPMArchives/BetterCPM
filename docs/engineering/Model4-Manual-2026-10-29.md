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
