# Engineering Specification 95: Command Processor Extensions

Date: 2026-09-02

## Decision

BetterCP/M distinguishes Resident System Extensions (RSXs) from Command
Processor Extensions (CPXs). An RSX extends or intercepts BDOS services. A
CPX extends the command processor with facilities such as scripting,
conditionals, aliases, search rules, or additional commands.

The intended high-to-low ordering is BIOS, core BDOS, RSXs, CPXs, reloadable
CCP, and TPA. RSXs and CPXs may move the CCP and TPA ceiling downward, but do
not require the BIOS or core BDOS above them to be relocated.

## Initial CPX ABI

The CCP now implements a forward CPX dispatch chain. A four-byte CPX header
contains the next-header address followed by the command-entry address. Zero
terminates the chain.

At command entry:

- `DE` points to the upper-case command text;
- `B` contains its length;
- carry set on return means the command was handled;
- carry clear declines the command and continues the chain; and
- the CPX preserves `SP`, `IX`, `IY`, and the command buffer.

Compatibility-resident CCP commands are recognized before CPX dispatch. If
every CPX declines, the CCP performs ordinary `.COM` lookup. This ordering
allows extensions without silently replacing required CP/M command behavior.

The initial system boots with a null chain. Loader, installation, removal,
discovery, and version negotiation remain later CPX increments.

## Memory-layout correction

The former CCP occupied 1,065 of 1,066 bytes in an incidental gap at
`E8D6h..ECFFh`. CPX support deliberately ends that exact-fit arrangement.
The current CCP is placed at `B000h` with a 2K implementation
budget through `B7FFh`. `B800h..BFFDh` is the initial extension arena and
`BFFEh..BFFFh` holds the CPX chain head. The page-zero gateway remains at
`C000h`, and the BDOS remains at `C100h`.

This fixed arena is a bring-up implementation of the ABI, not the final
dynamic allocator. It is presently protected from transient loading because
WBOOT does not yet reload it. A later loader will reconstruct the command
image and derive the CCP address and TPA ceiling from the actual configured
RSX and CPX images; only then may transient programs reclaim command memory.

The lower resident base enlarges the TRS-80 system image from 26 to 34
physical sectors. It remains wholly inside the two reserved MM 790K system
tracks and does not change the CP/M filesystem beginning at track offset 2.

## Verification

The focused CCP test installs two synthetic CPX headers: the first declines
the command and the second accepts it. This verifies forward chaining and the
carry-result contract while the production boot image retains an empty chain.
Native CP/M and cross builds must remain byte-identical.
