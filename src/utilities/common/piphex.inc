; DRI HEXRECORD validator, used by the text H/I transfer layer.
; HL/B: immutable input span beginning with colon, at most 255 bytes.
; A: 0 valid data, 1 zero-length terminator prefix, 2 invalid digit/form,
;    3 checksum error, 4 record too long, 5 more input required.
; PH_USED: consumed bytes (includes skipped XOFF); PH_SIZE: saved raw bytes.
; PH_XOFF signals skipped XOFF for the future transfer buffer-flush path.
; A zero-length prefix returns immediately; its tail belongs to the caller's
; end-of-tape drain, not the ordinary address/type/checksum validator.
PH_PARSE:
        LD (PH_PTR),HL
        LD A,B
        LD (PH_LEFT),A
        XOR A
        LD (PH_USED),A
        LD (PH_SIZE),A
        LD (PH_XOFF),A
        LD (PH_ERROR),A
        LD (PH_SUM),A
        LD (PH_LENGTH),A
        LD (PH_TYPE),A
        LD (PH_ADDR),A
        LD (PH_ADDR+1),A
        CALL PH_GET
        JP C,PH_RETURN
        CP ':'
        JR NZ,PH_FORM
        CALL PH_BYTE
        JP C,PH_RETURN
        LD (PH_LENGTH),A
        OR A
        JR Z,PH_END
        LD (PH_DATA),A
        CALL PH_BYTE                 ; load address high
        JP C,PH_RETURN
        LD (PH_ADDR+1),A
        CALL PH_BYTE                 ; load address low
        JP C,PH_RETURN
        LD (PH_ADDR),A
        CALL PH_BYTE                 ; record type (DRI does not restrict it)
        JP C,PH_RETURN
        LD (PH_TYPE),A
PH_DLOOP:
        CALL PH_BYTE
        JP C,PH_RETURN
        LD HL,PH_DATA
        DEC (HL)
        JR NZ,PH_DLOOP
        CALL PH_BYTE                 ; checksum
        JP C,PH_RETURN
        LD A,(PH_SUM)
        OR A
        RET Z
        LD A,3
        RET
PH_END:
        LD A,1
        RET
PH_FORM:
        LD A,2
        RET
PH_RETURN:
        LD A,(PH_ERROR)
        RET
PH_BYTE:
        CALL PH_DIGIT
        RET C
        ADD A,A
        ADD A,A
        ADD A,A
        ADD A,A
        LD (PH_HIGH),A
        CALL PH_DIGIT
        RET C
        LD HL,PH_HIGH
        OR (HL)
        LD E,A
        LD HL,PH_SUM
        ADD A,(HL)
        LD (HL),A
        LD A,E
        OR A
        RET
PH_DIGIT:
        CALL PH_GET
        RET C
        CP '0'
        JR C,PH_INVALID
        CP '9'+1
        JR NC,PH_ALPHA
        SUB '0'
        OR A
        RET
PH_ALPHA:
        CP 'A'
        JR C,PH_INVALID
        CP 'F'+1
        JR NC,PH_INVALID
        SUB 'A'-10
        OR A
        RET
PH_INVALID:
        LD A,2
        JR PH_FAILURE
PH_GET:
        LD A,(PH_LEFT)
        OR A
        JR Z,PH_MORE
        LD HL,(PH_PTR)
        LD A,(HL)
        INC HL
        LD (PH_PTR),HL
        LD HL,PH_USED
        INC (HL)
        LD HL,PH_LEFT
        DEC (HL)
        CP 13H
        JR NZ,PH_SAVE
        LD A,1
        LD (PH_XOFF),A
        JR PH_GET
PH_SAVE:
        LD (PH_CHAR),A
        LD A,(PH_SIZE)
        INC A
        CP 79                       ; DRI HSOURCE >= LAST(HBUFF)
        JR NC,PH_LONG
        LD (PH_SIZE),A
        DEC A
        LD E,A
        LD D,0
        LD HL,PH_BUFFER
        ADD HL,DE
        LD A,(PH_CHAR)
        LD (HL),A
        OR A
        RET
PH_MORE:
        LD A,5
        JR PH_FAILURE
PH_LONG:
        LD A,4
PH_FAILURE:
        LD (PH_ERROR),A
        SCF
        RET
PH_PTR: DW 0
PH_LEFT: DB 0
PH_USED: DB 0
PH_SIZE: DB 0
PH_XOFF: DB 0
PH_ERROR: DB 0
PH_SUM: DB 0
PH_HIGH: DB 0
PH_CHAR: DB 0
PH_LENGTH: DB 0
PH_DATA: DB 0
PH_ADDR: DW 0
PH_TYPE: DB 0
PH_BUFFER: DS 80
