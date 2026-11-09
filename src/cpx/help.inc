; Resident help printer for the existing bounded UH_QUERY recognizer.
; DE points to the metadata-owned title string, followed by four inline
; dollar-terminated parts: purpose, usage, resident options and topic name. The engine preserves
; caller BC/DE/HL; no console input, provider or filesystem calls are used.
; Standard /VER identification shares the title/purpose streams with help.
RH_IDENT:
        EX DE,HL
        LD DE,RH_IDPARTS
        LD B,4
        JR RH_HLOOP
RH_HELP:
        EX DE,HL
        LD DE,RH_PARTS
        LD B,9
RH_HLOOP:
        PUSH BC
        PUSH DE
        PUSH HL
        EX DE,HL
        LD C,9
        CALL 00005H
        POP HL
RH_HEND:
        LD A,(HL)
        INC HL
        CP '$'
        JR NZ,RH_HEND
        POP DE
        POP BC
        EX DE,HL
        DJNZ RH_HLOOP
        RET
; Alternating common/command streams use one relocation for all four frames.
RH_IDPARTS: DB '  - - -',13,10,' | BetterCP/M Utilities',13,10,' | ','$'
            DB 13,10,'$'
RH_PARTS: DB '  - - -',13,10,' | ','$'
          DB 13,10,' |',13,10,' |   Usage: ','$'
          DB 13,10,13,10,'   Options:',13,10,'$'
          DB '     /H /HELP       Display this help.',13,10
          DB '     /VER           Display utility identification.',13,10
          DB 'For detailed help, see HELP ','$'

; Malformed option or missing operand: short syntax plus the common help hint.
; The gateway has restored DE to the command's identification/inline parts.
RH_BAD:
        LD DE,(RH_ACTIVE)
        JR RH_SHORT
RH_FILE:
        LD HL,(RH_ACTIVE)
        PUSH HL
        JR RH_SPRINT
RH_SHORT:
        PUSH DE
        LD DE,RH_BADMSG
RH_SPRINT:
        LD C,9
        CALL 00005H
        POP HL
        LD B,2
RH_SNEXT:
        LD A,(HL)
        INC HL
        CP '$'
        JR NZ,RH_SNEXT
        DJNZ RH_SNEXT
        EX DE,HL
        LD C,9
        CALL 00005H
        LD DE,RH_BADUSE
        LD C,9
        CALL 00005H
        CALL RH_NAME
        LD DE,RH_BADEND
        LD C,9
        JP 00005H
RH_BADMSG: DB 'Invalid usage.',13,10,'$'
RH_BADUSE: DB 13,10,'Use ','$'
RH_BADEND: DB ' /HELP for help.',13,10,'$'
RH_ACTIVE: DW 0
