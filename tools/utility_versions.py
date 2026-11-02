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
        return title(name, version, build, development=display_development(owner))
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
    text = re.sub(r'; @utility-title ([A-Z][A-Z0-9]*)@',
                  lambda m: "TITLE: DB '" + banner(m[1]) + "',0", text)
    query = (ROOT / 'src/utilities/common/version.inc').read_text()
    match = re.search(r'; @utility-version ([A-Z][A-Z0-9]*)@', text)
    if match:
        name = match[1]
        prepared = query.replace('; @version-banner@', '        LD DE,UV_TEXT')
        extra = ''
        if name in ('STAT','CPX','RSX','DUP','SYSGEN','TIME','ERA','REN','TYPE','ED','SUBMIT','XSUB','ADMTST','VT52TST','ANSITST','SYSBUILD','RESPACK','RLMBUILD','WARM'):
            from utility_help import query_source, source
            prepared = prepared.replace('        CALL UV_QUERY',
                '        LD DE,UH_TEXT\n        CALL UH_QUERY\n        JR C,UV_EXIT\n'
                '        LD DE,UV_TEXT\n        CALL UV_QUERY', 1)
            extra = query_source(ROOT) + source(name,'UH_TEXT')
        text = text.replace(match[0], strings(name) + prepared + extra)
    if '; @rcp-version@' in text:
        commands = ['DIR','ERA','TYPE','REN','CLS','USER','VER','COPY','MOVE']
        data = ''.join(strings(n, True, 'UV_R'+n) for n in commands)
        if 'CPXBASE         EQU     00100H' in text:
            data += ''.join(strings(n, False, 'UV_T'+n) for n in ['DIR','USER','CLS','VER','COPY'])
            # MOVE remains transitional, with RCP identity until its own contract is completed.
            data += strings('MOVE', False, 'UV_TMOVE')
        resident = 'CPXBASE         EQU     00100H' not in text
        if resident:
            # Standalone tail wrapper is unused by RCP; keep carrier relocations bounded.
            query = query[query.index('\nUV_QUERY:') + 1:]
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
