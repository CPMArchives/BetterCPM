# BetterCP/M Command-Input System

Status: architectural design

## Model

BetterCP/M treats input as a progression through distinct persistent queues:

```text
physical keyboard or injected input
              |
              v
       raw type-ahead queue
              |
              v
        CCP line editor
              |
              v
    completed-command queue
              |
              v
       command dispatcher
```

Command history is a separate record of previously dispatched lines. Batch
contexts and command-source descriptions are likewise separate state even
though they ultimately produce entries for the completed-command stream.

## Raw type-ahead

BDOS owns a persistent circular byte queue for unread console input. Cooked
output already polls the console to implement CP/M flow control and preserves
one ordinary byte; that slot is to become the queue. Output-time polling may
continue accepting available keystrokes until the physical source is empty or
the queue is full.

The BIOS retains only hardware scanning, debounce, rollover, and the smallest
hardware-facing pending-key state. It does not own command type-ahead.

Cooked control characters retain their CP/M meanings while output is active:
`Ctrl-S` pauses, its resume key is consumed, `Ctrl-P` toggles printer echo, and
`Ctrl-C` requests WBOOT. Ordinary keys are queued in arrival order. Overflow
must be deterministic and non-destructive; the initial policy should reject
new bytes and may sound the console bell.

BDOS Functions 1, 6, 10, and 11 and the CCP editor observe one coherent input
queue, with cooked versus direct interpretation defined at the point of
consumption. Direct console input reads queued bytes first but does not apply
CCP editing rules.

## Line editing and completed commands

The CCP line editor consumes raw bytes and produces an editable line. Enter
commits a complete line to the completed-command queue. If input contains
multiple terminated lines, the later lines remain pending and can execute when
the preceding command returns.

The completed-command queue contains logical command records rather than raw
keyboard bytes. Records may originate from interactive input, a multiple-command
line, SUBMIT/FLOW processing, nested batch sources, or another authorized CPX.
The dispatcher should not need source-specific parsing paths merely to execute
them. Each record may carry minimal source and echo/status policy metadata.

## History

The existing 512-byte packed history buffer remains separate. It stores
completed lines that have been dispatched and supports Up/Down recall. Recalled
text is copied into the editor; history navigation does not remove or reorder
pending commands.

## Persistent state and WBOOT

The following live in protected persistent DATA and survive ordinary WBOOT:

- raw type-ahead ring state and bytes;
- pending completed-command records;
- the command-history ring;
- command-source and batch-context descriptions; and
- source, echo, abort, and completion-status state needed for reconstruction.

CPXs and the CCP remain reclaimable. WBOOT reloads them, after which the CCP
continues consuming the protected input and command state. Cold boot initializes
the queues according to configuration and discards stale runtime input.

Persistence must not preserve pointers into reclaimable CPX, CCP, or transient
memory. Tables describe content and sources; runtime addresses are reconstructed.

## Scripted input

`BATCHIO.RSX` may feed program-input bytes into the logical console-input layer
while a scripted-input scope is active. Injected and physical input share the
consumer interface but retain source identity so cancellation, precedence, and
security policy remain explicit. Scripted input does not enter command history
unless it actually produces a command dispatched by the CCP.

## Initial implementation sequence

1. Replace the single BDOS pending byte with a persistent ring buffer.
2. Route all applicable BDOS and CCP reads through that buffer.
3. Add persistent completed-command records and multiple-line promotion.
4. Integrate existing history without conflating history with pending work.
5. Define the command-source ABI used by SUBMIT.CPX and FLOW.CPX.
6. Add BATCHIO.RSX as an explicitly activated input provider.

