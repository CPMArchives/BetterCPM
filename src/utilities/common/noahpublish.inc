; Destination authorization and staged replacement. Existing original stays at
; FINAL until verified TMP is ready. BAK remains authoritative until publication
; and required protection restoration complete. No uncertain recovery is guessed.
NO_AUTHORIZE:
        XOR A
        LD (NO_EXISTED),A
        LD (NO_BACK_LIVE),A
        LD (NO_OLD_ATTR),A
        LD A,(NW_ACTIVE)
        OR A
        JR NZ,NO_NOT_INPUT
        LD HL,NX_FINAL
        CALL NS_IS_INPUT
        JR NZ,NO_NOT_INPUT
        LD DE,NO_INPUT_TEXT
        JP NO_SKIP
NO_NOT_INPUT:
        LD HL,NX_FINAL
        CALL NR_IS_MODULE
        JR NZ,NO_MODULE_SAFE
        LD DE,NO_MODULE_TEXT
        JP NO_SKIP
NO_MODULE_SAFE:
        CALL NO_INSPECT
        RET C
        OR A
        JR NZ,NO_EXISTING
        LD A,1
        OR A
        RET
NO_EXISTING:
        LD A,1
        LD (NO_EXISTED),A
        LD A,(NO_OBSERVED_ATTR)
        LD (NO_OLD_ATTR),A
        LD HL,NO_OBSERVED
        LD DE,NO_SNAPSHOT
        LD BC,32
        LDIR
        LD A,(NO_OLD_ATTR)
        AND 3
        JR Z,NO_ORDINARY
        LD B,A
        LD A,(NS_YES)
        OR A
        JR NZ,NO_PROTECTED_SKIP
        BIT 0,B
        JR Z,NO_CHECK_SYS
        LD A,(NS_RO)
        OR A
        JR Z,NO_PROTECTED_SKIP
NO_CHECK_SYS:
        BIT 1,B
        JR Z,NO_PROTECTED_ASK
        LD A,(NS_SYS)
        OR A
        JR Z,NO_PROTECTED_SKIP
NO_PROTECTED_ASK:
        LD A,B
        CALL NI_ASK
        RET C
        OR A
        RET NZ
        JR NO_DECLINED
NO_PROTECTED_SKIP:
        LD DE,NO_PROTECTED_TEXT
        JR NO_SKIP
NO_ORDINARY:
        LD A,(NW_ACTIVE)
        OR A
        LD A,1
        RET NZ
        LD A,(NS_YES)
        LD B,A
        LD A,(NS_ALL)
        OR B
        JR Z,NO_ORDINARY_ASK
        LD A,1
        OR A
        RET
NO_ORDINARY_ASK:
        XOR A
        CALL NI_ASK
        RET C
        OR A
        RET NZ
NO_DECLINED:
        LD DE,NO_DECLINED_TEXT
NO_SKIP:
        LD A,1
        LD (NS_WARNINGS),A
        PUSH DE
        LD HL,NX_FINAL
        CALL NX_PRINT_FCB
        POP DE
        CALL NH_PRINT
        XOR A
        RET
; Inspect ALL physical extents, preserving a first-entry identity snapshot and
; union of protection bits. Search state is never retained across a prompt/I/O.
NO_INSPECT:
        XOR A
        LD (NO_SEEN),A
        LD (NO_OBSERVED_ATTR),A
        LD HL,NX_FINAL
        LD DE,NX_SEARCH
        LD BC,36
        LDIR
        LD A,'?'
        LD (NX_SEARCH+12),A
        LD DE,NX_DIRECTORY
        LD C,26
        CALL AC_BDOS
        LD DE,NX_SEARCH
        LD C,17
        CALL AC_BDOS
NO_INSPECT_ENTRY:
        CP 0FFH
        JR Z,NO_INSPECT_END
        CP 4
        JP NC,NO_ERROR
        ADD A,A
        ADD A,A
        ADD A,A
        ADD A,A
        ADD A,A
        LD E,A
        LD D,0
        LD HL,NX_DIRECTORY
        ADD HL,DE
        LD A,(NO_SEEN)
        OR A
        JR NZ,NO_INSPECT_ATTR
        PUSH HL
        LD DE,NO_OBSERVED
        LD BC,32
        LDIR
        POP HL
        LD A,1
        LD (NO_SEEN),A
NO_INSPECT_ATTR:
        LD DE,9
        ADD HL,DE
        LD B,3
        LD E,1
        LD A,(NO_OBSERVED_ATTR)
        LD C,A
NO_ATTR_LOOP:
        LD A,(HL)
        AND 80H
        JR Z,NO_ATTR_NEXT
        LD A,C
        OR E
        LD C,A
NO_ATTR_NEXT:
        INC HL
        SLA E
        DJNZ NO_ATTR_LOOP
        LD A,C
        LD (NO_OBSERVED_ATTR),A
        LD DE,NX_SEARCH
        LD C,18
        CALL AC_BDOS
        JR NO_INSPECT_ENTRY
NO_INSPECT_END:
        LD A,(NO_SEEN)
        OR A
        RET

NO_PUBLISH:
        LD A,1
        LD (NX_PUBLICATION),A
        LD (NX_KEEP),A
        LD A,(NW_ACTIVE)
        OR A
        JR NZ,NO_PUBLICATION_INPUT_OK
        LD HL,NX_FINAL
        CALL NS_IS_INPUT
        JP Z,NO_ERROR
NO_PUBLICATION_INPUT_OK:
        LD HL,NX_FINAL
        CALL NR_IS_MODULE
        JP Z,NO_ERROR
        CALL NO_INSPECT
        RET C
        LD B,A
        LD A,(NO_EXISTED)
        CP B
        JP NZ,NO_ERROR
        OR A
        JP Z,NO_PUBLISH_NEW
        LD A,(NO_OBSERVED_ATTR)
        LD B,A
        LD A,(NO_OLD_ATTR)
        CP B
        JP NZ,NO_ERROR
        LD HL,NO_OBSERVED
        LD DE,NO_SNAPSHOT
        LD B,32
NO_IDENTITY_CHECK:
        LD A,(DE)
        CP (HL)
        JP NZ,NO_ERROR
        INC HL
        INC DE
        DJNZ NO_IDENTITY_CHECK
        ; Clear RO only at the authorized rename boundary, retaining SYS/ARC.
        LD HL,NX_FINAL
        LD A,(NO_OLD_ATTR)
        AND 6
        CALL NO_ATTRIBUTES
        JR NC,NO_BACKUP_RENAME
        CALL NO_RESTORE_FINAL
        JP NO_ERROR
NO_BACKUP_RENAME:
        LD HL,NX_FINAL
        LD DE,NX_BACKUP
        CALL NO_RENAME
        JR NC,NO_BACKUP_DONE
        ; A failed multi-extent rename may be partial. Never assume rollback
        ; is safe if the backup name now exists; retain/report both names.
        LD HL,NX_BACKUP
        CALL NX_EXISTS
        JP NZ,NO_UNCERTAIN
        CALL NO_RESTORE_FINAL
        JP NO_ERROR
NO_BACKUP_DONE:
        LD A,1
        LD (NO_BACK_LIVE),A
        LD HL,NX_BACKUP
        LD A,(NO_OLD_ATTR)
        CALL NO_ATTRIBUTES
        JP C,NO_ROLLBACK
NO_PUBLISH_NEW:
        LD HL,NX_FINAL
        CALL NX_EXISTS
        JR Z,NO_FINAL_ABSENT
        LD A,(NO_BACK_LIVE)
        OR A
        JP NZ,NO_UNCERTAIN
        JP NO_ERROR
NO_FINAL_ABSENT:
        LD HL,NX_TEMP
        LD DE,NX_FINAL
        CALL NO_RENAME
        JR NC,NO_NEW_NAMED
        ; A reported failure can still have moved some/all directory entries,
        ; including for a brand-new output. Inspect before claiming no publish.
        LD HL,NX_FINAL
        CALL NX_EXISTS
        JP NZ,NO_UNCERTAIN
        LD A,(NO_BACK_LIVE)
        OR A
        JP Z,NO_ERROR
        JP NO_ROLLBACK
NO_NEW_NAMED:
        XOR A
        LD (NX_LIVE),A
        LD A,(NO_EXISTED)
        OR A
        JR Z,NO_PUBLISHED
        LD HL,NX_FINAL
        LD A,(NO_OLD_ATTR)
        AND 3
        CALL NO_ATTRIBUTES
        JR NC,NO_PUBLISHED
        ; Required metadata failed. Keep verified new bytes in TMP before
        ; restoring the original name; never delete either copy to roll back.
        LD HL,NX_TEMP
        CALL NX_EXISTS
        JP NZ,NO_UNCERTAIN
        LD HL,NX_FINAL
        XOR A
        CALL NO_ATTRIBUTES
        JP C,NO_UNCERTAIN
        LD HL,NX_FINAL
        LD DE,NX_TEMP
        CALL NO_RENAME
        JP C,NO_UNCERTAIN
        LD A,1
        LD (NX_LIVE),A
        JP NO_ROLLBACK
NO_PUBLISHED:
        XOR A
        LD (NX_KEEP),A
        LD A,(NO_BACK_LIVE)
        OR A
        RET Z
        LD HL,NX_BACKUP
        LD A,(NO_OLD_ATTR)
        AND 6
        CALL NO_ATTRIBUTES
        JR C,NO_BACKUP_WARNING
        LD DE,NX_BACKUP
        LD C,19
        CALL AC_BDOS
        CP 0FFH
        JR Z,NO_BACKUP_WARNING
        XOR A
        LD (NO_BACK_LIVE),A
        RET
NO_BACKUP_WARNING:
        LD HL,NX_BACKUP
        CALL NX_EXISTS
        JR NZ,NO_BACKUP_STILL_PRESENT
        LD A,1
        LD (NS_WARNINGS),A
        LD DE,NO_CLEANUP_ABSENT
        CALL NH_PRINT
        LD HL,NX_BACKUP
        CALL NX_PRINT_FCB
        LD DE,NH_NEWLINE
        CALL NH_PRINT
        OR A
        RET
NO_BACKUP_STILL_PRESENT:
        LD HL,NX_BACKUP
        LD A,(NO_OLD_ATTR)
        CALL NO_ATTRIBUTES
        JR NC,NO_WARNING_PRINT
        LD A,1
        LD (NS_STOP),A
NO_WARNING_PRINT:
        CALL NA_REC_BACKUP
        LD A,1
        LD (NS_WARNINGS),A
        LD DE,NO_CLEANUP_TEXT
        CALL NH_PRINT
        LD HL,NX_BACKUP
        CALL NX_PRINT_FCB
        LD DE,NH_NEWLINE
        CALL NH_PRINT
        OR A
        RET
NO_ROLLBACK:
        LD HL,NX_FINAL
        CALL NX_EXISTS
        JP NZ,NO_UNCERTAIN
        LD HL,NX_BACKUP
        LD A,(NO_OLD_ATTR)
        AND 6
        CALL NO_ATTRIBUTES
        JP C,NO_UNCERTAIN
        LD HL,NX_BACKUP
        LD DE,NX_FINAL
        CALL NO_RENAME
        JP C,NO_UNCERTAIN
        XOR A
        LD (NO_BACK_LIVE),A
        CALL NO_RESTORE_FINAL
        JP NO_ERROR
NO_RESTORE_FINAL:
        LD HL,NX_FINAL
        LD A,(NO_OLD_ATTR)
        CALL NO_ATTRIBUTES
        RET NC
        LD A,1
        LD (NS_STOP),A
        LD DE,NO_PROTECTION_ERROR
        CALL NH_PRINT
        LD HL,NX_FINAL
        CALL NX_PRINT_FCB
        LD DE,NH_NEWLINE
        CALL NH_PRINT
        SCF
        RET
NO_UNCERTAIN:
        LD A,(NO_BACK_LIVE)
        OR A
        JR Z,NO_UNCERTAIN_REPORT
        LD HL,NX_BACKUP
        CALL NX_EXISTS
        JR Z,NO_UNCERTAIN_REPORT
        CALL NA_REC_BACKUP
        ; A successfully created backup is still our original even if its
        ; rename-back failed. Reapply protection before handing off recovery.
        LD HL,NX_BACKUP
        LD A,(NO_OLD_ATTR)
        CALL NO_ATTRIBUTES
        JR NC,NO_UNCERTAIN_REPORT
        LD DE,NO_PROTECTION_ERROR
        CALL NH_PRINT
        LD HL,NX_BACKUP
        CALL NX_PRINT_FCB
        LD DE,NH_NEWLINE
        CALL NH_PRINT
NO_UNCERTAIN_REPORT:
        LD A,(NO_OLD_ATTR)
        AND 3
        JR Z,NO_UNCERTAIN_NAMES
        LD DE,NO_PROTECTION_UNCERTAIN
        CALL NH_PRINT
NO_UNCERTAIN_NAMES:
        LD A,1
        LD (NS_STOP),A
        LD DE,NO_UNCERTAIN_TEXT
        CALL NH_PRINT
        LD HL,NX_BACKUP
        CALL NX_PRINT_FCB
        LD DE,NO_NEW_TEXT
        CALL NH_PRINT
        LD HL,NX_FINAL
        CALL NX_PRINT_FCB
        LD DE,NH_NEWLINE
        CALL NH_PRINT
NO_ERROR:
        LD A,AS_OUTPUT
        SCF
        RET
; HL=FCB, A=RO/SYS/ARC mask. Use a private FCB, leaving identities canonical.
NO_ATTRIBUTES:
        LD (NO_SET_MASK),A
        LD DE,NO_ATTR_FCB
        LD BC,36
        LDIR
        LD HL,NO_ATTR_FCB+9
        LD B,3
        LD A,(NO_SET_MASK)
        LD C,A
NO_SET_BITS:
        LD A,(HL)
        AND 7FH
        BIT 0,C
        JR Z,NO_SET_NEXT
        OR 80H
NO_SET_NEXT:
        LD (HL),A
        INC HL
        SRL C
        DJNZ NO_SET_BITS
        LD DE,NO_ATTR_FCB
        LD C,30
        CALL AC_BDOS
        CP 0FFH
        JP Z,NO_ERROR
        OR A
        RET
; HL=source FCB, DE=target FCB. Return C on reported failure.
NO_RENAME:
        PUSH HL
        PUSH DE
        LD HL,NX_RENAME
        LD DE,NX_RENAME+1
        LD BC,35
        LD (HL),0
        LDIR
        POP HL
        LD DE,NX_RENAME+16
        LD BC,12
        LDIR
        POP HL
        LD DE,NX_RENAME
        LD BC,12
        LDIR
        LD DE,NX_RENAME
        LD C,23
        CALL AC_BDOS
        CP 0FFH
        JP Z,NO_ERROR
        OR A
        RET
NO_INPUT_TEXT: DB ': selected input archive; skipped.',13,10,'$'
NO_PROTECTED_TEXT: DB ': protected; skipped.',13,10,'$'
NO_DECLINED_TEXT: DB ': replacement declined; skipped.',13,10,'$'
NO_CLEANUP_TEXT: DB 'Update completed; backup cleanup failed: ','$'
NO_CLEANUP_ABSENT: DB 'Update completed; cleanup failed; backup not found: ','$'
NO_PROTECTION_UNCERTAIN: DB 'Original protection may need restoration.',13,10,'$'
NO_PROTECTION_ERROR: DB 'Protection restoration failed: ','$'
NO_UNCERTAIN_TEXT: DB 'Recovery required; stop. Original/backup may be at ','$'
NO_NEW_TEXT: DB 13,10,'Final/new path: ','$'
NOAH_PUBLISH_DATA MACRO
NO_MODULE_TEXT: DB ' active NOAH.OVL cannot be replaced.',13,10,'$'
NO_EXISTED: DB 0
NO_BACK_LIVE: DB 0
NO_OLD_ATTR: DB 0
NO_OBSERVED_ATTR: DB 0
NO_SEEN: DB 0
NO_SET_MASK: DB 0
NO_OBSERVED: DS 32
NO_SNAPSHOT: DS 32
NO_ATTR_FCB: DS 36
        ENDM
