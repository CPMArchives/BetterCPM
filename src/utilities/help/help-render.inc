; HL points to a normalized source line. The terminator is LF or NUL.
next_line:
        LD A,(HL)
        OR A
        RET Z
        INC HL
        CP 10
        JR NZ,next_line
        RET
; A=0 prose, 1 title, 2 section, 3 local heading, 4 fence.
line_kind:
        PUSH HL
        LD A,(HL)
        CP 96
        JR Z,kind_fence
        LD B,0
kind_hash:
        LD A,(HL)
        CP '#'
        JR NZ,kind_space
        INC HL
        INC B
        LD A,B
        CP 4
        JR C,kind_hash
        JR kind_plain
kind_space:
        CP ' '
        JR NZ,kind_plain
        LD A,B
        JR kind_return
kind_fence:
        INC HL
        LD A,(HL)
        CP 96
        JR NZ,kind_plain
        INC HL
        LD A,(HL)
        CP 96
        JR NZ,kind_plain
        INC HL
        LD A,(HL)
        CP 10
        JR Z,kind_mark
        OR A
        JR Z,kind_mark
        LD DE,fence_text
        LD B,4
        CALL same_bytes
        JR NZ,kind_plain
        LD A,(HL)
        OR A
        JR Z,kind_mark
        CP 10
        JR NZ,kind_plain
kind_mark:
        LD A,4
        JR kind_return
kind_plain:
        XOR A
kind_return:
        POP HL
        RET
fence_text: DB 'text'

; Locate headings by scanning outside literal fences. Keep source addresses
; so long titles do not consume a fixed per-heading table.
index_topic:
        LD HL,arena
index_title:
        LD A,(HL)
        CP 10
        JR NZ,index_start
        INC HL
        JR index_title
index_start:
        LD (title_ptr),HL
        CALL line_kind
        CP 1
        JR NZ,invalid_topic
        CALL next_line
        LD (body_ptr),HL
        CALL next_section
        LD (first_section),HL
        OR A
        RET
invalid_topic:
        LD A,AS_FORMAT
        SCF
        RET
next_section:
        LD C,0
scan_heading:
        LD A,(HL)
        OR A
        RET Z
        PUSH BC
        CALL line_kind
        POP BC
        CP 4
        JR NZ,scan_candidate
        LD A,C
        XOR 1
        LD C,A
        JR scan_resume
scan_candidate:
        CP 2
        JR NZ,scan_resume
        LD A,C
        OR A
        RET Z
scan_resume:
        CALL next_line
        JR scan_heading
find_section:
        LD HL,0
        LD (section_hit),HL
        LD HL,(first_section)
find_next:
        LD A,(HL)
        OR A
        JR Z,section_scan_end
        PUSH HL
        INC HL
        INC HL
        INC HL
        CALL match_heading
        POP HL
        JR NZ,find_continue
        LD DE,(section_hit)
        LD A,D
        OR E
        JR NZ,ambiguous_heading
        LD (section_hit),HL
find_continue:
        CALL next_line
        CALL next_section
        JR find_next
section_scan_end:
        LD HL,(section_hit)
        LD A,H
        OR L
        RET NZ
        LD A,AS_END
        SCF
        RET
ambiguous_heading:
        LD A,AS_DUPLICATE
        SCF
        RET
; Full heading comparison. In fragments the whitespace separator is '-'.
match_heading:
        LD DE,section_arg
        LD C,0
match_leading:
        LD A,(HL)
        CP ' '
        JR Z,match_skip
        CP 9
        JR NZ,match_text
match_skip:
        INC HL
        JR match_leading
match_text:
        LD A,(HL)
        INC HL
        CP 10
        JR Z,match_end
        OR A
        JR Z,match_end
        CP ' '
        JR Z,match_gap
        CP 9
        JR Z,match_gap
        CP 96
        JR Z,match_text
        CP '*'
        JR NZ,match_symbol
        LD A,(HL)
        CP '*'
        LD A,'*'
        JR NZ,match_symbol
        INC HL
        JR match_text
match_gap:
        LD C,1
        JR match_text
match_symbol:
        LD B,A
        LD A,C
        OR A
        JR Z,match_char
        LD C,0
        LD A,(fragment_mode)
        OR A
        LD A,' '
        JR Z,match_sep
        LD A,'-'
match_sep:
        LD C,A
        LD A,(DE)
        CP C
        RET NZ
        LD C,0
        INC DE
match_char:
        LD A,B
        CALL upper
        LD B,A
        LD A,(DE)
        CP B
        RET NZ
        INC DE
        JR match_text
match_end:
        LD A,(DE)
        OR A
        RET

draw_page:
        XOR A
        LD (current_page),A
        LD (current_page+1),A
        LD (row_no),A
        LD (line_len),A
        LD (word_len),A
        LD (choice_count),A
        LD (visible_count),A
        LD (more_pages),A
        LD (grid_count),A
        LD (fenced),A
        LD (span_style),A
        LD (inline_code),A
        LD (need_space),A
        LD (indent),A
        CALL page_visibility
        LD A,(screen_ops)
        AND 1
        JR Z,draw_content
        LD A,1
        CALL T2_EMIT
draw_content:
        LD A,(view_mode)
        CP 2
        JP Z,draw_catalog
        CP 1
        JR Z,draw_section
        LD HL,(title_ptr)
        INC HL
        INC HL
        CALL inline_line
        CALL end_paragraph
        LD HL,(body_ptr)
        CALL render_part
        LD HL,(first_section)
        LD A,(HL)
        OR A
        RET Z
draw_sections:
        PUSH HL
        LD A,1
        CALL grid_item
        POP HL
        CALL next_line
        CALL next_section
        LD A,(HL)
        OR A
        JR NZ,draw_sections
        JP end_grid
draw_section:
        LD HL,(view_section)
        INC HL
        INC HL
        INC HL
        PUSH HL
        CALL inline_line
        CALL end_paragraph
        POP HL
        CALL next_line
        JP render_part
draw_catalog:
        LD HL,arena
catalog_row:
        LD DE,(data_end)
        OR A
        SBC HL,DE
        ADD HL,DE
        JP Z,end_grid
        PUSH HL
        LD A,3
        CALL grid_item
        POP HL
        LD DE,8
        ADD HL,DE
        JR catalog_row

; Render an overview or section body to the next Level 2 heading or EOF.
render_part:
        LD A,(HL)
        OR A
        JP Z,end_paragraph
        PUSH HL
        CALL line_kind
        CP 4
        JR Z,render_fence
        LD B,A
        LD A,(fenced)
        OR A
        JR NZ,render_literal
        LD A,B
        CP 2
        JR Z,render_end
        CP 3
        JR Z,render_subhead
        LD A,(HL)
        CP 10
        JR Z,render_blank
        CALL list_start
        CALL inline_line
        JR render_next
render_subhead:
        PUSH HL
        CALL end_paragraph
        POP HL
        INC HL
        INC HL
        INC HL
        INC HL
        CALL inline_line
        CALL end_paragraph
        JR render_next
render_blank:
        CALL end_paragraph
        CALL flush_line
        JR render_next
render_fence:
        CALL end_paragraph
        LD A,(fenced)
        XOR 1
        LD (fenced),A
        JR render_next
render_end:
        POP HL
        JP end_paragraph
render_literal:
        LD A,(HL)
        OR A
        JR Z,literal_eol
        CP 10
        JR Z,literal_eol
        INC HL
        CP 9
        JR NZ,literal_put
literal_tab:
        ; Tab stops restart at the left margin when a narrow line wraps.
        LD A,(line_len)
        AND 7
        LD B,A
        LD A,8
        SUB B
        LD B,A
literal_spaces:
        LD A,' '
        CALL append_char
        DJNZ literal_spaces
        JR render_literal
literal_put:
        CALL append_char
        JR render_literal
literal_eol:
        CALL flush_line
render_next:
        POP HL
        CALL next_line
        JP render_part

; A list marker begins a new paragraph. Hanging indent counts visible bytes.
list_start:
        PUSH HL
        CALL list_marker
        POP HL
        RET NZ
        PUSH HL
        CALL end_paragraph
        POP HL
list_mark:
        LD A,(HL)
        INC HL
        CP ' '
        JR Z,list_space
        CALL append_char
        JR list_mark
list_space:
        CALL append_char
        LD A,(line_len)
        LD (indent),A
        RET
list_marker:
        LD A,(HL)
        CP '-'
        JR Z,list_separator
        SUB '0'
        CP 10
        JR NC,list_absent
list_digit:
        INC HL
        LD A,(HL)
        SUB '0'
        CP 10
        JR C,list_digit
        LD A,(HL)
        CP '.'
        RET NZ
list_separator:
        INC HL
        LD A,(HL)
        CP ' '
        RET
list_absent:
        LD A,1
        OR A
        RET
end_paragraph:
        CALL word_flush
        LD A,(line_len)
        OR A
        CALL NZ,flush_line
        XOR A
        LD (indent),A
        LD (need_space),A
        LD (inline_code),A
        LD (span_style),A
        RET

inline_line:
        LD A,(HL)
        OR A
        JP Z,inline_eol
        CP 10
        JP Z,inline_eol
        CP 96
        JR Z,inline_tick
        LD B,A
        LD A,(inline_code)
        OR A
        LD A,B
        JR Z,inline_markup
        ; Inline literals retain repeated spaces; their bytes form a word.
        INC HL
        CP 9
        JR NZ,inline_literal
        LD A,' '
inline_literal:
        CALL word_add
        JR inline_line
inline_markup:
        CP '*'
        JR Z,inline_star
        CP '['
        JP Z,inline_link
inline_normal:
        INC HL
        CP 9
        JR Z,inline_space
        CP ' '
        JR Z,inline_space
        CALL word_add
        JR inline_line
inline_space:
        PUSH HL
        CALL word_flush
        POP HL
        LD A,1
        LD (need_space),A
        JR inline_line
inline_tick:
        LD A,(inline_code)
        OR A
        JR NZ,inline_toggle_code
        LD C,96
        CALL closing_marker
        LD A,96
        JR NZ,inline_normal
        XOR A
inline_toggle_code:
        XOR 1
        LD (inline_code),A
        INC HL
        JR inline_line
inline_star:
        INC HL
        LD A,(HL)
        CP '*'
        JR Z,inline_strong
        LD A,'*'
        CALL word_add
        JR inline_line
inline_strong:
        INC HL
        LD A,(span_style)
        OR A
        JR NZ,inline_toggle_strong
        LD C,'*'
        DEC HL
        CALL closing_marker
        INC HL
        JR Z,inline_open_strong
        LD A,'*'
        CALL word_add
        LD A,'*'
        CALL word_add
        JP inline_line
inline_open_strong:
        XOR A
inline_toggle_strong:
        XOR 128
        LD (span_style),A
        JP inline_line
; HL = final byte of the opening delimiter. Consecutive physical prose
; lines form one paragraph. Do not borrow a closer from the next block.
closing_marker:
        PUSH HL
closing_scan:
        INC HL
        LD A,(HL)
        OR A
        JR Z,closing_absent
        CP 10
        JR Z,closing_line
        CP C
        JR NZ,closing_scan
        LD A,C
        CP 96
        JR Z,closing_done
        INC HL
        LD A,(HL)
        CP C
        JR Z,closing_done
        DEC HL
        JR closing_scan
closing_line:
        INC HL
        LD A,(HL)
        OR A
        JR Z,closing_absent
        CP 10
        JR Z,closing_absent
        PUSH BC
        CALL line_kind
        POP BC
        OR A
        JR NZ,closing_absent
        PUSH HL
        CALL list_marker
        POP HL
        JR Z,closing_absent
        DEC HL
        JR closing_scan
closing_absent:
        LD A,1
        OR A
closing_done:
        POP HL
        RET
inline_eol:
        CALL word_flush
        LD A,1
        LD (need_space),A
        RET
; Recognize only complete [label](target) pairs on this source line.
inline_link:
        PUSH HL
link_bracket:
        INC HL
        LD A,(HL)
        OR A
        JP Z,link_literal
        CP 10
        JP Z,link_literal
        CP ']'
        JR NZ,link_bracket
        LD (label_end),HL
        INC HL
        LD A,(HL)
        CP '('
        JP NZ,link_literal
        INC HL
        LD (link_ptr),HL
link_paren:
        LD A,(HL)
        OR A
        JP Z,link_literal
        CP 10
        JP Z,link_literal
        INC HL
        CP ')'
        JR NZ,link_paren
        LD (after_link),HL
        LD HL,(link_ptr)
        CALL parse_link_target
        JP C,link_literal
        CALL word_flush
        LD A,(line_len)
        ADD A,5
        LD HL,screen_cols
        CP (HL)
        CALL NC,flush_nonempty
        LD HL,(link_ptr)
        LD A,2
        CALL register_key
        PUSH AF
        LD A,'['
        CALL word_add
        POP AF
        CALL word_add
        LD A,']'
        CALL word_add
        CALL word_flush
        LD A,1
        LD (need_space),A
        POP HL
        INC HL
link_label:
        LD DE,(label_end)
        OR A
        SBC HL,DE
        ADD HL,DE
        JR Z,link_after
        LD A,(HL)
        INC HL
        CP ' '
        JR NZ,link_label_char
        PUSH HL
        CALL word_flush
        POP HL
        LD A,1
        LD (need_space),A
        JR link_label
link_label_char:
        CALL word_add
        JR link_label
link_after:
        LD HL,(after_link)
        JP inline_line
link_literal:
        POP HL
        INC HL
        LD A,'['
        CALL word_add
        JP inline_line

; Word wrapping uses one bounded word and one bounded screen line.
word_add:
        PUSH HL
        PUSH AF
        LD A,(word_len)
        CP 255
        CALL Z,word_flush
        LD A,(word_len)
        LD E,A
        LD D,0
        LD HL,word_buf
        ADD HL,DE
        POP AF
        LD E,A
        LD A,(span_style)
        OR E
        LD (HL),A
        LD HL,word_len
        INC (HL)
        POP HL
        RET
word_flush:
        LD A,(word_len)
        OR A
        RET Z
        LD B,A
        LD A,(line_len)
        OR A
        JR Z,word_indent
        LD C,A
        LD A,(need_space)
        ADD A,C
        JR C,word_wrap
        ADD A,B
        JR C,word_wrap
        LD C,A
        LD A,(screen_cols)
        CP C
        JR C,word_wrap
        LD A,(need_space)
        OR A
        JR Z,word_copy
        LD A,' '
        CALL append_char
        JR word_copy
word_wrap:
        CALL flush_line
word_indent:
        LD A,(indent)
        OR A
        JR Z,word_copy
        LD B,A
        LD A,' '
word_pad:
        CALL append_char
        DJNZ word_pad
word_copy:
        LD A,(word_len)
        LD B,A
        LD HL,word_buf
word_chars:
        LD A,(HL)
        INC HL
        CALL append_char
        DJNZ word_chars
        XOR A
        LD (word_len),A
        LD (need_space),A
        RET
append_char:
        PUSH HL
        PUSH DE
        PUSH BC
        PUSH AF
        LD A,(line_len)
        LD HL,screen_cols
        CP (HL)
        CALL NC,flush_line
        LD A,(line_len)
        LD E,A
        LD D,0
        LD HL,line_buf
        ADD HL,DE
        POP AF
        LD (HL),A
        LD HL,line_len
        INC (HL)
        POP BC
        POP DE
        POP HL
        RET
flush_nonempty:
        LD A,(line_len)
        OR A
        RET Z
flush_line:
        PUSH HL
        PUSH DE
        PUSH BC
        CALL ensure_page
        LD A,(visible)
        OR A
        JR Z,flush_count
        LD HL,line_buf
        LD A,(line_len)
        OR A
        JR Z,flush_eol
        LD B,A
flush_char:
        LD A,(HL)
        AND 128
        CALL set_style
        LD A,(HL)
        AND 127
        CALL putc
        INC HL
        DJNZ flush_char
        XOR A
        CALL set_style
flush_eol:
        CALL newline
flush_count:
        LD HL,row_no
        INC (HL)
        XOR A
        LD (line_len),A
        POP BC
        POP DE
        POP HL
        RET
set_style:
        LD C,A
        LD A,(display_style)
        CP C
        RET Z
        LD A,C
        LD (display_style),A
        LD A,(screen_ops)
        AND 8
        RET Z
        PUSH BC
        PUSH DE
        PUSH HL
        LD A,C
        OR A
        LD A,5
        JR Z,emit_style
        DEC A
emit_style:
        CALL T2_EMIT
        POP HL
        POP DE
        POP BC
        RET
ensure_page:
        LD A,(row_no)
        LD HL,page_rows
        CP (HL)
        RET C
advance_page:
        XOR A
        LD (row_no),A
        LD (choice_count),A
        LD HL,(current_page)
        INC HL
        LD (current_page),HL
page_visibility:
        LD HL,(current_page)
        LD DE,(view_page)
        OR A
        SBC HL,DE
        LD A,0
        JR C,page_set
        JR Z,page_active
        INC A
        LD (more_pages),A
        XOR A
        JR page_set
page_active:
        INC A
page_set:
        LD (visible),A
        RET
; A=kind, HL=target. Return the printable key for this page.
register_key:
        PUSH AF
        PUSH HL
        CALL ensure_page
        LD A,(choice_count)
        CP 35
        JR C,register_room
        CALL flush_nonempty
        CALL advance_page
register_room:
        LD A,(choice_count)
        LD E,A
        LD D,0
        INC A
        LD (choice_count),A
        LD A,(visible)
        OR A
        JR Z,register_hidden
        LD A,(choice_count)
        LD (visible_count),A
        LD HL,choice_map
        ADD HL,DE
        ADD HL,DE
        ADD HL,DE
        POP BC
        POP AF
        LD (HL),A
        INC HL
        LD (HL),C
        INC HL
        LD (HL),B
        JR register_key_char
register_hidden:
        POP HL
        POP AF
register_key_char:
        LD HL,choice_keys
        ADD HL,DE
        LD A,(HL)
        RET

; Grid slots begin at fixed 20-column intervals. Never pad the final slot.
grid_item:
        LD (grid_kind),A
        LD (grid_ptr),HL
        LD A,(choice_count)
        CP 35
        CALL Z,end_grid
        LD A,(grid_count)
        OR A
        JR Z,grid_key
        LD B,A
        XOR A
grid_mul:
        ADD A,20
        DJNZ grid_mul
        LD C,A
grid_pad:
        LD A,(line_len)
        CP C
        JR NC,grid_key
        LD A,' '
        CALL append_char
        JR grid_pad
grid_key:
        LD HL,(grid_ptr)
        LD A,(grid_kind)
        CALL register_key
        CALL append_char
        LD A,(grid_kind)
        CP 3
        LD A,' '
        JR NZ,grid_sep
        LD A,'.'
grid_sep:
        CALL append_char
        LD A,' '
        CALL append_char
        LD HL,(grid_ptr)
        LD A,(grid_kind)
        CP 3
        JR NZ,grid_heading
        LD B,8
grid_name:
        LD A,(HL)
        CP ' '
        JR Z,grid_done
        INC HL
        CALL append_char
        DJNZ grid_name
        JR grid_done
grid_heading:
        INC HL
        INC HL
        INC HL
        LD B,16
grid_text:
        LD A,(HL)
        INC HL
        OR A
        JR Z,grid_done
        CP 10
        JR Z,grid_done
        CP 96
        JR Z,grid_text
        CP '*'
        JR NZ,grid_print
        LD A,(HL)
        CP '*'
        LD A,'*'
        JR NZ,grid_print
        INC HL
        JR grid_text
grid_print:
        CALL append_char
        DJNZ grid_text
grid_done:
        LD HL,grid_count
        INC (HL)
        LD A,(grid_cols)
        CP (HL)
        RET NZ
end_grid:
        XOR A
        LD (grid_count),A
        JP flush_nonempty
