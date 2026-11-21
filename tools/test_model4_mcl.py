#!/usr/bin/env python3
"""Native Model 4 MCL boot, full-TPA reconstruction and error cancellation."""
import shutil
import argparse
from pathlib import Path
from add_cpm_file_to_dmk import extract_raw
from build_montezuma_extended_790k import build
from test_disk_utilities import ROOT,medium,keys
from test_submit_xsub import marker
from test_config_startup_read import screen
from startup_record import build as record
from system_layout import LAYOUT as L
from run_trs80_command import DEFAULT_EMULATOR
from trs80gp_launch import run

OUT=ROOT/'build/test-results/model4-mcl'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case")
    selected_case=parser.parse_args().case
    shutil.rmtree(OUT,ignore_errors=True);OUT.mkdir(parents=True)
    fit=(bytes.fromhex('1109010e09cd0500c9')+b'FULL MCL FIT\r\n$').ljust(54144,b'\x76')
    extras=[('MARK.COM',marker(OUT)),('JPZERO.COM',b'\xc3\0\0'),
            ('FNZERO.COM',b'\x0e\0\xcd\x05\0\xc9'),('FIT.COM',fit),
            ('OVER.COM',fit+bytes(128)),('STAT.COM',(ROOT/'build/utilities/STAT.COM').read_bytes())]
    raw=extract_raw(medium(extras));raw[128:384]=record('MARK START;TAIL',system_base=L['SYSTEM'],mcl=1)
    image=build(bytes(raw))
    cases=[('sequence','MARK One;MARK "Two;2";;MARK THREE','MARK: THREE',('MARK: ONE','MARK: "TWO;2"','MARK: THREE')),
           ('returns','JPZERO;FNZERO;MARK RETURN','MARK: RETURN',('MARK: RETURN',)),
           ('syntax','MARK FIRST;MARK "bad','MCL invalid.',('MCL invalid.',)),
           ('unknown','MISSING;MARK NEVER','?',('? ',)),
           ('full-fit','FIT;MARK AFTERFIT','MARK: AFTERFIT',('FULL MCL FIT','MARK: AFTERFIT')),
           ('overflow','OVER;MARK NEVER','FILE WILL NOT FIT',('FILE WILL NOT FIT',)),
           ('memory','STAT MEM','Maximum loadable COM:',('MCL 128','54144 bytes'))]
    for name,command,completion,expected in cases:
        if selected_case and selected_case!=name:continue
        work=OUT/name;work.mkdir();disk=work/'a.dmk';disk.write_bytes(image)
        # Bounded captures avoid missing short-lived text between batch waits.
        args=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-d0',str(disk),
              '-id','15000','-it']
        args+=keys(command+'\r')+['-id','60000' if name in ('full-fit','overflow') else '30000',
                                  '-it','-ix']
        run(args,cwd=work,check=True,timeout=240)
        boot=screen(work/'trs80-text-0.bin');text=screen(work/'trs80-text-1.bin')
        (work/'screen.txt').write_text(text)
        assert 'MARK: START;TAIL' in boot,boot
        for phrase in expected:
            if phrase=='? ':assert '?' in text,text
            else:assert phrase in text,(name,phrase,text)
        if name in ('syntax','unknown','overflow'):
            assert 'MARK: NEVER' not in text and 'MARK: FIRST' not in text,text
        assert disk.read_bytes()==image,'read-only MCL execution changed media'
        print('PASS native Model 4 MCL '+name,flush=True)


if __name__=='__main__':main()
