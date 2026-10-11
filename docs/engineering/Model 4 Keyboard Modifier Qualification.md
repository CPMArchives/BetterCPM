# Model 4 keyboard modifier qualification

Date: 2026-10-11

## Confirmed driver defect

The former overlapping-key debounce compared translated characters rather than
physical key identities. A Shift change while the colon key remained held
produced both `:` and `*`. Releasing Control before releasing a letter could
likewise publish both the control character and the ordinary letter.

The scanner now retains the physical matrix slot separately from the
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

## Montezuma Micro punctuation chords

The temporary Up/Down bracket mapping is retired. Up and Down again return
0Bh and 0Ah for CCP history. Left/Right and Shift-Left remain unchanged.

The scanner implements the ten punctuation chords documented on printed page
10 of the [Montezuma Micro Model 4 manual](https://archive.org/download/CPM_Model_4_1984_Montezuma_Micro_PDF/CPM_Model_4_1984_Montezuma_Micro_PDF.pdf#page=12):

| Character | Original Model 4 Control chord |
| --- | --- |
| `[` | 8 / opening parenthesis |
| `]` | 9 / closing parenthesis |
| `{` | comma / opening angle bracket |
| `}` | period / closing angle bracket |
| `\` | slash |
| &#124; | 1 |
| `~` | 3 |
| `^` | 5 |
| backtick | 7 |
| `_` | minus |

Each chord works with Control alone or Control plus Shift. Ordinary letters,
shifted punctuation and existing letter controls retain their behavior. This
implements punctuation compatibility, not every Montezuma keyboard convention.

Arithmetic decoding replaces the ordinary-key table; cursor-store tails are
shared. BIOS now emits 636 of 638 allocated bytes, with no BDOS growth or
memory-boundary changes. The five-byte console state moves to EBD9h–EBDDh;
ROM relocation and RAM totals remain 2,253 and 2,256 bytes.

The BIOS vector test covers connected ordinary keys, all ten chords with and
without Shift, arrow controls, and output/cursor behavior. The emulator test
reads the same chords through public BIOS CONIN using physical matrix input.
Host-layout translation remains distinct: the previously observed host `[`
arrives as Up in Logical Layout, and host `]` produced no matrix event.
These observations do not establish how every host layout translates Control
chords; the original Model 4 signals are the qualified interface.

The rebuilt emulator image passes all 42 expected CONIN bytes. A separate
boot enters `:DIR *.*[$SYS]` through the punctuation chords and returns
`NO FILE` followed by a fresh prompt, without a filespec error.
