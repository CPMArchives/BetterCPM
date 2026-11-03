# Engineering Specification 209 — Native FDB.COM catalogue workbench

**Status:** First-attempt design for review. Package freeze remains on hold.
This proposal does not reopen the BetterCP/M 1.0 candidates.

**Target:** Native BetterCP/M utility on cpmsim and TRS-80 Model 4 under trs80gp.

## 1. Purpose and scope

FDB.COM lets a user inspect, compare, create, edit, and exchange disk-format
definitions entirely within CP/M. It reads and writes BetterCP/M compiled
catalogues (`.FDB`) and BetterCP/M FDF v1 text (`.FDF`). It must handle the
full 108-entry release catalogue within the standard 53 KiB cpmsim TPA.

CONFIG remains responsible for drive configuration. Its option E edits the
format assigned to an active logical drive. FDB provides catalogue management
and can apply a validated working definition to a drive for testing. Reuse
CONFIG's field editor, input conventions, and binding validation where
practical. The first implementation does not require a redesign of CONFIG.
See the [CONFIG guide](../user/users_guide.md#editing-disk-format-definitions)
and [1.0 format support](../platform/FORMAT-SUPPORT-1.0.md).

## 2. Session model

- **Default catalogue file.** The filename offered at save time. At startup,
  FDB opens DISK.FDB on the current drive and user area, or the file named
  on the command line.
- **Working catalogue.** The session's collection of entries, including pending
  imports and edits. It may be backed by a temporary file to conserve RAM.
- **Working format.** One definition open in the editor. Its source may be a
  drive, a catalogue entry, an imported text definition, or a blank definition.

The header shows the catalogue filename or Untitled, entry count, and
modification state. The editor separately shows the working format's ID,
description, source, and modification state. Viewing or comparing another
definition preserves both working objects.

## 3. Main menu

```text
FDB <version> (<revision>)

Working catalogue: A0:DISK.FDB       108 entries       Unmodified

[ F ] Open a catalogue from disk
[ N ] New empty working catalogue

[ L ] List or find formats
[ D ] Display format details
[ P ] Compare two formats

[ A ] Edit the format of an active logical drive
[ B ] Load a catalogue entry into the editor
[ C ] Create a new format

[ I ] Import into the working catalogue (.FDB or .FDF)
[ O ] Export from the working catalogue (.FDB or .FDF)
[ S ] Save catalogue or apply working format to a drive

Select [ F, N, L, D, P, A-C, I, O or S ], or BREAK (^C) to exit.
Your choice: [ ]
```

**F** changes the session catalogue. **N** starts an empty, untitled catalogue
and clears the default save filename. Neither creates a disk file. If opening,
starting over, or exiting would discard pending work, offer **Save / Discard /
Cancel**. A missing default file at startup permits opening another file or
starting empty.

**B** offers a one-time source filename, defaulting to the current catalogue.
Reading an entry from KAYPRO.FDB leaves DISK.FDB as the session default.
**A** offers drives B–D. If the active drive record lacks a catalogue ID or
description, leave those fields visibly unset until the user supplies them.

## 4. Format editor

Use a CONFIG-style layout with a fixed working-copy header, lettered fields,
current values, page number, and visible Modified indicator. Mark changed
values with an asterisk. Provide three pages.

1. **Geometry and identity.** ID, description, cylinders, sides, recording,
   inversion, physical sectors per surface track, sector size, and logical-track
   unit. Show calculated raw capacity and directory offset.
2. **Sector map and addressing.** Show slot, sector ID, and byte size together.
   Support uniform and mixed-size sectors, side order, side direction, and
   track/sector numbering. Wrap or page long maps without truncation.
3. **CP/M parameters.** Show SPT, BSH, BLM, EXM, DSM, DRM, AL0, AL1, CKS,
   and OFF, with their meanings. Distinguish editable parameters from
   calculated results.

Recalculate dependent geometry after each edit. Permit temporary inconsistencies
while the user edits related fields. For example, changing MMI012's logical
track from one surface to one cylinder moves its directory from byte 10,240 to
20,480 and reduces its maximum DSM from 394 to 389. Show the consequence and
flag the old DSM. Leave the decision to change DSM to the user.

**V** validates on demand. **S** validates before saving or applying. BREAK in
a field cancels that field edit. BREAK at editor level returns to the main menu
with the working format intact.

## 5. Saving and applying

The S menu names what will change and where. It offers three actions.

1. **Apply working format to a logical drive.** Show the destination B–D and
   request confirmation. Use the validated binding operation used by CONFIG.
   This changes the active assignment without formatting media or writing
   cold-boot defaults.
2. **Put working format in the working catalogue.** Add a new entry or
   explicitly replace an existing one. Mark the catalogue modified. Keep the
   working format available so the user can test it on a drive and then
   catalogue it without re-entry.
3. **Write working catalogue to disk.** Show the complete destination filename.
   Return accepts the current save default. An untitled catalogue requires an
   explicit filename. If an edited working format has not yet been added,
   offer to include it before writing.

To copy one entry to another catalogue, use **O → One format**. Existing
unrelated entries in the destination must survive. Before replacing a catalogue
file, validate the proposed result, write a temporary file, close it, and verify
its readback. The implementation must define a recoverable CP/M backup-and-rename
sequence for disk-full, write, close, or rename failure.

## 6. Import and export

Both operations accept .FDB and .FDF. The filename extension selects the
representation. Both offer **one entry** or **entire catalogue**.

**Import** stages entries in the working catalogue. Use the heading
`Import into working catalogue`. When it already contains entries, show one
hint: `For an empty catalogue, choose N first.` On success, report how many
entries were added or replaced and that changes are unsaved.

**Export** writes explicitly selected entries to a named destination. Show
the destination and scope before writing. Exporting one entry to an existing
catalogue preserves its other entries. Exporting the entire catalogue to
replace an existing file requires an explicit whole-file replacement confirmation.

Report duplicate IDs and ambiguous display names before committing changes.
Offer **Replace**, **Use a new ID/name**, or **Cancel** as applicable. Cancelling
an import or export must leave the prior working catalogue and destination file
usable.

## 7. List, display, and compare

**L** lists IDs, descriptions, and capacities, with a name filter and paging.
**D** displays one definition. **P** compares two definitions drawn independently
from a catalogue, an active drive, or the editor.

Display and Compare use the same four-page order: **Geometry**, **Addressing
and sector map**, **CP/M parameters and FDB encoding**, and **Effective
filesystem layout**. Compare opens in differences-only mode. Show differences
in effective values even when stored numbers match. For example, two definitions
can both have OFF=2 but place their directories 10 KiB apart. Distinguish an
unknown field in an active drive record from a field whose value is zero.

## 8. Acceptance gates

- **Stock round trip.** Natively export the shipped 108-entry DISK.FDB to text
  and compile it again. Require byte identity and cross-check both directions
  against the [host compiler](../../tools/fdfcomp.py) and
  [decompiler](../../tools/fdfdecomp.py). Refuse a lossy export if an extension
  cannot be represented.
- **New entry.** Add a 109th definition without changing the preceding 108.
  On both emulators, select it by name in CONFIG and read a known file through
  the resulting drive binding.
- **Catalogue workflow.** With DISK.FDB current, import one entry from
  KAYPRO.FDB, inspect it, and save. Verify that the source file and unrelated
  destination entries are unchanged. Exercise both encodings, single-entry and
  whole-catalogue operations, and **N → I → S**.
- **Drive workflow.** Capture a working B–D definition, edit and validate it,
  apply it, and save it as a named entry. Verify that drive A and cold-boot
  defaults are preserved.
- **Failure and recovery.** Exercise malformed text, invalid FDB checksums,
  unsupported extensions, duplicate identities, invalid maps, BREAK,
  insufficient disk space, and interrupted replacement. Check the actual files
  after each failure.
- **Resource and UI limits.** Measure peak TPA, stack margin, scratch-disk
  use, and .COM size on both targets. Verify that every screen fits 80 columns
  and that all values remain accessible through paging.

## Implementation order

First prove the native 108-entry binary/text round trip and measure its
resource use. Next implement the working catalogue and safe file replacement.
Then add the shared editor, drive operations, and inspection screens.
