# cpmsim ROM qualification assessment

Date: 2026-09-20
Status: feasibility established; BetterCP/M integration and release qualification pending

## Decision

`z80pack/cpmsim` is suitable as the authoritative BetterCP/M 1.0 ROM
qualification environment. Its common-segment mechanism supplies the required
read and instruction-fetch behavior while suppressing CPU and DMA writes. A
small qualification-only guard can turn each attempted write into a deterministic
failure and prevent the guest from moving or disabling the protected boundary.

This finding does **not** qualify the current BetterCP/M image. The present packed
image interleaves mutable state and workspaces with code from `D501h` through
`F3FFh`. Protecting that image today would correctly fail during normal boot and
disk operation. Stateful Stage 3 work and the existing ROMability relocations
must first produce separate RAM and immutable images.

The assessment used BetterCP/M revision `7e7f214` and z80pack revision
`b7a6fa36`. The ordinary z80pack boot/file/RSX test passed before qualification
instrumentation was introduced.

## Proven cpmsim behavior

The existing implementation provides:

- a configurable boundary in `segsize`;
- instruction fetches and reads from the common region at and above that
  boundary;
- suppressed CPU writes through `memwrt()`;
- suppressed controller DMA writes through `dma_write()`;
- a latched violation indication in `wp_common`;
- emulator-side `putmem()` initialization that is independent of runtime write
  protection; and
- MMU boundary and write-protection control through ports 22 and 23.

The proposed patch in `tools/cpmsim-rom-qualification.patch` adds no new memory
model. In a build made with `ROM_QUALIFY=YES`, setting `CPMSIM_ROM_START`:

1. selects the existing upper common segment;
2. protects it before guest execution;
3. exits with status 86 and a PC/address/value/source diagnostic on CPU or DMA
   writes;
4. rejects guest attempts to change ports 22 or 23;
5. reapplies the boundary and protection after emulator reset; and
6. leaves normal cpmsim behavior unchanged when the environment variable is
   absent.

`tools/test_cpmsim_rom_guard.py` builds a disposable patched cpmsim and proves:

- execution from protected memory with a successful write to RAM;
- deterministic CPU-write failure;
- deterministic DMA-write failure through the real disk controller path;
- rejection of guest protection disable;
- rejection of guest boundary movement;
- protection restoration across emulator reset; and
- unchanged behavior when qualification mode is inactive.

The diagnostic form is:

```text
ROM WRITE VIOLATION
PC=D605
ADDRESS=D700
DATA=42
SOURCE=CPU
```

The patch is a qualification aid suitable for carrying in BetterCP/M while an
upstream runtime option is considered. It is inactive in ordinary builds and
contains no BetterCP/M-specific device or memory-layout logic.

## Current memory audit

The current default advertises `0100h..D500h`, or 54,273 usable bytes, preserving
the 53 KiB gate. Engineering report 130 classifies the protected span as:

| Class | Bytes |
|---|---:|
| Executable code | 5,308 |
| Immutable tables, descriptors and messages | 365 |
| Mutable state | 1,028 |
| Stacks and transfer workspaces | 1,224 |
| Alignment/ABI padding | 10 |
| Total | 7,935 |

The 5,673 immutable bytes are a credible ROM payload. The 2,252 mutable and
workspace bytes cannot remain in the protected segment. Their current ownership
is:

| Current area | Bytes requiring RAM | Required treatment |
|---|---:|---|
| History/PDS `D504h..D5C3h` | 192 | Replace with the accepted PDS/RSX ownership model |
| Fixed system region | 90 | Move system stack, live ECB fields and CPX reconstruction records |
| BDOS tail | 109 | Separate persistent variables, call scratch and private stack |
| Extension dispatcher | 5 | Move live control state |
| Disk engine | 35 | Move definitions and controller/session state |
| BIOS | 16 | Move disk-selection and console state |
| File loader | 36 | Put the FCB in shared RAM workspace |
| DPH/binding/ALV/CSV tables | 576 | Materialize live records in the PDS/RAM state area |
| RSX reconstruction table | 41 | Move to the accepted reconstruction owner |
| Directory buffer | 128 | Keep writable in the RAM state/workspace area |
| Physical/module/CONFIG buffer | 1,024 | Move or overlay in RAM; it cannot remain above ROM |
| **Total** | **2,252** | |

This list is the relocation inventory, not a claim that every item needs a
separate allocation. The planned PDS absorbs several existing tables and records;
stacks and mutually exclusive transfer workspaces should share storage where
their lifetimes permit.

## Proposed qualification map

Use the following planning map for the cpmsim ROM build:

```text
0000h..00FFh   writable page zero and low system state
0100h..D500h   writable TPA (54,273 bytes)
D501h..E2FFh   writable fixed state, PDS, stacks and workspaces (3,583 bytes)
E300h..FFFFh   immutable code, constants and default templates (7,424 bytes)
```

`E300h` is the smallest conservative page-aligned boundary justified by the
current measurements. Replacing the existing 192-byte history allocation with a
1.25 KiB planned PDS while pessimistically treating every other current mutable
byte as additional requires 3,340 bytes. The proposed RAM region leaves 243 bytes
even under that deliberately double-counting bound. The current immutable payload
leaves 1,751 bytes in ROM for initialization code and default templates.

Stage 3 may reduce the RAM requirement by assigning HISTORY and other feature
state to their RSXs and by overlaying the upper half of the present one-KiB
workspace. It may also add small descriptors. Therefore `E300h` is a qualification
planning boundary, not a frozen public ABI. The final builder must derive and
check the boundary from the completed layouts.

The cpmsim ROM build may use memory through `FFFFh`; it is a distinct build from
the Model 4 profile whose upper address space is constrained at `F400h`. This does
not reduce the normal TPA and does not expose banking to BetterCP/M.

## Image and boot model

The qualification build should emit two products:

1. an immutable image linked for the protected region, with cold entry in that
   image; and
2. an explicit RAM-layout description used by the cold initializer and tests.

cpmsim loads the immutable image with its existing `-x` Mostek/Intel-HEX path.
That path uses emulator-side `putmem()` before execution and therefore models ROM
installation without performing a guest-visible copy. The load address becomes
the initial PC. `CPMSIM_ROM_START=E300` then enforces the boundary for all runtime
CPU and DMA accesses.

The present disk bootstrap must not load the protected resident image: its DMA
writes would be a qualification failure. The ROM cold entry instead initializes
writable defaults in RAM, establishes page zero and the PDS, initializes the disk
adapter, and reconstructs the command environment from disk. Warm boot continues
to load its disposable reloader and CCP/CPXs in writable memory.

## Subsystem consequences

- **BDOS:** code and constant dispatch data may remain in ROM. Variables, cached
  filesystem context, call scratch and the private stack move to RAM.
- **BIOS and disk:** vectors and routines may remain in ROM. Live drive state,
  bindings, DPHs, ALV/CSV storage, physical definitions and transfer buffers move
  to RAM. Stable DPH pointers continue to point to the live RAM records.
- **CONFIG/FDF:** immutable defaults and catalogue material may remain in ROM.
  Active selections and saved/default working copies are RAM or disk data.
  CONFIG must never patch the immutable template.
- **PDS:** the descriptor may have an immutable template, but the live descriptor,
  allocator, core state and reconstruction records are RAM objects.
- **RSX/CPX/CCP:** loadable modules and their state remain writable below the
  protected boundary. ROM routines may consult their live PDS records but may not
  retain writable tables beside resident code.
- **Reconstruction:** cold boot creates RAM state from immutable defaults; warm
  boot preserves or rebuilds each item according to its accepted lifetime.

No FDF/FDB redesign, bank-qualified pointer or generalized firmware layer is
required.

## Protection configuration

The reproducible qualification sequence is:

```shell
cd cpmsim/srcsim
make ROM_QUALIFY=YES build

CPMSIM_ROM_START=E300 ../cpmsim -z -x BetterCPM-ROM.hex -d /path/to/disks
```

The release runner must verify that the activation banner contains the expected
boundary. Exit 86 is always a failed qualification run. Qualification artifacts
must record the BetterCP/M and z80pack revisions, immutable-image checksum,
boundary, RAM map and test results.

## Remaining integration and acceptance work

cpmsim feasibility and guard instrumentation are proven. The authoritative 1.0
profile is not yet ready for scope closure because the following BetterCP/M work
remains:

1. finish Stage 3 state ownership and reconstruction;
2. relocate every item in the inventory and generate separate ROM/RAM maps;
3. implement the ROM cold initializer and immutable image builder;
4. boot the resulting image under the locked guard;
5. exercise cold boot, repeated warm boots, transient return, CCP/CPX/RSX
   reconstruction, disk I/O and CONFIG operations;
6. run all applicable BetterCP/M and CP/M 2.2 compatibility cases;
7. include deliberate CPU, DMA and control-port violations; and
8. publish advertised/usable TPA, PDS, fixed RAM, ROM and optional-module costs.

The acceptance matrix must run with the guard active for its entire lifecycle.
ROM-specific checks supplement the compatibility suite rather than replacing it.

## Recommendation

Adopt cpmsim as the selected 1.0 ROM qualification environment, subject to final
approval when the relocated BetterCP/M image completes the integration matrix.
Proceed with the `E300h` planning boundary and the qualification-only guard; do
not freeze the exact boundary until Stage 3 produces the final state inventory.

Because the complete BetterCP/M ROM image has not yet passed the matrix, leave
`TODO.md` and `docs/releases/1.0-SCOPE-DRAFT.md` unchanged. Once it passes, replace
their remaining environment-selection item with the exact cpmsim revision,
boundary, image checksum/build procedure and acceptance evidence.
