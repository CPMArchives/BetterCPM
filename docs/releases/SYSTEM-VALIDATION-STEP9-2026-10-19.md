# Step 9 — complete release workflows

Started 19 October 2026 after Step 8 closure (PR 408). This is original Step 9,
equivalent to stage 7 of the condensed campaign ledger. Validation remains
limited to the core OS and two completed System Disks; Utilities Disk and CP/M
Tools Disk qualification remains separate.

## Finite checklist

| ID | Workflow and completion evidence | Current status |
| --- | --- | --- |
| S9-01 | Continuous cpmsim boot/README/DIR/WHEREIS/ED/copy/rename/attributes/erase/SUBMIT/monitor-switching session; repeated command returns, second cold boot and saved-data/file/filesystem/system-track checks | PASS — V048 |
| S9-02 | Matching native Model 4 integrated session, actual keyboard editing, all three monitor personalities, repeated command returns and second cold boot with saved data; independent media/file checks | RUNNING |
| S9-03 | cpmsim CONFIG startup and disk-boot IOBYTE save, live value unchanged; named system-package export, confirmed install on populated media, complete filesystem preservation, installed cold boot and exact saved settings/data | PASS — V048 |
| S9-04 | Native CONFIG startup/IOBYTE save, named export and confirmed containing-disk installation, exact payload/expected binding patch, preserved files, installed cold boot and saved settings | RUNNING |

Use private fresh copies of the qualified V044 distribution images. All shipped
programs/providers remain release binaries. Supplemental scripts/witnesses and
the native first-session STARTUP.SUB fixture are declared; they do not replace
utilities. This reuses the hash-identified runtime baseline, not the old V017
results. Final clean merged-source builds and acceptance remain Step 11.

The [V048 evidence index](SYSTEM-VALIDATION-STEP9-EVIDENCE-2026-10-19.json)
records accepted result hashes and a durable archive containing raw traces,
before/after media, helper sources, file/filesystem audits and excluded attempts.
The archive was reopened and each archived file verified against its hash.

## V048 accepted cpmsim workflows

### Continuous user session — PASS

`/private/tmp/bettercpm-v048-r3-cpmsim-workflow/result.json` records one complete
session, followed by a cold boot with the saved data disk. The session reads the
shipped README through its last line, lists and locates a user-7 file, edits it
with ED, copies/renames across users, sets and clears read-only through STAT,
verifies a backup with COPY, erases the selected source, and runs a SUBMIT file.
Two more copy/erase cycles check repeated transient returns. ADM3A, VT52 and ANSI
are loaded in turn over ANSISCRN and display the saved text. All providers unload
and restore 53K; BYE exits. The second cold boot starts with no RSXs, restores
53K and reads the saved backup.

Independent checks require the user-0 sentinel, user-7 edited text and original
backup, and user-9 copied text; temporary/final erased names must be absent.
All 30 shipped files and source system records remain unchanged, and both
filesystems pass independent checks.

The first two attempts are excluded: a partial prompt-prefix match permitted
input before the CCP finished checking its SUBMIT stream and initializing the
interactive editor. Captures show missing ERA/PIP command prefixes and the
strict file oracle rejects the leftover file. A short fixed delay did not fix
that incomplete handshake. The accepted runner instead waits for the complete
editor cursor (including each personality's cursor presentation), retains its
strict file checks, and passes on fresh media. No production change is made.

### Save, export, install and configured cold boot — PASS

`/private/tmp/bettercpm-v048-config-install/result.json` records a continuous
CONFIG/SYSGEN workflow: confirmed startup `VER /VER` save; confirmed disk-boot
IOBYTE 85 (55h) save; live IOBYTE stays 95h through both writes and warm returns.
SYSGEN exports `LIB090.SYS`, whose complete 160-record payload is independently
compared with the configured source. It then installs the named package onto a
populated destination after confirmation; the entire containing filesystem is
byte-identical to its preinstallation state, including a user-7 sentinel.

Cold boot of that installed image executes the saved VER command and initializes
IOBYTE to 55h, verified by an independently assembled byte-0003h witness.
CONFIG inspection and sentinel reading work afterward. That read-only installed
boot leaves its whole disk byte-identical. All original shipped source files,
package/destination/reboot filesystems and immutable baseline hashes pass audits.
No live IOBYTE change, raw package-as-boot-image assumption or unchecked message
is used as a substitute for the independent payload and cold-boot checks.

## Completion

Close Step 9 when S9-01 through S9-04 have retained passing workflow evidence
and no unresolved integration finding remains. Each native result is reviewed
only after its full screen/media/file audits finish. Preserve raw bundles outside
temporary storage and record exact hashes. Historical intermediate results and
excluded harness attempts are not promoted to passes. Broader conformance
accounting and final release acceptance remain open after this step.
