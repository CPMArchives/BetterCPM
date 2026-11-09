; Screen layout belongs to HELP. All terminal operations use the admitted
; TCAP provider, while every printable character takes the normal console route.
navigation_break:
        LD A,(footer_row)
        OR A
        RET NZ
        JP newline

forget_status:
        LD HL,0
        LD (status_message),HL
        LD (status_detail),HL
        RET

leave_frame:
        LD A,(frame_started)
        OR A
        RET Z
        LD A,1
        CALL T2_EMIT                     ; leave the CCP a clean command line
        OR A
        RET Z
        JP newline

frame_row:
        LD B,A
        LD C,0
        LD A,2
frame_op:
        LD HL,frame_error
        BIT 0,(HL)
        RET NZ
        CALL T2_EMIT
        OR A
        RET Z
        LD A,1
        LD (frame_error),A
        OR A
        RET

draw_header:
        LD A,1
        CALL frame_op                    ; clear returns the cursor to (0,0)
        RET NZ
        LD A,1
        LD (frame_started),A
        LD (header_pass),A
        XOR A
        LD (heading_in_body),A
        LD A,(view_mode)
        CP 2
        LD HL,catalog_title
        JR Z,header_text
        OR A
        JR NZ,section_title
        LD HL,(title_ptr)
        INC HL
        INC HL
        JR header_text
section_title:
        LD HL,view_member
        LD A,(HL)
        OR A
        JR NZ,header_subject
        LD HL,view_file+2
header_subject:
        LD B,8
header_basename:
        LD A,(HL)
        CP ' '
        JR Z,header_dash
        CALL append_char
        INC HL
        DJNZ header_basename
header_dash:
        LD A,' '
        CALL append_char
        LD A,'-'
        CALL append_char
        LD A,' '
        CALL append_char
        LD HL,(view_section)
        INC HL
        INC HL
        INC HL
header_text:
        CALL inline_line
        CALL end_paragraph
        XOR A
        LD (header_pass),A
        RET
catalog_title: DB 'Help topics',0

; Use the normal Markdown formatter for a heading. Its first visible line
; is pinned. Repeat a wrapped heading in the body so all its text is readable.
header_line:
        CP 1
        JR Z,header_first
        LD (heading_in_body),A
        RET
header_first:
        LD A,2
        LD (header_pass),A
        LD A,128
        CALL set_style
        LD HL,line_buf
        LD A,(line_len)
        OR A
        JR Z,header_pad
        LD B,A
header_print:
        LD A,(HL)
        AND 127
        CALL putc
        INC HL
        DJNZ header_print
header_pad:
        LD A,(screen_ops)
        AND 8
        JR Z,header_normal
        LD A,(screen_cols)
        LD HL,line_len
        SUB (HL)
        JR Z,header_normal
        LD B,A
        LD A,' '
header_spaces:
        CALL putc
        DJNZ header_spaces
header_normal:
        XOR A
        JP set_style

; Keep the last column of the bottom row untouched: printing there can
; scroll terminals with immediate automatic margins. Report failures on
; this row alongside compact keys, without moving choices on the body page.
draw_footer:
        LD A,(footer_row)
        CALL frame_row
        RET NZ
        LD A,(screen_cols)
        DEC A
        LD (footer_left),A
        CP 38
        JR C,footer_compact
        LD HL,(status_message)
        LD A,H
        OR L
        JR Z,footer_mode
footer_compact:
        LD A,1
footer_mode:
        LD (compact_keys),A
        LD A,(visible_count)
        OR A
        JR Z,footer_previous
        LD B,A
        LD A,(compact_keys)
        OR A
        JR Z,footer_range
        LD A,B
        CP 11
        JR C,footer_range
        LD HL,any_key_text
        CALL footer_text
        JR footer_select
footer_range:
        LD A,B
        CP 27                           ; Q is always a command, never a choice
        JR C,footer_zero
        LD HL,before_r_text
        CALL footer_text
        LD A,B
        CP 27
        JR Z,footer_select
        JR footer_through
footer_zero:
        LD A,'0'
        CALL footer_char
        LD A,B
        CP 1
        JR Z,footer_select
footer_through:
        LD A,'-'
        CALL footer_char
        LD E,B
        LD D,0
        LD HL,choice_keys-1
        ADD HL,DE
        LD A,(HL)
        CALL footer_char
footer_select:
        LD HL,select_text
        CALL footer_label
        CALL footer_gap
footer_previous:
        LD HL,(view_page)
        LD A,H
        OR L
        JR Z,footer_next
        LD A,'<'
        CALL footer_char
        LD HL,prev_text
        CALL footer_label
        CALL footer_gap
footer_next:
        LD A,(more_pages)
        OR A
        JR Z,footer_quit
        LD A,'>'
        CALL footer_char
        LD HL,next_text
        CALL footer_label
        CALL footer_gap
footer_quit:
        LD A,'Q'
        CALL footer_char
        LD A,(depth)
        OR A
        LD HL,exit_text
        JR Z,footer_back
        LD HL,back_text
footer_back:
        CALL footer_label
        LD HL,(status_message)
        LD A,H
        OR L
        JR Z,footer_done
        PUSH HL
        CALL footer_gap
        POP HL
        CALL footer_text
        LD HL,status_detail
        CALL footer_text
footer_done:
        XOR A
        RET

footer_label:
        LD A,(compact_keys)
        OR A
        RET NZ
footer_text:
        LD A,(HL)
        CP ' '                           ; status strings can end in CR/LF
        RET C
        CALL footer_char
        INC HL
        JR footer_text
footer_gap:
        LD A,' '
        CALL footer_char
        LD A,(compact_keys)
        OR A
        RET NZ
        LD A,' '
footer_char:
        LD C,A
        LD A,(footer_left)
        OR A
        RET Z
        DEC A
        LD (footer_left),A
        LD A,C
        JP putc
any_key_text: DB 'Key',0
before_r_text: DB '0-P,R',0
select_text: DB ' Select',0
prev_text: DB ' Prev',0
next_text: DB ' Next',0
exit_text: DB ' Exit',0
back_text: DB ' Back',0
