# Step 9 — complete release workflows

Started 19 October 2026 after Step 8 closure (PR 408). This is original Step 9,
equivalent to stage 7 of the condensed campaign ledger. Validation remains
limited to the core OS and two completed System Disks; Utilities Disk and CP/M
Tools Disk qualification remains separate.

## Finite checklist

| ID | Workflow and completion evidence | Current status |
| --- | --- | --- |
| S9-01 | Continuous cpmsim boot/README/DIR/WHEREIS/ED/copy/rename/attributes/erase/SUBMIT/monitor-switching session; repeated command returns, second cold boot and saved-data/file/filesystem/system-track checks | PASS — V048 |
| S9-02 | Matching native Model 4 integrated session, actual keyboard editing, all three monitor personalities, repeated command returns and second cold boot with saved data; independent media/file checks | PASS — V049 |
| S9-03 | cpmsim CONFIG startup and disk-boot IOBYTE save, live value unchanged; named system-package export, confirmed install on populated media, complete filesystem preservation, installed cold boot and exact saved settings/data | PASS — V048 |
| S9-04 | Native CONFIG startup/IOBYTE save, named export and confirmed containing-disk installation, exact payload/expected binding patch, preserved files, installed cold boot and saved settings | PASS — V049 |

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

Closed 20 October 2026 with S9-01 through S9-04 PASS. V048 retains the two
cpmsim results; V049 retains the two native results, raw media/screens, executed
runners, independent audits and excluded attempts. Both durable archives were
reopened and all manifest file hashes verified. No production code changed.
Broader conformance accounting and final clean merged-source acceptance remain
open after this step.

## Resume — 20 October 2026

The two V048 native attempts were paused before a complete verdict and remain
excluded. A bounded replay of the ordinary workflow captured SUBMIT's
`Error On Line 003 Parameter Error`: its test script used an unescaped dollar
attribute marker. SUBMIT requires `$$` for a literal dollar. The V049 runner
escapes both STAT attribute markers and restarts on fresh disposable media.
This corrects the validation fixture; no production change is made.

A private read-only boot of the partially configured disk executes the saved
`VER /VER` startup. This diagnostic is not a substitute for the complete
configured export/install/cold-boot verdict.

The first corrected native attempt progressed through disk operations but did not
retain its transient TYPE capture. The new fixture explicitly holds each TYPE
display with a supplemental BDOS keyboard-read helper until capture and release.
The helper adds no file operations and all shipped programs remain unchanged.
The ungated attempt is excluded rather than accepted from partial media.

The CONFIG startup-save diagnostic also retains the full successful completion
message and returned prompt with the default monitors loaded. The first full
V049 configured workflow timed out while waiting for a message fragment; it is
excluded. The runner now gates on the complete message and retains a separate
save capture. The complete export/install workflow remains unqualified until
its independent checks finish.

The ready-gated file run independently preserved the expected ED edited file,
original backup, copied text and user-0 sentinel. Its later direct host commands
lost leading characters during recovery, observed in the live native window, so
it is not a pass. The revised fixture queues the ED launch and subsequent
monitor commands inside SUBMIT, keeping host keys only for ED and explicit
ready-message gates. Distinct complete CONFIG confirmation prompts also avoid
matching an earlier Y/N prompt still visible on screen. A shortened-settling
CONFIG diagnostic was excluded; the full runner retains its original intervals.

## V049 accepted native workflows — PASS

The accepted ordinary session is
`/private/tmp/bettercpm-v049-queued-native-workflow/applications-z26c52nx/result.json`.
It covers README through its last line, WHEREIS, transient/resident copies,
rename/type/erase, attribute changes, repeated returns, actual keyboard ED save,
backup preservation and all three personalities. SUBMIT dispatches the commands;
declared supplemental ready-message helpers hold the displays for capture.
Both providers unload to 53K. Independent checks require exactly the expected
five data files, unchanged user-0 sentinel and backup, no erased names, unchanged
system records and all 28 unmodified shipped files (STARTUP.SUB is the declared
first-session queue fixture). A second cold boot from a fresh original System
Disk reads NEWOLD from the saved disk and unloads to 53K; all 29 shipped files,
its system area and filesystem pass checks, and the entire saved data disk is
byte-identical after that read-only session.

The accepted configured session is
`/private/tmp/bettercpm-v049-captured-config-install/sysgen-bk042gat/result.json`.
Confirmed startup VER /VER and disk-boot IOBYTE 85 saves leave live IOBYTE at
95h. The named BASE090.SYS package contains exactly one header plus 160 payload
records; the payload equals the configured source. Confirmed containing-disk
installation preserves the entire exported filesystem byte-for-byte. Its sole
payload patch is the defined binding normalization at offset 7030 (E0h to A0h).
Retained raw export/install checkpoints permit independent comparison. Installed
cold boot executes VER /VER, the byte-0003h witness reports 55h, and an immediate
CONFIG /SHOW capture reports both live and saved decimal 85. The sentinel,
all 29 shipped source files and all 29 shipped destination files remain intact;
both filesystems pass independent checks. The prior delayed /SHOW capture had
scrolled the header away and is excluded; the complete fresh-media rerun passes
without removing that assertion.

The V049 archive retains 501 hash-verified files, including paused and excluded
attempts. The result index records its exact hash and both native result hashes.
Only the two named accepted native result files and their supplemental reviews
are workflow passes; diagnostic or partial runs are not promoted to passes.
