; SEARCH bounded command parser. Include shared selector modules and matcher.
; PCOMMAND: HL/B bounded command tail (0..127), D/E captured caller DU.
; CF clear: A=0 search ready (DU_MAP, FS_FCB, FS_MASK, configured matcher),
; A=1 /HELP, A=2 /VER. Queries do not call BDOS or inspect caller DU.
; CF set/A: 10 lexical/tail, 11 operand/order, 12 option, 13 pattern,
; 14 filespec. Input is unchanged; all returned search state cleared on errors
; and query paths. Clobbers AF/BC/DE/HL. IX/IY preserved.
; Quotes delimit a whole token. No escapes; embedded quotes/glued text fail.
; TAB inside quotes is literal TEXT data, outside quotes separates tokens.
; Quoted query names are always pattern data. /HELP wins over /VER.
PCOMMAND:
        LD (PDRIVE),DE
        LD A,B
        CP 128
        JP NC,PBADLEX
        PUSH HL
        PUSH BC
        LD A,B
        OR A
        JR Z,PNULOK
PNULCHK:
        LD A,(HL)
        OR A
        JP Z,PNULBAD
        INC HL
        DJNZ PNULCHK
PNULOK:
        POP BC
        POP HL
        LD DE,PTAIL
        LD C,B
        LD B,0
        LD A,C
        OR A
        JR Z,PCOPIED
        LDIR
PCOPIED:
        XOR A
        LD (DE),A
        LD (PFLAGS),A
        LD (PPAGED),A
        LD (PSTAGE),A
        LD (PLEXERR),A
        LD (PNTOK),A
        LD (PQUERY),A
        LD (STLEN),A
        LD (SHLEN),A
        CALL FS_CLEAR
        LD HL,PTAIL
        LD DE,PTOKENS
PNEW:
        LD A,(HL)
        OR A
        JP Z,PLEXDONE
        CP ' '
        JR Z,PSKIP
        CP 9
        JR Z,PSKIP
        LD A,L
        LD (DE),A
        INC DE
        LD A,H
        LD (DE),A
        INC DE
        LD C,0
        LD A,(HL)
        CP '"'
        JR Z,PQUOTE
        LD B,0
PPLAIN:
        LD A,(HL)
        OR A
        JR Z,PTOKEND
        CP ' '
        JR Z,PTOKEND
        CP 9
        JR Z,PTOKEND
        CP '"'
        CALL Z,PMARKBAD
        CALL PUPPER
        LD (HL),A
        INC HL
        INC C
        JR PPLAIN
PQUOTE:
        ; Token pointer skips the opening quote.
        INC HL
        DEC DE
        LD A,H
        LD (DE),A
        DEC DE
        LD A,L
        LD (DE),A
        INC DE
        INC DE
        LD B,1
PQUOTED:
        LD A,(HL)
        OR A
        JR Z,PUNCLOSE
        CP '"'
        JR Z,PQEND
        INC HL
        INC C
        JR PQUOTED
PUNCLOSE:
        CALL PMARKBAD
        JR PTOKEND
PQEND:
        LD (HL),0
        INC HL
        LD A,(HL)
        OR A
        JR Z,PTOKEND
        CP ' '
        JR Z,PTOKEND
        CP 9
        JR Z,PTOKEND
        CALL PMARKBAD
PTOKEND:
        LD A,C
        LD (DE),A
        INC DE
        LD A,B
        LD (DE),A
        INC DE
        LD A,(PNTOK)
        INC A
        LD (PNTOK),A
        LD A,(HL)
        OR A
        JR Z,PLEXDONE
        CP ' '
        JR Z,PSKIP
        CP 9
        JP NZ,PNEW
PSKIP:
        LD (HL),0
        INC HL
        JP PNEW
PLEXDONE:
        LD HL,PTOKENS
        LD (PSCAN),HL
        LD A,(PNTOK)
        LD (PLEFT),A
PLOOK:
        LD A,(PLEFT)
        OR A
        JR Z,PQUERYEND
        CALL PNEXT
        LD A,C
        OR A
        JR NZ,PLOOK
        LD DE,POHELP
        CALL PEQUAL
        JR NZ,PLOOKVER
        LD A,1
        LD (PQUERY),A
        JR PLOOK
PLOOKVER:
        LD DE,POVER
        CALL PEQUAL
        JR NZ,PLOOK
        LD A,(PQUERY)
        OR A
        JR NZ,PLOOK
        LD A,2
        LD (PQUERY),A
        JR PLOOK
PQUERYEND:
        LD A,(PQUERY)
        OR A
        RET NZ
        LD A,(PLEXERR)
        OR A
        JP NZ,PBADLEX
        LD HL,PTOKENS
        LD (PSCAN),HL
        LD A,(PNTOK)
        LD (PLEFT),A
PPARSE:
        LD A,(PLEFT)
        OR A
        JP Z,PFINISH
        CALL PNEXT
        LD (PTOKEN),HL
        LD A,B
        LD (PTLEN),A
        LD A,C
        OR A
        JR Z,PUNQUOTE
        LD A,(PSTAGE)
        OR A
        JP NZ,PBADARG
        LD (PPATPTR),HL
        LD A,B
        LD (PPATLEN),A
        LD A,1
        LD (PSTAGE),A
        JR PPARSE
PUNQUOTE:
        LD A,(HL)
        CP '/'
        JR Z,POPTION
        LD A,(PSTAGE)
        CP 1
        JP NZ,PBADARG
        LD (PFILEPTR),HL
        LD A,B
        LD (PFILELEN),A
        LD A,2
        LD (PSTAGE),A
        JR PPARSE
POPTION:
        LD A,(PSTAGE)
        CP 1
        JP Z,PBADARG
        LD DE,PONOH
        CALL PEQUAL
        LD C,1
        JR Z,PSETFLAG
        LD DE,PONOT
        CALL PEQUAL
        LD C,2
        JR Z,PSETFLAG
        LD DE,PONOC
        CALL PEQUAL
        LD C,4
        JR Z,PSETFLAG
        LD DE,POPAGE
        CALL PEQUAL
        JP NZ,PBADOPT
        LD A,1
        LD (PPAGED),A
        JP PPARSE
PSETFLAG:
        LD A,(PFLAGS)
        OR C
        LD (PFLAGS),A
        JP PPARSE
PFINISH:
        LD A,(PSTAGE)
        CP 2
        JP NZ,PBADARG
        LD HL,(PPATPTR)
        LD A,(PPATLEN)
        LD B,A
        LD A,(PFLAGS)
        LD C,A
        CALL SCONFIG
        JP C,PBADPAT
        LD HL,(PFILEPTR)
        LD A,(PFILELEN)
        LD B,A
        LD DE,(PDRIVE)
        CALL FS_PARSE
        JP C,PBADFILE
        ; FS_PARSE permits DU-only shorthand for some consumers. SEARCH
        ; requires a nonempty filename, not an implicit all-files operand.
        LD A,(FS_FLEN)
        OR A
        JP Z,PBADFILE
        XOR A
        RET
PNULBAD:
        POP BC
        POP HL
PBADLEX:
        LD A,10
        JR PFAIL
PBADARG:
        LD A,11
        JR PFAIL
PBADOPT:
        LD A,12
        JR PFAIL
PBADPAT:
        LD A,13
        JR PFAIL
PBADFILE:
        LD A,14
PFAIL:
        PUSH AF
        CALL FS_CLEAR
        XOR A
        LD (STLEN),A
        LD (SHLEN),A
        LD (PPAGED),A
        LD (PFLAGS),A
        POP AF
        SCF
        RET
PMARKBAD:
        PUSH AF
        LD A,1
        LD (PLEXERR),A
        POP AF
        RET
PUPPER:
        CP 'a'
        RET C
        CP 'z'+1
        RET NC
        SUB 32
        RET
; Next token: HL pointer, B length, C quoted flag.
PNEXT:
        LD HL,(PSCAN)
        LD E,(HL)
        INC HL
        LD D,(HL)
        INC HL
        LD B,(HL)
        INC HL
        LD C,(HL)
        INC HL
        LD (PSCAN),HL
        EX DE,HL
        LD A,(PLEFT)
        DEC A
        LD (PLEFT),A
        RET
; Exact HL/B token equals DE zero-terminated uppercase option; preserves inputs.
PEQUAL:
        PUSH HL
        PUSH DE
        PUSH BC
PEQLOOP:
        LD A,B
        OR A
        JR Z,PEQEND
        LD A,(DE)
        OR A
        JR Z,PEQNO
        CP (HL)
        JR NZ,PEQNO
        INC HL
        INC DE
        DJNZ PEQLOOP
PEQEND:
        LD A,(DE)
        OR A
        JR PEQDONE
PEQNO:
        LD A,1
        OR A
PEQDONE:
        POP BC
        POP DE
        POP HL
        RET
POHELP: DB '/HELP',0
POVER: DB '/VER',0
PONOH: DB '/NOHEX',0
PONOT: DB '/NOTEXT',0
PONOC: DB '/NOCASE',0
POPAGE: DB '/P',0
PDRIVE: DW 0
PFLAGS: DB 0
PPAGED: DB 0
PSTAGE: DB 0
PLEXERR: DB 0
PNTOK: DB 0
PQUERY: DB 0
PSCAN: DW 0
PLEFT: DB 0
PTOKEN: DW 0
PTLEN: DB 0
PPATPTR: DW 0
PPATLEN: DB 0
PFILEPTR: DW 0
PFILELEN: DB 0
PTAIL: DS 128
PTOKENS: DS 256
