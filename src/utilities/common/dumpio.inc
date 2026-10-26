; Fixed /LEN range; saturate the exclusive end at physical record EOF.
; Addition carry means beyond EOF too, never a wrapped small range.
SETRANGE:
        LD HL,LENGTH
        LD DE,RANGEEND
        CALL COPY32
        LD A,(LENSET)
        OR A
        RET Z
        LD HL,FROM
        LD DE,RANGELOW
        CALL COPY32
        LD HL,FROM
        LD DE,COUNT
        LD IX,CELL
        LD B,4
        OR A
SRADD:
        LD A,(DE)
        ADC A,(HL)
        LD (IX+0),A
        INC IX
        INC HL
        INC DE
        DJNZ SRADD
        RET C
        LD HL,CELL
        LD DE,LENGTH
        CALL CMP32
        RET NC
        LD DE,RANGEEND
        JP COPY32
; Load a display slot without reading masked data. Page buffers retain aligned
; slots; validity is derived from addresses, never from a sentinel byte value.
DISPLAYBYTE:
        LD HL,POS
        LD DE,STAGELOW
        CALL CMP32
        JR C,DBBLANK
        LD DE,RANGEEND
        CALL CMP32
        JP C,GETBYTE
DBBLANK:
        XOR A
        RET
; CF = cell outside committed display bounds. Preserve renderer registers.
CELLVALID:
        PUSH BC
        PUSH DE
        PUSH HL
        LD HL,DISPLAYPOS
        LD DE,CELL
        CALL COPY32
        LD A,(ROWINDEX)
        LD E,A
        LD D,0
        LD HL,CELL
        CALL ADD16
        LD DE,ACTIVELOW
        CALL CMP32
        JR C,CVDONE
        LD DE,RANGEEND
        CALL CMP32
        CCF
CVDONE:
        POP HL
        POP DE
        POP BC
        RET
; POS is a 32-bit byte address. GETBYTE never changes it. Cache by record.
GETBYTE:
        LD HL,POS
        LD DE,LENGTH
        CALL CMP32
        JR NC,GBEOF
        LD A,(POS)
        RLCA
        AND 1
        LD C,A
        LD HL,(POS+1)
        LD A,(POS+3)
        LD E,A
        ; record=(POS >> 7), via left shift of upper three bytes and bit7.
        ADD HL,HL
        LD A,E
        RLA
        LD E,A
        LD A,L
        OR C
        LD L,A
        LD (RECORD),HL
        LD A,E
        LD (RECORD+2),A
        LD A,(CACHEVALID)
        OR A
        JR Z,GBREAD
        LD HL,RECORD
        LD DE,CACHEKEY
        LD B,3
GBKEY:
        LD A,(DE)
        CP (HL)
        JR NZ,GBREAD
        INC HL
        INC DE
        DJNZ GBKEY
        JR GBCACHED
GBREAD:
        LD HL,RECORD
        LD DE,DFCB+33
        LD BC,3
        LDIR
        LD DE,CACHE
        LD C,26
        CALL SERVICE
        LD DE,DFCB
        LD C,33
        CALL SERVICE
        OR A
        JR NZ,GBERROR
        LD HL,RECORD
        LD DE,CACHEKEY
        LD BC,3
        LDIR
        LD A,1
        LD (CACHEVALID),A
GBCACHED:
        LD A,(POS)
        AND 127
        LD E,A
        LD D,0
        LD HL,CACHE
        ADD HL,DE
        LD A,(HL)
        OR A
        RET
GBEOF:
        LD A,1
        SCF
        RET
GBERROR:
        XOR A
        LD (CACHEVALID),A
        LD HL,POS
        LD DE,ERRPOS
        CALL COPY32
        LD A,2
        SCF
        RET
; Load complete candidate page transactionally. PAGEBUF remains valid on error.
LOADPAGE:
        LD HL,NEXT
        LD DE,POS
        CALL COPY32
        LD HL,0
        LD (STAGECOUNT),HL
        LD DE,STAGEBUF
LPLOOP:
        LD HL,POS
        PUSH DE
        LD DE,RANGEEND
        CALL CMP32
        POP DE
        JR NC,LPOK
        LD HL,(STAGECOUNT)
        PUSH DE
        LD DE,(PAGESIZE)
        OR A
        SBC HL,DE
        POP DE
        JR Z,LPOK
        PUSH DE
        CALL DISPLAYBYTE
        POP DE
        RET C
        LD (DE),A
        INC DE
        LD HL,(STAGECOUNT)
        INC HL
        LD (STAGECOUNT),HL
        PUSH DE
        LD HL,POS
        CALL INC32
        POP DE
        JR LPLOOP
LPOK:
        OR A
        RET
COMMITPAGE:
        LD HL,STAGELOW
        LD DE,ACTIVELOW
        CALL COPY32
        LD HL,NEXT
        LD DE,PAGE
        CALL COPY32
        LD HL,(STAGECOUNT)
        LD (PAGECOUNT),HL
        LD B,H
        LD C,L
        LD HL,STAGEBUF
        LD DE,PAGEBUF
        LD A,B
        OR C
        RET Z
        LDIR
        RET
; One aligned row at DISPLAYPOS. Masked slots never consult buffer contents.
ROWOUT:
        LD HL,DISPLAYPOS
        CALL HEX32
        CALL SPACE
        CALL SPACE
        XOR A
        LD (ROWINDEX),A
ROWHEX:
        LD HL,(RENDERPTR)
        LD A,(ROWINDEX)
        LD E,A
        LD D,0
        ADD HL,DE
        CALL CELLVALID
        JR C,RHBLANK
        LD A,(HL)
        CALL HEXBYTE
        JR RHNEXT
RHBLANK:
        CALL SPACE
        CALL SPACE
RHNEXT:
        LD HL,ROWINDEX
        INC (HL)
        LD A,(ROWBYTES)
        CP (HL)
        JR Z,ROWASCII
        LD A,(COMPACT)
        OR A
        JR Z,ROWSEP
        LD A,(ROWINDEX)
        CP 4
        JR NZ,ROWHEX
        CALL SPACE
        JR ROWHEX
ROWSEP:
        CALL SPACE
        LD A,(ROWINDEX)
        CP 8
        CALL Z,SPACE
        JR ROWHEX
ROWASCII:
        CALL SPACE
        CALL SPACE
        XOR A
        LD (ROWINDEX),A
        LD HL,(RENDERPTR)
        LD A,(ROWBYTES)
        LD B,A
RASTRING:
        CALL CELLVALID
        LD A,' '
        JR C,RAPUT
        LD A,(HL)
        CP 32
        JR C,RADOT
        CP 127
        JR C,RAPUT
RADOT:
        LD A,'.'
RAPUT:
        CALL PUT
        INC HL
        PUSH HL
        LD HL,ROWINDEX
        INC (HL)
        POP HL
        DJNZ RASTRING
        LD (RENDERPTR),HL
        LD HL,DISPLAYPOS
        LD A,(ROWBYTES)
        LD E,A
        LD D,0
        JP ADD16
DSTREAM:
        LD HL,NEXT
        LD DE,POS
        CALL COPY32
DSLOOP:
        CALL STREAMKEY
        JP C,DSEND
        LD HL,POS
        LD DE,RANGEEND
        CALL CMP32
        JP NC,DSEND
        LD HL,POS
        LD DE,DISPLAYPOS
        CALL COPY32
        LD A,(ROWBYTES)
        LD B,A
        LD DE,PAGEBUF
DSLOAD:
        PUSH BC
        PUSH DE
        CALL DISPLAYBYTE
        POP DE
        POP BC
        JP C,DSERROR
        LD (DE),A
        INC DE
        PUSH BC
        PUSH DE
        LD HL,POS
        CALL INC32
        POP DE
        POP BC
        DJNZ DSLOAD
        LD HL,PAGEBUF
        LD (RENDERPTR),HL
        CALL ROWOUT
        CALL NEWLINE
        JR DSLOOP
DSERROR:
        LD HL,READMSG
        CALL TEXT
        LD HL,ERRPOS
        CALL HEX32
DSEND:
        CALL NEWLINE
        JP DEXIT
STREAMKEY:
        LD C,11
        CALL SERVICE
        OR A
        RET Z
        LD E,255
        LD C,6
        CALL SERVICE
        CP 3
        JR Z,SKABORT
        OR A
        RET
SKABORT:
        SCF
        RET
DINITIALERR:
        LD HL,READMSG
        CALL TEXT
        LD HL,ERRPOS
        CALL HEX32
        CALL NEWLINE
        JP DEXIT
