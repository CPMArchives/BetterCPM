# Native catalogue list and export

**L** lists the working catalogue, including unsaved imports. Enter a case-insensitive
substring of the ID or description. Return lists all entries. Rows show the ID,
description and raw capacity in bytes. After twelve matching rows, Return continues
and Q or BREAK returns to the session. Capacity uses validated records per logical
track, with both sides counted once for cylinder-unit formats.

**O** asks for a working ID, or Return for the entire working catalogue, then an
explicit .FDB or .FDF destination. For a single ID, an existing destination is
read and validated before merging. Unrelated entries retain their order and
definitions. ID and display-name conflicts are resolved on a private candidate
copy. For the entire catalogue, replacing an existing file requires confirmation.
The destination and scope are shown before writing.

Export uses the session's existing temporary-file, readback and backup/rename
protocol. It preserves the working catalogue, its dirty flag, the editor and the
save default. Choosing the session file itself as a destination explicitly writes
that file. The session remains available for further changes or a normal save.
The session's entry-count and workspace limits apply to the proposed merge.

The core qualification checks the capacity of every stock entry, including
mixed-sector and cylinder-unit formats. It exercises filtered and paged listing,
new and existing export destinations, both representations, conflict resolution,
cancellation and failed promotion. The guest qualification imports a 109th entry,
finds it through L, merges it into another .FDB, exports all 109 to .FDF, then
saves the working catalogue to its original default. The host independently
checks the extracted source and all three destinations.

Run the guest case with `tools/qualify_fdb_session.py --exchange` and the target,
build-root and output arguments documented in the working-catalogue milestone.
The dedicated D detail and P comparison screens are separate spec 209 work.
