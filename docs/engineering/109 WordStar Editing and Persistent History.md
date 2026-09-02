# Engineering Specification 109: WordStar Editing and Persistent History

## Editing bindings

The enhanced CCP accepts the following WordStar-style controls without
changing BDOS Function 10 behavior for transient software:

| Key | Command-line action |
|---|---|
| `^S` | character left |
| `^D` | character right |
| `^A` | previous word |
| `^F` | next word |
| `^T` | delete the next word and adjacent spacing |
| `^E` | previous history entry |
| `^X` | next history entry |
| `^V` | toggle insert/overwrite |
| `^G` | delete character under cursor |
| `^H` | delete character left of cursor |

Physical arrows, Clear, and Shift-Left remain aliases. `^E` and `^X` were
chosen for history navigation rather than `^R` and `^C`: they preserve the
WordStar vertical-motion relationship and avoid CP/M's established `^C`
abort/warm-boot association.

## Model 4 keyboard boundary

The Model 4 modifier row at `F480h` identifies Control independently of the
ordinary key matrix. The BIOS now translates Control plus `@` through `_` to
ASCII control bytes. Physical Left and Right use private logical bytes 28 and
29, keeping physical Left distinct from `^H`; Shift-Left remains DEL (`7Fh`).

This translation belongs to the platform BIOS. The portable CCP never reads
the keyboard matrix.

## Persistent history block

The current implementation reserves `BE00h..BFFFh` as 512 bytes of protected,
warm-boot-persistent DATA. It is below the fixed `C000h` system gateway and
above installed RSXs. The default dynamic compatibility gateway consequently
moves from `BFFDh` to `BDFDh`.

The block contains a versioned control header and 503 bytes of packed,
length-prefixed command records. Complete command lines are appended in
execution order. When necessary, the oldest whole records are evicted until
the new record fits. Thus normal short commands yield substantially more
history entries without truncating a legal 127-character command.

The CCP keeps no authoritative history content in its reloadable image. It
holds only the line currently being edited; `^E`/`^X` copy selected persistent
records into that buffer. The block is initialized lazily when its signature
or version is absent, which preserves it across WBOOT while safely handling a
cold or previously uninitialized machine.

## Verification

Executable CCP tests append and retrieve multiple variable-length records and
exercise word movement, both character-deletion directions, and word deletion.
BIOS tests distinguish Control-H, physical Left, and Shift-Left at the actual
Model 4 matrix scanner.
