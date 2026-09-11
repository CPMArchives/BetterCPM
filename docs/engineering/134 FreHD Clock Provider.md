# Engineering Specification 134: FreHD Clock Provider

## Status

First provider increment implemented. Central BRSX-v2 registry publication is
still a Stage-2 dependency.

## Hardware contract

`FREHDCLK.RSX` implements BetterCP/M `TIME` ABI 1.0 using FreHD's documented
extended interface:

| Port | Use |
|---:|---|
| `C2h` | extended data |
| `C3h` | returned data size |
| `C4h` | extended command |
| `CFh` | controller status |

Extended command 1 returns six binary bytes in second, minute, hour, two-digit
year, day, month order. The FreHD firmware copies those fields atomically from
its DS1307 shadow state before exposing them, so one successful six-byte
transfer is a coherent sample. The provider validates all fields, interprets
the DS1307 year as 2000 through 2099, converts the date to the CP/M epoch, and
returns packed-BCD time. It never changes the hardware clock and advertises no
SET capability.

On the Model 4 the provider enables the `EXTIO` latch before addressing the
FreHD extended ports. This is required even when trs80gp's FreHD emulation is
enabled; without it the extended port block is deliberately invisible.

The same interface is emulated by trs80gp when FreHD support is enabled. The
provider is named for FreHD because the ABI does not depend on trs80gp.

## Discovery transition

`TIME.COM` uses only Resident Service Function 208 and `TIME` ABI 1.0. It has no
FreHD port knowledge. `TIME /PROVIDER` also asks the RSX manager for the current
provider stem and reports the discovered ABI and capabilities.

The current v1 carrier temporarily intercepts Function 208 and publishes its
own sole `TIME` service. This is a bring-up bridge necessitated by the full
fixed-core regions. Stage 2 replaces it with the central registry resolver in
the existing one-kilobyte RSX-manager slot. Function 202 reloads reconstruction
code before a profile change; while the profile is active, that slot can hold
the resolver. The public utility and provider-call ABI do not change.

## Artifacts

- `build/rsx/FREHDCLK.RSX`
- `build/utilities/TIME.COM`
- the standard generated TRS-80 boot disk, which contains both files but does
  not load the optional provider automatically

Operator sequence:

```text
RSX LOAD FREHDCLK
TIME
TIME /PROVIDER
```

Absence, controller timeout, error status, malformed samples, impossible dates,
and unsupported SET requests return defined errors rather than fabricated time.
