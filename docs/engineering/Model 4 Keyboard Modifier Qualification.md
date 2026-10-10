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

## Bracket mapping

A raw matrix diagnostic under trs80gp Logical Layout observed host `[` as
Model 4 row 6, bit 3: the physical Up key. The former byte 11 invoked CCP
history recall and replaced the command being entered. The BIOS cannot
distinguish host `[` from a physical Up arrow with that same matrix state.

The Up and Down slots now publish ASCII `[` (5Bh) and `]` (5Dh). History
navigation remains available through Ctrl-K (0Bh) and Ctrl-J (0Ah); this is a Model 4 keyboard mapping change, with no CCP
or BDOS changes. The BIOS size and writable-state layout are unchanged.
The BIOS regression checks both brackets and both history chords.

The user and the raw matrix probe both confirmed that host `]` produces no
matrix event in Logical Layout. This is an emulator limitation; the BIOS
cannot recover a character it never receives. Physical Down provides a
closing-bracket fallback. Host `[` continues to work normally via the Up slot.
These mappings also apply on real Model 4 keyboards. Left/Right editing and
Shift-Left backspace remain unchanged.

The rebuilt image (SHA-256
`e0253bfdb49012cb87e9d915053c23ff889d634bdd370ec3e49dfba05fef716d`)
passes the complete byte regression, including `5B 5D 0B 0A` for the two
brackets and history chords. A separate boot entered `:DIR *.*[$SYS]`
through physical matrix keys and returned `NO FILE` and a fresh `A0>` prompt,
with no history replacement or filespec error. BIOS remains 637/638 bytes
and the ROM/RAM inventory check passes.
