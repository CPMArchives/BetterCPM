; Isolated ARC method-8 encoder entry, sharing CR's checked input/RLE/hash
; primitives and CR context. This is a codec proof entry; it does not write ARC
; member headers or enable archive updates.
;
; Call CR_INIT, then N8_RUN. The caller supplies ARC method-8 member bytes as
; output: the 0Ch dynamic-LZW header followed by eight-code-group LSB streams.
; Member metadata, CRC, length and publication belong to the future writer.

N8_GROUP       EQU 52
N8_GROUP_BYTES EQU 53

N8_RUN:
        LD A,(IX+CX_PHASE)
        CP CP_DONE
        JP Z,CX_DONE
        LD A,CP_READY
        CALL CX_CHECK_STATE
        RET C
        CALL CX_CHECK_WRITE
        RET C
        CALL CX_DATA
        CALL N8_RESET
        LD A,12
        CALL CR_WRITE
        RET C
N8_MAIN:
        CALL CR_RLE
        RET C
        LD A,D
        OR A
        JR NZ,N8_FINISH
        LD (IX+CR_TOKEN),E
        LD A,(IX+CR_HAVE)
        OR A
        JR Z,N8_FIRST
        CALL CR_FIND
        RET C
        JR NZ,N8_MISS
        LD (IX+CR_CURRENT),E
        LD (IX+CR_CURRENT+1),D
        JR N8_MAIN
N8_MISS:
        LD A,(IX+CR_NEXT+1)
        CP 16
        JR NC,N8_NO_INSERT
        CALL CR_INSERT
        RET C
N8_NO_INSERT:
        LD L,(IX+CR_CURRENT)
        LD H,(IX+CR_CURRENT+1)
        CALL N8_PUT_DATA
        RET C
N8_FIRST:
        LD A,(IX+CR_TOKEN)
        LD (IX+CR_CURRENT),A
        XOR A
        LD (IX+CR_CURRENT+1),A
        LD (IX+CR_HAVE),1
        JR N8_MAIN
N8_FINISH:
        LD A,(IX+CR_HAVE)
        OR A
        JR Z,N8_DONE
        LD L,(IX+CR_CURRENT)
        LD H,(IX+CR_CURRENT+1)
        CALL N8_PUT_DATA
        RET C
        CALL N8_FLUSH_FINAL
        RET C
N8_DONE:
        JP CX_DONE

; Reinitialize CR's shared hash and private LZW counters for ARC's dictionary:
; CLEAR=256, first phrase code=257, nine-bit initial width.
N8_RESET:
        LD HL,0
        CALL CR_KEY_PTR
        LD D,H
        LD E,L
        INC DE
        LD (HL),0FFH
        LD BC,5003*2-1
        LDIR
        LD HL,257
        LD (IX+CR_NEXT),L
        LD (IX+CR_NEXT+1),H
        LD (IX+CR_OUT_NEXT),L
        LD (IX+CR_OUT_NEXT+1),H
        LD HL,512
        LD (IX+CR_LIMIT),L
        LD (IX+CR_LIMIT+1),H
        LD (IX+CR_WIDTH),9
        LD (IX+CR_HAVE),0
        LD (IX+CR_HAVE_OUT),0
        LD (IX+N8_GROUP),0
        LD (IX+N8_GROUP_BYTES),0
        LD (IX+CR_OUTBITS),0
        LD (IX+CR_OUTBYTE),0
        RET

; HL=code. LSB-first, grouped at eight codes. Width transitions flush a
; partial group to the current width's full byte count before changing width.
N8_PUT_CODE:
        LD (IX+CR_WIRE),L
        LD (IX+CR_WIRE+1),H
        LD A,(IX+CR_WIDTH)
        LD (IX+CR_BITSLEFT),A
N8_CODE_BIT:
        LD L,(IX+CR_WIRE)
        LD H,(IX+CR_WIRE+1)
        SRL H
        RR L
        LD (IX+CR_WIRE),L
        LD (IX+CR_WIRE+1),H
        JR NC,N8_CODE_ZERO
        LD A,(IX+CR_OUTBITS)
        OR A
        JR NZ,N8_MASK_SHIFT_INIT
        LD A,1
        JR N8_MASK_READY
N8_MASK_SHIFT_INIT:
        LD B,A
        LD A,1
N8_MASK_SHIFT:
        ADD A,A
        DJNZ N8_MASK_SHIFT
N8_MASK_READY:
        LD B,A
        LD A,(IX+CR_OUTBYTE)
        OR B
        LD (IX+CR_OUTBYTE),A
N8_CODE_ZERO:
        INC (IX+CR_OUTBITS)
        LD A,(IX+CR_OUTBITS)
        CP 8
        JR NZ,N8_CODE_MORE
        LD A,(IX+CR_OUTBYTE)
        CALL CR_WRITE
        RET C
        LD (IX+CR_OUTBYTE),0
        LD (IX+CR_OUTBITS),0
        INC (IX+N8_GROUP_BYTES)
N8_CODE_MORE:
        DEC (IX+CR_BITSLEFT)
        JR NZ,N8_CODE_BIT
        INC (IX+N8_GROUP)
        LD A,(IX+N8_GROUP)
        CP 8
        JR Z,N8_GROUP_FULL
        OR A
        RET
N8_GROUP_FULL:
        LD (IX+N8_GROUP),0
        LD (IX+N8_GROUP_BYTES),0
        XOR A
        RET

; Pad an unfinished byte with zero bits, then extend the group to WIDTH bytes.
N8_FLUSH_GROUP:
        LD A,(IX+N8_GROUP)
        OR A
        RET Z
        LD A,(IX+CR_OUTBITS)
        OR A
        JR Z,N8_PAD_BYTES
        LD A,(IX+CR_OUTBYTE)
        CALL CR_WRITE
        RET C
        LD (IX+CR_OUTBYTE),0
        LD (IX+CR_OUTBITS),0
        INC (IX+N8_GROUP_BYTES)
N8_PAD_BYTES:
        LD A,(IX+N8_GROUP_BYTES)
        LD B,(IX+CR_WIDTH)
        CP B
        JR NC,N8_GROUP_DONE
        XOR A
        CALL CR_WRITE
        RET C
        INC (IX+N8_GROUP_BYTES)
        JR N8_PAD_BYTES
N8_GROUP_DONE:
        LD (IX+N8_GROUP),0
        LD (IX+N8_GROUP_BYTES),0
        XOR A
        RET

; At member end the ARC decoder uses the final short group length. Emit only
; the pending byte, with unused high bits zero; do not extend to WIDTH bytes.
N8_FLUSH_FINAL:
        LD A,(IX+CR_OUTBITS)
        OR A
        RET Z
        LD A,(IX+CR_OUTBYTE)
        CALL CR_WRITE
        RET C
        LD (IX+CR_OUTBYTE),0
        LD (IX+CR_OUTBITS),0
        XOR A
        RET

; Emit one data code and track the decoder's one-code-late dictionary growth.
N8_PUT_DATA:
        CALL N8_PUT_CODE
        RET C
        LD A,(IX+CR_HAVE_OUT)
        OR A
        JR NZ,N8_ADVANCE
        LD (IX+CR_HAVE_OUT),1
        XOR A
        RET
N8_ADVANCE:
        LD L,(IX+CR_OUT_NEXT)
        LD H,(IX+CR_OUT_NEXT+1)
        INC HL
        LD (IX+CR_OUT_NEXT),L
        LD (IX+CR_OUT_NEXT+1),H
        LD A,(IX+CR_WIDTH)
        CP 12
        JR Z,N8_ADVANCED
        LD E,(IX+CR_LIMIT)
        LD D,(IX+CR_LIMIT+1)
        OR A
        SBC HL,DE
        JR C,N8_ADVANCED
        CALL N8_FLUSH_GROUP
        RET C
        INC (IX+CR_WIDTH)
        SLA E
        RL D
        LD (IX+CR_LIMIT),E
        LD (IX+CR_LIMIT+1),D
N8_ADVANCED:
        XOR A
        RET

