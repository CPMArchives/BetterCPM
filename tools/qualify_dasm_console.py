#!/usr/bin/env python3
"""Real console input/backspace, two-page listing and confirmed output abort."""
import argparse
import json
from pathlib import Path
from build_dasm import build
from dasm_native import campaign,DEFAULT_SYSTEM


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--system',type=Path,default=DEFAULT_SYSTEM)
    p.add_argument('--utilities',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--work-candidate',action='store_true',help='diagnostic work-disk candidate, not packaged acceptance')
    p.add_argument('--platforms',nargs='+',choices=['z80pack','trs80gp'],default=['z80pack','trs80gp'])
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    image=build(Path.home()/'bin/z80asm',a.output/'cross')
    report={'scope':'ordinary console/keyboard; no scripted function-10 input','platforms':{}}
    for platform in a.platforms:
        prompt=b'A0>_ ' if platform=='trs80gp' else b'C0>_ '
        steps=[(b'B:DASM\r',b'\r\n*',30),(b'RTINX\x08Y.COM\r',b'\r\n*',30),
            (b'N4\r',b'\r\n*',30),(b'L=2\r',b'\r\n*',30),
            (b'L100\r',b'\r\n*',30),(b'L\r',b'\r\n*',30),
            (b'RLONG.COM\r',b'\r\n*',30),(b'N1000\r',b'\r\n*',30),
            (b'SABORT.ASM\rY',b'\r\n*',30),(b'P100,1100\r',b'\r\n*',30),
            (b'QL100,1100\r',b'QL100,1100\r\r\n',30),(b'\x03Y',prompt,60),(b'VER /B\r',prompt,30)]
        frames=[1200,300,180,180,300,300,600,180,300,300,0,1800,300]
        commands=['A:RSX LOAD ZPRTC','A:RSX LIST','B:DASM /VER'] if platform=='z80pack' else ['RSX LIST','B:DASM /VER']
        if a.work_candidate:steps=[(b'DASM\r' if c==b'B:DASM\r' else c,w,t) for c,w,t in steps]
        files={'TINY.COM':b'\0\0\0\xc9','LONG.COM':bytes(4096),'ABORT.ASM':b'KEEP ORIGINAL'}
        if a.work_candidate:files['DASM.COM']=image
        log,out=campaign(platform,files,
            commands,a.output/platform,system=a.system,utilities=a.utilities,interactive=steps,
            interactive_frames=frames,extract=['ABORT.ASM'],utility_files=None if a.work_candidate else {'DASM.COM':image})
        assert out['ABORT.ASM'].startswith(b'KEEP ORIGINAL')
        assert b'cancelled; output not published' in log.lower(),log[-4000:]
        assert b'0100' in log and b'0101' in log and b'0102' in log and b'0103' in log
        assert b'outside loaded input' not in log and b'Command Error' not in log,log[-4000:]
        if platform=='z80pack':assert b'ZPRTC' in log and b'51K' in log
        else:assert b'M4SCRN' in log and b'ADM3A' in log
        report['platforms'][platform]={'status':'DIAGNOSTIC_PASS' if a.work_candidate else 'PASS','backspace':True,'successive_two_line_pages':True,
            'confirmed_ctrl_c':True,'original_output_preserved':True,'ordinary_console_input':True,
            'resident_profile':'M4SCRN+ADM3A' if platform=='trs80gp' else 'ZPRTC',
            'execution_report':platform+'/execution.json'}
        (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        print('PASS',platform,'ordinary console backspace/paging, output cancellation and CCP return',flush=True)
if __name__=='__main__':main()
