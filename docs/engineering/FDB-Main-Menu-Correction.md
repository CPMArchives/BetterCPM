# FDB main-menu correction for 1.01

This change implements the main-menu presentation in Engineering Specification
209 §3: a component version heading, grouped bracketed command letters, and
`Your choice: [ ]`. It retains the existing E (resume editor) command and includes
Q in the selection hint. The command dispatcher, line-input convention, editor
operations, pending-change decisions, and exit-to-CCP implementation are unchanged.
This does not claim to fix the separately reported, unreproduced exit defect.

The heading is generated from the same component identity as the query interface:
FDB 1.01 (003). The matching FDBVIEW.OVL must accompany this FDB.COM. The viewer
compatibility token is regenerated normally; no additional runtime file is needed.

## Memory and implementation

The old resident image ended at 35C2h, only 62 bytes before the fixed IMPORTBUF at
3600h. The expanded literal menu cannot fit there without recovering space.
A deterministic build-time dictionary therefore encodes selected, zero-terminated
ASCII UI messages in the existing resident area. PUTS recognizes the tagged fixed
messages and expands plain ASCII dictionary words. Dynamic catalogue text,
file-format strings, editor geometry, and command keys keep their existing format.
The assembly source retains readable menu text.

| Measurement | Before | After |
| --- | ---: | ---: |
| FDB.COM | 21,281 bytes | 21,315 bytes |
| Resident IMAGEEND | 35C2h | 35E4h |
| IMPORTBUF boundary | 3600h | 3600h |
| EDITOREND | D3F7h | D3F7h |
| FDBVIEW.OVL | 4,736 bytes | 4,736 bytes |
| Private stack | 128 bytes | 128 bytes |
| Catalogue entries | 128 maximum | 128 maximum |
| Working/import catalogue buffers | 9,472 bytes each | 9,472 bytes each |
| Required TPA | 53K | 53K |

There is no extra resident system allocation or TPA reduction. The executable is
34 bytes larger; the resident layout retains 28 bytes before IMPORTBUF. The main
menu fits an 80-column, 24-row display, including the extra pending-editor line.

## Validation

`tools/test_fdb_menu.py` executes the assembled program on the full Z80 core.
It checks the clean and Untitled menus, Q/BREAK, pending-editor cancel, resume and
discard, and every eligible fixed message (53 cases). It also checks PUTS's
BC/DE preservation, returned terminator pointer, balanced stack, and exact decoded
bytes. The measured stack high-water mark in these paths is 32 of 128 bytes.
Existing session, editor, query/ABI, component-input and registry tests pass.

`tools/qualify_fdb_menu.py` runs the assigned COM/OVL pair on private copies of the
released System disks. The focused sequence covers details and sector-map viewer
return, clean Q/BREAK, a new Untitled catalogue, and pending-editor Q/Cancel/Resume
and BREAK/Discard. A subsequent CCP file read checks restoration after exit.
It verifies the grouped menu is visible, all original non-FDB files and reserved
system sectors remain unchanged, the installed pair matches the build, the
filesystem checks cleanly, and the original release media are untouched.

Both cpmsim and native Model 4 runs pass, each with nine complete menu captures.
The final artifact pair is identical on both targets.
Native qualification unloads the normal display RSXs in its private session to
provide the required 53K, then restores the original STARTUP profile. The runner
waits for the startup banner and a unique readiness marker before replaying keys;
CCP prompt matching excludes a trailing blank, which is not present after CLS.

The [evidence directory](evidence/2026-11-06-fdb-main-menu/) contains build receipts,
revision assignment proposals/acceptances, test results, and captured menus.
Readable menu snapshots trim trailing blank rows; the capture archive retains
the original screen bytes. Only
utility:FDB revision 003 baselines are accepted for z80pack and trs80gp. Locked
1.0 release packages are unchanged. This remains a bounded menu correction;
other FDB usability work remains deferred.
