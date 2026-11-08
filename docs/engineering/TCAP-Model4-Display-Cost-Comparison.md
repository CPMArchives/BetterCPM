# Model 4 ADM3A display-path memory comparison

Measured 8 November 2026. This closes the missing native-console component in
the earlier [Z-System capability-layer benchmark](TCAP-ZSystem-Benchmark.md).
The question is the cost of the core ADM3A display path, including capability
data, application routines and the code that interprets controls and renders
their effects. General RSX loading and ordinary console routing are excluded.
This does not claim identical complete VLIB/SCX feature sets.

## Result

| Required static component | BetterCP/M, Model 4 ADM3A | NZ-COM/Z-System, Montezuma 2.31 |
| --- | ---: | ---: |
| Screen backend and personality, including allocation rounding and descriptors | 2,560 | — |
| Native BIOS display engine, local state, control table and shared helpers | — | 445 |
| Full environment, including the 128-byte TCAP | Included in personality allocation | 256 |
| Application-linked capability routines and working data, including geometry | 777 | 613 |
| Shared BIOS cursor position/column state used by the backend | 3 | Included in native engine |
| **Total static bytes** | **3,340** | **1,314** |

Thus the current BetterCP/M ADM3A path occupies approximately **2.54 times** the
memory of the measured Z-System/Montezuma path for these core operations.
Removing BetterCP/M's three shared BIOS cursor bytes gives 3,337, with no material
change to that conclusion. Its resident portion is 2,563 bytes; the application
helper is another 777. The historical side has 701 resident bytes in this
accounting and 613 application bytes.

The earlier 857-byte number omitted the native console implementation and
geometry access. Adding the measured 445-byte native engine gives 1,302 bytes;
adding the 12 bytes for geometry gives **1,314**. The full 256-byte environment is
charged conservatively, although it also contains general Z-System information.

The 1,024-byte generic BetterCP/M RSX allocation is excluded at the maintainer's
direction. General NZ-COM command processing, virtual BIOS routing and generic
CP/M I/O dispatch are likewise excluded. Both totals exclude keyboard input,
the hardware framebuffer, application call sites and stack. The earlier original
VLIB CPU fixture observed 30 bytes of stack; the BetterCP/M helper fixture
observed 16, each excluding the platform BIOS's internal stack.

## Native console measurement

The actual unmodified `MMCPM231.DSK` supplied for the reference setup has SHA-256
`480cdf5dc504ad437448a27938241c81e45d91bab9c0073db738d11cabfb34aa`.
This measurement reads that original download, not the user's writable disk.

The output engine runs from EF48h through F0EEh inclusive: **423 bytes**, including
initialization, local state and the 32-byte control table. Its only external
direct CALL/JP targets are `clearmem` and `fillmem`. Their complete shared bodies,
ED28h through ED3Dh inclusive, add **22 bytes**. Both helpers are charged in full,
although other BIOS functions also use them. The next byte after the output
engine starts the separate printer-status routine.

Boundaries are identified using the read-only reconstructed MM 2.32 source in
the project reference archive. Assembling that section at the original addresses
and comparing every byte with the actual 2.31 disk finds exactly one difference:
the insert-line destination operand at F056h is 7Fh in the disk and 81h in the
reconstructed source. It does not change instruction lengths or boundaries.
Both shared helper bodies match the original disk byte for byte. This is a
binary-backed static measurement, not a new full-machine qualification campaign.
The original BIOS's role is also documented in the
[Montezuma programmer's guide](https://oldcomputers.dyndns.org/public/pub/manuals/montezuma_system_programmers_guide_trs80m4.pdf).

The [measurement receipt](evidence/tcap-public-integration/mm-console-comparison.json)
records input hashes, extraction anchors, boundaries, code hashes, the exact
source/binary difference and both totals. No third-party source or binary is
redistributed. Reproduce with the pinned local reference archive and disk:

```sh
python3 tools/prototypes/tcap/measure_mm_console.py
```

## Interpretation and limits

The 2,560-byte BetterCP/M allocation contains the 535-byte ADM3A payload and the
1,182-byte screen backend. The other **843 bytes** are descriptor allocation and
rounding: 512 bytes of descriptor pages, 30 bytes of runtime callable-service
records and 301 bytes of padding from rounding allocations to whole pages.
Those bytes consume TPA and are counted. The Montezuma code is packed inside its
existing BIOS rather than allocated as separate unloadable components.

BetterCP/M's backend also exposes additional SCRN/SCX operations. Charging its
whole required backend is appropriate for the current core TCAP path because
that is what must be loaded, but this does not prove equal coverage of every
operation. Its ability to switch ADM3A/ANSI/VT52 and unload is a separate
architectural benefit; the historical MM path measured here implements its
fixed ADM3A-style console and remains in the BIOS. No ANSI cost equivalence or
general minimum implementation size is established by this comparison.

The corrected conclusion is that the small public TCAP increment does not by
itself establish a comparably small usable display path. With the missing
Montezuma rendering code included, substantial BetterCP/M memory overhead remains.
