# Compact TCAP model: first executable qualification

Status: private XTAB 0.1 experiment, 8 November 2026. The ordinary checked cpmsim
source-image lifecycle passes. Public integration, installation qualification,
Model 4 and Model II remain open. Utility migrations, HELP delivery and release
assignment remain deferred.

This implements the [Z-System model](TCAP-Memory-Redesign.md): a small description
with each personality and a bounded application library. It adds no BIOS hook,
loader path, kernel reservation, global counter, token engine or cache. It uses
the existing checked BMET2 carrier binding and Function 182 registry. The prepared
ordinary system comes from the current engineering worktree; this experiment
applies no additional system/loader patches to it. It is not a clean release build
or conformance with the superseded transaction contract.

## Allocated memory

| Personality | Table | Query code | Extra resident allocation | Application helper | Comparable total |
| --- | ---: | ---: | ---: | ---: | ---: |
| ADM3A | 33 | 10 | 256 | 543 | **799** |
| ANSI | 56 | 10 | 256 | 543 | **799** |
| VT52 | 29 | 10 | 0 | 543 | **543** |

All quantities are bytes. The helper contains 373 bytes of code and 170 bytes of
data: two registry requests, two coordinate bytes and a 128-byte table copy. Its
only external runtime service is existing BDOS. No library dependency or separate
interpreter allocation is omitted.

Resident differences include payload rounding, the second ten-byte callable
descriptor and the existing descriptor-page charge in both baseline and variant.
The VT52 addition fits its already allocated page. ANSI's complete resident setup
grows from 4,608 to 4,864 bytes, of which only 256 is added TCAP allocation. The
543-byte helper is then transient application memory, giving the comparable
799-byte total.

The diagnostic COM, including the entire helper plus callers, messages and failure
printer, is 730 bytes. Added to the largest extra resident allocation, that is
**986 bytes**, or **1,002 bytes** with the helper's maximum observed 16-byte stack
use. The stack fixture captures the library and a mocked BDOS leaf; platform
BDOS/BIOS internal stack is excluded. This distinction also applies to the
[historical benchmark](TCAP-ZSystem-Benchmark.md).

## Guest and CPU evidence

A complete pinned cpmsim CPU executes the ordinary checked BIOS, BDOS, command
loader, filesystem and RSX manager on disposable images, beginning at cold boot.
The sequence loads ANSISCRN, then ADM3A, ANSI, VT52 and ANSI again, unloading each
personality before loading the next. Each runs the diagnostic twice; each JP 0
warm return is followed by fresh discovery and a descriptor copy. Absence is
checked before loading and after every removal.

An independent terminal model checks actual `TCAP TEXT` cells at zero-based row
4, column 9: ADM3A reverse, ANSI bold, VT52 plain. All control and text output
passes through BDOS and the selected personality/backend.

| State | Exclusive TPA ceiling |
| --- | --- |
| Cold boot, no RSXs | E101h |
| ANSISCRN alone | D601h |
| ANSISCRN + compact ADM3A | D201h |
| After ADM3A unload | D601h |
| ANSISCRN + compact ANSI | CE01h |
| After ANSI unload | D601h |
| ANSISCRN + compact VT52 | D201h |
| After VT52 unload | D601h |
| After final personality/backend unload | **E101h** |

A **57,344-byte COM** executes before loading and after complete unload. The exact
gateway address and maximum whole-record COM capacity return to their original
baseline. No permanent memory loss is observed.

The separate Z80 helper campaign passes 58 cases: copying without output, absent
and wrong-provider bindings, invalid magic/version/length/offsets, unterminated
strings, refusal after failed discovery, non-CRT route refusal, invalid
coordinates, decimal coordinates through 255, byte coordinates, emphasis/plain
fallback, stack balance and IX/IY preservation. These fixtures do not prove every
metadata or hardware behavior; the existing checked loader is reused.

[Guest receipt](evidence/tcap-compact-model/qualification.json) and
[CPU receipt](evidence/tcap-compact-model/cpu.json) record checks, sizes, binding
identity and hashes. No historical library code is included in this experiment.

## Private interface and limits

The second advertisement is **XTAB 0.1**, alongside MCON. Query A=0 returns HL
pointing to the read-only record, A=0; other selectors return A=255. IX/IY and SP
are preserved. No caller pointer is retained. Applications copy the bounded
record and reopen after layout/route changes. Matching Function 182 provider
indices establish that MCON and XTAB belong to the same current allocation.

The private record is 16–128 bytes:

| Offset | Meaning |
| ---: | --- |
| 0–1 | `TC` |
| 2 | Experimental table version 0 |
| 3 | Complete record length |
| 4–5 | Rows/columns, independently zero when unknown |
| 6 | Capability bits: clear=1, position=2, erase line=4, strong emphasis=8 |
| 7 | Emphasis choice: plain=0, bold=1, reverse=2 |
| 8–14 | Byte offsets for clear, position, erase line, strong begin/end, initialize/deinitialize |
| 15 | Reserved zero |
| 16 onward | Zero-terminated templates; offset zero means absent/empty |

Template bytes 1/2 format zero-based row/column plus 32; 3/4 format one-based
decimal row/column. Other nonzero bytes are literals. The generated tables use
tokens only in position templates. This private grammar is not historical Z3T
binary compatibility or a stable public ABI.

`TC_OPEN` returns 0 success, 1 unavailable, 2 malformed. `TC_EMIT` takes A=slot
0–6, B/C=zero-based coordinates and adds status 3 for invalid arguments. Empty
optional strings give plain fallback. The prototype supports CRT only and
ordinary synchronous transient calls. It does not promise nested style restoration,
takeover tokens, abandoned-session cleanup or physical host-size detection. ANSI
stream dimensions remain unknown; ADM3A/VT52 have their existing 80×24 viewport.

## Reproduction and remaining gates

Prepare and build an ordinary checked `cpmsim-fullram` workspace using the normal
build components, then choose a fresh experiment output directory:

```sh
build/tcap-feasibility/venv/bin/python tools/prototypes/tcap/zsystem_model.py \
  build/tcap-table-reference-01/profiles/cpmsim-fullram/z80pack \
  --output build/tcap-table-model-reproduce --qualify
build/tcap-feasibility/venv/bin/python tools/prototypes/tcap/zsystem_model_cpu.py \
  build/tcap-table-model-reproduce
```

The existing monitor-test environment, cross assembler, CP/M filesystem tools,
C compiler and local z80pack sources are required. The default cpmsim is the
pinned executable under `build/tcap-cpmsim-emulator/`; `--simulator` can select a
different qualified executable. The builder verifies the prepared workspace's
source closure and assembler before using its checked compatibility identity.
Only disposable disk copies receive private personalities and probes.

Next are the small public replacement contract, fuller route/geometry and
admission integration, actual package installation, then independent Model 4 and
Model II qualification. The 799-byte result establishes feasibility, not
completion of those gates.
