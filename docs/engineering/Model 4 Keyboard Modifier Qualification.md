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


## MM CLEAR/ESC restoration — 2026-10-22

Restore the MM CP/M 2.32 BIOS `keytable`, `keytables` and `keytablec`
conventions for CLEAR: unshifted and Shift-CLEAR return ESC (`1Bh`);
Ctrl-CLEAR, including Ctrl+Shift variants, returns DEL (`7Fh`). BREAK still
returns Ctrl-C (`03h`). This is a Model 4 driver correction for both real
hardware and emulation, not an application-specific cancellation alias.
The local historical source reference is
`CPM/montezuma-micro/source-reference/mmcpm232/bios.asm`, lines 820–831.

In [trs80gp](https://48k.ca/trs80gp.html#keyboard), Home activates CLEAR in
Logical and Physical layouts; Physical Layout also maps the host apostrophe
key to CLEAR. Its software keyboard has a `CLR` key. On a MacBook,
[Fn–Left Arrow generates Home](https://support.apple.com/en-us/102650).
Therefore the host entry sequence is Fn–Left for CLEAR/ESC, with Control added
for DEL (using the user's remapped Control key if applicable). Host Esc is
mapped to BREAK, so it remains Ctrl-C. These host shortcuts are documented
mappings; the automated native test below injects the physical matrix rather
than claiming an automated macOS host-event test.

CLEAR is no longer the CCP's physical insert/overwrite alias. Ctrl-V retains
that function; the CCP's old logical `1Fh` alias remains accepted for consoles
that send it. The console-input change is global to applications; the CCP
still has no Model 4 hardware knowledge.

The implementation indexes special keys using the existing physical slot in
E and reuses comparison flags for shifted punctuation. The ordinary Control
mask has no redundant upper-bound test: reachable ordinary decoded characters
are @.._, while special keys and punctuation are below @ (CLEAR is handled
explicitly). Net code savings leave one byte, used as padding to retain the
existing console-state anchors. The BIOS remains **757/757 bytes**; its five
mutable console bytes and all memory-region allocations stay in place.
Unloaded 53K TPA is unchanged. BIOS interface remains 1.7; implementation is 1.13.

A fresh isolated complete Model 4 build and ROM/RAM ownership check pass.
The compiled BIOS test passes all 17 vector contracts, 80 disk read/write
mappings, failure paths, SECTRAN, connected matrix keys and punctuation, plus
all eight CLEAR modifier combinations (none, either/both Shift, Control with
none/either/both Shift).

`tools/test_model4_keyboard_modifiers.py` reads actual public BIOS CONIN in
trs80gp from a disposable copy. All **50 expected bytes** match, including
`1B 1B 1B 7F 7F 7F 03 03` for CLEAR, either Shift-CLEAR, Control-CLEAR,
Ctrl+either Shift-CLEAR, BREAK and Ctrl-BREAK. Existing debounce, rollover,
punctuation chords and arrow mappings also pass. The reference image hash is
`958c28035d3feec6482398dbdf21b66abaff27134567e4109b3415190386edec`;
the runner verifies that image remains unchanged. The diagnostic clears its
private screen first so startup text cannot contaminate its byte transcript.
The first isolated build stopped at a console-state-address inventory mismatch;
retaining the existing anchors resolves it without changing inventory contracts.

These are new keyboard-change qualification results, not a claim that prior
whole-release acceptance automatically covers a modified BIOS. Rebuild images
from the updated source before expecting these mappings in daily sessions.

The subsystem-version regression also now expects the already-released BDOS 1.9
(the former 1.7 expectation was stale) and the new BIOS 1.13; generated metadata
consistency checks pass. This does not change BDOS behavior or its version.

Verified durable evidence archive:
`validation-evidence/BetterCPM-MM-CLEAR-ESC-20261022.tar.gz` in the local CP/M
project workspace; SHA-256
`847927c208d936c21984cb63a46126f9340ebd80c9bee62fce987e7f30cac095`.
It includes native captures/results, the immutable tested image, BIOS bytes and
listing, complete-build state/log, runner sources and a per-file hash manifest.
Every archived regular file was reopened and its hash verified.
