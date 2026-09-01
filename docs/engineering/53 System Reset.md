# Engineering Specification 53: System Reset

## Milestone

BetterCP/M now implements BDOS function 0 (System Reset). All 39 functions
defined by CP/M 2.2 are present; reserved functions 38 and 39 remain unsupported.

## Contract

Function 0 terminates the transient program by transferring control to the BIOS
`WBOOT` vector. It does not restore the BDOS caller's stack or return through the
application call site. This is the same programmed warm-start boundary reached
through page-zero `JMP 0000h`.

The transfer deliberately goes through the public BIOS vector rather than
calling a platform implementation directly. Reconstruction of the command
environment, page-zero gateways, and default DMA state belongs to WBOOT and the
future CCP integration, not to the BDOS dispatcher.

## Present limitation

The provisional BIOS WBOOT entry remains a non-returning stop loop because the
BetterCP/M CCP has not yet been implemented. Function 0 therefore reaches the
correct architectural boundary but cannot yet resume an interactive command
environment. That becomes the next system-level development phase.

## Verification

Direct-BDOS and application `CALL 0005h` tests temporarily replace only the
BIOS WBOOT vector with an observable recovery shim. Both prove that Function 0
reaches WBOOT; the production vector is then restored. The ordinary BIOS test
continues to verify that its provisional WBOOT implementation is non-returning.

Native CP/M ZSM4/Digital Research LINK and the host assembler must produce
byte-identical BDOS and resident-system binaries.

## Next increment

Define and implement the first CCP command-loop milestone so WBOOT can
reconstruct and enter a usable BetterCP/M command environment.
