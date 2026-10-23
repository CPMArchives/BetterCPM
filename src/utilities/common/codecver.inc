; Compression command /VER entry. Emit once outside execution fall-through.
; Startup establishes the private stack first. The low 128 stack bytes are
; scratch for the bounded tail; the query uses the upper half. Normalize TAB
; separators in this copy only, preserving the original command tail.
; CF=handled, BC/DE/HL preserved. Caller restores entry SP and RETs when handled.
; Banner/query markers are expanded from authoritative metadata and
; common version.inc by tools/codec_version.py. No filesystem/drive calls.
CODEC_VERSION_CODE MACRO
UC_VERSION:
        PUSH BC
        PUSH DE
        PUSH HL
        LD A,(80H)
        CP 128
        JR NC,UC_VERSION_NONE
        OR A
        JR Z,UC_VERSION_NONE
        LD B,A
        LD HL,81H
        LD DE,UC_STACK
UC_VERSION_COPY:
        LD A,(HL)
        CP 9
        JR NZ,UC_VERSION_CONTROL
        LD A,' '
UC_VERSION_CONTROL:
        ; The shared case-fold matcher must not treat control 0Fh as '/'.
        ; Other controls remain invalid tokens; normal parsing sees originals.
        CP 20H
        JR NC,UC_VERSION_BYTE
        LD A,0FFH
UC_VERSION_BYTE:
        LD (DE),A
        INC HL
        INC DE
        DJNZ UC_VERSION_COPY
        LD HL,UC_STACK
        LD A,(80H)
        LD B,A
        LD DE,UC_VERSION_TEXT
        PUSH IX
        PUSH IY
        CALL UV_QUERY
        POP IY
        POP IX
        POP HL
        POP DE
        POP BC
        RET
UC_VERSION_NONE:
        POP HL
        POP DE
        POP BC
        OR A
        RET
; @codec-version-text@
; @codec-version-query@
        ENDM
