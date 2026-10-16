# VT52 portable backend integration

Status: portable VT52 integration checkpoint qualified, 2026-10-16. This
supersedes the native-wire implementation. CPU, native assembler, live emulator,
application, protected-ROM and clean distribution checks below pass; it does
not claim completion of the other personality conversions or full-system release
validation.

VT52 provider version 1.2 advertises portable MCON 1.1, capability 0004h. It
keeps the ordinary chain at offset 8, initially zero manager-owned backend word
at 12, and callback at 14. The parser contains no BIOS imports, video addresses
or host escape strings. The same carrier uses M4SCRN or ANSISCRN through the
[screen backend ABI](Unloadable%20Screen%20Backend%20ABI.md).

Cursor movement, erase and scrolling now call typed operations. Printable output
advances within the current row and clamps at column 79. Parser reset retains
position and queued replies. Internal clear resets unfinished parsing and clears
and homes through the backend. Private cursor presentation delegates without
advancing the personality cursor. Unknown MCON operations return FFh instead of
accidentally exposing screen-backend operations to monitor callers.

The provider payload is 547 bytes with 96 relocation words. Backend and frontend
allocations are optional loaded memory; no permanent BIOS/BDOS source changes
are required. Unloading the pair restores the 53K baseline.

After building both backends and VT52, the following CPU checks pass:

- `test_vt52_foundation.py --bios build/audit/release-090-z80pack`: 49,920
  relocated control/address cases against a controlled screen-service recorder;
  reply ordering, all 16 queue phases and 17 capacity boundaries, reset/clear,
  unsupported finals, input bypass and assembled exercise behavior. Its native
  strings normalize recorded screen operations for comparison; they are not
  bytes emitted by the portable personality.
- `test_vt52_rendering.py --bios build/audit/release-090-z80pack`: identical
  frontend with actual Model 4/ANSI-host renderers at two backend addresses;
  right edge, cross-screen scrolling, erase, partial address/reset and private
  cursor position preservation.
- `test_vt52_lifecycle.py --bios build/bios` and with the cpmsim BIOS above:
  missing-backend rejection, actual load, removal-while-needed rejection,
  upward relocation after unrelated removal, partial-parser and queued-reply
  preservation, reference rebinding, Function 182 lookup and complete unload.

## Native and live checks

`test_monitor_backend_native.py` runs ZSM4 and DRI LINK on private CP/M disks.
VT52 (547 bytes), M4SCRN (372 bytes) and ANSISCRN (523 bytes) match their host
builds byte for byte. VT52's reply-data buffer now uses explicit zero bytes
rather than assembler-dependent reserved storage.

`qualify_vt52_cpmsim.py` passes with the actual pair: load after HELLO, remove
HELLO to force movement, complete identification and all three VT52TST phases,
unload the pair, report 53K and exit with BYE. The captured host stream contains
ANSI addressing and erase from ANSISCRN, not unparsed VT52 addresses.
`qualify_vt52_wordstar.py` opens, edits, saves and exits original VT52-configured
WordStar through the pair on disposable media; the saved file contains the
inserted marker. These are application/transport checks, not a physical terminal
certification.

The clean distribution build also caught a pre-existing one-byte drift in the
extension live-state inventory. The emitted extension symbols place its five
bytes at E591h..E595h, and the inventory now matches. No source/layout change to
the core was needed for that correction.

Both clean distribution images build and boot-qualify, with the matching
backend and VT52 on each disk (28 files/152K free on cpmsim; 27 files/600K free
on Model 4). The fresh memory report retains 54,273 bytes unloaded TPA (53K+1).

Protected-ROM cpmsim passes the exercise and unload/53K check with no ROM write
violation. The test must use its matching ROM-relocated R3PACK, not the ordinary
RAM container. Initial attempts with an older ROM image/RAM overlay mix failed
profile loading; the final campaign used a freshly rebuilt matching ROM set.

`qualify_vt52_model4.py` uses a disposable STARTUP.SUB to serialize actual
load, VT52TST and unload under trs80gp. Four raw video captures verify the
identification page, marker at row 5/column 10, tab at column 8, right-edge AC,
reset continuation, both KEEP erase rows, command return, empty RSX profile and
53K restored. Earlier timing-based typing runs were unreliable; the final
startup-script campaign completed, and a mistaken string-length assertion was
corrected against its saved captures. No renderer change was required.
Evidence is under `build/vt52-development/model4/pages-jj3xsjq4/` locally.

The VT52 integration gates in this increment pass. ADM3A and ANSI personality
conversion remain separate work, along with the portable starter template. The editable host template is a legacy
teaching example; it does not become portable merely by changing its capability
word.
