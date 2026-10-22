#!/usr/bin/env python3
"""Native Model 4 standard prompt consumer and real screen qualification."""
import argparse,hashlib,json,subprocess
from pathlib import Path
from add_cpm_file_to_dmk import extract_raw,add_file,FILESYSTEM_FIRST_SECTOR,SECTOR_SIZE,DIRECTORY_ENTRIES
from build_montezuma_extended_790k import build
from run_trs80_command import DEFAULT_EMULATOR,key_args
from trs80gp_launch import run
from test_dump_enhanced import row
ROOT=Path(__file__).resolve().parents[1]
sha=lambda b:hashlib.sha256(b).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--image',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=False);w=a.output.resolve()
    original=a.image.read_bytes();raw=extract_raw(original)
    # Replace only private fixture files if already present.
    directory=FILESYSTEM_FIRST_SECTOR*SECTOR_SIZE
    for i in range(DIRECTORY_ENTRIES):
        at=directory+i*32
        if raw[at]==0 and bytes(v&127 for v in raw[at+1:at+12]) in (b'UIEX    COM',b'STARTUP SUB'):raw[at]=0xe5
    add_file(raw,'UIEX.COM',(ROOT/'build/shared-ui/UIEX.COM').read_bytes())
    add_file(raw,'STARTUP.SUB',b'RSX LOAD M4SCRN\r\nRSX LOAD ADM3A\r\nUIEX\r\nUIEX /40\r\nUIEX\r\n\x1a')
    initial=bytes(raw);image=w/'private.dmk';image.write_bytes(build(raw))
    cmd=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-ktx','-d0',str(image),'-itime','60000']
    stages=[]
    def capture(label,wait):
        stages.append(label);cmd.extend(['-iw',wait,'-id','120','-it'])
    for tag in ['wide','compact']:
        capture(tag+'-default','Value: [DEFAULT]')
        cmd+=key_args('BAD\r',delay=25);capture(tag+'-invalid','BAD is rejected; edit or cancel.')
        cmd+=key_args('\x19',delay=25);capture(tag+'-restored','Value: [DEFAULT]')
        cmd+=key_args('\r' if tag=='compact' else 'OK\r',delay=25);capture(tag+'-choice','Accept? (Y/N) [N]')
        cmd+=key_args('Y',delay=25);capture(tag+'-error','Demo rejects Y;')
        cmd+=key_args('\r',delay=25);capture(tag+'-accepted','Press a key to return.')
        cmd+=key_args('Q',delay=25)
    capture('cancel-default','Value: [DEFAULT]')
    cmd+=key_args('\x03',delay=25);capture('text-cancel','Accept? (Y/N) [N]')
    cmd+=['-ik','6','2','-id','25','-ik','6','0','-id','25']
    capture('choice-cancel','Press a key to return.')
    cmd+=key_args('Q',delay=25)+['-id','120','-it','-ix'];stages.append('returned')
    (w/'invocation.json').write_text(json.dumps(cmd,indent=2)+'\n');run(cmd,cwd=w,timeout=1200)
    files=sorted(w.glob('trs80-text-*.bin'),key=lambda f:int(f.stem.rsplit('-',1)[1]));assert len(files)==len(stages),(len(files),stages)
    screens={label:bytes(c&127 for c in f.read_bytes()[:1920]) for label,f in zip(stages,files)}
    for label,v in screens.items():(w/(label+'.txt')).write_text('\n'.join(v[i:i+80].decode('ascii').rstrip() for i in range(0,1920,80))+'\n')
    for tag in ['wide','compact']:
        for stage in ['default','invalid','restored','choice','error','accepted']:
            frame=screens[tag+'-'+stage]
            assert frame[:27]==b'Shared UI developer example'
            assert frame[160:].startswith(b'Body sentinel: unchanged by prompts.')
        assert screens[tag+'-default'][1840:].startswith(b'Value: [DEFAULT] _')
        assert screens[tag+'-restored'][1840:].startswith(b'Value: [DEFAULT] _')
        assert files[stages.index(tag+'-default')].read_bytes()[1840+17]==(ord('_')|128)
        assert screens[tag+'-error'][1840:].startswith(b'Accept? (Y/N) [N] Demo rejects Y;')
        assert screens[tag+'-accepted'][80:].startswith(b'DEFAULT' if tag=='compact' else b'OK')
        assert screens[tag+'-accepted'][240:].startswith(b'Choice N accepted')
    assert screens['compact-error'][1840+38]==ord('~')
    assert not screens['compact-error'][1840+39:].strip()
    assert screens['choice-cancel'][80:].startswith(b'Cancelled')
    assert screens['choice-cancel'][240:].startswith(b'Cancelled')
    after=bytes(extract_raw(image.read_bytes()))
    (w/'after.raw').write_bytes(after)
    (w/'diskdefs').write_text('diskdef bettercpm-default\n seclen 512\n tracks 160\n sectrk 10\n blocksize 2048\n maxdir 128\n skew 1\n boottrk 4\n os 2.2\nend\n')
    fs=subprocess.run(['fsck.cpm','-T','raw,pcw800','-f','bettercpm-default','-n',str(w/'after.raw')],cwd=w,capture_output=True,text=True)
    (w/'filesystem.txt').write_text(fs.stdout+fs.stderr);assert fs.returncode==0
    assert a.image.read_bytes()==original,'reference disk changed'
    result={'status':'PASS','program_sha256':sha((ROOT/'build/shared-ui/UIEX.COM').read_bytes()),'source_image_sha256':sha(original),'stages':stages,'scope':'Real Model 4 M4SCRN/ADM3A: wide/compact separate defaults, editing/correction, Ctrl-Y restoration, choice errors/truncation, Enter default, Ctrl-C and physical CLEAR cancellation, reverse caret, preserved body rows, clean filesystem and unchanged reference image.'}
    (w/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(w)
if __name__=='__main__':main()
