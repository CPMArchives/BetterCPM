WPKEY:
        LD C,1
        CALL BDOS
        CP 3
        JR Z,WPCANCEL
        CP '?'
        JR Z,WPHELP
        CP 13
        JR Z,WPYES
        AND 0DFH
        CP 'Y'
        JR Z,WPYES
        CP 'N'
        JR Z,WPANSWER
        CP 'A'
        JR NZ,WPKEY
        LD (ALLYES),A
WPYES:
        LD A,'Y'
WPANSWER:
        LD (WRESPONS),A
        JP NL
WPHELP:
        CALL NL
        LD HL,MSGPHELP
        CALL TEXT
        JP WPROMPT
WPCANCEL:
        LD A,1
        LD (CANCEL),A
        LD (INCOMPLE),A
        JP NL
