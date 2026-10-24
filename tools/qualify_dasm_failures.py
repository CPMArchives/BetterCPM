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
            def prefill(raw,definition,folder):
                # Preallocate most free data through cpmtools; the native helper
                # still performs real sequential writes until BDOS reports full.
                import subprocess,re,hashlib
                listing=subprocess.run(['cpmls','-T','raw','-f',definition,'-D',str(raw)],cwd=folder,check=True,capture_output=True).stdout
                free=int(re.search(rb'(\d+)K Free',listing)[1])*1024
                amount=max(0,(free-16384)//2048*2048)
                payload=bytes([0xa5])*amount
                host=folder/'PREFILL.DAT';host.write_bytes(payload)
                subprocess.run(['cpmcp','-T','raw','-f',definition,str(raw),str(host),'0:PREFILL.DAT'],cwd=folder,check=True,capture_output=True)
                subprocess.run(['fsck.cpm','-T','raw','-f',definition,'-n',str(raw)],cwd=folder,check=True,capture_output=True)
                (folder/'prefill.json').write_text(json.dumps({'bytes':amount,'sha256':hashlib.sha256(payload).hexdigest(),'native_remaining_bytes_at_most':16384},indent=2)+'\n')
            log,out=campaign(platform,files,['QFAULT'],w,system=a.system,utilities=a.utilities,
                setup=prefill if kind=='data' else None,
                extract=['KEEP.ASM'],utility_files={'DASM.COM':image})
            assert b'DASM FILESYSTEM FIXTURE READY' in log and b'DASM FILESYSTEM FIXTURE FAILED' not in log,log[-3000:]
            assert b'DASM RESIDENT CANARY PASS' in log and b'DASM RESIDENT CANARY FAIL' not in log,log[-3000:]
            expected=b'read-only' if kind in ('file-ro','media-ro') else b'I/O failed'
            assert expected in log,log[-3000:]
            assert out['KEEP.ASM'][:13]==b'KEEP ORIGINAL' and 13<=len(out['KEEP.ASM'])<=128 and set(out['KEEP.ASM'][13:])<={0,26}
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
