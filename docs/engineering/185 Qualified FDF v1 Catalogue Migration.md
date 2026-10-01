# Engineering Specification 185: Qualified FDF v1 Catalogue Migration

## Result

The retained Montezuma Micro corpus now has a deterministic, qualified FDF
version-1 migration in `metadata/DISK.FDF`. The migration reads the preserved
96-record `third_party/montezuma/DISK.FDF` grammar and the 16 definitions
recovered from CONFIG.COM. It does not alter either reference source.

Each admitted definition has a stable ID tied to its source and ordinal:
`MMF001` through `MMF096` identify old DISK.FDF records and `MMI001` through
`MMI016` identify internal CONFIG records. Gaps in the external series preserve
the positions of excluded evidence. Full historical names and source ordinals
remain comments. Display-name abbreviations are explicit in the migration tool;
no historical name is silently truncated to the FDB's 32-byte field.

The old option byte is translated field by field into encoding, sides,
inversion, traversal, and recorded-ID modes. Its derived double-step bit is not
copied. The four demonstrated SUPER formats receive the established five
1024-byte plus one 512-byte size map. Micro-Abacus receives the established
cylinder-track semantic extension. All other admitted DPB, geometry, and sector
ID values remain equal to their source records.

## Excluded evidence

`metadata/mm-fdf-exclusions.json` preserves the complete source parameters,
sector IDs, source ordinal, and rejection reason for the five records that fail
the frozen structural rules: Acorn SS, Eagle SS, Omikron Mapper II, Pied Piper
Executive, and Zenith H89 SD. Source hashes bind both the admitted output and
the exclusion record to the exact retained inputs. The migration does not
repair, renumber away, or publish these five definitions as supported.

## Focused evidence

`tools/test_mm_fdf_migration.py` regenerates both committed artifacts and
requires byte identity. It proves 112 source records, 107 admitted descriptors,
five exact exclusions, complete field preservation, four mixed-sector
normalizations, one cylinder-track normalization, unique IDs and descriptions,
and successful independent reading of the compiled catalogue.

The resulting FDB is 8,320 bytes, matching the design-stage measurement. Its
focused-test SHA-256 is
`4dea7bd989580fc13f61e79d47e92466a440799c41b002f4caba65ec8f893c03`;
this is reproducibility evidence, not part of the format ABI.

## Remaining Step 4 work

The catalogue is qualified source and host-compiled binary input; it is not yet
installed on a native disk and CONFIG does not yet consume it. Native/catalogue
packaging, CONFIG selection through the normalized-binding transaction, and
cross-platform disk evidence remain separate increments.
