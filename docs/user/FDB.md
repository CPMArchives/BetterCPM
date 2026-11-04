# FDB catalogue workbench

FDB.COM and its matching FDBVIEW.OVL ship in user 0 on both System disks,
with CONFIG.COM and the 108-entry DISK.FDB. Copy both FDB files into the same
drive and user area when using a work disk. The viewer must match the COM;
missing or damaged viewers are refused without changing pending work.

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
fields or returns while preserving the working format.

A captures B–D into the editor; B loads a named catalogue entry; C starts a
blank definition; E resumes pending work. Edit related fields, inspect the
result and press V to validate. S offers applying to B–D, putting the working
format in the catalogue, or writing the catalogue. Applying changes the active
drive only; it does not format media or save cold-boot defaults. Cylinder
formats retain catalogue units, with equivalent runtime units used when needed.
Drive A is protected. Confirmation is required before application.

O exports one or all entries to .FDB or .FDF. Exporting one entry into an
existing catalogue preserves unrelated entries. S saves the complete working
catalogue. Review the displayed destination and replacement confirmation.
Replacement writes and verifies a temporary file before backup/rename. Keep at
least 10 KiB and two directory entries free for a maximum-size catalogue
replacement, in addition to the existing file. On failure, retain any .BAK or
.$$$ recovery files until the original or verified replacement is recovered.
Use a writable copy of release media for edits.

The command form `FDB DISK.FDB ROUND.FDF` decompiles a catalogue;
`FDB ROUND.FDF ROUND.FDB` compiles it. An unsupported required extension or a
lossy export is refused. CONFIG uses the catalogue on the current drive or A:;
use `/LOGICAL=B /PHYSICAL=1 /FORMAT="display name"` to bind a supported format
by name. The physical drive's declared track/side capabilities must fit it.

For Model 4 System installation, follow the
[qualified named-binding procedure](../platform/MODEL4-SHIPPED-INSTALLATION.txt).
The workbench does not itself install a system or format media.
