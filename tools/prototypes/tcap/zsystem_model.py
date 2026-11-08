"""Build/qualify private table-driven TCAP on an ordinary checked cpmsim image.

No BIOS, loader or backend hook is inserted. XTAB 0.1 is experimental and makes
no claim to implement the superseded public transaction ABI. All media is copied.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'tools'))
from build_ccp import assemble
from build_cpx_module import relocation_offsets
from build_rsx_module import make_module
from build_z80pack_image import symbols
from checked_build_contract import load_contract
from checked_carriers import rsx_metadata


def description(name):
    # Tokens 1/2: zero-based row/column plus 32. Tokens 3/4: one-based decimal.
    profiles = {
        'ANSI': (0, 0, 1, [b'\x1b[2J\x1b[H', b'\x1b[\x03;\x04H', b'\x1b[K',
                            b'\x1b[1m', b'\x1b[22m', b'\x1b[0m', b'\x1b[0m']),
        'ADM3A': (24, 80, 2, [b'\x1a', b'\x1b=\x01\x02', b'\x15', b'\x0f',
                                b'\x0e', b'\x0e', b'\x0e']),
        'VT52': (24, 80, 0, [b'\x1bH\x1bJ', b'\x1bY\x01\x02', b'\x1bK',
                               b'', b'', b'', b'']),
    }
    rows, cols, style, strings = profiles[name]
    data = bytearray(b'TC\0\0'+bytes((rows, cols, 7 | (8 if style else 0), style))+bytes(8))
    for slot, value in enumerate(strings):
        if value:
            data[8+slot] = len(data)
            data.extend(value+b'\0')
    data[3] = len(data)
    assert len(data) <= 128
    return bytes(data)


PRINTER = """HEX:    PUSH AF
        RRCA
        RRCA
        RRCA
        RRCA
        CALL NIB
        POP AF
NIB:    AND 15
        ADD A,48
        CP 58
        JR C,CHAR
        ADD A,7
CHAR:   PUSH HL
        PUSH BC
        LD E,A
        LD C,2
        CALL 5
        POP BC
        POP HL
        RET
"""


def build(workspace, out):
    out.mkdir(parents=True, exist_ok=False)
    asm = Path.home()/'bin/z80asm'
    contract = load_contract(workspace, asm)
    platform = workspace/'build/z80pack'
    shutil.copytree(platform/'disks', out/'disks')
    shutil.copy2(platform/'diskdefs', out/'diskdefs')
    def install(name, data):
        path = out/name
        path.write_bytes(data)
        subprocess.run(['cpmcp', '-f', 'bettercpm-default', str(out/'disks/drivea.dsk'),
                        str(path), '0:'+name], cwd=out, check=True)
    def emit(name, source, base=0x100):
        return assemble(asm, f'        ASEG\n        ORG 0{base:04X}H\n'+source+'\n        END\n',
                        out/(name+'.bin'), out/(name+'.lst'), base)
    for name, path in [('RCP.CPX', 'build/cpx/RCP.CPX'), ('R3PACK.RSX', 'build/system/R3PACK.RSX'),
                       ('R3CACHE.RSX', 'build/system/R3CACHE.RSX'), ('RSX.COM', 'build/utilities/RSX.COM'),
                       ('ANSISCRN.RSX', 'build/rsx/ANSISCRN.RSX'), ('BYE.COM', 'build/z80pack-tools/BYE.COM')]:
        install(name, (workspace/path).read_bytes())
    profiles = {}
    for name, entry, minor in [('ANSI', 'AN_ENTRY', 2), ('ADM3A', 'AM_ENTRY', 1), ('VT52', 'VT_ENTRY', 1)]:
        text = (ROOT/'src/rsx'/(name.lower()+'.mac')).read_text()
        assert text == (workspace/'src/rsx'/(name.lower()+'.mac')).read_text(), 'personality source differs from prepared inputs'
        text = text.replace('        CSEG\n        .PHASE ', '        ASEG\n        ORG ').replace('        .DEPHASE\n', '')
        for include in ('ansi-dispatch.inc', 'screen/rendition.inc'):
            text = text.replace('        INCLUDE '+include, (ROOT/'src/rsx'/include).read_text())
        # Large candidate's unrelated short-branch rewrites are not used here.
        baseline = assemble(asm, text, out/(name+'-base.bin'), out/(name+'-base.lst'), 0x8000)
        base_symbols = symbols(out/(name+'-base.lst'))
        ordinary = make_module(name=name, version=(0, 1), services=[], linked_base=0x8000,
                               code=baseline, relocations=[], reconstruction_class='STATEFUL',
                               callable_services=[(b'MCON', 1, minor, base_symbols[entry]-0x8000, 4)])
        record = description(name)
        query = """XT_QUERY:
        OR A
        JR NZ,XT_BAD
        LD HL,XT_TABLE
        RET
XT_BAD: LD A,255
        RET
XT_TABLE:
"""+''.join('        DB '+','.join(map(str, record[i:i+16]))+'\n'
             for i in range(0, len(record), 16))
        source = text.replace('        END', query+'        END')
        code = assemble(asm, source, out/(name+'.bin'), out/(name+'.lst'), 0x8000)
        alternate = assemble(asm, source.replace('08000H', '08101H'), out/(name+'-alt.bin'),
                             out/(name+'-alt.lst'), 0x8101)
        labels = symbols(out/(name+'.lst'))
        assert len(code) == labels['XT_TABLE']+len(record)-0x8000
        assert code[-len(record):] == record
        repairs = relocation_offsets(code, alternate, 0x101)
        carrier = make_module(name=name, version=(0, 1), services=[], linked_base=0x8000,
                              code=code, relocations=repairs, reconstruction_class='STATEFUL',
                              callable_services=[(b'MCON', 1, minor, labels[entry]-0x8000, 4),
                                                 (b'XTAB', 0, 1, labels['XT_QUERY']-0x8000, 0)])
        # Use the ordinary checked BMET2 binding to the already verified core.
        # No new admission engine or privileged callback path is required.
        at = int.from_bytes(carrier[30:32], 'little')
        header = bytearray(carrier[:512])
        header[4] = 3
        carrier = bytes(header)+carrier[512:at]+rsx_metadata(name, carrier[at:], contract)
        install(name+'.RSX', carrier)
        # The loader's existing descriptor page is charged in both totals.
        allocation = int.from_bytes(carrier[14:16], 'little')+256
        base_allocation = int.from_bytes(ordinary[14:16], 'little')+256
        profiles[name] = dict(descriptor_bytes=len(record), query_bytes=len(code)-len(baseline)-len(record),
                              payload_bytes=len(code), baseline_payload_bytes=len(baseline),
                              allocated_bytes=allocation, baseline_allocated_bytes=base_allocation,
                              extra_allocated_bytes=allocation-base_allocation, relocation_words=len(repairs))
    client = (ROOT/'tools/prototypes/tcap/zsystem_client.inc').read_text()
    # Long failure branches are unconditional on code placement; retain compact
    # local loops. This also makes budget accounting independent of relaxation.
    client = re.sub(r'\bJR (Z,|NZ,|C,|NC,)?(TC_BAD|TC_NONE)\b', r'JP \1\2', client)
    emit('client', client, 0x4000)
    labels = symbols(out/'client.lst')
    library = dict(code_bytes=labels['TC_CODE_END']-0x4000,
                   private_data_bytes=labels['TC_LIBRARY_END']-labels['TC_CODE_END'],
                   total_bytes=labels['TC_LIBRARY_END']-0x4000)
    for profile in profiles.values():
        profile['comparable_tcap_bytes'] = profile['extra_allocated_bytes']+library['total_bytes']
        assert profile['comparable_tcap_bytes'] <= 1280, profile
    boundary = """        LD DE,MSG
        LD C,9
        CALL 5
        LD HL,(6)
        LD A,H
        CALL HEX
        LD A,L
        CALL HEX
        LD DE,NL
        LD C,9
        CALL 5
        JP 0
MSG: DB 'BOUNDARY $'
NL: DB 13,10,'$'
"""+PRINTER
    install('BOUND.COM', emit('boundary', boundary))
    largest = emit('maxcom', """        LD DE,MSG
        LD C,9
        CALL 5
        JP 0
MSG: DB 'MAXIMUM COM PASS',13,10,'$'
""")
    install('MAXCOM.COM', largest.ljust(57344, b'\0'))
    # Exercise the public registry, private description, and ordinary BDOS output.
    probe = """        LD E,1
        LD C,8
        CALL 5
        CALL TC_OPEN
        OR A
        JP NZ,FAIL
        LD A,5
        CALL TC_EMIT
        OR A
        JP NZ,FAIL
        LD BC,0409H
        LD A,1
        CALL TC_EMIT
        OR A
        JP NZ,FAIL
        LD A,3
        CALL TC_EMIT
        OR A
        JP NZ,FAIL
        LD DE,WORD
        LD C,9
        CALL 5
        LD A,4
        CALL TC_EMIT
        OR A
        JP NZ,FAIL
        LD A,6
        CALL TC_EMIT
        OR A
        JP NZ,FAIL
        LD DE,MSG
        LD C,9
        CALL 5
        JP 0
FAIL:   CALL HEX
        LD A,(TC_MLOOK+19)
        CALL HEX
        LD A,(TC_LOOK+19)
        CALL HEX
        LD DE,ERR
        LD C,9
        CALL 5
        JP 0
WORD: DB 'TCAP TEXT$'
MSG: DB 13,10,'TABLE PROBE PASS',13,10,'$'
ERR: DB 'TABLE PROBE FAIL',13,10,'$'
"""
    probe_image = emit('probe', probe+PRINTER+client)
    install('TABLE.COM', probe_image)
    install('ABSENT.COM', emit('absent', """        LD DE,LOOK
        LD C,182
        CALL 5
        CP 1
        LD DE,BAD
        JR NZ,PRINT
        LD DE,GOOD
PRINT:  LD C,9
        CALL 5
        JP 0
LOOK: DB 1,20,0,0,'XTAB',0,1,0,0
        DS 8,0
GOOD: DB 'TABLE ABSENT PASS',13,10,'$'
BAD: DB 'TABLE ABSENT FAIL',13,10,'$'
"""))
    report = dict(status='BUILT private XTAB 0.1; not public ABI qualification',
                  model='Z-System-style per-personality description and per-application library',
                  permanent_tcap_bytes=0, bios_or_loader_changes=False,
                  helper=library, profiles=profiles, probe_com_bytes=len(probe_image),
                  helper_source_sha256=hashlib.sha256(client.encode()).hexdigest(),
                  checked_compatibility_id=contract['compatibility_id'],
                  tested_maximum_com_bytes=57344,
                  builder_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  loaded_file_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                      for p in sorted(out.glob('*.RSX'))},
                  system_image_sha256=hashlib.sha256((platform/'disks/drivea.dsk').read_bytes()).hexdigest())
    (out/'build.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


def qualify(out, simulator):
    from qualify_cpmsim_package import Guest
    report = json.loads((out/'build.json').read_text())
    report['checks'] = []
    guest = Guest(simulator, out/'disks', out)
    def command(text, wanted=None):
        data = guest.prompt(text)
        assert b'FAIL' not in data and b'error' not in data.lower(), (text, data[-1500:])
        if wanted: assert wanted in data, (text, data[-1500:])
        check = {'command': text}
        if text == 'BOUND':
            values = re.findall(rb'BOUNDARY ([0-9A-F]{4})', data)
            assert len(values) == 1, data
            check['boundary'] = int(values[0], 16)
        report['checks'].append(check)
        print('PASS', check, flush=True)
        return check
    try:
        guest.prompt()
        initial = command('BOUND')['boundary']
        command('MAXCOM', b'MAXIMUM COM PASS')
        command('ABSENT', b'TABLE ABSENT PASS')
        command('RSX LOAD ANSISCRN')
        backend = command('BOUND')['boundary']
        for name in ('ADM3A', 'ANSI', 'VT52', 'ANSI'):
            command('RSX LOAD '+name)
            loaded = command('BOUND')['boundary']
            assert backend-loaded == report['profiles'][name]['allocated_bytes']
            command('TABLE', b'TABLE PROBE PASS')
            cells = [guest.screen.buffer[4][col] for col in range(9, 18)]
            assert ''.join(c.data for c in cells) == 'TCAP TEXT', (name, guest.screen.display)
            assert all(c.bold == (name == 'ANSI') and c.reverse == (name == 'ADM3A') for c in cells), (name, cells)
            report['checks'][-1]['rendering'] = {'text': 'TCAP TEXT', 'row': 4, 'column': 9,
                                                'bold': name == 'ANSI', 'reverse': name == 'ADM3A'}
            # Every probe JP 0 warm return is followed by a fresh discovery.
            command('TABLE', b'TABLE PROBE PASS')
            command('RSX UNLOAD '+name)
            command('ABSENT', b'TABLE ABSENT PASS')
            assert command('BOUND')['boundary'] == backend
        command('RSX UNLOAD ANSISCRN')
        assert command('BOUND')['boundary'] == initial
        command('MAXCOM', b'MAXIMUM COM PASS')
        command('ABSENT', b'TABLE ABSENT PASS')
        report['unloaded_boundary_before'] = initial
        report['unloaded_boundary_after'] = initial
        report['simulator_sha256'] = hashlib.sha256(simulator.read_bytes()).hexdigest()
        report['status'] = 'PASS private table-model cpmsim source-image lifecycle'
        report['limitations'] = ['not public ABI 1.0 conformance', 'no installation qualification',
                                'Model 4 and Model II not qualified', 'CRT route only',
                                'utility migrations and release assignment deferred']
    except Exception as error:
        report['status'] = 'FAIL private table-model cpmsim source-image lifecycle'
        report['failure'] = str(error)
        raise
    finally:
        guest.close()
        (out/'qualification.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('workspace', type=Path)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--simulator', type=Path, default=ROOT/'build/tcap-cpmsim-emulator/z80pack/cpmsim/cpmsim')
    p.add_argument('--qualify', action='store_true')
    args = p.parse_args()
    out = args.output.resolve()
    result = build(args.workspace.resolve(), out)
    if args.qualify: result = qualify(out, args.simulator.resolve())
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
