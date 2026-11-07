; Private matched-system root. Permanent gateway tail, never an RSX allocation.
; VG_LOAD requires a readable 21-byte header and DE=exclusive envelope end.
; A successful check authorizes only these pinned bytes; caller loads afterward.
; Entry offsets are private to this source-closure build, not a public ABI.
        REPT LY_SYS+00F8H-$
        DB 0
        ENDM
VG_CHECK: JP VG_READY                 ; DE -> 16-byte build identity
VG_ALLOC: JP VG_ISSUE                 ; HL -> four-byte prepared validity
VG_PUBL: JP VG_COPY                   ; HL -> prepared value, DE -> live validity
VG_LOAD: JP VG_BOUND                  ; A=role 0..7, HL -> bound artifact
VG_META: JP VG_MVER
VG_XTEST: JP VG_XID
VG_COLD: JP VG_CLEAR                  ; true cold entry only
VG_CBOOT:
        LD SP,SYS_STKTOP
        CALL VG_CLEAR
        JP SYS_COLD+3
VG_READY:
        LD A,(VG_MASK)
        INC A
        JR NZ,VG_BAD
VG_IDENT:
        LD HL,VG_BUILD
        LD B,16
VG_IDLP:
        LD A,(DE)
        CP (HL)
        JR NZ,VG_BAD
        INC DE
        INC HL
        DJNZ VG_IDLP
        XOR A
        RET
VG_BAD: OR 255
        RET
VG_CLEAR:
        XOR A
        LD (VG_MASK),A
        LD HL,VG_NEXT
        LD B,4
VG_ZLOOP:
        LD (HL),A
        INC HL
        DJNZ VG_ZLOOP
        RET
VG_ISSUE:
        LD A,(VG_MASK)
        INC A
        JP NZ,VG_BAD
        PUSH HL
        LD HL,VG_NEXT
        LD B,4
        LD A,255
VG_MAX:
        AND (HL)
        INC HL
        DJNZ VG_MAX
        INC A
        JR NZ,VG_ROOM
        POP HL
        LD A,20                       ; saturated: no destination/counter mutation
        OR A
        RET
VG_ROOM:
        LD HL,VG_NEXT
        LD B,4
VG_CARRY:
        INC (HL)
        JR NZ,VG_DONE
        INC HL
        DJNZ VG_CARRY
VG_DONE:
        POP DE
        LD HL,VG_NEXT
VG_COPY:
        LD BC,4
        LDIR
        XOR A
        RET
; Bound artifact envelope: role byte, identity[16], length word, CRC word, bytes.
; Trusted pins in the root contain length/CRC per role. No caller-supplied CRC
; can authorize foreign bytes. All roles must pass before TCAP metadata/entry.
VG_BOUND:
        LD (VG_LIMIT),DE             ; caller-supplied exclusive buffer end
        CP 8
        JR NC,VG_BAD
        CP (HL)
        JR NZ,VG_BAD
        LD (VG_ROLE),A
        PUSH HL
        INC HL
        EX DE,HL
        CALL VG_IDENT
        POP HL
        OR A
        RET NZ
        LD DE,17
        ADD HL,DE
        PUSH HL
        LD A,(VG_ROLE)
        ADD A,A
        ADD A,A
        LD E,A
        LD D,0
        LD HL,VG_PINS
        ADD HL,DE
        EX DE,HL
        POP HL
        LD B,4
VG_PINLP:
        LD A,(DE)
        CP (HL)
        JP NZ,VG_BAD
        INC DE
        INC HL
        DJNZ VG_PINLP
        ; HL now addresses payload. Fetch pinned length/CRC from envelope,
        ; whose values were just compared to the trusted root table.
        PUSH HL
        LD DE,-4
        ADD HL,DE
        LD C,(HL)
        INC HL
        LD B,(HL)
        INC HL
        LD E,(HL)
        INC HL
        LD D,(HL)
        LD (VG_WANT),DE
        POP HL
        PUSH HL
        ADD HL,BC
        JR C,VG_RBAD
        LD DE,(VG_LIMIT)
        OR A
        SBC HL,DE
        POP DE
        JP NZ,VG_BAD
        CALL VG_CRC
        LD DE,(VG_WANT)
        OR A
        SBC HL,DE
        JP NZ,VG_BAD
        LD A,(VG_ROLE)
        LD B,A
        INC B
        LD A,080H
VG_BIT: RLCA
        DJNZ VG_BIT
        LD HL,VG_MASK
        OR (HL)
        LD (HL),A
        XOR A
        RET
VG_RBAD:
        POP DE
        JP VG_BAD
; CRC-16/CCITT, initial FFFF; DE bytes, BC count, HL result.
VG_CRC:
        LD HL,0FFFFH
VG_BYTE:
        LD A,B
        OR C
        RET Z
        LD A,(DE)
        XOR H
        LD H,A
        PUSH BC
        LD B,8
VG_POLY:
        ADD HL,HL
        JR NC,VG_SHIFT
        LD A,H
        XOR 010H
        LD H,A
        LD A,L
        XOR 021H
        LD L,A
VG_SHIFT:
        DJNZ VG_POLY
        POP BC
        INC DE
        DEC BC
        JR VG_BYTE
VG_XID:
        PUSH BC
        PUSH DE
        PUSH HL
        LD DE,VG_XTCP
        LD B,4
VG_XLOOP:
        LD A,(DE)
        CP (HL)
        JR NZ,VG_NOTX
        INC DE
        INC HL
        DJNZ VG_XLOOP
        POP HL
        POP DE
        POP BC
        INC HL
        INC HL
        INC HL
        INC HL
        CALL VG_MVER
        OR A                          ; matched identity: carry clear, A=status
        RET
VG_NOTX:
        POP HL
        POP DE
        POP BC
        SCF                           ; different service: ordinary legacy rules
        RET
VG_MVER:
        PUSH BC
        PUSH DE
        LD A,(HL)
        OR A
        JR Z,VG_XVER
        CP 1
        JR NZ,VG_VNO
        INC HL
        LD A,(HL)
        CP 3
        JR NZ,VG_VNO
        JR VG_VOK
VG_XVER:
        INC HL
        LD A,(HL)
        CP 4
        JR NZ,VG_VNO
VG_VOK:
        POP DE
        POP HL                        ; code length from saved BC
        LD BC,VG_IDOFF+16
        OR A
        SBC HL,BC
        JP C,VG_BAD
        EX DE,HL
        LD BC,VG_IDOFF
        ADD HL,BC
        EX DE,HL
        JP VG_READY
VG_VNO:
        POP DE
        POP BC
        JP VG_BAD
VG_XTCP: DB 'XTCP'
VG_BUILD:
; @validity-build-id@
VG_PINS:
; @validity-artifact-pins@
VG_MASK: DB 0
VG_NEXT: DB 0,0,0,0
VG_ROLE: DB 0
VG_WANT: DW 0
VG_LIMIT: DW 0
; Infallible persistent publisher body, including prepared validity copy.
; @validity-publisher@
VG_END:
