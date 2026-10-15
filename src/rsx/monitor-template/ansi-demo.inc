; MONDEMO sample grammar: ordinary ASCII plus FF and ESC H/J/K/A/B/C/D.
; Replace byte strings/counts for your host, or add incoming keys/ESC finals.
; All emitted data go through MONRAW; this example is for an ANSI host.
TP_CLS: DB 7,27,'[2J',27,'[H'
TP_BYTES:
        DB 12,7,27,'[2J',27,'[H' ; FF: clear/home
        DB 0
TP_CODES:
        DB 'H',3,27,'[H'
        DB 'J',3,27,'[J'
        DB 'K',3,27,'[K'
        DB 'A',3,27,'[A'
        DB 'B',3,27,'[B'
        DB 'C',3,27,'[C'
        DB 'D',3,27,'[D'
        DB 0
