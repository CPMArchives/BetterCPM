; ********************************************************************************
; *                    TRS-80 Model 4 Hardware Constants                         *
; *                                                                              *
; * Defines the Model 4 I/O ports, memory addresses, floppy-controller commands, *
; * and bootstrap locations used by the BetterCP/M platform-specific code.       *
; ********************************************************************************

; -------------------------------------------------------------------------------
; Hardware I/O Ports
; -------------------------------------------------------------------------------

OPTREG          EQU     084H            ; memory/video options register
INTMASK         EQU     0E0H            ; interrupt-mask register
NMIREG          EQU     0E4H            ; NMI-mask register
MODLATCH        EQU     0ECH            ; mode latch
FDCSTATUS       EQU     0F0H            ; floppy-controller status port
FDCCOMMAND      EQU     0F0H            ; floppy-controller command port
FDCTRACK        EQU     0F1H            ; floppy-controller track port
FDCSECTOR       EQU     0F2H            ; floppy-controller sector port
FDCDATA         EQU     0F3H            ; floppy-controller data port
FDCSELECT       EQU     0F4H            ; floppy drive-select port

; -------------------------------------------------------------------------------
; Memory Map and Display Geometry
; -------------------------------------------------------------------------------

NMIVECTOR       EQU     0066H           ; Z80 NMI vector
VIDEOBASE       EQU     0F800H          ; video-memory base
VIDEOCOLS       EQU     80              ; display columns
VIDEOROWS       EQU     24              ; display rows
VIDEOSIZE       EQU     VIDEOCOLS*VIDEOROWS ; video-memory size
VIDEOEND        EQU     VIDEOBASE+VIDEOSIZE ; end of video memory
KEYBASE         EQU     0F400H          ; keyboard-matrix base
BOOTBASE        EQU     04300H          ; ROM stage-zero load address
STAGE1BASE      EQU     05000H          ; stage-one load address
DISKBUFFER      EQU     06000H          ; bootstrap disk buffer
STAGE1STACK     EQU     07000H          ; stage-one stack address

; -------------------------------------------------------------------------------
; Floppy Commands and Bootstrap Sectors
; -------------------------------------------------------------------------------

FDCREAD         EQU     080H            ; floppy read-sector command
FDCRESTORE      EQU     008H            ; floppy restore command
FDCSEEK         EQU     018H            ; floppy seek command
FDCWRITE        EQU     0A0H            ; floppy write-sector command
STAGE1SECTOR    EQU     3               ; stage-one system-track sector
VERIFYSECTOR    EQU     5               ; bring-up verification sector
