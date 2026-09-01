# Engineering Specification 58: Transient Command Tail

## Milestone

The BetterCP/M CCP now separates a transient command name from its arguments and
provides the conventional CP/M command tail at `0080h`.

## Command parsing

The first token remains a bare uppercase program name of one through eight
characters. The loader resolves that token as `NAME.COM`. Characters beginning
with the separating space are retained as the command tail rather than being
mistaken for part of the program name.

The byte at `0080h` contains the tail length, bytes beginning at `0081h` contain
the tail including its leading separator, and a carriage return follows the
last character. An invocation without arguments produces a zero length and a
carriage return at `0081h`.

This increment deliberately does not yet construct the two default FCBs at
`005Ch` and `006Ch`; that is the next program-invocation compatibility step.

## Physical fixture

`HELLO.COM` remains a normal transient using only public BDOS calls. It now also
reads the command-tail length and characters through the CP/M page-zero
interface. The automated physical test enters `HELLO WORLD` and requires:

```text
Hello from BetterCP/M WORLD
```

The test therefore covers keyboard input, CCP tokenization, `.COM` loading,
page-zero tail construction, transient consumption, and warm-start return.

## Verification

The CCP occupies 873 of its 960-byte resident region. All existing BIOS, BDOS,
directory, resident-system, `DIR`, and transient-loader checks continue to pass.
Native ZSM4 and cross-assembled binaries remain byte-identical.

The physical test also exposed and prevented an important Z80 count-register
error during development: the bounded `LDIR` count must be placed in `BC` as a
16-bit value with a zero high byte. This history is retained because an inverted
count would turn a short command tail into a destructive multi-page copy.
