; Transient-only frozen wildcard source list. DU-only destinations retain
; source names: cross-DU mapping is injective and cannot overlap source files.
; Capacity overflow is detected during collection, before any destination I/O.
BC_WSTART:
        LD      A,(BC_COLEN)
        OR      A
        JP      NZ,BC_CSYNT             ; wildcard targets must be a DU alone
        LD      A,(BC_CSDRV)
        LD      HL,BC_CDDRV
        CP      (HL)
        JR      NZ,BC_WINIT
        LD      A,(BC_CSUSR)
        LD      HL,BC_CDUSR
        CP      (HL)
        JP      Z,BC_CEXIST             ; reject source/destination DU alias
BC_WINIT:
        XOR     A
        LD      (CT_COUNT),A
        LD      HL,CT_NAMES
        LD      (CT_END),HL
        LD      HL,BC_FCB
        LD      DE,BC_WFCB
        LD      BC,36
        LDIR
        LD      HL,BC_WLAST
        LD      B,11
        XOR     A
BC_WZERO:
        LD      (HL),A
        INC     HL
        DJNZ    BC_WZERO
        INC     A
        LD      (BC_WACTIVE),A
BC_WNEXT:
        CALL    BC_CSELS
        LD      DE,BC_DMA
        LD      C,26
        CALL    BDOS
        XOR     A
        LD      (BC_WBEST),A
        LD      A,'?'
        LD      (BC_WFCB+12),A
        LD      DE,BC_WFCB
        LD      C,17
BC_WSEARCH:
        CALL    BDOS
        CP      0FFH
        JR      Z,BC_WFOUND
        ADD     A,A
        ADD     A,A
        ADD     A,A
        ADD     A,A
        ADD     A,A
        LD      E,A
        LD      D,0
        LD      HL,BC_DMA+1
        ADD     HL,DE
        LD      DE,BC_WNAME
        LD      B,11
BC_WNCP:
        LD      A,(HL)
        AND     07FH
        LD      (DE),A
        INC     HL
        INC     DE
        DJNZ    BC_WNCP
        LD      HL,BC_WNAME
        LD      DE,BC_WLAST
        CALL    BC_WCMP
        JR      C,BC_WCONT
        JR      Z,BC_WCONT
        LD      A,(BC_WBEST)
        OR      A
        JR      Z,BC_WSAVE
        LD      HL,BC_WNAME
        LD      DE,BC_WBEST
        CALL    BC_WCMP
        JR      NC,BC_WCONT
BC_WSAVE:
        LD      HL,BC_WNAME
        LD      DE,BC_WBEST
        LD      BC,11
        LDIR
BC_WCONT:
        LD      DE,BC_WFCB
        LD      C,18
        JR      BC_WSEARCH
BC_WFOUND:
        LD      A,(BC_WBEST)
        OR      A
        JP      NZ,CT_COLLECT
        LD      A,(BC_WLAST)
        OR      A
        JP      NZ,CT_BEGIN
        LD      DE,BC_NOFILE
        CALL    BC_PRINT
        JP      BC_WEND
CT_COLLECT:
        LD      A,(CT_COUNT)
        CP      64
        JP      Z,CT_FULL
        INC     A
        LD      (CT_COUNT),A
        LD      HL,BC_WBEST
        LD      DE,(CT_END)
        LD      BC,11
        LDIR
        LD      (CT_END),DE
        LD      HL,BC_WBEST
        LD      DE,BC_WLAST
        LD      BC,11
        LDIR
        JP      BC_WNEXT
CT_FULL:
        LD      DE,CT_FULLMSG
        CALL    BC_PRINT
        JP      BC_WEND
CT_BEGIN:
        LD      A,(CT_COUNT)
        LD      (CT_LEFT),A
        LD      HL,CT_NAMES
        LD      (CT_CURSOR),HL
CT_NEXT:
        LD      A,(CT_LEFT)
        OR      A
        JP      Z,BC_WEND
        LD      HL,(CT_CURSOR)
        LD      DE,BC_WBEST
        LD      BC,11
        LDIR
CT_COPY:
        LD      HL,BC_FCB
        LD      DE,BC_FCB+1
        LD      BC,35
        LD      (HL),0
        LDIR
        LD      HL,BC_NEWFCB
        LD      DE,BC_NEWFCB+1
        LD      BC,35
        LD      (HL),0
        LDIR
        LD      HL,BC_WBEST
        LD      DE,BC_FCB+1
        LD      BC,11
        LDIR
        LD      HL,BC_WBEST
        LD      DE,BC_NEWFCB+1
        LD      BC,11
        LDIR
        XOR     A
        LD      (BC_WERROR),A
        LD      (BC_CMADE),A
        CALL    BC_COPEN
        LD      A,(BC_WERROR)
        OR      A
        JP      NZ,BC_WEND
        LD      HL,(CT_CURSOR)
        LD      DE,11
        ADD     HL,DE
        LD      (CT_CURSOR),HL
        LD      HL,CT_LEFT
        DEC     (HL)
        JP      CT_NEXT
BC_WEND:
        XOR     A
        LD      (BC_WACTIVE),A
        JP      BC_COK
