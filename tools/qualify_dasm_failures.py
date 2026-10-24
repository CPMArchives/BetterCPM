#!/usr/bin/env python3
"""Qualify real directory/data-full and file/media read-only failures natively."""
import argparse
import json
from pathlib import Path
from build_dasm import build
from dasm_native import campaign,DEFAULT_SYSTEM
from dasm_script_harness import scripted
from dasm_native_faults import setup


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--system',type=Path,default=DEFAULT_SYSTEM)
    p.add_argument('--utilities',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--platforms',nargs='+',choices=['z80pack','trs80gp'],default=['z80pack','trs80gp'])
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    image=build(Path.home()/'bin/z80asm',a.output/'cross')
    report={'scope':'real private filesystem failure paths; no power-loss claim','platforms':{}}
    for platform in a.platforms:
        results={}
        for kind in ('directory','data','file-ro','media-ro'):
            dest='KEEP.ASM' if kind=='file-ro' else 'OUT.ASM'
            lines=['RTINY.COM','N80','S'+dest,'P100,180','QL100,180','Z','G']
            files={'TINY.COM':b'\xc9'*128,'KEEP.ASM':b'KEEP ORIGINAL',
                'QFAULT.COM':scripted(image,lines,setup_source=setup(kind),setup_entry='HF_START',cleanup_entry='HF_CLEAN')}
            w=a.output/platform/kind
            log,out=campaign(platform,files,['QFAULT'],w,system=a.system,utilities=a.utilities,
                extract=['KEEP.ASM'],utility_files={'DASM.COM':image})
            assert b'DASM FILESYSTEM FIXTURE READY' in log and b'DASM FILESYSTEM FIXTURE FAILED' not in log,log[-3000:]
            assert b'DASM RESIDENT CANARY PASS' in log and b'DASM RESIDENT CANARY FAIL' not in log,log[-3000:]
            expected=b'read-only' if kind in ('file-ro','media-ro') else b'I/O failed'
            assert expected in log,log[-3000:]
            assert out['KEEP.ASM'].startswith(b'KEEP ORIGINAL')
            # Probe exact output absence independently from console diagnostics.
            import subprocess
            definition='dasm-system' if platform=='trs80gp' else 'bettercpm-default'
            listing=subprocess.run(['cpmls','-T','raw','-f',definition,'system.raw'],cwd=w,check=True,capture_output=True).stdout.upper()
            assert b'OUT.ASM' not in listing,listing
            results[kind]={'status':'PASS','original_preserved':True,'output_unpublished':True,
                'resident_canary':True,'execution_report':str(w.relative_to(a.output)/'execution.json')}
            print('PASS',platform,kind,'real filesystem refusal/recovery',flush=True)
        report['platforms'][platform]={'status':'PASS','cases':results}
        (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
