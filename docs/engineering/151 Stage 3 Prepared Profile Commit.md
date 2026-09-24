# Engineering Specification 151: Stage 3 Prepared Profile Commit

## Status and production gate

The prepared Stage 3 entry is now the production Function 202 selector. It
connects enumerate/query, append/removal preparation, in-memory commit,
persistent-profile publication, resolver restoration, and resident
self-retirement. The former manager, validator, and publisher path has been
removed; production accepts only BRSX version 2 carriers.

Production cutover and Stage 3 qualification are complete. Forced movement,
failure rollback, warm-boot lifecycle, and immutable-code behavior pass on
trs80gp and cpmsim.

## Prepared transaction

The version-2 production entry accepts LOAD and UNLOAD, validates the
caller-owned bounds, and selects the append or removal coordinator. Removal
builds a prospective profile excluding the named provider; retained providers
use the existing carrier, snapshot, and pointer-union preparation stages.

The finalizer constructs the scheduler and commit requests and a prospective
41-byte persistent profile (count, four names, four primary service numbers).
It verifies that proposed allocations and their gateway stay above the entire
caller workspace. The commit engine publishes that prepared profile before the
final generation store. An empty profile releases the manager reservation and
restores the normal page-zero TPA ceiling.

The internal commit request retains its 25-byte mode-zero form. Mode 1 extends
it to 35 bytes:

| Offset | Size | Meaning |
|---:|---:|---|
| 7 | 1 | publication mode: 0 or 1 |
| 25 | 2 | prepared persistent publisher entry |
| 27 | 2 | prospective persistent profile address |
| 29 | 2 | live persistent profile address |
| 31 | 2 | public request address |
| 33 | 2 | returned primary service |

These are private preparation/commit interfaces, not additional public BDOS
selectors or a frozen general allocator ABI.

## Disk workspace and return safety

Physical-sector reads can overwrite all 1,024 bytes of `LY_CFG`. Overlay reads
therefore execute in caller-owned RAM and stage a complete image before copying
it into its execution slot. The final 12 bytes of the manager slot are never
copied by this handoff; they contain the live return frame and BDOS gateway.
The builder enforces a 1,012-byte executable/data prefix for manager overlays.

The platform raw-overlay selectors enforce the same boundary. The TRS-80
selector stages the second 512-byte sector, and the z80pack selector stages the
eighth 128-byte record. Each installs bytes 0 through 1,011, preserves the nine
live return-frame bytes at offsets 1,012 through 1,020, and installs the common
three-byte BDOS gateway at offsets 1,021 through 1,023. Raw replacement can
therefore return through the active frame without retaining the old overlay.

Transaction RAM is capped at `7000h`, below every prospective resident move.
The top 3,840 bytes of that effective caller workspace are reserved as follows:

| Offset from reserved base | Size | Purpose |
|---:|---:|---|
| 0000h | 1,024 | staged incoming overlay |
| 0400h | 256 | position-independent reader code |
| 0500h | 256 | reader state and private stack |
| 0600h | 1,024 | saved CONFIG/movement workspace |
| 0A00h | 1,024 | prefetched resolver |
| 0E00h | 256 | isolated manager return stack |

The entry moves the fixed three-word extension return frame into the final
stack band before any manager phase executes. Disk and overlay reads therefore
cannot overwrite either that frame or live STATEFUL allocations. The raw file
reader consumes two complete 512-byte records for every private overlay;
builders pad all such overlay files to exactly 1,024 bytes.

The resolver and commit dependencies are read before the commit starts. Resolver
restoration after commit is a bounded memory copy, with no file operation that
could fail after publication. These bytes are transient workspace, not a new
permanent PDS allocation. Production `RSX.COM` supplies bounds that leave space
for prospective resident allocations. BATCHIO retirement deliberately consumes
the disposable command workspace and warm boots after success or failure; a
successful commit never returns through the removed provider.

## Qualification

`tools/test_rsx_stage3.py` executes the assembled entry, coordinators, preparers,
finalizer, commit, publisher, and resolver with a file-service fixture. Every
fixture read overwrites the complete CONFIG buffer, modelling the physical I/O
hazard. It checks:

- append of HELLO and STATEFUL;
- state initialization and mutation before removing the leading provider;
- forced retained STATEFUL relocation preserving mutable data and linked/runtime
  pointers;
- rejection of insufficient workspace and a missing resolver without changing
  live allocations, persistent records, or the generation;
- final removal restoring the default TPA ceiling.

The coordinator, overlay handoff, BRSX-v2 carrier normalizer, and in-memory
commit have separate focused tests. The production test snapshots each
STATEFUL carrier byte before movement and proves that reconstruction changes
only loader-owned header words and declared pointer slots; executable code and
immutable descriptors remain byte-exact.

The platform-loader and return-stack concerns found during exploratory
production integration are now resolved. `M4_RSLOAD` preserves the requested
selector without replacing the physical-read status flags. Failure recovery
moves its return frame back to the protected extension caller's stack before
raw manager restoration can overwrite the manager slot. The focused loader
safety test verifies both behaviors, including a restoration stub that
deliberately overwrites the former manager-stack location. It also executes
both platform selectors against synthetic carriers and verifies the preserved
frame and installed gateway byte for byte.

Production dispatch now uses the prepared transaction path. All supplied
callers issue the 18-byte version-2 request. LOAD and UNLOAD callers provide
explicit workspace bounds; BATCHIO self-retirement uses the same removal
transaction and then warm boots. Warm boot preserves the committed live chain
and does not reload retained STATEFUL data from the original carrier.

`tools/test_stage3_cross_platform.py` supplies final integrated evidence on
both supported 1.0 platforms. Its success scenario initializes and mutates a
STATEFUL provider, forces relocation by removing the provider below it, checks
state before and after warm boot, and exercises the callable service through
Function 208. Its rollback scenario removes a required resolver file, proves
the transaction fails, and verifies that the former profile and state remain
published. Both scenarios pass on trs80gp and cpmsim. Stage 3 is complete; no
further production architecture increment is planned.
