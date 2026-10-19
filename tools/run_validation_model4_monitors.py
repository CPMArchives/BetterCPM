#!/usr/bin/env python3
"""Exercise shipped monitor personalities against a qualified Model 4 image."""
import argparse,json,shutil,tempfile,subprocess
from pathlib import Path
from add_cpm_file_to_dmk import extract_raw,add_file,FILESYSTEM_FIRST_SECTOR,SECTOR_SIZE,DIRECTORY_ENTRIES
from build_montezuma_extended_790k import build
from run_validation_model4 import sha,audit_files
from run_trs80_command import DEFAULT_EMULATOR,key_args
from trs80gp_launch import run


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('baseline','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--monitor',choices=('ADM3A','VT52','ANSI'),required=True)
    p.add_argument('--scripted-start',action='store_true',help='replace only STARTUP.SUB with the private exercise queue to avoid host SUBMIT entry timing')
    p.add_argument('--audit-only',type=Path,help='check retained captures without relaunching or changing the test image')
    a=p.parse_args();report=json.loads((a.baseline/'report.json').read_text())
    original=a.baseline/report['image'];assert report['target']=='trs80gp' and sha(original)==report['sha256']
    a.output.mkdir(parents=True,exist_ok=True);w=a.audit_only.resolve() if a.audit_only else Path(tempfile.mkdtemp(prefix=a.monitor.lower()+'-',dir=a.output.resolve()))
    if not a.audit_only:shutil.copy2(__file__,w/'executed-runner.py')
    program={'ADM3A':'ADMTST','VT52':'VT52TST','ANSI':'ANSITST'}[a.monitor]
    image=w/'a.dmk';marker='MONITOR REGRESSION FINISHED'
    if not a.audit_only:
        raw=extract_raw(original.read_bytes())
        # Preserve shipped providers. Default entry keeps STARTUP.SUB intact;
        # scripted entry explicitly replaces it with a private test queue.
        script=['RSX UNLOAD ADM3A','RSX UNLOAD M4SCRN','RSX LOAD M4SCRN',
                'RSX LOAD '+a.monitor,'RSX LIST',program,'RSX UNLOAD '+a.monitor,
                'RSX UNLOAD M4SCRN','RSX LIST','MREGDONE']
        if a.scripted_start:
            script.insert(script.index(program),'MREGWAIT')
            add_file(raw,'MREGWAIT.COM',bytes.fromhex('1110010e09cd05000e01cd0500c30000')+b'MREG READY$')
            for index in range(DIRECTORY_ENTRIES):
                at=FILESYSTEM_FIRST_SECTOR*SECTOR_SIZE+index*32
                if raw[at]==0 and raw[at+1:at+12]==b'STARTUP SUB':raw[at]=0xE5
            add_file(raw,'STARTUP.SUB',(':VER /BANNER\r\n'+'\r\n'.join(script)+'\r\n\x1a').encode())
        add_file(raw,'MREG.SUB',('\r\n'.join(script)+'\r\n\x1a').encode())
        add_file(raw,'MREGDONE.COM',bytes.fromhex('110b010e09cd0500c30000')+('\r\n'+marker+'\r\n$').encode())
        image.write_bytes(build(bytes(raw)))
    cmd=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-ktx','-d0',str(image),'-itime','15000',
         '-iw','Type TYPE README.TXT for more','-id','6000']+( [] if a.scripted_start else key_args('SUBMIT MREG\r',delay=25))
    stages=[]
    def capture(label,*wait):
        stages.append(label)
        for text in wait:cmd.extend(['-iw',text])
        cmd.extend(['-id','120','-it'])
    capture('loaded','TPA available:')
    if a.scripted_start:cmd+=['-iw','MREG READY']+key_args(' ',delay=60)
    capture('position','Marker: row 5','Press a key to continue.')
    cmd+=key_args(' ',delay=60)
    capture('reset','Parser reset:','Press a key to continue.')
    if a.monitor=='ADM3A':
        cmd+=key_args(' ',delay=60);capture('movement','TAB should put','Press a key to continue.')
        cmd+=key_args(' ',delay=60);capture('video','Cursor OFF/ON query passed.','Press a key to continue.')
        cmd+=key_args(' ',delay=60)+['-iw','No ENTER is required.']+key_args('A:[]',delay=60)
        capture('keyboard','ADMTST keyboard checks passed.')
    elif a.monitor=='VT52':
        cmd+=key_args(' ',delay=60);capture('erase','VT52 erase tests:','Press a key to continue.')
        cmd+=key_args(' ',delay=60)
    else:cmd+=key_args(' ',delay=60)
    capture('unloaded','No RSXs loaded','TPA available: 53K',marker)
    cmd+=['-ix']
    if not a.audit_only:
        (w/'invocation.json').write_text(json.dumps(cmd,indent=2)+'\n')
        run(cmd,cwd=w,timeout=900)
    files=sorted(w.glob('trs80-text-*.bin'));assert len(files)==len(stages),(files,stages)
    pages={label:path.read_bytes()[:1920] for label,path in zip(stages,files)}
    text={label:bytes(c&127 for c in page) for label,page in pages.items()}
    for label,page in text.items():(w/(label+'.txt')).write_text('\n'.join(page[i:i+80].decode('ascii').rstrip() for i in range(0,1920,80))+'\n')
    assert a.monitor.encode() in text['loaded'] and b'M4SCRN' in text['loaded']
    assert text['position'][410:434]==b'Marker: row 5, column 10'
    assert b'Parser reset:' in text['reset'] and b'readable' in text['reset']
    if a.monitor=='ADM3A':
        assert pages['movement'][160:164]==b'LEFT' and pages['movement'][248:250]==b'AB'
        assert pages['movement'][320:325]==b'RIGHT'
        v=pages['video'];assert v[87:89]==bytes([ord('O')|128,ord('N')|128]) and v[90:93]==b'OFF'
        assert v[800:806]==b'LINE A' and v[880:960]==b' '*80
        assert v[960:966]==b'LINE C' and v[1040:1046]==b'LINE D'
        assert b'ADMTST keyboard checks passed.' in text['keyboard']
    elif a.monitor=='VT52':
        assert text['position'][568:570]==b'AB' and text['position'][878:880]==b'AC'
        assert text['erase'][320:400]==b'EOL KEEP'+b' '*72
        assert text['erase'][480:560]==b'EOS KEEP'+b' '*72
    else:
        v=pages['position'];assert text['position'][560:581]==b'Normal Reverse Normal'
        assert all(c&128 for c in v[567:574]) and not any(c&128 for c in v[560:566])
        assert text['position'][720:800].rstrip()==b'Erase KEEP'
    assert b'No RSXs loaded' in text['unloaded'] and b'TPA available: 53K' in text['unloaded'] and marker.encode() in text['unloaded']
    audit_root=w if not (w/'file-audit').exists() else Path(tempfile.mkdtemp(prefix='reaudit-',dir=w))
    audit_report=dict(report,included=[f for f in report['included'] if not (a.scripted_start and f['name']=='STARTUP.SUB')])
    audit=audit_files(original,image,audit_report,audit_root)
    check=subprocess.run(['fsck.cpm','-T','raw,pcw800','-f','bettercpm-default','-n',str(audit_root/'file-audit/after.raw')],cwd=audit_root/'file-audit',capture_output=True,text=True)
    (w/'filesystem.txt').write_text(check.stdout+check.stderr);assert check.returncode==0
    assert sha(original)==report['sha256']
    (w/'result.json').write_text(json.dumps({'status':'PASS','monitor':a.monitor,'baseline_sha256':report['sha256'],
        'emulator_sha256':sha(DEFAULT_EMULATOR),'executed_runner_sha256':sha(w/'executed-runner.py'),'audit_runner_sha256':sha(Path(__file__)),'stages':stages,'system_file_audit':audit,
        'startup_fixture_replaced':a.scripted_start,'filesystem_status':check.returncode,'scope':'shipped Model 4 monitor/backend pair; selected screen-memory assertions and unload/53K; no audible bell or exhaustive protocol claim'},indent=2)+'\n')
    print(w,flush=True)


if __name__=='__main__':main()
