# Outline: Post-1.0 BetterCP/M Terminal Architecture

## 1. Status

Recorded 2026-10-12 from the maintainer's discussion draft. The directions
below are proposals, not frozen contracts or claims of completed implementation.
The accepted 1.0 decision is recorded separately in
[Terminal Monitor RSX](../architecture/31%20Terminal%20Monitor%20RSX.md).

The separately accepted [VIEW.COM functional specification](POST-1.0-VIEW-SPECIFICATION.md)
records a concrete consumer's screen and input requirements. VIEW implementation
is post-1.0 work for the Utilities Disk; its requirements do not freeze the
terminal subsystem's API or turn this outline into an approved interface.

This is **not yet a complete engineering specification**. It is an architectural outline for post-1.0 work.

The accepted BetterCP/M 1.0 design uses the Monitor RSX mechanism as a practical interim solution for full-screen terminal support. That mechanism should remain explicitly provisional.

The post-1.0 goal is a more systematic terminal architecture that improves portability without sacrificing ordinary CP/M compatibility.

---

## 2. Fundamental Compatibility Requirement

The most important requirement is:

> Existing CP/M software must continue to run normally under BetterCP/M without being rewritten to call a BetterCP/M-specific terminal or screen API.

BetterCP/M may provide enhanced terminal facilities, but ordinary CP/M programs must not be required to know that those facilities exist.

A program configured for a particular historical terminal should continue to emit that terminal's normal control sequences.

For example:

```text
Kaypro utility
    |
    | emits Kaypro terminal controls
    v
BetterCP/M
```

If the appropriate Kaypro-compatible terminal personality is active, the program should run unmodified.

The same principle applies to programs configured for:

- ADM-3A;
- VT52;
- Kaypro;
- VT100/ANSI;
- other historical terminal personalities.

---

## 3. Z-System as a Model

Z-System provides an important conceptual precedent.

Ordinary CP/M applications can run under Z-System without needing to know about Z-System's TCAP facilities.

Similarly, BetterCP/M's future terminal architecture should enhance the execution environment **transparently**, rather than requiring every application to adopt a new API.

The enhanced environment should therefore remain compatible with software that believes it is simply talking to the terminal for which it was configured.

---

## 4. Virtual Terminal Personality

The long-term BetterCP/M design should treat the terminal presented to applications as a **virtual terminal personality**.

Conceptually:

```text
legacy application
      |
      | emits terminal-specific character stream
      v
BetterCP/M virtual terminal personality
      |
      | interprets/maps terminal operations
      v
actual console implementation
```

The outward-facing terminal personality need not be the same as the physical or emulated console underneath it.

Examples:

```text
WordStar configured for ADM-3A
        |
        v
ADM-3A BetterCP/M personality
        |
        v
Model 4 native video hardware
```

or:

```text
Kaypro utility
        |
        v
Kaypro personality
        |
        v
VT100-compatible host terminal
```

Thus terminal personality and physical console become separate concepts.

---

## 5. Legacy Application Path

Legacy CP/M applications should use the ordinary CP/M console interfaces exactly as they do today.

They should not need to:

- discover a TCAP block;
- invoke a BetterCP/M-specific screen call;
- link against a BetterCP/M library;
- detect that BetterCP/M is present;
- modify their terminal-control logic.

The compatibility path should look conceptually like:

```text
Legacy CP/M application
        |
        | normal console output
        v
terminal-personality interpreter
        |
        v
console backend
        |
        v
actual display
```

Loading or selecting the appropriate terminal personality should be sufficient.

---

## 6. Example Compatibility Goal

Suppose a utility is recovered from a Kaypro software archive and was compiled or configured to use Kaypro terminal control sequences.

Under BetterCP/M, the desired procedure should be approximately:

```text
load/select Kaypro terminal personality
run utility
```

The utility itself should remain unchanged.

The same principle should hold for WordStar, editors, debuggers, Z-System applications, and other historical software.

---

## 7. Native BetterCP/M Applications

BetterCP/M-native programs such as:

- `VIEW.COM`;
- a selected third-party full-screen editor, if included, without requiring BetterCP/M-specific changes;
- a future debugger;
- other interactive system utilities;

may eventually benefit from a higher-level screen interface.

Such an interface could expose abstract operations such as:

```text
get geometry
position cursor
clear line
clear screen
cursor on/off
write screen data
read command key
bell
```

However, that interface must be **optional**.

It must not replace or bypass the legacy compatibility path.

---

## 8. Two Interfaces, One Underlying Terminal System

The eventual architecture may therefore expose two ways of reaching the same terminal subsystem.

Conceptually:

```text
                         +----------------------+
Legacy CP/M program --->| terminal byte stream |
                         +----------+-----------+
                                    |
                                    v
                           active personality
                                    |
                                    v
                             console backend
                                    |
                                    v
                              actual display


                         +----------------------+
BCPM-native program --->| abstract screen API  |
                         +----------+-----------+
                                    |
                                    v
                           same terminal/backend
```

The native API is an optimization and convenience for BetterCP/M-aware applications.

The byte-stream path remains the compatibility contract.

---

## 9. Terminal Personality vs. Console Backend

The architecture should distinguish at least two layers.

### Terminal personality

Defines the control language visible to applications.

Examples:

```text
ADM-3A
VT52
Kaypro
VT100/ANSI
```

It interprets such things as:

- cursor movement;
- direct cursor addressing;
- clear screen;
- clear to end of line;
- cursor visibility;
- other terminal-specific control sequences.

### Console backend

Defines how screen operations are performed on the actual platform.

Examples:

```text
Model 4 native video
serial terminal
emulator-hosted console
memory-mapped display
```

This permits many-to-many mappings:

```text
ADM-3A personality -> Model 4 video
VT52 personality   -> Model 4 video
Kaypro personality -> ANSI terminal
```

subject to the capabilities actually implemented.

---

## 10. Terminal Translation

The long-term architecture may therefore amount to terminal virtualization or translation rather than merely traditional TCAP substitution.

Traditional application-side TCAP often answers:

> "What sequence should this program emit for cursor positioning?"

BetterCP/M may instead need to answer:

> "What terminal personality is this application speaking, and how do I translate that personality into operations on the actual console?"

That is a broader problem.

A future TCAP system should therefore not automatically be constrained to a simple database of output strings.

---

## 11. BetterCP/M 1.0 as Prototype

The accepted BetterCP/M 1.0 Monitor RSX design is intended to provide an experimental form of this architecture. Implementation and qualification are pending; the audit prototypes are not shipping providers.

Current 1.0 decisions include:

- Monitor RSX loaded through cold-start `SUBMIT`;
- ADM-3A personality for Model 4;
- VT52 as the general target;
- basic-console fallback when the Monitor RSX is absent;
- the 53K core TPA baseline restored when all RSXs are unloaded; unloading only the monitor releases its own allocation while other RSXs retain theirs.

This is sufficient for 1.0 but should be treated as a prototype rather than the final terminal architecture.

---

## 12. Lessons to Gather from 1.0

The 1.0 Monitor RSX implementation should provide practical evidence about what a later architecture actually needs.

Questions to observe include:

- Which terminal operations are required by real historical applications?
- How much sequence parsing is needed?
- Which terminal personalities are most useful in the modern CP/M community?
- How often do terminal personalities require stateful interpretation?
- Which functions are common enough to deserve a formal capability definition?
- What operations do BetterCP/M-native programs such as VIEW require?
- How expensive is translation in resident memory?
- Which operations must remain available with a minimal console fallback?

These observations should influence the post-1.0 design rather than prematurely freezing a theoretical TCAP format.

---

## 13. Future TCAP/Personality Database

Post-1.0 BetterCP/M should investigate a formal terminal-personality database.

Possible sources of terminal definitions include the large historical collections already available in:

- Z-System TCAP libraries;
- CP/M application installation databases;
- terminal configuration files from historical software;
- modern CP/M emulator projects.

BetterCP/M should reuse that accumulated knowledge where practical rather than recreate terminal definitions from scratch.

The eventual storage format remains undecided.

---

## 14. Discovery and Selection

A mature design will need a defined way to determine which terminal personality is active.

Possible future mechanisms may include:

- system configuration;
- boot configuration;
- RSX selection;
- a terminal-profile loader;
- an environment descriptor;
- a discovery call available to BetterCP/M-aware programs.

No particular mechanism is selected by this outline.

The important requirement is that **legacy applications should not need to use it**.

---

## 15. Native Screen API

A future native screen API should be evaluated separately from terminal compatibility.

It may be useful for BetterCP/M-aware programs because it can avoid:

```text
abstract screen operation
        ->
encode as virtual terminal sequence
        ->
parse that sequence again
        ->
perform screen operation
```

A native program could instead request the screen operation directly.

However:

> A native screen API is an optimization layer, not the fundamental compatibility interface.

Legacy software must continue to work entirely through ordinary CP/M console I/O.

---

## 16. No BetterCP/M Lock-In for Applications

The post-1.0 architecture should avoid creating a new class of BetterCP/M-only programs unnecessarily.

Whenever practical:

- programs using ordinary terminal protocols should remain portable;
- BetterCP/M enhancements should be transparent;
- applications should not need to detect BetterCP/M merely to display a full screen.

BetterCP/M-native applications may use enhanced facilities where useful, but the system should preserve CP/M's traditional application model.

---

## 17. Compatibility Principle

The overarching rule should be:

> BetterCP/M adapts itself to CP/M software; CP/M software should not have to adapt itself to BetterCP/M.

For terminal handling, this means that if an application expects an ADM-3A, Kaypro, VT52, or other supported monitor, BetterCP/M should strive to present that environment transparently.

---

## 18. Possible Long-Term Architecture

A mature design might eventually resemble:

```text
                   Legacy CP/M software
                           |
                    console byte stream
                           |
                           v
                +-----------------------+
                | Terminal Personality  |
                | parser/emulator       |
                +-----------+-----------+
                            |
                            | abstract screen ops
                            v
                +-----------------------+
                | Console Backend       |
                +-----------+-----------+
                            |
                            v
                    physical/emulated
                         display


BetterCP/M-native software
          |
          | optional abstract screen API
          +--------------------+
                               |
                               v
                        Console Backend
```

Whether the native API passes through the personality layer or reaches the backend directly remains a later design question.

---

## 19. Post-1.0 Questions

The eventual specification will need to settle at least:

- terminal-personality format;
- terminal-profile database format;
- sequence-parser architecture;
- discovery mechanism;
- personality selection;
- console-backend interface;
- native screen API;
- RSX versus other implementation placement;
- memory residency;
- dynamic loading/unloading;
- fallback behavior;
- capability negotiation;
- versioning;
- whether terminal translation can be stacked;
- relationship to existing Z-System TCAP data;
- compatibility with physical serial terminals;
- compatibility with native-video machines.

These questions are explicitly **not settled by this outline**.

---

## 20. Architectural Direction

For BetterCP/M 1.0:

> Use Monitor RSX terminal personalities as the practical compatibility mechanism.

For post-1.0:

> Develop a formal terminal architecture in which BetterCP/M can transparently present historical terminal personalities to unmodified CP/M applications while optionally exposing a cleaner abstract screen interface to BetterCP/M-aware software.

The guiding compatibility requirement remains:

> A CP/M program configured for a supported terminal should require no modification to run under BetterCP/M; selecting or loading the corresponding BetterCP/M terminal personality should be sufficient.

## 21. Review notes and additional open questions

The separation of terminal personality from console backend is the central
proposal. A capability description that tells an aware application which bytes
to emit is distinct from a parser that interprets an unaware application's byte
stream. Historical TCAP collections may supply useful definitions, but their
ability to describe stateful parsing must be investigated rather than assumed.
The Z-System comparison above is a research lead: verify its actual TCAP and
console mechanisms before treating it as evidence of transparent emulation.

The compatibility goal applies to applications whose machine-specific
dependencies are covered by the supported console interfaces. Direct video,
keyboard or other hardware access, private BIOS calls, instruction-set differences
and unrelated platform dependencies require separate compatibility work.

Additional questions to retain for the later discussion:

- **Input and replies:** how are function/cursor keys encoded, and how are
  terminal identification or status replies delivered through console input?
- **Shared state:** if native calls reach the backend directly, how do cursor
  position, attributes, margins and a partially received escape sequence remain
  coherent with the byte-stream interpreter?
- **Capability limits:** what happens when the backend cannot reproduce geometry,
  graphics, character sets or other operations requested by a personality?
  Define supported subsets and fallback behavior rather than promise universal
  translation.
- **Selection boundaries:** is personality selection session-wide or scoped to
  a program? How are the prior personality, parser state and display restored
  on ordinary return, warm boot, abort or failed load?
- **Transport boundary:** distinguish interpreting a protocol on native video,
  translating it to a host terminal, and passing it unchanged to a matching
  physical terminal. Avoid accidental double interpretation.
- **Qualification:** use real application traces and rendered-screen/input tests
  in addition to parser tests; record both permanent and loaded memory costs.

These notes extend the discussion agenda. They do not choose an API, database
format, provider ABI or post-1.0 implementation schedule.
