#!/usr/bin/env python3
"""Qualify production PIP disk transfer and device admission on Model 4."""
from pathlib import Path
import tempfile,subprocess
from test_sysgen_install import setup_program
from test_disk_utilities import medium
from build_montezuma_extended_790k import build,RAW_SIZE
from add_cpm_file_to_dmk import extract_raw
from run_trs80_command import DEFAULT_EMULATOR,key_args
from trs80gp_launch import run
ROOT=Path(__file__).resolve().parents[1]
def main():
    report=ROOT/'build/test-results/pip-model4';report.mkdir(parents=True,exist_ok=True)
    import test_sysgen_install
    test_sysgen_install.OUT=report
    payload=b'MODEL FOUR PIP TRANSFER\r\n'+b'V'*500+b'\x1a'
    with tempfile.TemporaryDirectory(prefix='pip-model4-') as t:
        w=Path(t);source=medium([('PIO.COM',(ROOT/'build/utilities/PIP.COM').read_bytes()),('SRC.TXT',payload),('SETBSYS.COM',setup_program())])
        (w/'source.dmk').write_bytes(source);(w/'target.dmk').write_bytes(build(b'\xe5'*RAW_SIZE))
        args=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-d0',str(w/'source.dmk'),'-d1',str(w/'target.dmk'),'-id','4000']
        for command,delay in [('SETBSYS\r',3500),('PIO B3:OUT.TXT=A0:SRC.TXT[V]\r',15000),('PIO CRT:=SRC.TXT\r',5000),('PIO LPT:=SRC.TXT\r',3500),('PIO B3:BAD.TXT=PTR:\r',3500),('PIO /VER\r',3500)]:
            args+=key_args(command)+['-id',str(delay),'-it']
        args+=['-ix'];run(args,cwd=w,timeout=180,check=True)
        screens=[]
        for i,p in enumerate(sorted(w.glob('trs80-text-*.bin'),key=lambda p:int(p.stem.rsplit('-',1)[1]))):
            raw=p.read_bytes()[:1920];txt='\n'.join(bytes(c&127 for c in raw[x:x+80]).decode('ascii').rstrip() for x in range(0,1920,80));screens.append(txt);(report/f'{i}.txt').write_text(txt)
        assert 'A0>' in screens[1] and 'ERROR' not in screens[1],screens[1]
        assert 'MODEL FOUR PIP TRANSFER' in screens[2],screens[2]
        assert 'DEVICE UNAVAILABLE' in screens[3] and 'DEVICE UNAVAILABLE' in screens[4],screens[3:5]
        assert 'Build 026' in screens[5],screens[5]
        assert (w/'source.dmk').read_bytes()==source,'source changed'
        raw=w/'target.img';raw.write_bytes(extract_raw((w/'target.dmk').read_bytes()))
        (w/'diskdefs').write_text('diskdef bettercpm-default\n seclen 512\n tracks 160\n sectrk 10\n blocksize 2048\n maxdir 128\n skew 1\n boottrk 4\n os 2.2\nend\n')
        out=w/'OUT.TXT';subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(raw),'3:OUT.TXT',str(out)],cwd=w,check=True)
        assert out.read_bytes()==payload.ljust(640,b'\x1a'),len(out.read_bytes())
        listing=subprocess.check_output(['cpmls','-T','raw','-f','bettercpm-default',str(raw)],cwd=w).decode().lower()
        assert 'bad.txt' not in listing and 'out.$$$' not in listing,listing
    print('PASS: Model 4 verified multi-DU disk copy, CRT output, unavailable-device preflight and /VER')
if __name__=='__main__':main()
