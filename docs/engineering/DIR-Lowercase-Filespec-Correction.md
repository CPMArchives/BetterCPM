# Transient DIR lowercase filespec correction

The reported `:DIR *.COM` issue is specifically a lowercase operand defect:
`:DIR *.com` reports `NO FILE`, although matching uppercase CP/M directory
entries exist. `:DIR *.COM` and resident `DIR *.com` work. The original-case
transient command tail reaches DP_PARSE; its operand copy previously retained
lowercase letters when constructing the search FCB. A mixed-case extension
fails in the same way.

DIR now converts only ASCII a through z to uppercase while copying its operand
into the existing private DP_ARG buffer. The original command tail is unchanged.
Wildcards, punctuation, DU syntax and attribute predicates retain their grammar.
The correction also reaches DIR's WHEREIS path, which uses the same parsed
operand. Option recognition, sorting, output formatting, resident DIR and the
shared operand libraries are unchanged.

The correction adds **13 bytes** to the assigned DIR.COM: 11,635 to 11,648 bytes.
Its 2-KiB-block disk allocation stays 12 KiB. It adds no data buffer, resident
allocation or TPA reduction. DIR's component identity advances from 1.0 (014)
to **1.0 (015)**, independently of the v1.0.1 package version. Reference and
candidate builds at 014, the revision proposal, and the final 015 assignment
are preserved separately for both supported targets. The assigned final bytes
are identical on the two targets. Other component revisions and baselines are
not changed; whole-release build/display baseline reconciliation remains release
integration work, as noted in the earlier utility query review.

## Focused validation

`tools/test_dir_case.py` fails on the original program at `*.com` and passes on
the correction. It executes the compiled parser, checks uppercase FCB fields
for lowercase/mixed-case wildcard and exact names, DU/attribute syntax, ASCII
range boundaries and preserved punctuation, and verifies the input tail is
unchanged. Its full-command WHEREIS fixtures check matching and nonmatching
files. Existing DIR option (31 valid/40 invalid), malformed-filespec/entry-target,
and WHEREIS failure/recovery tests also pass.

`tools/qualify_dir_case.py` uses private copies of the released System media.
It installs reference and corrected DIR binaries plus controlled matching,
nonmatching and SYS fixtures, then executes thirteen cases. The reference
lowercase search must fail while its uppercase search succeeds. Corrected
uppercase, lowercase, mixed-case and qualified/option-bearing wildcard searches
must yield the same ordered filenames. Exact and question-mark searches,
WHEREIS, a genuine no-match, malformed input, resident DIR and a subsequent CCP
file read are also checked. Native captures must contain the exact command
spelling, so an accidentally uppercased injection cannot pass this test.

Both cpmsim and Model 4 campaigns pass, including an observed lowercase failure
in the reference binary on each platform. File hashes, reserved sectors, filesystem integrity and the
original release images are checked independently. The verification
mode can finish auditing existing guest captures without repeating the run;
this was used after correcting the host fsck argument order, not to bypass
any guest or filesystem assertion. Whole-image byte equality is not claimed:
the normal startup SUBMIT run leaves a deleted $$$.SUB slot and queue data in
free space (confirmed in the cpmsim difference); file content hashes, reserved
system bytes and filesystem consistency are the integrity criteria.

The [evidence directory](evidence/2026-11-06-dir-lowercase/) binds final payloads,
revision receipts, regression logs and emulator captures. Readable snapshots
normalize line endings and trim trailing whitespace; the capture archives
preserve the original bytes. The frozen 1.0 release
packages remain unchanged. This correction does not broaden the v1.0.1 scope.
