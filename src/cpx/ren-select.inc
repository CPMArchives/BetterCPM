; Resident REN: location-free template=shared source selection.
; Fixed workspace; directory rescans avoid a resident batch list. Preflight all
; DUs before mutation. Positional mapping is idempotent, so renamed targets are
; harmless no-ops if they still match the original source pattern on rescans.
BC_REN:
        LD (RF_ARG),HL
        LD A,B
        LD (RF_LEN),A
        LD C,25
        CALL BDOS
        LD (BC_DSAVE),A
        LD C,32
        LD E,0FFH
        CALL BDOS
        LD (BC_USAVE),A
        LD HL,(RF_ARG)
        LD A,(RF_LEN)
        LD B,A
        LD C,0
RF_SPLIT:
        LD A,B
        OR A
        JP Z,RF_ALT
        LD A,(HL)
        CP '='
        JR Z,RF_EQUAL
        INC HL
        INC C
        DEC B
        JR RF_SPLIT
; Prefer '=' so literal underscores in a template remain ordinary characters.
; Retain the historical '_' separator only when '=' is absent.
RF_ALT:
        LD HL,(RF_ARG)
        LD A,(RF_LEN)
        LD B,A
        LD C,0
RF_UNDER:
        LD A,B
        OR A
        JP Z,BC_DBAD
        LD A,(HL)
        CP '_'
        JR Z,RF_EQUAL
        INC HL
        INC C
        DEC B
        JR RF_UNDER
RF_EQUAL:
        INC HL
        DEC B
        LD (RF_SRC),HL
        LD A,B
        LD (RF_SLEN),A
        LD HL,(RF_ARG)
        LD B,C
        ; Trim outer spaces only; template must be a single location-free token.
        CALL RF_TRIM
        LD A,B
        OR A
        JP Z,BC_DBAD
        PUSH HL
        PUSH BC
        LD A,1
        CALL FP_VALIDATE
        POP BC
        POP HL
        JP C,BC_DBAD
        LD DE,RF_TEMP
        CALL BC_PFCB
        LD HL,(RF_SRC)
        LD A,(RF_SLEN)
        LD B,A
        CALL RF_TRIM
        LD A,B
        OR A
        JP Z,BC_DBAD
        LD A,(BC_USAVE)
        LD E,A
        LD A,(BC_DSAVE)
        LD D,A
        CALL FS_PARSE
        JP C,BC_DBAD
        LD HL,DU_MAP+16
        LD B,48
RF_DOMAIN:
        LD A,(HL)
        OR A
        JP NZ,BC_BDERR
        INC HL
        DJNZ RF_DOMAIN
        XOR A
        LD (RF_PASS),A
        LD (RF_ANY),A
RF_BEGIN:
        LD BC,0
        LD (RF_INDEX),BC
RF_DU:
        LD BC,(RF_INDEX)
        CALL DU_NEXT
        JP C,RF_END
        LD (RF_INDEX),BC
        LD A,D
        LD (RF_DRIVE),A
        LD A,E
        LD (RF_USER),A
        CALL RF_SELECT
        LD HL,RF_LAST
        LD B,11
        XOR A
RF_ZERO:
        LD (HL),A
        INC HL
        DJNZ RF_ZERO
RF_NEXT:
        CALL RF_FIND
        JR C,RF_DU
        LD A,1
        LD (RF_ANY),A
        LD HL,RF_BEST
        LD DE,RF_LAST
        LD BC,11
        LDIR
        LD HL,RF_BEST
        CALL RF_MAP
        JP C,BC_DBAD
        LD HL,RF_BEST
        LD DE,RF_NAME
        CALL BC_WCMP
        JR Z,RF_NEXT                 ; same-name mapping is a no-op
        LD A,(RF_ATTR)
        AND 1
        JP NZ,RF_READONLY
        LD A,(RF_PASS)
        OR A
        JR NZ,RF_RENAME
        LD C,29
        CALL BDOS
        LD A,(RF_DRIVE)
        LD B,A
        INC B
RF_ROBIT:
        SRL H
        RR L
        DJNZ RF_ROBIT
        JP C,RF_READONLY
        CALL RF_FCB
        LD HL,RF_NAME
        LD DE,RF_FILE+1
        LD BC,11
        LDIR
        LD DE,RF_FILE
        LD C,17
        CALL BDOS
        CP 0FFH
        JP NZ,BC_REXISTS             ; includes any selected-source overlap
        CALL RF_PAIRS
        JP C,RF_COLLIDE
        JP RF_NEXT
RF_RENAME:
        CALL RF_FCB
        LD HL,RF_BEST
        LD DE,RF_FILE+1
        LD BC,11
        LDIR
        LD HL,RF_NAME
        LD DE,RF_FILE+17
        LD BC,11
        LDIR
        LD DE,RF_FILE
        LD C,23
        CALL BDOS
        CP 0FFH
        JP Z,RF_FAILED
        JP RF_NEXT
RF_END:
        LD A,(RF_PASS)
        OR A
        JP NZ,BC_DURST
        LD A,(RF_ANY)
        OR A
        JP Z,BC_RNOFILE
        INC A
        LD (RF_PASS),A
        JP RF_BEGIN
RF_SELECT:
        LD A,(RF_DRIVE)
        LD E,A
        LD C,14
        CALL BDOS
        LD A,(RF_USER)
        LD E,A
        LD C,32
        JP BDOS
RF_FCB:
        LD HL,RF_FILE
        LD B,36
        XOR A
RF_CLEAR:
        LD (HL),A
        INC HL
        DJNZ RF_CLEAR
        RET
; Shared source search; HL points to the raw entry and carry reports EOF.
RF_FIRST:
        LD HL,FS_FCB
        LD DE,RF_SEARCH
        LD BC,36
        LDIR
        XOR A
        LD (RF_SEARCH),A
        LD A,'?'
        LD (RF_SEARCH+12),A
        LD DE,BC_DMA
        LD C,26
        CALL BDOS
        LD DE,RF_SEARCH
        LD C,17
        JR RF_CALL
RF_MORE:
        LD DE,RF_SEARCH
        LD C,18
RF_CALL:
        CALL BDOS
        CP 0FFH
        SCF
        RET Z
        ADD A,A
        ADD A,A
        ADD A,A
        ADD A,A
        ADD A,A
        LD E,A
        LD D,0
        LD HL,BC_DMA
        ADD HL,DE
        LD (BC_DIREP),HL
        CALL RD_FILTER
        JR NC,RF_MORE
        LD HL,(BC_DIREP)
        INC HL
        LD DE,RF_CAND
        LD B,11
RF_COPY:
        LD A,(HL)
        AND 7FH
        LD (DE),A
        INC DE
        INC HL
        DJNZ RF_COPY
        OR A
        RET
; Lexically next unique original source. Every rescan also observes no-op names.
RF_FIND:
        XOR A
        LD (RF_BEST),A
        CALL RF_FIRST
RF_SCAN:
        JR C,RF_DONE
        LD HL,RF_CAND
        LD DE,RF_LAST
        CALL BC_WCMP
        JR C,RF_STEP
        JR Z,RF_STEP
        LD A,(RF_BEST)
        OR A
        JR Z,RF_SAVE
        LD HL,RF_CAND
        LD DE,RF_BEST
        CALL BC_WCMP
        JR NC,RF_STEP
RF_SAVE:
        LD HL,RF_CAND
        LD DE,RF_BEST
        LD BC,11
        LDIR
        LD HL,(BC_DIREP)
        LD DE,9
        ADD HL,DE
        LD A,(HL)
        AND 80H
        LD (RF_ATTR),A
        ; Normalize RO to bit zero.
        RLCA
        LD (RF_ATTR),A
RF_STEP:
        CALL RF_MORE
        JR RF_SCAN
RF_DONE:
        LD A,(RF_BEST)
        OR A
        RET NZ
        SCF
        RET
; Map one concrete name through the positional template. Save into RF_NAME.
RF_MAP:
        LD DE,RF_TEMP+1
        LD IX,RF_NAME
        LD B,11
RF_POS:
        LD A,(DE)
        CP '?'
        JR NZ,RF_LITERAL
        LD A,(HL)
RF_LITERAL:
        LD (IX+0),A
        INC IX
        INC HL
        INC DE
        DJNZ RF_POS
        LD HL,RF_NAME
        LD A,(HL)
        CP ' '
        SCF
        RET Z
        LD B,8
        CALL RF_FIELD
        RET C
        LD B,3
RF_FIELD:
        LD C,0
RF_CHAR:
        LD A,(HL)
        CP ' '
        JR NZ,RF_LETTER
        INC C
        JR RF_ADV
RF_LETTER:
        LD A,C
        OR A
        SCF
        RET NZ
RF_ADV:
        INC HL
        DJNZ RF_CHAR
        OR A
        RET
; Duplicate mappings only matter within this source DU. Search every original
; selected entry; physical extents of the same name are not separate sources.
RF_PAIRS:
        LD HL,RF_NAME
        LD DE,RF_TARGET
        LD BC,11
        LDIR
        CALL RF_FIRST
RF_PAIR:
        JR NC,RF_PCHECK
        OR A
        RET
RF_PCHECK:
        LD HL,RF_CAND
        LD DE,RF_BEST
        CALL BC_WCMP
        JR Z,RF_PNEXT
        LD HL,RF_CAND
        CALL RF_MAP
        JR NC,RF_PVALID
        LD A,4
        LD (FS_ERROR),A
        JR RF_PBAD
RF_PVALID:
        LD HL,RF_NAME
        LD DE,RF_TARGET
        CALL BC_WCMP
        JR Z,RF_PBAD
RF_PNEXT:
        CALL RF_MORE
        JR NC,RF_PAIR
        OR A
        RET
RF_PBAD:
        SCF
        RET
RF_TRIM:
        LD A,B
        OR A
        RET Z
        LD A,(HL)
        CP ' '
        JR NZ,RF_TAIL
        INC HL
        DEC B
        JR RF_TRIM
RF_TAIL:
        PUSH HL
        LD E,B
        LD D,0
        ADD HL,DE
RF_TBACK:
        DEC HL
        LD A,(HL)
        CP ' '
        JR NZ,RF_TEND
        DEC B
        JR NZ,RF_TBACK
RF_TEND:
        POP HL
        RET
BC_REXISTS:
        LD DE,BC_REXMSG
        JP BC_RPRINT
BC_RNOFILE:
        LD DE,BC_NOFILE
BC_RPRINT:
        CALL BC_PRINT
        JP BC_DURST
RF_COLLIDE:
        LD A,(FS_ERROR)
        OR A
        JP NZ,BC_DBAD
        LD DE,RF_CMSG
        JP BC_RPRINT
RF_READONLY:
        LD DE,RF_RMSG
        JP BC_RPRINT
RF_FAILED:
        LD DE,RF_FMSG
        JP BC_RPRINT
RF_ARG: DW 0
RF_LEN: DB 0
RF_SRC: DW 0
RF_SLEN: DB 0
RF_PASS: DB 0
RF_ANY: DB 0
RF_INDEX: DW 0
RF_DRIVE: DB 0
RF_USER: DB 0
RF_ATTR: DB 0
RF_TEMP: DS 36
RF_SEARCH: DS 36
RF_FILE: DS 36
RF_LAST: DS 11
RF_BEST: DS 11
RF_CAND: DS 11
RF_NAME: DS 11
RF_TARGET: DS 11
RF_CMSG: DB 13,10,'Rename mapping collision.',13,10,'$'
RF_RMSG: DB 13,10,'Read only.',13,10,'$'
RF_FMSG: DB 13,10,'Rename failed.',13,10,'$'
