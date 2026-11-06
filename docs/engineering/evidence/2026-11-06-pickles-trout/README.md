# Pickles & Trout CP/M 2.2mH qualification

**PT2SS passes cpmsim RAM file interchange through the canonical Model II
adapter.** Three independent trials ran in parallel on private images. No BIOS,
BDOS, CONFIG or FDB implementation changes were needed. Model 4, ROM, physical
media, historical booting and formatting remain outside this qualification.

The previously downloaded `PT22MHA.IMD`, `PT22MHB.IMD` and `PTWORKDS.IMD` in
`~/Downloads/Pickles & Trout/` match the pinned upstream originals byte for byte.
The upstream README calls B the apparently better master copy. Both master
images and the archived work disk were tested; the user's generated
`PT-Working-Boot.IMD` was neither mounted nor modified.

| Original | Sequential files recovered | Probe bytes | Final block | Extra random read |
|---|---:|---:|---:|---|
| PT22MHA.IMD | 74 | 38,912 | 299 | MENU.COM record 256 |
| PT22MHB.IMD | 74 | 38,912 | 299 | MENU.COM record 256 |
| PTWORKDS.IMD | 74 | 40,960 | 299 | None needed |

The longest final worker took 12.404 seconds. The trials preserve original
directory entries, every recorded original extent, the 11,520 historical
reserved bytes, the 16,384 canonical reserved bytes, image bounds, IMD headers
and sector order. POSIX cpmtools independently checks extracted records and the
written filesystem. All five valid ATON/Lifeboat originals pass the updated
runner; the malformed sixth remains rejected.

[Sources](sources.json) · [Inspection](inspection.json) ·
[Guest results](cpmsim-results.json) · [ATON regression](aton-regression.json) ·
[Other checks](checks.json)

## Format evidence

All three images have 77 single-sided surfaces: C0/H0 is FM 26 × 128 bytes;
the remaining surfaces are MFM 16 × 512 bytes with IDs 1–16. The embedded DPB
in every image agrees with the provisional PT2SS entry from a-griff's Model II
port: SPT 64, BSH 4, BLM 15, EXM 0, DSM 299, DRM 127, AL0 C0h, AL1 00h,
CKS 32, OFF 2. Its 300 two-KiB allocation blocks occupy exactly the remaining
75 surfaces. Logical sector order is ascending ID, independently verified by
file extraction and the guest trials; physical interleave is retained in IMD.

The raw media stream is 625,920 bytes. Padding only the exceptional first
surface to an 8,192-byte slot yields a 630,784-byte canonical image, with the
directory at byte 16,384. The adapter reverses that representation and refuses
reserved-byte or padding changes. The FDF entry retains the required BOOT
extension; older readers and unsupported BIOS implementations cannot silently
bind it as ordinary uniform media.

## Master-disk record beyond sequential EOF

Both masters have MENU.COM extent 0 containing 128 records, extent 1 containing
27 records, and extent 2 containing one record. CP/M sequential reading stops
after 155 records (19,840 bytes); record 256 remains addressable by random I/O.
That record contains bytes 80h through FFh. The reason for its presence is
unknown; it is preserved without repair or reinterpretation.

The original test reader incorrectly concatenated all recorded extents, so its
expectation differed from COPY's correct sequential EOF behavior. The revised
reader keeps extent positions and treats sequential streams separately. The
simple contiguous-file helper now rejects this case rather than flattening it.
The runner checks record 256 with a read-only BDOS function 33 transient before
and after the probe write. A deliberately wrong expected byte must report
failure, proving that the check detects a mismatch. cpmtools output is compared
at each recorded extent's actual offset; bytes in unwritten gaps have no defined
file value and are not used as expected data.

This is a qualification-tool correction, not a change to CP/M EOF semantics.

## Use

Use the rebuilt RAM BIOS and matching CONFIG from PR632 or later. Convert a
private raw file with the shared adapter, then mount it as physical drive 1:

```sh
python3 docs/engineering/evidence/2026-11-06-model2/adapt.py \
  to-raw /path/to/PT22MHB.IMD /path/to/private.raw
```

Put SUPPDISK.FDB on the C work disk as DISK.FDB. In the guest:

```text
A:CONFIG /PHYSICAL=1 /TRACKS=77 /SIDES=1 /STEP=6
C:
A:CONFIG /LOGICAL=B /PHYSICAL=1 /FORMAT="Pickles & Trout M2 SS"
A:
DIR B:
```

Reconstruct a new IMD using the unchanged original template:

```sh
python3 docs/engineering/evidence/2026-11-06-model2/adapt.py \
  to-imd /path/to/PT22MHB.IMD /path/to/private.raw /path/to/written.IMD
```

Neither conversion overwrites an existing output. The original variable-length
raw stream cannot be mounted directly as the canonical cpmsim image.

## Reproduce

Run from the repository root, with the pinned originals, patched cpmsim,
POSIX cpmtools and z80asm at `~/bin/z80asm`. The System image and emulator hashes
are pinned in the guest receipt; the System was prepared for PR632 and is
unchanged here. Its preparation procedure is in the
[Model II guide](../2026-11-06-model2/INTERCHANGE.md).

```sh
python3 -B docs/engineering/evidence/2026-11-06-pickles-trout/inspect.py \
  --images /path/to/originals --output /path/to/inspection.json
python3 -B docs/engineering/evidence/2026-11-06-model2/qualify.py \
  --sources docs/engineering/evidence/2026-11-06-pickles-trout/sources.json \
  --images /path/to/originals --system /path/to/qualified-RAM-System.dsk \
  --catalogue docs/engineering/evidence/2026-11-06-pickles-trout/qualification-catalogue.FDF \
  --simulator /path/to/cpmsim --cpmtools /path/to/POSIX-cpmtools \
  --output /path/to/new-results --jobs 3
```

Each worker owns all four writable images. Read-back follows that worker's
write. M2WORK is a scratch definition only; PT2SS is the sole new supplemental
entry. The production 108-entry catalogue is unchanged.
