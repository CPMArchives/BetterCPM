# Model 4 keyboard modifier qualification

Date: 2026-10-11

## Confirmed driver defect

The former overlapping-key debounce compared translated characters rather than
physical key identities. A Shift change while the colon key remained held
produced both `:` and `*`. Releasing Control before releasing a letter could
likewise publish both the control character and the ordinary letter.

The scanner now retains the physical key-table slot separately from the
translated byte. Modifier changes on that same slot do not enqueue another
character. A different overlapping key still queues normally. Shifted
punctuation uses the Model 4 ASCII ranges, including `!`, quotes, `#`, `%`,
`&`, parentheses, `+`, and angle brackets previously omitted.

The emitted BIOS is 637 of its existing 638 bytes. BDOS and the memory layout
are unchanged. Console working state grows from four to five bytes; the ROM
ownership inventory reflects the additional mutable byte.

## Before and after evidence

`tools/test_model4_keyboard_modifiers.py` installs a private diagnostic and
reads through the public BIOS CONIN vector. The diagnostic writes hexadecimal
bytes directly to video so BDOS output polling cannot consume test keystrokes.
A ready marker ensures the diagnostic has finished loading before input starts.

The old distribution emitted `3A 2A 2A 3A` for the two held-colon modifier
sequences, and `01 41` for Control-A followed by Control release. The fixed
image emits exactly `3A 2A` and `01`. Shifted punctuation, overlapping A/B,
and the complete expected byte stream pass. The source image remains untouched.

Qualified image SHA-256:
`0bff864bce1f6baad1c2944a675f04057768ebb5b0e8a33b7822813b41c83227`.

Build and ROM/RAM ownership checks pass. The z80pack ROM-profile RAM map
continues to pass unchanged.

## Bracket mapping remains a separate decision

A raw matrix diagnostic under trs80gp Logical Layout observed host `[` as
Model 4 row 6, bit 3: the physical Up key. BetterCP/M maps that key to byte
11, which the CCP interprets as history recall. This explains replacement of
the current input by a previous command. The BIOS cannot distinguish host `[`
from a physical Up arrow when the emulator supplies the same matrix state.

The proposed choice is to publish `[` for that key and use the existing
Ctrl-K history shortcut, or retain Up-arrow history and establish another
bracket chord/mapping. This change has not been made pending the user's choice.
Right-bracket host mapping still requires qualification. No bracket fix is
claimed by the modifier regression.
