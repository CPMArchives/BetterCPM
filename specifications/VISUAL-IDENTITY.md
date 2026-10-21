# BetterCP/M Visual Identity

**Design Standard — Version 1.0 — Final**

## Design Philosophy

BetterCP/M adopts a **minimalist, scalable, text-based visual identity** built around implied frames, careful alignment, and purposeful white space.

The objective is a distinctive, recognizable aesthetic that remains elegant and unobtrusive, from a full cold-boot banner to a small utility identification screen.

The aesthetic should feel technically serious, clean, restrained, and appropriate to the CP/M tradition.

## Core Design Principles

1. **Minimalism.** Every visual element should serve a purpose. Avoid unnecessary ornamentation.
2. **Implied frames.** The signature BetterCP/M motif consists of short horizontal strokes (`- - -`) and detached vertical strokes (`|`) that suggest the boundaries of a box without fully drawing one. Corners need not be explicitly connected.
3. **Negative space.** Missing borders are intentional. The viewer's eye completes the suggested structure.
4. **Spatial hierarchy.** Use alignment, indentation, and white space to organize information. Text itself can provide visual separation without additional rules.
5. **Vertical economy.** On an 80×24 terminal, vertical space is considerably more valuable than horizontal space. Prefer modest horizontal indentation over extra blank lines or decorative rows.
6. **Scalability.** The visual language must work at every scale, from a compact two- or three-line display to a full-screen interactive application.
7. **Flexible consistency.** Spaced hyphens are a recurring design element, not an immutable logo. Their number, length, and arrangement may vary. Continuous lines are also acceptable where appropriate.
8. **Information first.** Visual styling must never interfere with readability, functionality, or CP/M compatibility.

## Signature Visual Elements

The characteristic BetterCP/M design uses:

- Short, spaced horizontal strokes: `- - -`
- Detached vertical strokes: `|`
- Implied rather than connected corners
- Generous but purposeful white space
- Centered headings where appropriate
- Aligned columns for structured information
- Subtle indentation to establish hierarchy
- Standard 7-bit ASCII characters for portability

Full rectangular borders remain permissible where they serve a practical purpose, but implied framing is the preferred house style.

## Reference Design: Cold-Boot Banner

```
 - - -                                                  - - -
|                                                            |
|                         BetterCP/M                         |
                          Release X.Y

                  CP/M 2.2 Compatible System

    Processor    Z80                 Console     VT100
    Memory       64K                 TPA         54K
|   System       Kaypro              Drives      A: B:       |
|                                                            |
 - - -                                                  - - -
```

The cold-boot banner establishes the system's identity and displays useful configuration information.

Values such as processor, memory, console, and machine type must reflect the actual system or its known configuration.

The full banner appears on cold boot, not on every warm boot or return to the CCP.

The current static `:VER /BANNER` implementation uses the same implied frame
with the BetterCP/M name, metadata-owned release, compatibility statement and
README guidance. It omits processor, memory, TPA, console, machine and drive
fields because it does not query those capabilities. The sample hardware values
above are illustrative and must not be copied into a static production banner.
An explicit `:VER /BANNER` invocation may display the banner on demand; ordinary
`VER` retains its concise version output. Startup invocation remains in
`STARTUP.SUB`, outside the BIOS and permanent resident code.

## Reference Design: Utility Identification

```
A>STAT /VER

STAT 2.2
  - - -
 | BetterCP/M Utilities
 | Disk Status and Device Configuration
```

The single implied corner is the compact expression of the same aesthetic used in the cold-boot banner.

The title occupies the primary margin. The subordinate information is slightly indented and visually grouped by the partial frame.

## Applying the Aesthetic

**Cold-boot screens:** Four implied corners framing the system identity and configuration.

**Interactive applications and games:** Two or four implied corners, depending on screen layout and available space.

**Utility `/VER` and `/HELP` screens:** Compact identification using one implied corner or similarly restrained styling.

**Routine command output:** No compulsory branding or framing. Preserve conventional CP/M behavior, output formats, and compatibility.

**Multi-section displays:** Short spaced-hyphen rules may provide separation when alignment and white space alone are insufficient.

The same visual grammar should remain recognizable throughout the operating system without requiring identical layouts everywhere.

## Design Constraints

- Compatible with ordinary 80-column CP/M text terminals.
- No dependence on ANSI graphics, color, or special character sets.
- Functional on monochrome displays and serial terminals.
- Avoid large ASCII-art logos, heavy borders, excessive rules, and decorative clutter.
- Do not impose BetterCP/M styling on third-party software unnecessarily.
- Preserve the standard CP/M command prompt and ordinary utility output conventions.

## Governing Principle

**Use alignment and white space to establish structure. Suggest boundaries rather than drawing them completely. Add visual elements only when they contribute to clarity, hierarchy, or identity.**

BetterCP/M's identity should be recognizable through a consistent visual grammar—not through excessive branding or decoration.
