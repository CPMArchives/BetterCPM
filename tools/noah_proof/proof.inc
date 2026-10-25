; NOAH feasibility profile 1. Not the production writer/step ABI.
; Shared by cross/native examples. Include archive.inc and codec.inc first.
; Existing AS ABI 1 and CX ABI 1 remain unchanged, including register rules.
; All addresses/lengths little endian. No memory is emitted here.
NP_VERSION EQU 1
NP_HEADER EQU 128
NP_CRC EQU 124
NP_INDEX EQU 24
NP_ENTRY_SIZE EQU 16
NP_MODULES EQU 2
; Header: 0 magic(4), 4 version(2), 6 count(2), 8 build(8),
; 16 total physical bytes(4), 20 header size(2), 22 reserved(2).
; Entry: id(2), AS/CX ABI(2), file offset(4), code length(2),
; load address(2), entry address(2), workspace bytes(2).
; Entries 1=LBR, 2=UNCR. Reserved header bytes are zero.
; CRC-32/ISO-HDLC covers the entire record-aligned file with bytes 124..127
; treated as zero. Includes index, lengths, bodies and record padding.
; Profile binds the complete header except CRC to the executable build;
; no untrusted address is used for loading or dispatch. All modules are
; loaded and validated together before execution; every invocation reloads.
; Future demand loading must revalidate on every reopen (not implemented).
; IX=AS/CX context, IY and alternate banks preserved by library entries.
; Ordinary registers scratch; NC success; C/A explicit AS_*/CS_* outcome.
; Callbacks are resident, never in either replaceable module window.
; Records, contexts, selection reservation, stack and DMA are outside code.
