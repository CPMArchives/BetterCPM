; Optional command variables. All code/cache/scratch follows reconstructed CCP
; lifetime; only the bounded owner table survives ordinary COM execution.
V_INIT:
        LD HL,LY_PD2
        LD DE,V_HEAD
        LD BC,12
        LDIR
        LD HL,(LY_PD2+8)
        LD (V_CAP),HL
        EX DE,HL
        LD HL,LY_PD2
        OR A
        SBC HL,DE
        LD (V_OWNER),HL
        RET
V_READY:
        LD HL,LY_PD2
        LD DE,V_HEAD
        LD B,12
VR_HEAD:
        LD A,(DE)
        CP (HL)
        JP NZ,V_FATAL
        INC DE
        INC HL
        DJNZ VR_HEAD
        LD HL,(V_CAP)
        LD A,H
        OR L
        RET Z
        DEC HL
        DEC HL
        EX DE,HL
        LD HL,(V_OWNER)
        LD C,(HL)
        INC HL
        LD B,(HL)
        INC HL
        LD (V_FIRST),HL
        PUSH HL
        EX DE,HL
        OR A
        SBC HL,BC
        POP HL
        JP C,V_CORRUPT
        ADD HL,BC
        LD (V_END),HL
        LD HL,0
        LD (V_PREV),HL
        LD HL,(V_FIRST)
VR_RECORD:
        LD DE,(V_END)
        OR A
        SBC HL,DE
        ADD HL,DE
        JP Z,VR_PAD
        JP NC,V_CORRUPT
        LD (V_CUR),HL
        LD A,(HL)
        DEC A
        CP 8
        JP NC,V_CORRUPT
        INC A
        LD B,A
        INC HL
        LD A,(HL)
        CP 128
        JP NC,V_CORRUPT
        INC HL
        LD (V_NAME),HL
        ADD A,B
        LD E,A
        LD D,0
        ADD HL,DE
        LD (V_NEXT),HL
        LD DE,(V_END)
        OR A
        SBC HL,DE
        JP C,VR_NBOUND
        JP NZ,V_CORRUPT
VR_NBOUND:
        LD HL,(V_NAME)
        PUSH BC
        CALL V_IDENT
        POP BC
        JP C,V_CORRUPT
        LD DE,V_KEY
VR_CANON:
        LD A,(DE)
        CP (HL)
        JP NZ,V_CORRUPT
        INC DE
        INC HL
        DJNZ VR_CANON
        LD HL,(V_CUR)
        INC HL
        LD B,(HL)
        INC HL
        LD A,(V_KLEN)
        LD E,A
        LD D,0
        ADD HL,DE
        LD A,B
        OR A
        JR Z,VR_ORDER
VR_VALUE:
        LD A,(HL)
        CP 32
        JP C,V_CORRUPT
        CP 127
        JP NC,V_CORRUPT
        INC HL
        DJNZ VR_VALUE
VR_ORDER:
        LD HL,(V_PREV)
        LD A,H
        OR L
        JR Z,VR_ADVANCE
        CALL V_CMPKEY
        JP Z,V_CORRUPT
        JP C,V_CORRUPT
VR_ADVANCE:
        LD HL,(V_CUR)
        LD (V_PREV),HL
        LD HL,(V_NEXT)
        JP VR_RECORD
VR_PAD:
        LD DE,(V_CAP)
        LD HL,(V_OWNER)
        ADD HL,DE
        EX DE,HL
        LD HL,(V_END)
VR_ZERO:
        OR A
        SBC HL,DE
        ADD HL,DE
        JR Z,VR_OK
        LD A,(HL)
        OR A
        JP NZ,V_CORRUPT
        INC HL
        JR VR_ZERO
VR_OK:  OR A
        RET
V_CORRUPT:
        LD HL,(V_OWNER)
        LD BC,(V_CAP)
        XOR A
VR_CLEAR:
        LD (HL),A
        INC HL
        DEC BC
        LD A,B
        OR C
        JR Z,VR_RESET
        XOR A
        JR VR_CLEAR
VR_RESET:
        LD DE,V_MRESET
        JP V_ERROR
V_FATAL:
        LD DE,V_MFATAL
        LD C,9
        CALL BDOS
VF_STOP: JR VF_STOP
; Validate/fold HL/B name into KEY, preserving HL/B. Carry means invalid.
V_IDENT:
        PUSH HL
        PUSH BC
        LD A,B
        DEC A
        CP 8
        JR NC,VI_BAD
        INC A
        LD (V_KLEN),A
        LD DE,V_KEY
        LD C,0
VI_CHAR:
        LD A,(HL)
        CP 'a'
        JR C,VI_FOLD
        CP 'z'+1
        JR NC,VI_FOLD
        SUB 32
VI_FOLD:
        CP '_'
        JR Z,VI_STORE
        CP 'A'
        JR C,VI_DIGIT
        CP 'Z'+1
        JR C,VI_STORE
VI_DIGIT:
        PUSH AF
        LD A,C
        OR A
        JR Z,VI_POPBAD
        POP AF
        CP '0'
        JR C,VI_BAD
        CP '9'+1
        JR NC,VI_BAD
VI_STORE:
        LD (DE),A
        INC DE
        INC HL
        INC C
        DJNZ VI_CHAR
        OR A
        JR VI_RETURN
VI_POPBAD:
        POP AF
VI_BAD: SCF
VI_RETURN:
        POP BC
        POP HL
        RET
; Compare KEY to record at HL. Preserve HL. Z equal, C key sorts first.
V_CMPKEY:
        PUSH HL
        LD C,(HL)
        INC HL
        INC HL
        LD DE,V_KEY
        LD A,(V_KLEN)
        LD B,A
VC_NEXT:
        LD A,B
        OR A
        JR Z,VC_KEYEND
        LD A,C
        OR A
        JR Z,VC_GREATER
        LD A,(DE)
        CP (HL)
        JR NZ,VC_RETURN
        INC HL
        INC DE
        DEC B
        DEC C
        JR VC_NEXT
VC_KEYEND:
        LD A,C
        OR A
        JR Z,VC_RETURN
        SCF
        JR VC_RETURN
VC_GREATER:
        LD A,1
        OR A
VC_RETURN:
        POP HL
        RET
V_ADVANCE:
        LD A,(HL)
        INC HL
        ADD A,(HL)
        INC HL
        LD E,A
        LD D,0
        ADD HL,DE
        RET
V_FIND:
        LD HL,(V_FIRST)
VF_NEXT:
        LD DE,(V_END)
        OR A
        SBC HL,DE
        ADD HL,DE
        JR Z,VF_ABSENT
        CALL V_CMPKEY
        JR Z,VF_FOUND
        JR C,VF_ABSENT
        CALL V_ADVANCE
        JR VF_NEXT
VF_FOUND:
        LD A,1
        JR VF_SAVE
VF_ABSENT:
        XOR A
VF_SAVE:
        LD (V_FOUND),A
        LD (V_SLOT),HL
        OR A
        RET
; Expand selected raw text once; do not publish a partial command on failure.
V_EXPAND:
        CALL V_READY
        RET C
        LD HL,(V_CAP)
        LD A,H
        OR L
        RET Z
        LD HL,V_EXPBUF
        LD (V_OUT),HL
        XOR A
        LD (V_OLEN),A
        LD HL,CCP_DATA
        LD A,(CCP_COUNT)
        LD B,A
VE_NEXT:
        LD A,B
        OR A
        JP Z,VE_DONE
        LD A,(HL)
        INC HL
        DEC B
        CP '%'
        JR Z,VE_PERCENT
        CALL V_PUT
        RET C
        JR VE_NEXT
VE_PERCENT:
        LD A,B
        OR A
        JP Z,V_INVALID
        LD A,(HL)
        CP '%'
        JR NZ,VE_NAME
        INC HL
        DEC B
        CALL V_PUT
        RET C
        JR VE_NEXT
VE_NAME:
        LD (V_TOKEN),HL
        LD C,0
VE_SCAN:
        LD A,B
        OR A
        JP Z,V_INVALID
        LD A,(HL)
        INC HL
        DEC B
        CP '%'
        JR Z,VE_LOOKUP
        INC C
        LD A,C
        CP 9
        JP NC,V_INVALID
        JR VE_SCAN
VE_LOOKUP:
        PUSH HL
        PUSH BC
        LD HL,(V_TOKEN)
        LD B,C
        CALL V_IDENT
        JR C,VE_BADPOP
        CALL V_FIND
        JR Z,VE_UNDEF
        LD A,(HL)
        INC HL
        LD B,(HL)
        INC HL
        LD E,A
        LD D,0
        ADD HL,DE
        LD A,B
        OR A
        JR Z,VE_RESTORE
VE_INSERT:
        LD A,(HL)
        INC HL
        CALL V_PUT
        JR C,VE_POPRETURN
        DJNZ VE_INSERT
VE_RESTORE:
        POP BC
        POP HL
        JR VE_NEXT
VE_UNDEF:
        LD DE,V_MUNDEF
        JR VE_POPERROR
VE_BADPOP:
        LD DE,V_MINVALID
VE_POPERROR:
        POP BC
        POP HL
        JP V_ERROR
VE_POPRETURN:
        POP BC
        POP HL
        RET
VE_DONE:
        LD A,(V_OLEN)
        LD (CCP_COUNT),A
        OR A
        RET Z
        LD C,A
        LD B,0
        LD HL,V_EXPBUF
        LD DE,CCP_DATA
        LDIR
        OR A
        RET
V_PUT:
        PUSH HL
        PUSH AF
        LD A,(V_OLEN)
        CP 127
        JR Z,VP_FULL
        INC A
        LD (V_OLEN),A
        POP AF
        LD HL,(V_OUT)
        LD (HL),A
        INC HL
        LD (V_OUT),HL
        POP HL
        OR A
        RET
VP_FULL:
        POP AF
        POP HL
        LD DE,V_MOVER
        JP V_ERROR
; Called after UPPER preserves the original spelling in CCP_RAW.
V_COMMAND:
        LD A,(CCP_COUNT)
        CP 3
        JP C,V_NOT
        LD HL,CCP_DATA
        LD A,(HL)
        CP 'V'
        JP NZ,V_NOT
        INC HL
        LD A,(HL)
        CP 'A'
        JP NZ,V_NOT
        INC HL
        LD A,(HL)
        CP 'R'
        JP NZ,V_NOT
        LD A,(CCP_COUNT)
        SUB 3
        LD B,A
        JR Z,VA_MATCH
        INC HL
        LD A,(HL)
        CP ' '
        JP NZ,V_NOT
        JR VA_MATCH
V_NOT:
        OR A
        RET
VA_MATCH:
        LD HL,(V_CAP)
        LD A,H
        OR L
        LD DE,V_MOFF
        JP Z,VA_ERROR
        LD HL,CCP_RAW+3
        CALL CCP_PSKIP
        JP Z,VA_LIST
        XOR A
        LD (V_DELETE),A
        LD A,(HL)
        CP '/'
        JR NZ,VA_NAME
        INC HL
        DEC B
        LD A,B
        CP 2
        JP C,VA_INVALID
        LD A,(HL)
        AND 0DFH
        CP 'D'
        JP NZ,VA_INVALID
        INC HL
        DEC B
        LD A,(HL)
        CP ' '
        JP NZ,VA_INVALID
        CALL CCP_PSKIP
        LD A,1
        LD (V_DELETE),A
VA_NAME:
        LD (V_TOKEN),HL
        LD C,0
VA_SCAN:
        LD A,B
        OR A
        JR Z,VA_KEY
        LD A,(HL)
        CP ' '
        JR Z,VA_KEY
        CP '='
        JR Z,VA_KEY
        INC HL
        DEC B
        INC C
        JR VA_SCAN
VA_KEY:
        PUSH HL
        PUSH BC
        LD HL,(V_TOKEN)
        LD B,C
        CALL V_IDENT
        POP BC
        POP HL
        JP C,VA_INVALID
        LD A,B
        OR A
        JR Z,VA_QUERY
        LD A,(HL)
        CP '='
        JR Z,VA_SET
        CALL CCP_PSKIP
        JP NZ,VA_INVALID
VA_QUERY:
        CALL V_FIND
        LD DE,V_MUNDEF
        JP Z,VA_ERROR
        LD A,(V_DELETE)
        OR A
        JR NZ,VA_EDIT
        CALL V_PRINT
        SCF
        RET
VA_SET:
        LD A,(V_DELETE)
        OR A
        JP NZ,VA_INVALID
        INC HL
        DEC B
        LD (V_VALUE),HL
        LD A,B
        LD (V_VLEN),A
        OR A
        JR Z,VS_OK
VS_CHAR:
        LD A,(HL)
        CP 32
        JP C,VA_INVALID
        CP 127
        JP NC,VA_INVALID
        INC HL
        DJNZ VS_CHAR
VS_OK:
        CALL V_FIND
VA_EDIT:
        LD HL,V_EDIT
        LD DE,V_EDIT+1
        LD BC,511
        LD (HL),0
        LDIR
        LD HL,(V_SLOT)
        LD DE,(V_FIRST)
        OR A
        SBC HL,DE
        LD (V_PREFIX),HL
        LD A,(V_FOUND)
        OR A
        LD HL,(V_SLOT)
        CALL NZ,V_ADVANCE
        LD (V_SUFFIX),HL
        EX DE,HL
        LD HL,(V_END)
        OR A
        SBC HL,DE
        LD (V_TAIL),HL
        LD DE,(V_PREFIX)
        ADD HL,DE
        LD A,(V_DELETE)
        OR A
        JR NZ,VA_SIZE
        LD A,(V_KLEN)
        LD E,A
        LD A,(V_VLEN)
        ADD A,E
        ADD A,2
        LD E,A
        LD D,0
        ADD HL,DE
VA_SIZE:
        LD (V_USED),HL
        INC HL
        INC HL
        EX DE,HL
        LD HL,(V_CAP)
        OR A
        SBC HL,DE
        LD DE,V_MFULL
        JP C,VA_ERROR
        LD HL,(V_USED)
        LD (V_EDIT),HL
        LD HL,(V_FIRST)
        LD DE,V_EDIT+2
        LD BC,(V_PREFIX)
        CALL V_COPY
        LD A,(V_DELETE)
        OR A
        JR NZ,VA_SUFFIX
        LD A,(V_KLEN)
        LD (DE),A
        INC DE
        LD C,A
        LD B,0
        LD A,(V_VLEN)
        LD (DE),A
        INC DE
        LD HL,V_KEY
        CALL V_COPY
        LD A,(V_VLEN)
        LD C,A
        LD B,0
        LD HL,(V_VALUE)
        CALL V_COPY
VA_SUFFIX:
        LD HL,(V_SUFFIX)
        LD BC,(V_TAIL)
        CALL V_COPY
        LD HL,V_EDIT
        LD DE,(V_OWNER)
        LD BC,(V_CAP)
        LDIR
        SCF
        RET
V_COPY:
        LD A,B
        OR C
        RET Z
        LDIR
        RET
VA_LIST:
        LD HL,(V_FIRST)
VL_NEXT:
        LD DE,(V_END)
        OR A
        SBC HL,DE
        ADD HL,DE
        JR Z,VL_DONE
        PUSH HL
        CALL V_PRINT
        POP HL
        CALL V_ADVANCE
        JR VL_NEXT
VL_DONE:
        SCF
        RET
V_PRINT:
        LD B,(HL)
        INC HL
        LD A,(HL)
        LD (V_PRINTLEN),A
        INC HL
        CALL V_CHARS
        LD A,'='
        CALL V_CHAR
        LD A,(V_PRINTLEN)
        LD B,A
        CALL V_CHARS
        LD A,13
        CALL V_CHAR
        LD A,10
        JP V_CHAR
V_CHARS:
        LD A,B
        OR A
        RET Z
VP_CHAR:
        LD A,(HL)
        INC HL
        CALL V_CHAR
        DJNZ VP_CHAR
        RET
V_CHAR:
        PUSH HL
        PUSH BC
        LD E,A
        LD C,2
        CALL BDOS
        POP BC
        POP HL
        RET
VA_INVALID:
        LD DE,V_MINVALID
VA_ERROR:
        CALL V_ERROR
        CALL CCP_VCANCEL
        SCF
        RET
V_INVALID:
        LD DE,V_MINVALID
V_ERROR:
        LD C,9
        CALL BDOS
        SCF
        RET
V_MINVALID: DB 'VAR invalid.',13,10,'$'
V_MUNDEF: DB 'VAR undefined.',13,10,'$'
V_MOVER: DB 'VAR expansion exceeds 127.',13,10,'$'
V_MFULL: DB 'VAR full.',13,10,'$'
V_MRESET: DB 'VAR reset.',13,10,'$'
V_MOFF: DB 'VAR disabled; use CONFIG and cold boot.',13,10,'$'
V_MFATAL: DB 'PDS invalid; cold boot required.',13,10,'$'
