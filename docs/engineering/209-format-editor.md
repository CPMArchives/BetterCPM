# Native FDB working-format editor

FDB retains a working format independently of its open catalogue. A captures
an active B, C or D assignment, B loads a catalogue ID, and C starts a blank
definition. B accepts a one-time .FDB or .FDF source filename. Return uses the
current working catalogue, including pending imports. E resumes the editor.

The three numbered pages cover geometry and identity, addressing and sector
maps, and CP/M parameters. Select a field by its letter and enter the new
value. Binary choices use 0 and 1, with their meaning shown beside the field.
I on page 1 edits the ID and N edits the description. M changes a slot's ID
and size together. Page 2 displays eight slots at a time with their byte sizes.
Use < and > for adjacent groups. BREAK in a field cancels that entry. Q or
BREAK from the editor returns to the catalogue with the working format intact.

Edits can be temporarily inconsistent. Page 1 recalculates raw bytes, directory
byte offset and maximum DSM from the recorded sectors and logical-track unit.
It flags an excessive DSM and leaves its value available for explicit editing.
V runs the native catalogue validator on a temporary one-entry definition.
Drive captures leave unavailable catalogue identity fields visibly unset.
Cataloguing requires an ID and description. Validation of anonymous drive
geometry uses temporary identity fields only in the validation buffer.

S offers D to apply to an active logical drive, K to stage the working
definition in the catalogue, and W to write the working catalogue. Applying
requires a separate confirmation naming the destination. It reads that drive's
current physical mapping and retains it when constructing the new binding.
Explicit size maps pass CONFIG's Function 183 validation before the Function
181 setter. Successful application resets only the affected logical drive.
Catalogue formats may have up to 255 sectors. Applying requires a format
representable in the BIOS's 32-slot record. K uses the existing atomic import
and duplicate-resolution path, and W uses the recoverable save protocol.

The editor code is included in FDB.COM. Session startup copies it above the
session's catalogue scratch area. Assembly checks bound the resident image,
catalogue snapshots and high editor region. At runtime FDB checks the actual
TPA ceiling before the copy. The two-filename converter keeps its original
scratch limit. The session continues to accept a 9,472-byte working catalogue.

## Qualification

Run `python3 tools/test_fdb_editor.py` for the MMI012 directory and DSM example,
one-time source loading, pending-format inclusion and a mixed 255-slot edit.
Run the session and round-trip tests alongside it. The platform qualifier is
`tools/qualify_fdb_editor.py --target z80pack|trs80gp --build-root BUILD_ROOT
--output NEW_DIRECTORY`. Supply the qualified cpmsim path using `--simulator`
on z80pack. It uses fresh disposable media, queries all four physical and
logical records through the public API, changes DSM on a captured format,
confirms application to D, C and B, then compares complete records and the
entire system disk against their expected contents.

The qualified COM is 18,452 bytes, SHA-256
`49d35852959819100d3284ba857ebe389330106c3b91636c8a4ac5d1fae73eaf`.
The interactive session spans 0100h through D04Fh (53,072 bytes), leaving
1,200 bytes of the standard 53 KiB TPA. This includes both catalogue snapshots,
working-format maps, originals for field comparisons, and the relocated editor.

On cpmsim and Model 4 under trs80gp the extracted active API records matched
the expected B, C and D bindings after applying the captured B format with
DSM set to 100. The A binding, physical records, destination physical selectors
and complete boot image matched their baselines. The editor core test also
captured, named, applied and catalogued a working format in one session,
including rejection of drive A and a declined apply to D. The session save
and recovery suite and all 40 conversion regression cases passed.
