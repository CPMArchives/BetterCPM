; Model II CRT/keyboard backend. See docs/platform/MODEL2-PORT.md.
; FFh writes select bank 1; RTC NMI is disabled in both mappings.
; Only the two straight-line VRAM routines may run with video enabled.
; No stack access, indirect calls, or data in the overlay during that interval.
; Preserve the caller's interrupt enable when borrowing its address window.
PL_INIT:
IO_COLD: LD A,095H
        LD (0003H),A
        XOR A
        LD (LY_RSTA),A
        LD A,10
        OUT (0FCH),A
        LD A,020H
        OUT (0FDH),A                    ; disable hardware cursor; monitor draws cursor
        JP M2_CLEAR
PL_CONST:
        IN A,(0FFH)
        AND 080H
        RET
PL_CONIN:
        CALL PL_CONST
        JR Z,PL_CONIN
        IN A,(0FCH)
        AND 07FH
        RET
M2_CURSOR:
        LD A,C
        OR A
        JR Z,M2_SUPPORTED
        SET 7,C
        CALL PL_CONOT
M2_SUPPORTED:
        LD A,1
        RET
PL_CONOT:
        LD A,C
        LD HL,(M2_POS)
        LD DE,80
        CP 28
        JR Z,M2_CLEAR
        CP 13
        JR Z,M2_CR
        CP 10
        JR Z,M2_LF
        CP 8
        JR Z,M2_BS
        LD A,I
        DI
        PUSH AF
        LD A,081H
        OUT (0FFH),A
        LD (HL),C
        LD A,1
        OUT (0FFH),A
        POP AF
        JP PO,M2_NEXT
        EI
M2_NEXT:INC HL
        LD A,(M2_COL)
        INC A
        CP 80
        JR C,M2_STORE
        XOR A
        JR M2_STORE
M2_CR:  LD A,(M2_COL)
        LD E,A
        OR A
        SBC HL,DE
        XOR A
        JR M2_STORE
M2_BS:  LD A,(M2_COL)
        OR A
        RET Z
        DEC HL
        DEC A
        JR M2_STORE
M2_LF:  ADD HL,DE
        LD A,(M2_COL)
M2_STORE:
        LD (M2_COL),A
        LD DE,0FF80H                    ; first address after 24 rows of 80
        OR A
        SBC HL,DE
        ADD HL,DE
        JR NC,M2_SCROLL                 ; ADD sets carry iff the subtraction borrowed
        LD (M2_POS),HL
        RET
M2_SCROLL:
        LD A,(M2_COL)
        ADD A,030H
        LD L,A
        LD H,0FFH
        LD (M2_POS),HL
        LD A,I
        DI
        PUSH AF
        LD A,081H
        OUT (0FFH),A
        LD HL,0F850H
        LD DE,0F800H
        LD BC,1840
        LDIR
        LD BC,79
        JR M2_FILL
M2_CLEAR:
        XOR A
        LD (M2_COL),A
        LD HL,0F800H
        LD (M2_POS),HL
        LD A,I
        DI
        PUSH AF
        LD A,081H
        OUT (0FFH),A
        LD DE,0F800H
        LD BC,1919
M2_FILL:
        LD H,D
        LD L,E
        LD (HL),020H
        INC DE
        LDIR
        LD A,1
        OUT (0FFH),A
        POP AF
        RET PO
        EI
        RET
M2_POS: DW 0F800H
M2_COL: DB 0
M2_VIDEO_END:
        IF M2_VIDEO_END GT 0F800H
        DB M2_CONSOLE_EXECUTES_INSIDE_VIDEO_WINDOW
        ENDIF
