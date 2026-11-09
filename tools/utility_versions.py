"""Deterministic utility identities; counters advance only for released revisions."""
from pathlib import Path
import re
from component_identity import title, identification
ROOT = Path(__file__).resolve().parents[1]
def identities():
    from component_registry import utility_identities
    return utility_identities()

def display_development(owner):
    from component_build import selected_display
    return selected_display(owner)['development']

def banner(name, resident=False):
    version, build = identities()['RCP' if resident else name]
    from component_registry import load
    owner = 'utility:' + ('RCP' if resident else name)
    row = load()['components'][owner]
    if row.get('display_format') == 'numeric':
        from component_build import selected_display
        value = title(name, version, build, development=display_development(owner))
        return value[:-1] + ', Resident RCP)' if resident else value
    checked_id = None
    from checked_carriers import selected_contract
    contract = selected_contract()
    if contract and not resident and name in ('CONFIG','STAT','SYSGEN','SYSBUILD','RESPACK','RLMBUILD','DIR','USER','CLS','VER','COPY','MOVE'):
        checked_id = contract['compatibility_id']
    return title(name, version, build, style='legacy-common', resident=resident, checked_id=checked_id)

def strings(name, resident=False, label='UV_TEXT'):
    from component_registry import load
    owner = 'utility:' + ('RCP' if resident else name)
    row = load()['components'][owner]
    if row.get('display_format') == 'numeric' and not resident:
        from component_build import selected_display
        version, revision = identities()['RCP' if resident else name]
        text = identification(name, version, revision, row['description'], development=display_development(owner))
        lines = [label+':'] + ["        DB '"+line.replace("'","''")+"',13,10" for line in text.splitlines()] + ["        DB '$'"]
        return '\n'.join(lines)+'\n'
    return f"{label}:\n        DB '{banner(name, resident)}',13,10,'$'\n"

def expand_versions(text):
    if '; @release-heading@' in text:
        import json
        version = json.loads((ROOT/'metadata/release-package.json').read_text())['version']
        old = 'BetterCP/M development (after core 1.0)'
        # Package 1.1 selects its core explicitly. Component development
        # markers remain independent; the package heading must not claim 1.0.
        heading = ('BetterCP/M '+version if re.fullmatch(r'1\.1(?:\.[0-9]+)?',version) else
                   old if display_development('utility:RCP') else 'BetterCP/M '+version)
        if len(heading) > len(old):
            raise ValueError('distribution heading exceeds its fixed field')
        padding = len(old)-len(heading)
        # ZSM4 has no DS count,fill extension and rejects a zero REPT count.
        # Explicit bytes preserve the cross image in both display states.
        fill = '\n        REPT '+str(padding)+'\n        DB 0\n        ENDM' if padding else ''
        text = text.replace('; @release-heading@',
            "DB 13,10,'"+heading+"',13,10,'$'"+fill)
    text = re.sub(r'; @utility-title ([A-Z][A-Z0-9]*)@',
                  lambda m: "TITLE: DB '" + banner(m[1]) + "',0", text)
    query = (ROOT / 'src/utilities/common/version.inc').read_text()
    match = re.search(r'; @utility-version ([A-Z][A-Z0-9]*)@', text)
    if match:
        name = match[1]
        prepared = query.replace('; @version-banner@', '        LD DE,UV_TEXT')
        extra = ''
        if name in ('STAT','CPX','RSX','DUP','SYSGEN','TIME','ERA','REN','TYPE','ED','SUBMIT','XSUB','ADMTST','VT52TST','ANSITST','SYSBUILD','RESPACK','RLMBUILD','WARM','PATH','NDR'):
            from utility_help import query_source, source
            prepared = prepared.replace('        CALL UV_QUERY',
                '        LD DE,UH_TEXT\n        CALL UH_QUERY\n        JR C,UV_EXIT\n'
                '        LD DE,UV_TEXT\n        CALL UV_QUERY', 1)
            extra = query_source(ROOT) + source(name,'UH_TEXT')
        text = text.replace(match[0], strings(name) + prepared + extra)
    if '; @rcp-version@' in text:
        commands = ['DIR','ERA','TYPE','REN','CLS','USER','VER','COPY','MOVE']
        resident = 'CPXBASE         EQU     00100H' not in text
        if resident:
            from utility_help import resident_parts, query_source
            records = resident_parts()
            data = ''.join(strings(n, True, 'UV_R'+n)+records[n] for n in commands)
            data += (ROOT/'src/cpx/help.inc').read_text()
            help_query = query_source(ROOT)
            printer = '        LD C,9\n        CALL 00005H'
            assert help_query.count(printer) == 1
            data += help_query.replace(printer, '        CALL RH_HELP')
        else:
            data = ''.join(strings(n, True, 'UV_R'+n) for n in commands)
        if 'CPXBASE         EQU     00100H' in text:
            data += ''.join(strings(n, False, 'UV_T'+n) for n in ['DIR','USER','CLS','VER','COPY'])
            # MOVE remains transitional, with RCP identity until its own contract is completed.
            data += strings('MOVE', False, 'UV_TMOVE')
        if resident:
            # Standalone tail wrapper is unused by RCP; keep carrier relocations bounded.
            query = query[query.index('\nUV_QUERY:') + 1:]
            printer = '        LD C,9\n        CALL 00005H'
            assert query.count(printer) == 1
            query = query.replace(printer, '        CALL RH_IDENT')
            # These adjacent dispatch branches fit JR. Save eight repair words
            # for the resident help gate without enlarging the BCPX header.
            text, shortened = re.subn(r'JP      NC,(BC_TRY[A-Z]+)',
                                     r'JR      NC,\1', text)
            assert shortened == 8
            # Reuse one syntax response while retaining each parser's cleanup.
            old = 'BC_DBAD:\n        LD      DE,BC_IFSPEC\n        CALL    BC_PRINT'
            assert text.count(old) == 1
            text = text.replace(old, 'BC_DBAD:\n        LD      DE,BC_IFSPEC\n        CALL    RH_FILE')
            text, errors = re.subn(
                r'(BC_(?:CLRBAD|USERBAD|VERBAD):[^\n]*\n)'
                r'        LD      DE,BC_RQMARK\n        JP      BC_PRINT',
                r'\1        JP      RH_BAD', text)
            assert errors == 3
            text, errors = re.subn(
                r'(BC_CSYNT:[^\n]*\n)        LD      DE,BC_CUSAGE\n'
                r'        JR      BC_CPRINT',
                r'\1        CALL    RH_BAD\n        JR      BC_COK', text)
            assert errors == 1
            text = re.sub(r'LD      DE,(UV_R[A-Z]+)',
                          r'LD      DE,\1-BC_COMMAND', text)
            text = text.replace('CALL    UV_QUERY', 'CALL    RH_VERSION')
            data += (ROOT / 'src/cpx/feature-hint.inc').read_text()
        prepared = query.replace('; @version-banner@', '')
        if not resident:
            from utility_help import query_source, source
            dispatch = ''
            for n in ('DIR','USER','CLS','VER','COPY','MOVE'):
                dispatch += ('        LD HL,UV_T'+n+'\n        OR A\n        SBC HL,DE\n'
                             '        JR NZ,UCN_'+n+'\n        LD DE,UHP_'+n+'\n'
                             '        JP UHC_CALL\nUCN_'+n+':\n')
                data += source(n,'UHP_'+n)
            dispatch += 'UHC_CALL:\n        LD HL,0081H\n        LD A,(0080H)\n        LD B,A\n        CALL UH_QUERY\n'
            prepared = prepared.replace('        LD HL,0081H', dispatch+'        JR C,UV_EXIT\n        POP HL\n        POP DE\n        PUSH DE\n        PUSH HL\n        LD HL,0081H',1)
            data += query_source(ROOT)
        text = text.replace('; @rcp-version@', data + prepared)
    return text
