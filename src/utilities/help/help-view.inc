; Each frame records the user's exact file, member, section and page.
screen_init:
        LD A,80
        LD (screen_cols),A
        LD A,22
        LD (page_rows),A
        CALL T2_OPEN
        OR A
        JR NZ,screen_grid
        LD DE,4
        ADD HL,DE
        LD B,0
        LD A,(HL)
        CP 3
        JR C,screen_width
        DEC A
        LD B,A                          ; zero-based last row
        DEC A
        LD (page_rows),A
screen_width:
        INC HL
        LD A,(HL)
        OR A
        JR Z,screen_caps
        LD (screen_cols),A
screen_caps:
        LD C,(HL)                       ; actual columns, zero if unknown
        INC HL
        LD A,(HL)
        LD (screen_ops),A
        AND 3                           ; clear and absolute positioning
        CP 3
        JR NZ,screen_grid
        LD A,C
        CP 12                           ; room for the compact key legend
        JR C,screen_grid
        LD A,B
        LD (footer_row),A
screen_grid:
        LD A,(screen_cols)
        LD B,0
screen_slot:
        INC B
        SUB 20
        JR NC,screen_slot
        DEC B
        JR NZ,screen_slot_ok
        INC B
screen_slot_ok:
        LD A,B
        CP 5
        JR C,screen_grid_done
        LD A,4
screen_grid_done:
        LD (grid_cols),A
        RET

enter_view:
        CALL open_view
        JP C,view_error
        LD A,(view_mode)
        CP 2
        JR NZ,enter_topic
        CALL load_catalog
        JP C,view_error
        CALL close_file
        JP C,view_error
        LD HL,arena
        LD DE,(data_end)
        OR A
        SBC HL,DE
        JP NZ,show_view
        LD HL,empty_archive
        JP print_exit
enter_topic:
        CALL load_topic
        JP C,view_error
        CALL close_file
        JP C,view_error
        CALL index_topic
        JP C,view_error
        LD A,(section_arg)
        OR A
        JR NZ,requested_section
        LD A,(view_mode)
        CP 1
        JP NZ,show_view
        ; Parent text is re-read after a link. Removable media may have
        ; changed. Only reuse a saved position that is still a real heading.
        LD HL,(first_section)
restore_section:
        LD A,(HL)
        OR A
        JR Z,restore_home
        LD DE,(view_section)
        OR A
        SBC HL,DE
        ADD HL,DE
        JR Z,show_view
        CALL next_line
        CALL next_section
        JR restore_section
restore_home:
        XOR A
        LD (view_mode),A
        LD HL,0
        LD (view_page),HL
        JR show_view
requested_section:
        CALL find_section
        JR NC,section_found
        CP AS_DUPLICATE
        LD HL,section_missing
        JR NZ,section_diagnostic
        LD HL,section_ambiguous
section_diagnostic:
        LD (status_message),HL
        LD HL,section_arg
        LD DE,status_detail
        LD BC,128
        LDIR
        XOR A
        LD (section_arg),A
        LD A,(depth)
        OR A
        JP NZ,go_back
        JR show_view
section_found:
        LD (view_section),HL
        LD A,1
        LD (view_mode),A
        XOR A
        LD (section_arg),A
show_view:
        CALL draw_page
        LD A,(frame_error)
        OR A
        JR NZ,stream_redraw
        LD HL,(current_page)
        LD DE,(view_page)
        OR A
        SBC HL,DE
        JR NC,view_status
        ; A returned-to source may now have fewer pages.
        LD HL,(current_page)
        LD (view_page),HL
        JR show_view
view_status:
        LD A,(footer_row)
        OR A
        JR Z,stream_status
        CALL draw_footer
        JR NZ,stream_redraw
        CALL forget_status
        JR wait_key
stream_redraw:
        XOR A
        LD (footer_row),A
        LD (frame_error),A
        LD (frame_started),A
        CALL newline
        JR show_view
stream_status:
        LD HL,(status_message)
        LD A,H
        OR L
        JR Z,view_prompt
        CALL puts
        LD HL,status_detail
        LD A,(HL)
        OR A
        JR Z,view_status_done
        CALL puts
        CALL newline
view_status_done:
        CALL forget_status
view_prompt:
        LD HL,prompt
        CALL puts
wait_key:
        LD E,0FFH
        LD C,6
        CALL BDOS
        OR A
        JR Z,wait_key
        CALL upper
        CP 3
        JR Z,go_back
        CP 'Q'
        JR Z,go_back
        CP ','
        JR Z,page_prev
        CP '<'
        JR Z,page_prev
        CP '.'
        JR Z,page_next
        CP '>'
        JR Z,page_next
        LD HL,choice_keys
        LD B,35
        LD C,0
key_scan:
        CP (HL)
        JR Z,key_hit
        INC HL
        INC C
        DJNZ key_scan
        JR wait_key
key_hit:
        LD A,(visible_count)
        CP C
        JR Z,wait_key
        JR C,wait_key
        LD B,0
        LD HL,choice_map
        ADD HL,BC
        ADD HL,BC
        ADD HL,BC
        LD A,(HL)
        INC HL
        LD E,(HL)
        INC HL
        LD D,(HL)
        EX DE,HL
        PUSH AF
        PUSH HL
        CALL navigation_break
        CALL push_view
        POP HL
        POP BC
        JR C,too_deep
        LD A,B
        CP 1
        JP Z,open_section
        CP 2
        JP Z,open_link
        JP open_catalog_choice
page_prev:
        LD HL,(view_page)
        LD A,H
        OR L
        JR Z,wait_key
        DEC HL
        JR page_change
page_next:
        LD A,(more_pages)
        OR A
        JR Z,wait_key
        LD HL,(view_page)
        INC HL
page_change:
        LD (view_page),HL
        CALL navigation_break
        JP show_view
go_back:
        LD A,(depth)
        OR A
        JR Z,leave_reader
        CALL navigation_break
        CALL pop_view
        JP enter_view
leave_reader:
        CALL navigation_break
        CALL leave_frame
        JP finish
too_deep:
        LD HL,depth_message
        LD (status_message),HL
        JP show_view
push_view:
        LD A,(depth)
        CP 16
        CCF
        RET C
        CALL frame_pointer
        EX DE,HL
        LD HL,view_start
        LD BC,frame_size
        LDIR
        LD HL,depth
        INC (HL)
        OR A
        RET
pop_view:
        LD HL,depth
        DEC (HL)
        LD A,(HL)
        CALL frame_pointer
        LD DE,view_start
        LD BC,frame_size
        LDIR
        RET
frame_pointer:
        LD HL,view_stack
        OR A
        RET Z
        LD B,A
        LD DE,frame_size
frame_seek:
        ADD HL,DE
        DJNZ frame_seek
        RET
open_section:
        LD (view_section),HL
        LD A,1
        LD (view_mode),A
        LD HL,0
        LD (view_page),HL
        JP show_view
open_catalog_choice:
        LD DE,requested
        LD BC,8
        LDIR
        LD HL,view_file
        CALL copy_candidate
        CALL open_archive
        CALL NC,find_member
        JR navigate_result
open_link:
        PUSH HL
        LD DE,link_target_name
        LD B,127
save_link_target:
        LD A,(HL)
        CP ')'
        JR Z,link_target_saved
        LD (DE),A
        INC HL
        INC DE
        DJNZ save_link_target
link_target_saved:
        XOR A
        LD (DE),A
        POP HL
        CALL parse_link_target
        JR C,link_bad
        LD HL,link_base
        LD DE,requested
        LD BC,8
        LDIR
        LD HL,link_section
        LD DE,section_arg
        LD BC,129
        LDIR
        LD A,1
        LD (fragment_mode),A
        LD A,(view_member)
        OR A
        JR Z,link_default
        LD HL,view_file
        CALL copy_candidate
        CALL open_archive
        JR C,navigate_result
        CALL find_member
        JR NC,navigate_result
        CP AS_END
        JR NZ,link_error
        LD A,(archive_lock)
        OR A
        JR NZ,link_bad
link_default:
        XOR A
        LD (lookup_kind),A
        CALL search_defaults
navigate_result:
        JP NC,enter_view
link_error:
        CP AS_END
        JR NZ,view_error_carry
link_bad:
        LD HL,link_target_name
        LD DE,status_detail
        LD BC,128
        LDIR
        LD HL,link_message
        LD (status_message),HL
        JR recover_view
view_error:
        CP AS_END
        JR NZ,view_error_carry
        LD HL,source_gone
        LD A,(depth)
        OR A
        JP Z,print_exit
        JR view_message
view_error_carry:
        LD B,A
        LD A,(depth)
        OR A
        LD A,B
        JP Z,read_failure
        CP AS_RANGE
        LD HL,memory_message
        JR Z,view_message
        LD HL,damage_message
view_message:
        LD (status_message),HL
recover_view:
        LD A,(depth)
        OR A
        JP Z,finish
        XOR A
        LD (section_arg),A
        CALL pop_view
        JP enter_view

; Parse a Markdown destination into private scratch. Rendering and selection
; use the same grammar without changing the active request during a redraw.
parse_link_target:
        XOR A
        LD (link_section),A
        LD DE,link_base
        LD B,8
        LD A,' '
link_pad:
        LD (DE),A
        INC DE
        DJNZ link_pad
        PUSH HL
        LD B,0
link_name_len:
        LD A,(HL)
        CP '.'
        JR Z,link_name_end
        INC B
        LD A,B
        CP 9
        JR NC,bad_link_pop
        LD A,(HL)
        CP 33
        JR C,bad_link_pop
        CP ')'
        JR Z,bad_link_pop
        INC HL
        JR link_name_len
link_name_end:
        POP HL
        LD DE,link_base
        CALL read_basename
        RET C
        INC HL
        LD DE,link_ext
        LD B,3
link_ext_next:
        LD A,(HL)
        CALL upper
        LD C,A
        LD A,(DE)
        CP C
        JR NZ,bad_link
        INC HL
        INC DE
        DJNZ link_ext_next
        LD A,(HL)
        CP ')'
        JR Z,link_parsed
        CP '#'
        JR NZ,bad_link
        INC HL
        LD DE,link_section
        LD B,127
fragment_next:
        LD A,(HL)
        CP ')'
        JR Z,fragment_end
        CP 33
        JR C,bad_link
        CALL upper
        LD (DE),A
        INC DE
        INC HL
        DJNZ fragment_next
bad_link:
        SCF
        RET
bad_link_pop:
        POP HL
        JR bad_link
fragment_end:
        XOR A
        LD (DE),A
        LD A,(link_section)
        OR A
        JR Z,bad_link
link_parsed:
        OR A
        RET
link_ext: DB 'HLP'
empty_archive: DB 'No help topics in this archive.',13,10,0
section_missing: DB 'No such section: ',0
section_ambiguous: DB 'Ambiguous section: ',0
link_message: DB 'Link not found: ',0
source_gone: DB 'Selected help source or member was not found.',13,10,0
depth_message: DB 'HELP: Navigation history is full.',13,10,0
prompt: DB 'Choice (< > Q): ',0
choice_keys: DB '0123456789ABCDEFGHIJKLMNOPRSTUVWXYZ'
