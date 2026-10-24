# DDT selected-input and artifact records

This increment extends the PR #490 input pilot and the unpushed BYE build-record
integration to DDT. It does not alter version/revision assignments or executable
identification. DDT remains 1.0 (Build 002) pending the display migration.

The selected-input map covers the original DDT0MOV.ASM, DDT1ASM.ASM and
DDT2MON.ASM files; the translation and adaptation builder; DDT source/query/UI
includes; shared preparation code; and the selected registry identity. It also
records payload origins, bootstrap origin, parity flags and assembler bytes.
The original reference DDT.COM hash remains a separate report field, not an
executable source dependency. Third-party selected paths now receive the same
workspace containment checks as other selected sources.

DDT can be built with `--target z80pack` (default) or `--target trs80gp`. The
executable bytes are platform independent, but input records bind to the named
target so a reference from the other target is not silently reused. Prepared
checked contexts and native mode remain unsupported by this map. These are
cross-build receipts, not native parity or emulator qualification claims.

The existing DDT report retains all legacy fields, including translation and
relocation guards, and adds component identity, input record, explicit-reference
comparison, artifact identity and available Git provenance. Its existing PASS
status describes those build guards; an added qualification field explicitly
denies broader execution qualification. The older source_sha256 dictionary is
retained for compatibility and remains diagnostic; it is not the selected-input
fingerprint and still contains the full legacy utility TSV hash.

Inputs are captured before and after assembly. A race refuses report emission;
an old report is removed before rebuilding. Output bytes are checked before
report generation, and installation into build/utilities happens only after
these checks. Concurrent builds must use isolated output directories. Failed
attempts may leave diagnostic binaries/listings but never an old success report.

`--baseline FILE` accepts the raw `input_record` object from a prior report.
It never advances counters, accepts a publication baseline, or relabels existing
artifacts. Missing/invalid references report unknown; identical explicit
references report unchanged; changed selected inputs report development. No
`-dev` title is embedded in this increment. Missing Git provenance is null,
not a claim that the reconstruction's source matches a committed checkout.

Four DDT tests use the real host assembler for artifact binding, repeated builds,
reference comparison, target-bound records and race refusal. Copied-fixture
tests also mutate each original assembly source and a selected UI include.
Together with BYE integration, input selection and registry tests, 28 tests pass.
Legacy registry projections remain unchanged. Old/new default DDT and BYE
binaries are compared byte for byte; checked compatibility hashes remain subject
to the previously documented broad metadata/tool closure.

```sh
python3 tools/test_ddt_build_record.py
python3 tools/build_ddt.py --target trs80gp --no-install --output OUTPUT
```

Remaining versioning work includes input maps for the other components, generated
linkage/native inputs, checked-contract dependency refinement, explicit revision
acceptance with executable comparison, the common numeric revision/development
display, unresolved RCP/MOVE/WARM migration, and artifact-driven disk manifests.
