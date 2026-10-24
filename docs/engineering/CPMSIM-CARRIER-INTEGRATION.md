# Checked cpmsim direct-carrier integration

Date: 24 October 2026. Bounded normal-build integration checkpoint following
[resident services and reconstruction](CPMSIM-RESIDENT-RSX-INTEGRATION.md).
Core 1.0 remains the frozen `3b2d2d7` baseline.

## Result and scope

The ordinary RSX, CCP and CPX builders now construct the qualified checked
carrier formats when selected through a verified prepared-profile context.
They no longer require assessment-time conversion or instruction patching.
Default builds retain their existing formats and bytes. Full checked
package/install/export, private utility guards and distribution acceptance
remain pending; the full-distribution guards are still enforced.

`checked_carriers.py` supplies the binding policy and prepared-input identity.
BRSX3 carries BMET2 metadata with a mandatory first binding record. BCM2 and
BCPX2 carry the schema-2 public/private identity trailer and whole-carrier
CRC16/CCITT-FALSE. Existing relocation, payload checksum, runtime descriptor
and allocation calculations remain unchanged. Binding metadata adds 20 bytes
per RSX file and command trailers add 22 bytes per command carrier; these are
file overhead, not additional resident allocations.

Bindings come from the verified source closure, selected layout/profile flags
and assembler hash. The common assembly helper verifies the actual assembler
before emitting code under a checked context. Unknown checked module names
and unsupported hardware modules fail admission to the builder policy.
The Model 4 screen backend is omitted from the selected cpmsim screen build;
the ANSI host screen backend builds without requiring a Model 4 BIOS listing.

`build_checked_carriers.py` invokes ordinary builders for the CCP, RCP and HELLO
CPX modules and twelve supported RSX modules, including BATCHIO. This is a
component driver, not distribution selection. HELLO.RSX, HELLO.CPX and
STATEFUL.RSX remain development fixtures excluded from distribution.
M4SCRN and FREHDCLK are not emitted by this cpmsim component driver. Optional
104/105 frontends and custom monitor templates are not newly qualified here.

## Verification

| Check | Full RAM | Legacy checked |
|---|---:|---:|
| Carriers identical to qualified reference with reference identity | 15 | 15 |
| Real command carrier streaming cases | 12 | 12 |
| Real RSX native admission/metadata cases | 24 | 24 |
| Unsupported/unknown module policy denials | 4 | 4 |
| Existing resident, reader and command-stage cases | 537 | 537 |
| Repeat carrier artifacts identical | 15 | 15 |

The real command cases cover local and foreign-profile CCP, RCP and public
HELLO CPX, each with intact and damaged CRC. Successful loads reproduce the
independently relocated complete payload and allocation boundary; failures
retain the boundary. Real RSX cases exercise the emitted carrier and metadata
validators with resident identity services for local and foreign copies of all
twelve modules. Private foreign carriers are rejected without publishing facts;
public ECHO and HELLO remain portable. These are controlled component tests,
not a new live whole-OS transaction or stack campaign.

The existing synthetic command fixtures now construct their BCPX header
independently of the production builder, avoiding accidental double binding.
The resident carrier fixture consumes directly generated checked RSX records.
Both profiles still reproduce the earlier resident and streaming-stage code.

Together with 11 profile/contract and 13 distribution unit tests, the checks
comprise 1,178 counted cases. Existing default RSX carrier and runtime-overlay
campaigns also pass. Rebuilding the ordinary default cpmsim distribution passes
filesystem, file integrity, CONFIG fingerprint and live simulator boot checks.
Its 30-file, 368,640-byte image is unchanged:
`d806fa1911fa18623f9d7495d561cae57d6623bb66fbe68e85f3b355a866ee96`.
Seventeen default RSX/CCP/CPX carriers, including the hardware-specific carriers,
are byte-identical to the preceding checkpoint. No new Model 4 distribution or
live-boot qualification is claimed.

The [machine-readable evidence](CPMSIM-CARRIER-INTEGRATION.json) records the
1,096-file input closure, build identities, artifact hashes, per-case results,
repeat comparisons and default checks. Tests use `d40c1d9` plus the exact
recorded working-tree bytes preserved by this checkpoint commit. Build IDs:

- Full RAM: `1da73608d97e4662621614b3a906a8cc`.
- Legacy checked: `35233499dabb98b5bbc188259128cadd`.

No runtime allocation or TPA change is introduced. The previously measured
two-byte BDOS stack margin remains a limit; this checkpoint does not establish
a new whole-OS stack bound.

## Reproduction and next increment

Prepare fresh workspaces for both checked profiles with
`build_distribution.py --target z80pack --profile PROFILE --prepare-profile
--work WORK`, then run from each prepared profile directory:

```sh
export BETTERCPM_BUILD_CONTEXT="$PWD/build/profile/context.json"
python3 tools/build_checked_resident_rsx.py
python3 tools/build_checked_carriers.py
python3 tools/test_checked_carriers.py --reference /path/to/matching-reference-profile --foreign /path/to/other-prepared-profile --output "$PWD/build/carrier-qualification.json"
```

Build both profiles before cross-profile testing. The frozen reference profile
is comparison evidence only. Run the existing resident/RSX and command-stage
qualifiers for their regression cases. Repeating the carrier driver must retain
all fifteen artifact hashes; prepared-cache reuse must still verify the closure.

The next bounded increment is checked package/install/export integration and
private utility guards. Complete checked distribution construction and
acceptance follows separately.
