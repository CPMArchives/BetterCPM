"""Qualify public compact TCAP on disposable Model 4 or Model II media."""
import argparse
import json
from pathlib import Path
import re
import sys

from build_profiles import symbols
from tcap_test_support import ROOT, sha
from build_ccp import assemble
from trs80gp_launch import run
from run_trs80_command import DEFAULT_EMULATOR, key_args


def screen(path):
    raw = path.read_bytes()[:1920]
    assert len(raw) == 1920
    return '\n'.join(bytes(c & 127 for c in raw[i:i+80]).decode('ascii', errors='replace').rstrip()
                     for i in range(0,1920,80))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('workspace', type=Path)
    p.add_argument('--platform', choices=('model4','model2'), required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--emulator', type=Path, default=DEFAULT_EMULATOR)
    p.add_argument('--resume', action='store_true', help='audit complete retained captures and continue remaining gates')
    p.add_argument('--integrated', action='store_true', help='compatibility flag; TCAP 2.0 direct qualification is the default')
    p.add_argument('--personality',choices=('ADM3A','VT52','ANSI'),default='ADM3A')
    p.add_argument('--inline-cache',action='store_true')
    p.add_argument('--all-personalities',action='store_true',help='qualify the integrated ADM3A, VT52 and ANSI profiles together')
    a = p.parse_args()
    workspace, out, emu = a.workspace.resolve(), a.output.resolve(), a.emulator.resolve()
    out.mkdir(parents=True, exist_ok=a.resume)
    previous = json.loads((out/'qualification.json').read_text()) if a.resume else None
    m2 = a.platform == 'model2'
    suffix = '.imd' if m2 else '.dmk'
    if m2:
        from checked_build_contract import load_contract
        identity = load_contract(workspace, Path.home()/'bin/z80asm')['compatibility_id']
        context = json.loads((workspace/'build/profile/context.json').read_text())
        assert context['profile'] == 'model2-fullram' and not context.get('public_tcap',False)
        baseline = context['symbols']['LY_TPA']
        artifacts = workspace/'build/trs80m2'
        package = (artifacts/'SYSTEM.SYS').read_bytes()
        from model2_media import image, geometry
        from test_model2_release_media import decoded, repack
        fmt = geometry()
        reserved = 3328+(fmt.off-1)*fmt.raw_track_bytes
        def make(payload, files): return image(payload, list(files.items()))
        def raw(data): return decoded(data)[2]
        def package_payload(data):
            d = raw(data)
            return d[:384]+d[1536:1664]+d[512:1024]+d[3328:3328+152*128]
        def blank_protected(data):
            comment, tracks, data = decoded(data)
            data = bytearray(data)
            data[:reserved] = b'\xe5'*reserved
            return repack(comment, tracks, data)
    else:
        identity = json.loads((workspace/'build-state.json').read_text())['source']['revision']
        baseline = symbols((workspace/'src/system/layout.inc').read_text())['LY_TPA']
        package = (workspace/'build/trs80/system-package/SYSTEM.SYS').read_bytes()
        from build_montezuma_extended_790k import build, RAW_SIZE
        from add_cpm_file_to_dmk import extract_raw
        from build_trs80_boot import install_files
        reserved = 20480
        def make(payload, files):
            data = bytearray(b'\xe5'*RAW_SIZE)
            data[:len(payload)] = payload
            install_files(data, list(files.items()), directory=reserved, block_count=(RAW_SIZE-reserved)//2048)
            return build(data)
        def raw(data): return extract_raw(data)
        def package_payload(data): return raw(data)[:len(package)-128]
        def blank_protected(data):
            data = bytearray(extract_raw(data))
            data[:reserved] = b'\xe5'*reserved
            return build(data)
    maximum = (baseline-256)//128*128
    from build_integrated_display import build as build_display
    from integrated_display_qualification import fixtures as direct_fixtures
    if a.all_personalities:
        from integrated_display_qualification import collection
        files,budgets,direct_sequence=collection(workspace,out,a.platform,maximum,('ADM3A','VT52','ANSI'),a.inline_cache,True)
        budget=budgets['ADM3A']
    else:
        carrier,budget=build_display(workspace,out/'profile',a.platform,a.personality,inline_cache=a.inline_cache)
        files=direct_fixtures(out/'fixtures',maximum,handshake=True,personality=a.personality)
        files[a.personality+'.RSX']=carrier
        budgets={a.personality:budget}
    files['HELLO.RSX']=(workspace/'build/rsx/HELLO.RSX').read_bytes()
    files['SUBMIT.COM']=(workspace/'build/utilities/SUBMIT.COM').read_bytes()
    for name, path in [('RCP.CPX','build/cpx/RCP.CPX'),('R3PACK.RSX','build/system/R3PACK.RSX'),
                       ('R3CACHE.RSX','build/system/R3CACHE.RSX')]: files[name] = (workspace/path).read_bytes()
    files['SYSTEM.SYS'] = package
    files['KEEP.TXT'] = b'PRESERVE FILES DURING TCAP INSTALLATION\r\n'
    for name in ('RSX','SYSGEN','CONFIG','STAT'):
        files[name+'.COM'] = (workspace/'build/utilities'/(name+'.COM')).read_bytes()
    marker_source = """        ASEG
        ORG 0100H
        LD DE,MSG
        LD C,9
        CALL 5
        LD HL,82H
        LD B,2
LOOP:   PUSH HL
        PUSH BC
        LD E,(HL)
        LD C,2
        CALL 5
        POP BC
        POP HL
        INC HL
        DJNZ LOOP
        LD C,1
        CALL 5
        JP 0
MSG: DB 'TCAP STEP $'
        END
"""
    marker_source=marker_source.replace('        LD C,1\n        CALL 5\n','''        LD A,(82H)
    SUB '0'
    LD B,A
    ADD A,A
    ADD A,A
    ADD A,B
    ADD A,A
    LD B,A
    LD A,(83H)
    SUB '0'
    ADD A,B
REDUCE: CP 26
    JR C,LETTER
    SUB 26
    JR REDUCE
LETTER:
    ADD A,'A'
    LD (WANT),A
READ:   LD C,1
    CALL 5
    LD HL,WANT
    CP (HL)
    JR NZ,READ
''').replace("MSG: DB 'TCAP STEP $'","WANT: DB 0\nMSG: DB 'TCAP STEP $'")
    files['MARK.COM'] = assemble(Path.home()/'bin/z80asm', marker_source,
                                out/'MARK.bin', out/'MARK.lst', 0x100)
    source = out/('source'+suffix)
    if not a.resume: source.write_bytes(make(package[128:], files))
    assert package_payload(source.read_bytes()) == package[128:]
    from integrated_display_qualification import commands as direct_commands,audit as direct_audit
    commands=direct_sequence if a.all_personalities else direct_commands(a.personality)
    report = {'status':'RUNNING','platform':a.platform,'service':'TCAP 2.0','identity':identity,
              'baseline_boundary':baseline,'maximum_com_bytes':maximum,'budgets':budgets,
              'emulator_sha256':sha(emu),'runner_sha256':sha(Path(__file__)),'checks':{}}
    def save(): (out/'qualification.json').write_text(json.dumps(report, indent=2)+'\n')
    def launch(disk, folder, second=None):
        cmd = [str(emu),'-m2' if m2 else '-m4']
        if m2: cmd += ['-mem','64']
        cmd += ['-batch','-turbo','-itime','20000','-d0',str(disk)]
        if not m2: cmd += ['-ktx']
        if second: cmd += ['-d1',str(second)]
        return cmd
    def key(value): return ['-i',value,'-id','60'] if m2 else key_args(value, delay=25)
    def lifecycle(label, image):
        case = out/label
        case.mkdir(exist_ok=a.resume)
        staged = dict(files)
        queue = []
        for i in range(len(commands)+1):
            queue.append(f'MARK {i:02d}')
            if i < len(commands): queue.append(commands[i])
        # Stock CCP consumes a single-extent reversed submit stack. Keep each
        # prepared queue below 128 records; a third profile otherwise starts at
        # the wrong extent. Chain via the ordinary SUBMIT utility, not a core fix.
        if len(queue)>120:
            staged['TCAPMORE.SUB']=('\r\n'.join(queue[88:])+'\r\n\x1a').encode('ascii')
            queue=queue[:88]+['SUBMIT TCAPMORE']
        assert len(queue)<=128
        staged['$$$.SUB'] = b''.join(bytes((len(c),))+c.encode()+bytes(127-len(c)) for c in reversed(queue))
        disk = case/('workflow'+suffix)
        # Use the installed protected surface, preserving the freshly installed
        # destination's geometry, and add only the deterministic SUBMIT fixture.
        if image == source:
            data = make(package[128:], staged)
        else:
            original = image.read_bytes()
            if m2:
                from test_model2_release_media import decoded, repack
                comment, tracks, installed_raw = decoded(original)
                temp = make(package[128:], staged)
                _, _, temp_raw = decoded(temp)
                data = repack(comment, tracks, installed_raw[:reserved]+temp_raw[reserved:])
            else:
                temp_raw = raw(make(package[128:], staged))
                data = build(raw(original)[:reserved]+temp_raw[reserved:])
        retained = sorted(case.glob('trs80-text-*.bin'), key=lambda p:int(p.stem.rsplit('-',1)[1]))
        if not retained: disk.write_bytes(data)
        else: assert raw(disk.read_bytes())[:reserved] == raw(image.read_bytes())[:reserved]
        cmd = launch(disk, case)
        stages = [('checkpoint',0)]
        cmd += ['-iw','TCAP STEP 00','-it']
        active = None
        for i, command in enumerate(commands):
            if command.startswith('RSX LOAD ') and command.split()[-1] in budgets:
                active = command.split()[-1]
            cmd += ['-id','60']+key(chr(65+i%26))
            if command.startswith('DEMO '):
                ready='INTEGRATED READY '+command[-1]
                cmd += ['-iw',ready,'-it']
                stages.append(('render',active))
                cmd += ['-id','60']+key(command[-1])
            cmd += ['-iw',f'TCAP STEP {i+1:02d}','-it']
            stages.append(('checkpoint',i+1))
        cmd += ['-ix']
        if len(retained) != len(stages):
            assert not retained, 'partial captures require a fresh output directory'
            (case/'arguments.json').write_text(json.dumps(cmd, indent=2)+'\n')
            print('Running', a.platform, label, flush=True)
            run(cmd, cwd=case, timeout=1800)
        else:
            print('Auditing retained', a.platform, label, flush=True)
        captures = sorted(case.glob('trs80-text-*.bin'), key=lambda p:int(p.stem.rsplit('-',1)[1]))
        assert len(captures) == len(stages), (len(captures), len(stages))
        frames, rendered = [], []
        for (kind, value), capture in zip(stages, captures):
            text = screen(capture)
            capture.with_suffix('.txt').write_text(text+'\n')
            if kind == 'checkpoint':
                assert f'TCAP STEP {value:02d}' in text, (value, text)
                # Text below the current blocking checkpoint may be old screen
                # contents left by cursor-position tests. It is not new output.
                if value: frames.append(text.split(f'TCAP STEP {value:02d}',1)[0])
            else:
                cells = capture.read_bytes()[4*80+9:4*80+18]
                assert bytes(c & 127 for c in cells) == b'TCAP TEXT', (value, text)
                reverse = value != 'VT52'
                assert all(bool(c & 128) == reverse for c in cells), (value, cells)
                rendered.append({'personality':value,'reverse':reverse,'capture':capture.name})
        checked = direct_audit(commands, frames, budgets, baseline)
        for check in checked:
            if check['command'] == 'TINFO':
                assert check['info_hex'] in ('18500F02','18500700'), check
        report['checks'][label] = {'commands':checked,'rendering':rendered,
                                  'captures':{p.name:sha(p) for p in captures},
                                  'workflow_image_sha256':sha(disk)}
        report['checks'][label]['consumer_helper_bytes']=budget['helper_bytes']
        save()
    try:
        save()
        lifecycle('source-lifecycle', source)
        destination = out/('installed'+suffix)
        destination.write_bytes(blank_protected(source.read_bytes()))
        before = raw(destination.read_bytes())
        case = out/'installation'
        case.mkdir(exist_ok=a.resume)
        installer_source = source
        if not m2:
            # The standard Model 4 B: definition is a smaller system format.
            # Use the maintained CONFIG-API fixture to select the matching
            # extended system geometry before invoking the ordinary installer.
            import test_sysgen_install as setup
            saved = setup.OUT
            try:
                setup.OUT = case
                setter = setup.setup_program()
            finally:
                setup.OUT = saved
            install_fileset = dict(files)
            install_fileset['SETBSYS.COM'] = setter
            queue = ['SETBSYS','SYSGEN SYSTEM.SYS B:']
            install_fileset['$$$.SUB'] = b''.join(bytes((len(c),))+c.encode()+bytes(127-len(c)) for c in reversed(queue))
            installer_source = case/'installer-source.dmk'
            installer_source.write_bytes(make(package[128:], install_fileset))
        cmd = launch(installer_source, case, destination)
        if m2:
            cmd += ['-iw','A0>','-id','300']+key('SYSGEN SYSTEM.SYS B:\r')
        cmd += ['-iw','Proceed (Y/N)?','-it']+key('Y')
        cmd += ['-iw','System installed and verified','-it','-ix']
        (case/'arguments.json').write_text(json.dumps(cmd, indent=2)+'\n')
        print('Running', a.platform, 'installation', flush=True)
        run(cmd, cwd=case, timeout=1800)
        after = raw(destination.read_bytes())
        assert after[reserved:] == before[reserved:], 'SYSGEN changed destination files'
        assert after[:reserved] != before[:reserved]
        report['checks']['installation'] = {'filesystem_unchanged':True,'installed_image_sha256':sha(destination)}
        save()
        lifecycle('installed-lifecycle', destination)
        report.update(status='PASS public TCAP source, installation, installed cold/warm lifecycle and unload',
                      permanent_memory_loss_bytes=0)
    except BaseException as error:
        report.update(status='FAIL', detail=str(error))
        raise
    finally:
        save()
    print(report['status'], a.platform, out, flush=True)


if __name__ == '__main__':
    main()
