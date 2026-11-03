# Model 4 CAPS native diagnosis

Status: one native single-press sequence passes; earlier host-key observations
remain unresolved, 2026-11-03. This is a
follow-up to `Model4-Lowercase-First-Draft.md`. Production BIOS source and
its 757-byte allocation remain unchanged from `37fa57a`.

## Evidence so far

The maintainer's tests show that the draft boots, accepts lowercase and shifted
uppercase, and executes lowercase CCP commands without a terminal RSX loaded.
Software-keyboard CAPS changes case. Switching to physical keyboard input was
reported to clear the software CAPS key and return to lowercase. After restoring
the macOS Caps Lock key assignment, case switching works but is reported to
require two physical presses. These observations do not establish the event
sequence delivered to the BIOS.

One native capture from the first standalone launcher was inspected. It timed
out after 1800 seconds, with 114 events, including 30 keyboard events. The keyboard
events comprise the automatically typed KEYREAD command. There are no CAPS
press/release events. This proves neither that the probe reached its screen nor
that physical input was delivered to that instance. It is not a passing CAPS test.

An earlier launcher was incorrectly distributed without its Python companion.
The replacement embedded its Python code and disk, but still relied on timed
KEYREAD typing and a temporary application wrapper. There is no evidence that
either launch mechanism caused the CAPS symptom.

## Diagnostic that starts at boot

Run `python3 -B tools/prepare_model4_caps_diagnostic.py` after building the draft.
It uses the existing manual test disk when available, otherwise the development
boot image. `--image` selects another Model 4 boot disk containing the same exact
BIOS. The builder checks that BIOS before preparing private diagnostic media.

The resulting `Caps-Monitor-37fa57a.dmk` has a saved startup command of CAPTRACE.
The single-file `Run-Caps-Monitor.command` embeds that disk and requests a new
Model 4 instance through the installed emulator's real application bundle. It
does not depend on adjacent scripts, repository paths, a temporary bundle,
timed command typing, or an emulator process staying open until a Python timeout.
The builder does not launch an emulator.

CAPTRACE uses the real public BIOS CONST and CONIN entries. It logs each returned
character, even if it equals the preceding one, and changes in these values:

| Column | Meaning |
|---|---|
| RAW | F480h modifier register, sampled after the BIOS call; bit 08h is CAPS |
| STATE | Read-only view of the draft's guarded CAPS state byte at EBBFh |
| LAST-BYTE | Last actual public CONIN return, in hex; initially `--` |

STATE 20h/28h selects lowercase; 00h/08h selects uppercase. Bit 3 records the
confirmed CAPS contact. The low-level values are samples, not a continuous bus
trace. CONIN can block until an ordinary key is released. The last byte remains
visible on state-only rows, and screen rows wrap after 19 records. Ctrl-C exits
through warm boot.

The program checks WBOOT and the draft scanner signature before reading private
state. A different BIOS produces a visible mismatch message and exits. It writes
only its TPA storage and video RAM; it does not patch the driver or its CAPS byte.
An independent readback checks its installed COM bytes, filesystem allocation,
startup record, and preservation of reserved-system bytes outside that record.

## Controlled results and their limits

The builder cross-assembles and executes the monitor together with the production
BIOS in the bounded instruction runner. It checks two input models:

| Supplied contact model | Returned A-key bytes |
|---|---|
| Each CAPS actuation supplies a complete press/release | 61, 41, 61, 41, 61 |
| Successive actuations alternate a maintained contact between down and up | 41, 41, 61, 61 |

The second controlled model reproduces an apparent two-actuations-per-case-change
pattern while preserving the driver's intended one-toggle-per-confirmed-press
rule. This makes a latched contact a plausible explanation. It does **not** prove
that macOS or trs80gp supplies that contact model. A missed or insufficiently
confirmed release is another possibility; native data must decide.

The wrong-BIOS guard, repeated-character logging, Ctrl-C exit, single-file
relocation, embedded disk checksum, and explicit Model 4 launch request are
checked. The app-launch API is mocked for the request check; no native result
is inferred from it. Generated `report.json` records the exact COM/image hashes
and leaves native input qualification pending.

## Native capture — 13:33 run

The maintainer ran the new diagnostic image, SHA-256
`26f119878a2631e1ebc9400bb551b5f7315a29e929a565e6fb2c2f34682b651b`.
The screenshot shows actual LAST-BYTE changes `61,41,61,41,61`. The matching
capture folder's event log contains five A-key presses/releases and four CAPS
presses/releases. After the first A-key actuation, each round is exactly:

```text
k731   CAPS contact down
k011   A contact down
k730   CAPS contact up
k010   A contact up
```

That sequence repeats four times. Each CAPS press changed the subsequent A-key
return once. The two-press requirement was not reproduced in this run. In
particular, the log rules out a maintained contact spanning alternate CAPS
actuations for these four rounds. The emulated release occurs when ordinary
typing resumes, rather than appearing as a separate event before A goes down.

Brief screen rows with a different RAW contact and confirmed STATE settle on
following scans. They are consistent with sampling around the confirmation
interval, rather than evidence of a missed release in this sequence. This is
not a continuous timing trace.

The evidence is recorded as `PASS_FOR_CAPTURED_SEQUENCE` in
`evidence/2026-11-03-model4-caps/native-single-press-sequence.json` and its keyboard
event snapshot. There are no event timestamps, so actual press durations cannot
be measured; the requested protocol used half-second presses. Keyboard layout
selection was not captured by the launcher. The earlier double-press and
remapped-key observations remain unqualified. Ordinary short-tap comparison and
the planned application/regression checks are still needed.

## Native handoff

1. Double-click the new standalone launcher, or mount its DMK in drive 0 of a
   Model 4 and cold boot. CAPS TRACE should appear automatically.
2. Type `a`. Perform four rounds of one physical CAPS press, held for about half
   a second, release, then type `a`. Each press should change 61 to 41 or vice
   versa, regardless of initial lock state.
3. Capture the screen before exiting with Ctrl-C. Note the selected keyboard
   layout. The launcher prints the private capture folder in Downloads, which
   contains the emulator's keyboard event log.

Compare both the raw contact and the confirmed-state transitions with the
returned characters before proposing any production change. Do not reinterpret
both physical edges as lock toggles merely to accommodate a possible host latch:
a complete momentary key actuation would then toggle twice on real hardware.

The earlier validated candidate and its conformance evidence remain separate.
This diagnostic and its single native sequence do not establish full CAPS,
terminal-provider, TED, SEARCH, or new production-candidate release acceptance.
