"""Live checked-distribution acceptance on isolated cpmsim disk copies."""
from pathlib import Path
import binascii
import json
import re
import shutil
import subprocess
import textwrap
from test_z80pack_sysgen_install import session
from build_ccp import assemble
from system_layout import LAYOUT as L
from fdf_format import select_fdf
from build_z80pack_image import DEFAULT_FORMAT
from checked_system_package import make,validate,raw_payload
from startup_record import build as startup_record


def qualify(root,image,out,simulator):
    out.mkdir(parents=True);results={}
    fmt=select_fdf(root/'third_party/montezuma/DISK.FDF',DEFAULT_FORMAT)
    expected=(L['TPA']-256)//128*128
    contract=json.loads((root/'build/z80pack/checked-package.json').read_text())
    good=(root/'build/z80pack/system-package/SYSTEM.SYS').read_bytes()
    def save(name,**value):
        results[name]=value;(out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    def rawput(data,record,payload):
        for i in range(0,len(payload),128):
            tr,within=divmod(record+i//128,fmt.spt)
            at=tr*fmt.raw_track_bytes+fmt.raw_record_map()[within]*128
            data[at:at+128]=payload[i:i+128]
    def case(name):
        w=out/name;(w/'disks').mkdir(parents=True)
        shutil.copy2(root/'build/z80pack/diskdefs',w/'diskdefs')
        for drive in 'abcd':
            data=bytearray(image.read_bytes())
            # Tests isolate preservation from SUBMIT's temporary-file writes.
            rawput(data,1,startup_record(':VER /BANNER',system_base=L['SYSTEM']))
            (w/'disks'/f'drive{drive}.dsk').write_bytes(data)
        return w
    def put(w,name,data,drive='a'):
        path=w/name;path.write_bytes(data);disk=w/'disks'/f'drive{drive}.dsk'
        subprocess.run(['cpmrm','-f','bettercpm-default',str(disk),'0:'+name],cwd=w,capture_output=True)
        subprocess.run(['cpmcp','-f','bettercpm-default',str(disk),str(path),'0:'+name],cwd=w,check=True,capture_output=True)
    def run(w,commands,stem='transcript',initial=b'A0>_ '):
        steps=[(c.encode()+b'\r',b'A0>_ ',30) if isinstance(c,str) else c for c in commands]
        raw=session(simulator,w/'disks',steps,w/(stem+'.bin'),initial_prompt=initial)
        text=re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]','',raw.decode('ascii',errors='replace')).replace('\r','')
        (w/(stem+'.txt')).write_text(text);return text
    def maps(text):return [int(x) for x in re.findall(r'Maximum loadable COM:\s*(\d+)',text)]
    def asm(w,name,text):
        return assemble(Path.home()/'bin/z80asm','        ASEG\n        ORG 0100H\n'+textwrap.dedent(text)+'\n        END\n',w/(name+'.bin'),w/(name+'.lst'),0x100)

    w=case('boundary')
    records=(L['TPA']-256)//128
    s=f'''        LD HL,(6)
            LD DE,0{L['TPA']:04X}H
            OR A
            SBC HL,DE
            JR NZ,BAD
            LD HL,(0{L['SYSTEM']+0x90:04X}H)
            OR A
            SBC HL,DE
            JR NZ,BAD
            LD HL,0180H
            LD DE,{(records-1)*128}
    LOOP:   LD A,H
            DEC A
            ADD A,A
            LD B,A
            LD A,L
            RLCA
            AND 1
            OR B
            CP (HL)
            JR NZ,BAD
            INC HL
            DEC DE
            LD A,D
            OR E
            JR NZ,LOOP
            LD DE,OK
            JR SHOW
    BAD:    LD DE,ERR
    SHOW:   LD C,9
            CALL 5
            RET
    OK: DB 'FULLRAM FIT PASS',13,10,'$'
    ERR: DB 'FULLRAM FIT FAILED',13,10,'$'
    '''
    code=asm(w,'FIT',s);assert len(code)<=128
    payload=code.ljust(128,b'\0')+b''.join(bytes([i&255])*128 for i in range(1,records))
    put(w,'FIT.COM',payload);put(w,'OVER.COM',payload+bytes([records&255])*128)
    for name,code in [('JPZERO',b'\xc3\0\0'),('FNZERO',b'\x0e\0\xcd\x05\0\x76'),('BIOSWB',b'\x2a\x01\0\xe9')]:put(w,name+'.COM',code)
    t=run(w,['STAT MEM','FIT','STAT MEM','OVER','STAT MEM','FIT','JPZERO','FNZERO','BIOSWB','CPX /V','STAT MEM'])
    assert t.count('FULLRAM FIT PASS')==2 and 'FULLRAM FIT FAILED' not in t
    assert 'FULLRAM FIT' not in t.split('A0>OVER \n',1)[1].split('BetterCP/M Memory Map',1)[0]
    m=maps(t);assert len(m)==4 and all(x==expected for x in m)
    save('boundary',fit_bytes=len(payload),rejected_bytes=len(payload)+128,returns=['RET','JP 0','BDOS 0','BIOS WBOOT'],maps=m)

    w=case('stateful')
    for name,path in [('HELLO.RSX','build/rsx/HELLO.RSX'),('ECHO.RSX','build/rsx/ECHO.RSX'),('STATEFUL.RSX','build/rsx/STATEFUL.RSX'),('STATTST.COM','build/utilities/STATTST.COM'),('HELLO.CPX','build/cpx/HELLO.CPX')]:
        put(w,name,(root/path).read_bytes())
    t=run(w,['CPX LOAD HELLO','HELLO','CPX UNLOAD HELLO','RSX LOAD HELLO','RSX LOAD STATEFUL','STATTST INIT','STATTST MUTATE','STATTST CHECK','RSX UNLOAD HELLO','STATTST CHECK','RSX LOAD ECHO','STATTST CHECK','RSX LOAD MISSING','STATTST CHECK','RSX LOAD ZPRTC','TIME','RSX UNLOAD ZPRTC','STATTST CHECK','RSX UNLOAD ECHO','RSX UNLOAD STATEFUL','STAT MEM'])
    assert t.count('STATEFUL CHECK PASS')==5 and 'FAILED' not in t
    assert 'Hello from HELLO.CPX' in t and 'RSX module or profile error' in t and maps(t)[-1]==expected
    save('stateful',checks=5,public_cpx=True,missing_rejected=True,unloaded_tpa=expected)
    w=case('monitor')
    t=run(w,['RSX LOAD ANSISCRN','STAT MEM',(b'RSX LOAD ADM3A\r',b'\x1b[7m \x1b[0m ',30),(b'STAT MEM\r',b'\x1b[7m \x1b[0m ',30),(b'RSX UNLOAD ADM3A\r',b'A0>_ ',30),'RSX UNLOAD ANSISCRN','STAT MEM'])
    assert maps(t)==[expected-2560,expected-3072,expected],maps(t)
    save('monitor',screen_pair_tpa=expected-3072,unloaded_tpa=expected)
    for kind in ('payload','public-id','old-format','truncated','late-crc'):
        w=case('cpx-'+kind);bad=bytearray((root/'build/cpx/HELLO.CPX').read_bytes())
        if kind=='payload':bad[bad.index(b'Hello from')]=ord('J')
        elif kind=='public-id':
            bad[-18]=1;bad[-2:]=binascii.crc_hqx(bad[:-2],65535).to_bytes(2,'little')
        elif kind=='old-format':bad=bad[:-22];bad[4]=1
        elif kind=='truncated':bad=bad[:640]
        else:bad[-1]^=1
        put(w,'BAD.CPX',bad,'b');put(w,'GOOD.CPX',(root/'build/cpx/HELLO.CPX').read_bytes(),'b')
        for name,path in [('STATEFUL.RSX','build/rsx/STATEFUL.RSX'),('STATTST.COM','build/utilities/STATTST.COM')]:put(w,name,(root/path).read_bytes())
        t=run(w,['RSX LOAD STATEFUL','STATTST INIT','STATTST MUTATE','PIP HELLO.CPX=B:BAD.CPX','CPX LOAD HELLO','STATTST CHECK','CPX UNLOAD HELLO','PIP HELLO.CPX=B:GOOD.CPX','CPX LOAD HELLO','HELLO','STATTST CHECK','CPX UNLOAD HELLO','RSX UNLOAD STATEFUL','STAT MEM'])
        assert 'CPX?' in t and 'Jello from' not in t and 'Hello from HELLO.CPX' in t and t.count('STATEFUL CHECK PASS')==2 and maps(t)[-1]==expected
        save('cpx-'+kind,rejected=True,state_checks=2,recovered=True)
    for kind,record,offset in [('stage2-code',84,0),('stage2-id',99,104),('ccp',116,0)]:
        w=case('halt-'+kind);path=w/'disks/drivea.dsk';data=bytearray(path.read_bytes())
        tr,within=divmod(record,fmt.spt);data[tr*fmt.raw_track_bytes+fmt.raw_record_map()[within]*128+offset]^=1;path.write_bytes(data)
        raw=session(simulator,w/'disks',[],w/'halt.bin',initial_prompt=b'!');assert b'A0>' not in raw
        save('halt-'+kind,halt_before_prompt=True)
    for mode in ('package','disk'):
        w=case('install-'+mode);put(w,'KEEP.TXT',b'PRESERVE THIS FILE\r\n','b')
        if mode=='package':put(w,'SYSTEM.SYS',good)
        target=w/'disks/driveb.dsk';before=target.read_bytes()
        cmd='SYSGEN SYSTEM.SYS B:' if mode=='package' else 'SYSGEN A: B:'
        t=run(w,[(cmd.encode()+b'\r',b'Proceed (Y/N)?',60),(b'Y',b'A0>_ ',90)])
        assert 'System installed and verified.' in t
        assert target.read_bytes()[fmt.reserved_records*128:]==before[fmt.reserved_records*128:]
        shutil.copy2(target,w/'disks/drivea.dsk');cold=run(w,['STAT MEM'],'cold')
        assert maps(cold)[-1]==expected
        save('install-'+mode,filesystem_unchanged=True,cold_boot=True,tpa=expected)
    w=case('export');t=run(w,['SYSGEN A: B:EXPORTED.SYS']);assert 'Package exported and verified.' in t
    exported=w/'EXPORTED.SYS'
    subprocess.run(['cpmcp','-f','bettercpm-default',str(w/'disks/driveb.dsk'),'0:EXPORTED.SYS',str(exported)],cwd=w,check=True,capture_output=True)
    assert exported.read_bytes()==make(raw_payload(root,w/'disks/drivea.dsk'),contract)
    save('export',exact_host_package=True)
    for kind in ('identity','old-format','truncated','binding','stage2'):
        w=case('reject-package-'+kind);bad=bytearray(good)
        if kind=='identity':bad[80]^=1
        elif kind=='old-format':bad[4]=1
        elif kind=='truncated':bad=bad[:-128]
        elif kind=='binding':bad[16]^=1
        else:
            bad[128+84*128]^=1;bad[96:98]=binascii.crc_hqx(bad[128:],65535).to_bytes(2,'little')
        if kind!='truncated':bad[126:128]=binascii.crc_hqx(bad[:126],65535).to_bytes(2,'little')
        put(w,'BAD.SYS',bad);target=w/'disks/driveb.dsk';before=target.read_bytes()
        t=run(w,['SYSGEN BAD.SYS B:']);assert 'system package is invalid' in t and target.read_bytes()==before
        save('reject-package-'+kind,target_unchanged=True)
    for kind in ('missing-rcp','changed-pack','decline'):
        w=case(kind);target=w/'disks/driveb.dsk'
        if kind=='missing-rcp':subprocess.run(['cpmrm','-f','bettercpm-default',str(target),'0:RCP.CPX'],cwd=w,check=True,capture_output=True)
        if kind=='changed-pack':
            bad=bytearray((root/'build/system/R3PACK.RSX').read_bytes());bad[8]^=1;put(w,'R3PACK.RSX',bad,'b')
        before=target.read_bytes();t=run(w,[(b'SYSGEN A: B:\r',b'Proceed (Y/N)?',60),(b'N' if kind=='decline' else b'Y',b'A0>_ ',90)])
        assert target.read_bytes()==before
        if kind!='decline':assert 'Matching RCP.CPX and R3PACK.RSX required' in t
        save(kind,target_unchanged=True)
    return {'cases':len(results),'unloaded_tpa':expected,'screen_pair_tpa':expected-3072,'status':'PASS'}
