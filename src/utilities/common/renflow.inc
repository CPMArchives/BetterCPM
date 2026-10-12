; REN transient policy adapter. Parsing completes before any directory mutation.
; Switches are separate whitespace-delimited tokens, accepted in any position.
R_OPTIONS:
        LD DE,R_ARGS
        XOR A
        LD (R_ALEN),A
R_TOKEN:
        LD A,B
        OR A
        JP Z,R_OPDONE
        LD A,(HL)
        CP ' '
        JR NZ,R_TSTART
        INC HL
        DEC B
        JR R_TOKEN
R_TSTART:
        LD (R_TPTR),HL
        LD C,0
R_TSCAN:
        LD A,(HL)
        CP ' '
        JR Z,R_TEND
        INC HL
        INC C
        DEC B
        JR NZ,R_TSCAN
R_TEND:
        LD (R_REST),HL
        LD A,B
        LD (R_REMLEN),A
        LD A,C
        LD (R_TLEN),A
        LD HL,(R_TPTR)
        LD A,(HL)
        CP '/'
        JR Z,R_SWITCH
        LD A,(R_ALEN)
        OR A
        JR Z,R_COPYTOK
        LD A,' '
        LD (DE),A
        INC DE
        LD A,(R_ALEN)
        INC A
        LD (R_ALEN),A
R_COPYTOK:
        LD A,(R_ALEN)
        ADD A,C
        LD (R_ALEN),A
R_COPYCHAR:
        LD A,(HL)
        LD (DE),A
        INC HL
        INC DE
        DEC C
        JR NZ,R_COPYCHAR
        JR R_RESUME
R_SWITCH:
        PUSH DE
        LD B,C
        LD DE,R_OPTWORDS
        LD IX,R_OPTFLAGS
R_OPTNEXT:
        PUSH HL
        PUSH BC
R_OPTCHAR:
        LD A,(DE)
        OR A
        JR Z,R_OPTEND
        LD A,B
        OR A
        JR Z,R_OPTNO
        LD A,(DE)
        CP (HL)
        JR NZ,R_OPTNO
        INC DE
        INC HL
        DEC B
        JR R_OPTCHAR
R_OPTEND:
        LD A,B
        OR A
        JR Z,R_OPTYES
R_OPTNO:
        LD A,(DE)
        INC DE
        OR A
        JR NZ,R_OPTNO
        POP BC
        POP HL
        INC IX
        LD A,(DE)
        OR A
        JR NZ,R_OPTNEXT
        POP DE
        SCF
        RET
R_OPTYES:
        POP BC
        POP HL
        LD A,(IX+0)
        POP DE
        CP 1
        JR Z,R_SETCONFIRM
        CP 2
        JR Z,R_SETYES
        CP 3
        JR Z,R_SETNO
        CP 4
        JR Z,R_SETDRY
        SUB 4
        LD (R_QUIET),A
        JR R_RESUME
R_SETCONFIRM:
        LD (R_CONFIRM),A
        JR R_RESUME
R_SETYES:
        LD A,1
        LD (R_YEXPLICIT),A
        LD (R_POLICY),A
        JR R_RESUME
R_SETNO:
        LD A,2
        LD (R_POLICY),A
        JR R_RESUME
R_SETDRY:
        LD A,1
        LD (R_DRY),A
R_RESUME:
        LD HL,(R_REST)
        LD A,(R_REMLEN)
        LD B,A
        JP R_TOKEN
R_OPDONE:
        LD HL,R_ARGS
        LD A,(R_ALEN)
        LD B,A
        OR A
        SCF
        RET Z
        OR A
        RET
; Called only after a concrete mapping and target check succeed.
R_BEFORE:
        LD A,(R_DRY)
        OR A
        JR NZ,R_PREVIEW
        LD A,(R_POLICY)
        CP 2
        JR Z,R_PREVIEW
        CP 1
        JR Z,R_ALLOW
        LD A,(R_QUIET)
        CP 2
        JR Z,R_ALLOW
        LD A,(R_CONFIRM)
        OR A
        JR Z,R_ALLOW
        CALL R_MAPPING
        LD DE,R_ASK
        CALL BC_PRINT
R_ANSWER:
        LD C,1
        CALL BDOS
        CP 3
        JP Z,R_ABORT
        AND 5FH
        CP 'Y'
        JR Z,R_YANSWER
        CP 'N'
        JR NZ,R_ANSWER
        CALL R_NEWLINE
        CALL R_INC_SKIP
        SCF
        RET
R_YANSWER:
        CALL R_NEWLINE
        JR R_ALLOW
R_PREVIEW:
        CALL R_MAPPING
        CALL R_NEWLINE
        CALL R_INC_SKIP
        SCF
        RET
R_ALLOW:
        CALL R_ROOM
        OR A
        RET
R_SUCCESS:
        XOR A
        LD (R_TRY),A
        LD HL,RF_NAME
        LD DE,(R_NEXT)
        LD BC,11
        LDIR
        LD (R_NEXT),DE
        LD HL,(R_RENAMED)
        INC HL
        LD (R_RENAMED),HL
        LD A,(R_QUIET)
        OR A
        RET NZ
        CALL R_MAPPING
        LD DE,R_OK
        JP BC_PRINT
R_PROTECTED:
        LD HL,RF_BEST
        CALL RF_MAP
        LD A,(RF_ATTR)
        AND 1
        LD DE,R_ROMSG
        JR NZ,R_SKIP
        LD DE,R_SYSMSG
        JR R_SKIP
R_SAME:
        LD DE,R_SAMEMSG
R_SKIP:
        PUSH DE
        CALL R_INC_SKIP
        LD A,(R_QUIET)
        CP 2
        JR Z,R_SKIPQUIET
        CALL R_MAPPING
        POP DE
        JP BC_PRINT
R_SKIPQUIET:
        POP DE
        RET
R_COLLISION:
        ; Unattended policy is explicit skip. Interactive name selection follows.
        LD A,(R_POLICY)
        OR A
        JR NZ,R_COLSKIP
        LD A,(R_DRY)
        OR A
        JR NZ,R_COLSKIP
        LD A,(R_QUIET)
        CP 2
        JR Z,R_COLSKIP
        JP R_COLPROM
R_COLSKIP:
        XOR A
        LD (R_TRY),A
        LD DE,R_EXISTMSG
        CALL R_SKIP
        JP RF_NEXT
R_ABORT:
        LD A,1
        LD (R_ABORTED),A
        CALL BC_DURST
        CALL R_SUMMARY
        JP 0
R_INC_SKIP:
        LD HL,(R_SKIPPED)
        INC HL
        LD (R_SKIPPED),HL
        RET
; Group every visible mapping by source DU. Quiet mode creates no empty groups.
R_MAPPING:
        LD A,(R_QUIET)
        CP 2
        RET Z
        LD A,(RF_DRIVE)
        LD B,A
        LD A,(R_GROUPDRIVE)
        CP B
        JR NZ,R_HEADING
        LD A,(RF_USER)
        LD B,A
        LD A,(R_GROUPUSER)
        CP B
        JR Z,R_NAMES
R_HEADING:
        LD A,(RF_DRIVE)
        LD (R_GROUPDRIVE),A
        ADD A,'A'
        CALL R_CHAR
        LD A,(RF_USER)
        LD (R_GROUPUSER),A
        LD L,A
        LD H,0
        CALL R_NUMBER
        LD DE,R_COLON
        CALL BC_PRINT
R_NAMES:
        LD DE,R_INDENT
        CALL BC_PRINT
        LD HL,RF_BEST
        CALL R_NAME
        LD DE,R_ARROW
        CALL BC_PRINT
        LD HL,RF_NAME
R_NAME:
        LD B,8
        CALL R_FIELD
        LD A,(HL)
        CP ' '
        JR Z,R_NODOT
        LD A,'.'
        CALL R_CHAR
R_NODOT:
        LD B,3
R_FIELD:
        LD A,(HL)
        CP ' '
        CALL NZ,R_CHAR
        INC HL
        DJNZ R_FIELD
        RET
R_CHAR:
        PUSH HL
        PUSH BC
        PUSH DE
        LD E,A
        LD C,2
        CALL BDOS
        POP DE
        POP BC
        POP HL
        RET
R_NEWLINE:
        LD DE,R_CRLF
        JP BC_PRINT
; Unsigned 16-bit decimal, without leading zeros.
R_NUMBER:
        LD DE,10
        LD BC,0
R_DIV:
        OR A
        SBC HL,DE
        JR C,R_DIVEND
        INC BC
        JR R_DIV
R_DIVEND:
        ADD HL,DE
        PUSH HL
        LD H,B
        LD L,C
        LD A,H
        OR L
        CALL NZ,R_NUMBER
        POP HL
        LD A,L
        ADD A,'0'
        JP R_CHAR
R_SUMMARY:
        LD A,(R_QUIET)
        CP 2
        RET Z
        LD A,(R_DRY)
        OR A
        JR Z,R_COUNTS
        LD DE,R_DRYMSG
        JP BC_PRINT
R_COUNTS:
        XOR A
        LD (R_COMMA),A
        LD HL,(R_RENAMED)
        LD DE,R_RNMSG
        CALL R_COUNT
        LD HL,(R_SKIPPED)
        LD DE,R_SKMSG
        CALL R_COUNT
        LD HL,(R_FAILED)
        LD DE,R_FAILMSG
        CALL R_COUNT
        LD A,(R_COMMA)
        OR A
        JP NZ,R_NEWLINE
        RET
R_COUNT:
        LD A,H
        OR L
        RET Z
        PUSH HL
        PUSH DE
        LD A,(R_COMMA)
        OR A
        JR Z,R_COUNTNUM
        LD DE,R_SEPARATOR
        CALL BC_PRINT
R_COUNTNUM:
        POP DE
        POP HL
        PUSH DE
        CALL R_NUMBER
        POP DE
        CALL BC_PRINT
        LD A,1
        LD (R_COMMA),A
        RET
R_OPTWORDS: DB '/C',0,'/Y',0,'/N',0,'/DRY',0,'/Q',0,'/QQ',0,0
R_OPTFLAGS: DB 1,2,3,4,5,6
R_POLICY: DB 0
R_CONFIRM: DB 0
R_YEXPLICIT: DB 0
R_DRY: DB 0
R_QUIET: DB 0
R_ABORTED: DB 0
R_ALEN: DB 0
R_TLEN: DB 0
R_TPTR: DW 0
R_REST: DW 0
R_REMLEN: DB 0
R_RENAMED: DW 0
R_SKIPPED: DW 0
R_GROUPDRIVE: DB 0FFH
R_GROUPUSER: DB 0FFH
R_COMMA: DB 0
R_ARGS: DS 128
R_QNOTICE: DB 'REN: /Y not specified. /QQ assumes /Y.',13,10,'$'
R_DRYMSG: DB 'Dry run only: no files were renamed.',13,10,'$'
R_ASK: DB ' - Rename? Y/N ', '$'
R_OK: DB ' success',13,10,'$'
R_ROMSG: DB ' [SKIPPED - READ ONLY]',13,10,'$'
R_SYSMSG: DB ' [SKIPPED - SYSTEM]',13,10,'$'
R_SAMEMSG: DB ' [SKIPPED - SAME NAME]',13,10,'$'
R_EXISTMSG: DB ' [SKIPPED - TARGET EXISTS]',13,10,'$'
R_COLON: DB ':',13,10,'$'
R_INDENT: DB '   ','$'
R_ARROW: DB ' -> ','$'
R_CRLF: DB 13,10,'$'
R_SEPARATOR: DB ', ','$'
R_RNMSG: DB ' FILES RENAMED','$'
R_SKMSG: DB ' SKIPPED','$'

; Collision help and literal replacement name. No overwrite or cycle solving.
R_COLPROM:
        CALL R_MAPPING
        LD DE,R_COLMSG
        CALL BC_PRINT
        LD C,1
        CALL BDOS
        CP 3
        JP Z,R_ABORT
        CP '?'
        JR Z,R_HELPIT
        AND 5FH
        CP 'A'
        JP Z,R_ABORT
        CP 'S'
        JP Z,R_COLSKIP
        CP 'N'
        JR Z,R_NEWNAME
        JP R_COLPROM
R_HELPIT:
        CALL R_NEWLINE
        LD DE,R_COLHELP
        CALL BC_PRINT
        JR R_COLPROM
R_NEWNAME:
        XOR A
        LD (R_TRY),A
        CALL R_NEWLINE
R_NEWPROM:
        LD DE,R_NEWMSG
        CALL BC_PRINT
        XOR A
        LD (R_ILEN),A
        LD (R_IFULL),A
R_INCHAR:
        LD C,1
        CALL BDOS
        CP 3
        JP Z,R_ABORT
        CP 13
        JR Z,R_INEND
        CP 8
        JR Z,R_BACK
        CP 127
        JR Z,R_BACK
        CP 21
        JR Z,R_RELINE
        LD E,A
        LD A,(R_ILEN)
        CP 31
        JR NC,R_OVER
        LD L,A
        LD H,0
        LD BC,R_IBUF
        ADD HL,BC
        LD A,E
        CP 'a'
        JR C,R_ISTORE
        CP 'z'+1
        JR NC,R_ISTORE
        AND 5FH
R_ISTORE:
        LD (HL),A
        LD A,(R_ILEN)
        INC A
        LD (R_ILEN),A
        JR R_INCHAR
R_OVER:
        LD A,1
        LD (R_IFULL),A
        JR R_INCHAR
R_BACK:
        LD A,(R_ILEN)
        OR A
        JR Z,R_INCHAR
        DEC A
        LD (R_ILEN),A
        JR R_INCHAR
R_RELINE:
        XOR A
        LD (R_ILEN),A
        LD (R_IFULL),A
        JR R_INCHAR
R_INEND:
        CALL R_NEWLINE
        LD A,(R_IFULL)
        OR A
        JR NZ,R_INBAD
        LD A,(R_ILEN)
        OR A
        JP Z,R_COLPROM
        LD B,A
        LD HL,R_IBUF
        CALL OQ_SPLIT
        JR C,R_INBAD
        LD A,(OQ_LEN)
        OR A
        JR NZ,R_INBAD
        XOR A
        CALL FP_VALIDATE
        JR C,R_INBAD
        LD HL,R_IBUF
        LD A,(R_ILEN)
        LD B,A
        LD DE,R_NEWFCB
        CALL BC_PFCB
        LD HL,R_NEWFCB+1
        LD DE,RF_NAME
        LD BC,11
        LDIR
        JP R_CHECK
R_INBAD:
        LD DE,R_INVALID
        CALL BC_PRINT
        JP R_NEWPROM
R_CHECK:
        LD HL,RF_BEST
        LD DE,RF_NAME
        CALL BC_WCMP
        JR NZ,R_CHECKEX
        CALL R_SAME
        JP RF_NEXT
R_CHECKEX:
        CALL RF_FCB
        LD HL,RF_NAME
        LD DE,RF_FILE+1
        LD BC,11
        LDIR
        LD DE,RF_FILE
        LD C,17
        CALL BDOS
        CP 0FFH
        JP NZ,R_COLPROM
        LD A,(R_TRY)
        OR A
        JP NZ,R_MUTATE
        JP RF_RENAME
; Per-DU ledger prevents arbitrary interactive targets from being selected again.
; The resident engine's fixed-point assumption alone does not cover new names.
R_DUSTART:
        LD HL,R_HEAP
        LD (R_NEXT),HL
        LD HL,(6)
        LD DE,256
        OR A
        SBC HL,DE
        LD (R_LIMIT),HL
        RET
R_ROOM:
        LD HL,(R_NEXT)
        LD DE,11
        ADD HL,DE
        LD DE,(R_LIMIT)
        OR A
        SBC HL,DE
        RET C
        RET Z
        LD DE,R_NOMEM
        CALL BC_PRINT
        JP R_ABORT
R_SEEN:
        LD HL,R_HEAP
        LD (R_SCAN),HL
R_SEENLP:
        LD HL,(R_SCAN)
        LD DE,(R_NEXT)
        OR A
        SBC HL,DE
        RET Z
        LD HL,RF_CAND
        LD DE,(R_SCAN)
        CALL BC_WCMP
        SCF
        RET Z
        LD HL,(R_SCAN)
        LD DE,11
        ADD HL,DE
        LD (R_SCAN),HL
        JR R_SEENLP
R_COLMSG: DB ' - File exists. N/S/A/? ', '$'
R_COLHELP: DB 'N New name, S Skip file, A Abort remainder.',13,10,'$'
R_NEWMSG: DB 'New name? ','$'
R_INVALID: DB 'Invalid filename.',13,10,'$'
R_NOMEM: DB 'Insufficient memory.',13,10,'$'
R_ILEN: DB 0
R_IFULL: DB 0
R_IBUF: DS 32
R_NEWFCB: DS 36
R_NEXT: DW 0
R_LIMIT: DW 0
R_SCAN: DW 0

; Recoverable failure retries only the current mapping, without re-confirming it.
; Retry rechecks target existence and drive protection before another mutation.
R_FAILURE:
        LD A,(R_DRY)
        OR A
        JR NZ,R_FAILSKIP
        LD A,(R_POLICY)
        OR A
        JR NZ,R_FAILSKIP
        LD A,(R_QUIET)
        CP 2
        JR Z,R_FAILSKIP
R_FAILPROM:
        LD DE,R_FPRE
        CALL BC_PRINT
        LD HL,RF_BEST
        CALL R_NAME
        LD DE,R_FAILASK
        CALL BC_PRINT
        LD C,1
        CALL BDOS
        CP 3
        JR Z,R_FAILABORT
        CP '?'
        JR Z,R_FAILHELP
        AND 5FH
        CP 'A'
        JR Z,R_FAILABORT
        CP 'S'
        JR Z,R_FAILANS
        CP 'R'
        JR NZ,R_FAILPROM
        CALL R_NEWLINE
        LD A,1
        LD (R_TRY),A
        JP R_CHECK
R_FAILHELP:
        CALL R_NEWLINE
        LD DE,R_FHELP
        CALL BC_PRINT
        JR R_FAILPROM
R_FAILABORT:
        CALL R_FAILCOUNT
        CALL R_NEWLINE
        JP R_ABORT
R_FAILANS:
        CALL R_NEWLINE
R_FAILSKIP:
        CALL R_FAILCOUNT
        CALL R_MAPPING
        LD DE,R_FAILLINE
        CALL BC_PRINT
        JP RF_NEXT
R_FAILCOUNT:
        XOR A
        LD (R_TRY),A
        LD HL,(R_FAILED)
        INC HL
        LD (R_FAILED),HL
        RET
R_DRIVEWR:
        LD C,29
        CALL BDOS
        LD A,(RF_DRIVE)
        LD B,A
        INC B
R_DBITS:
        SRL H
        RR L
        DJNZ R_DBITS
        RET
R_TRY: DB 0
R_FAILED: DW 0
R_FPRE: DB 'REN ','$'
R_FAILASK: DB ' - Failed. R/S/A/? ','$'
R_FHELP: DB 'R Retry, S Skip file, A Abort remainder.',13,10,'$'
R_FAILLINE: DB ' [FAILED]',13,10,'$'
R_FAILMSG: DB ' FAILED','$'
