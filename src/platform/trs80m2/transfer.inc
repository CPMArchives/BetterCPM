; FD1791 + Z80 DMA on the Model II eight-inch controller.
; A=drive 0..3, D=cylinder, E=sector ID, C=80h read/A0h write,
; HL=buffer. On success HL advances by exactly the on-disk sector size.
; BCM2SS only. Reject impossible CHS before enabling DMA. All waits bounded.
M2_XFER:
        CP 4
        JP NC,M2_INVALID
        LD B,A
        LD A,D
        CP 77
        JP NC,M2_INVALID
        LD A,E
        OR A
        JP Z,M2_INVALID
        LD A,D
        OR A
        LD A,E
        JR Z,M2_FM
        CP 17
        JP NC,M2_INVALID
        LD A,0C0H                      ; MFM, head zero
        JR M2_SELECT
M2_FM:  CP 27
        JP NC,M2_INVALID
        LD A,040H                      ; FM, head zero
M2_SELECT:
        LD (M2_ADDR),HL
        LD (M2_CHS),DE
        LD (M2_MODE),A
        LD A,C
        LD (M2_CMD),A
        LD A,3                          ; first attempt plus two recoverable retries
        LD (M2_TRIES),A
        LD A,B
        LD (M2_UNIT),A
M2_ATTEMPT:
        LD A,(M2_UNIT)
        LD B,A
        LD HL,M2_MASKS
        LD E,A
        LD D,0
        ADD HL,DE
        LD A,(M2_MODE)
        OR (HL)
        OUT (0EFH),A
        LD HL,M2_LAST
        LD A,B
        CP (HL)
        JR Z,M2_SEEK
        LD (HL),B
        LD A,008H                     ; restore after each drive change
        CALL M2_TYPE1
        JP NZ,M2_ABORT
M2_SEEK:LD DE,(M2_CHS)
        IN A,(0E5H)
        CP D
        JR Z,M2_AT_TRACK
        LD A,D
        OUT (0E7H),A
        LD A,018H
        CALL M2_TYPE1
        JP NZ,M2_ABORT
M2_AT_TRACK:
        LD DE,(M2_CHS)
        LD A,E
        OUT (0E6H),A
        LD HL,128
        LD A,D
        OR A
        JR Z,M2_LENGTH
        LD HL,512
M2_LENGTH:
        LD DE,(M2_ADDR)
        LD (M2_DMA_ADDR),DE
        PUSH HL
        DEC HL
        LD (M2_DMA_LEN),HL
        LD HL,M2_DMA
        LD BC,(M2_DMA_END-M2_DMA)*256+0F8H
        LD A,(M2_CMD)
        CP 080H
        JR Z,M2_GO
        INC B
        INC B
M2_GO:  OTIR
        LD A,087H
        OUT (0F8H),A
        LD A,(M2_CMD)
        OUT (0E4H),A
        LD B,32
M2_DELAY:DJNZ M2_DELAY
        LD BC,0
M2_WAIT:
        IN A,(0E0H)
        RRCA
        JR C,M2_DONE
        DEC BC
        LD A,B
        OR C
        JR NZ,M2_WAIT
        POP HL
        LD A,1                          ; interrupt timeout
        JR M2_ABORT
M2_DONE:
        LD A,0C3H
        OUT (0F8H),A
        POP HL
        LD DE,(M2_ADDR)
        ADD HL,DE
        IN A,(0E4H)
        AND 0FCH                       ; includes write protect, record type/fault
        RET Z
M2_ABORT:
        PUSH AF                         ; keep the controller status through cleanup
        LD A,0C3H
        OUT (0F8H),A
        LD A,0D0H
        OUT (0E4H),A
        LD A,0FFH
        LD (M2_LAST),A
        POP AF
        BIT 6,A                         ; write protection is final
        JR NZ,M2_FAILED
        LD HL,M2_TRIES
        DEC (HL)
        JP NZ,M2_ATTEMPT                ; restore head, reselect CHS and reset DMA
M2_FAILED:
        OR A
        RET
M2_INVALID:
        LD A,1
        OR A
        RET
M2_TYPE1:
        OUT (0E4H),A
        LD B,32
M2_SETTLE: DJNZ M2_SETTLE
        LD BC,0
M2_BUSY:
        IN A,(0E4H)
        BIT 0,A
        JR Z,M2_TRACK_STATUS
        DEC BC
        LD A,B
        OR C
        JR NZ,M2_BUSY
        JR M2_INVALID
M2_TRACK_STATUS:
        AND 098H
        RET NZ
        ; Allow the head to settle after seek/restore at 4 MHz (~15 ms).
        LD BC,2400
M2_HEAD:DEC BC
        LD A,B
        OR C
        JR NZ,M2_HEAD
        RET
M2_MASKS: DB 14,13,11,7
M2_LAST: DB 0FFH
M2_TRIES: DB 0
M2_UNIT: DB 0
M2_MODE: DB 0
M2_CMD: DB 0
M2_ADDR: DW 0
M2_CHS: DW 0
; WR4 interrupts disabled; A=fixed FDC data, B=incrementing RAM, READY high.
M2_DMA: DB 0C3H,091H,0,08BH,06DH,0E7H
M2_DMA_LEN: DW 0
        DB 03CH,010H,08DH
M2_DMA_ADDR: DW 0
        DB 08AH,0CFH
M2_DMA_END: DB 001H,0CFH              ; turn around and reload for a write
