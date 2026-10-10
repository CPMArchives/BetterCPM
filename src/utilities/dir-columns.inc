; Measure exactly the fields DT_ROW emits. Dry output uses the same numeric
; formatter, without BDOS output or paging. Maximum cell width is DU-specific.
DC_LAYOUT:
        XOR A
        LD (DC_WIDTH),A
        LD (DC_POS),A
        INC A
        LD (DG_MEASURE),A
        LD HL,DT_BUFFER
        LD (DT_SCAN),HL
        LD HL,(DT_FILES)
        LD (DC_LEFT),HL
DC_SCAN:
        LD HL,(DC_LEFT)
        LD A,H
        OR L
        JR Z,DC_PICK
        XOR A
        LD (DG_CHARS),A
        LD HL,(DT_SCAN)
        LD DE,12
        ADD HL,DE
        CALL DT_SIZE
        CALL DT_SUFFIX
        CALL DT_ATTRIBUTES
        LD A,(DG_CHARS)
        ADD A,14               ; name 8 + blank + extension 3 + two blanks
        LD HL,DC_WIDTH
        CP (HL)
        JR C,DC_ADVANCE
        LD (HL),A
DC_ADVANCE:
        LD HL,(DT_SCAN)
        LD DE,24
        ADD HL,DE
        LD (DT_SCAN),HL
        LD HL,(DC_LEFT)
        DEC HL
        LD (DC_LEFT),HL
        JR DC_SCAN
DC_PICK:
        XOR A
        LD (DG_MEASURE),A
        LD A,(DC_REQUEST)
        OR A
        JR NZ,DC_EXPLICIT
        LD A,4
        CALL DC_FITS
        RET NC
        LD A,2
        CALL DC_FITS
        RET NC
        LD A,1
DC_EXPLICIT:
        JP DC_FITS
; A=request, carry if width*columns + three-character separators exceeds 80.
DC_FITS:
        LD (DC_COLS),A
        LD B,A
        LD A,(DC_WIDTH)
        LD C,A
        LD A,0FDH              ; -3, so no separator after the final cell
DC_SUM:
        ADD A,C
        ADD A,3
        DJNZ DC_SUM
        CP 81
        CCF
        RET
DC_SEPARATOR:
        LD HL,DC_POS
        INC (HL)
        LD A,(DC_COLS)
        CP (HL)
        JR Z,DC_NEWLINE
        LD A,(DG_CHARS)
        LD B,A
        LD A,(DC_WIDTH)
        SUB B
        JR Z,DC_DELIMITER
        LD B,A
DC_PAD:
        PUSH BC
        LD A,' '
        CALL BC_PCHAR
        POP BC
        DJNZ DC_PAD
DC_DELIMITER:
        LD DE,DC_SEP
        JP BC_PRINT
DC_NEWLINE:
        XOR A
        LD (DC_POS),A
        LD DE,BC_NL
        JP BC_PRINT
DC_REJECT:
        LD DE,DC_MSG
        CALL BC_PRINT
        JP BC_DURST
DC_LEFT: DW 0
DC_REQUEST: DB 0
DC_COLS: DB 1
DC_WIDTH: DB 0
DC_POS: DB 0
DC_SEP: DB ' : $'
DC_MSG: DB 13,10,'Requested columns do not fit.',13,10,'$'
