"""Part 12 guards, applied only inside the checked streaming cpmsim stage."""
import json,re


def apply(root):
    from assessment_checked_profiles import replace
    identity = json.loads((root/'assessment-profile.json').read_text())['compatibility_id']
    def append(s, extra):
        s,n=re.subn(r'^        END(?:[ \t]+[A-Z]\w*)?[ \t]*$', lambda m:extra+'\n'+m[0],s,flags=re.M)
        assert n==1
        return s
    guard = '''
; Part 12 private utility contract. Establish a private stack before calling.
; Page-zero WBOOT locates the BIOS before any compiled private address is read.
P12CHECK:
        LD A,(0)
        CP 0C3H
        JR NZ,P12BAD
        LD HL,(1)
        LD DE,LY_BIOS+3
        OR A
        SBC HL,DE
        JR NZ,P12BAD
        LD HL,LY_CID
        LD DE,P12ID
        LD B,16
P12LOOP:
        LD A,(DE)
        CP (HL)
        JR NZ,P12BAD
        INC HL
        INC DE
        DJNZ P12LOOP
        RET
P12BAD:
        LD DE,P12MSG
        LD C,9
        CALL 5
        JP 0
P12MSG: DB 'Private utility build mismatch.',13,10,'$'
P12ID: DB ''' + ','.join(str(b) for b in bytes.fromhex(identity)) + '\n'
    for stem, anchor in (
        ('config', '        LD SP,04000H'),
        ('sysgen', '        LD SP,03F00H'),
        ('stat', 'MEMREPORT:                              ; report BetterCP/M memory map'),
    ):
        p = root/f'src/utilities/{stem}.mac'
        s = replace(p.read_text(), anchor, anchor+'\n        CALL P12CHECK')
        selected_guard = guard
        if stem == 'config':
            # Reuse CONFIG's zero-terminated compatibility diagnostic. Its
            # existing 512-byte stack reservation remains completely intact.
            selected_guard = guard.replace('LD DE,P12MSG\n        LD C,9\n        CALL 5',
                                           'LD HL,ABIMSG\n        CALL PUTS')
            selected_guard = selected_guard.replace("P12MSG: DB 'Private utility build mismatch.',13,10,'$'\n", '')
        s = append(s,selected_guard)
        p.write_text(s)
    p = root/'tools/build_config.py'
    s = replace(p.read_text(), ' return expand_config_ui(text)',
                " text=text.replace('Requires BetterCP/M disk BIOS ABI 5 (four drives).', 'Requires matching BetterCP/M private build.')\n return expand_config_ui(text)")
    p.write_text(s)
    # CLS.COM shares RCP code but has no private carrier binding. Resolve the
    # documented BIOS MONCALL entry just as monitorconsole.inc does. The
    # resident RCP source and its allocation are untouched.
    p = root/'tools/build_rcp_transients.py'
    s = replace(p.read_text(), '    return text\n\n\ndef main()',
                "    text=text.replace('        JP      LY_BIOS+66', '        LD HL,(1)\\n        LD DE,63\\n        ADD HL,DE\\n        JP (HL)')\n    return text\n\n\ndef main()")
    p.write_text(s)
    # The final cpmsim CONFIG carries only its own resident/IOBYTE descriptors.
    # Intermediate native products are merely inputs to the host build.
    p = root/'tools/build_disk_utilities.py'
    s = replace(p.read_text(), '    validation=assembly(records)',
                '    if args.config_extra_resident: records=records[-1:]\n    validation=assembly(records)')
    s = replace(s, '    io_meta=io_assembly(io_records)',
                '    if args.config_extra_resident: io_records=io_records[-1:]\n    io_meta=io_assembly(io_records)')
    p.write_text(s)
    # These host/native development products still emit pre-checked formats.
    # Do not leave apparently usable writers alongside a checked build.
    for stem in ('sysbuild', 'respack', 'rlmbuild'):
        p = root/f'src/utilities/{stem}.mac'
        s = p.read_text()
        s, n = re.subn(r'(CALL\s+UV_CHECK)[^\n]*',
                      r'\1\n        LD SP,03F00H\n        LD DE,P12NO\n        LD C,9\n        CALL 5\n        JP 0', s, count=1)
        assert n == 1, stem
        s = append(s, "P12NO: DB 'Native packaging tool unavailable in checked cpmsim build.',13,10,'$'\n")
        p.write_text(s)
    p = root/'tools/utility_versions.py'
    s = replace(p.read_text(), "if name=='SYSGEN':", "if not resident and name in ('CONFIG','STAT','SYSGEN','SYSBUILD','RESPACK','RLMBUILD','DIR','USER','CLS','VER','COPY','MOVE'):")
    s = replace(s, "detail='Assessment P11 '+ident[:8]", "detail='P12 '+ident[:8]")
    p.write_text(s)
