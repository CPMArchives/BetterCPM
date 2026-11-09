; One decoded subject occupies the available TPA above arena. The stack is
; below arena. Decoder storage is charged only while its method is active.
check_room:
        PUSH HL
        LD DE,(6)
        OR A
        SBC HL,DE
        POP HL
        JR NC,out_of_room
        OR A
        RET
out_of_room:
        LD A,AS_RANGE
        SCF
        RET
bounded_end:
        ; HL points to a 32-bit length, DE to the start of writable storage.
        LD C,(HL)
        INC HL
        LD B,(HL)
        INC HL
        LD A,(HL)
        INC HL
        OR (HL)
        JR NZ,out_of_room
        EX DE,HL
        ADD HL,BC
        JR C,out_of_room
        JP check_room

load_topic:
        LD A,(view_member)
        OR A
        JR NZ,load_member
        LD HL,context+AS_OFFSET
        LD B,4
        XOR A
loose_offset:
        LD (HL),A
        INC HL
        DJNZ loose_offset
        LD HL,context+AS_FILE_SIZE
        CALL raw_to_arena
        RET C
        LD HL,view_file+10
        JP unpack_inner
load_member:
        LD A,(active_format)
        CP 3
        JR NZ,load_ark
        LD HL,context+AS_MEMBER+AM_OFFSET
        LD DE,context+AS_OFFSET
        LD BC,4
        LDIR
        LD HL,context+AS_MEMBER+AM_STORED
        CALL raw_to_arena
        RET C
        LD DE,(context+AS_MEMBER+AM_CRC)
        LD A,D
        OR E
        JR Z,lbr_logical_end
        PUSH DE
        LD BC,(context+AS_MEMBER+AM_STORED)
        LD HL,arena
        LD DE,0
        CALL LBR_CRC16
        POP HL
        OR A
        SBC HL,DE
        JP NZ,AR_CHECK
lbr_logical_end:
        LD HL,(context+AS_MEMBER+AM_LENGTH)
        LD DE,arena
        ADD HL,DE
        LD (data_end),HL
member_inner:
        LD HL,view_member+8
        JP unpack_inner
raw_to_arena:
        LD DE,arena
        CALL bounded_end
        RET C
        LD (data_end),HL
        LD (context+AS_COUNT),BC
        LD HL,arena
        LD (context+AS_BUFFER),HL
        JP LB_TRANSFER

load_ark:
        LD A,(context+AS_MEMBER+AM_METHOD)
        CP 5
        JR NC,load_lzw
        LD HL,context+AS_MEMBER+AM_LENGTH
        LD DE,arena
        CALL bounded_end
        RET C
        LD (data_end),HL
        LD A,(context+AS_MEMBER+AM_METHOD)
        CP 3
        JR NC,ark_prepare
        CALL ARK_TEST_STORED
        RET C
ark_prepare:
        CALL NK_RESET
        LD DE,arena
ark_block:
        PUSH DE
        LD BC,128
        CALL NK_READ
        POP HL
        JR C,ark_done
        ADD HL,BC
        EX DE,HL
        JR ark_block
ark_done:
        CP AS_END
        JP Z,member_inner
        SCF
        RET
load_lzw:
        CP 10
        JP NC,unsupported
        ; LZW uses the first 24 KiB of the arena only during X_RUN.
        LD HL,context+AS_MEMBER+AM_LENGTH
        LD DE,arena+24576
        CALL bounded_end
        RET C
        LD HL,arena+24576
        LD (output_ptr),HL
        LD HL,context+AS_MEMBER+AM_STORED
        LD DE,NR_LIMIT
        LD BC,4
        LDIR
        XOR A
        LD HL,0
        LD (NR_TOTAL),HL
        LD (NR_TOTAL+2),HL
        CALL NK_RESET
        CALL X_INIT
        RET C
        CALL X_RUN
        RET C
        LD HL,arena+24576
        LD BC,(NR_TOTAL)
        LD DE,arena
        LD A,B
        OR C
        JR Z,lzw_copied
        LDIR
lzw_copied:
        LD (data_end),DE
        JP member_inner
unsupported:
        LD A,AS_UNSUPPORTED
        SCF
        RET

; Adapt NOAH's ARC decoder to archive-bounded input and an in-memory sink.
; Its INIT discards the prefix of the first CP/M record. ARK_RAW already
; starts at the exact member offset, so synthesize only those discarded bytes.
NX_POLL:
        XOR A
        RET
NR_READ:
        LD A,(X_SKIP)
        OR A
        RET NZ
        CALL ND_INPUT
        RET NC
        CP AS_END
        LD A,1
        JR NZ,nr_read_fail
        XOR A
nr_read_fail:
        SCF
        RET
NR_WRITE:
        LD HL,(output_ptr)
        LD (HL),A
        INC HL
        LD (output_ptr),HL
        LD HL,(NR_TOTAL)
        INC HL
        LD (NR_TOTAL),HL
        OR A
        RET
XL_TEST EQU unsupported
XL_READ EQU unsupported
 INCLUDE noahark-decode.inc
 INCLUDE noahark-huffman.inc
 INCLUDE noahlzw-phase.inc

; Stage compressed input at the high end, below the applicable decoder
; context. Decoded output grows up from arena and cannot overwrite input.
unpack_inner:
        CALL encoding
        LD (inner_kind),A
        OR A
        JP Z,normalize_topic
        LD BC,UQ_CONTEXT_SIZE
        CP 1
        JR Z,codec_size
        LD BC,UCN_CONTEXT_SIZE
codec_size:
        LD HL,(6)
        OR A
        SBC HL,BC
        JP C,out_of_room
        LD (codec_ptr),HL
        PUSH BC
        LD DE,(data_end)
        LD HL,arena
        EX DE,HL
        OR A
        SBC HL,DE
        LD B,H
        LD C,L
        LD A,B
        OR C
        JP Z,codec_empty
        LD HL,(codec_ptr)
        OR A
        SBC HL,BC
        JP C,codec_no_space
        LD DE,arena
        OR A
        SBC HL,DE
        JP C,codec_no_space
        ADD HL,DE
        LD (input_ptr),HL
        LD (output_limit),HL
        LD HL,(codec_ptr)
        DEC HL
        EX DE,HL
        LD HL,(data_end)
        DEC HL
        LDDR
        POP BC
        LD IX,(codec_ptr)
        PUSH IX
        POP HL
        LD D,H
        LD E,L
        INC DE
        PUSH BC
        LD BC,CX_PREFIX_SIZE-1
        LD (HL),0
        LDIR
        POP BC
        LD (IX+CX_ABI),1
        LD (IX+CX_SIZE),C
        LD (IX+CX_SIZE+1),B
        LD HL,codec_read
        LD (IX+CX_READ),L
        LD (IX+CX_READ+1),H
        LD HL,codec_write
        LD (IX+CX_WRITE),L
        LD (IX+CX_WRITE+1),H
        LD HL,arena
        LD (output_ptr),HL
        LD A,(inner_kind)
        CP 1
        JR NZ,cr_decode
        CALL USQ_INIT
        CALL NC,USQ_HEAD
        CALL NC,USQ_RUN
        JR codec_done
cr_decode:
        CALL UNCR_INIT
        CALL NC,UNCR_HEAD
        CALL NC,UNCR_RUN
codec_done:
        LD IX,context
        JR NC,codec_success
        CP CS_WRITE
        JP Z,out_of_room
        LD A,AS_FORMAT
        SCF
        RET
codec_success:
        LD HL,(output_ptr)
        LD (data_end),HL
        JR normalize_topic
codec_no_space:
        POP BC
        JP out_of_room
codec_empty:
        POP BC
        LD A,AS_FORMAT
        SCF
        RET
codec_read:
        LD HL,(input_ptr)
        LD DE,(codec_ptr)
        OR A
        SBC HL,DE
        JR Z,codec_eof
        ADD HL,DE
        LD A,(HL)
        INC HL
        LD (input_ptr),HL
        OR A
        RET
codec_eof:
        XOR A
        SCF
        RET
codec_write:
        LD C,A
        LD HL,(output_ptr)
        LD DE,(output_limit)
        OR A
        SBC HL,DE
        JP NC,out_of_room
        ADD HL,DE
        LD (HL),C
        INC HL
        LD (output_ptr),HL
        OR A
        RET
; Convert CRLF/CR/LF to one LF in place. An all-zero tail can be record
; padding from a host file transfer. Reject NUL embedded in authored text.
normalize_topic:
        LD HL,arena
        LD DE,arena
norm_char:
        PUSH DE
        LD DE,(data_end)
        OR A
        SBC HL,DE
        ADD HL,DE
        POP DE
        JR Z,norm_end
        LD A,(HL)
        INC HL
        CP 1AH
        JR Z,norm_end
        OR A
        JR Z,norm_padding
        CP 13
        JR Z,norm_cr
        CP 10
        JR Z,norm_put
        CP 9
        JR Z,norm_put
        CP 32
        JR C,norm_bad
        CP 127
        JR NC,norm_bad
norm_put:
        LD (DE),A
        INC DE
        JR norm_char
norm_cr:
        LD A,10
        LD (DE),A
        INC DE
        PUSH DE
        LD DE,(data_end)
        OR A
        SBC HL,DE
        ADD HL,DE
        POP DE
        JR Z,norm_end
        LD A,(HL)
        CP 10
        JR NZ,norm_char
        INC HL
        JR norm_char
norm_end:
        XOR A
        LD (DE),A
        LD (data_end),DE
        RET
norm_padding:
        PUSH DE
        LD DE,(data_end)
        OR A
        SBC HL,DE
        ADD HL,DE
        POP DE
        JR Z,norm_end
        LD A,(HL)
        INC HL
        OR A
        JR Z,norm_padding
        CP 1AH
        JR Z,norm_end
norm_bad:
        LD A,AS_FORMAT
        SCF
        RET
