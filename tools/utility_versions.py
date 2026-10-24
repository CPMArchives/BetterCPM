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
        text = text.replace(match[0], strings(name) + query.replace('; @version-banner@', '        LD DE,UV_TEXT'))
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
        text = text.replace('; @rcp-version@', data + query.replace('; @version-banner@', ''))
    return text
