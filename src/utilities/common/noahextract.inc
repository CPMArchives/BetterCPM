; NOAH extraction: shared archive selection/member pattern and one destination
; DU. The source adapter switches into its owner user for reads and restores
; destination user before output I/O. NO_AUTHORIZE/NO_PUBLISH handle collision,
; protection, backup/rollback and cleanup without overwriting selected inputs.
; Every output is staged, closed, reopened and byte-compared before publication.
NX_EXTRACT:
        XOR A
        LD HL,NX_TOTAL
        LD B,16
NX_ZERO_COUNTS:
        LD (HL),A
        INC HL
        DJNZ NX_ZERO_COUNTS
        ; Audit counters include the directory itself.
        LD HL,NH_AUDIT+LA_CHECKED
        LD DE,NX_TOTAL
        LD BC,4
        LDIR
        LD HL,(NX_TOTAL)
        LD DE,(NH_AUDIT+LA_UNCHECKED)
        ADD HL,DE
        LD (NX_TOTAL),HL
        LD HL,(NX_TOTAL+2)
        LD DE,(NH_AUDIT+LA_UNCHECKED+2)
        ADC HL,DE
        LD (NX_TOTAL+2),HL
        LD A,(NH_ARK)
        OR A
        JR NZ,NX_TOTAL_READY
        LD HL,(NX_TOTAL)
        LD A,H
        OR L
        JR NZ,NX_TOTAL_DECREMENT
        LD HL,(NX_TOTAL+2)
        DEC HL
        LD (NX_TOTAL+2),HL
        LD HL,0
NX_TOTAL_DECREMENT:
        DEC HL
        LD (NX_TOTAL),HL
NX_TOTAL_READY:
        LD A,(NH_DUSER)
        LD E,A
        LD C,32
        CALL AC_BDOS
        CALL NH_REOPEN
        JP C,NX_ARCHIVE_ERROR
NX_NEXT:
        CALL NX_POLL
        JP C,NX_STOP
        CALL NH_NEXT
        JR NC,NX_MEMBER
        CP AS_END
        JP Z,NX_SUMMARY
        JP NX_ARCHIVE_ERROR
NX_MEMBER:
        CALL NS_MEMBER_MATCH
        JP NZ,NX_NEXT
        CALL NA_RESET_NAMES
        XOR A
        LD (NX_TEMP_OPEN),A
        LD (NX_VERIFY_OPEN),A
        LD (NX_LIVE),A
        LD (NX_KEEP),A
        LD (NX_ATTEMPTED),A
        LD (NX_PUBLICATION),A
        LD HL,NX_FINAL
        LD DE,NX_FINAL+1
        LD BC,36*6-1
        LD (HL),0
        LDIR
        LD A,(NH_DEST)
        INC A
        LD (NX_FINAL),A
        LD HL,NH_CONTEXT+AS_MEMBER
        LD DE,NX_FINAL+1
        LD BC,11
        LDIR
        CALL NH_MEMBER_PROBE
        JP C,NX_MEMBER_ERROR
        CP AS_UNSUPPORTED
        JR Z,NX_SKIP_MEMBER
        LD A,(NC_MEMBER_PENDING)
        OR A
        JR NZ,NX_NEW_OUTPUT
        CALL NO_AUTHORIZE
        JP C,NX_MEMBER_ERROR
        OR A
        JR NZ,NX_NEW_OUTPUT
NX_SKIP_MEMBER:
        LD HL,NX_SKIPPED
        CALL NX_INC_COUNT
        JP NX_NEXT
NX_NEW_OUTPUT:
        LD A,(NH_ARK)
        OR A
        JR NZ,NX_CRC_REPORTED
        LD A,(IX+AS_MEMBER+AM_CRC)
        OR (IX+AS_MEMBER+AM_CRC+1)
        JR NZ,NX_CRC_REPORTED
        LD HL,NX_FINAL
        CALL NX_PRINT_FCB
        LD DE,NH_CRC_MISSING
        CALL NH_PRINT
NX_CRC_REPORTED:
        CALL NX_TEMP_PAIR
        JP C,NX_MEMBER_ERROR
        LD A,1
        LD (NX_ATTEMPTED),A
        LD DE,NX_TEMP
        LD C,22
        CALL AC_BDOS
        CP 0FFH
        JP Z,NX_OUTPUT_ERROR
        LD A,1
        LD (NX_LIVE),A
        LD (NX_TEMP_OPEN),A
NX_WRITE_LOOP:
        CALL NX_POLL
        JP C,NX_MEMBER_ERROR
        CALL NX_SOURCE_CHUNK
        JR NC,NX_WRITE_CHUNK
        CP AS_END
        JP NZ,NX_MEMBER_ERROR
        JR NX_CLOSE_WRITTEN
NX_WRITE_CHUNK:
        LD DE,NX_BUFFER
        LD C,26
        CALL AC_BDOS
        LD DE,NX_TEMP
        LD C,21
        CALL AC_BDOS
        OR A
        JP NZ,NX_OUTPUT_ERROR
        JR NX_WRITE_LOOP
NX_CLOSE_WRITTEN:
        LD DE,NX_TEMP
        LD C,16
        CALL AC_BDOS
        CP 0FFH
        JP Z,NX_OUTPUT_ERROR
        XOR A
        LD (NX_TEMP_OPEN),A
        LD HL,NX_TEMP
        LD DE,NX_VERIFY
        LD BC,12
        LDIR
        LD DE,NX_VERIFY
        LD C,15
        CALL AC_BDOS
        CP 0FFH
        JP Z,NX_OUTPUT_ERROR
        LD A,1
        LD (NX_VERIFY_OPEN),A
        ; Reset only the selected member's read cursor from immutable metadata.
        LD HL,NH_CONTEXT+AS_MEMBER+AM_OFFSET
        LD DE,NH_CONTEXT+AS_POSITION
        LD BC,4
        LDIR
        LD HL,NH_CONTEXT+AS_MEMBER+AM_LENGTH
        LD DE,NH_CONTEXT+AS_LEFT
        LD BC,4
        LDIR
        LD A,(NH_ARK)
        OR A
        CALL NZ,NW_PLANS+24
NX_VERIFY_LOOP:
        CALL NX_POLL
        JP C,NX_MEMBER_ERROR
        CALL NX_SOURCE_CHUNK
        JR NC,NX_VERIFY_CHUNK
        CP AS_END
        JP NZ,NX_MEMBER_ERROR
        JR NX_VERIFY_EOF
NX_VERIFY_CHUNK:
        LD DE,NX_READ_BUFFER
        LD C,26
        CALL AC_BDOS
        LD DE,NX_VERIFY
        LD C,20
        CALL AC_BDOS
        OR A
        JP NZ,NX_OUTPUT_ERROR
        LD HL,NX_BUFFER
        LD DE,NX_READ_BUFFER
        LD B,128
NX_COMPARE_BYTES:
        LD A,(DE)
        CP (HL)
        JP NZ,NX_OUTPUT_ERROR
        INC HL
        INC DE
        DJNZ NX_COMPARE_BYTES
        JR NX_VERIFY_LOOP
NX_VERIFY_EOF:
        LD DE,NX_READ_BUFFER
        LD C,26
        CALL AC_BDOS
        LD DE,NX_VERIFY
        LD C,20
        CALL AC_BDOS
        CP 1
        JP NZ,NX_OUTPUT_ERROR
        LD DE,NX_VERIFY
        LD C,16
        CALL AC_BDOS
        CP 0FFH
        JP Z,NX_OUTPUT_ERROR
        XOR A
        LD (NX_VERIFY_OPEN),A
        CALL NX_POLL
        JP C,NX_MEMBER_ERROR
        LD A,(NC_MEMBER_PENDING)
        OR A
        JP NZ,NC_MEMBER_PROCESS
        CALL NO_PUBLISH
        JP C,NX_OUTPUT_ERROR
        LD HL,NX_FINAL
        LD DE,NX_EXTRACTED_TEXT
        CALL NH_PROGRESS_FCB
        LD HL,NX_COMPLETED
        CALL NX_INC_COUNT
        ; This adapter has no filesystem timestamp setter: never fake success.
NX_STAMP_CHECK:
        LD A,(NH_ARK)
        OR A
        JP NZ,NW_PLANS+21
        LD HL,NH_CONTEXT+AS_MEMBER+AM_DATES
        LD B,8
        XOR A
NX_STAMP_SCAN:
        OR (HL)
        INC HL
        DJNZ NX_STAMP_SCAN
        JP Z,NX_NEXT
        CALL AC_SET_STAMP
        LD A,1
        LD (NS_WARNINGS),A
        LD DE,NX_STAMP_TEXT
        CALL NH_PRINT
        JP NX_NEXT
NX_OUTPUT_ERROR:
        LD A,AS_OUTPUT
NX_MEMBER_ERROR:
        LD (NX_RESULT),A
        LD A,(NH_ABORTED)
        OR A
        JR Z,NX_RESULT_READY
        LD A,AS_CANCEL
        LD (NX_RESULT),A
NX_RESULT_READY:
        CALL NX_CLEANUP
        LD A,(NX_RESULT)
        CP AS_CANCEL
        JP Z,NX_STOP
        LD HL,NX_FINAL
        CALL NX_PRINT_FCB
        LD DE,NX_FAILED_TEXT
        CALL NH_PRINT
        LD IX,NH_CONTEXT
        LD A,(IX+AS_PHASE)
        CP AS_SELECTED
        JR NZ,NX_ERROR_STOP
        CALL NX_RETRY_CLEANUP
        JR C,NX_ERROR_STOP
        LD HL,NI_TARGET_CTX
        CALL NI_FAILURE
        JR C,NX_ERROR_ABORT
        CP 'R'
        JR Z,NX_RETRY_MEMBER
        CALL NX_COUNT_FAILURE
        LD DE,NX_FAILURE_SKIP_TEXT
        CALL NH_PRINT
        JP NX_NEXT
NX_RETRY_MEMBER:
        LD A,1
        LD (NS_WARNINGS),A
        ; No sticky reader error is cleared: only a still-selected member can
        ; rewind its own bounded cursor. NEXT has not been called again.
        LD HL,NH_CONTEXT+AS_MEMBER+AM_OFFSET
        LD DE,NH_CONTEXT+AS_POSITION
        LD BC,4
        LDIR
        LD HL,NH_CONTEXT+AS_MEMBER+AM_LENGTH
        LD DE,NH_CONTEXT+AS_LEFT
        LD BC,4
        LDIR
        JP NX_MEMBER
NX_ERROR_ABORT:
        CALL NX_COUNT_FAILURE
        JP NX_STOP
NX_ERROR_STOP:
        CALL NX_COUNT_FAILURE
        JP NX_SUMMARY
NX_COUNT_FAILURE:
        LD A,1
        LD (NS_ARC_FAILED),A
        LD (NS_WARNINGS),A
        LD HL,NX_FAILED
        JP NX_INC_COUNT
NX_ARCHIVE_ERROR:
        LD A,1
        LD (NS_ARC_FAILED),A
        LD DE,NX_ARCHIVE_TEXT
        CALL NH_PRINT
        JP NX_SUMMARY
NX_STOP:
        LD DE,NX_CANCEL_TEXT
        CALL NH_PRINT
NX_SUMMARY:
        LD HL,NX_TOTAL
        LD B,4
        XOR A
NX_ANY_SELECTED:
        OR (HL)
        INC HL
        DJNZ NX_ANY_SELECTED
        JR NZ,NX_SUMMARY_COUNTS
        LD A,1
        LD (NS_WARNINGS),A
        LD DE,NS_NO_MEMBERS
        CALL NH_PRINT
NX_SUMMARY_COUNTS:
        LD HL,NX_TOTAL
        CALL NW_NONZERO
        JR Z,NX_SUMMARY_RESULT_READY
        LD A,2
        LD (NS_DISPOSITION),A
        LD HL,NX_COMPLETED
        CALL NW_NONZERO
        JR Z,NX_SUMMARY_RESULT_READY
        LD A,1
        LD (NS_DISPOSITION),A
NX_SUMMARY_RESULT_READY:
        LD HL,NX_TOTAL
        LD DE,NX_UNPROCESSED
        LD BC,4
        LDIR
        LD DE,NX_COMPLETED
        CALL NX_SUB_COUNT
        CALL NX_SUB_COUNT
        CALL NX_SUB_COUNT
        CALL NA_EXTRACT
        LD DE,NX_DONE_TEXT
        CALL NH_PRINT
        LD HL,NX_COMPLETED
        CALL NH_PRINT_COUNT
        LD DE,NX_SKIP_TEXT
        CALL NH_PRINT
        LD HL,NX_SKIPPED
        CALL NH_PRINT_COUNT
        LD DE,NX_FAIL_TEXT
        CALL NH_PRINT
        LD HL,NX_FAILED
        CALL NH_PRINT_COUNT
        LD DE,NH_NEWLINE
        CALL NH_PRINT
        LD DE,NX_UNPROCESSED_TEXT
        CALL NH_PRINT
        LD HL,NX_UNPROCESSED
        CALL NH_PRINT_COUNT
        LD DE,NH_NEWLINE
        CALL NH_PRINT
        JP NH_CLOSE
NX_SUB_COUNT:
        LD HL,NX_UNPROCESSED
        LD B,4
        OR A
NX_SUB_BYTE:
        LD A,(DE)
        LD C,A
        LD A,(HL)
        SBC A,C
        LD (HL),A
        INC HL
        INC DE
        DJNZ NX_SUB_BYTE
        RET
NX_INC_COUNT:
        INC (HL)
        RET NZ
        INC HL
        INC (HL)
        RET NZ
        INC HL
        INC (HL)
        RET NZ
        INC HL
        INC (HL)
        RET
NX_POLL:
        LD C,6
        LD E,0FFH
        CALL AC_BDOS
        CP 3
        JR Z,NX_POLL_STOP
        OR A
        RET
NX_POLL_STOP:
        LD A,1
        LD (NH_ABORTED),A
        LD A,AS_CANCEL
        SCF
        RET
NX_SOURCE_CHUNK:
        LD HL,NX_BUFFER
        LD DE,NX_BUFFER+1
        LD BC,127
        LD (HL),1AH
        LDIR
        LD DE,NX_BUFFER
        LD BC,128
        JP NH_READ

; Return Z if absent, NZ if present. Only our private search FCB/DMA changes.
NX_EXISTS:
        LD DE,NX_SEARCH
        LD BC,36
        LDIR
        ; A partial rename/delete can leave only a later physical extent.
        LD A,'?'
        LD (NX_SEARCH+12),A
        LD DE,NX_DIRECTORY
        LD C,26
        CALL AC_BDOS
        LD DE,NX_SEARCH
        LD C,17
        CALL AC_BDOS
        CP 0FFH
        RET Z
        OR 1
        RET
NX_TEMP_PAIR:
        ; A prior codec stage can leave extent, allocation and record fields
        ; here. MAKE does not reset every field: start each new file at record
        ; zero rather than carrying the preceding temporary's cursor/map.
        LD HL,NX_TEMP
        LD DE,NX_TEMP+1
        LD BC,35
        LD (HL),0
        LDIR
        LD A,(NH_DEST)
        INC A
        LD (NX_TEMP),A
        LD HL,NX_TEMP+1
        LD B,11
        LD A,' '
NX_TEMP_SPACES:
        LD (HL),A
        INC HL
        DJNZ NX_TEMP_SPACES
        LD HL,NX_FINAL+1
        LD DE,NX_TEMP+1
        LD B,6
NX_PREFIX:
        LD A,(HL)
        CP ' '
        JR Z,NX_PREFIX_DONE
        LD (DE),A
        INC DE
        INC HL
        DJNZ NX_PREFIX
NX_PREFIX_DONE:
        LD (NX_DIGITS),DE
        XOR A
        LD (NX_NUMBER),A
        LD HL,NX_TMP_EXT
        LD DE,NX_TEMP+9
        LD BC,3
        LDIR
NX_PAIR_CANDIDATE:
        LD A,(NX_NUMBER)
        LD C,0
NX_TENS:
        CP 10
        JR C,NX_DIGITS_READY
        SUB 10
        INC C
        JR NX_TENS
NX_DIGITS_READY:
        ADD A,'0'
        LD B,A
        LD HL,(NX_DIGITS)
        LD A,C
        ADD A,'0'
        LD (HL),A
        INC HL
        LD (HL),B
        LD HL,NX_TEMP
        LD DE,NX_BACKUP
        LD BC,36
        LDIR
        LD HL,NX_BAK_EXT
        LD DE,NX_BACKUP+9
        LD BC,3
        LDIR
        LD HL,NX_TEMP
        CALL NS_IS_INPUT
        JR Z,NX_NEXT_PAIR
        LD HL,NX_BACKUP
        CALL NS_IS_INPUT
        JR Z,NX_NEXT_PAIR
        LD HL,NX_TEMP
        CALL NX_SAME_FINAL
        JR Z,NX_NEXT_PAIR
        LD HL,NX_BACKUP
        CALL NX_SAME_FINAL
        JR Z,NX_NEXT_PAIR
        ; Archive must not be selected as a recovery filename either.
        LD HL,NX_TEMP
        CALL NX_EXISTS
        JR NZ,NX_NEXT_PAIR
        LD HL,NX_BACKUP
        CALL NX_EXISTS
        JR Z,NX_PAIR_FOUND
NX_NEXT_PAIR:
        LD A,(NX_NUMBER)
        INC A
        LD (NX_NUMBER),A
        CP 100
        JR C,NX_PAIR_CANDIDATE
        LD A,AS_OUTPUT
        SCF
        RET
NX_PAIR_FOUND:
        OR A
        RET
NX_SAME_FINAL:
        LD DE,NX_FINAL
        LD B,12
NX_ID_COMPARE:
        LD A,(DE)
        CP (HL)
        RET NZ
        INC HL
        INC DE
        DJNZ NX_ID_COMPARE
        RET
NX_CLEANUP:
        LD A,(NX_TEMP_OPEN)
        OR A
        JR Z,NX_CLEAN_VERIFY
        LD DE,NX_TEMP
        LD C,16
        CALL AC_BDOS
        CP 0FFH
        JR Z,NX_TEMP_UNCERTAIN
        XOR A
        LD (NX_TEMP_OPEN),A
        JR NX_CLEAN_VERIFY
NX_TEMP_UNCERTAIN:
        LD HL,NX_TEMP
        CALL NX_CLOSE_UNCERTAIN
NX_CLEAN_VERIFY:
        LD A,(NX_VERIFY_OPEN)
        OR A
        JR Z,NX_CLEAN_LIVE
        LD DE,NX_VERIFY
        LD C,16
        CALL AC_BDOS
        CP 0FFH
        JR Z,NX_VERIFY_UNCERTAIN
        XOR A
        LD (NX_VERIFY_OPEN),A
        JR NX_CLEAN_LIVE
NX_VERIFY_UNCERTAIN:
        LD HL,NX_VERIFY
        CALL NX_CLOSE_UNCERTAIN
NX_CLEAN_LIVE:
        LD A,(NX_LIVE)
        OR A
        RET Z
        LD A,(NX_KEEP)
        OR A
        JR NZ,NX_RETAIN
        LD DE,NX_TEMP
        LD C,19
        CALL AC_BDOS
        ; A reported delete result is not proof of complete absence.
        LD HL,NX_TEMP
        CALL NX_EXISTS
        JR NZ,NX_RETAIN
NX_TEMP_ABSENT:
        XOR A
        LD (NX_LIVE),A
        RET
NX_RETAIN:
        LD HL,NX_TEMP
        CALL NX_EXISTS
        JR Z,NX_TEMP_ABSENT
        CALL NA_REC_TEMP
        LD A,1
        LD (NX_KEEP),A
        LD (NS_WARNINGS),A
        LD DE,NX_RETAIN_TEXT
        CALL NH_PRINT
        LD HL,NX_TEMP
        CALL NX_PRINT_FCB
        LD DE,NH_NEWLINE
        CALL NH_PRINT
        SCF
        RET
NX_CLOSE_UNCERTAIN:
        LD A,1
        LD (NX_KEEP),A
        LD (NS_WARNINGS),A
        LD (NS_STOP),A
        LD DE,NX_CLOSE_TEXT
        CALL NH_PRINT
        CALL NX_PRINT_FCB
        LD DE,NH_NEWLINE
        JP NH_PRINT
; A restart may discard only a closed, disposable candidate stage. Publication
; is a one-way boundary for this decision, even if rollback subsequently works.
NX_RETRY_CLEANUP:
        LD A,(NX_PUBLICATION)
        LD B,A
        LD A,(NS_STOP)
        OR B
        LD B,A
        LD A,(NH_ABORTED)
        OR B
        LD B,A
        LD A,(NX_KEEP)
        OR B
        JR NZ,NX_RETRY_UNSAFE
        CALL NX_CLEANUP
        RET C
        LD A,(NX_TEMP_OPEN)
        LD B,A
        LD A,(NX_VERIFY_OPEN)
        OR B
        LD B,A
        LD A,(NX_LIVE)
        OR B
        JR NZ,NX_RETRY_UNSAFE
        LD A,(NX_ATTEMPTED)
        OR A
        RET Z
        ; MAKE failure may still have left a name. Never commandeer or reset
        ; an unconfirmed entry; require observed absence before starting over.
        LD HL,NX_TEMP
        CALL NX_EXISTS
        JR Z,NX_RETRY_ABSENT
        LD A,1
        LD (NS_STOP),A
        JP NX_RETAIN
NX_RETRY_ABSENT:
        XOR A
        LD (NX_ATTEMPTED),A
        RET
NX_RETRY_UNSAFE:
        SCF
        RET
NX_PRINT_FCB:
        LD A,(HL)
        DEC A
        LD D,A
        LD A,(NH_DUSER)
        LD E,A
        CALL NS_PRINT_DU
        INC HL
        LD B,8
        CALL NX_NAME_FIELD
        LD A,(HL)
        CP ' '
        RET Z
        LD E,'.'
        LD C,2
        CALL AC_BDOS
        LD B,3
NX_NAME_FIELD:
        LD A,(HL)
        CP ' '
        JR Z,NX_NAME_NEXT
        LD E,A
        LD C,2
        CALL AC_BDOS
NX_NAME_NEXT:
        INC HL
        DJNZ NX_NAME_FIELD
        RET
NX_TMP_EXT: DB 'TMP'
NX_BAK_EXT: DB 'BAK'
NX_EXISTS_TEXT: DB ': exists; skipped.',13,10,'$'
NX_EXTRACTED_TEXT: DB ': extracted and verified.',13,10,'$'
NX_FAILED_TEXT: DB ': extraction failed.',13,10,'$'
NX_FAILURE_SKIP_TEXT: DB 'Skipped after failure.',13,10,'$'
NX_STAMP_TEXT: DB 'Timestamp not restored: filesystem service unavailable.',13,10,'$'
NX_RETAIN_TEXT: DB 'Temporary retained: ','$'
NX_CLOSE_TEXT: DB 'Close unconfirmed: ','$'
NX_ARCHIVE_TEXT: DB 'NOAH: Archive read failed; extraction stopped.',13,10,'$'
NX_CANCEL_TEXT: DB 'NOAH: Extraction cancelled.',13,10,'$'
NX_DONE_TEXT: DB 'Extracted (hex): ','$'
NX_SKIP_TEXT: DB '; skipped: ','$'
NX_FAIL_TEXT: DB '; failed: ','$'
NX_UNPROCESSED_TEXT: DB 'Unprocessed (hex): ','$'
NOAH_EXTRACT_DATA MACRO
NX_ATTEMPTED: DB 0
NX_PUBLICATION: DB 0
NX_TOTAL: DS 4
NX_COMPLETED: DS 4
NX_SKIPPED: DS 4
NX_FAILED: DS 4
NX_UNPROCESSED: DS 4
NX_DIGITS: DW 0
NX_NUMBER: DB 0
NX_RESULT: DB 0
NX_TEMP_OPEN: DB 0
NX_VERIFY_OPEN: DB 0
NX_LIVE: DB 0
NX_KEEP: DB 0
NX_FINAL: DS 36
NX_TEMP: DS 36
NX_BACKUP: DS 36
NX_RENAME: DS 36
NX_SEARCH: DS 36
NX_VERIFY: DS 36
NX_BUFFER: DS 128
NX_READ_BUFFER: DS 128
NX_DIRECTORY: DS 128
        ENDM
