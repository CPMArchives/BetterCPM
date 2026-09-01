# Engineering Specification 52: Read Console Buffer

## Milestone

BetterCP/M now implements BDOS function 10 (Read Console Buffer), completing
the CP/M 2.2 console-service group.

## Contract

Function 10 receives `DE` pointing to `[maximum][count][data...]`. It accepts
the full documented maximum range from 1 through 255, returns the edited length
in the count byte, and stores data beginning at `DE+2`. CR, LF, and capacity
terminate input; no terminator is stored, and a full buffer returns without
reading another byte. The Function-10 address remains independent of the DMA
address.

## Editing behavior

The editor implements the ledger-required CP/M controls: Backspace and DEL
remove one character; initial Ctrl-C warm-boots; Ctrl-E continues on a new
physical line; Ctrl-R redisplays and retains the line; Ctrl-U and Ctrl-X discard
the line using their respective physical-line and erase presentations. Editing
uses the caller's starting logical column.

BetterCP/M also selects the DRI-compatible profile for seven-bit input masking,
Ctrl-P printer-echo toggling, noninitial Ctrl-C retention, caret display of
accepted controls, correction display, and a final carriage return.

## Architecture

Input still enters exclusively through BIOS `CONIN`; output uses the same cooked
path as Functions 1, 2, and 9. Consequently logical devices, flow control,
printer echo, column tracking, and pending input retain one implementation.

## Verification

Tests cover ordinary input, parity stripping, CR and LF termination, capacity
without over-read, Backspace, DEL, Ctrl-E, Ctrl-R, Ctrl-U, Ctrl-X, count/data
placement, source limits of 1 and 255 bytes, direct BDOS entry, and application
entry through `CALL 0005h`.

Native CP/M ZSM4/Digital Research LINK and the host assembler must produce
byte-identical BDOS and resident-system binaries.

## Next increment

Implement function 0 (System Reset), the final defined CP/M 2.2 BDOS function.
