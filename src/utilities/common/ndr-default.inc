; /DEFAULT edits the on-disk provider. The live table is never changed.
; Exact supported header/code/metadata match; old table/checksum may vary.
; Verified staging precedes renames. CP/M has no atomic replacement:
; interruption may leave stem.$NB (original) and/or stem.$ND (new).
NF_DEFAULT:
        LD DE,NF_RSX
        LD (NM_FEXT),DE
        CALL NM_FILE
        LD HL,NM_FCB+9
        LD DE,NF_RSX
        LD BC,3
        CALL NF_COMPARE
        JP NZ,NM_BAD
        LD HL,NM_HEADER
        LD DE,NM_IMAGE
        LD BC,64
        LDIR
        CALL NM_VALIDATE
        JP C,NM_BADSET
        ; DS storage is not guaranteed to contain zeroes in a COM image.
        LD HL,NF_TEMP
        LD DE,NF_TEMP+1
        LD BC,107
        XOR A
        LD (HL),A
        LDIR
        LD HL,NM_FCB
        LD DE,NF_TEMP
        LD BC,12
        LDIR
        LD HL,NM_FCB
        LD DE,NF_BACK
        LD BC,12
        LDIR
        LD HL,NF_TEX
        LD DE,NF_TEMP+9
        LD BC,3
        LDIR
        LD HL,NF_BEX
        LD DE,NF_BACK+9
        LD BC,3
        LDIR
        ; Search supplies directory attributes even if OPEN masks FCB bits.
        LD DE,NM_EXTRA
        LD C,26
        CALL BDOS
        LD DE,NM_FCB
        LD C,17
        CALL BDOS
        CP 255
        JP Z,NM_IOERR
        ADD A,A
        ADD A,A
        ADD A,A
        ADD A,A
        ADD A,A
        LD E,A
        LD D,0
        LD HL,NM_EXTRA+9
        ADD HL,DE
        LD A,(HL)
        AND 128
        LD DE,NF_PROTECTED
        JP NZ,NF_PRINT
        LD DE,0FFF8H
        ADD HL,DE
        LD DE,NF_ATTRS
        LD B,11
NF_GETATTR:
        LD A,(HL)
        AND 128
        LD (DE),A
        INC HL
        INC DE
        DJNZ NF_GETATTR
        CALL NM_OPEN
        JP Z,NM_IOERR
        LD HL,NF_BUFFER
        LD (NF_PTR),HL
        LD A,1
        LD (NF_LEFT),A
NF_READ:
        LD DE,(NF_PTR)
        LD C,26
        CALL BDOS
        LD DE,NM_FCB
        LD C,20
        CALL BDOS
        OR A
        JP NZ,NF_READFAIL
        LD HL,(NF_PTR)
        LD DE,NF_BUFFER
        OR A
        SBC HL,DE
        JR NZ,NF_READNEXT
        LD A,(NF_BUFFER+4)
        CP 2
        LD B,NF_RECS2
        JR Z,NF_RCSET
        CP 3
        JP NZ,NF_READFAIL
        LD B,NF_RECS3
NF_RCSET:
        LD (NF_VERSION),A
        LD A,B
        LD (NF_RECORDS),A
        LD (NF_LEFT),A
NF_READNEXT:
        LD HL,(NF_PTR)
        LD DE,128
        ADD HL,DE
        LD (NF_PTR),HL
        LD HL,NF_LEFT
        DEC (HL)
        JR NZ,NF_READ
        LD DE,NM_EXTRA
        LD C,26
        CALL BDOS
        LD DE,NM_FCB
        LD C,20
        CALL BDOS
        CP 1
        JP NZ,NF_READFAIL
        CALL NM_CLOSE
        JP Z,NM_IOERR
        CALL NF_SUM
        LD DE,(NF_BUFFER+44)
        OR A
        SBC HL,DE
        JP NZ,NF_BAD
        LD A,2
        LD (NF_BUFFER+4),A
        LD HL,(NF_REFERENCE+44)
        LD (NF_BUFFER+44),HL
        LD HL,NF_BUFFER
        LD DE,NF_REFERENCE
        LD BC,NF_TABLE_OFFSET
        CALL NF_COMPARE
        JP NZ,NF_BAD
        LD HL,NF_BUFFER+NF_META_OFFSET
        LD DE,NF_META2
        LD BC,NF_SIZE2-NF_META_OFFSET
        LD A,(NF_VERSION)
        CP 2
        JR Z,NF_METACHECK
        LD DE,NF_META3
        LD BC,NF_SIZE3-NF_META_OFFSET
NF_METACHECK:
        CALL NF_COMPARE
        JP NZ,NF_BAD
        LD A,(NF_VERSION)
        LD (NF_BUFFER+4),A
        LD HL,NM_TABLE
        LD DE,NF_BUFFER+NF_TABLE_OFFSET
        LD BC,320
        LDIR
        CALL NF_SUM
        LD (NF_BUFFER+44),HL
        LD DE,NF_TEMP
        CALL NF_EXISTS
        JP NZ,NF_COLLISION
        LD DE,NF_BACK
        CALL NF_EXISTS
        JP NZ,NF_COLLISION
        LD DE,NF_TEMP
        LD C,22
        CALL BDOS
        INC A
        JP Z,NM_IOERR
        LD HL,NF_BUFFER
        LD (NF_PTR),HL
        LD A,(NF_RECORDS)
        LD (NF_LEFT),A
NF_WRITE:
        LD DE,(NF_PTR)
        LD C,26
        CALL BDOS
        LD DE,NF_TEMP
        LD C,21
        CALL BDOS
        OR A
        JP NZ,NF_STAGEFAIL
        LD HL,(NF_PTR)
        LD DE,128
        ADD HL,DE
        LD (NF_PTR),HL
        LD HL,NF_LEFT
        DEC (HL)
        JR NZ,NF_WRITE
        CALL NF_CLOSE
        JP Z,NF_STAGEFAIL
        LD HL,NF_TEMP+12
        LD B,24
        XOR A
NF_REWIND:
        LD (HL),A
        INC HL
        DJNZ NF_REWIND
        LD DE,NF_TEMP
        LD C,15
        CALL BDOS
        INC A
        JP Z,NF_STAGEFAIL
        LD HL,NF_BUFFER
        LD (NF_PTR),HL
        LD A,(NF_RECORDS)
        LD (NF_LEFT),A
NF_VERIFY:
        LD DE,NM_EXTRA
        LD C,26
        CALL BDOS
        LD DE,NF_TEMP
        LD C,20
        CALL BDOS
        OR A
        JP NZ,NF_STAGEFAIL
        LD HL,NM_EXTRA
        LD DE,(NF_PTR)
        LD BC,128
        CALL NF_COMPARE
        JP NZ,NF_STAGEFAIL
        LD HL,(NF_PTR)
        LD DE,128
        ADD HL,DE
        LD (NF_PTR),HL
        LD HL,NF_LEFT
        DEC (HL)
        JR NZ,NF_VERIFY
        LD DE,NF_TEMP
        LD C,20
        CALL BDOS
        CP 1
        JP NZ,NF_STAGEFAIL
        CALL NF_CLOSE
        JP Z,NF_STAGEFAIL
        LD HL,NF_ATTRS
        LD DE,NM_FCB+1
        CALL NF_ATTRIBUTES
        LD HL,NF_ATTRS
        LD DE,NF_TEMP+1
        CALL NF_ATTRIBUTES
        LD HL,NF_ATTRS
        LD DE,NF_BACK+1
        CALL NF_ATTRIBUTES
        LD DE,NF_TEMP
        LD C,30
        CALL BDOS
        INC A
        JP Z,NF_STAGEFAIL
        LD HL,NM_FCB
        LD DE,NF_BACK
        CALL NF_RENFILE
        JP Z,NF_STAGEFAIL
        LD HL,NF_TEMP
        LD DE,NM_FCB
        CALL NF_RENFILE
        JR Z,NF_ROLLBACK
        LD DE,NF_BACK
        LD C,19
        CALL BDOS
        INC A
        LD DE,NF_KEPT
        JP Z,NF_PRINT
        LD DE,NF_SAVED
        JP NF_PRINT
NF_ROLLBACK:
        LD HL,NF_BACK
        LD DE,NM_FCB
        CALL NF_RENFILE
        JR NZ,NF_STAGEFAIL
        LD DE,NF_RECOVERY
        JP NF_PRINT
NF_STAGEFAIL:
        CALL NF_CLOSE
        LD DE,NF_TEMP
        LD C,19
        CALL BDOS
        INC A
        LD DE,NF_CLEANUP
        JP Z,NF_PRINT
        JP NM_IOERR
NF_READFAIL:
        CALL NM_CLOSE
NF_BAD:
        LD DE,NF_INVALID
        JP NF_PRINT
NF_COLLISION:
        LD DE,NF_BUSY
        JP NF_PRINT
NF_EXISTS:
        LD C,17
        CALL BDOS
        INC A
        RET
NF_CLOSE:
        LD DE,NF_TEMP
        LD C,16
        CALL BDOS
        INC A
        RET
NF_RENFILE:
        PUSH DE
        LD DE,NF_RENAME
        LD BC,12
        LDIR
        POP HL
        LD DE,NF_RENAME+16
        LD BC,12
        LDIR
        LD DE,NF_RENAME
        LD C,23
        CALL BDOS
        INC A
        RET
NF_ATTRIBUTES:
        LD B,11
NF_ATTRLOOP:
        LD A,(DE)
        AND 127
        OR (HL)
        LD (DE),A
        INC DE
        INC HL
        DJNZ NF_ATTRLOOP
        RET
NF_COMPARE:
        LD A,(DE)
        CP (HL)
        RET NZ
        INC HL
        INC DE
        DEC BC
        LD A,B
        OR C
        JR NZ,NF_COMPARE
        RET
NF_SUM:
        LD DE,NF_BUFFER+512
        LD BC,NF_PAYLOAD_SIZE
        LD HL,0
NF_SUMLOOP:
        LD A,(DE)
        ADD A,L
        LD L,A
        JR NC,NF_SUMNEXT
        INC H
NF_SUMNEXT:
        INC DE
        DEC BC
        LD A,B
        OR C
        JR NZ,NF_SUMLOOP
        RET
; Dollar signs in recovery filenames require zero-terminated diagnostics.
NF_PRINT:
        EX DE,HL
NF_PLOOP:
        LD A,(HL)
        OR A
        JP Z,NM_EXIT
        CALL NM_CHAR
        INC HL
        JR NF_PLOOP
NF_DKEY: DB 'DEFAULT',0
NF_RSX: DB 'RSX'
NF_TEX: DB '$ND'
NF_BEX: DB '$NB'
NF_PROTECTED: DB 'NDR carrier is read-only; defaults unchanged.',13,10,0
NF_INVALID: DB 'Invalid or unsupported NDR carrier; defaults unchanged.',13,10,0
NF_BUSY: DB 'Staging/recovery file exists (.$ND or .$NB); defaults unchanged.',13,10,0
NF_SAVED: DB 'NDR startup defaults saved; effective on next provider load.',13,10,0
NF_KEPT: DB 'NDR startup defaults saved; original retained as .$NB.',13,10,0
NF_RECOVERY: DB 'Default save failed. Original is .$NB; replacement is .$ND.',13,10,0
NF_CLEANUP: DB 'Default save failed; original unchanged; remove stale .$ND.',13,10,0
NF_VERSION: DB 0
NF_RECORDS: DB 0
NF_LEFT: DB 0
NF_PTR: DW 0
NF_ATTRS: DS 11
NF_TEMP: DS 36
NF_BACK: DS 36
NF_RENAME: DS 36
NF_BUFFER: DS 1152
