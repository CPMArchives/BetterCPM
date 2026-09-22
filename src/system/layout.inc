; ********************************************************************************
; *                         BetterCP/M Common RAM Layout                         *
; *                                                                              *
; * Defines the shared resident, transient, extension, workspace, and protected  *
; * memory assignments. BetterCP/M requires no hidden RAM or bank switching;     *
; * build-time size checks enforce every boundary.                               *
; ********************************************************************************

  ; TPA is 0100H through LY_TPA-1.  The three-byte jump and command
  ; history follow it.  The command processor itself is reconstructible.
  ; LY_RSX is optional: one K is charged only with an active RSX profile.
  ; LY_CFG reuses LY_BUF; LY_LOAD and its stack borrow the finished TPA.
  ; Keep build-time size checks: even a twelve-byte overrun is fatal.

; -------------------------------------------------------------------------------
; Resident and Reconstructible Regions
; -------------------------------------------------------------------------------

LY_SYS          EQU     0D5C4H          ; resident system gateway base
LY_BDOS         EQU     0D6BCH          ; unified BDOS base
LY_EXT          EQU     0E49FH          ; protected extension-services base
LY_DISK         EQU     0E648H          ; resident disk-service base
LY_BIOS         EQU     0EA08H          ; compatibility BIOS base
LY_FILE         EQU     0EC86H          ; shared file-loader base
LY_TAB          EQU     0ED17H          ; resident disk-table base
LY_RSTA         EQU     0EF57H          ; resident-state workspace base
LY_DIR          EQU     0EF80H          ; directory buffer address
LY_BUF          EQU     0F000H          ; shared sector/overlay buffer
LY_RSX          EQU     0D104H          ; optional protected RSX region

; -------------------------------------------------------------------------------
; Transient and Shared Workspace
; -------------------------------------------------------------------------------

LY_LOAD         EQU     00100H          ; transient loader address
LY_CFG          EQU     0F000H          ; configuration-overlay address
LY_CPX          EQU     0F009H          ; reconstructible CPX region
LY_STKL         EQU     00480H          ; transient loader stack low
LY_STKT         EQU     00500H          ; transient loader stack top
LY_LIMIT        EQU     0F400H          ; resident-memory upper limit
LY_RAMEND       EQU     0F400H          ; available RAM end
LY_HIST         EQU     0D504H          ; persistent command-history base
LY_TPA          EQU     0D501H          ; exclusive TPA upper bound
LY_SECTS        EQU     0000DH          ; resident system sector count

; -------------------------------------------------------------------------------
; PDS ABI 1 Static-Layout Bridge
; -------------------------------------------------------------------------------

  ; PDS ABI 1 static-layout bridge. The versioned system descriptor at LY_PDSD
  ; publishes LY_PDSF as its live lower boundary. Until configurable sizing is
  ; implemented, the upper boundary is LY_PDST and boot size equals current size.
LY_PDSD         EQU     LY_SYS+080H     ; PDS versioned descriptor address
LY_PDST         EQU     LY_SYS          ; PDS upper boundary
LY_PDSF         EQU     LY_SYS+088H     ; PDS live lower-bound field
LY_PDSS         EQU     LY_SYS-LY_HIST  ; current protected-data size

; -------------------------------------------------------------------------------
; Protected COM Handoff and Shared Filename State
; -------------------------------------------------------------------------------

  ; Protected COM handoff and shared filename state (checked by builders).
LY_COMSTART     EQU     LY_SYS+074H     ; protected COM handoff state
LY_COMDONE      EQU     LY_SYS+003H     ; protected COM return entry
LY_FCB          EQU     LY_FILE+109     ; shared filename FCB address
