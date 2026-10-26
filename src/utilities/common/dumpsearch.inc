FIND:
        LD HL,FIPROMPT
        LD A,95
        CALL EDITNEW
        JP C,VIEWLOOP
FINDTYPE:
        LD HL,HAPROMPT
        CALL STATUS
FTKEY:
        CALL WAITKEY
        CP 27
        JP Z,FINDCANCEL
        CALL UPPER
        CP 'A'
        JR Z,FINDASCII
        CP 'H'
        JR Z,FINDHEX
        ; No implicit interpretation: retain pattern and reprompt.
        LD HL,CHOICEMSG
        CALL STATUS
        JR FTKEY
FINDASCII:
        LD A,(EDITLEN)
        CP 33
        JP NC,FINDBAD
        LD (TEMPLEN),A
        LD C,A
        LD B,0
        LD HL,EDITBUF
        LD DE,TEMPPAT
        LDIR
        JR FINDSTART
FINDHEX:
        XOR A
        LD (TEMPLEN),A
        LD A,(EDITLEN)
        LD B,A
        LD HL,EDITBUF
        LD DE,TEMPPAT
FHSPACE:
        LD A,B
        OR A
        JR Z,FHEND
        LD A,(HL)
        CP ' '
        JR NZ,FHPAIR
        INC HL
        DEC B
        JR FHSPACE
FHPAIR:
        LD A,(TEMPLEN)
        CP 32
        JR NC,FINDBAD
        LD A,(HL)
        CALL HEXDIGIT
        JR C,FINDBAD
        RLCA
        RLCA
        RLCA
        RLCA
        LD C,A
        INC HL
        DEC B
        JR Z,FINDBAD
        LD A,(HL)
        CALL HEXDIGIT
        JR C,FINDBAD
        OR C
        LD (DE),A
        INC DE
        LD A,(TEMPLEN)
        INC A
        LD (TEMPLEN),A
        INC HL
        DEC B
        JR FHSPACE
FHEND:
        LD A,(TEMPLEN)
        OR A
        JP Z,FINDCANCEL
FINDSTART:
        LD A,1
        LD (NEWSEARCH),A
        XOR A
        LD (DIRECTION),A
        LD HL,PAGE
        LD DE,CAND
        CALL COPY32
        LD DE,ACTIVELOW
        CALL CMP32
        JR NC,FSREADY
        LD HL,ACTIVELOW
        LD DE,CAND
        CALL COPY32
FSREADY:
        JP SEARCH
FINDBAD:
        LD HL,BADINPUT
        CALL STATUS
        CALL WAITEDIT
        JP C,VIEWLOOP
        JP FINDTYPE
FINDCANCEL:
        CALL HINT
        JP VIEWLOOP
CONTINUEFIND:
        XOR A
        LD (NEWSEARCH),A
        LD A,(PATLEN)
        LD (TEMPLEN),A
        LD C,A
        LD B,0
        LD HL,PATTERN
        LD DE,TEMPPAT
        LDIR
        LD HL,ANCHOR
        LD DE,CAND
        CALL COPY32
        LD A,(DIRECTION)
        OR A
        JR NZ,SEARCHPREV
        LD A,(MATCHED)
        OR A
        JP Z,SEARCH
        LD HL,CAND
        CALL INC32
        JP SEARCH
SEARCHPREV:
        LD HL,CAND
        CALL NONZERO
        JP Z,SEARCHNONE
        CALL DEC32
SEARCH:
        ; Only poll input between candidates. All candidate comparisons are
        ; bounded by 32 bytes; cancellation never commits provisional state.
        CALL SEARCHKEY
        JP C,FINDCANCEL
        LD HL,CAND
        LD DE,RANGELOW
        CALL CMP32
        JP C,SEARCHNONE
        LD DE,RANGEEND
        CALL CMP32
        JP NC,SEARCHNONE
        LD HL,CAND
        LD DE,POS
        CALL COPY32
        LD HL,TEMPPAT
        LD A,(TEMPLEN)
        LD B,A
SEARCHBYTE:
        PUSH BC
        PUSH HL
        LD HL,POS
        LD DE,RANGEEND
        CALL CMP32
        JR NC,SBEOF
        CALL GETBYTE
        JR SBDONE
SBEOF:
        LD A,1
        SCF
SBDONE:
        POP HL
        POP BC
        JR C,SEARCHREAD
        CP (HL)
        JR NZ,SEARCHADV
        INC HL
        PUSH BC
        PUSH HL
        LD HL,POS
        CALL INC32
        POP HL
        POP BC
        DJNZ SEARCHBYTE
        JP SEARCHFOUND
SEARCHREAD:
        CP 1
        JR Z,SEARCHADV
        CALL READSTATUS
        JP VIEWLOOP
SEARCHADV:
        LD HL,CAND
        LD A,(DIRECTION)
        OR A
        JR NZ,SEARCHBACK
        CALL INC32
        JP SEARCH
SEARCHBACK:
        CALL NONZERO
        JR Z,SEARCHNONE
        CALL DEC32
        JP SEARCH
SEARCHNONE:
        LD A,(NEWSEARCH)
        OR A
        JR Z,SNOMORE
        CALL SAVEPAT
        CALL RESETANCHOR
        LD HL,NOTMSG
        CALL STATUS
        JP VIEWLOOP
SNOMORE:
        LD HL,NOMORE
        CALL STATUS
        JP VIEWLOOP
SEARCHFOUND:
        LD HL,CAND
        LD DE,NEXT
        CALL COPY32
        CALL ALIGNNEXT
        LD HL,RANGELOW
        LD DE,STAGELOW
        CALL COPY32
        CALL LOADPAGE
        JP C,MOVEERROR
        CALL COMMITPAGE
        CALL SAVEPAT
        LD HL,CAND
        LD DE,ANCHOR
        CALL COPY32
        LD A,1
        LD (MATCHED),A
        CALL RENDER
        LD HL,MATCHMSG
        CALL STATUS
        LD HL,CAND
        CALL HEX32
        JP VIEWLOOP
SAVEPAT:
        LD A,(TEMPLEN)
        LD (PATLEN),A
        LD C,A
        LD B,0
        LD HL,TEMPPAT
        LD DE,PATTERN
        LDIR
        LD A,1
        LD (ACTIVE),A
        RET
SEARCHKEY:
        LD C,11
        CALL SERVICE
        OR A
        RET Z
        LD E,255
        LD C,6
        CALL SERVICE
        CP 27
        JR Z,SEARCHESC
        OR A
        RET
SEARCHESC:
        SCF
        RET

CHOICEMSG: DB 'Choose H or A; ESC cancels',0
