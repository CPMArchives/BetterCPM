# DASM tool-set qualification

Qualification date: 2026-10-25. This report concerns the bounded BetterCP/M
DASM adaptation, DSYM converter and DLINK checked launcher on the Model 4/trs80gp
and z80pack/cpmsim emulator targets. It does not qualify physical hardware or
the entire Utilities Disk. TED remains pending. The binaries retain their
owned development identity, `1.0 (001-dev)`.

## Implementation

The maintained Conn 1.5 engine emits byte-preserving ZSM4 source, supports
logical origins through FFFFH, preserves aliases and annotations, and stages
file replacement with recoverable backups. Session format 2 validates the
binary and complete component graph before changing live tables. DSYM converts
complete checked final-address reports, refusing bare symbol maps that cannot
establish successful linking. DLINK verifies the unchanged disk LINK image and uses bounded child
memory to capture a checked report without replacing existing outputs.

The launcher preserves the BIOS warm-boot vector, required by Model 4's screen
backend. Only the two verified warm-boot operands in the loaded LINK copy are
redirected to DLINK's exit handler; the distributed LINK.COM is unchanged.
Intercepted BDOS calls use a separate 1 KiB stack.

The original DASM import and Conn/Barker/Christensen credits remain intact.
The historical SIG/M distribution/modification basis is recorded in provenance;
its submission form is an unsigned generic template. ZSM4 4.7 and DRI LINK 1.3
remain externally versioned, unchanged third-party tools.

## Qualification matrix

| Gate | z80pack/cpmsim | Model 4/trs80gp |
| --- | --- | --- |
| Normal resident-profile memory measurement | PASS | PASS |
| 5,420-byte real utility fixture | PASS | PASS |
| Native build parity, converter and five-byte round trip | PASS | PASS |
| Multi-module link and failed-link rejection | PASS | PASS |
| Session graph, aliases/comments/controls and four origins | PASS | PASS |
| Eight opcode/data corpora (10,503 logical bytes) | PASS | PASS |
| 8,192-byte capacity reconstruction | PASS | PASS |
| Four real filesystem refusal/recovery cases | PASS | PASS |
| Live backspace, paging, confirmed cancellation and CCP return | PASS | PASS |
| Valid session plus six damaged graph refusals | PASS | PASS |
| B100H startup refusal and resident guard | PASS | PASS |

Each native build must match the corresponding host binary before its verdict
can pass. Reconstruction compares the declared logical interval byte for byte;
record padding is checked separately. One-byte images include an explicit 1Ah
outside that interval to work around LINK's one-byte-output behavior. Non-0100H
logical origins use ORG 100H with PHASE/DEPHASE to produce packed bytes.

The eight opcode/data corpora cover 10,503 logical bytes, with separate 8,192-byte
capacity reconstruction, a 5,420-byte real utility fixture (an earlier DLINK build, treated only as input) reconstruction,
and mixed-data/session/origin cases. Native linked
fixtures include separate code/data modules, aliases, ZERO/FFFF, a long exported
name, unresolved-symbol rejection and six-character significance collisions.

Native filesystem tests use actual directory-full, data-full, file-read-only and
BDOS drive-write-protected states on disposable disks. The data-full fixture preallocates
most free space with checked host filesystem tools, then performs native writes
until BDOS reports full; the native failure boundary is real. Independent full-core tests inject
create/read/write/close/rename failures and every session publication transition,
including collisions and retained recovery copies. Those model injections are
separate evidence from real filesystem cases; neither claims power-loss durability.

## Memory and console

| Region | Half-open addresses | Capacity |
| --- | --- | --- |
| Image | 0100H..5200H | 20,736 bytes |
| Controls | 5200H..5800H | 1,536 bytes, including terminator |
| Symbols | 5800H..6800H | 4,096 bytes, including terminator |
| Input | 6900H..8900H | 8,192 bytes |
| Comments | 8900H..9100H | 2,048 bytes, including terminator |
| Transaction/import staging | 9100H..B100H | 8,192 bytes |
| Required unused margin | B100H..B200H | 256 bytes |

| Normal target | Active ceiling | COM address span from 0100H | Admitted input |
| --- | --- | --- | --- |
| Model 4, M4SCRN+ADM3A | CA01H | 51,457 bytes | 8,192 bytes |
| z80pack, ZPRTC | CF01H | 52,737 bytes | 8,192 bytes |

The active BDOS operand, including resident providers, is the exclusive TPA
ceiling. B200H is the startup minimum. Successful scripted native cases lower
the ceiling to B800H and check a canary above it; the insufficient-memory test
uses B100H and checks refusal plus intact resident storage. Ordinary console
cases use the normal M4SCRN+ADM3A profile on Model 4 and ZPRTC on z80pack.
Input capacity remains a fixed 8 KiB; there is no disk-backed paging. DLINK
keeps the child ceiling at A000H and requires room through B810H for its own
storage and margin; DSYM requires 2A92H.

The private stack reserves 512 bytes. Across 161 independent host campaigns,
the observed high-water mark was 44 bytes, with the bottom 32 bytes intact.
This is measured coverage rather than a formal bound for future changes or
arbitrary BIOS implementations. The full 80-character command test also checks
space for BDOS's trailing carriage return, which previously reached the first
reserved stack byte.

Work output and break handling use direct-console services so cooked-console
ETX cancellation cannot bypass cleanup. Model 4 uses its physical BREAK key,
which produces the same ETX byte. The harness holds it through blocking disk I/O,
then releases it before waiting for the abort question: the BIOS debounces input
by waiting for physical key release. Confirmation is a separate keypress.
The Model 4 batch file then executes an independent post-exit program; its
unique success marker proves that command processing resumed after cancellation.
Live-console tests use actual keyboard input for
backspace, successive listing pages, confirmed cancellation, original-file
preservation and CCP return; the scripted function-10 wrappers do not substitute
for those tests. CP/M's normal function-10 command-line editing remains in use.

## Evidence and reproduction

[DASM-Qualification.json](DASM-Qualification.json) binds all verdicts to the
exact binaries and both System/Utilities image hashes.
[DASM-Qualification-Evidence.tar.gz](DASM-Qualification-Evidence.tar.gz) contains
source/build maps, fixtures, native outputs, host results, console captures,
execution receipts, final failure/session work-volume images, independent filesystem
audits and a SHA-256 manifest. The final integration, corrected-launcher, filesystem, console and runtime-profile
gates execute the final disk images. Retained DASM-only gates name their tested media and are accepted only
after both inventories prove identical DASM/DSYM/ZSM4/LINK bytes and the same
System image. The native Model 4 DASM/DSYM build witness retains matching source,
binaries and successful build screens; only that verified build portion of the
earlier campaign is used. The failed launcher portion is excluded.

Failed and superseded development
attempts are excluded from acceptance; earlier development receipts remain
historical evidence only.

Use the `qualify_dasm*` and `qualify_dlink.py` runners with explicit frozen System
and Utilities directories and new output directories. `collect_dasm_qualification.py`
refuses incomplete, failed or mixed-artifact campaigns. `build_utilities_disk.py --dasm-acceptance RECEIPT` rejects a receipt for different binaries or disk images.
The complete source companion travels with the provisional Utilities package.
The package records component acceptance for DASM.COM, DSYM.COM and DLINK.COM;
the whole Utilities release and its other component gates remain independent.

For the command contract, limits, file-recovery procedure and worked native
example, see [DASM.TXT](../../src/distribution/DASM.TXT),
[DASM Implementation Status](DASM%20Implementation%20Status.md) and
[DASM Symbol Conversion](DASM%20Symbol%20Conversion.md).

## Qualified binaries

| Binary | Bytes | SHA-256 |
| --- | --- | --- |
| DASM.COM | 20,736 | `8034d629ee464d33659684c39493022bd48c7cb1227952428c751fbf169b66e9` |
| DSYM.COM | 10,386 | `8cd2d1e09fc60432a3345e1321b54a92316f18fb7ef30b9e8c8da18c2f63f98a` |
| DLINK.COM | 6,216 | `2bc9912e769b6d8e6635afa47d6ca6121a53ba60870cac7330b441ff0dbed8f7` |

The evidence archive contains 1213 hashed entries; its SHA-256 is
`d3ecbcf447cb5b78ca90efc8b5a7f6201efaf2e0f5b506b298f43d3b0cd97791`.
