#!/usr/bin/env python3
"""Disposable real-terminal TED integration gate; source/payload-bound evidence."""
import argparse
import hashlib
import json
from pathlib import Path
from build_ted import ROOT, build
from dasm_native import campaign, compact_source, cpm_text


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--system',type=Path,required=True)
    p.add_argument('--utilities',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--platforms',nargs='+',default=['z80pack','trs80gp'])
    p.add_argument('--cross-smoke',action='store_true')
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    image=build(Path.home()/'bin/z80asm',a.output/'cross')
    native=cpm_text(compact_source((a.output/'cross/TEDNAT.MAC').read_text().rstrip('\x1a')))
    original=b'Original\t spaces  \r\nLF\nCR\rend  '
    original+=b'\x1a'*(-len(original)%128)
    edited=b'X'+original[1:]
    post=bytes.fromhex('1109010e09cd0500c9')+b'TED EDITOR POSTEXIT PASS\r\n$'
    report={'status':'IN_PROGRESS','scope':'interactive startup/edit/save/exit integration gate; full acceptance separate',
            'payload_sha256':hashlib.sha256(image).hexdigest(),'platforms':{}}
    for platform in a.platforms:
        native_platform=platform=='trs80gp'
        files={'INPUT.TXT':original,'QPOST.COM':post}
        commands=(['RSX UNLOAD ADM3A','RSX LOAD ANSI'] if native_platform else
                  ['A:','RSX LOAD ANSISCRN','RSX LOAD ANSI','C:'])
        if a.cross_smoke:files['TEDDEV.COM']=image
        else:
            files['TEDNAT.MAC']=native
            commands=['B:ZSM4 TEDDEV=TEDNAT','B:LINK TEDDEV[A]']+commands
        sequence=[(b'S\r',b'^Z command',60),(b'X',b'Xriginal',90),
                  (b'\x0b',b'^K...',30),(b'S',b'replace? Y/N:',90),
                  (b'Y\r',b'Saved.',120),(b'\x0b',b'^K...',30),
                  (b'Q',b'TED EDITOR POSTEXIT PASS' if native_platform else b'C0>_ ',90)]
        if native_platform:interactive=sequence
        else:
            interactive=[(b'TEDDEV INPUT.TXT\r',b'TED>',60)]+sequence+[(b'QPOST\r',b'TED EDITOR POSTEXIT PASS',30)]
        log,outputs=campaign(platform,files,commands,a.output/platform,system=a.system,
            utilities=a.utilities,extract=['TEDDEV.COM','INPUT.TXT','TEB00000.BAK'],
            interactive=interactive,interactive_launch='TEDDEV INPUT.TXT' if native_platform else None,
            interactive_followup='QPOST',interactive_prompt='TED>',
            interactive_frames=[180,60,60,60,600,60,600] if native_platform else None,
            interactive_ready=['^Z command','Xriginal','^K...','replace? Y/N:','Saved.','^K...','TED EDITOR POSTEXIT PASS'] if native_platform else None)
        assert outputs['INPUT.TXT']==edited,(platform,outputs['INPUT.TXT'])
        assert outputs['TEB00000.BAK']==original
        assert outputs['TEDDEV.COM'][:len(image)]==image
        assert b'TED EDITOR POSTEXIT PASS' in log
        report['platforms'][platform]={'status':'PASS','native_build':not a.cross_smoke,
            'native_cross_parity':not a.cross_smoke,'execution':platform+'/execution.json'}
        (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        print('PASS',platform,'interactive editor integration',flush=True)
    report['status']='PASS';(a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
