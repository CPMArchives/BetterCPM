; PIP's RO-replacement approval only. Command/HEX/device input is unchanged.
; Keep exactly one cooked BDOS 1 read and historical AND DF uppercase folding.
; Only Y/y approves; every other byte declines without retry or a new alias.
PU_KEY:
        LD C,1
        CALL 5
        AND 0DFH
        RET
; @confirmation@
