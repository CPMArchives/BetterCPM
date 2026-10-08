# Engineering Specification 119: BCPX Version 1 Module Format

## Decision

The `BCX1` proof carrier is superseded by the versioned `BCPX` format. Version
1 is a general relocatable Command Processor Extension carrier: the protected
loader selects an arbitrary eight-character filename stem from the persistent
reconstruction table and does not identify BASIC or HELLO itself.

The first 512-byte record group contains the structural header and relocation
directory. Executable code follows at byte 512. Command metadata follows the
executable bytes and is not copied into command-environment memory.

## Version 1 header

| Offset | Size | Meaning |
|---:|---:|---|
| 0 | 4 | `BCPX` signature |
| 4 | 1 | format version, `1` |
| 5 | 1 | module class, `1` for CPX |
| 6 | 1 | required CPX ABI major, `1` |
| 7 | 1 | required CPX ABI minor, `0` |
| 8 | 2 | flags; all undefined bits must be zero |
| 10 | 2 | link base |
| 12 | 2 | executable byte count |
| 14 | 2 | page-rounded runtime allocation |
| 16 | 2 | command-entry offset |
| 18 | 2 | initialization offset, or `FFFFh` |
| 20 | 2 | shutdown offset, or `FFFFh` |
| 22 | 2 | relocation count |
| 24 | 2 | header size, currently 512 |
| 26 | 2 | payload offset, currently 512 |
| 28 | 2 | relocation-directory offset, currently 48 |
| 30 | 2 | command-metadata offset |
| 32 | 8 | uppercase, space-padded module name |
| 40 | 2 | module major and minor version bytes |
| 42 | 1 | number of exported command names |
| 43 | 1 | reserved |
| 44 | 2 | additive 16-bit payload checksum |
| 46 | 2 | reserved |

Each relocation is a little-endian 16-bit offset into the executable image.
Each command-metadata record is an uppercase, space-padded eight-byte name.
Version 1 permits at most 232 relocation records in its first header group.

## Loader behavior

The loader validates signature, format, class, required ABI, nonzero size,
page-rounded allocation, aligned section boundaries, relocation count and
sites, command-entry bounds, and both lifecycle-entry fields before publishing
the runtime entry.  Each lifecycle field is either `FFFFh` or an offset strictly
within the executable byte count. It loads only the executable byte count,
applies each relocation against the calculated runtime base, writes the
validated entry address into the common runtime header, and links the module
in persistent-table order.

After constructing the complete prospective chain, the reloader calls present
initialization entries in configured order and publishes the chain only after
all succeed.  Before a transient program reclaims the live command environment,
the CCP calls present shutdown entries in reverse order.  The exact register,
failure, recovery, and pointer-lifetime rules are defined by section 7.4 of the
*RSX and CPX Programmer's Guide*.

The version-1 live header occupies the first eight executable bytes:

| Offset | Size | Meaning |
|---:|---:|---|
| 0 | 2 | next live CPX base, or zero |
| 2 | 2 | relocated command-entry address |
| 4 | 2 | relocated initialization-entry address, or zero |
| 6 | 2 | relocated shutdown-entry address, or zero |

The loader owns and rewrites these words.  The carrier's entry offsets remain
relative to the beginning of this complete executable image.  An absent
`FFFFh` lifecycle offset becomes zero in the corresponding live-header word.

`BCM1` remains the private CCP carrier and is normalized into the loader's
internal descriptor rather than being mistaken for a CPX header. This explicit
split preserves CCP compatibility while allowing the CPX format to evolve.

## RCP-owned protected shadow policy

Accepted design addition; implementation and lifecycle qualification remain
pending. This policy does not alter the BCPX carrier or its eight-byte live
header, and it does not introduce a general shadow-state allocator.

RCP's per-command automatic-handoff policy shall reside in protected runtime
memory associated with the installed RCP package, outside its reconstructible
executable image. RCP owns the bit assignments. The core may initialize or
discard the entire byte, but shall not interpret individual command bits.
Zero shall represent the package's default policy, with automatic handoff
enabled; a compact suppression bitmap may encode OFF as a set bit.

For the bounded initial implementation, reserve one byte at `LY_SYS+00B6h`
(currently D67Ah). It is the first of seven existing zero-filled bytes after
the four eight-byte CPX profile records, before `SINIBODY`. Naming this byte
must preserve every existing field address, the four-record capacity, gateway
size and BDOS boundary. The audited reservation-only prototype is byte-identical
to the current gateway. No history/PDS owner-private storage may be borrowed.
This is fixed gateway-associated package state, not a new 1.0 PDS owner.

The following lifetime rules are required:

- Preserve policy across command invocations, transient execution, WBOOT,
  CCP/CPX reconstruction and RSX reconfiguration while RCP remains installed.
- Explicitly removing RCP discards/resets the policy. A later successful load
  begins with defaults. This supersedes the earlier proposal to retain it
  across explicit unloading and reloading.
- Cold boot restores defaults regardless of earlier contents.
- Duplicate LOAD, no-op or failed profile requests, unloading another package,
  and profile reordering shall not reset RCP's policy.
- Never save the byte through CONFIG, startup records or permanent disk state.
- Never clear it merely because transient lookup failed; the user may later
  make the transient available.

Explicit-removal handling belongs to the committed profile-removal path.
The ordinary CPX shutdown callback shall not discard this state: shutdown also
runs before ordinary transient execution. Initialization of a reconstructed
RCP shall not overwrite valid shadow policy while its profile membership
continues. Package association must use a defined package identity, not a live
address or profile slot index; alternate filenames and duplicate package
instances require an explicit identity policy before being claimed supported.

`COPY /HANDOFF=OFF` and `COPY /HANDOFF=ON` shall work through resident COPY
without COPY.COM. OFF suppresses subsequent automatic handoff attempts while
retaining the resident diagnostic. ON restores automatic handoff. Parse these
controls before ordinary COPY operands; malformed controls leave policy
unchanged. Other command bits, if admitted, are independently controlled by
RCP. Explicit transient invocation remains an ordinary program invocation.

The session policy is distinct from a one-invocation handoff request. The
latter belongs to CCP working state, is cleared between commands, and causes
direct entry into normal transient lookup without another resident/CPX search.
The agreed diagnostic sequence is defined in architecture specification 16
and `COPY Utility.md`; the exact backward-compatible handoff signaling ABI is
still to be specified and qualified.

Before implementation closure, measure cold reset, removal and control code,
including overlay limits; require zero BDOS growth. Test all lifetime rules,
per-command independence, absent/present transients and preservation of
unrelated protected bytes. A general per-profile runtime-state facility is
post-1.0 work.

## Verification

`tools/test_cpx_format.py` checks both shipped modules' identity, ABI, section
layout, relocation bounds, names, command metadata, and payload checksums.
The reloader tests exercise arbitrary filename-driven restoration and
relocation; physical `trs80gp` tests verify BASIC/HELLO ordering, unloading,
reloading, WBOOT reconstruction, and directory-write integrity.
