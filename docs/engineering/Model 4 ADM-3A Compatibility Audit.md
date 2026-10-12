# Model 4 Montezuma terminal compatibility audit

Audited 2026-10-12. Read-only feasibility audit; no production console, layout,
BDOS or BIOS behavior was changed.

## Conclusion

MM-compatible Model 4 console output is a worthwhile platform compatibility
target, but it cannot be appended to the present BIOS allocation. A bounded
resident-space decision and explicit control-code migration are required before
implementation. This does not require a general terminal-capability service.

## Evidence and provenance

The project reference `sources/mmcpm232.zip` contains `mmcpm232/bios.asm`, a
reconstructed MM 2.32 BIOS listing. It was read without modifying the synced
archive. Its `conoutcrt`, `outputchar`, `escseq`, control handlers and
`ctrlcodetable` establish the implemented behavior. This reconstructed source
is evidence alongside the original programmer's guide; it is not proof that
every MM release behaved identically.

The [MM programmer's guide](https://oldcomputers.dyndns.org/public/pub/manuals/montezuma_system_programmers_guide_trs80m4.pdf)
identifies the video driver as ADM-3A emulation and describes escape-parser and
video state. Direct retrieval currently redirects to a login, so the source
archive provides the inspectable detailed behavior for this audit.

## Current memory measurement

A fresh `tools/build_bios.py` build emits 636 bytes in the 638-byte BIOS region
EA08h–EC85h: **2 bytes free**. SHA-256:
`e418765150836c98d9e344d698e0b175636c9b31f3c2c47b1c0b70f7723215b1`.

Other current emitted components have no usable adjacent reserve: gateway
248/248, BDOS 3555/3555, disk 960/960, file loader 145/145 and tables 576/576.
Extension services have one spare byte (424/425). These are measured component
sizes, not a claim that every private workspace byte is spare or interchangeable.
No spare area sufficient for terminal emulation was established.

## MM output contract observed in the reference

- ESC `=` row+20h column+20h positions the cursor; values outside the supported
  range clamp to row 23 / column 79 after unsigned subtraction.
- ESC `0` hides and ESC `1` enables the cursor; unrecognized escape selectors
  reset parser state without printing the selector.
- 07h bell; 08h backspace (crosses to preceding row when needed); 09h tab;
  0Ah down/scroll; 0Bh up; 0Ch right; 0Dh carriage return.
- 15h/18h clear to end of line; 17h/19h clear to end of screen;
  1Ah clear screen and home; 1Eh home.
- 1Ch insert line; 1Dh delete line.
- 0Eh disables reverse video; 0Fh and 16h toggle reverse video.
  The recovered 0Fh routine toggles despite its descriptive comment saying on:
  confirm against the selected MM binary before promising this edge behavior.
- Other low controls have zero handler entries and are ignored.

Current BetterCP/M scroll output explicitly handles backspace and 1Ch clear/home,
with CR/LF in the compact leaf. It has no ESC addressing parser. MM's 1Ch insert
line conflicts with BetterCP/M's existing clear/home convention. Backspace at
column zero and unsupported-control rendering also differ.

## Cost assessment

The recovered complete MM video slice, from `conoutcrt` through `cursorflag`,
assembles to **423 bytes**, including its control table and seven state bytes.
This is an isolated reference measurement, not a drop-in BetterCP/M implementation
or a qualified final growth estimate. External fill/initialization helpers and
platform differences must also be accounted for. No recovered code was installed.

The reference escape parser alone occupies 57 bytes, excluding dispatch,
coordinate-address calculation, cursor visibility support and retained state.
It already exceeds the two-byte gap by a large margin. Minimal addressing/home/
clear support should be budgeted at roughly 100–150 additional bytes pending a
prototype. A fuller MM-compatible implementation merits a provisional 256–384
byte growth budget after reuse of existing scroll/CR/LF code; this is an estimate,
not a measured optimized implementation.

Additional retained parser state is needed (escape phase and pending row); MM
also has reverse-video and cursor state. Existing keyboard state cannot be borrowed:
output sequences may span calls while keyboard operations continue.

No BDOS code growth, public-vector additions, CPX changes or TCAP mechanism are
needed. Resident BIOS growth is nevertheless real and must be paid for by proven
code savings or a deliberate packed-layout adjustment. Reclaimable CCP space does
not solve permanent BIOS storage. Without other savings, expanding the protected
resident span reduces TPA. Do not assume a specific TPA cost until a prototype and
whole-system layout build establish it.

## Recommended bounded implementation gate

1. Freeze MM 2.32 console-output compatibility as the platform target and resolve
   the 1Ch migration. Audit CLS, console tests and applications using clear/home;
   use MM 1Ah clear/home and 1Eh home where appropriate.
2. Prototype the output state machine in an isolated build and measure its net
   code/state increase. Preserve bootstrap consoles separately; only resident
   output needs the complete contract.
3. Choose proven savings or an explicit layout budget. Keep BDOS byte count
   unchanged; rebuild every dependent resident/boot artifact if addresses move.
4. Qualify addressing corners/clamping, escape interruption/reset, all controls,
   line operations, cursor visibility/reverse video, scrolling, keyboard behavior,
   BDOS console paths and cold/warm reconstruction. Compare boundary cases with
   the MM binary and test an ADM-3A-configured application on real emulator disks.
5. Only then advertise the Model 4 monitor and VIEW profile as MM/ADM-3A-compatible.
   Generic VT52 is a parallel system-monitor target, not merely a utility choice;
   see the [bounded memory review](Bounded%20Monitor%20Memory%20and%20Efficiency%20Review.md)
   for separate and shared profile samples and host-terminal limitations.

Recommendation: proceed with this bounded compatibility work if a few hundred
resident bytes are acceptable. It is technically straightforward state-machine
work, but not a two-byte patch and not layout-neutral in the current build.
