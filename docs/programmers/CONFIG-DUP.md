# CONFIG.COM and DUP.COM

CONFIG 1.01 and DUP 1.13 are ordinary transient programs. They require
BetterCP/M disk ABI 5 and four logical drives. CONFIG needs 42 KiB of
transient space; allow 51 KiB for DUP and its private copy buffer. They add no resident allocation: maximum TPA remains
54,273 bytes when no RSXs are installed.

Run `CONFIG` or `DUP` at the command prompt. Keep `DISK.FDF` on the current
drive or A:. The utilities load its text at run time; they do not translate
through cpmtools diskdefs. The shipped, unmodified catalogue has 96 entries.
Sixteen recovered MM built-in formats precede those entries, giving 112 choices.
The built-ins remain available when DISK.FDF is missing.
An existing BIOS binding not found in the file is identified as an unlisted
current BIOS format rather than assigned a guessed name.

## CONFIG

The main menu retains the MM letter assignments. F, G, H and I have implementations;
A–E explicitly report “Feature not yet implemented.” Changes take effect
immediately and survive warm boot. CONFIG H is undergoing acceptance testing.

H saves the four physical drive definitions and four logical bindings to the
current boot disk A:. It requires the matching `A:SYSGEN.DAT`, generated with
the system image. It checks the immutable resident carrier before confirmation,
writes only changed configuration records, and verifies each write. A failed
write or comparison triggers restoration of the original changed records;
restoration failures are reported explicitly. This is not power-loss atomic.
Files, boot loaders and resident executable code are preserved. An ordinary
cold boot then uses the saved settings. H does not install a new system on
another disk and does not persist loaded RSXs: load FDF.RSX again before using
bindings that require it. The z80pack adapter currently has fixed settings.
The reference file consumes disk space, not resident RAM. CONFIG temporarily
borrows and then reloads its format catalogue while running H.

F displays physical drives 0–3. Each drive has six settings:

- Drive size in inches (the present adapter accepts 5).
- Tracks: 35, 40, 77 or 80.
- Sides: 1 or 2.
- Step rate: 6, 12, 20 or 30 ms.
- Motor spin-up in quarter seconds, 0–16.
- Head settling time in milliseconds, 0–255.

Enter keeps the current setting; Ctrl-C returns without applying an edit.
Hardware reductions which would invalidate an attached format are rejected.
The drive count is currently fixed at four by the BIOS ABI; it is displayed,
not editable.

G selects logical drive A–D and then a disk format. Each page displays sixteen
entries A–P. Comma or less-than moves backward; period or greater-than moves
forward. Paging stops at the ends. Enter selects the marked first entry on
the page. Ctrl-C returns to the previous menu.

After checking the format against supported BIOS limits and the available
hardware, CONFIG asks for the physical attachment (0–3), then checks that
specific drive. B and C may have different formats on the same physical drive.
The BIOS remains the final validator; rejected changes leave the binding intact.
A's system binding is protected.

I opens the format workbench. It copies a B-D binding for editing, including
DPB words, geometry, flags, sector IDs and individual sizes. Q applies the
complete working copy; Ctrl-C discards it. The first version exposes dependent
parameters explicitly, without automatic capacity calculations or named-file
saving. See [workbench details](../engineering/FORMAT-WORKBENCH.md).

An incompatible format can exceed hardware capabilities or fail BIOS consistency
checks. The compiled validator now accepts 107 of 112 catalogue definitions;
five source inconsistencies remain under investigation. This count is validation
coverage, not verification of 107 physical formats. Optional FDF.RSX provides
extended ordering and mixed-size mapping. Load it before assigning such formats;
unloading it detaches dependent B-D bindings and restores its TPA allocation.

## DUP

A formats a disk using the selected logical drive's current BIOS binding.
Use CONFIG G or I first to choose another format. DUP displays the logical drive,
physical target, and known format name, then requires Y before writing.
Any other response cancels. Physical drive 0 is protected, including aliases.

The formatter generates sector IDs in the FDF skew order, address marks,
CRC commands, erased data and gaps. It supports standard FM/MFM track streams
within the current adapter's 3,125/6,250-byte revolution budgets, and honours
the inverted-data flag. It rejects tracks that cannot fit before requesting
confirmation. No boot system is installed on the formatted disk.

After writing each track, A reads every 128-byte record through the BIOS
and checks for E5 fill. Each read performs a fresh physical-sector read, so
sector CRC errors are detected as well as wrong contents. Verification must
pass before the next cylinder/side is formatted.

Progress shows cylinder and side. Ctrl-C aborts between synchronous operations;
the message makes clear that a partly formatted disk remains. Controller errors
stop the operation and display their status. A read or compare failure reports
cylinder, side, sector ID, zero-based record within the surface, and status.
Status 254 is DUP's content mismatch, rather than a controller status.
“Format complete” now means every requested track passed read-back verification.

B copies all sector contents, including reserved tracks, directories, deleted
file remnants and unused space. It is not a file copy or a flux/track clone.
Choose source and destination logical drives. Physical drive 0 is protected as
a destination, and source/destination aliases of the same hardware are rejected.
The confirmation identifies both physical drives.

When bindings differ, B tries the checked BIOS setter with the source format
and destination hardware. Incompatible hardware is rejected before writing.
DUP then offers to format the destination while copying. Declining restores
the original binding without writing media. For each cylinder/side, DUP first
buffers the source, formats and verifies the erased destination track if needed,
writes the buffered contents, and reads them back for comparison. With matching
bindings it copies and verifies without reformatting. Source read failures,
destination errors, compare failures and Ctrl-C stop the copy.

Temporary configuration is restored on completion, cancellation and errors;
BDOS disk state is invalidated for every alias. All BIOS writes are synchronous.
A failed restoration retains the saved binding and prompts to retry instead of
silently returning. After restoration, CONFIG may be needed to access the copied
disk through that logical drive. The source format must already be configured;
there is no format autodetection or single-drive disk-swapping mode.

C scans all configured sectors, including reserved tracks, without writing.
It uses the same record walker as A and B, but accepts arbitrary contents and
continues past unreadable sectors. It reports their locations/status and a final
count, counting each failed physical sector once. Ctrl-C stops the scan. It does
not check directory/allocation consistency or attempt repair.

The UI uses the private inverse-character service when available, with plain
text fallback. Configuration and console calls go through BDOS; sector transfers use the
standard BIOS vectors discovered through page zero. The transients contain no
platform port or hardware memory-map accesses. The write-track stream follows the current BIOS
contract, so it is not an assertion of support for every possible controller.

## Build and tests

`python3 tools/build_disk_utilities.py` creates both COM files. The complete
build includes them and DISK.FDF in the boot image automatically.

`python3 tools/test_disk_utilities.py` checks the assembly parser against all
112 records and verifies paging, inverse headings, copy/check menus and exits.
Additional `settings`, `format`, and `reject` arguments run the corresponding
emulator scenarios. Every run uses private disk copies. Screen captures are
retained under `build/test-results/disk-utilities/`.

`tools/test_dup_operations.py` exercises copying, check, declined confirmation,
full binding restoration, source/system preservation, reserved-track data and
untargeted-track preservation on private images. Its `same`, `mixed`, `bad`,
`protected`, and `abort` modes cover matching formats, mixed sector sizes, bad
CRCs, write protection and interruption. The mixed case uses FDF.RSX.

The z80pack adapter still rejects format changes and write-track requests.
Copy between matching fixed-format bindings and read-only checking use its
standard BIOS interface; cross-format copying requires adapter support.

Real-hardware timing and native ZSM4 parity for these new utilities remain
unverified. Tests of other BIOS services are documented separately.

## Formatting regression found during implementation

The first complete 40-cylinder test reached cylinder 32 and returned controller
status 128 (not ready), although the earlier one-track BIOS test passed.
Fetching the control overlay switches to the system disk before each target
track. Re-selecting the target at the same cylinder after the common seek
service fixes this failure. This adds seven bytes to the existing control
overlay (916 bytes total) and no permanent RAM. The public ABI is unchanged;
BIOS implementation is now 1.5.

The target adapter has a timed motor/drive-select latch. Its refresh behaviour
is documented in the [Tandy Model 4 technical reference](https://www.vintagecomputer.net/fjkraan/comp/trs80-4p/doc/Model_4_Technical_Reference_Manual_1985_Tandy.pdf).
The regression verifies all 40 requested tracks, their sector IDs, ID/data
CRCs and erased payloads; untargeted tracks and the system image stay identical.
This is a target I/O fix, not a change to the portable memory arrangement.

The current control overlay occupies 1024 bytes; the 916-byte figure above
records the earlier formatting regression fix. Current BIOS implementation is 1.9.

## Read-back performance and diagnostics

BIOS 1.8 skips the mechanical seek and settling delay when the same physical
drive remains selected at the same cylinder. Failed seeks/restores invalidate
the remembered position before a retry. Drive changes still restore,
seek and settle normally. DUP uses ABI 4 to copy each newly read physical sector
into its own transient buffer. A 512-byte sector now needs one read per pass,
instead of four; a 1024-byte sector needs one instead of eight. Every byte is
still compared after formatting and copying. The cache expires at every track
and pass, writes bypass it, and z80pack uses the standard 128-byte read path.
The cache occupies idle write-track workspace, adding no resident memory and
preserving the 54,273-byte TPA without an RSX.

DUP 1.13 explains CRC, unavailable-sector, not-ready, write-protection and
comparison errors while retaining the numeric status. Formatting failures also
show cylinder and side. Status 1 remains a merged adapter failure: it cannot
reliably distinguish timeout, seek failure and invalid request. A retry succeeding
does not establish the cause of the earlier failure.

The format display distinguishes writing from verification. Successful surface
verifications are counted independently of cylinder-loop termination, and the
count must match cylinders times sides before completion is reported. A full
80-cylinder double-sided run reports 160 verified tracks. `test_dup_full_format.py`
checks every ID, CRC and erased payload on all 1,600 default-format sectors,
starting with an unformatted container rather than relying on existing sectors.

The user's latest MM DUP benchmark is 18 seconds formatting plus 11 seconds
verifying (29–30 seconds total) for an 80-cylinder, double-sided 800K disk.
That run reported one bad sector; the earlier total was 42 seconds. Compare actual confirmation-to-completion
time, not the regression harness's boot, menu or fixed waiting periods.
`test_dup_full_format.py` now waits for the completion display and records that
interval from emulator capture timestamps; its run uses `-turbo`.

Earlier full-disk measurement (BIOS 1.8, DUP 1.12, trs80gp `-turbo`):
341.10 wall seconds from confirmation to completion. All 160 tracks and
1,600 sectors passed independent ID, CRC and erased-data checks, and DUP
returned to CP/M. This remains substantially slower than the user's MM result;
emulator settings must be matched before treating the ratio as definitive.
The format control overlay is still reloaded from the system disk for each
track, causing drive switches and repeated restores/seeks.

MM DUP 2.01 screenshots supplied September 7 show a drive/format listing,
an insertion prompt, and a further destruction warning when it detects a
nonblank disk. Formatting runs upward to track 79; verification runs downward
from 79 to 0. The repeated error is on track 79, at the start of verification;
MM pauses for Enter, continues, then reports one bad sector. This does not
establish whether the media or the write-to-read transition caused the error.
Timing comparisons should exclude the manual error-acknowledgement pause.
BetterCP/M retains the agreed immediate verification after each written track.

DUP 1.13 applies the MM investigation by keeping a private 1K copy of the
adapter's format control image. It restores that image to its advertised
workspace before each track request, avoiding a system-disk read and the
associated drive switching. The standard formatter's validation and error
paths are retained, as are immediate per-track verification and full byte
comparison. Platforms without this capability use ordinary operation 5.
Resident allocation and the maximum 54,273-byte TPA remain unchanged.

The same full 800K regression now measures 50.81 seconds with DUP 1.13,
versus 341.10 seconds with 1.12 (about 6.7 times faster). All 160 tracks and
1,600 sectors pass ID/data CRC and erased-byte checks. This remains slower
than the user's MM run, but retains immediate per-track verification and
byte comparisons. These are emulator wall times, not real-hardware timings.
