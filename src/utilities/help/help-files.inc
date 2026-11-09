; A candidate is the exact disk file under consideration. Restore the caller
; user after every open. The shared adapter owns later cross-user reads.
close_file:
        LD IX,context
        LD A,(adapter+AP_OPENED)
        OR A
        RET Z
        JP AC_CLOSE
open_candidate:
        CALL close_file
        RET C
        LD HL,adapter
        LD DE,adapter+1
        LD BC,AP_SIZE-1
        LD (HL),0
        LDIR
        LD A,(candidate)
        LD (adapter),A
        LD HL,candidate+2
        LD DE,adapter+1
        LD BC,11
        LDIR
        LD HL,adapter
        LD (context+AS_USER),HL
        LD HL,AS_CONTEXT_SIZE
        LD (context+AS_SIZE),HL
        LD A,1
        LD (context+AS_ABI),A
        LD A,(candidate+1)
        CALL select_user
        CALL AC_OPEN_RAW
        PUSH AF
        LD A,(home_user)
        CALL select_user
        POP AF
        RET NC
        LD A,AS_END
        SCF
        RET
open_archive:
        CALL open_candidate
        RET C
start_archive:
        LD HL,candidate+10
        CALL encoding
        LD (active_format),A
        CP 3
        JP Z,LBR_OPEN
        JP ARK_OPEN
next_member:
        LD IX,context
        LD A,(active_format)
        CP 3
        JP Z,LBR_NEXT
        JP ARK_NEXT
reset_path:
        XOR A
        LD (path_index),A
        RET
next_du:
        LD A,(path_index)
        LD HL,path_count
        CP (HL)
        JR NC,file_miss
        LD E,A
        INC A
        LD (path_index),A
        LD D,0
        LD HL,path_list
        ADD HL,DE
        ADD HL,DE
        LD DE,candidate
        LD BC,2
        LDIR
        OR A
        RET
file_miss:
        LD A,AS_END
        SCF
        RET
; HL -> padded archive filename. Stop at the first file of that name.
find_archive:
        LD DE,candidate+2
        LD BC,11
        LDIR
        CALL reset_path
archive_on_path:
        CALL next_du
        RET C
        CALL open_candidate
        JP NC,start_archive
        CP AS_END
        JR Z,archive_on_path
        SCF
        RET
find_loose:
        CALL reset_path
loose_du:
        CALL next_du
        RET C
        LD HL,requested
        LD DE,candidate+2
        LD BC,8
        LDIR
        LD HL,extensions
        LD B,3
loose_type:
        PUSH BC
        LD DE,candidate+10
        LD BC,3
        LDIR
        PUSH HL
        CALL open_candidate
        POP HL
        POP BC
        JP NC,choose_file
        CP AS_END
        JP NZ,member_error
        DJNZ loose_type
        JR loose_du
choose_file:
        XOR A
        LD (view_member),A
choose_source:
        LD HL,candidate
        LD DE,view_file
        LD BC,13
        LDIR
        XOR A
        LD (view_mode),A
        LD HL,0
        LD (view_section),HL
        LD (view_page),HL
        RET
; Choose the preferred encoding independent of member order. This is also
; the /REPORT path: selection only needs directory metadata.
find_member:
        LD A,3
        LD (best_rank),A
member_scan:
        CALL next_member
        JR C,member_scan_end
        LD HL,context+AS_MEMBER
        LD DE,requested
        LD B,8
        CALL same_bytes
        JR NZ,member_scan
        LD HL,context+AS_MEMBER+8
        CALL encoding
        LD HL,best_rank
        CP (HL)
        JR NC,member_scan
        LD (HL),A
        LD HL,context+AS_MEMBER
        LD DE,best_member
        LD BC,11
        LDIR
        OR A
        JR NZ,member_scan
        JR member_selected
member_scan_end:
        CP AS_END
        JP NZ,member_error
        LD A,(best_rank)
        CP 3
        JP Z,file_miss
member_selected:
        LD HL,best_member
        LD DE,view_member
        LD BC,11
        LDIR
        JP choose_source
member_error:
        SCF
        RET
; C on failure. Only AS_END is a lookup miss.
search_defaults:
        LD A,(lookup_kind)
        OR A
        JR NZ,default_lbr
        CALL find_loose
        RET NC
        CP AS_END
        JP NZ,member_error
default_lbr:
        LD HL,def_lbr
        CALL search_one
        RET NC
        CP AS_END
        JP NZ,member_error
        LD HL,def_ark
search_one:
        CALL find_archive
        RET C
        JP find_member
use_explicit:
        LD HL,source_spec
copy_candidate:
        LD DE,candidate
        LD BC,13
        LDIR
        RET
resolve_command:
        LD A,(explicit_file)
        OR A
        JR Z,command_default
        CALL use_explicit
        CALL open_candidate
        JR NC,command_exp_open
        CP AS_END
        JP NZ,member_error
        LD A,1
        LD (source_missing),A
        JP file_miss
command_exp_open:
        LD A,(archive_lock)
        OR A
        JP Z,choose_file
        CALL start_archive
        RET C
        LD A,(requested)
        CP ' '
        JR Z,archive_home
        CALL find_member
        JR command_fallback
command_default:
        LD A,(requested)
        CP ' '
        JR NZ,command_topic
        LD HL,def_lbr
        CALL find_archive
        JR NC,archive_home
        CP AS_END
        JP NZ,member_error
        LD HL,def_ark
        CALL find_archive
        RET C
archive_home:
        CALL set_index
        CALL find_member
        RET NC
        CP AS_END
        JP NZ,member_error
        CALL choose_file
        LD A,2
        LD (view_mode),A
        OR A
        RET
command_topic:
        CALL search_defaults
command_fallback:
        RET NC
        CP AS_END
        JP NZ,member_error
        LD A,(report_only)
        OR A
        JP NZ,file_miss
        LD HL,requested
        LD DE,original_request
        LD BC,8
        LDIR
        CALL set_index
        LD A,1
        LD (lookup_kind),A
        XOR A
        LD (section_arg),A
        LD A,(archive_lock)
        OR A
        JR Z,command_index_default
        CALL use_explicit
        CALL open_archive
        JR C,command_restore
        CALL find_member
        JR command_restore
command_index_default:
        CALL search_defaults
command_restore:
        PUSH AF
        LD HL,original_request
        LD DE,requested
        LD BC,8
        LDIR
        POP AF
        RET
set_index:
        LD HL,index_name
        LD DE,requested
        LD BC,8
        LDIR
        RET

; Reopen the exact identity captured on the navigation stack. This avoids
; retaining FCBs or decoded parent topics while following a link.
open_view:
        LD HL,view_file
        CALL copy_candidate
        LD A,(view_mode)
        CP 2
        JP Z,open_archive
        LD A,(view_member)
        OR A
        JP Z,open_candidate
        CALL open_archive
        RET C
seek_member:
        CALL next_member
        RET C
        LD HL,view_member
        LD DE,context+AS_MEMBER
        LD B,11
        CALL same_bytes
        JR NZ,seek_member
        OR A
        RET

; Generate a compact table of unique archive basenames in encounter order.
load_catalog:
        LD HL,arena
        LD (data_end),HL
catalog_next:
        CALL next_member
        JR C,catalog_end
        LD HL,context+AS_MEMBER+8
        CALL encoding
        CP 3
        JR NC,catalog_next
        LD HL,arena
catalog_check:
        LD DE,(data_end)
        OR A
        SBC HL,DE
        ADD HL,DE
        JR Z,catalog_add
        PUSH HL
        LD DE,context+AS_MEMBER
        LD B,8
        CALL same_bytes
        POP HL
        JR Z,catalog_next
        LD DE,8
        ADD HL,DE
        JR catalog_check
catalog_add:
        PUSH HL
        LD DE,8
        ADD HL,DE
        CALL check_room
        POP DE
        RET C
        LD HL,context+AS_MEMBER
        LD BC,8
        LDIR
        LD (data_end),DE
        JR catalog_next
catalog_end:
        CP AS_END
        JP NZ,member_error
        OR A
        RET
