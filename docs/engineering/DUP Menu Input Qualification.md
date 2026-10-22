# DUP menu and drive input shared-library qualification

## Scope

DUP 1.0 Build 006 routes its main-menu and interactive drive selection through
the existing shared choice controller. The common CHOICE display remains
unchanged: bracketed answer field, optional inverse blank, cursor placement,
selected-byte echo and newline. Invalid menu input returns to the main menu;
invalid drive input returns FFh to the existing caller. Ctrl-C retains the
main-menu exit versus drive-selection return distinction.

`DP_MENU` and `DP_DRIVE` select the context; only expanded DUP's CHOICE reader
calls `DU_PICK`. The disk-common source remains unchanged for CONFIG/SYSGEN.
The binding retains every KEY-folded input byte, mapping unknown bytes to an
internal help member for controller dispatch and returning the original byte
to the caller. It does not add help, new defaults, silent retry, acknowledgment
or typeahead flushing. CR and ESC retain their existing caller behavior.

Every menu return restores the strict Y/N list/count/default and clears the
menu mode before FORMAT/COPY can ask permission. `DP_ASK` does not repair a
corrupted confirmation configuration: existing fail-closed/no-read checks remain
valid. Malformed menu lists return Ctrl-C rather than dispatching a stale choice.
The command-line ASKDRV path continues returning configured drives without
reading or displaying input; disk operations and cleanup are unchanged.

## Artifact and memory

- DUP 1.0 Build 006: 8,592 bytes, previously 8,483 (+109 transient bytes).
- SHA-256: `1ac470563dd48f22522fc9477f9359ea7162e816501356c773e5ecd6ba5f3018`.
- One shared controller is reused; no second controller or editor is linked.
- Additional state: mode and original-byte storage (two bytes), plus nine bytes
  of immutable choice lists. No input buffer or resident allocation.
- Existing 3E00h stack boundary, workspace and 51K TPA requirement unchanged.
- Native ZSM4/LINK output matches the cross build byte for byte.

`tools/build_dup.py` exposes the shared expanded source for an isolated DUP
build. The general disk-utility builder and native builder use that source;
qualifying DUP need not regenerate CONFIG's platform validation metadata.

## Compiled checks

`tools/test_dup_shared_menus.py` compares 1,024 menu/drive cases against a
retained pre-migration CHOICE fragment: all 256 first bytes, two contexts and
plain/inverse display modes. Zero is a no-key poll followed by B. Output bytes
and output service, returned selection, consumed/remaining input and stack
balance match. Drive result flags match too. BDOS clobbers general registers.

Seven sequential contexts reuse one controller instance across menu, drive,
invalid choice, cancellation and approval. Two malformed menu-list cases abort
without input and do not contaminate a later N approval. Three command-line
modes return both configured drives without any I/O.

The existing confirmation campaign passes all 255 nonzero answers, the three
malformed-configuration/no-read cases and six version/purity cases. DUP's parser,
direct dispatch and one-shot exit checks also pass. These confirm that generic
menu selection cannot turn a non-Y answer into destructive permission.

## Actual platform evidence

- Native Model 4: `/private/tmp/bcpm-dup-menu-native/result.json`. Thirteen VRAM
  captures cover invalid main-menu input, lower-case operation/drive selection,
  invalid drive return, drive Ctrl-C return, N and X refusal after drive selection,
  and main-menu Ctrl-C exit. Both physical disk images are byte-for-byte unchanged.
- cpmsim interactive: `/private/tmp/bcpm-dup-menu-cpmsim-final/result.json`
  passes invalid/valid menu and drive input, lower-case selection, Ctrl-C in both
  contexts, N/X refusal and normal return. Both disk images are unchanged.
- Existing cpmsim direct-operation campaign passes refused FORMAT/COPY, protected
  system-drive FORMAT refusal, approved raw COPY with exact payload equality,
  read-only CHECK and caller return. Its transcript is retained under
  `build/test-results/dup-command-line/`.

The first interactive cpmsim harness sent Ctrl-C when the drive heading appeared,
before the remainder of the cooked display finished; BDOS intercepted it during
output. The corrected harness waits for the complete choice field. This is a
harness synchronization correction, not a changed utility input contract.
