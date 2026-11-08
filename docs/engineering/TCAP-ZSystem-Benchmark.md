# Z-System TCAP: measured footprint and BetterCP/M benchmark

Status: measured original library objects, 8 November 2026. This is a historical
benchmark and CPU experiment, not BetterCP/M platform qualification.

## Result and scope

The relevant VLIB 4.5 core occupies **541 bytes of program segment plus 60 bytes
of private working data**. Adding the full 256-byte ZCPR3 environment, including
its 128-byte TCAP, gives **857 bytes**. Adding geometry access gives **869 bytes**.
These counts include the selected routines' transitive SYSLIB and Z3LIB modules.
They do not mean that every feature in VLIB or the entire Z-System occupies 857
bytes. Loading all VLIB 4.5 modules and dependencies instead totals 3,075 bytes
with the environment.

The underlying console implementation is **not counted**: the platform BIOS's
display code, any terminal emulator and external terminal firmware lie outside
this measured library closure. The linked BIOS access modules listed below are
not the implementation of a machine's BIOS. Consequently 857 bytes is a
capability-layer benchmark, not a measured complete display-system footprint.
It cannot be compared with BetterCP/M's whole RSX/personality/backend stack to
establish architectural efficiency. The [public integration report](TCAP-Public-Integration-Results.md)
separates the added TCAP allocation from that existing console stack.
The subsequent [Model 4 display-path comparison](TCAP-Model4-Display-Cost-Comparison.md)
measures the actual Montezuma 2.31 native output engine at 445 bytes including
shared helpers. Adding it and geometry gives a 1,314-byte historical core path,
compared with 3,340 bytes for the current BetterCP/M ADM3A path excluding generic
RSX machinery. This is a scoped output-path comparison, not complete feature parity.

The [ZCPR3 Installation Manual](https://www.hartetechnologies.com/manuals/Z-System/zcpr3_installation_manual.pdf#page=93)
places TCAP inside the environment. Its
[VLIB overview](https://www.hartetechnologies.com/manuals/Z-System/zcpr3_installation_manual.pdf#page=109)
describes application library operations for positioning, erasure and emphasis.
The 1984 manual establishes the layout/model; the exact executable measurements
here use the later original LIBS45A distribution, not an asserted 1984 binary.

| Linked use | Program bytes | Private data | Linked total | Plus full environment |
| --- | ---: | ---: | ---: | ---: |
| Environment/geometry access | 16 | 2 | 18 | 274 |
| Video initialization | 158 | 60 | 218 | 474 |
| Emphasis on/off with initialization | 474 | 60 | 534 | 790 |
| Core screen operations | 541 | 60 | 601 | **857** |
| Core plus geometry | 553 | 60 | 613 | **869** |
| All VLIB 4.5 exports and dependencies | 2,418 | 401 | 2,819 | 3,075 |

Geometry access uses the environment's first half; it does not require a further
128-byte TCAP allocation. The full environment is counted once, conservatively,
even though it supplies other Z-System facts. Application libraries are linked
into each utility, rather than a mandatory resident video engine. The shared
environment and per-application code/data have different lifetimes.

Core entry roots are Z3VINIT, TINIT, DINIT, CLS, EREOL, GOTOXY, STNDOUT and STNDEND.
The geometry variant additionally roots GETCRT. No function-level stripping is
used: selecting an entry includes its entire original REL module and closure.

| Core module | Program bytes | Private data |
| --- | ---: | ---: |
| VLIB VIDAB: initialization and pointer table | 154 | 58 |
| VLIB VID7: cursor-string interpreter | 184 | 0 |
| VLIB VID89: output/delay | 69 | 0 |
| VLIB VID1: clear screen/end of screen | 27 | 0 |
| VLIB VID2: erase line | 10 | 0 |
| VLIB VID34: standout on/off | 18 | 0 |
| VLIB VID56: initialize/deinitialize | 30 | 0 |
| Z3LIB Z3INI | 4 | 2 |
| SYSLIB COUT, CAPS, @BIOSA, BIOS | 45 | 0 |
| Total | **541** | **60** |

## What is outside the static total

Application startup, call instructions, application header/installation pointers
and its runtime stack are separate. For example, loading the environment address
and calling initialization takes six Z80 instruction bytes; an ordinary CALL
takes three. These are not an uncounted resident engine.

Fourteen executions of the original linked core, including cursor values up to
255, matched the expected output bytes and returned with balanced SP. Maximum
observed stack use was **30 bytes including the entry return address**. Thus the
857-byte core plus this observed stack uses 887 bytes before application call
sites. This is an observed bound for these fixtures, not a proof of all possible
stack paths. The console BIOS leaf is captured; a real platform BIOS may use
additional stack internally. The fixture allocated the full 128-byte TCAP and
populated 91 bytes. Null-environment initialization and inert clear/position
calls were also exercised.

## Reproduction and provenance

Download the unmodified [LIBS45A.LBR archive](https://www.df.lth.se/~pi/cpm/files/ftp.mayn.de/pub/cpm/archive/zcpr33/libs45a.lbr).
Its SHA-256 is
`39232c13fb0181a26a77a1187ef32121e318a3d4085a294fe6e04bb05fe8cf99`.
The matching [original VLIB source directory](https://www.df.lth.se/~pi/cpm/files/ftp.mayn.de/pub/cpm/archive/zcpr33/vlibsrc/)
was inspected separately. Historical source and binaries are research inputs in
ignored build storage; they are not vendored into BetterCP/M.

Run from the repository root, choosing a fresh output directory:

```sh
python3 tools/prototypes/tcap/measure_zsystem.py \
  --archive build/tcap-zsystem-benchmark/downloads/libs45a.lbr \
  --output build/tcap-zsystem-benchmark/reproduce --execute
```

The optional CPU execution requires the local z80pack Z80 core at
`~/projects/git/z80pack/z80core` and a C compiler. Static object measurement needs
only Python and the repository's existing CrLZH decoder. The tool extracts the
three Microsoft libraries, verifies compressed member checksums, parses their
original REL records, follows external chains, links relocations and reports
actual segment sizes. CP/M file-record padding and encoded REL metadata are
excluded; allocated DSEG and reserved program bytes are included. Unhandled REL
record kinds fail rather than silently contributing zero bytes.

[Recorded measurements](evidence/tcap-zsystem-benchmark/measurement.json) include
archive, script and expanded-library hashes, module inventories, linked-image
hashes and the CPU observations. Two independent output runs reproduced the same
report and linked images.

## Consequence for BetterCP/M

Use the same division of work: a small description with the selected personality,
small helpers linked into the application, and existing output/rendering paths.
The target is the measured 857/869-byte core, with **1,280 bytes** as the maximum permitted
footprint for the comparable TCAP feature set. Count both extra allocated
resident bytes and application helper code/data, including metadata and alignment;
also disclose stack and call-site costs. Prefer a result below the historical
benchmark. No TCAP bytes may remain permanently reserved after unload.

The rejected 13.5 KiB BetterCP/M experiment included an existing 4.5 KiB
resolver/backend/personality baseline; its TCAP increment was 9 KiB. Both totals
must be reported to avoid comparing a whole rendering stack with only Z-System's
capability layer. The [replacement design](TCAP-Memory-Redesign.md) removes that
incremental framework rather than relocating it elsewhere.
