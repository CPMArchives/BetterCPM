#!/usr/bin/env python3
"""Qualify DDT's Model 4 VRAM and physical keyboard on disposable media."""
import argparse,hashlib,json
from pathlib import Path
from build_ddt import version_text, ROOT
from add_cpm_file_to_dmk import extract_raw,add_file,FILESYSTEM_FIRST_SECTOR,SECTOR_SIZE,DIRECTORY_ENTRIES
from build_montezuma_extended_790k import build
from run_trs80_command import DEFAULT_EMULATOR,key_args
from trs80gp_launch import run


def sha(data):return hashlib.sha256(data).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--image',type=Path,help='optional source DMK; never mounted or modified')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False);w=a.output.resolve()
    if a.image:original=a.image.read_bytes()
    else:
        from test_disk_utilities import medium
        original=medium([])
    (w/'source.dmk').write_bytes(original)
    raw=extract_raw(original);directory=FILESYSTEM_FIRST_SECTOR*SECTOR_SIZE
    for i in range(DIRECTORY_ENTRIES):
        at=directory+i*32
        if raw[at]==0 and bytes(v&127 for v in raw[at+1:at+12]) in (b'DDT     COM',b'STARTUP SUB',b'DDONE   COM'):raw[at]=0xe5
    data=(ROOT/'build/utilities/DDT.COM').read_bytes();add_file(raw,'DDT.COM',data)
    add_file(raw,'DDONE.COM',bytes.fromhex('110b010e09cd0500c30000')+b'DDT RETURNED$')
    image=w/'private.dmk';private=build(raw);image.write_bytes(private)
    cmd=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-ktx','-d0',str(image),'-id','5000'];stages=[]
    # Do not use -iw for DDT's direct-console fields. On this emulator it
    # stalls despite the matching VRAM text. Settled captures are asserted
    # afterwards, so absent/late output is a test failure rather than a pass.
    def capture(label,delay=1500):
        stages.append(label);cmd.extend(['-id',str(delay),'-it'])
        if label in ('edit','scroll','cancel'):cmd.append('-ics')
    def keys(text):cmd.extend(key_args(text,delay=25))
    capture('boot')
    keys('DDT /VER\r');capture('version',3000)
    keys('DDT\r');capture('prompt',3000)
    keys('H100,2X');capture('edit')
    keys('\x7f0\r');capture('arithmetic')
    keys('H100,2X\x13\x070\r');capture('interior')
    keys('Z'+'1'*31);capture('scroll')
    keys('\x19H1,2\r');capture('clear')
    keys('F300,30F,41\rS300\r');capture('substitute')
    keys('99');capture('pending')
    # Physical Model 4 CLEAR is ESC, distinct from Control-letter editing.
    cmd+=['-ik','6','2','-id','25','-ik','6','0','-id','25'];capture('cancel')
    keys('D300,300\r');capture('unchanged')
    keys('A400\rMVI A,5\rRET\r.\rL400,402\r');capture('assembly')
    keys('G0\r');capture('warmboot',3000)
    keys('DDONE\r');capture('returned',3000)
    keys('DDT\r');capture('restart',3000)
    keys('\x03');capture('break',3000)
    cmd+=['-ix'];(w/'invocation.json').write_text(json.dumps(cmd,indent=2)+'\n')
    try:run(cmd,cwd=w,timeout=90)
    finally:
        assert (w/'source.dmk').read_bytes()==original,'retained source copy changed'
        if a.image:assert a.image.read_bytes()==original,'supplied baseline changed'
    files=sorted(w.glob('trs80-text-*.bin'),key=lambda f:int(f.stem.rsplit('-',1)[1]))
    assert len(files)==len(stages),(len(files),stages)
    screens={name:bytes(c&127 for c in f.read_bytes()[:1920]) for name,f in zip(stages,files)}
    for name,value in screens.items():
        (w/(name+'.txt')).write_text('\n'.join(value[i:i+80].decode('ascii').rstrip() for i in range(0,1920,80))+'\n')
    expected={'boot':b'A0>','version':version_text().splitlines()[0].encode(),'prompt':b'-_',
              'edit':b'-H100,2X_','arithmetic':b'0120 00E0','interior':b'-H100,20',
              'scroll':b'1'*23+b'_','clear':b'0003 FFFF','substitute':b'0300 41 _',
              'pending':b'0300 41 99_','cancel':b'-_','unchanged':b'0300 41 A',
              'assembly':b'0402  RET','warmboot':b'A0>','returned':b'DDT RETURNED',
              'restart':b'-_','break':b'A0>'}
    for label,needle in expected.items():assert needle in screens[label],(label,needle,screens[label])
    assert b'0300 41 99' not in screens['cancel']
    assert b'0120 00E0' in screens['interior']
    assert b'Z'+b'1'*23 not in screens['scroll'],'viewport did not scroll'
    assert image.read_bytes()==private,'debugger campaign changed private disk'
    report={'status':'PASS','program_sha256':sha(data),'baseline_sha256':sha(original),
            'emulator_sha256':sha(DEFAULT_EMULATOR.read_bytes()),'private_initial_sha256':sha(private),
            'private_final_sha256':sha(image.read_bytes()),'stages':stages,
            'captures':{f.name:sha(f.read_bytes()) for f in files},'source_unchanged':True,
            'screenshots':{name:{'file':f'trs80-{i}.gif','sha256':sha((w/f'trs80-{i}.gif').read_bytes())} for i,name in enumerate(['edit','scroll','cancel'])},
            'fixture_components':{n:sha((ROOT/n).read_bytes()) for n in ['build/system/resident.bin','build/trs80/boot.bin','build/trs80/stage1.bin','build/ccp/ccp.rlm','build/cpx/RCP.CPX']},
            'scope':'Model 4 boot control, /VER, physical DEL and Ctrl-S/G editing, horizontal scroll, Ctrl-Y clear, S prefix and physical CLEAR cancellation without commit, A/L, G0 warm boot, restart and BREAK warm boot. Only private.dmk mounted.'}
    (w/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(w)


if __name__=='__main__':main()
