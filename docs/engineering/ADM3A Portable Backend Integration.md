# Portable MM-style ADM3A integration

Status: portable ADM3A production-integration checkpoint qualified, 2026-10-16.
Both clean System Disks pass filesystem, installed-file integrity, CONFIG
fingerprint and boot/command-identity checks.

ADM3A provider 1.1 uses portable MCON 1.1, capability 0004h. The canonical
chain remains at +8; the initially zero manager-owned backend word is +12.
The parser owns row, column, pending address, reverse and visibility state.
It contains no Model 4 addresses, BIOS symbol imports or hardware port writes.
It calls SCRN for cells, positioning, fills, scrolling, line operations and bell.
The backend clamps cell output, while the personality implements MM wrapping.

Visibility query returns the logical MM mode. ESC 0/1 also updates backend
cursor visibility; hidden private-cursor draws are suppressed. Reverse mode
survives clear/reset and applies to blank fills. Cursor operations retain the
established MM row/column and cross-row backspace semantics.

The new payload is 492 bytes versus the previous 583. M4SCRN is 359 bytes,
512 allocated. ANSISCRN provider 1.1 remains SCRN ABI 1.0 and is 620 payload
bytes/114 relocations, within its unchanged 768-byte allocation. It explicitly
paints reverse EOL/EOS blanks: ANSI erase commands cannot be relied upon to
retain reverse attributes in subsequent rows. No permanent core growth occurs. Both backend provider versions are now 1.1,
while the SCRN callable ABI remains 1.0. Operation 7 accepts literal display
bytes: Model 4 preserves them; ANSI-host output substitutes `?` for unsupported
glyphs without emitting terminal controls. The original MM binary confirms all
448 ordinary-byte/reverse combinations.

The cursor review also corrected VT52 provider 1.3 (559 payload bytes). Private
cursor draws must advance logical and physical position per BDOS Function 178.
Both personalities now implement them through typed cells, including a reverse
blank cursor on cpmsim. Prior VT52 evidence asserting no advance is superseded;
new boundary and host command-line Backspace checks cover the correction.

Checks passing with actual assembled code:

- 131,072 relocated address sequences, parser reset, visibility, clear, raw
  bypass and the assembled ADMTST utility's controlled visual/input campaign;
- 46,080 directed Model 4 movement/erase cases, guarded video boundaries,
  reverse fills and the original bounded bell pulse sequence;
- 15,360 relocated insert/delete operations compared with original MM 2.32;
- identical frontend through actual Model 4 and ANSI-host backends, each at two
  addresses: wrapping, scrolling, reverse blank fills, line operations,
  incomplete addressing/reset and visibility;
- real RSX manager on both platforms: missing-backend rejection, actual load,
  removal-while-needed rejection, partial address and reverse/visibility state
  retained after movement, backend-reference repair, service lookup and 53K
  restoration on unload;
- native ZSM4/LINK matches ADM3A, VT52 and both backend payloads byte for byte.

The actual Function 178 handler is also tested with both personalities and both
backends. Cursor draws preserve DE across backend dispatch so the handler can
distinguish drawing from querying, including adverse relocation addresses.
Production Model 4 Function 6 input polling also reads a held/released matrix key
with the configured CRT IOBYTE.

Directed tests that initialize cursor state set both the personality coordinates
and the backend's physical cursor; real applications move it through the parser.
Live cpmsim passes all ADMTST visual phases, cursor visibility, keyboard,
unrelated-module movement and unload/53K. It also corrects `RSX LISX` with
Backspace to execute `RSX LIST` while the monitor is active. The same exercise
passes protected-ROM cpmsim with no write violations and its matching relocated
R3PACK. Native ZSM4/LINK parity passes for the final personality and backends.

The Model 4 campaign captured the complete ADMTST pages, physical A/colon/bracket
keyboard checks, unload and 53K restoration. It used the initial portable
candidate; the later cursor correction is covered by current CPU and host
checks, and the dedicated Model 4 command-line-editing campaign now passing.
Original MM CONFIG 3.10 also renders its opening menu with the corrected portable
personality; configuration operations were not exercised.

The Model 4 startup now loads M4SCRN, then ADM3A, clears the screen and prints
the banner. This explicitly initializes screen position before presentation.
A manual personality switch likewise requires CLS before screen use. Both disks
include the identical ADM3A carrier and ADMTST Build 002; cpmsim startup remains
the basic console. The final clean System Disks contain 30 files/148K free
(cpmsim) and 27 files/600K free (Model 4). Both pass rebuild/boot qualification.
The final native editing campaign types `RSX LISX`, corrects it with Backspace
and executes `RSX LIST`; it then unloads both modules and confirms 53K.

Native test automation must allow warm return to finish before sending matrix
keys. A marker printed by a transient precedes CCP/RCP reload and is not itself
a readiness signal. The batch campaigns retain bounded delays and assert the
resulting command output. Earlier prompt-wait/early-input timeouts were not
qualification successes. The final editing evidence is under
`build/monitor-development/native-campaign/editing-_63u28kh/`; final clean-build
evidence is under `/private/tmp/adm3a-final-qualified-work/` locally.

ANSI personality conversion and portable templates remain subsequent work.
