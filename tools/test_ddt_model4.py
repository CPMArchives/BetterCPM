#!/usr/bin/env python3
"""Qualify DDT's real Model 4 field rendering, debugger input and warm boot."""
import argparse,hashlib,json,subprocess
from pathlib import Path
from build_ddt import ROOT
from add_cpm_file_to_dmk import extract_raw,add_file,FILESYSTEM_FIRST_SECTOR,SECTOR_SIZE,DIRECTORY_ENTRIES
from build_montezuma_extended_790k import build
from run_trs80_command import DEFAULT_EMULATOR,key_args
from trs80gp_launch import run


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--image',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=False);w=a.output.resolve();original=a.image.read_bytes();raw=extract_raw(original)
    directory=FILESYSTEM_FIRST_SECTOR*SECTOR_SIZE
    for i in range(DIRECTORY_ENTRIES):
        at=directory+i*32
        if raw[at]==0 and bytes(v&127 for v in raw[at+1:at+12]) in (b'DDT     COM',b'STARTUP SUB',b'DDONE   COM'):raw[at]=0xe5
    data=(ROOT/'build/utilities/DDT.COM').read_bytes();add_file(raw,'DDT.COM',data)
    add_file(raw,'DDONE.COM',bytes.fromhex('110b010e09cd0500c30000')+b'DDT RETURNED$')
    add_file(raw,'STARTUP.SUB',b'DDT /VER\r\nDDT\r\nDDONE\r\n\x1a')
    image=w/'private.dmk';image.write_bytes(build(raw));cmd=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-ktx','-d0',str(image),'-itime','20000'];stages=[]
    def capture(label,wait):stages.append(label);cmd.extend(['-iw',wait,'-id','120','-it'])
    capture('prompt','-_')
    cmd+=key_args('H100,2X',delay=25);capture('edit','-H100,2X_')
    cmd+=key_args('\x7f0\r',delay=25);capture('arithmetic','0120 00E0')
    cmd+=key_args('F300,30F,41\rS300\r',delay=25);capture('substitute','0300 41 _')
    cmd+=key_args('99',delay=25);capture('pending','0300 41 99_')
    cmd+=['-ik','6','2','-id','25','-ik','6','0','-id','25']
    capture('cancel','-_')
    cmd+=key_args('D300,300\r',delay=25);capture('unchanged','0300 41 A')
    cmd+=key_args('A400\rMVI A,5\rRET\r.\rL400,402\r',delay=25);capture('assembly','0402  RET')
    cmd+=key_args('G0\r',delay=25)+['-iw','DDT RETURNED','-id','120','-it','-ix'];stages.append('returned')
    (w/'invocation.json').write_text(json.dumps(cmd,indent=2)+'\n');run(cmd,cwd=w,timeout=180)
    files=sorted(w.glob('trs80-text-*.bin'),key=lambda f:int(f.stem.rsplit('-',1)[1]));assert len(files)==len(stages),(len(files),stages)
    screens={name:bytes(c&127 for c in f.read_bytes()[:1920]) for name,f in zip(stages,files)}
    for name,value in screens.items():(w/(name+'.txt')).write_text('\n'.join(value[i:i+80].decode('ascii').rstrip() for i in range(0,1920,80))+'\n')
    for label,needle in [('prompt',b'DDT 1.0 (Build 001)'),('edit',b'-H100,2X_'),('arithmetic',b'0120 00E0'),('substitute',b'0300 41 _'),('pending',b'0300 41 99_'),('unchanged',b'0300 41 A'),('assembly',b'0402  RET'),('returned',b'DDT RETURNED')]:assert needle in screens[label],(label,needle)
    # Escape removes provisional text from its original address-prefix row.
    assert b'0300 41 99' not in screens['cancel']
    assert a.image.read_bytes()==original
    report={'status':'PASS','program_sha256':hashlib.sha256(data).hexdigest(),'baseline_sha256':hashlib.sha256(original).hexdigest(),'stages':stages,'scope':'Native Model 4 execution: startup /VER, prefix/caret editing and physical DEL, arithmetic, physical CLEAR cancellation without operand commit, A/L commands, and G0 return through SUBMIT. Baseline unchanged.'}
    (w/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(w)


if __name__=='__main__':main()
