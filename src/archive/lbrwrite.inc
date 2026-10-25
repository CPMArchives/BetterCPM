; LBR staged writer ABI 1. Definitions only. Include archive.inc first.
; IX=caller-owned initialized LW_SIZE bytes; IY/alternate banks/SP preserved.
; AF/BC/DE/HL scratch; NC success, C/A AS_* result. Non-reentrant per context.
; Caller supplies a structurally/integrity-audited immutable original, or NEW.
; No file publication, console, timestamps, protection or filesystem allocation
; inside this library. All raw format manipulation belongs here, not the CLI.
;
; IO callback: IX unchanged, A=0 original read, 1 source read, 2 staged read,
; 3 staged write. LW_IOREC is a 24-bit absolute 128-byte record number;
; LW_IOBUF points at exactly 128 accessible bytes. LW_SOURCE identifies the
; source identity/plan row for operation 1. Set LW_ACTUAL=128 on success.
; C/A explicit error, NC short transfer is AS_TRUNC, never implicit EOF.
; Callback preserves IX/IY/alternate banks/SP, other registers scratch.
; Callback must detect source open/close errors and restore caller ownership.
;
; Configuration: ABI, IO, BUFF/AUX/FIRST (three disjoint 128-byte buffers),
; ENTRY/HEADER (two 32-byte records), IDS (COUNT x 13 DU/name identities),
; PLANS (COUNT x LP_SIZE), PATTERN (11 bytes), OLDREC (24-bit record count),
; CAP (32-bit explicit ordinary capacity), FLAGS. All ranges nonwrapping and
; disjoint from context/code/stack. Caller initializes all state to zero.
; COUNT<=512. Plan status 0 skipped, 1 accepted active, 2 displaced accepted.
; Each plan retains physical source records, CRC16 and independent CRC32 state.
; Source lengths are full CP/M records, never Ctrl-Z trimmed.
;
; LW_DISCOVER: snapshot header/count original entries. LW_FIND: ENTRY+1 canonical
; name -> A=0 no old match, A=1 match (ENTRY then contains original raw entry).
; LW_PLAN: choose preservation/rebuild and directory capacity; no output I/O.
; LW_RUN: VERIFY=0 construct; VERIFY=1 replay intended bytes and compare staged
; readback. Between calls close/reopen staged output. Same sources/original and
; accepted plan must remain stable; errors forbid publication.
; LW_HASH_BEGIN/RECORD: caller scratch digest/CRC16 over BUFF, full 128 bytes.
; CRC32 is ISO-HDLC internal state (initial FFFFFFFF, final xor not applied).
; LW_DIGEST / LW_CRC are caller-visible results; no stage-vs-itself verification.
; Stack: bounded loops, no recursion; caller budgets callback/OS stack too.
LW_ABI EQU 0
LW_FLAGS EQU 1
LW_IO EQU 2
LW_COUNT EQU 4
LW_IDS EQU 6
LW_PLANS EQU 8
LW_BUFF EQU 10
LW_AUX EQU 12
LW_FIRST EQU 14
LW_ENTRY EQU 16
LW_HEADER EQU 18
LW_PATTERN EQU 20
LW_OLDREC EQU 22
LW_OLDDIR EQU 25
LW_DIRECTORY EQU 27
LW_CAP EQU 29
LW_OCCUPIED EQU 33
LW_KEEP EQU 37
LW_ACCEPTED EQU 41
LW_ACTIVE EQU 45
LW_MATCHED EQU 49
LW_CAPACITY EQU 53
LW_SOURCE EQU 57
LW_SCANREC EQU 59
LW_SLOT EQU 61
LW_DATAREC EQU 62
LW_OUTREC EQU 65
LW_IOREC EQU 68
LW_IOBUF EQU 71
LW_ACTUAL EQU 73
LW_VERIFY EQU 75
LW_DIRCRC EQU 76
LW_DIGEST EQU 78
LW_CRC EQU 82
LW_PHASE EQU 84
LW_ROW EQU 85
LW_LEFT EQU 86
LW_POSITION EQU 89
LW_ORIGHASH EQU 92
LW_SOURCEHASH EQU 96
LW_TEMP EQU 100
LW_SIZE EQU 104
LF_NEW EQU 1
LF_COMPACT EQU 2
LF_REMOVE EQU 4
LF_CAP EQU 8
LF_REBUILD EQU 16
LP_STATUS EQU 0
LP_RECORDS EQU 1
LP_CRC EQU 3
LP_DIGEST EQU 5
LP_SIZE EQU 12
LW_GET MACRO FIELD
 LD L,(IX+FIELD)
 LD H,(IX+FIELD+1)
 ENDM
LW_SET MACRO FIELD
 LD (IX+FIELD),L
 LD (IX+FIELD+1),H
 ENDM
