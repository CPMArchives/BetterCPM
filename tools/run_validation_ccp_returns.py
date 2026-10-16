#!/usr/bin/env python3
"""Observe repeated transient termination and public DU/TPA state on cpmsim."""
import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from build_ccp import assemble
from run_validation_returning import sha
from test_z80pack_sysgen_install import session
from system_layout import LAYOUT

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('baseline','diskdefs','suite','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--simulator',type=Path,default=Path.home()/'projects/git/z80pack/cpmsim/cpmsim')
    parser.add_argument('--cycles',type=int,default=3)
    parser.add_argument('--full-tpa',action='store_true')
    parser.add_argument('--du-scope',choices=('all','a0'),default='all')
    args=parser.parse_args()
    assert args.cycles>0
    report=json.loads((args.baseline/'report.json').read_text())
    original=args.baseline/report['image']
    assert report['target']=='z80pack' and sha(original)==report['sha256']
    program=args.suite/'suite/build/CCPTEST.COM'
    hashes={line.split()[1]:line.split()[0] for line in (args.suite/'suite/build/SHA256SUMS.txt').read_text().splitlines() if line.strip()}
    assert sha(program)==hashes[program.name]
    args.output.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix='ccp-returns-',dir=args.output.resolve()))
    disks=work/'disks';disks.mkdir()
    for letter in 'ab':shutil.copy2(original,disks/f'drive{letter}.dsk')
    shutil.copy2(args.diskdefs,work/'diskdefs')
    sources={}
    for source,name in [('returnstate.mac','STATE.COM'),('function0.mac','FUNCZERO.COM')]:
        path=ROOT/'tests/fixtures/conformance'/source
        assemble(Path.home()/'bin/z80asm',path.read_text(),work/name,work/(name+'.lst'),0x100)
        sources[name]={'source_sha256':sha(path),'binary_sha256':sha(work/name)}
    for path in (program,work/'STATE.COM',work/'FUNCZERO.COM'):
        subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(disks/'drivea.dsk'),str(path),'0:'+path.name],cwd=work,check=True)
    full_methods=[]
    if args.full_tpa:
        subprocess.run(['cpmrm','-T','raw','-f','bettercpm-default',str(disks/'driveb.dsk'),'0:*.*'],cwd=work,check=True)
        path=ROOT/'tests/fixtures/conformance/fullreturn.mac'
        capacity=(LAYOUT['TPA']-0x100)//128*128
        for route,name,exit_code in [('RET','ERET','        RET'),('JUMP','EJUMP','        JP 0'),('FUNCTION0','EFN0','        LD C,0\n        CALL 5')]:
            source=path.read_text().replace('@COUNT@',str(capacity-256)).replace('@ROUTE@',route).replace('@EXIT@',exit_code)
            file=work/(name+'.COM')
            code=assemble(Path.home()/'bin/z80asm',source,file,work/(name+'.lst'),0x100)
            assert len(code)<=256
            file.write_bytes(code.ljust(capacity,b'\xa5'))
            sources[file.name]={'source_template_sha256':sha(path),'binary_sha256':sha(file),'bytes':capacity}
            subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(disks/'driveb.dsk'),str(file),'0:'+file.name],cwd=work,check=True)
            full_methods.append((route,'B0:'+name))
        paint_source=ROOT/'tests/fixtures/conformance/painttpa.mac'
        paint=work/'PAINT.COM'
        assemble(Path.home()/'bin/z80asm',paint_source.read_text().replace('@COUNT@',str(capacity-257)),paint,work/'paint.lst',0x100)
        subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(disks/'drivea.dsk'),str(paint),'0:PAINT.COM'],cwd=work,check=True)
        sources[paint.name]={'source_template_sha256':sha(paint_source),'binary_sha256':sha(paint),'fill_byte':'5A'}
        oversized=work/'OVERRET.COM'
        oversized.write_bytes((work/'ERET.COM').read_bytes()+bytes(128))
        subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(disks/'driveb.dsk'),str(oversized),'0:'+oversized.name],cwd=work,check=True)
        exported=work/'oversize-extracted.bin'
        subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(disks/'driveb.dsk'),'0:OVERRET.COM',str(exported)],cwd=work,check=True)
        assert exported.read_bytes()==oversized.read_bytes()
        sources[oversized.name]={'binary_sha256':sha(oversized),'bytes':oversized.stat().st_size,'installed_bytes_verified':True}
    trace=work/'transcript.bin';results=[]
    def commands():
        contexts=[('A0:',0,0)] if args.du_scope=='a0' else [('A0:',0,0),('B3:',1,3),('B31:',1,31)]
        for navigation,drive,user in contexts:
            prompt=f'{chr(65+drive)}{user}>_ '.encode()
            yield (navigation.encode()+b'\r',prompt,30)
            for cycle in range(args.cycles):
                methods=full_methods if args.full_tpa else [('jump-zero','A0:CCPTEST /0025'),('entry-ret','A0:CCPTEST /0028'),('function-zero','A0:FUNCZERO')]
                for method,command in methods:
                    if args.full_tpa:
                        yield (b'A0:PAINT\r',prompt,30)
                    before=trace.read_bytes()
                    if args.full_tpa or method=='function-zero':
                        yield (command.encode()+b'\r',prompt,30)
                    else:
                        yield (command.encode()+b'\r',b'Press Enter to run the test: ',30)
                        yield (b'\r',prompt,30)
                    delta=trace.read_bytes()[len(before):]
                    if args.full_tpa:
                        assert ('FULL-TPA '+method+' ENTERED').encode() in delta, delta
                        assert b'FULL-TPA PATTERN OR RETURN FAILED' not in delta
                    assert b'FUNCTION ZERO RETURNED' not in delta
                    assert b'FAIL:' not in delta and b'Failed items:' not in delta
                    expected=f'STATE D={drive:02X} U={user:02X} TOP={LAYOUT["TPA"]:04X}'.encode()
                    yield (b'A0:STATE\r',expected,30)
                    yield (b'',prompt,30)
                    results.append({'drive':drive,'user':user,'cycle':cycle+1,'method':method,'public_state':expected.decode(),'status':'PASS'})
        if args.full_tpa:
            before=trace.read_bytes()
            yield (b'B0:OVERRET\r',prompt,30)
            delta=trace.read_bytes()[len(before):]
            assert b'FULL-TPA RET ENTERED' not in delta
            assert b'?\r\n' not in delta and b'Bad Sector' not in delta
            assert b'FULL-TPA PATTERN OR RETURN FAILED' not in delta
            expected=f'STATE D={drive:02X} U={user:02X} TOP={LAYOUT["TPA"]:04X}'.encode()
            yield (b'A0:STATE\r',expected,30)
            yield (b'',prompt,30)
            results.append({'method':'oversize-rejection','bytes':capacity+128,'status':'PASS','public_state':expected.decode()})
        yield (b'CPX LIST\r',b'RCP',30)
        yield (b'',prompt,30)
        yield (b'RSX LIST\r',b'No RSXs loaded',30)
        yield (b'',prompt,30)
        yield (b'BYE\r',b'System halted',10)
    try:
        transcript=session(args.simulator.resolve(),disks,commands(),trace)
    except Exception as error:
        assert sha(original)==report['sha256'],'reference image changed during failed run'
        (work/'failure.json').write_text(json.dumps({'error':str(error),'completed_cases':results,'baseline_sha256':report['sha256'],'fixtures':sources},indent=2)+'\n')
        raise
    assert transcript.count(b'Type TYPE README.TXT for more')==1,'cold startup repeated on warm return'
    assert sha(original)==report['sha256']
    result={'baseline_sha256':report['sha256'],'suite_program_sha256':sha(program),'simulator_sha256':sha(args.simulator),'fixtures':sources,'cases':results,'cold_banner_count':1,'cpx_rcp_reconstructed':True,'no_rsxs_loaded':True,'full_tpa':args.full_tpa,'du_scope':args.du_scope,'scope':'external termination/reconstruction observations, not fabricated suite PASS rows; full-TPA evidence only when full_tpa=true; no I/O-fault claim'}
    (work/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'pass':len(results),'evidence':str(work)},indent=2))


if __name__=='__main__':main()
