#!/usr/bin/env python3
"""Native current-module parity and execution from NOAH companion Utilities media.

An exact-byte native baseline can supply unchanged modules. Changed modules
are rebuilt with the original ZSM4/LINK; no source, byte or padding mismatch is
accepted. This campaign complements the full codec/ARC/extent runtime campaign.
"""
import argparse
import json
from pathlib import Path
import re
import shutil
from build_noah import build, ROOT
from dasm_native import campaign
from noah_distribution import image_name
from qualify_noah_codecs import sha, native_match, probe
from qualify_noah_proof import verify_system
from test_ark import member
from test_usq_com import padded


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('system','utilities','baseline','output'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--platforms',nargs='+',choices=('z80pack','trs80gp'),default=['z80pack','trs80gp'])
    a=p.parse_args()
    a.system=a.system.resolve();a.utilities=a.utilities.resolve();a.baseline=a.baseline.resolve();a.output=a.output.resolve()
    systems=verify_system(a.system,a.platforms)
    a.output.mkdir(parents=True,exist_ok=False)
    cross=a.output/'cross'
    image=build(Path.home()/'bin/z80asm',cross)
    names=['NOAH','NHCLI','NCSQ','NCUSQ','NCCR','NCUNCR','NHARK','NCLZW','NCAR8']
    expected={n:(cross/(n+'.bin')).read_bytes() for n in names}
    for n in ('NOAH.COM','NOAH.OVL'):
        assert (ROOT/'build/utilities'/n).read_bytes()==(cross/n).read_bytes(),'stale packaged '+n
    tools={n:(ROOT/'third_party'/folder/n).read_bytes() for n,folder in [('ZSM4.COM','zsm4'),('LINK.COM','dri-link')]}
    mem=probe(Path.home()/'bin/z80asm',cross)
    report={'scope':'current native module parity and companion Utilities volume execution; full runtime baseline recorded separately',
            'layout':image.layout,'verified_systems':systems,
            'binaries':{n:{'bytes':len((cross/n).read_bytes()),'sha256':sha((cross/n).read_bytes())} for n in ('NOAH.COM','NOAH.OVL')},
            'platforms':{}}
    groups=[names[:2],names[2:6],names[6:]]
    for platform in a.platforms:
        base=a.output/platform;base.mkdir()
        native={};proof=[]
        for index,group in enumerate(groups):
            changed=[]
            for n in group:
                old=a.baseline/platform/('build-'+str(index))/('after-'+n+'.COM')
                try:
                    raw=old.read_bytes();native_match(raw,expected[n])
                except (OSError,AssertionError):
                    changed.append(n)
                else:
                    native[n]=raw
                    proof.append({'module':n,'status':'PASS','exact_byte_reuse':str(old),'sha256':sha(raw)})
            if not changed:continue
            files={n+'.MAC':(cross/(n+'.MAC')).read_bytes() for n in changed}
            prefix=['RSX UNLOAD ADM3A','RSX UNLOAD M4SCRN'] if platform=='trs80gp' else []
            commands=prefix+[f'B:ZSM4 {n}={n}' for n in changed]+[f'B:LINK {n}[A]' for n in changed]
            log,outputs=campaign(platform,files,commands,base/('build-'+str(index)),system=a.system,
                 utilities=a.utilities,extract=[n+'.COM' for n in changed],utility_files=tools,timeout=600)
            assert re.findall(rb'Errors: +([0-9]+)',log)==[b'0']*len(changed)
            for n in changed:
                raw=outputs[n+'.COM'];native_match(raw,expected[n]);native[n]=raw
                proof.append({'module':n,'status':'PASS','execution':'build-'+str(index)+'/execution.json','sha256':sha(raw)})
        assert set(native)==set(names)
        companion=bytearray(image.overlay[:128])
        for n in names[1:]:
            body=native[n][:len(expected[n])];companion.extend(body+bytes(-len(body)%128))
        assert bytes(companion)==image.overlay
        # The existing native runner expects canonical Utilities filenames.
        # Alias copies retain the exact companion-volume bytes and hashes.
        paired=base/'paired-media';paired.mkdir()
        source=a.utilities/image_name(platform)
        canonical='BetterCPM-Utilities-'+platform+('-80T-DS-800K.dmk' if platform=='trs80gp' else '-332K.dsk')
        shutil.copyfile(source,paired/canonical)
        work='A' if platform=='trs80gp' else 'C'
        data=bytes(range(256))
        keep=member(b'keep me',name=b'KEEP.BIN');drop=member(b'drop me',name=b'DROP.BIN')
        old=padded(keep+drop+b'\x1a\0opaque suffix')
        files={'INPUT.BIN':data,'OLD.ARK':old,'NCMEM.COM':mem}
        prefix=['A:','RSX LOAD ANSISCRN','RSX LOAD ANSI','C:'] if platform=='z80pack' else []
        commands=prefix+['B:',f'{work}:NCMEM','NOAH /VER',
            f'NOAH /ADD {work}:SMOKE.ARK {work}:INPUT.BIN',
            f'NOAH /ADD /SQ /Y {work}:SMOKE.ARK {work}:INPUT.BIN',
            f'NOAH /ADD /CR /Y {work}:SMOKE.ARK {work}:INPUT.BIN',
            f'NOAH /ADD /Y {work}:OLD.ARK {work}:INPUT.BIN',
            f'NOAH /COMPACT /Y {work}:OLD.ARK',
            f'NOAH /REMOVE /Y {work}:OLD.ARK DROP.BIN',
            f'NOAH /TEST {work}:SMOKE.ARK',
            f'NOAH /X /Y {work}:SMOKE.ARK {work}:',work+':']
        log,outputs=campaign(platform,files,commands,base/'runtime',system=a.system,utilities=paired,
             extract=['SMOKE.ARK','OLD.ARK','INPUT.BIN'],
             utility_files={n:(cross/n).read_bytes() for n in ('NOAH.COM','NOAH.OVL')},timeout=900)
        ceiling=b'C501' if platform=='z80pack' else b'CA01'
        assert b'NOAH QUAL TPA '+ceiling in log
        assert re.findall(rb'Outcome: ([a-z/-]+)\.',log)==[
            b'success']*3+[b'warning/partial',b'failure',b'warning/partial',b'success',b'success'],log[-4000:]
        assert b'ARK opaque trailer: unvalidated.' in log
        suffix=old[len(keep)+len(drop)+2:]
        added=keep+drop+member(data,name=b'INPUT.BIN')+b'\x1a\0'
        suffix=padded(added+suffix)[len(added):]
        assert outputs['OLD.ARK']==padded(keep+member(data,name=b'INPUT.BIN')+b'\x1a\0'+suffix)
        assert outputs['INPUT.BIN']==data and outputs['SMOKE.ARK'][1]==8
        assert source.read_bytes()==(paired/canonical).read_bytes()
        report['platforms'][platform]={'status':'PASS','runtime_ceiling_hex':ceiling.decode(),
            'system_sha256':systems[platform]['image_sha256'],'utilities_sha256':sha(source.read_bytes()),
            'native_modules':proof,'native_outputs':{n:sha(b) for n,b in native.items()},
            'runtime_console_sha256':sha(log),'runtime_outputs':{n:sha(b) for n,b in outputs.items()},
            'execution':'runtime/execution.json','paired_original_unchanged':True}
        (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        print('PASS',platform,'current native modules and packaged NOAH companion volume',flush=True)
    report['noah_acceptance']='PASS'
    (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
