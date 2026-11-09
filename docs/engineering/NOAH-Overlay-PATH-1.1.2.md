# NOAH overlay PATH maintenance fix

Target: BetterCP/M v1.1.2. Classification: maintenance/integration bug fix.
Status: implemented, focused checks passed and maintainer authorized v1.1.2
publication, 9 November 2026. NOAH identification revision: 1.0 (021).

## Cause and correction

The production loader in `src/utilities/common/noahresident.inc` previously
opened `NOAH.OVL` in the captured invocation drive/user and then hard-coded A0.
It never consulted the configured PATH. BDOS Open remains an exact-directory
operation; the CCP's successful PATH lookup of `NOAH.COM` does not extend it.

The loader now searches the invocation drive/user first, followed by the live
system PATH in order. Symbolic drive 0 and user FFh resolve against the captured
invocation directory, including after a previous candidate changed the selected
user. Entries resolving to the invocation directory are skipped after its first
search. All FCB scratch is cleared before each attempt. Count zero selects the
standard current-directory/A0 policy; an explicit list receives no extra A0
entry. Unsupported systems retain the historical current-directory/A0 fallback.
Malformed live counts or entries stop the search rather than reading past the
six-entry allocation or selecting an invalid user.

The existing layout contract is used read-only. As with PATH.COM, admission
requires a known BIOS WBOOT vector, the BM version-1 descriptor and symbolic
PATH capability bit 2. The universal NOAH binary contains the three supported
layout tuples, generated from the canonical layout and existing build profiles;
there are no independently maintained absolute addresses in production source.
This introduces no CCP/kernel change, service, separate PATH setting, resident
allocation, or dependency on experimental 1.2 facilities.

Inspection of the CCP's loader/handoff and the published ECB/PATH contracts
found no established executable-load-directory interface or general companion
file resolver. The CCP retains private loader state but does not publish it to
NOAH as such an interface. The approved current-directory/PATH policy therefore
applies; overlay lookup does not infer an executable location from default FCBs.

Only an unsuccessful Open (FFh, CP/M's absent/unopenable result) advances the
search. After any successful Open, header, ABI/build identity, bounds, complete
length, read and CRC validation failures stop immediately. No later overlay is
tried. Existing validation still runs on every phase reload. Distinct messages
report `NOAH.OVL not found` and `NOAH.OVL invalid or incompatible`, both followed
by `operation stopped`. Caller drive/user and default DMA are restored on both
success and failure. Existing transaction recovery and companion overwrite
protection remain in place.

Install the updated NOAH.COM and its matching NOAH.OVL as a pair, as before.
The existing build-identity validation intentionally rejects mixed versions.
The NOAH distribution note and main specification describe the corrected policy.

## Focused verification

| Check | Result |
| --- | --- |
| `python3 tools/test_noah_path.py` | 36 production-binary Z80 cases passed: all three layouts, current/first/later/missing overlays, invalid current/PATH copies before valid copies, header/build/index/length/CRC errors, read failure, six entries, dynamic fields, default/unsupported/malformed state, dirty failed-Open FCB scratch, codec reloads, LBR/ARC listing/extraction, ARC creation and queries. Drive/user/DMA and seeded system memory preserved. |
| Same regression with original loader/build source restored temporarily | Failed at the first remote PATH case with the original unavailable/invalid error; modified source restored afterward. |
| `test_noah_codecs.tests(machine())` | 51 existing codec/overlay transaction cases passed; maximum intercepted stack 54 bytes. |
| `test_noah_write.tests(machine())` | 38 existing LBR-write CLI/transaction cases passed. |
| `tools/test_noah_path_cpm.py` on published v1.1.1 cpmsim System image | Nine real CCP/BDOS cases passed: current, remote, missing, invalid PATH before valid, invalid current before valid, cross-user launch, ARC listing/extraction, cross-user codec reload/output readback. Returned to A0/A7 as appropriate. |

The guest harness copies the System image and creates scratch B/C/D images;
it removes ED.COM and FDB.COM only from the disposable A copy to make room for
fixtures. It does not alter the input media. Guest input was extracted from the
local published `BetterCPM-1.1.1-System-cpmsim.zip`, not an experimental 1.2 disk.

Reproduce the guest check with:

```sh
python3 tools/test_noah_path_cpm.py \
  --system-image /path/to/BetterCPM-Distribution-z80pack-332K.dsk \
  --diskdefs /path/to/diskdefs \
  --simulator /path/to/patched/cpmsim \
  --output build/noah-path-guest-new
```

These are focused utility checks. Model 4 and Model II layout admission was
executed on the Z80 core with modeled BDOS, not as new hardware/emulator media
qualification. The maintenance release branch starts directly at the published v1.1.1 tag;
only this fix and its publication files are added. Release packaging verifies
exact binary identity and disk-file readback without another engineering campaign.
