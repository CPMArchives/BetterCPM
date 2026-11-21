#!/usr/bin/env python3
"""Native Model 4 CONFIG saved-composition and cold/warm accounting checks."""
from pathlib import Path
import shutil
from add_cpm_file_to_dmk import extract_raw
from build_montezuma_extended_790k import build
from test_disk_utilities import ROOT, medium, keys
from test_config_startup_read import screen
from run_trs80_command import DEFAULT_EMULATOR
from trs80gp_launch import run
from startup_record import build as record, choices, parse
from system_layout import LAYOUT as L

OUT=ROOT/'build/test-results/config-pds'


def launch(name, image, steps):
    work=OUT/name; work.mkdir()
    disk=work/'a.dmk'; disk.write_bytes(image)
    args=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-d0',str(disk),'-id','3000','-iw','A0>','-id','1000','-it']
    for command, completion in steps:
        args+=keys(command)+['-iw',completion,'-id','1000','-it']
    args+=['-it','-ix']
    run(args,cwd=work,check=True,timeout=240)
    captures=sorted(work.glob('trs80-text-*.bin'),key=lambda p:int(p.stem.rsplit('-',1)[1]))
    text=screen(captures[-1])
    (work/'screen.txt').write_text(text)
    return disk.read_bytes(),text


def main():
    shutil.rmtree(OUT,ignore_errors=True); OUT.mkdir(parents=True)
    # VER exercises coexistence with the saved startup domain.
    original=extract_raw(medium((('STAT.COM',(ROOT/'build/utilities/STAT.COM').read_bytes()),)))
    original[128:384]=record('VER',system_base=L['SYSTEM'])
    image=build(bytes(original))
    saved,text=launch('save-expanded',image,[
        ('CONFIG\r','Your choice:'),('F','^C Return'),
        ('A','Pending choices H/M/V: 3 0 0'),('B','Pending choices H/M/V: 3 1 0'),
        ('C','Pending choices H/M/V: 3 1 1'),('C','Pending choices H/M/V: 3 1 2'),
        ('C','Pending choices H/M/V: 3 1 3'),
        ('\x03','Configuration options:'),('S','Save pending cold-boot changes only'),
        ('A','(Y/N)?'),('Y','Pending cold-boot changes saved and verified.')])
    raw=extract_raw(saved)
    assert choices(raw[128:384],system_base=L['SYSTEM'])==(3,1,3)
    assert parse(raw[128:384],system_base=L['SYSTEM'])=='VER'
    assert raw[:128]==original[:128] and raw[384:]==original[384:], 'pending save captured unrelated bytes'
    _,text=launch('cold-activates-saved',saved,[('CONFIG\r','Your choice:'),('F','^C Return')])
    # A fresh process is a true cold boot: it must now activate the saved owners.
    assert 'Active H/M/V bytes: 384 128 512' in text,text
    assert 'Saved choices H/M/V: 3 1 3' in text,text
    assert 'Next cold boot maximum COM (no RSXs): 53376' in text,text
    _,text=launch('expanded-stat',saved,[('STAT MEM\r','Maximum loadable COM:')])
    assert 'total 1036; metadata 12; HISTORY 384; MCL 128; VAR 512' in text,text
    assert '53376 bytes' in text,text
    # Reenter the settings domain after saving: saved/pending choices change
    # while active composition remains fixed. The worker fixture tests WBOOT.
    _,text=launch('save-keeps-active',image,[
        ('CONFIG\r','Your choice:'),('F','^C Return'),('B','Pending choices H/M/V: 2 1 0'),
        ('\x03','Configuration options:'),('S','Save pending cold-boot changes only'),
        ('A','(Y/N)?'),('Y','Pending cold-boot changes saved and verified.'),
        (' ','Save pending cold-boot changes only'),('\x03','Configuration options:'),
        ('F','^C Return')])
    assert 'Active H/M/V bytes: 192 0 0' in text,text
    assert 'Saved choices H/M/V: 2 1 0' in text,text
    print('PASS native CONFIG verified saved layout, startup preservation, cold activation, warm non-resize and STAT owner accounting')


if __name__=='__main__':
    main()
