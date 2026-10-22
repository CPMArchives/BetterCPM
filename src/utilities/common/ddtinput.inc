; ********************************************************************************
; *                 BetterCP/M DDT Shared Input Binding                           *
; ********************************************************************************
; Shared editor binding for DDT's existing counted command buffer.
; The core's entry vector and 32-byte grammar remain owned by DDT.
EDITBUF EQU COMBUF
EDITLEN EQU CURLEN
DU_WIDTH EQU 24

DU_GET:                                 ; read one provisional debugger line
        LD (DU_SSP),SP
        LD SP,DU_TOP
        PUSH BC
        PUSH DE
        PUSH HL
        XOR A
        LD (DU_POS),A
        CALL DU_INIT
DU_AGAIN:                               ; redraw only after recognized editing
        CALL DU_DRAW
DU_READ:                                ; direct input keeps control keys local
        LD C,6
        LD E,255
        CALL DU_SVC
        OR A
        JR Z,DU_READ
        CP 3
        JP Z,0000H
        CP 21
        JR Z,DU_RESET
        CP 24
        JR Z,DU_RESET
        CALL UE_KEY
        CP UI_SEND
        JR Z,DU_DONE
        CP UI_ABORT
        JR Z,DU_ABORT
        CP UI_LIMIT
        JR Z,DU_BELL
        CP UI_SKIP
        JR Z,DU_READ
        JR DU_AGAIN
DU_RESET:                               ; legacy clear aliases affect text only
        CALL DU_INIT
        JR DU_AGAIN
DU_BELL:                                ; refuse excess input without submission
        LD A,7
        CALL DU_PUT
        JR DU_READ
DU_INIT:                                ; initialize caller-owned shared state
        LD A,32
        LD B,0
        LD HL,0
        CALL UE_INIT
        RET
DU_DONE:                                ; publish unchanged text to the DDT parser
        CALL DU_BLANK
        LD A,(EDITLEN)
        LD B,A
        LD HL,EDITBUF
        OR A
        JR Z,DU_END
DU_ECHO:                                ; leave the complete submitted line visible
        LD A,(HL)
        CALL DU_PUT
        INC HL
        DJNZ DU_ECHO
DU_END:                                 ; match buffered input's final carriage return
        LD A,13
        CALL DU_PUT
        LD HL,COMBUF
        LD (NEXTCOM),HL
        POP HL
        POP DE
        POP BC
        LD SP,(DU_SSP)
        RET
DU_ABORT:                               ; discard provisional text and core frames
        CALL DU_BLANK
        LD SP,STACK-12
        JP START
DU_SVC:                                 ; BDOS may destroy all pointer registers
        PUSH BC
        PUSH DE
        PUSH HL
        CALL TRAPAD
        POP HL
        POP DE
        POP BC
        RET
DU_PUT:                                 ; direct output cannot consume editing input
        PUSH AF
        PUSH BC
        PUSH DE
        PUSH HL
        LD E,A
        LD C,6
        CALL TRAPAD
        POP HL
        POP DE
        POP BC
        POP AF
        RET
DU_HOME:                                ; return to field start without erasing prefix
        LD A,(DU_POS)
        OR A
        RET Z
        LD B,A
DU_BACK:                                ; position relative to the caller's prefix
        LD A,8
        CALL DU_PUT
        DJNZ DU_BACK
        RET
DU_BLANK:                               ; erase stale input and return to field start
        CALL DU_HOME
        LD B,DU_WIDTH
DU_SPACE:                               ; clear each visible field cell
        LD A,' '
        CALL DU_PUT
        DJNZ DU_SPACE
        LD B,DU_WIDTH
        CALL DU_BACK
        XOR A
        LD (DU_POS),A
        RET
DU_DRAW:                                ; render a bounded horizontally scrolled field
        CALL DU_HOME
        LD A,(EDITCUR)
        LD B,A
        LD A,(EDITSTART)
        CP B
        JR C,DU_RIGHT
        JR Z,DU_RIGHT
        LD A,B
        LD (EDITSTART),A
DU_RIGHT:                               ; scroll when the caret leaves the viewport
        LD A,(EDITSTART)
        LD C,A
        LD A,B
        SUB C
        CP DU_WIDTH
        JR C,DU_WINDOW
        LD A,B
        SUB DU_WIDTH-1
        LD (EDITSTART),A
DU_WINDOW:                              ; bind the visible buffer window
        LD A,(EDITSTART)
        LD C,A
        LD A,(EDITCUR)
        SUB C
        LD (DU_POS),A
        LD B,0
        LD HL,EDITBUF
        ADD HL,BC
        LD B,DU_WIDTH
DU_CELL:                                ; emit each cell without consuming input
        LD A,(EDITLEN)
        CP C
        LD A,' '
        JR C,DU_GLYPH
        JR NZ,DU_DATA
        LD A,(EDITCUR)
        CP C
        LD A,' '
        JR NZ,DU_GLYPH
        LD A,'_'
        JR DU_GLYPH
DU_DATA:                                ; fetch a printable buffer character
        LD A,(HL)
DU_GLYPH:                               ; write the cell and advance
        CALL DU_PUT
        INC HL
        INC C
        DJNZ DU_CELL
        LD A,(DU_POS)
        LD B,A
        LD A,DU_WIDTH
        SUB B
        LD B,A
        JP DU_BACK
EDITCUR: DS 1                           ; insertion index
EDITSTART: DS 1                         ; viewport origin
EDITMAX: DS 1                           ; bounded input capacity
EDITPROMPT: DS 2                        ; unused opaque library prompt
DU_POS: DS 1                            ; physical caret relative to field start
DU_SSP: DS 2                            ; core stack restored on accepted input
        DS 256                          ; private editor and BDOS callback stack
DU_TOP:                                 ; top of the private editor stack
