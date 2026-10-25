; Shared filespec grammar -> bounded, frozen, sorted archive queue.
; 512 identities (drive,user,11-byte canonical name). Overflow fails BEFORE
; archive opens/writes. Existing OS directory API has FF for no more matches;
; fatal media errors remain OS handling, never reclassified as a checked pass.
NS_LIMIT        EQU 512
NS_RECORD       EQU 13
NS_RUN:
        LD C,25
        CALL AC_BDOS
        LD (NS_OLD_DRIVE),A
        LD (NH_DEST),A
        LD E,0FFH
        LD C,32
        CALL AC_BDOS
        LD (NS_OLD_USER),A
        LD (NH_DUSER),A
        LD A,1
        LD (NS_CAPTURED),A
        CALL NS_PARSE
        JP C,NH_USAGE_ERROR
        CALL NS_FREEZE
        JR NC,NS_QUEUE_READY
        LD A,(NH_ABORTED)
        OR A
        LD DE,NS_QUEUE_ERROR
        JR Z,NS_QUEUE_MESSAGE
        LD DE,NX_CANCEL_TEXT
NS_QUEUE_MESSAGE:
        CALL NH_PRINT
        JP NH_RETURN
NS_QUEUE_READY:
        LD A,(NH_MODE)
        CP 3
        JP Z,NW_ADD_BATCH
        LD HL,(NS_COUNT)
        LD A,H
        OR L
        JR NZ,NS_PROCESS_START
        LD DE,NS_NO_ARCHIVES
        CALL NH_PRINT
        JP NH_RETURN
NS_PROCESS_START:
        LD HL,NS_TABLE
        LD (NS_CURRENT),HL
        LD HL,0
        LD (NS_PROCESSED),HL
        LD (NS_BAD_ARCHIVES),HL
NS_PROCESS:
        XOR A
        LD (NS_ARC_FAILED),A
        LD (NS_MATCHED),A
        LD (NS_MATCHED+1),A
        LD (NS_MATCHED+2),A
        LD (NS_MATCHED+3),A
        LD HL,(NS_CURRENT)
        LD D,(HL)
        INC HL
        LD E,(HL)
        LD A,E
        LD (NS_CUR_USER),A
        PUSH DE
        LD C,32
        CALL AC_BDOS
        LD DE,NS_ARCHIVE_TEXT
        CALL NH_PRINT
        POP DE
        CALL NS_PRINT_DU
        LD HL,(NS_CURRENT)
        INC HL
        INC HL
        LD B,8
        CALL NX_NAME_FIELD
        LD A,(HL)
        CP ' '
        JR Z,NS_ARCHIVE_NL
        LD E,'.'
        LD C,2
        CALL AC_BDOS
        LD B,3
        CALL NX_NAME_FIELD
NS_ARCHIVE_NL:
        LD DE,NH_NEWLINE
        CALL NH_PRINT
        JP NH_ARCHIVE
NS_ARCHIVE_DONE:
        LD A,(NS_ARC_FAILED)
        OR A
        JR Z,NS_COUNT_ARCHIVE
        LD HL,(NS_BAD_ARCHIVES)
        INC HL
        LD (NS_BAD_ARCHIVES),HL
NS_COUNT_ARCHIVE:
        LD HL,(NS_PROCESSED)
        INC HL
        LD (NS_PROCESSED),HL
        LD A,(NH_ABORTED)
        OR A
        JR NZ,NS_FINISH
        LD A,(NS_STOP)
        OR A
        JR NZ,NS_FINISH
        LD DE,(NS_COUNT)
        OR A
        SBC HL,DE
        JR Z,NS_FINISH
        LD HL,(NS_CURRENT)
        LD DE,NS_RECORD
        ADD HL,DE
        LD (NS_CURRENT),HL
        JP NS_PROCESS
NS_FINISH:
        LD DE,NS_BATCH_TEXT
        CALL NH_PRINT
        LD HL,(NS_COUNT)
        CALL NS_PRINT_WORD
        LD DE,NS_PROCESSED_TEXT
        CALL NH_PRINT
        LD HL,(NS_PROCESSED)
        CALL NS_PRINT_WORD
        LD DE,NS_FAILED_TEXT
        CALL NH_PRINT
        LD HL,(NS_BAD_ARCHIVES)
        CALL NS_PRINT_WORD
        LD DE,NS_UNPROCESSED_TEXT
        CALL NH_PRINT
        LD HL,(NS_COUNT)
        LD DE,(NS_PROCESSED)
        OR A
        SBC HL,DE
        CALL NS_PRINT_WORD
        LD DE,NH_NEWLINE
        CALL NH_PRINT
        LD A,(NS_WARNINGS)
        OR A
        JR Z,NS_BATCH_RETURN
        LD DE,NS_WARNING_TEXT
        CALL NH_PRINT
NS_BATCH_RETURN:
        JP NH_RETURN
NS_PRINT_WORD:
        LD A,H
        CALL NH_HEX
        LD A,L
        JP NH_HEX
NS_RESTORE:
        LD A,(NS_CAPTURED)
        OR A
        RET Z
        LD A,(NS_OLD_USER)
        LD E,A
        LD C,32
        CALL AC_BDOS
        LD A,(NS_OLD_DRIVE)
        LD E,A
        LD C,14
        CALL AC_BDOS
        LD DE,80H
        LD C,26
        JP AC_BDOS
NS_PRINT_DU:
        LD A,D
        ADD A,'A'
        PUSH DE
        LD E,A
        LD C,2
        CALL AC_BDOS
        POP DE
        LD A,E
        LD B,0
NS_DU_TENS:
        CP 10
        JR C,NS_DU_DIGITS
        SUB 10
        INC B
        JR NS_DU_TENS
NS_DU_DIGITS:
        PUSH AF
        LD A,B
        OR A
        JR Z,NS_DU_ONES
        ADD A,'0'
        LD E,A
        LD C,2
        CALL AC_BDOS
NS_DU_ONES:
        POP AF
        ADD A,'0'
        LD E,A
        LD C,2
        CALL AC_BDOS
        LD E,':'
        JP AC_BDOS

NS_PARSE:
        ; Normalize a private bounded tail; never edit the CCP tail itself.
        LD HL,81H
        LD DE,NS_TAIL
        LD A,(80H)
        LD B,A
NS_COPY_TAIL:
        LD A,(HL)
        CALL NH_UPPER
        LD (DE),A
        INC HL
        INC DE
        DJNZ NS_COPY_TAIL
        LD HL,NS_TAIL
        LD A,(80H)
        LD B,A
        XOR A
        LD (NS_OPERANDS),A
        LD (NS_MODE_SET),A
        LD (NS_YES),A
        LD (NS_RO),A
        LD (NS_SYS),A
        LD (NS_ALL),A
        LD (NS_STOP),A
        LD (NS_WARNINGS),A
        LD (NW_COMPACT),A
        LD (NW_CAP_SET),A
        LD (NW_FORMAT),A
        LD (NW_ACTIVE),A
        LD (NW_PROMPT),A
NS_TOKEN_LOOP:
        CALL NH_TOKEN
        JP C,NS_PARSE_OPERANDS
        LD (NS_TOKEN_PTR),DE
        LD (NS_TOKEN_LEN),A
        LD A,(DE)
        CP '/'
        JR Z,NS_OPTION
        LD A,(NS_OPERANDS)
        CP 2
        JP NC,NS_BAD
        OR A
        JR NZ,NS_SECOND
        LD (NH_ARG),DE
        LD A,(NS_TOKEN_LEN)
        LD (NH_LENGTH),A
        JR NS_OPERAND_SAVED
NS_SECOND:
        LD (NS_MEMBER_ARG),DE
        LD A,(NS_TOKEN_LEN)
        LD (NS_MEMBER_LEN),A
NS_OPERAND_SAVED:
        LD A,(NS_OPERANDS)
        INC A
        LD (NS_OPERANDS),A
        JR NS_TOKEN_LOOP
NS_OPTION:
        LD A,(NS_TOKEN_LEN)
        CALL NH_IS_LIST
        JR NZ,NS_TRY_TEST
        XOR A
        JR NS_SET_MODE
NS_TRY_TEST:
        CALL NH_IS_TEST
        JR NZ,NS_TRY_EXTRACT
        LD A,1
        JR NS_SET_MODE
NS_TRY_EXTRACT:
        CALL NH_IS_EXTRACT
        JR NZ,NS_FLAGS
        LD A,2
NS_SET_MODE:
        LD C,A
        LD A,(NS_MODE_SET)
        OR A
        JR Z,NS_NEW_MODE
        LD A,(NH_MODE)
        CP C
        JP NZ,NS_BAD
NS_NEW_MODE:
        LD A,C
        LD (NH_MODE),A
        LD A,1
        LD (NS_MODE_SET),A
        JR NS_TOKEN_LOOP
NS_FLAGS:
        CALL NW_OPTION
        JP C,NS_BAD
        OR A
        JP NZ,NS_TOKEN_LOOP
        LD A,(NS_TOKEN_LEN)
        CP 2
        JR NZ,NS_SYS_FLAG
        LD DE,(NS_TOKEN_PTR)
        INC DE
        LD A,(DE)
        CP 'Y'
        JR Z,NS_SET_YES
        CP 'R'
        JP NZ,NS_BAD
        LD A,1
        LD (NS_RO),A
        JP NS_TOKEN_LOOP
NS_SET_YES:
        LD A,1
        LD (NS_YES),A
        JP NS_TOKEN_LOOP
NS_SYS_FLAG:
        LD A,(NS_TOKEN_LEN)
        CP 4
        JP NZ,NS_BAD
        CALL NS_IS_SYS
        JP NZ,NS_BAD
        LD A,1
        LD (NS_SYS),A
        JP NS_TOKEN_LOOP
NS_PARSE_OPERANDS:
        LD A,(NS_OPERANDS)
        OR A
        JP Z,NS_BAD
        LD A,(NH_MODE)
        CP 2
        JR NC,NS_PARSE_SOURCE
        LD A,(NS_YES)
        LD C,A
        LD A,(NS_RO)
        OR C
        LD C,A
        LD A,(NS_SYS)
        OR C
        JP NZ,NS_BAD
NS_PARSE_SOURCE:
        LD HL,(NH_ARG)
        LD A,(NH_LENGTH)
        LD B,A
        LD A,(NS_OLD_DRIVE)
        LD D,A
        LD A,(NS_OLD_USER)
        LD E,A
        CALL FS_PARSE
        RET C
        LD HL,(FS_FILE)
        LD A,(FS_FLEN)
        LD B,A
        CALL NS_LEXICAL
        RET C
        CALL NS_DOMAIN
        RET C
        LD HL,DU_MAP
        LD DE,NS_ARCH_MAP
        LD BC,64
        LDIR
        LD HL,FS_FCB
        LD DE,NS_ARCH_FCB
        LD BC,36
        LDIR
        LD A,(FS_MASK)
        LD (NS_ATTR_MASK),A
        CALL NW_PARSE_CHECK
        RET C
        LD A,(NH_MODE)
        CP 3
        JP Z,NW_PARSE_ADD
        LD HL,BC_ALL
        LD B,3
        LD A,(NS_OPERANDS)
        CP 2
        JR NZ,NS_BUILD_MEMBER
        LD HL,(NS_MEMBER_ARG)
        LD A,(NS_MEMBER_LEN)
        LD B,A
        LD A,(NH_MODE)
        CP 2
        JR NZ,NS_BUILD_MEMBER
        LD A,(NS_OLD_DRIVE)
        LD D,A
        LD A,(NS_OLD_USER)
        LD E,A
        CALL DU_PARSE
        RET C
        PUSH HL
        PUSH BC
        CALL NS_DOMAIN
        JR C,NS_DEST_BAD
        LD BC,0
        CALL DU_NEXT
        JR C,NS_DEST_BAD
        LD A,D
        LD (NH_DEST),A
        LD A,E
        LD (NH_DUSER),A
        CALL DU_NEXT
        JR NC,NS_DEST_BAD
        POP BC
        POP HL
        LD A,B
        OR A
        JR NZ,NS_BUILD_MEMBER
        LD HL,BC_ALL
        LD B,3
        JR NS_BUILD_MEMBER
NS_DEST_BAD:
        POP BC
        POP HL
        SCF
        RET
NS_BUILD_MEMBER:
        CALL NS_LEXICAL
        RET C
        PUSH HL
        PUSH BC
        LD A,1
        CALL FP_VALIDATE
        POP BC
        POP HL
        RET C
        LD DE,NS_MEMBER_FCB
        CALL BC_PFCB
        OR A
        RET
NS_LEXICAL:
        PUSH HL
        PUSH BC
        LD A,B
        OR A
        JR Z,NS_LEX_DONE
NS_LEX_LOOP:
        LD A,(HL)
        CP '['
        JR Z,NS_LEX_BAD
        CP ']'
        JR Z,NS_LEX_BAD
        CP '/'
        JR Z,NS_LEX_BAD
        CP 5CH
        JR Z,NS_LEX_BAD
        CP '|'
        JR Z,NS_LEX_BAD
        CP '"'
        JR Z,NS_LEX_BAD
        INC HL
        DJNZ NS_LEX_LOOP
NS_LEX_DONE:
        POP BC
        POP HL
        OR A
        RET
NS_LEX_BAD:
        POP BC
        POP HL
        SCF
        RET
NS_DOMAIN:
        LD HL,DU_MAP+16
        LD B,48
NS_DOMAIN_LOOP:
        LD A,(HL)
        OR A
        JR NZ,NS_BAD
        INC HL
        DJNZ NS_DOMAIN_LOOP
        OR A
        RET
NS_BAD:
        SCF
        RET

NS_FREEZE:
        LD HL,0
        LD (NS_COUNT),HL
        LD (NS_SCAN_INDEX),HL
        LD HL,NS_ARCH_MAP
        LD DE,DU_MAP
        LD BC,64
        LDIR
NS_FREEZE_DU:
        LD BC,(NS_SCAN_INDEX)
        CALL DU_NEXT
        JR NC,NS_FREEZE_SELECTED
        OR A
        RET
NS_FREEZE_SELECTED:
        LD (NS_SCAN_INDEX),BC
        LD A,D
        LD (NS_CANDIDATE),A
        LD A,E
        LD (NS_CANDIDATE+1),A
        LD C,32
        CALL AC_BDOS
        LD HL,NS_ARCH_FCB
        LD DE,NS_SEARCH
        LD BC,36
        LDIR
        LD A,(NS_CANDIDATE)
        INC A
        LD (NS_SEARCH),A
        LD A,'?'
        LD (NS_SEARCH+12),A
        LD DE,NS_DMA
        LD C,26
        CALL AC_BDOS
        LD DE,NS_SEARCH
        LD C,17
        CALL AC_BDOS
NS_DIRECTORY_ENTRY:
        PUSH AF
        CALL NX_POLL
        JR NC,NS_FREEZE_CONTINUE
        POP BC
        SCF
        RET
NS_FREEZE_CONTINUE:
        POP AF
        CP 0FFH
        JR Z,NS_FREEZE_DU
        CP 4
        JP NC,NS_BAD
        ADD A,A
        ADD A,A
        ADD A,A
        ADD A,A
        ADD A,A
        LD E,A
        LD D,0
        LD HL,NS_DMA
        ADD HL,DE
        INC HL
        LD DE,NS_CANDIDATE+2
        LD B,11
NS_COPY_NAME:
        LD A,(HL)
        AND 7FH
        LD (DE),A
        INC HL
        INC DE
        DJNZ NS_COPY_NAME
        ; Attribute predicate is evaluated against each matching physical entry.
        LD DE,-3
        ADD HL,DE
        LD B,3
        LD E,1
        LD C,0
NS_ATTRIBUTE_BITS:
        LD A,(HL)
        AND 80H
        JR Z,NS_ATTRIBUTE_NEXT
        LD A,C
        OR E
        LD C,A
NS_ATTRIBUTE_NEXT:
        INC HL
        SLA E
        DJNZ NS_ATTRIBUTE_BITS
        LD A,(NS_ATTR_MASK)
        LD B,C
        INC B
NS_ATTRIBUTE_MATCH:
        RRCA
        DJNZ NS_ATTRIBUTE_MATCH
        JR NC,NS_DIRECTORY_NEXT
        CALL NS_INSERT
        RET C
NS_DIRECTORY_NEXT:
        LD DE,NS_SEARCH
        LD C,18
        CALL AC_BDOS
        JR NS_DIRECTORY_ENTRY
; Insert in global DU/name order; identical extents/overlapping DU terms dedup.
NS_INSERT:
        LD HL,NS_TABLE
        LD DE,(NS_COUNT)
        LD (NS_REMAIN),DE
NS_INSERT_SCAN:
        LD DE,(NS_REMAIN)
        LD A,D
        OR E
        JR Z,NS_INSERT_HERE
        PUSH HL
        LD DE,NS_CANDIDATE
        LD B,NS_RECORD
NS_COMPARE_NAME:
        LD A,(DE)
        CP (HL)
        JR NZ,NS_COMPARE_RESULT
        INC DE
        INC HL
        DJNZ NS_COMPARE_NAME
        POP HL
        OR A
        RET
NS_COMPARE_RESULT:
        POP HL
        JR C,NS_INSERT_HERE
        LD DE,NS_RECORD
        ADD HL,DE
        LD DE,(NS_REMAIN)
        DEC DE
        LD (NS_REMAIN),DE
        JR NS_INSERT_SCAN
NS_INSERT_HERE:
        LD DE,(NS_COUNT)
        PUSH HL
        LD HL,NS_LIMIT
        OR A
        SBC HL,DE
        POP HL
        JP Z,NS_BAD
        LD (NS_INSERT_PTR),HL
        ; Move the tail by one record, from the end downward.
        LD HL,(NS_REMAIN)
        ADD HL,HL
        LD B,H
        LD C,L
        ADD HL,HL
        ADD HL,HL
        ADD HL,BC
        LD BC,(NS_REMAIN)
        ADD HL,BC                  ; 10*remaining; add three more for 13
        ADD HL,BC
        ADD HL,BC
        LD B,H
        LD C,L
        LD A,B
        OR C
        JR Z,NS_INSERT_COPY
        LD HL,(NS_INSERT_PTR)
        ADD HL,BC
        DEC HL
        LD D,H
        LD E,L
        PUSH BC
        LD BC,NS_RECORD
        EX DE,HL
        ADD HL,BC
        EX DE,HL
        POP BC
        LDDR
NS_INSERT_COPY:
        LD HL,NS_CANDIDATE
        LD DE,(NS_INSERT_PTR)
        LD BC,NS_RECORD
        LDIR
        LD HL,(NS_COUNT)
        INC HL
        LD (NS_COUNT),HL
        OR A
        RET
NS_QUEUE_FCB:
        LD HL,(NS_CURRENT)
        LD A,(HL)
        INC A
        LD (NH_ADAPTER),A
        INC HL
        INC HL
        LD DE,NH_ADAPTER+1
        LD BC,11
        LDIR
        RET
NS_MEMBER_FILTER:
        CALL NS_MEMBER_MATCH
        LD A,1
        RET Z
        XOR A
        RET
NS_MEMBER_MATCH:
        LD HL,NH_CONTEXT+AS_MEMBER
        LD DE,NS_MEMBER_FCB+1
        LD B,11
NS_MEMBER_CHAR:
        LD A,(DE)
        CP '?'
        JR Z,NS_MEMBER_NEXT
        CP (HL)
        RET NZ
NS_MEMBER_NEXT:
        INC HL
        INC DE
        DJNZ NS_MEMBER_CHAR
        RET
; Z if candidate FCB at HL belongs to ANY frozen input, not just current one.
NS_IS_INPUT:
        LD (NS_IDENTITY),HL
        LD DE,(NS_COUNT)
        LD (NS_ID_LEFT),DE
        LD HL,NS_TABLE
NS_INPUT_NEXT:
        LD DE,(NS_ID_LEFT)
        LD A,D
        OR E
        JR Z,NS_NOT_INPUT
        PUSH HL
        LD DE,(NS_IDENTITY)
        LD A,(DE)
        DEC A
        CP (HL)
        JR NZ,NS_INPUT_SKIP
        INC HL
        LD A,(NH_DUSER)
        CP (HL)
        JR NZ,NS_INPUT_SKIP
        INC HL
        INC DE
        LD B,11
NS_INPUT_NAME:
        LD A,(DE)
        CP (HL)
        JR NZ,NS_INPUT_SKIP
        INC HL
        INC DE
        DJNZ NS_INPUT_NAME
        POP HL
        XOR A
        RET
NS_INPUT_SKIP:
        POP HL
        LD DE,NS_RECORD
        ADD HL,DE
        LD DE,(NS_ID_LEFT)
        DEC DE
        LD (NS_ID_LEFT),DE
        JR NS_INPUT_NEXT
NS_NOT_INPUT:
        OR 1
        RET
NS_IS_SYS:
        PUSH HL
        LD HL,NS_SYS_WORD
        JP NH_MATCH
NS_SYS_WORD: DB '/SYS',0
NS_ARCHIVE_TEXT: DB 'Archive ','$'
NS_BATCH_TEXT: DB 'Archives (hex): selected ','$'
NS_PROCESSED_TEXT: DB '; processed ','$'
NS_FAILED_TEXT: DB '; failed ','$'
NS_QUEUE_ERROR: DB 'NOAH: Selection failed or exceeds 512 archives; nothing modified.',13,10,'$'
NS_NO_ARCHIVES: DB 'NOAH: No archives matched.',13,10,'$'
NS_NO_MEMBERS: DB 'No members matched.',13,10,'$'
NS_UNPROCESSED_TEXT: DB '; unprocessed ', '$'
NS_WARNING_TEXT: DB 'Warnings, skips or incomplete CRC coverage reported above.',13,10,'$'
NOAH_SELECTION_DATA MACRO
NS_CAPTURED: DB 0
NS_OLD_DRIVE: DB 0
NS_OLD_USER: DB 0
NS_CUR_USER: DB 0
NS_OPERANDS: DB 0
NS_MODE_SET: DB 0
NS_YES: DB 0
NS_RO: DB 0
NS_SYS: DB 0
NS_ALL: DB 0
NS_STOP: DB 0
NS_WARNINGS: DB 0
NS_ARC_FAILED: DB 0
NS_MEMBER_ARG: DW 0
NS_MEMBER_LEN: DB 0
NS_TOKEN_PTR: DW 0
NS_TOKEN_LEN: DB 0
NS_SCAN_INDEX: DW 0
NS_COUNT: DW 0
NS_PROCESSED: DW 0
NS_BAD_ARCHIVES: DW 0
NS_CURRENT: DW 0
NS_REMAIN: DW 0
NS_INSERT_PTR: DW 0
NS_IDENTITY: DW 0
NS_ID_LEFT: DW 0
NS_ATTR_MASK: DB 0
NS_MATCHED: DS 4
NS_ARCH_MAP: DS 64
NS_ARCH_FCB: DS 36
NS_MEMBER_FCB: DS 36
NS_SEARCH: DS 36
NS_CANDIDATE: DS NS_RECORD
NS_TAIL: DS 128
NS_DMA: DS 128
NS_TABLE: DS NS_LIMIT*NS_RECORD
        ENDM
