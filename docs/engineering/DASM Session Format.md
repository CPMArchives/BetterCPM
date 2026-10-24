# DASM session format 2

`Sname.ALL` saves the current logical input interval and analysis. `Rname.ALL`
requires that the same canonical drive/user/binary name is already loaded.
The stored logical length must fit its readable extent, and its logical CRC32
must match. Loading restores the saved origin and length; it never silently
rebinds analysis to another binary. Empty inputs and unknown versions are refused.

The earlier development format 1 used a 16-bit length and different offsets;
it is refused without changing live analysis.

The descriptor is exactly one 128-byte physical record. Integer fields and
CRC values use little-endian byte order. The 32-bit length representation can express 65,536 without wrapping; this
release rejects a nonzero high length word because its input capacity is 8 KiB.
CRC32 is CRC-32/ISO-HDLC, reflected
polynomial EDB88320H, initial/final XOR FFFFFFFFH. It detects corruption, not
malicious modification. The host test independently checks it with zlib.

| Offset | Bytes | Meaning |
| --- | --- | --- |
| 0 | 4 | ASCII BCDS |
| 4 | 1 | Version 2 |
| 5 | 3 | Reserved, zero |
| 8 | 2 | Logical origin |
| 10 | 4 | Unsigned logical input length; current admission is 1..8192 |
| 14 | 12 | Canonical binary drive (1..16) and space-padded 8.3 name |
| 26 | 1 | Binary user, 0..31 |
| 27 | 4 | CRC32 of exactly the logical binary bytes |
| 31 | 19 | Symbol component record |
| 50 | 19 | Comment component record |
| 69 | 19 | Control component record |
| 88 | 36 | Reserved, zero |
| 124 | 4 | CRC32 of descriptor bytes 0..123 |

Each component record contains a 12-byte canonical drive/name, one user byte,
a two-byte physical 128-byte record count and a four-byte CRC32 covering every
physical record byte, including text EOF/padding. Components are canonical
`.SYM`, `.DOC` and `.CTL` text. Their names must be exact, uppercase, unadorned
FCB spellings; wildcard and attribute bits are refused. Components may not alias
the binary, descriptor or another component role.

Save first checks the descriptor destination, overwrite answer and attributes,
then reserves an unused descriptor scratch. Each component gets an unused
`DSAnnnnn` generation name on the destination DU and is published through the
ordinary checked staging state machine. Existing generations remain unchanged.
Only after all components have been written, closed and hashed is the reserved
descriptor completed and published. Replacement retains the old descriptor
under a unique BAK recovery name. Its component graph remains usable.

A failure before the old-descriptor rename retains the old destination.
A failure after that rename retains its backup and the new descriptor stage.
New orphan generations may remain; the error reports their identities. Do not
remove old generations merely because a new descriptor exists. CP/M offers no
multi-file atomic transaction or power-loss durability guarantee.

Load checks the complete descriptor, binary identity/hash and each component's
identity, count, hash, text grammar, ordering/conflicts and arena capacity.
Symbols stage at workspace +0000..0FFF, controls at +1000..15FF and comments at
+1600..1DFF; the descriptor is at +1F00..1F7F. Live tables and origin/length
change only after all validation and closes succeed. Legacy separate component
imports remain available; legacy implicit same-basename ALL files are refused
as invalid descriptors.
