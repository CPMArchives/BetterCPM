# CONFIG.COM and DUP.COM

The version 1.00 utilities are ordinary transient programs. They require
BetterCP/M disk ABI 3, four logical drives, and at least 42 KiB of available
transient address space. They add no resident allocation: maximum TPA remains
54,273 bytes when no RSXs are installed.

Run `CONFIG` or `DUP` at the command prompt. Keep `DISK.FDF` on the current
drive or A:. The utilities load its text at run time; they do not translate
through cpmtools diskdefs. The shipped, unmodified catalogue has 96 entries.
Sixteen recovered MM built-in formats precede those entries, giving 112 choices.
The built-ins remain available when DISK.FDF is missing.
An existing BIOS binding not found in the file is identified as an unlisted
current BIOS format rather than assigned a guessed name.

## CONFIG

The main menu retains the MM letter assignments. F, G and I are implemented;
A–E and H explicitly report “Feature not yet implemented.” Changes take effect
immediately and survive warm boot. Saving them with SYSGEN is not implemented;
cold boot reloads the installed configuration.

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

Progress shows cylinder and side. Ctrl-C aborts between track operations;
the message makes clear that a partly formatted disk remains. Controller errors
stop the operation and display their status. B (Copy) and C (Check for errors)
currently report “Feature not yet implemented.”

The UI uses the private inverse-character service when available, with plain
text fallback. All OS calls go through BDOS; the transients contain no platform
port or memory-map accesses. The write-track stream follows the current BIOS
contract, so it is not an assertion of support for every possible controller.

## Build and tests

`python3 tools/build_disk_utilities.py` creates both COM files. The complete
build includes them and DISK.FDF in the boot image automatically.

`python3 tools/test_disk_utilities.py` checks the assembly parser against all
112 records and verifies paging, inverse headings, placeholders and exits.
Additional `settings`, `format`, and `reject` arguments run the corresponding
emulator scenarios. Every run uses private disk copies. Screen captures are
retained under `build/test-results/disk-utilities/`.

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
records the earlier formatting regression fix. Current BIOS implementation is 1.6.
