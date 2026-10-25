# NOAH safe source-preflight failures

Status: NOAH 1.0 revision 9, bounded failure-handling increment, 2026-10-25.
The [behavioral specification](NOAH%20Specification.md) remains normative.
This increment fixes unintended empty LBR creation and adds Retry/Skip/Abort at
confirmed safe source-preflight boundaries. It does not complete the general
failure interface or outcome reporting, and adds no archive format or browser.

## No accepted additions

A new ADD with selected sources but no accepted source no longer treats the
implicit initial directory allocation as a requested capacity change. With no
old archive and no explicit `/CAPACITY`, it leaves the archive absent and creates
no staging file, including when `/COMPACT` was also specified. Invalid capacity
still fails validation before the no-change shortcut. An explicit valid capacity
can remain an intentional change after candidate failures, as allowed by the
existing specification. Existing no-source/no-match/self-exclusion rules remain
unchanged; an empty selection never creates an archive merely for capacity.

Failed replacements preserve the old member or an earlier accepted same-name
version from this invocation. A candidate is not displaced until its new source
has passed preflight and the existing collision authorization.

## Safe choices

The shared immediate-choice controller offers:

```text
Retry/Skip/Abort? R/S/A [S]:
```

Choices are case-insensitive; Enter defaults to Skip. Abort, ESC and Ctrl-C
cancel the invocation and preserve already completed work. Invalid keys use the
existing choice validation. `/Q` retains the prompt and diagnostics. `/Y` skips
without waiting, with no automatic Retry loop. Repeated retries require explicit
user choices.

The implemented boundaries are deliberately limited:

| Boundary | Retry behavior | Skip / Abort |
| --- | --- | --- |
| Ordinary ADD source open/read preflight, with confirmed close | Reopen and rehash that candidate, using the same frozen identity and existing accepted plans | Skip omits this candidate without displacing an accepted version; Abort abandons the update |
| Standalone codec source preflight before staging | Restart name/size/header/hash/codec preflight from the same frozen source identity | Skip continues to the next frozen source; Abort leaves remaining sources unprocessed |
| Compressed ADD source preflight before its encoded stage | Same codec preflight restart, preserving earlier verified spool rows | Skip omits that candidate; Abort cleans or reports owned scratch state |

There is no Retry over an output stage, retained TMP, member-expansion spool,
live writer aggregate, or publication/rollback state. Aggregate integrity failure
during the writer phase abandons the update. Existing conservative handling of
other extraction/archive failures remains unchanged; this increment does not
claim to offer Retry at every potentially recoverable operation.

## Close certainty

The codec source-size/header probe now sets its input-ownership flag when open
succeeds and clears it only after confirmed close. Its failed close can therefore
be cleaned up without losing the handle state. Retry is considered only after
the input is confirmed closed and no output stage has existed.

If cleanup cannot confirm input close, NOAH reports the source identity and
`source close uncertain; batch stopped`. It stops the frozen batch, forbids
another codec call from resetting that ownership flag, and prevents compressed
ADD from advancing to another source. Ordinary ADD source-close errors continue
to abandon the update without a retry question. No uncertain close licenses
publication or loss of an original. This is not a filesystem locking or
power-loss atomicity claim.

## Qualification and bounds

`tools/test_noah_failures.py` runs 21 assembled-code transactions covering Retry,
default/explicit/quiet/unattended Skip, Abort/ESC/Ctrl-C, repeated failure,
no-empty-archive behavior, explicit/invalid capacity, original and earlier accepted
versions, compressed ADD, standalone codecs, staging failures and persistent
input-close failure. Existing adapter (137), writer (38), codec (51) and quiet
reporting (31) suites also pass. The shared harness adds a source-close-specific
fault injection so a genuine unconfirmed input can be distinguished from output
close failures.

`tools/qualify_noah_codecs.py --source-failures` builds all six native modules
with unmodified ZSM4/LINK on both platforms and checks complete native/cross and
companion parity. The runtime campaign, with terminal providers loaded, first
proves `/Y` returns from a failed preflight without waiting. Interactive Retry
then re-enters a recognized unsupported source, Skip continues to a valid next
source, and an independent output-byte check plus post-exit marker confirms
successful decoding and return to the caller. Physical I/O and close failures,
Abort and the empty-archive regression are fault-injected in assembled-code host
tests; they are not claimed as native disk-error injection.

The resident image is 17,744 bytes; the shared window is 4680h and codec context
4E80h. Controller code is 17,006 bytes; plans occupy 8900h–A100h and transformed
identities A100h–BB00h. The maximum required end BB00h remains below active
ceilings C501h (z80pack) and CA01h (Model 4) in the recorded loaded-provider
configurations. Source exports, measured layouts, native products, console traces
and filesystem receipts are retained in the [qualification receipt](NOAH-Safe-Source-Failures.json)
and [portable evidence](NOAH-Safe-Source-Failures-evidence.tar.gz).

Remaining work includes staged-operation failure choices where safety can be
established, complete outcome accounting, ARK handlers and final Utilities Disk
packaging. The interactive browser remains deferred.

The subsequent [revision 10 staged-failure increment](NOAH%20Staged%20Failures.md)
extends these choices to verified disposable-stage cleanup boundaries. The
revision 9 measurements and receipts remain historical.
