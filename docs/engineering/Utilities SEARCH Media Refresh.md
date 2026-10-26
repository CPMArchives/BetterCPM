# Utilities media refresh for SEARCH

**2026-10-27.** SEARCH adds one member to each primary Utilities image. The new
hashes are recorded in [SEARCH Utilities Acceptance](SEARCH%20Utilities%20Acceptance.md).
Historical receipts remain attached to their original image hashes; the new
receipts below record actual executions of the changed images.

| Component | Fresh checks on both new images | Retained coverage |
| --- | --- | --- |
| SEARCH | Native ZSM4/LINK parity, installed command, paging/stop, results/totals, DU scope, read-only fixtures and TPA/stack budget | Behavioral CPU suites rerun for the assigned executable |
| DDT | 26 simulator interactions and Model 4 debugger stages, G/T/U, operand cancellation, direct return and unchanged debuggee/Utilities | No historical placement result substituted |
| ZSM4/LINK | Macro/include, multi-module execution, rejected operand/unresolved external and six byte-identical codec builds; shipped System file audit and batch cleanup | No historical placement result substituted |
| TED | Fresh native builds and installed groups, interaction, large-file, recovery/API and capacity cases | Prior compiled/full-component coverage retained only for identical TED bytes and the identical System images |
| DASM/DSYM/DLINK | Fresh native parity, symbol conversion and five-byte reconstruction using packaged tools | Prior full-component coverage retained only for identical programs and the identical System images |

The [refresh receipts](utilities-search-refresh/) and their evidence archives bind
each fresh run to the new primary images. Retained full-component receipts are
identified by checksum and preserve their original media identities. The collector
refuses changed retained programs or System images; it never relabels an old run.
SEARCH and component packaging guards also reject changed program/image identities,
failed or missing platform results and stale native/corresponding source.

All 24 primary members pass independent byte, extent, allocation and padding
inspection. Selected Utilities volumes remain byte-identical after execution.
Work/System copies intentionally receive test files and native build outputs;
shipped System files are independently extracted and checked after the toolchain
runs. Nothing overwrites the original paired System images.

The separate NOAH companion images are byte-identical to their existing accepted
images. Their historical receipt and original System bindings are retained,
including their stated CLI/overlay scope; no fresh NOAH System-pair test is claimed.
The whole Utilities publication flag remains PROVISIONAL. This does not reopen
SEARCH implementation or its exact-pair acceptance, and it is not a public release.
Physical hardware, ROM/XIP and arbitrary BIOS/interrupt environments remain outside
these RAM emulator qualifications.

## Reproduction

Use absolute paths for media/campaign folders. The existing drivers are
`test_ddt_utilities_release.py`, `qualify_utilities_toolchain.py` plus
`audit_utilities_toolchain.py`, `qualify_ted_session.py`, `qualify_ted_editor.py`
for the separate simulator native build, and `qualify_dasm.py --from-utilities`.
Their `--system` root contains per-target System images and reports; the toolchain
audit needs the complete original file inventory in each System report.

`collect_utilities_media_refresh.py --campaign-map /path/to/campaigns.json
--output /path/to/receipts` requires the inventory path, per-target campaign
folders under `DDT`, `toolchain`, `TED`, `DASM`, and `TED-native-z80pack`. It validates
all required passing reports before producing the new exact-pair receipts and
checksummed evidence archives. Pass those receipts to `build_utilities_disk.py`
with its existing component acceptance options and `--search-acceptance`.

The final builder checks each receipt against the exact generated image, retains
source/license companions and bundles receipts/evidence in the host ZIP. Repeated
assembly must reproduce the tested image bytes; checksum lists and ZIP readback
verify the complete review package. No merge or public publication is performed.
