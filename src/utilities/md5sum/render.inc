; Conventional untagged md5sum entries, shared by console and saved output.
HEADERS:
        RET
PUTNAME:
        LD HL,LASTNAME
        LD B,8
MDBASE:
        LD A,(HL)
        CP ' '
        CALL NZ,PUT
        INC HL
        DJNZ MDBASE
        LD A,(HL)
        CP ' '
        RET Z
        LD A,'.'
        CALL PUT
        LD B,3
MDEXT:
        LD A,(HL)
        CP ' '
        CALL NZ,PUT
        INC HL
        DJNZ MDEXT
        RET
RESULTRO:
        LD A,(NARROW)
        OR A
        JR Z,MDWIDE
        CALL NEWLINE
        CALL PUTNAME
        CALL ENDLINE
        CALL NEWLINE
        LD HL,CVALUES
        CALL MDDIGEST
        CALL ENDLINE
MDWIDE:
        CALL NEWLINE
        LD HL,CVALUES
        CALL MDDIGEST
        LD A,' '
        CALL PUT
        LD A,'*'
        CALL PUT
        CALL PUTNAME
        XOR A
        CALL PUT
        LD A,(NARROW)
        OR A
        JR NZ,MDSAVE
        LD HL,LINE
        CALL TEXT
        CALL NL
MDSAVE:
        JP WLINE
; Digest serialization is byte order, not numeric word order.
MDDIGEST:
        LD B,16
MDHEX:
        LD A,(HL)
        PUSH AF
        RRCA
        RRCA
        RRCA
        RRCA
        CALL MDNIBBLE
        POP AF
        CALL MDNIBBLE
        INC HL
        DJNZ MDHEX
        RET
MDNIBBLE:
        AND 15
        ADD A,'0'
        CP '9'+1
        JR C,MDPUTHEX
        ADD A,'a'-'9'-1
MDPUTHEX:
        JP PUT
