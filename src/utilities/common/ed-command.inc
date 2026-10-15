; Initial ED command-line core: inline I, B, C, D, U and signed counts.
; HL = exact command bytes, B = length. Returns carry on failure, A='?' or '>'.
; Commands before an error remain applied. A/N use the initialized source;
; W/N use initialized work output. Other initial commands use memory/console.
EC_INIT:
        CALL GX_INIT
        XOR A
        LD (EC_UPPER),A
        LD (ET_COL),A
        LD (ET_MUTE),A
        INC A
        LD (EC_VERIFY),A
        RET
EC_RUN:
        LD (GM_STACK),SP
        XOR A
        LD (GM_ACTIVE),A
        CALL EC_EXEC
        PUSH AF
        XOR A
        LD (GM_ACTIVE),A
        POP AF
        RET
EC_EXEC:
        XOR A
        LD (EC_IOERR),A
        LD (ET_COL),A
        LD (EC_PTR),HL
        LD A,B
        LD (EC_LEFT),A
        LD (EC_SIZE),A
EC_NEXT:
        LD A,(GM_ACTIVE)
        OR A
        JP NZ,EC_MACNEXT
        LD A,(EC_LEFT)
        OR A
        RET Z
EC_MACNEXT:
        LD A,(EC_LEFT)
        LD (EC_ATSTART),A
        CALL EC_GET
        LD (EC_WHERE),A
        CP 'I'
        JP Z,EC_INSUC
        CP 'i'
        JP Z,EC_INSLC
        XOR A
        LD (EC_NEG),A
        LD (EC_PREFIX),A
        LD HL,1
        LD (EC_COUNT),HL
        LD A,(EC_WHERE)
        CP '-'
        JP NZ,EC_NUMBER
        LD A,1
        LD (EC_NEG),A
        LD (EC_PREFIX),A
        CALL EC_GET
EC_NUMBER:
        CP '#'
        JP NZ,EC_DIGITS
        LD A,1
        LD (EC_PREFIX),A
        LD HL,0FFFFH
        LD (EC_COUNT),HL
        CALL EC_GET
        JP EC_DISP
EC_DIGITS:
        CP '0'
        JP C,EC_DISP
        CP '9'+1
        JP NC,EC_DISP
        PUSH AF
        LD A,1
        LD (EC_PREFIX),A
        POP AF
        LD HL,0
        LD (EC_COUNT),HL
EC_NUMLOOP:
        SUB '0'
        LD E,A
        LD D,0
        LD HL,(EC_COUNT)
        LD B,H
        LD C,L
        ADD HL,HL
        ADD HL,HL
        ADD HL,BC
        ADD HL,HL
        ADD HL,DE
        LD (EC_COUNT),HL
        CALL EC_GET
        CP '0'
        JP C,EC_DISP
        CP '9'+1
        JP C,EC_NUMLOOP
EC_DISP:
        LD (EC_RAW),A
        LD (EC_WHERE),A
        CALL EI_UP
        LD (EC_CMD),A
        LD (EC_WHERE),A
        LD HL,(EC_COUNT)
        LD A,H
        OR L
        JP NZ,EC_SELECT
        LD A,1
        LD (EC_NEG),A               ; DRI zero distance implies backward
EC_SELECT:
        LD A,(EC_CMD)
        CP 13
        JP Z,EC_RETURN
        CP 'F'
        JP Z,EC_FIND
        CP 'S'
        JP Z,EC_SUB
        CP 'J'
        JP Z,EC_JUXT
        CP 'N'
        JP Z,EC_AUTOSCAN
        CP 'M'
        JP Z,EC_MACRO
        CP 'R'
        JP Z,EC_LIBRARY
        CP 'X'
        JP Z,EC_XCMD
        CP 'W'
        JP Z,EC_WRITE
        CP 'A'
        JP Z,EC_APP
        CP 'B'
        JP Z,EC_BEGIN
        CP 'C'
        JP Z,EC_MOVE
        CP 'D'
        JP Z,EC_DELETE
        CP 'U'
        JP Z,EC_UCASE
        CP 'L'
        JP Z,EC_LINES
        CP 'K'
        JP Z,EC_KILL
        CP 'T'
        JP Z,EC_TYPE
        CP 'V'
        JP Z,EC_VCMD
        JP EC_BAD
EC_WRITE:
        CALL EX_RUN
        RET C
        JP EC_NEXT
EC_FIND:
        CALL EG_RUN
        RET C
        JP EC_NEXT
EC_SUB:
        CALL GS_RUN
        RET C
        JP EC_NEXT
EC_JUXT:
        CALL GJ_RUN
        RET C
        JP EC_NEXT
EC_AUTOSCAN:
        CALL GN_RUN
        RET C
        JP EC_NEXT
EC_MACRO:
        CALL GM_DEFINE
        RET C
        JP EC_NEXT
EC_LIBRARY:
        CALL GR_RUN
        RET C
        JP EC_NEXT
EC_XCMD:
        CALL GX_RUN
        RET C
        JP EC_NEXT
EC_RETURN:
        LD A,(GM_ACTIVE)
        OR A
        JP NZ,EC_NEXT
        LD A,(EC_SIZE)
        LD B,A
        LD A,(EC_ATSTART)
        CP B
        JP NZ,EC_NEXT            ; CR is move/type only as the first command
        CALL EL_MOVE
        LD HL,1
        LD (EC_COUNT),HL
        XOR A
        LD (EC_NEG),A
        CALL ET_TYPE
        RET C
        JP EC_NEXT
EC_APP:
        CALL EA_RUN
        RET C
        JP EC_NEXT
EC_TYPE:
        CALL ET_TYPE
        RET C
        JP EC_NEXT
EC_VCMD:
        LD HL,(EC_COUNT)
        LD A,H
        OR L
        JP Z,EC_STATE
        LD A,(EC_NEG)
        XOR 1
        LD (EC_VERIFY),A
        JP EC_NEXT
EC_STATE:
        LD A,2                      ; caller must format the 0V memory report
        SCF
        RET
EC_LINES:
        CALL EL_MOVE
        JP EC_NEXT
EC_KILL:
        CALL EL_KILL
        JP EC_NEXT
EC_BEGIN:
        LD A,(EC_NEG)
        OR A
        CALL Z,EB_TOP
        LD A,(EC_NEG)
        OR A
        CALL NZ,EB_END
        JP EC_NEXT
EC_UCASE:
        LD A,(EC_NEG)
        XOR 1
        LD (EC_UPPER),A
        JP EC_NEXT
EC_MOVE:
        LD A,0
        LD (EC_DFLAG),A
        JP EC_REPEAT
EC_DELETE:
        LD A,1
        LD (EC_DFLAG),A
EC_REPEAT:
        LD HL,(EC_COUNT)
        LD A,H
        OR L
        JP Z,EC_NEXT
        DEC HL
        LD (EC_COUNT),HL
        LD A,(EC_DFLAG)
        OR A
        JP NZ,EC_DELSTEP
        LD A,(EC_NEG)
        OR A
        JP NZ,EC_BACK
        CALL EB_RIGHT
        JP EC_STEPOK
EC_BACK:
        CALL EB_LEFT
        JP EC_STEPOK
EC_DELSTEP:
        LD A,(EC_NEG)
        OR A
        JP NZ,EC_DELBACK
        CALL EB_DEL
        JP EC_STEPOK
EC_DELBACK:
        CALL EB_ERASE
EC_STEPOK:
        JP NC,EC_REPEAT              ; movement/deletion saturates at edge
        JP EC_NEXT
EC_INSUC:
        LD A,1
        JP EC_INSERT
EC_INSLC:
        LD A,(EC_UPPER)
EC_INSERT:
        LD (EC_TRANS),A
        LD A,(GM_ACTIVE)
        OR A
        JP NZ,EC_INLOOP
        LD A,(EC_LEFT)
        OR A
        JP Z,EC_INPUT
EC_INLOOP:
        LD A,(GM_ACTIVE)
        OR A
        JP NZ,EC_INCHAR
        LD A,(EC_LEFT)
        OR A
        JP Z,EC_EOL
EC_INCHAR:
        CALL EC_GET
        LD (EC_WHERE),A
        CP 26
        JP Z,EC_NEXT
        OR A
        JP Z,EC_BAD
        CP 12
        JP Z,EC_CRLF
        LD C,A
        LD A,(EC_TRANS)
        OR A
        LD A,C
        CALL NZ,EI_UP
        LD C,A
        LD (EC_WHERE),A
        CALL EB_PUT
        JP C,EC_FULL
        JP EC_INLOOP
EC_CRLF:
        LD C,13
        LD A,C
        LD (EC_WHERE),A
        CALL EB_PUT
        JP C,EC_FULL
        LD C,10
        LD A,C
        LD (EC_WHERE),A
        CALL EB_PUT
        JP C,EC_FULL
        JP EC_INLOOP
EC_EOL:
        LD C,13
        LD A,C
        LD (EC_WHERE),A
        CALL EB_PUT
        JP C,EC_FULL
        LD C,10
        LD A,C
        LD (EC_WHERE),A
        CALL EB_PUT
        JP C,EC_FULL
        JP EC_NEXT
EC_GET:
        LD A,(GM_ACTIVE)
        OR A
        JP NZ,GM_GET
        LD A,(EC_LEFT)
        OR A
        JP Z,EC_CR
        DEC A
        LD (EC_LEFT),A
        LD HL,(EC_PTR)
        LD A,(HL)
        INC HL
        LD (EC_PTR),HL
        RET
EC_CR:
        LD A,13
        RET
EC_INPUT:
        LD A,1                      ; caller must enter interactive insert mode
        SCF
        RET
EC_BAD:
        LD A,'?'
        SCF
        RET
EC_FULL:
        LD A,'>'
        SCF
        RET
EC_PTR: DW 0
EC_IOERR: DB 0
EC_RAW: DB 0
EC_PREFIX: DB 0
EC_SIZE: DB 0
EC_ATSTART: DB 0
EC_LEFT: DB 0
EC_COUNT: DW 0
EC_NEG: DB 0
EC_CMD: DB 0
EC_WHERE: DB 0
EC_DFLAG: DB 0
EC_UPPER: DB 0
EC_TRANS: DB 0

EC_VERIFY: DB 1
