# Native verified LINK report conversion

`DSYM [DU:]base.LOG [destination-DU:]` converts the complete final-address report
captured by `DLINK` into a new `base.DSY`. It refuses a bare `.SYM`: native
LINK 1.3 produces syntactically valid symbol files after unresolved externals
and multiple definitions. Zero-valued absolute symbols are legal and cannot
identify such failures. Historical bare-pair parsing remains an internal host
reference fixture, not the native command's accepted success evidence.

```text
B:ZSM4 ONE=ONE
B:ZSM4 TWO=TWO
DLINK PROGRAM ONE TWO
DSYM PROGRAM.LOG
DASM
RPROGRAM.COM
N6
RPROGRAM.DSY
```

The example's length must be measured for the actual program. `DLINK base`
alone links `base.REL`. Output is new `base.COM`, `base.SYM` and `base.LOG`;
none may exist at entry. With explicit modules, the first operand is the
output base. Input suffixes are absent or `.REL`; the output operand is a base
without an extension. Exact single drive/user operands use the shared grammar.
Inputs and output must use the same user; drives may differ. Unqualified
operands default to the caller's original DU. Names and the rendered LINK
command are bounded; compound DU scopes, arbitrary options and multiline
link commands are refused.

DLINK loads only **B0:LINK.COM**, requiring the unchanged packaged 15,616-byte
LINK 1.3 image and CRC32 D6350FEDH. Its upstream SHA-256 remains
`82df88a9bcfb1068eb37df08df6d664711d20c73ddae66b81577dfed02642677`.
This wrapper does not alter or bring LINK into BetterCP/M-owned versioning.

The compact launcher copies its checked resident region to A000H after checking
the active ceiling against its complete code, data and stack end plus 256 bytes.
Its BDOS entry jump is **the first byte at A000H**, so the child's exclusive TPA
ceiling cannot include any launcher instructions. LINK may use its own stack
below that boundary. The wrapper supplies an initial child stack and restores
the caller's BDOS/warm-boot vectors, SP, user, drive and default DMA on orderly
return. It is transient and does not install a persistent RSX.

Console output uses checked private log DMA. Every child file operation selects
the output user and then restores the child's user/DMA. Destructive operations
are restricted to the two preflighted new output identities; deletion of a file
not created by this invocation is refused without erasing it. Unexpected scratch
writes are refused. The legacy LINK A option is not enabled; jobs that cannot
fit the bounded child workspace fail safely instead of enabling its disk-scratch
path. Captured file errors block publication of the log. A unique
`DLGnnnnn.$$$` stage is closed and renamed only after orderly child exit and
checked capture completion. Failures retain and name the stage; new COM/SYM
outputs remain explicitly unverified.

DSYM requires an exact LINK 1.3 header, complete name/address map, ordered
ABSOLUTE/CODE SIZE/DATA SIZE/COMMON SIZE/USE FACTOR trailer, consistent nonzero
section ranges, and the launcher's final `DLINK END` marker. Unknown diagnostics,
missing/trailing tokens and failed-link reports are rejected before output
creation. It uses the map's final addresses directly, with no invented relocation
bias. The report is the conversion input, so a separate `.SYM` receipt or a
guess about whether a `.SYM` matches a build is unnecessary.

Names are normalized, sorted, checked against the pinned ZSM4 vocabulary and
limited to 12 characters/255 unique records. Exact duplicates coalesce; same
normalized name/different value fails. Aliases, absolute ZERO and FFFFH survive.
The pinned toolchain exports six significant characters by default: the native
fixture demonstrates LONGSYMBOLAA appearing as LONGSY. The converter retains
the final report spelling; it cannot recover lost source spelling. Two exports
colliding in those six characters cause LINK diagnostics and conversion refusal.

The native campaign builds DLINK/DSYM with unchanged ZSM4/LINK and checks host
parity. It links code/data modules with aliases, ZERO/FFFF equates and a long
source export, and rejects native unresolved and export-collision reports.
Independent full-core tests additionally inject loader/capture/file failures,
exercise users 0/16/31 and check exact TPA cutoffs and resident-code canaries.
These are emulator/core results; physical Model 4 qualification is separate.
