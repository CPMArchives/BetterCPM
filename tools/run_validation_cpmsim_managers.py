#!/usr/bin/env python3
"""Validate shipped batch, identity, clock and extension management utilities."""
import argparse,json,re,shutil,subprocess
from pathlib import Path
from run_validation_cpmsim_ren import audit
from run_validation_returning import sha
from test_z80pack_attributes import directory
from test_z80pack_sysgen_install import session
from utility_versions import banner


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('baseline','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();w=a.output.resolve();w.mkdir(parents=True,exist_ok=False);base=a.baseline.resolve()
    report=json.loads((base/'report.json').read_text());(w/'disks').mkdir()
    for letter in 'ab':shutil.copy2(base/report['image'],w/'disks'/f'drive{letter}.dsk')
    shutil.copy2(base/'diskdefs',w/'diskdefs');shutil.copy2(__file__,w/'executed-runner.py')
    def put(letter,user,name,data):
        f=w/(str(user)+'-'+name);f.write_bytes(data)
        subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(w/'disks'/f'drive{letter}.dsk'),str(f),f'{user}:{name}'],cwd=w,check=True,capture_output=True)
    put('a',0,'V029.SUB',b'TYPE B3:$1.TXT\r\nTYPE B3:DONE.TXT'.ljust(128,b' '))
    put('b',3,'ARG.TXT',b'PARAMETER CONTENT PASSED\r\n\x1a')
    put('b',3,'DONE.TXT',b'BATCH RUN FINISHED\r\n\x1a')
    b=w/'disks/driveb.dsk';before=b.read_bytes();sim=Path.home()/'projects/git/z80pack/cpmsim/cpmsim';prompt=b'A0>_ '
    steps=[]
    for name in ('VER','TIME','SUBMIT','CPX','RSX'):
        steps.append((f':{name} /VER\r'.encode(),prompt,30))
    steps += [(b'SUBMIT V029 ARG\r',b'BATCH RUN FINISHED',60),(b'',prompt,30),
              (b'TIME /PROVIDER\r',prompt,30),(b'RSX LOAD ZPRTC\r',prompt,30),
              (b'TIME /PROVIDER\r',prompt,30),(b'TIME\r',prompt,30),
              (b'RSX UNLOAD ZPRTC\r',prompt,30),(b'TIME /PROVIDER\r',prompt,30),
              (b'CPX UNLOAD RCP\r',prompt,30),(b'CPX LIST\r',prompt,30),
              (b'CPX LOAD RCP\r',prompt,30),(b'DIR /VER\r',prompt,30),
              (b'RSX LOAD ANSISCRN\r',prompt,30),(b'RSX LOAD ANSI\r',prompt,30),
              (b'RSX LIST\r',prompt,30),(b'RSX UNLOAD ANSI\r',prompt,30),
              (b'RSX UNLOAD ANSISCRN\r',prompt,30),(b'RSX LIST\r',prompt,30),
              (b'BYE /Y\r',b'System halted',30)]
    trace=session(sim,w/'disks',steps,w/'transcript.bin')
    for name in ('VER','TIME','SUBMIT','CPX','RSX'):assert banner(name).encode() in trace,name
    assert trace.index(b'PARAMETER CONTENT PASSED')<trace.index(b'BATCH RUN FINISHED')
    assert trace.count(b'No TIME provider is loaded')==2
    assert b'Provider: ZPRTC' in trace and re.search(rb'\d{4}-\d{2}-\d{2}',trace),trace[-5000:]
    assert b'No CPXs loaded' in trace and banner('DIR',resident=True).encode() in trace
    assert b'ANSI : BDOS 255' in trace and b'ANSISCRN : BDOS 255' in trace
    assert b'No RSXs loaded' in trace and b'TPA available: 53K' in trace
    assert b.read_bytes()==before,'batch changed input disk'
    raw=directory(w/'disks/drivea.dsk',w/'diskdefs')
    assert not any(raw[i]<32 and bytes(x&127 for x in raw[i+1:i+12])==b'$$$     SUB' for i in range(0,len(raw),32)),'batch queue not removed'
    shipped=audit(base,report,w,w/'disks/drivea.dsk')
    r=subprocess.run(['fsck.cpm','-T','raw','-f','bettercpm-default','-n',str(b)],cwd=w,capture_output=True,check=True)
    (w/'filesystem-b.txt').write_bytes(r.stdout+r.stderr)
    (w/'result.json').write_text(json.dumps({'status':'PASS','runner_sha256':sha(Path(__file__)),'baseline_sha256':report['sha256'],'simulator_sha256':sha(sim),'unchanged_shipped_files':shipped,'scope':'shipped identities, SUBMIT parameter/order/physical EOF/queue cleanup, TIME discovery/read, CPX unload/reload and monitor RSX load/unload/53K'},indent=2)+'\n')
    print('PASS shipped SUBMIT TIME VER CPX RSX workflows',w)

if __name__=='__main__':main()
