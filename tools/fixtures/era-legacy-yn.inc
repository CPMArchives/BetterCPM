; Historical ERA confirmation reference, retained for differential tests.
; From BetterCPM 55bc5fe7cec38e9e1f4859ece940d6b8fa9bf49c src/utilities/era.mac.
; The unchanged production console helpers are linked by the test harness.
E_YN:
        CALL E_KEY
        CP 3
        SCF
        RET Z
        AND 0DFH
        CP 'Y'
        JR Z,E_YESKEY
        CP 'N'
        JR NZ,E_YN
        CALL E_CHAR
        CALL E_NEWLINE
        LD A,1
        OR A
        RET
E_YESKEY:
        CALL E_CHAR
        CALL E_NEWLINE
        XOR A
        RET
