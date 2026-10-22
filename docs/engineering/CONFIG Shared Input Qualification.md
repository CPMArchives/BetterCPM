# CONFIG Shared Input Qualification

**2026-10-22 — CONFIG 1.0 Build 014**

## Change and scope

Startup-command replacement and freeform decimal fields now use the shared
basic editor, including physical-profile byte values, format-workbench numbers,
sector slots/IDs/size codes and disk-boot IOBYTE input. The existing track/step
choice lists, menus and confirmations remain separate. DUMP's shared editor
source and executable behavior are unchanged.

The renderer is inline on CONFIG's existing 80-column console layout, using 79
columns, horizontal scrolling and either reverse-video or underscore cursor
marking. No loaded backend is required. Word commands, defaults, choices and
the standard result interface are future increments, not implemented features
of this migration. See the [engineering specification](CONFIG%20Specification.md#shared-input-migration-build-014)
and [shared library specification](Shared%20Input%20and%20UI%20Specification.md).

## Exact artifact and memory

The dual-profile CONFIG.COM is **15,552 bytes**, SHA-256:

```text
2167646cfe1506405cd1834deaf26d3bc4712dc8a5911d04c26e9040fbfad9e4
```

Native ZSM4/LINK output matches every byte. The executable ends at 3DC0h,
leaving **64 bytes** before the unchanged 3E00h private stack boundary. The
previous dual-profile Build 013 was 15,457 bytes: this increment adds 95 bytes.
Both the Model 4 and cpmsim configuration-validation/IOBYTE profiles are
embedded. The AC00h transient-memory guard is unchanged. No BIOS/BDOS/CCP code,
resident storage, permanent ABI or unloaded TPA change is made.

The editor reuses the startup counted-input buffer and six bytes at
ABE0h..ABE5h. The duplicate append-only numeric reader is omitted from CONFIG's
expanded source; its other consumers retain the original code. Shorter field
labels avoid duplicate prompt text and reserve space for editable input.

## Passed checks

| Evidence | Result and scope |
| --- | --- |
| `tools/test_config_shared_input.py` | 24 compiled-code cases: actual startup commit/cancel paths, case/space preservation, insertion/deletion/movement, ESC/Ctrl-C, DEL, cursor marking/fallback, horizontal scroll, capacity limits, numeric correction/overflow, byte-field default and overflow, stack and workspace guards. Hostile BDOS fixture and independent console model; not native screen evidence. |
| `tools/build_native_config.py` | All 15,552 native ZSM4/LINK bytes match the cross build. |
| `tools/test_config_shared_input_live.py` | Actual cpmsim: startup editing, preserved pending value after ESC, numeric invalid-input recovery and local Ctrl-C, normal return, private disk byte identity and independent filesystem check. |
| `tools/test_config_shared_input_model4.py` | Actual trs80gp Model 4: six screen captures covering edited startup value, reverse cursor, physical CLEAR cancellation, numeric error, numeric cancellation and normal CCP return. Private disk and immutable source image unchanged. |
| `tools/test_config_startup_read.py` | Native startup-record display, edit, clear, test, 126-character boundary, pending save and saved-record inspection pass. |
| `tools/test_config_save_all.py` | Native merged active/pending save, cold-boot state check, saved startup inspection and fault-injected rollback pass. |
| Existing compiled CONFIG regressions | Command-line parsing, pending defaults, startup save/rollback, persistent IOBYTE, CRC validation, logical/physical/edit CLI and saved inspection pass. |
| DUMP regression | All 80 enhanced and 19 DRI/version cases pass. Its executable remains the identical qualified Build 002. |

The focused native startup/save fixtures were updated from the superseded J/H
menu bindings to current A/S. The all-settings native save fixture uses a bounded
180-second timeout instead of 40 seconds for simulated disk I/O.

## Integration findings and limits

The first host campaign exposed cooked Function 2 output consuming Ctrl-S and
its following key during redraw. Active-field output now uses direct Function
6; the existing optional Function 178 supplies the Model 4 cursor presentation.
Ordinary menu output retains its previous cooked behavior. CPU tests reject
cooked output on the editor paths so that the integration error cannot silently
return under a permissive console fixture.

Earlier native attempts used unsuitable text-wait markers, including a
lowercase marker for uppercase matrix input. The final native campaign uses
the established bounded CONFIG timing approach and independently asserts all
six captured screens. Failed attempts are not counted as passes.

Only decimal syntax/word overflow and physical byte overflow are handled by
the shared numeric correction loop. Field-specific geometry, hardware and
IOBYTE policy rejection retains the existing caller behavior. A complete
standard prompt controller and migration of those policies remain separate
work. No claim is made that the full standard UI profile is implemented.

Local evidence roots for this exact artifact:

- `/private/tmp/bcpm-config-ui-live-final/`
- `/private/tmp/bcpm-config-ui-model4-4/`
- `build/config-development/`
- `build/test-results/config-startup-read/`
- `build/test-results/config-save-all/`
- `build/utilities/config-shared-input-tests.json`

All three focused report identities and the native binary were checked against
the exact SHA-256 above. These are utility migration checks, not a new full
System Disk or Utilities Disk release-acceptance run.
