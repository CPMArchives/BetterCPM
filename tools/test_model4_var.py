#!/usr/bin/env python3
"""Native Model 4 VAR startup, warm/full-COM lifetime and memory accounting."""
import shutil
import argparse
from add_cpm_file_to_dmk import extract_raw
from build_montezuma_extended_790k import build
from test_disk_utilities import ROOT,medium,keys
from test_submit_xsub import marker
from test_config_startup_read import screen
from startup_record import build as record
from system_layout import LAYOUT as L
from run_trs80_command import DEFAULT_EMULATOR
from trs80gp_launch import run

OUT=ROOT/'build/test-results/model4-var'


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--case')
    selected=parser.parse_args().case
    shutil.rmtree(OUT,ignore_errors=True);OUT.mkdir(parents=True)
    fit=(bytes.fromhex('1109010e09cd0500c9')+b'VAR FULL FIT\r\n$').ljust(54016,b'\x76')
    extras=[('MARK.COM',marker(OUT)),('JPZERO.COM',b'\xc3\0\0'),
            ('FIT.COM',fit),('OVER.COM',fit+bytes(128)),
            ('STAT.COM',(ROOT/'build/utilities/STAT.COM').read_bytes())]
    raw=extract_raw(medium(extras))
    raw[128:384]=record('VAR BOOT=START',system_base=L['SYSTEM'],mcl=1,variables=1)
    image=build(bytes(raw))
    cases=[('warm-full','VAR X=ONE;MARK %x%;JPZERO;MARK %BOOT%;FIT;MARK %BOOT%',
            ('MARK: ONE','VAR FULL FIT','MARK: START')),
           ('undefined','VAR X=ONE;VAR /D X;MARK %X%;MARK NEVER',('VAR undefined.',)),
           ('overflow','OVER;MARK NEVER',('FILE WILL NOT FIT',)),
           ('memory','STAT MEM',('HISTORY 192; MCL 128; VAR 128','54016 bytes','08704 CCP image'))]
    for name,command,expected in cases:
        if selected and selected!=name:continue
        work=OUT/name;work.mkdir();disk=work/'a.dmk';disk.write_bytes(image)
        args=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-d0',str(disk),'-id','15000','-it']
        args+=keys(command+'\r')+['-id','60000' if name in ('warm-full','overflow') else '30000','-it','-ix']
        run(args,cwd=work,check=True,timeout=240)
        text=screen(work/'trs80-text-1.bin');(work/'screen.txt').write_text(text)
        for phrase in expected:assert phrase in text,(name,phrase,text)
        assert 'MARK: NEVER' not in text,text
        if name=='warm-full':assert text.count('MARK: START')==2,text
        assert disk.read_bytes()==image,'VAR execution changed read-only media'
        print('PASS native Model 4 VAR '+name,flush=True)


if __name__=='__main__':main()
