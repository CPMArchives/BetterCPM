; Work on a bounded private copy. Help queries have already been handled.
read_args:
        LD HL,requested
        LD B,8
        LD A,' '
args_blank:
        LD (HL),A
        INC HL
        DJNZ args_blank
        LD HL,section_arg
        LD (section_write),HL
        LD A,(80H)
        CP 128
        CCF
        RET C
        LD B,A
        LD HL,81H
        LD DE,tail_buf
        OR A
        JR Z,args_copied
args_copy:
        LD A,(HL)
        CP 9
        JR NZ,args_graphic
        LD A,' '
args_graphic:
        CP ' '
        JR C,args_bad
        CALL upper
        LD (DE),A
        INC DE
        INC HL
        DJNZ args_copy
args_copied:
        XOR A
        LD (DE),A
        LD HL,tail_buf
args_next:
        LD A,(HL)
        OR A
        JP Z,args_done
        INC HL
        CP ' '
        JR Z,args_next
        DEC HL
        PUSH HL
args_boundary:
        LD A,(HL)
        OR A
        JR Z,args_cut
        INC HL
        CP ' '
        JR NZ,args_boundary
        DEC HL
args_cut:
        LD (HL),0
        INC HL
        EX (SP),HL
        CALL parse_token
        POP HL
        RET C
        JR args_next
args_bad:
        SCF
        RET
parse_token:
        LD A,(HL)
        CP '/'
        JR NZ,args_operand
        INC HL
        PUSH HL
        LD DE,opt_report
        CALL token_match
        POP HL
        JR Z,args_report
        PUSH HL
        LD DE,opt_r
        CALL token_match
        POP HL
        JR Z,args_report
        LD DE,opt_source
        PUSH HL
        CALL prefix_match
        JR Z,args_source
        POP HL
        PUSH HL
        LD DE,opt_s
        CALL prefix_match
        JR NZ,args_unknown
args_source:
        POP DE
        LD A,(explicit_file)
        OR A
        JR NZ,args_bad
        INC A
        LD (explicit_file),A
        JP parse_source
args_unknown:
        POP HL
        JR args_bad
args_report:
        LD A,1
        LD (report_only),A
        OR A
        RET
args_operand:
        LD A,(requested)
        CP ' '
        JR NZ,args_section
        CALL strlen
        LD DE,requested
        JP read_basename
args_section:
        LD DE,(section_write)
        LD A,(section_arg)
        OR A
        JR Z,args_append
        LD A,' '
        LD (DE),A
        INC DE
args_append:
        LD A,(HL)
        LD (DE),A
        OR A
        JR Z,args_appended
        INC HL
        INC DE
        JR args_append
args_appended:
        LD (section_write),DE
        RET
args_done:
        LD A,(explicit_file)
        OR A
        JR Z,args_need_topic
        LD HL,source_spec+10
        CALL encoding
        CP 3
        JR NC,args_lock
        LD HL,source_spec+2
        LD DE,requested
        LD A,(DE)
        CP ' '
        JR NZ,args_assert_topic
        LD BC,8
        LDIR
        JR args_need_topic
args_assert_topic:
        LD B,8
        CALL same_bytes
        JP NZ,args_bad
        JR args_need_topic
args_lock:
        LD A,1
        LD (archive_lock),A
args_need_topic:
        LD A,(report_only)
        OR A
        RET Z
        LD A,(requested)
        CP ' '
        JP Z,args_bad
        OR A
        RET
token_match:
        CALL prefix_match
        RET NZ
        LD A,(HL)
        OR A
        RET
prefix_match:
        LD A,(DE)
        OR A
        RET Z
        CP (HL)
        RET NZ
        INC DE
        INC HL
        JR prefix_match
opt_report: DB 'REPORT',0
opt_r: DB 'R',0
opt_source: DB 'SOURCE=',0
opt_s: DB 'S=',0

; HL/B exact basename, DE -> already space-padded output.
read_basename:
        LD A,B
        OR A
        JR Z,name_bad
        CP 9
        JR NC,name_bad
        PUSH HL
        PUSH BC
        PUSH DE
        XOR A
        CALL FP_VALIDATE
        POP DE
        POP BC
        POP HL
        RET C
name_loop:
        LD A,(HL)
        CP '.'
        JR Z,name_bad
        CALL upper
        LD (DE),A
        INC DE
        INC HL
        DJNZ name_loop
        OR A
        RET
name_bad:
        SCF
        RET
parse_source:
        CALL strlen
        ; Named directories use the system's resolver. Numeric prefixes use
        ; the shared DU grammar and must identify exactly one drive/user.
        CALL CN_PREFIX
        JR C,source_du
        LD A,(home_drive)
        DEC A
        LD D,A
        LD A,(home_user)
        LD E,A
        CALL DU_PARSE
        RET C
        PUSH HL
        PUSH BC
        LD BC,0
        CALL DU_NEXT
        JR C,source_bad_du
        PUSH DE
        CALL DU_NEXT
        POP DE
        JR NC,source_bad_du
        POP BC
        POP HL
        INC D
source_du:
        LD A,D
        LD (source_spec),A
        LD A,E
        LD (source_spec+1),A
        PUSH HL
        PUSH BC
        XOR A
        CALL FP_VALIDATE
        POP BC
        POP HL
        RET C
        LD DE,source_spec+2
        PUSH HL
        LD HL,source_spec+2
        LD B,11
        LD A,' '
source_pad:
        LD (HL),A
        INC HL
        DJNZ source_pad
        POP HL
source_base:
        LD A,(HL)
        OR A
        JR Z,name_bad
        INC HL
        CP '.'
        JR Z,source_ext
        LD (DE),A
        INC DE
        JR source_base
source_ext:
        CALL strlen
        LD A,B
        CP 3
        JR NZ,name_bad
        LD DE,source_spec+10
        LD BC,3
        LDIR
        LD HL,source_spec+10
        CALL encoding
        CP 5
        JR NC,name_bad
        OR A
        RET
source_bad_du:
        POP BC
        POP HL
        SCF
        RET
; A = index in the encoding table, 5 for another extension. HL preserved.
encoding:
        LD DE,extensions
        LD C,0
encoding_next:
        PUSH HL
        PUSH DE
        LD B,3
        CALL same_bytes
        POP DE
        POP HL
        JR Z,encoding_found
        INC DE
        INC DE
        INC DE
        INC C
        LD A,C
        CP 5
        JR C,encoding_next
encoding_found:
        LD A,C
        RET

; Snapshot the resolved effective PATH once, starting with the caller DU.
init_path:
        LD A,(home_drive)
        LD D,A
        LD A,(home_user)
        LD E,A
        CALL append_du
        LD HL,layout_table
path_layout:
        LD E,(HL)
        INC HL
        LD D,(HL)
        INC HL
        LD A,D
        OR E
        JR Z,path_default
        PUSH HL
        LD HL,(1)
        OR A
        SBC HL,DE
        POP HL
        JR Z,path_check
        LD DE,4
        ADD HL,DE
        JR path_layout
path_check:
        LD E,(HL)
        INC HL
        LD D,(HL)
        INC HL
        PUSH HL
        EX DE,HL
        LD DE,path_signature
        LD B,3
        CALL same_bytes
        JR NZ,path_unknown
        BIT 2,(HL)
        JR Z,path_unknown
        POP HL
        LD E,(HL)
        INC HL
        LD D,(HL)
        EX DE,HL
        LD A,(HL)
        OR A
        JR Z,path_default
        CP 7
        JR C,path_read
        JR path_default
path_unknown:
        POP HL
path_default:
        LD HL,default_path
path_read:
        LD B,(HL)
        INC HL
path_entry:
        LD D,(HL)
        INC HL
        LD E,(HL)
        INC HL
        LD A,D
        OR A
        JR NZ,path_drive_ok
        LD A,(home_drive)
        LD D,A
path_drive_ok:
        LD A,E
        CP 255
        JR NZ,path_user_ok
        LD A,(home_user)
        LD E,A
path_user_ok:
        PUSH BC
        PUSH HL
        CALL append_du
        POP HL
        POP BC
        DJNZ path_entry
        RET
path_signature: DB 'BM',1
append_du:
        LD A,D
        DEC A
        CP 16
        RET NC
        LD A,E
        CP 32
        RET NC
        LD HL,path_list
        LD A,(path_count)
        OR A
        JR Z,path_add
        LD B,A
path_dup:
        LD A,(HL)
        INC HL
        CP D
        LD A,(HL)
        INC HL
        JR NZ,path_continue
        CP E
        RET Z
path_continue:
        DJNZ path_dup
path_add:
        LD (HL),D
        INC HL
        LD (HL),E
        LD HL,path_count
        INC (HL)
        RET
