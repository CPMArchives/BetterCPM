# Engineering Specification 110: CCP Control-Key Compatibility

## Milestone

The enhanced CCP preserves the documented CP/M command-entry controls while
retaining non-conflicting cursor editing and persistent history.

## Command-entry contract

| Key | CCP action |
|---|---|
| `Ctrl-C` | Warm boot through BDOS Function 0. Disk maps and software read-only locks are reset by the normal WBOOT path. |
| `Ctrl-E` | Emit a physical CR/LF and continue editing the same instruction queue without executing it. |
| `Ctrl-H` | Destructively remove the character left of the logical cursor. |
| `Ctrl-P` | Toggle the shared cooked-console printer-echo state. |
| `Ctrl-S` | Move one character left while the CCP editor owns input. |
| `Ctrl-U`, `Ctrl-X` | Discard the complete instruction queue and redraw an empty prompt. |

Physical Up and Down select older and newer persistent-history records. They
replace the former, incompatible `Ctrl-E`/`Ctrl-X` history bindings. Physical
Left/Right and the remaining non-conflicting WordStar controls retain their
editing actions.

`Ctrl-S` is intentionally contextual. At the interactive CCP prompt it is an
editor command. While the cooked console is producing output, including output
from a transient program, it pauses scrolling until the next key.

## Shared console behavior

Printer echo is BDOS state rather than a private CCP flag. The CCP reaches it
through provisional private Function 205, so `Ctrl-P` at the prompt affects
the same console-to-`LST:` duplication used by transient programs. The public
CP/M console functions continue to recognize `Ctrl-P` directly.

Cooked input and output consume the key which resumes a `Ctrl-S` pause. A
resume `Ctrl-C` warm-boots; a resume `Ctrl-P` toggles printer echo. Ordinary
unpaused output polling still preserves one type-ahead byte.

## Verification

Focused CCP tests verify that `Ctrl-E` retains a line and `Ctrl-U`/`Ctrl-X`
clear it. BDOS tests verify that the CCP printer toggle changes the shared
printer-echo state and that an ordinary key resumes paused output. Native CP/M
and cross builds remain byte-identical.
