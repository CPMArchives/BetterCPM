# Engineering Specification 184: FDB v1 Reader and Validation

## Result

Implementation Step 4 now has an independent host-side reader for the compiled
FDB version-1 format. `tools/fdf_v1.py` reads an existing binary catalogue; it
does not rely on the serializer's in-memory `Format` objects or accept source
FDF text as proof that the binary representation is valid.

The reader validates complete-record length, the 65,408-byte envelope, signature
and major version, compatible fixed prefixes, descriptor-table arithmetic,
whole-file CRC, descriptor identities, duplicated sector counts, referenced
pool bounds and ownership, object overlap, zero gaps and padding, and the exact
last-record boundary. It rejects malformed sector-ID lists and TLV framing,
including repeated kinds, bad terminators, optional encodings of known semantic
extensions, and invalid mixed-sector or cylinder-track payloads.

Unknown optional extensions are skipped. An unknown required extension marks
only its descriptor unsupported and preserves its identity and description for
diagnostics; it does not invalidate other descriptors in a structurally valid
database. Known, supported descriptors are reconstructed through the same
semantic validator used by the compiler, so their DPB, geometry, topology,
allocation, and directory relationships are checked again from decoded bytes.

## Focused evidence

`tools/test_fdb_v1_reader.py` independently reads the qualified uniform,
mixed-sector, and cylinder-track fixture. Its negative mutations prove rejection
of CRC damage, undersized framing, duplicate-count disagreement, overlapping
pool objects, nonzero unowned bytes, arbitrary extra records, optional encoding
of a required semantic extension, and malformed assigned-extension payloads.

The test also proves that an unknown optional extension remains usable, an
unknown required extension makes only that descriptor unavailable, and a newer
minor version remains readable when its fixed prefixes and required semantics
remain compatible.

## Remaining Step 4 work

This increment establishes the binary-reader contract without changing CONFIG
or the active disk-state representation. Step 4 still requires migration and
qualification of the 107 admitted historical definitions while preserving the
five excluded reference records, native/catalogue packaging, CONFIG selection
through the normalized-binding transaction, and cross-platform disk evidence.
