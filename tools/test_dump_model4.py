#!/usr/bin/env python3
"""Native trs80gp DUMP screen, navigation, search, CLEAR/ESC and read-only checks."""
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
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--image',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--utilities',type=Path);a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=False);w=a.output.resolve()
    original=a.image.read_bytes();raw=extract_raw(original)
    # Replace only private fixture files if already present.
    directory=FILESYSTEM_FIRST_SECTOR*SECTOR_SIZE
    for i in range(DIRECTORY_ENTRIES):
        at=directory+i*32
        if raw[at]==0 and bytes(v&127 for v in raw[at+1:at+12]) in (b'DUMP    COM',b'DHEX    BIN',b'STARTUP SUB',b'DQDONE  COM'):raw[at]=0xe5
    payload=bytes(range(256))*8
    if not a.utilities:add_file(raw,'DUMP.COM',(ROOT/'build/utilities/DUMP.COM').read_bytes())
    entry,blocks=add_file(raw,'DHEX.BIN',payload)
    add_file(raw,'DQDONE.COM',bytes.fromhex('110b010e09cd0500c30000')+b'DUMP RETURNED$')
    batch=b'RSX LOAD M4SCRN\r\nRSX LOAD ADM3A\r\nDUMP DHEX.BIN /P\r\nDUMP DHEX.BIN /40 /P\r\nDUMP DHEX.BIN /FROM=7 /LEN=172 /P\r\nDUMP DHEX.BIN /FROM=7 /LEN=3 /40 /P\r\nDQDONE\r\n\x1a'
    if a.utilities:batch=batch.replace(b'DUMP DHEX',b'B:DUMP DHEX')
    add_file(raw,'STARTUP.SUB',batch)
    initial=bytes(raw);image=w/'private.dmk';image.write_bytes(build(raw))
    cmd=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-ktx','-d0',str(image),'-itime','60000']
    if a.utilities:
        shutil=__import__('shutil');shutil.copy2(a.utilities,w/'utilities.dmk');cmd += ['-d1',str(w/'utilities.dmk')]
    stages=[]
    def capture(label,wait):
        stages.append(label);cmd.extend(['-iw',wait,'-id','120','-it'])
    capture('wide','^R Up ^C Down F Find G Go Q Quit')
    cmd+=key_args('\x03',delay=25);capture('down','00000170')
    cmd+=key_args('G',delay=25);capture('goprompt','Go to offset:')
    cmd+=key_args('10\x13\x07\x080\x04\r',delay=25);capture('goto','00000000')
    cmd+=key_args('F7F8081\rH',delay=25);capture('match','Match at 0000007F')
    cmd+=key_args('.',delay=25);capture('next','Match at 0000017F')
    cmd+=key_args(',',delay=25);capture('previous','Match at 0000007F')
    cmd+=key_args('FABC',delay=25)
    # Physical CLEAR, not Ctrl-[ synthesized through a host layout.
    cmd+=['-ik','6','2','-id','25','-ik','6','0','-id','25']
    capture('cancel','., Match')
    cmd+=key_args('Q',delay=25)
    capture('compact','^R Up ^C Down F Find G Go Q Quit')
    cmd+=key_args('Q',delay=25)
    capture('range','^R Up ^C Down F Find G Go Q Quit')
    cmd+=key_args('\x03',delay=25);capture('range-down','00000170')
    cmd+=key_args('\x03',delay=25);capture('range-end','End of file')
    cmd+=key_args('\x12',delay=25);capture('range-up','00000000')
    cmd+=key_args('\x12',delay=25);capture('range-begin','Beginning of file')
    cmd+=key_args('G178\r',delay=25);capture('range-goto','00000170')
    cmd+=key_args('Q',delay=25)
    capture('compact-range','^R Up ^C Down F Find G Go Q Quit')
    cmd+=key_args('Q',delay=25)+['-iw','DUMP RETURNED','-id','120','-it','-ix'];stages.append('returned')
    (w/'invocation.json').write_text(json.dumps(cmd,indent=2)+'\n');run(cmd,cwd=w,timeout=1200)
    files=sorted(w.glob('trs80-text-*.bin'),key=lambda f:int(f.stem.rsplit('-',1)[1]));assert len(files)==len(stages),(len(files),stages)
    screens={label:bytes(c&127 for c in f.read_bytes()[:1920]) for label,f in zip(stages,files)}
    for label,v in screens.items():(w/(label+'.txt')).write_text('\n'.join(v[i:i+80].decode('ascii').rstrip() for i in range(0,1920,80))+'\n')
    for label,pos in [('wide',0),('down',368),('goto',0),('match',112),('next',368),('previous',112),('cancel',112)]:
        assert screens[label][:76]==row(payload,pos).encode(),(label,screens[label][:80])
    assert files[stages.index('goprompt')].read_bytes()[23*80+14]==(ord('_')|128), 'software insertion cursor missing'
    assert screens['compact'][:37]==row(payload,0,True).encode()
    for label,pos in [('range',0),('range-down',368),('range-end',368),('range-up',0),('range-begin',0),('range-goto',368)]:
        assert screens[label][:76]==row(payload,pos,lower=7,end=377).encode(),(label,screens[label][:80])
    assert not screens['range-down'][80:160].strip()
    assert screens['compact-range'][:37]==row(payload,0,True,lower=7,end=10).encode()
    assert screens['compact-range'][80:117]==row(payload,8,True,lower=7,end=10).encode()
    assert not screens['compact-range'][160:240].strip()
    assert b'DUMP RETURNED' in screens['returned']
    after=bytes(extract_raw(image.read_bytes()))
    # Startup SUBMIT may create/retire its queue. Check the viewed file's
    # complete directory entry (including attributes) and allocated data apart
    # from that known boot activity, then run an independent filesystem check.
    at=directory+entry*32
    assert after[at:at+32]==initial[at:at+32], 'input directory/attributes changed'
    for block in blocks:
        at=directory+block*2048
        assert after[at:at+2048]==initial[at:at+2048], 'input allocation data changed'
    (w/'after.raw').write_bytes(after)
    (w/'diskdefs').write_text('diskdef bettercpm-default\n seclen 512\n tracks 160\n sectrk 10\n blocksize 2048\n maxdir 128\n skew 1\n boottrk 4\n os 2.2\nend\n')
    fs=subprocess.run(['fsck.cpm','-T','raw,pcw800','-f','bettercpm-default','-n',str(w/'after.raw')],cwd=w,capture_output=True,text=True)
    (w/'filesystem.txt').write_text(fs.stdout+fs.stderr);assert fs.returncode==0
    assert a.image.read_bytes()==original,'reference disk changed'
    if a.utilities:assert (w/'utilities.dmk').read_bytes()==a.utilities.read_bytes()
    result={'status':'PASS','program_sha256':sha((ROOT/'build/utilities/DUMP.COM').read_bytes()),'source_image_sha256':sha(original),'stages':stages,'scope':'Actual Model 4 execution with shipped monitor/backend: wide/compact page cells, Ctrl-C Page Down, Go To with all four WordStar edit keys and software cursor, cross-record forward/backward Find, physical CLEAR cancellation, direct CCP return and unchanged input allocations/attributes and clean independent filesystem check (startup queue activity is separate).'}
    (w/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(w)
if __name__=='__main__':main()
