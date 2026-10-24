; Standard single-handle CP/M adapter workspace at AS_USER.
; Caller zeroes workspace and builds AP_FCB (ordinary exact name/drive).
; AC_OPEN fills AS_FILE_SIZE and AS_READ, then calls LBR_OPEN.
; AC_CLOSE closes the FCB even after library failure. Caller owns lifetime.
; Archive owner user is captured on OPEN. READ/CLOSE switch to that user
; temporarily and restore the entry user even on failure; no drive changes.
; BDOS DMA becomes AP_DMA; caller restores its DMA.
; Public/callback registers follow archive.inc. Scratch is caller-owned.
AP_FCB          EQU 0
AP_DMA          EQU 48
AP_POSITION     EQU 36
AP_OUTPUT       EQU 40
AP_LEFT         EQU 42
AP_OPENED       EQU 44
AP_SKIP         EQU 45
AP_CHUNK        EQU 46
AP_OWNER        EQU 176
AP_RETURN_USER  EQU 177
AP_SIZE         EQU 178
