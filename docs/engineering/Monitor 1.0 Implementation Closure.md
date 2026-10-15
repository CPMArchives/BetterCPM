# Monitor 1.0 implementation closure

Status: 2026-10-15. The bounded 1.0 monitor implementation is complete for its
stated personalities and backends. This is an implementation milestone, not
a declaration that BetterCP/M 1.0 or every terminal configuration is qualified.

## Implemented contracts

- BIOS dispatch covers direct BIOS and BDOS-mediated console callers. Raw bypass
  avoids recursive provider entry; public input/status normalization is preserved.
- MCON 1.0 metadata restricts backend, reconstruction class and callable entry.
  A prospective profile accepts only one provider.
- Transactions validate before detach/movement, rebind the retained provider,
  restore the basic console on removal, and retain the previous binding on failure.
- Warm command return discards unfinished parser continuation. Explicit internal
  clear/home uses operation 4, preserving Model 4 MM insert-line semantics.
- All provider memory follows the normal RSX policy. Unloading all RSXs restores
  53K TPA; provider additions require no further permanent BIOS or BDOS growth.

## Provider evidence

| Provider | Backend | Utility | Qualification record |
| --- | --- | --- | --- |
| ADM3A | Model 4 native display | ADMTST | [Native ADM3A](ADM3A%20Native%20Qualification.md) |
| VT52 | cpmsim ANSI host | VT52TST | [Live VT52](VT52%20Live%20Qualification.md) |
| ANSI | cpmsim ANSI host | ANSITST | [ANSI foundation and live/application qualification](ANSI%20Provider%20Foundation%20Qualification.md) |

ADM3A qualifies the selected original MM behavior, production lifecycle,
native screen/input controls, bell and original MM CONFIG opening screen.
VT52 includes bounded 80×24 scrolling on larger hosts, ordered replies,
retained state and an unchanged WordStar edit/save test. ANSI includes bounded
sequence buffering, supported screen controls and unchanged TE open/edit/save.
VT52 and ANSI provider/utility campaigns also pass enforced cpmsim ROM protection.
The TE application campaign itself was on ordinary cpmsim.

Normal complete builds supply the modules and utilities. The Model 4 startup
script loads ADM3A after the banner. cpmsim remains banner-only, with manual
VT52/ANSI selection; adding an automatic default is not necessary for the
current interface and is not silently introduced here.

## Shared regression closure

The current source passed the following shared checks on 2026-10-15:

- `tools/test_monitor_metadata.py`: 34 version/class/backend cases.
- `tools/test_monitor_bios_hooks.py`: native and `--z80pack-build <host-build>`
  vectors, routed console/cursor/list, normalization, raw bypass and detach.
- `tools/test_monitor_selection.py`: both backends, actual preparation/commit,
  duplicate/changed-carrier rejection, retained movement/state and TPA restoration.
- `tools/test_monitor_commit_publication.py`: rebinding before generation
  publication and failure retaining the old binding.
- `tools/test_monitor_return_clear.py`: clear preserves utility registers;
  prompt and reconstruction reset precede output.

These execute assembled production code using the instruction runner. They
complement the earlier real cpmsim and trs80gp campaigns; they are not
substitutes for those campaigns or physical-hardware testing.

## Developer support

[Monitor RSX Development](../programmers/Monitor%20RSX%20Development.md) documents
carrier creation, callback restrictions, state/pointer relocation, testing and
the editable host template. MONDEMO is intentionally excluded from production
media. Table-only adaptations cover small grammars; coordinates, replies, CSI
parameters and modes require custom parsing and their own qualification.

## Remaining boundaries

The release still needs final qualification against frozen artifacts alongside
the remaining utilities. Full VT100/xterm, VT52 graphics/keypad extensions,
unqualified hardware configurations and arbitrary applications are not promised.
Further terminal personalities, a real TCAP database and simultaneous monitors
remain outside 1.0. The next planned system-disk implementation is ED.COM;
monitor implementation does not require another core feature stage.
