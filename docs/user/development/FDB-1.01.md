# FDB 1.01 development workbench — outside the locked 1.0 manuals

For released FDB 1.0 (001), use the [Command and Utilities Reference](../../manuals/Command-and-Utilities-Reference.md#fdb). These retained development instructions are not a replacement for the locked release entry.

This guide describes the 1.01 development workbench. Released 1.0 media and
packages remain unchanged. The development identity is `FDB 1.01 (002-dev)`;
this work does not establish a release baseline.

FDB.COM and its matching FDBVIEW.OVL ship in user 0 on both System disks,
with CONFIG.COM and the 108-entry DISK.FDB. Copy both FDB files into the same
drive and user area when using a work disk. The viewer must match the COM;
missing or damaged viewers are refused without changing pending work.

`FDB /VER` displays the component identity and compact BetterCP/M Utilities
identification. `FDB /H` and `FDB /HELP` display the same short help screen.
These exact tokens are case-insensitive, accept space or TAB separators, and
ignore other arguments. Help takes precedence over `/VER`. Queries return
without opening a catalogue, changing drives/users, or setting up the console;
they also work in the normal Model 4 50 KiB configuration. Longer tokens such
as `/VERIFY` and `/HELPER` are not queries.

The help screen lists the positional command forms as well as the switches:

| Command | Action |
| --- | --- |
| `FDB` | Open DISK.FDB in the workbench. |
| `FDB file.FDB` | Open a named catalogue in the workbench. |
| `FDB in.FDB out.FDF` | Export a catalogue as FDF text. |
| `FDB in.FDF out.FDB` | Compile FDF text to a catalogue. |

Listing, comparison, editing, drive application, and selective import/export
are interactive workbench operations.

The interactive workbench needs the standard 53 KiB TPA. On Model 4, the
normal startup loads screen personalities; before starting FDB, release them:

```
RSX UNLOAD ADM3A
RSX UNLOAD M4SCRN
```

After quitting FDB, run `SUBMIT STARTUP` with the unmodified shipped startup
script, or cold-boot, to restore the normal console. That script loads M4SCRN
then ADM3A as one queued sequence before clearing the screen. If your startup
script is customized, use your normal console startup sequence. If other
extensions also consume memory, unload unneeded extensions or use a clean
boot. FDB refuses insufficient memory without changing files.

Run `FDB` to open the working catalogue. F opens a catalogue; N starts an empty
one. I imports one definition or an entire .FDB or .FDF. L lists entries with
filtering and paging. D displays one format; P compares independent catalogue,
editor or active-drive sources. Pages 1–4 show geometry, sector maps, CP/M
parameters and effective layout. Q returns from a viewer or menu; BREAK cancels
fields or returns while preserving the working format. ESC also cancels a
field. Sector maps use `,< Previous   .> Next`, show the visible slot range and
total, and stop at the last chunk. Comparison uses the longer map; an empty
differences chunk does not mean the whole comparison is identical. Invalid
choices retry locally.

Filename prompts accept `NAME.EXT`, `A:NAME.EXT`, and the displayed
`A0:NAME.EXT` form (A–P, user 0–15). An explicit user must match the current
user area; FDB never switches it. Inputs occupy a separate line, accept up to
32 characters, and remain editable with Backspace or DEL at the limit. Excess
characters sound the bell and are discarded until corrected or submitted.

A captures B–D into the editor; B loads a named catalogue entry; C starts a
blank definition; E resumes pending work. Edit related fields, inspect the
result and press V to validate. Numeric input shows the selected field, its
current value and accepted decimal/0x range. Failed relationship checks name
the relevant page and rule; SPT/DSM mismatches show current and expected/maximum
values. Temporary inconsistency remains editable. Edit the ID with I on page
1; I on page 3 edits CKS. S offers applying to B–D, putting the working
format in the catalogue, or writing the catalogue. Applying changes the active
drive only; it does not format media or save cold-boot defaults. Cylinder
formats retain catalogue units, with equivalent runtime units used when needed.
Drive A is protected. Before confirmation, FDB shows the logical target,
physical selector, current/proposed runtime SPT and working format identity.
Declining leaves all bindings unchanged.

The editor and RAM catalogue have separate modification states. Pending editor
work is not yet in the catalogue. K adds it to RAM; W writes the catalogue to
disk. Applying a drive does not perform either operation. Quitting with pending
work offers catalogue+write, discard, or cancel.

O exports one or all entries to .FDB or .FDF. Exporting one entry into an
existing catalogue preserves unrelated entries. S saves the complete working
catalogue. A named catalogue shows the full default destination above the
prompt; Untitled requires a filename. Review the destination and replacement
confirmation.
Replacement writes and verifies a temporary file before backup/rename. Keep at
least 10 KiB and two directory entries free for a maximum-size catalogue
replacement, in addition to the existing file. On failure, retain any .BAK or
.$$$ recovery files until the original or verified replacement is recovered.
Recovery diagnostics name the actual destination, backup and temporary file,
and distinguish pre-existing recovery files. Keep them until their contents are
understood. Use a writable copy of release media for edits.

The command form `FDB DISK.FDB ROUND.FDF` decompiles a catalogue;
`FDB ROUND.FDF ROUND.FDB` compiles it. An unsupported required extension or a
lossy export is refused. CONFIG uses the catalogue on the current drive or A:;
use `/LOGICAL=B /PHYSICAL=1 /FORMAT="display name"` to bind a supported format
by name. The physical drive's declared track/side capabilities must fit it.

For Model 4 System installation, follow the
[qualified named-binding procedure](../../platform/MODEL4-SHIPPED-INSTALLATION.txt).
The workbench does not itself install a system or format media.
