; Translate a canonical package record in HL to a BCM2SS BIOS record.
; Only the first eight package records are in FM. Record 3 holds the ROM
; diagnostic vector, physically sector 13. The data starts at cylinder 1.
        LD A,L
        CP 3
        JR NZ,M2_PM_DATA
        LD L,12
        JR M2_PM_DONE
M2_PM_DATA:
        CP 8
        JR C,M2_PM_DONE
        PUSH DE
        LD DE,56
        ADD HL,DE
        POP DE
M2_PM_DONE:
