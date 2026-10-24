# Checked cpmsim package and utility integration

Date: 24 October 2026. This bounded normal-build checkpoint follows
[direct carrier generation](CPMSIM-CARRIER-INTEGRATION.md), reconciled with
merged main `2023d895e3ee21a58571df44afec69f83e3006c0` (including PR #478).
Core 1.0 remains frozen at `3b2d2d7`.

## Result and scope

The maintained builders now compose the checked 160-record RAM system payload,
its 161-record BCSY2 SYSTEM.SYS package and the matching CONFIG, SYSGEN and STAT
utilities. Selected conditional assembly replaces the assessment-time source
patches. The cpmsim package builder consumes artifacts and verified build receipts
from the existing resident and carrier builders.
It constructs component files only; complete distribution media and live
installation/recovery acceptance remain the final integration stage.

`build_checked_package.py` assembles the cpmsim bootstrap, composes the resident
and raw command/RSX carriers, then generates the package contract and installer
admission code from those exact bytes. It verifies the prepared source identity,
assembler, resident/component receipts and module hashes before composition.
The resident builder now records BDOS, file-loader and both command-stage
carrier hashes as upstream inputs. Changed upstream carriers, foreign/stale
package guards and modified generated guard inputs are rejected. The ordinary
`build_system_package.py` command delegates selected checked builds to this
builder; its legacy `compose()` API refuses a checked context.

The selected SYSGEN understands BCSY2 and validates package identity, header and
payload CRCs, normalized system bytes, saved A: binding and destination RCP.CPX
and R3PACK.RSX before installation. Disk-to-file export validates the buffered
system and reconstructs the saved binding, build identity and CRC fields.
Only the declared CONFIG/SYSGEN-owned editable fields are normalized: startup,
physical definitions, logical bindings and cold IOBYTE. Normalization restores
the buffered payload on both success and failure.

CONFIG and SYSGEN check page-zero WBOOT opcode and BIOS base, then the complete
private build ID, before accessing compiled private addresses. STAT applies
that gate to MEM; its ordinary documented-BDOS operations remain public.
Standalone CLS resolves the current host's MONCALL vector from WBOOT. Checked
SYSBUILD, RESPACK and RLMBUILD explicitly refuse operation because their native
writers still emit the earlier formats. Their version queries remain available.
Checked utility banners use the build identity rather than incrementing a
released utility build number.

Checked CONFIG contains only its selected cpmsim resident and IOBYTE descriptors;
it does not depend on intermediate Model 4 products. Its 15,561-byte program
ends 55 bytes below the existing private stack reservation at 3E00h. The stack
reservation itself is unchanged. No resident allocation or TPA cost is added.
HELLO and STATEFUL remain development fixtures excluded from distribution.

## Verification

| Component checks | Full RAM | Legacy checked |
|---|---:|---:|
| Package, installer/export and generated-input cases | 32 | 32 |
| Utility gates, entry-stack cases and public CLS dispatch | 69 | 69 |
| Resident, reader, carrier and command-stage regressions | 537 | 537 |

The package campaign exercises matching/foreign packages, old formats, truncated
and extra records, header/binding/payload corruption, resealed foreign IDs and
changed boot/stage/CCP/private bytes. Open, header-read, payload-read and close
failures are injected. The assembled LOADFILE routine performs no destination
activity during these refusal cases. Required destination files must match;
missing or foreign files fail with the caller's user number restored. Both
matching and edited exports run the native XHEADER/P11HEAD helpers and validate
the resulting package, preserving the payload. Host builder refusal cases cover
changed package metadata, generated assembly, upstream stage carrier and legacy
package composition under a checked context.

The utility campaign covers each private ID byte and wrong WBOOT opcode/base,
with no private-ID read when the vector does not match. It measures the actual
entry path before the private stack, checks CONFIG's long/quoted tails, executes
all three disabled native writers and exercises both local and foreign CLS
against the current host vector. These are component tests with controlled I/O;
they do not establish a new live checked-OS installation or whole-OS stack bound.
The earlier two-byte BDOS stack margin remains a limit to track.

The two layouts plus 11 profile/contract and 13 distribution unit tests total
1,300 counted cases. Default regression campaigns additionally pass 250 utility
identity/query cases, 10 package admission cases, 24 export cases, 32 SYSGEN
command-line cases and the version/pre-private-stack campaign. The latter
observes 24 of 32 available bytes in its tested default entry paths.

The ordinary default cpmsim distribution passes filesystem, file-integrity,
CONFIG fingerprint and simulator boot checks. Its 30-file disk image and eight
affected utilities are byte-identical to a separately built main `2023d895`
baseline. Its image SHA256 is
`75e0ae5e15972fc92579fe3924a28c9d32c7e23cc6431bd932b54ef0841a9c13`.
This baseline includes the newly merged utility-query/compression/NOAH changes;
it is not the earlier pre-merge disk. The common-builder Model 4 development
image also remains byte-identical. No new Model 4 live-boot or complete Model 4
distribution qualification is claimed.

The [machine-readable evidence](CPMSIM-PACKAGE-UTILITY-INTEGRATION.json) retains
source input hashes, build IDs, emitted artifact hashes, per-case results,
repeat-build comparisons, cache validation and default regression results.
Build identities are:

- Full RAM: `2fd0f3f5a3cb273ccc2a386c38e5d90d`.
- Legacy checked: `0d416223caaec55cb7378be0131bddcf`.

## Reproduction and final stage

Prepare fresh workspaces for both profiles with
`build_distribution.py --target z80pack --profile PROFILE --prepare-profile
--work WORK`, then run from each prepared directory:

```sh
export BETTERCPM_BUILD_CONTEXT="$PWD/build/profile/context.json"
python3 tools/build_checked_resident_rsx.py
python3 tools/build_checked_carriers.py
python3 tools/build_checked_package.py
python3 tools/test_checked_packages.py "$PWD" /path/to/other-prepared-profile --output "$PWD/build/package-tests"
python3 tools/test_checked_utilities.py "$PWD" /path/to/other-prepared-profile --output "$PWD/build/utility-tests"
```

Build both layouts before running foreign-profile tests. Run mutation tests
sequentially with other consumers of their generated artifacts. Repeat package
and utility generation must preserve all recorded hashes. Prepared-cache reuse
must still verify the source closure.

The remaining planned stage is complete checked distribution integration and
acceptance for both cpmsim layouts: manifest-selected media construction,
publication/cache handling, boot, application/RSX lifecycle, installation/export
and recovery campaigns. Full-distribution guards remain until that work passes.
Model 4 memory reclamation, ROM/XIP and native checked packaging remain separate
roadmap work, not prerequisites for closing cpmsim integration.
