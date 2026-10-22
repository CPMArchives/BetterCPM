# ERA shared input qualification

2026-10-22 — ERA 1.0 Build 004

## Change and compatibility boundary

ERA's Y/N and R/S/A/? prompts now share the choice-only controller through
`common/erainput.inc`. Its existing console reader, echo/newline, help,
protection/admission, retry/skip/abort, reporting and unattended paths remain
application-owned. Invalid Y/N input retries silently; invalid recovery input
repeats the question. Enter/ESC remain invalid, while Ctrl-C cancels locally.
The adapter consumes no acknowledgment-only key and flushes no typeahead.

Each context initializes the shared pointer/count/default and context byte;
registers BC/DE/HL/IX are preserved by the adapter. There is no editor, word
module, text-field controller, formatting buffer or resident allocation.

## Size and safety correction

Final ERA is **7,897 bytes**, SHA-256
`2731fd8e6f98e5d8ce9203531e918dccba7e6ee451d9df529fc8f54e8e4873d7`.
Cross assembly and native ZSM4/LINK are byte-identical. Both use the same expanded
source. The native builder handles legacy/current local tool paths and puts
cpmsim's host helpers on its process PATH.

The binding is 280 bytes: 185 controller code, 83 adapter code, six choice bytes
and six state bytes. Replacing the old recovery print site removes six bytes,
for 274 bytes of migration growth. A separate eight-byte prompt correction
makes total growth 282 bytes over Build 003's 7,615. The existing 256-byte stack
remains; the bounded selection heap starts 282 bytes later. Heap overflow
refusal is still tested. Unloaded OS TPA is unchanged.

Native testing exposed a pre-existing exact-file display defect before the
shared controller was entered. Classification leaves E_CURRENT one past the
collected records; E_FIRST previously returned the selected record only in IX,
while E_FULL reloaded IX from that stale cursor. The question could therefore
show filler rather than the selected DU/name. E_FIRST now updates E_CURRENT
before returning. Erase selection was separately initialized; this correction
makes the approval display identify the actual target. The source comment and
an explicit ineligible-first/eligible-second rendering regression retain this
explanation.

## Compiled qualification

- 256 confirmation input cases compare the migrated routine with the retained
  legacy E_YN source, linked to unchanged production console helpers. Returned
  A/carry/zero flags, echo/newline, caller registers, stack and remaining input
  agree, including zero as a no-key poll and ESC/Enter retry behavior.
- 256 recovery cases cover valid/lowercase choices, help, invalid-key repaint,
  Ctrl-C cancellation, typeahead and register/stack preservation. Three sequential
  contexts prove Y/N -> recovery -> Y/N state reuse.
- One exact-target case skips a noneligible record, selects the next one and
  displays its correct B3:SECOND.DAT identity despite a stale one-past cursor.
- Six /VER identity/purity cases pass; unused editor/field symbols are absent.
- Existing pure admission, formatting, recovery, unattended failure, RO restore,
  heap-boundary and paging checks pass, as do eight destructive failure-injection,
  19 allocation-planner and 51 read-only raw-adapter cases.
- The bounded runner now implements existing ADD IX,DE so the new first-hit
  traversal regression can skip a record. Three wrap/carry/zero-preservation
  probes and all 17 existing BIOS-vector contracts pass. No production CPU or
  BIOS code was changed.

The legacy reference is stored with commit provenance in
`tools/fixtures/era-legacy-yn.inc`; tests do not rely on a moving HEAD or a full
Git history. Recovery-fault choices are compiled-code evidence, not a claim of
native disk-fault injection.

## Actual platform qualification

The final binary passes 18 cpmsim ordinary sessions, covering explicit protected
admission, matching OR branches, negation, unattended RO skipping, one RO prompt,
quiet confirmation, Ctrl-C, malformed inputs, multi-DU deduplication and per-file
choices. The separate destructive campaign passes exact zeroing/scrubbing,
multi-extent and shared-block handling, RO authorization, empty files, refusal,
cache refresh and a controlled same-invocation drive-RO setup.

Native Model 4 interaction passes correct single-file naming, invalid physical
CLEAR/ESC and Enter retention, N refusal followed by a fresh question for that
file, Y deletion, read-only N and Ctrl-C preservation, and normal CCP return.
All other file payloads, the RO attribute and system records are preserved;
independent filesystem checking passes. A separate native destructive campaign
passes zeroing unshared blocks, E5/zero directory scrubbing and preservation of
another user's shared data/metadata. Native screen captures and raw images are
retained.

Early fixtures had two issues: the ordinary cpmsim test asserted an obsolete
Build 002 literal, now read from utility-version metadata; the native script
could match an older question still in VRAM and send an answer during loading.
It now clears the screen between cases. The stale private run was stopped and
fresh final campaigns passed. Initial native-tool path/PATH failures were build
fixture issues, resolved without a utility or OS workaround.

This is focused qualification of a changed existing utility, not a new core-OS
or complete release-distribution acceptance run. ERA remains implemented; this
work shares its input machinery and corrects the approval identity display.
