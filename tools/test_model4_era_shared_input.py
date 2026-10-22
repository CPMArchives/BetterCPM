#!/usr/bin/env python3
"""Native ERA confirmation compatibility, protection and file-state checks."""
import argparse,hashlib,json,subprocess
from pathlib import Path
from test_disk_utilities import ROOT,medium
from test_model4_copy import files
from add_cpm_file_to_dmk import extract_raw
from build_montezuma_extended_790k import build
from run_trs80_command import DEFAULT_EMULATOR,key_args
from test_sysgen_install import screen
from trs80gp_launch import run


def main():
    p=argparse.ArgumentParser();p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    w=a.report.resolve();w.mkdir(parents=True,exist_ok=False)
    raw=extract_raw(medium([('ERA.COM',(ROOT/'build/utilities/ERA.COM').read_bytes()),
                            ('FIRST.DAT',b'FIRST MUST SURVIVE DECLINE\r\n'),
                            ('ROFILE.DAT',b'PROTECTED PAYLOAD\r\n')]))
    for at in range(20480,24576,32):
        if raw[at]==0 and bytes(c&127 for c in raw[at+1:at+12])==b'ROFILE  DAT':raw[at+9]|=128
    before=files(raw[20480:]);(w/'before.raw').write_bytes(raw)
    disk=w/'a.dmk';disk.write_bytes(build(raw));stages=[]
    cmd=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-ktx','-d0',str(disk),'-itime','30000','-id','5000']
    def capture(name,marker):
        stages.append(name);cmd.extend(['-iw',marker,'-id','120','-it'])
    def command(text):
        # Old questions remain in VRAM; remove them before matching a new one.
        cmd.extend(key_args('CLS\r',delay=25)+['-id','6000'])
        cmd.extend(key_args(text+'\r',delay=25))
    command(':ERA FIRST.DAT');capture('first','Erase? Y/N')
    # Original ERA treats physical CLEAR/ESC and Enter as invalid, not cancel.
    cmd+=['-ik','6','2','-id','25','-ik','6','0','-id','25']
    cmd+=key_args('\rX',delay=25)+['-id','500','-it'];stages.append('invalid')
    cmd+=key_args('N',delay=25);capture('decline','ERA cancelled.')
    cmd+=['-id','6000'];command(':ERA FIRST.DAT');capture('again','Erase? Y/N')
    cmd+=key_args('Y',delay=25);capture('erase','1 FILES ERASED')
    cmd+=['-id','6000'];command(':ERA ROFILE.DAT[$RO]');capture('readonly','Read only. Erase? Y/N')
    cmd+=key_args('N',delay=25);capture('protected','SKIPPED - PROTECTED')
    cmd+=['-id','6000'];command(':ERA ROFILE.DAT[$RO]');capture('cancel-question','Read only. Erase? Y/N')
    cmd+=key_args('\x03',delay=25);capture('cancel','ERA cancelled.')
    cmd+=['-id','6000','-it','-ix'];stages.append('returned')
    (w/'invocation.json').write_text(json.dumps(cmd,indent=2)+'\n');run(cmd,cwd=w,timeout=900)
    captures=sorted(w.glob('trs80-text-*.bin'),key=lambda p:int(p.stem.rsplit('-',1)[1]))
    assert len(captures)==len(stages),(len(captures),stages)
    texts={name:screen(path) for name,path in zip(stages,captures)}
    for name,text in texts.items():(w/(name+'.txt')).write_text(text)
    assert 'Erase? Y/N' in texts['invalid'] and 'ERA cancelled.' not in texts['invalid']
    assert 'A0:FIRST.DAT - Erase? Y/N' in texts['first']
    assert 'A0:FIRST.DAT - Erase? Y/N' in texts['again']
    assert 'Erase? Y/N' in texts['again'] and '1 FILES ERASED' in texts['erase']
    assert 'SKIPPED - PROTECTED' in texts['protected'] and 'ERA cancelled.' in texts['cancel']
    assert 'A0>' in texts['returned']
    after=extract_raw(disk.read_bytes());(w/'after.raw').write_bytes(after);now=files(after[20480:])
    assert (0,b'FIRST   DAT') not in now
    for key,(payload,entries) in before.items():
        if key==(0,b'FIRST   DAT'):continue
        assert now[key][0]==payload,key
    assert all(entry[9]&128 for entry in now[0,b'ROFILE  DAT'][1])
    assert after[:20480]==raw[:20480],'system records changed'
    (w/'diskdefs').write_text('diskdef bettercpm-default\n seclen 512\n tracks 160\n sectrk 10\n blocksize 2048\n maxdir 128\n skew 1\n boottrk 4\n os 2.2\nend\n')
    fs=subprocess.run(['fsck.cpm','-T','raw,pcw800','-f','bettercpm-default','-n',str(w/'after.raw')],cwd=w,capture_output=True,text=True)
    (w/'filesystem.txt').write_text(fs.stdout+fs.stderr);assert fs.returncode==0
    result={'status':'PASS','program_sha256':hashlib.sha256((ROOT/'build/utilities/ERA.COM').read_bytes()).hexdigest(),
            'stages':stages,'scope':'Actual native Model 4 confirmations: invalid ESC/Enter/X retain prompt, N preserves file, Y erases, RO N/Ctrl-C preserve payload/attribute, normal return, unchanged other files/system records and clean filesystem. Recovery fault choices are separately CPU-qualified.'}
    (w/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(w)


if __name__=='__main__':main()
