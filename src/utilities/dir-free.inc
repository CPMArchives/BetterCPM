; Free space belongs to each current DU report; the BDOS allocation map is shared.
DX_FINISH:
        JP BC_DURST
DX_CURRENT:
        LD C,31
        CALL BDOS
        PUSH HL
        LD C,27
        CALL BDOS
        EX DE,HL
        POP HL
        CALL DF_COUNT
        LD HL,DF_VALUE
        LD DE,DTD_NUM
        LD BC,4
        LDIR
        CALL DTD_DEC
        LD DE,DX_MESSAGE
        JP BC_PRINT
DX_MESSAGE: DB 'K FREE$'
