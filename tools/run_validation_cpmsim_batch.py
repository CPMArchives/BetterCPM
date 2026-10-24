#!/usr/bin/env python3
"""Validate durable batch continuation and supplemental XSUB full-TPA input."""
import argparse,json,shutil,subprocess
from pathlib import Path
from run_validation_cpmsim_ren import audit
from run_validation_returning import sha
from test_z80pack_attributes import directory
from test_z80pack_sysgen_install import session
from test_submit_xsub import full_program
from test_z80pack_submit_xsub import input_probe


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('baseline','build-root','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False);base=a.baseline.resolve();report=json.loads((base/'report.json').read_text())
    sim=Path.home()/'projects/git/z80pack/cpmsim/cpmsim';results=[]
    for xsub in (False,True):
        w=a.output.resolve()/('xsub' if xsub else 'ordinary');(w/'disks').mkdir(parents=True)
        for letter in 'ab':shutil.copy2(base/report['image'],w/'disks'/f'drive{letter}.dsk')
        shutil.copy2(base/'diskdefs',w/'diskdefs');shutil.copy2(__file__,w/'executed-runner.py')
        def put(letter,user,name,data):
            f=w/('fixture-'+name);f.write_bytes(data)
            subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(w/'disks'/f'drive{letter}.dsk'),str(f),f'{user}:{name}'],cwd=w,check=True,capture_output=True)
        put('b',3,'DONE.TXT',b'BATCH RETURN COMPLETED\r\n\x1a')
        program='FULLIN' if xsub else 'FULLTPA';binary=full_program(w,xsub);put('a',0,program+'.COM',binary)
        extras={}
        if xsub:
            for name,part in [('XSUB.COM','utilities'),('BATCHIO.RSX','rsx')]:
                source=a.build_root/'build'/part/name;put('a',0,name,source.read_bytes());extras[name]=sha(source)
        if xsub:
            probe=input_probe(w);put('a',0,'INPUT.COM',probe)
            # Proof-only variant prints the same result, then requests BDOS 0.
            boot=bytearray(probe);off=boot.index(bytes.fromhex('0e09cd0500c9'))+2
            boot[off:off+3]=bytes((0xc3,))+ (0x100+len(boot)).to_bytes(2,'little')
            boot+=bytes.fromhex('cd05000e00c30500');put('a',0,'INPUT0.COM',boot)
        script=(b'XSUB\r\n' if xsub else b'')+program.encode()+b'\r\n'+(b'BATCHFULL\r\n' if xsub else b'')+b'TYPE B3:DONE.TXT\r\n\x1a'
        put('a',0,'V031.SUB',script);before=(w/'disks/driveb.dsk').read_bytes()
        steps=[(b'SUBMIT V031\r',b'BATCH RETURN COMPLETED',90),(b'',b'A0>_ ',30),(b'RSX LIST\r',b'A0>_ ',30)]
        if xsub:steps += [(b'INPUT\rBATCHFULL\r',b'INPUT OK',30),(b'',b'A0>_ ',30),(b'RSX LIST\r',b'A0>_ ',30),
                          (b'INPUT0\rBATCHFULL\r',b'INPUT OK',30),(b'',b'A0>_ ',30),(b'RSX LIST\r',b'A0>_ ',30)]
        steps += [(b'BYE /Y\r',b'System halted',30)]
        trace=session(sim,w/'disks',steps,w/'transcript.bin')
        assert (b'FULLIN OK' if xsub else b'FULLTPA OK') in trace and b'FAILED' not in trace
        assert b'TPA available: 53K' in trace,trace[-3000:]
        if xsub:assert b'BATCHIO : BDOS 10' in trace and b'TPA available: 51K' in trace and b'No RSXs loaded' in trace
        assert (w/'disks/driveb.dsk').read_bytes()==before
        raw=directory(w/'disks/drivea.dsk',w/'diskdefs')
        assert not any(raw[i]<32 and bytes(v&127 for v in raw[i+1:i+12])==b'$$$     SUB' for i in range(0,len(raw),32))
        shipped=audit(base,report,w,w/'disks/drivea.dsk')
        r={'status':'PASS','xsub':xsub,'probe_bytes':len(binary),'probe_sha256':sha(w/('fixture-'+program+'.COM')),
           'contract_finding':None,'supplemental_nonmanifest_files':extras,'baseline_sha256':report['sha256'],'runner_sha256':sha(Path(__file__)),
           'simulator_sha256':sha(sim),'unchanged_shipped_files':shipped}
        (w/'result.json').write_text(json.dumps(r,indent=2)+'\n');results.append(r);print(program,'PASS',w,flush=True)
    (a.output/'result.json').write_text(json.dumps({'status':'PASS','cases':results},indent=2)+'\n')

if __name__=='__main__':main()
