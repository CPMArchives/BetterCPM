; COMMON RAM ASSIGNMENTS -- no hidden RAM or bank switching required.
; TPA is 0100H through LY_TPA-1.  The three-byte jump and command
; history follow it.  The command processor itself is reconstructible.
; LY_RSX is optional: one K is charged only with an active RSX profile.
; LY_CFG reuses LY_BUF; LY_LOAD and its stack borrow the finished TPA.
; Keep build-time size checks: even a twelve-byte overrun is fatal.
LY_SYS          EQU     0D5C4H
LY_BDOS         EQU     0D6BCH
LY_EXT          EQU     0E49FH
LY_DISK         EQU     0E648H
LY_BIOS         EQU     0EA08H
LY_FILE         EQU     0EC86H
LY_TAB          EQU     0ED17H
LY_RSTA         EQU     0EF57H
LY_DIR          EQU     0EF80H
LY_BUF          EQU     0F000H
LY_RSX          EQU     0D104H
LY_LOAD         EQU     00100H
LY_CFG          EQU     0F000H
LY_CPX          EQU     0F009H
LY_STKL         EQU     00480H
LY_STKT         EQU     00500H
LY_LIMIT        EQU     0F400H
LY_RAMEND       EQU     0F400H
LY_HIST         EQU     0D504H
LY_TPA          EQU     0D501H
LY_SECTS        EQU     0000DH

; PDS ABI 1 static-layout bridge. The versioned system descriptor at LY_PDSD
; publishes LY_PDSF as its live lower boundary. Until configurable sizing is
; implemented, the upper boundary is LY_PDST and boot size equals current size.
LY_PDSD         EQU     LY_SYS+080H
LY_PDST         EQU     LY_SYS
LY_PDSF         EQU     LY_SYS+088H
LY_PDSS         EQU     LY_SYS-LY_HIST

; Protected COM handoff and shared filename state (checked by builders).
LY_COMSTART     EQU     LY_SYS+074H
LY_COMDONE      EQU     LY_SYS+003H
LY_FCB          EQU     LY_FILE+109
