# 132 — PDS ABI Stage 1

Date: 2026-09-11  
Status: implemented static-layout bridge

## Scope

Stage 1 gives the existing 192-byte persistent region a versioned symbolic
interface without moving it, reducing history, or changing the TPA ceiling.
It deliberately does not implement allocation, configurable size, service
registration, or runtime expansion.

## Descriptor

The existing fixed Extension Control Block at `LY_SYS+080h` is the PDS ABI 1
descriptor and remains identified by `BM`, version 1. Flag bit 0 states that
the static PDS view is valid. Its `+08h` word, formerly described only as the
RSX lower boundary, is now canonically `ECB_PDSLOW`; `ECB_RSXLOW` remains an
internal compatibility label at the same address.

The Stage 1 view is:

| Property | Published value |
| --- | --- |
| Descriptor | `LY_PDSD = LY_SYS+080h` |
| ABI identity | `BM`, version 1, flag bit 0 |
| PDS upper boundary | `LY_PDST = LY_SYS` |
| Live lower boundary | word at `LY_PDSF = LY_SYS+088h` |
| Current size | `LY_PDST - (LY_PDSF)` |
| Configured boot size | equal to current size in this static stage |

`tools/system_layout.py` exports the equivalent derived values to builders and
tests. Consumers should use these symbols rather than new literal references to
`D504h` or `D5C4h`.

## Compatibility

The physical PDS remains `D504h–D5C3h`. Its ten-byte history control area and
182-byte record capacity are unchanged. The dynamic gateway remains at `D501h`
and the maximum complete-record COM size remains 54,272 bytes. Existing ECB
field offsets and version remain unchanged.

Later stages may extend discovery through a callable system service and replace
the static-size rule with explicit current and configured-size fields. Such an
extension must preserve the ABI 1 prefix or advance the descriptor version.
