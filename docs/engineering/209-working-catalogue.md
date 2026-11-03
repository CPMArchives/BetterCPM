# Working catalogue and recoverable saves

This milestone builds on the native round trip in PR #594 and implements the
session and catalogue-write portions of [specification 209](209%20Native%20FDB%20Catalogue%20Workbench.md).

Run `FDB` to open DISK.FDB on the current drive and user area, or
`FDB B:OTHER.FDF` to use a named source and save default. A missing or invalid
startup file leaves an empty, untitled session. The two-filename command
continues to convert to a new destination. In the session, type a choice and
press Return. BREAK cancels a prompt or requests exit at the menu.

- **F** opens a validated .FDB or .FDF. **N** starts an untitled empty catalogue.
  Leaving modified work offers Save, Discard or Cancel. An unsuccessful open
  preserves the current working copy.
- **I** accepts a source filename and one ID or Return for all entries. Duplicate
  IDs offer replacement, a different ID or cancellation. Conflicting descriptions
  can be renamed on the imported copy. A successful import marks the working
  catalogue modified. Cancelling any conflict discards the entire pending import.
- **L** lists IDs and descriptions. **S** writes the whole working catalogue.
  Return accepts the displayed default. An untitled catalogue requires a name.
  The final prompt shows the drive, user and filename. A successful Save As
  becomes the new default. **Q** or BREAK exits.
- The working copy and import snapshot each hold 9,472 compiled bytes. The session
  accepts up to 128 entries subject to this size limit. The stock 108 entries
  and the 109-entry test catalogue fit. Text is streamed, so the size limit
  applies to the compiled representation.

## Save and recovery

For a destination such as B:TEST.FDB or B:TEST.FDF, all operations use the
current user area on B. The temporary file is TEST.$$$ and the backup is
TEST.BAK. A pre-existing file with either recovery name stops the save.

1. Validate the working catalogue. Write a fresh temporary file and close it.
2. Reopen it. Compare every record and verify EOF. For FDF, generate the
   expected text again and compare the physical bytes, including padding.
3. If the destination exists, rename it to the backup. Rename the verified
   temporary file to the destination. If promotion fails, try to restore the
   backup to the original name. Each rename checks that its target is absent.
4. Once promotion succeeds, clear the modified flag and remove the backup.
   Report a retained backup if removal fails.

Allow enough free blocks and directory entries for the entire new file alongside
the original. A write or close failure before replacement leaves the destination
intact. A failed readback retains the temporary file for inspection. After an
interruption, inspect the files on the indicated drive and user area before retrying:

| Files found | Recovery |
| --- | --- |
| Original destination plus .$$$ | The destination is still available. Inspect or set aside the temporary file before retrying. |
| .BAK and .$$$, destination absent | Restore the previous catalogue with `REN TEST.FDB=TEST.BAK` (use TEST.FDF for a text destination). The temporary file contains the verified proposal. |
| Destination and .BAK | Inspect the published catalogue. Keep or rename the backup until satisfied with the result. |
| Only .$$$ from a new-file save | Its write may have been interrupted. Validate a copy under the intended extension before adopting it. |

Recovery assumes the CP/M directory can still be read and individual BDOS
renames completed normally. Keep recovery files until their contents are
identified. FDB refuses to overwrite them on a subsequent save.

## Qualification

`python3 tools/test_fdb_session.py` exercises the assembled utility against the
record-level BDOS fault harness, including write, close, promotion and rollback
failures, byte corruption during readback, both rename boundaries, recovery
name collisions, dirty-state prompts, text replacement and import conflicts.
`python3 tools/test_fdb_roundtrip.py` runs the existing conversion regression
suite. `tools/qualify_fdb_session.py` runs the interactive stock-to-109 save on
disposable system tracks and extracts both files for comparison.

The CONFIG-style working-format editor, live drive operations, richer inspection
and the separate O export workflow belong to later specification 209 stages.

On cpmsim and Model 4 under trs80gp, the same 13,230-byte COM imported TEST109
into the stock catalogue, confirmed replacement of DISK.FDB, and returned to
the command prompt. Each extracted result matched the host's serialization of
the original 108 definitions followed by TEST109. The source file was unchanged
and neither recovery name remained. The resulting 109-entry catalogue SHA-256
was `f05a2a1561aadd40d365ca391c85dd18bab7ef6170852ce1019c6325bb345619`.
All 40 conversion regression cases passed. Failure injection and interrupted
directory states were tested in the full Z80 core with a BDOS test harness.
