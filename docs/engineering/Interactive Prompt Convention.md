# BetterCP/M 1.0 interactive inline-help convention

Status: common UI convention proposed and recorded on 2026-10-10. This document
does not change existing executable behavior or introduce a general help service.

## Scope and behavior

For interactive prompts offering three or more abbreviated actions whose meanings
are not self-evident, include `?` as an inline-help action. It prints a concise
one-line explanation and immediately repeats the original prompt, including its
command/item context. Help must not mutate operation policy, counters, selected
items, retry state, or filesystem state. Repeated help requests remain harmless.
Use only choices that have defined semantics for that operation.

Future ERA failure recovery is the reference example:

```text
ERA TOM.DOC - Failed. R/S/A/? ?
R Retry, S Skip, A Abort all.
ERA TOM.DOC - Failed. R/S/A/?
```

R retries the current operation; S skips the current item; A aborts the entire
command. Apply this to ordinary and destructive ERA failures where interactive
recovery is possible. This records the intended ERA interface, not an implemented
recovery loop in today's basic ERA.

Do not add `?` to initial, per-file `/C`, or destructive Y/N confirmations,
read-only skip messages, or paging. Paging spells out its actual controls.
For example, a future implementation accepting both keys may say
`MORE -- Space/ENTER for next page.`; do not advertise ENTER before supporting it.

ERA `/Y` must follow its noninteractive failure policy without stopping for
R/S/A/?. `/Q` suppresses informational output; it does not answer prompts or
enable unattended execution. Each utility retains its own mode contract. COPY
`/B` is its explicit noninteractive mode; SUBMIT alone retains interactive COPY
semantics. A help request cannot override any of these policies.

This is not `COMMAND //`, command-line help, a shared resident service, or a
Z-System help architecture. A richer general help facility remains post-1.0.

## Retrofit audit

Audit covers current COPY.COM, STAT.COM, RCP DIR/ERA/TYPE/REN/COPY/MOVE, basic
transient ERA/TYPE/REN, and confirmation/input prompts in CONFIG, DUP and SYSGEN.
No production code was changed. Byte deltas below are exact string-length deltas
for the stated replacements; they are not measured rebuilt allocation changes.

| Prompt | Current and proposed behavior | One-line help | Code-size impact | Documentation/tests |
| --- | --- | --- | --- | --- |
| Transient COPY collision | Current `[Destination exists. Overwrite? Y/N/O/S/R/?]`; retain unchanged | Existing `Y - Yes  N - No  O - Overwrite All  S - Skip All  R - Rename` | 0 bytes | Already documented and qualified on z80pack and Model 4, including help/invalid-response reprompting and policy reset |
| Transient COPY verification | Current `[VERIFY ERROR] R/S/?`; retain unchanged as an established exception to the three-action guideline | Existing `R - Retry  S - Skip`; Ctrl-C abort remains separately documented | 0 bytes | Already documented and qualified, including help, skip, abort and retry; adding an A action would change the contract and is not proposed |
| RCP TYPE paging | Current `--More--`; candidate `MORE -- Space for next page; Ctrl-C abort.` | None; controls are printed directly | +34 string bytes in RCP and each generated fallback carrying that string; no new branch | Requires updating paging docs and output assertions; Space/Ctrl-C behavior stays unchanged |
| Standalone TYPE source paging | Current `--More--`; same candidate wording | None | +34 string bytes if this source is built; no new branch | Audit build selection before treating this source as the shipped TYPE.COM; same output/doc changes |
| Resident/basic transient ERA | Current `ALL (Y/N)?`; retain unchanged | None | 0 bytes | No existing multi-choice failure prompt to retrofit; future richer ERA owns R/S/A/? implementation and tests |
| COPY rename | Current `New Name:`; retain unchanged | None | 0 bytes | Free-form filename input, not an abbreviated action menu; invalid name/blank/Ctrl-C behavior remains as qualified |
| STAT | No interactive action menu | None | 0 bytes | STAT command-line syntax and diagnostics remain unchanged |
| Resident COPY/MOVE, DIR, REN | No multi-action interactive recovery menu | None | 0 bytes | Do not introduce new prompts merely for consistency |
| CONFIG/SYSGEN/DUP confirmations | Existing save/proceed/erase/format Y/N prompts; retain unchanged | None | 0 bytes | Numeric drive entry is also outside this convention; no retrofit needed |

COPY's existing help paths print help for unknown action keys as well as `?`.
That is compatible with the convention and should not be changed merely to
standardize wording. The convention does not require adding retry/skip/abort
recovery to current COPY read/write errors, which already have qualified cleanup
and continuation/stop policies.

## COPY prompt-context retrofit — 2026-10-10

The initial audit found existing help actions; a subsequent source review found
that their reprompts printed the choices without repeating the filename pair.
Collision help now returns to CTPROMPT rather than CTASK, with no byte growth.
Verification help calls CTPAIR before its existing reprompt, adding three bytes
to COPY.COM. The prompt strings, help strings, action choices, and operation
policies are unchanged. No BIOS, BDOS, CCP, or RCP allocation grows.

COPY.COM is now 10,306 bytes, SHA-256
`856f62904ace57feab13cccbc1587e4ca7103abacc3935e4b5f46667a5df93cd`.
The earlier frozen campaign remains evidence for its recorded 10,303-byte binary;
targeted prompt regression tests qualify this small subsequent change.
The z80pack interactive and verification-flow suites explicitly check that both
help and invalid-response paths repeat the correct filename pair. They also
retain copy-policy, data-preservation, cleanup and noninteractive checks.

Both z80pack suites passed. Model 4 interactive-choices, verify-skip and
verify-abort also passed, with saved screens independently checked for the
filename pair immediately after help. Evidence is preserved in
`/private/tmp/copy-help-bundle-20261010`; all 209 files passed manifest size/hash
verification. Manifest SHA-256:
`80888e7094e3e83e7d0c5cd9aa5c81d68674e7e86d05e0aae36245345ad29887`.

## Qualification requirements for future implementations

Check that `?` and repeated `?` print help and reprompt for the same item without
changing counts, policy, or media. Check R/S/A individually, invalid responses,
and the utility's established Ctrl-C behavior. Verify unattended modes never
prompt. Quiet-mode checks must follow each utility's documented interaction
policy. Simple Y/N and paging behavior must not acquire a help menu.
