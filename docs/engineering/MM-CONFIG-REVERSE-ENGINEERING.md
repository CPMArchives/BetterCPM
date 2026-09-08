# Montezuma Micro CONFIG: logical-drive limits

Examined 2026-09-08. This is static reverse engineering of the original
CONFIG.COM binaries, correlated with the recovered MM 2.32 BIOS source.
It is not a claim to have recovered CONFIG's original assembly source or
performed an emulator test of extra logical drives.

## Result

CONFIG 3.10 has a sixteen-letter display and derives its selectable range
from existing BIOS floppy definitions. It does not create definitions for
undefined logical drives. The supplied MM BIOS provides four floppy DPHs,
for A–D, plus an optional RAM disk at M. Its remaining pointer slots are zero.
Thus the A–D restriction follows from the BIOS's allocated structures; it is
not a hardcoded four-letter restriction in CONFIG G's input routine, nor
is it a consequence of having only four physical floppy drives.

The code establishes the mechanism. It does not establish the authors'
reason for allocating only four floppy definitions. Saving resident RAM
is plausible, but remains an inference.

## Binary evidence (CONFIG 3.10, COM addresses)

| Address | Behavior |
| --- | --- |
| 0152–015C | Copies eight BIOS jump vectors beginning at SELDSK into local stubs at 0B9F. The self-jumps in the on-disk binary are patched at startup. |
| 0740–0742 | Starts at letter A with a loop count of 16. All A–P entries are displayed. |
| 0758–0766 | Calls SELDSK for each logical drive. A null DPH displays “Undefined disk drive.” |
| 0768–0783 | Follows DPH+10 to the DPB. Zero at MM's extended DPB offset 20 takes the fixed-storage/hard-disk display path rather than the configurable-floppy path. |
| 078B–0796 | Records the first and last configurable floppy letters. |
| 07CA–07CF | Supplies last configurable letter + 1 as the input upper bound. With the supplied BIOS this is E, so A–D are accepted. |
| 0C17–0C1C | Common input routine checks A <= choice < supplied upper bound. There is no literal D limit here. |
| 07DF–07F7 | Rechecks SELDSK and the format identifier after selection. A null DPH or zero identifier returns to the list. This also rejects holes inside the allowed letter range. |
| 088B–08BA | Prompts for a physical drive and retrieves its definition pointer independently of the logical drive letter. |
| 08D4–08FF | Checks track/side compatibility with the selected physical drive. |
| 0901–0934 | Copies format parameters and translation data into the selected drive's existing DPB/XLT, and changes its physical-drive pointer. No new DPH is allocated. |

The last two paths also explain why different logical drives can share a
physical drive: each logical definition receives a physical-drive pointer.
There is no uniqueness check in this assignment path.

## BIOS corroboration

The recovered `mm232-bios.asm` has a sixteen-entry DPH pointer table:

```asm
; Existing MM BIOS allocation, reproduced here as a reference excerpt.
dph0ptr: dw dph0             ; A
 dph1ptr: dw dph1            ; B
 dph2ptr: dw dph2            ; C
 dph3ptr: dw dph3            ; D
         db 0,0,0,0,0,0,0,0 ; E-H
         db 0,0,0,0,0,0,0,0 ; I-L
 dph4ptr: dw 0               ; M; boot installs RAM-disk DPH if available
         db 0,0,0,0,0,0     ; N-P
```

Its SELDSK rejects numbers >=16, then indexes this table and returns its
pointer. Its four floppy DPHs each reference a DPB, translation table,
checksum vector and allocation vector. These are real resident allocations,
not merely letters that CONFIG can turn on. The recovered source locations
are SELDSK around line 1329, DPH definitions around 1993, and pointer table
around 2585. BOOT initializes A–D and conditionally installs M.

For BetterCP/M, this supports separating a sixteen-slot logical namespace
from allocation of active drive state. It does not prove that modifying
MM's pointer table alone would make its entire system support more drives;
all other consumers and buffer limits would also need checking.

## Retrieved files and provenance

The original distributions were already downloaded locally. CONFIG was
extracted afresh from each image using cpmtools, after decoding DMK sector
order and checking all 720 sectors' ID and data CRCs in each image.

- `CPMb232.dsk`: CONFIG **3.10**, matching the user's screenshots.
- `CPMb231.dsk`: CONFIG **3.01**, retained as a comparison binary.
- Both COM files are 12,928 bytes (including CP/M record padding).

Original archive sources:

- [MM 2.32 distribution](https://electrickery.hosting.philpem.me.uk/comp/trs80-4p/trs80Archives_cpm/cpmb232.zip)
- [MM 2.31 distribution](https://electrickery.hosting.philpem.me.uk/comp/trs80-4p/trs80Archives_cpm/cpmb231.zip)

Saved under `third_party/montezuma/`:

- `CONFIG-3.10.COM` and `CONFIG-3.01.COM`: original extracted binaries.
- `CONFIG-3.10-annotated.lst`: traced selection/assignment paths, with inline
  strings treated as data.
- `CONFIG-3.10-linear.lst` and `CONFIG-3.01-linear.lst`: complete raw linear
  decoder output. These deliberately retain code/data ambiguities; strings,
  menu vectors and format records must not be interpreted as executed code.
- `CONFIG-extraction-manifest.json`: source image and extracted file hashes.

The decoder was the installed z80pack `z80core/simdis.c` with a standalone
COM-loading wrapper, loading bytes at 0100H. The saved annotated listing is
an analysis aid, not a reassemblable source file. Original MM binary and
instruction material remains third-party reference material, not relicensed
under BetterCP/M's license.

Extraction geometry for cpmtools after sector reordering: 40 tracks,
18 sectors of 256 bytes, 2 reserved tracks, 2048-byte blocks, 128 directory
entries, skew 1, CP/M 2.2. Physical sector IDs are reordered as
1,3,5,7,9,11,13,15,17,2,4,6,8,10,12,14,16,18 before extraction.
