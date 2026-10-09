; Transient-only frozen source list and positional destination mapping.
; Capacity overflow is detected during collection, before any destination I/O.
BC_WSTART:
        LD      HL,BC_NEWFCB+1
        LD      DE,CT_PATTERN
        LD      BC,11
        LDIR
        LD      A,(BC_COLEN)
        OR      A
        JR      NZ,BC_WINIT
        LD      HL,CT_PATTERN
        LD      B,11
CT_INHERIT:
        LD      (HL),'?'
        INC     HL
        DJNZ    CT_INHERIT
BC_WINIT:
        XOR     A
        LD      (CT_COUNT),A
        LD      HL,CT_NAMES
        LD      (CT_END),HL
        LD      HL,0
        LD      (CTDUIDX),HL
        LD      HL,CT_DUS
        LD      (CTDUENDP),HL
        LD      HL,BC_FCB
        LD      DE,BC_WFCB
        LD      BC,36
        LDIR
        JP      CTDUNEXT
BC_WRESET:
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
        JP      CTDUNEXT
CT_COLLECT:
        LD      A,(CT_COUNT)
        CP      64
        JP      Z,CT_FULL
        INC     A
        LD      (CT_COUNT),A
        LD      HL,(CTDUENDP)
        LD      A,(BC_CSDRV)
        LD      (HL),A
        INC     HL
        LD      A,(BC_CSUSR)
        LD      (HL),A
        INC     HL
        LD      (CTDUENDP),HL
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
        LD      HL,CT_DUS
        LD      (CTDUCUR),HL
        LD      HL,CT_TARGETS
        LD      (CT_DCUR),HL
        LD      A,(CT_COUNT)
        LD      (CT_LEFT),A
        LD      HL,CT_NAMES
        LD      (CT_CURSOR),HL
CT_NEXT:
        LD      A,(CT_LEFT)
        OR      A
        JP      Z,BC_WEND
        LD      HL,(CTDUCUR)
        LD      A,(HL)
        LD      (BC_CSDRV),A
        INC     HL
        LD      A,(HL)
        LD      (BC_CSUSR),A
        INC     HL
        LD      (CTDUCUR),HL
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
        LD      HL,(CT_DCUR)
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
        LD      HL,(CT_DCUR)
        LD      DE,11
        ADD     HL,DE
        LD      (CT_DCUR),HL
        LD      HL,CT_LEFT
        DEC     (HL)
        JP      CT_NEXT
BC_WEND:
        XOR     A
        LD      (BC_WACTIVE),A
        JP      BC_COK

; Build and check the complete mapping before any destination is opened.
CTPREF:
        XOR     A
        LD      (CT_DONE),A
        LD      HL,CT_NAMES
        LD      (CT_CURSOR),HL
        LD      HL,CT_TARGETS
        LD      (CT_DCUR),HL
CTMAPNXT:
        LD      HL,(CT_CURSOR)
        LD      DE,(CT_DCUR)
        CALL    CTGEN
        JP      C,CTBADNAM
        LD      A,(CT_DONE)
        OR      A
        JR      Z,CTSRCCK
        LD      (CTSCAN),A
        LD      HL,CT_TARGETS
        CALL    CTCKSET
        JP      Z,CTCONFL
CTSRCCK:
        CALL    CTSRCTST
        JP      Z,CTCONFL
CTMAPADV:
        LD      HL,(CT_CURSOR)
        LD      DE,11
        ADD     HL,DE
        LD      (CT_CURSOR),HL
        LD      HL,(CT_DCUR)
        ADD     HL,DE
        LD      (CT_DCUR),HL
        LD      HL,CT_DONE
        INC     (HL)
        LD      A,(CT_COUNT)
        CP      (HL)
        JP      NZ,CTMAPNXT
        JP      CT_BEGIN
CTCKSET:
        LD      (CTCKPTR),HL
CTCKNEXT:
        LD      HL,(CTCKPTR)
        LD      DE,(CT_DCUR)
        CALL    BC_WCMP
        RET     Z
        LD      HL,(CTCKPTR)
        LD      DE,11
        ADD     HL,DE
        LD      (CTCKPTR),HL
        LD      HL,CTSCAN
        DEC     (HL)
        JR      NZ,CTCKNEXT
        LD      A,1
        OR      A                       ; nonzero means no collision
        RET
CTCONFL:
        LD      DE,CT_MAPMSG
        CALL    BC_PRINT
        JP      BC_WEND
CTBADNAM:
        LD      DE,CT_NAMEMSG
        CALL    BC_PRINT
        JP      BC_WEND

; Positional substitution over the fixed 8+3 fields. PFCB expands terminal
; stars into question marks; both copy the corresponding padded source bytes.
CTGEN:
        PUSH    DE
        PUSH    HL
        LD      HL,CT_PATTERN
        LD      (CTGPTR),HL
        POP     HL
        LD      B,11
CTGBYTE:
        PUSH    HL
        LD      HL,(CTGPTR)
        LD      A,(HL)
        INC     HL
        LD      (CTGPTR),HL
        POP     HL
        CP      '?'
        JR      NZ,CTGSTORE
        LD      A,(HL)
CTGSTORE:
        LD      (DE),A
        INC     HL
        INC     DE
        DJNZ    CTGBYTE
        POP     HL
        LD      B,8
        CALL    CTVFIELD
        RET     C
        LD      A,C
        OR      A
        JR      Z,CT_INVALID           ; empty name, unlike empty extension
        LD      B,3
CTVFIELD:
        LD      C,0                    ; count nonpadding characters
        LD      E,0                    ; padding already seen
CTVBYTE:
        LD      A,(HL)
        CP      ' '
        JR      NZ,CTNONSP
        LD      E,1
        JR      CTVNEXT
CTNONSP:
        LD      A,E
        OR      A
        JR      NZ,CT_INVALID
        LD      A,(HL)
        CP      21H
        JR      C,CT_INVALID
        CP      7FH
        JR      NC,CT_INVALID
        PUSH    HL
        PUSH    BC
        LD      HL,CTBADCH
        LD      B,14
CT_BADCHAR:
        CP      (HL)
        JR      Z,CTCHBAD
        INC     HL
        DJNZ    CT_BADCHAR
        POP     BC
        POP     HL
        INC     C
CTVNEXT:
        INC     HL
        DJNZ    CTVBYTE
        OR      A
        RET
CTCHBAD:
        POP     BC
        POP     HL
CT_INVALID:
        SCF
        RET
CTBADCH:
        DB      '*?.:;[]=<>/,'
        DB      05CH,022H

; Destination wildcards do not turn an exact source into a wildcard search.
CTDWILD:
        PUSH    HL
        PUSH    DE
        LD      HL,(BC_COFCP)
        LD      DE,BC_NEWFCB
        OR      A
        SBC     HL,DE
        POP     DE
        POP     HL
        JP      NZ,BC_CVBAD
        OR      A
        RET
