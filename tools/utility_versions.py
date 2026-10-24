"""Deterministic utility identities; counters advance only for released revisions."""
from pathlib import Path
import csv
import re
ROOT = Path(__file__).resolve().parents[1]
def identities():
    with (ROOT / 'metadata/utility-versions.tsv').open(encoding='ascii') as source:
        rows = list(csv.DictReader(source, delimiter='\t'))
    result = {}
    for row in rows:
        name, version, build = row['utility'], row['version'], int(row['build'])
        if name in result or not re.fullmatch(r'[A-Z][A-Z0-9]+', name) or not re.fullmatch(r'\d+\.\d+', version) or build < 1:
            raise ValueError('invalid utility identity: ' + str(row))
        result[name] = (version, build)
    return result

def banner(name, resident=False):
    version, build = identities()['RCP' if resident else name]
    detail = f'Resident, RCP Build {build:03d}' if resident else f'Build {build:03d}'
    from checked_carriers import selected_contract
    contract = selected_contract()
    if contract and not resident and name in ('CONFIG','STAT','SYSGEN','SYSBUILD','RESPACK','RLMBUILD','DIR','USER','CLS','VER','COPY','MOVE'):
        detail = 'Checked ' + contract['compatibility_id'][:8]
    return f'BetterCP/M {name} {version} ({detail})'

def strings(name, resident=False, label='UV_TEXT'):
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
            data += strings('MOVE', True, 'UV_TMOVE')
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
