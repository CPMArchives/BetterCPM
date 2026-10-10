# Building the current BetterCP/M System Disks

The authoritative [manifest in progress](DISTRIBUTION-MANIFEST.md) selects disk
membership. `metadata/distribution.json` records its System Disk projection,
implementation status, target applicability, and user area. Planned PIP,
WHEREIS, and the full-screen editor are reported as omissions until integrated.
Utilities and CP/M Tools disks are not assembled by this first builder.

From the repository root:

```sh
python3 tools/build_distribution.py
python3 tools/build_distribution.py --target z80pack
python3 tools/build_distribution.py --target trs80gp
```

Prerequisites are those used by the existing build/qualification tools:
`~/bin/z80asm`, Python 3, cpmtools (`cpmcp`, `cpmls`, `fsck.cpm`), the qualified
cpmsim environment and its helpers, and trs80gp. `--simulator` and `--emulator`
override the existing local default paths. Model 4 launch uses the repository's
LaunchServices wrapper on macOS. The builder actually boots both targets;
there is no filesystem-only shortcut advertised as a boot-qualified release.

Each target is rebuilt from a private source snapshot using existing builders.
The current utility metadata needs common Model 4 artifacts even during a
cpmsim build; prerequisites are built inside that snapshot. Development build
artifacts and disks are untouched. Only freshly assembled system tracks are
retained from intermediate target images; the distribution filesystem starts
empty and receives the exact selected build artifacts. No utility, diagnostic,
or extension is selected by scanning development-disk contents.

The script lives at `tools/build_distribution.py`. After all requested targets
pass validation, it publishes these convenient image names:

- `build/trs80/BetterCPM-Distribution-trs80gp-80T-DS-System.dmk`
- `build/z80pack/disks/library/BetterCPM-Distribution-z80pack-332K.dsk`

These names are distinct from development images. Each named image is replaced
atomically from a checksum-verified temporary copy. Existing successful named
images remain intact when build or validation fails.

The same validated images and full evidence are retained in a new immutable
generation under `build/distribution/`:

- `z80pack/BetterCPM-Distribution-z80pack-332K.dsk`
- `trs80gp/BetterCPM-Distribution-trs80gp-80T-DS-System.dmk`

Each target directory includes `report.json`, the build log, directory listing,
filesystem check output, and boot transcript/screens. The report records source
revision/input hashes, manifest hash, included artifact hashes, target-specific
omissions, planned omissions, allocated/free capacity, tool/emulator hashes,
and validation results. The raw Model 4 intermediate is only a filesystem-tool
representation; the DMK carries the actual Model 4 system and boot tracks.

All requested targets must pass before a generation is published. Earlier
successful generations are never overwritten. A failed invocation reports the
failed command and leaves previous distributions intact. Choose `--work` to
retain isolated build logs and artifacts on failure:

```sh
python3 tools/build_distribution.py --work /tmp/bettercpm-dist-build
python3 tools/build_distribution.py --work /tmp/bettercpm-dist-build --reuse-work
```

`--reuse-work` accepts only a completed build whose source revision, input
hashes, assembler hash, and every cached artifact hash still match. It does not
select artifacts by timestamp or fall back to an old binary after build failure.
Use a fresh work directory after changing inputs or after an incomplete build.
Use `--output` to choose a separate publication directory.

`BYE` shuts down cpmsim and returns to the host shell. `BYE.COM` is included
only on the cpmsim distribution; it is not a Model 4 utility. The builder
verifies a real simulator exit before publishing that image.

Clock providers are available for explicit loading: `ZPRTC.RSX` on cpmsim and
`FREHDCLK.RSX` on Model 4. FreHD requires the relevant hardware/emulation;
shipping that provider does not make every Model 4 clock-capable. CPX/RSX
management includes its required file-backed runtime helpers. Optional P2DOS
and 104/105 clock adapters and test extensions are not selected. No on-disk
user documentation has been selected yet; host documentation remains here.

These are distributions of the current implemented state. They are not final
1.0 release candidates and do not replace the remaining conformance campaign
or the cpmsim reproducibility requirement.
