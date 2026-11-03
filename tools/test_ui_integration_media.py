#!/usr/bin/env python3
"""Focused shared-choice integration on private cpmsim/Model 4 media.

Uses the existing session, DMK and emulator launch infrastructure. Prepare-only
creates a reviewable native invocation without claiming execution/qualification.
"""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
from test_z80pack_sysgen_install import session
from build_z80pack_image import disk_definition,DEFAULT_FORMAT
from fdf_format import select_fdf
from add_cpm_file_to_dmk import extract_raw,add_file,FILESYSTEM_FIRST_SECTOR,SECTOR_SIZE,DIRECTORY_ENTRIES
from build_montezuma_extended_790k import build as make_dmk
from convert_fdf_image import raw_to_dmk,dmk_to_raw
from run_trs80_command import DEFAULT_EMULATOR,key_args
from trs80gp_launch import run as launch
ROOT=Path(__file__).resolve().parents[1]
sha=lambda b:hashlib.sha256(b).hexdigest()


def native_marker(message):
    """Print a unique completion marker, block, clear old screen text, warm boot.

    Uses the same BDOS 9/1 marker handshake as dasm_native.campaign. Scrolling
    after acknowledgement prevents the next -iw matching an earlier prompt.
    """
    code=bytearray.fromhex('1100000e09cd05000e01cd05001100000e09cd0500c30000')
    text=(message+'\r\n$').encode('ascii')
    code[1:3]=(256+len(code)).to_bytes(2,'little')
    code[14:16]=(256+len(code)+len(text)).to_bytes(2,'little')
    return bytes(code)+text+b'\r\n'*24+b'$'


def native_schedule(steps):
    """SUBMIT owns shell commands; only modal responses use physical keys."""
    script=[];markers={};actions=[]
    for index,(key,prompt) in enumerate(steps):
        if key.startswith('B:'):
            assert key.endswith('\r'),key
            script+=['CLS',key[:-1]]
            outgoing=''
        else:outgoing=key
        complete=prompt=='A0>'
        if complete:
            name=f'UI{index:02}'
            prompt=f'UI STEP {index:02} DONE'
            markers[name+'.COM']=native_marker(prompt)
            script.append(name)
        actions.append((outgoing,prompt,complete))
    return ('\r\n'.join(script)+'\r\n\x1a').encode(),markers,actions


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--system',type=Path,required=True,help='Existing paired system directory, containing z80pack/trs80gp report.json')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--platform',choices=('cpmsim','model4'),required=True)
    p.add_argument('--prepare-only',action='store_true')
    p.add_argument('--emulator',type=Path,default=DEFAULT_EMULATOR)
    p.add_argument('--simulator',type=Path,default=Path.home()/'projects/git/z80pack/cpmsim/cpmsim')
    a=p.parse_args();w=a.output.resolve();w.mkdir(parents=True,exist_ok=False)
    native=a.platform=='model4';platform='trs80gp' if native else 'z80pack'
    report=json.loads((a.system/platform/'report.json').read_text())
    base=a.system/platform/report['image'];original=base.read_bytes()
    artifacts={name:(ROOT/'build/utilities'/(name+'.COM')).read_bytes() for name in ('CRCKSUM','MD5SUM','DASM')}
    if not native:artifacts['BYE']=(ROOT/'build/z80pack-tools/BYE.COM').read_bytes()
    files={name+'.COM':data for name,data in artifacts.items()}
    files.update({'FIX.DAT':b'123456789'+b'\x1a'*119,'CRC.LST':b'KEEP CRC'+b'\x1a'*120,'MD5.LST':b'KEEP MD5'+b'\x1a'*120})
    # Always use logged A: and explicit B: file operands; no user source is modified.
    steps=[]
    for name in artifacts:
        for query in ('/HELP /VER /BOGUS','/VER /BOGUS'):
            steps.append((f'B:{name} {query}\r','A0>'))
    for name,listname in [('CRCKSUM','CRC.LST'),('MD5SUM','MD5.LST')]:
        steps += [(f'B:{name} B:FIX.DAT /FILE=B:NEW{listname}\r','A0>'),
                  (f'B:{name} B:FIX.DAT /FILE=B:{listname}\r','Overwrite?'),
                  (('??-[\x1bn' if native else '??#-\x1bn'),'A0>'),
                  (f'B:{name} B:FIX.DAT /FILE=B:{listname}\r','Overwrite?'),('\x03','A0>')]
    steps += [('B:DASM\r','*'),('X\r','Restart DASM (Y/N)? '),('n','*'),('G\r','A0>')]
    if not native:steps += [('B:BYE\r','Exit cpmsim? (Y/N) [N]: '),('#-\x1bn','A0>')]
    (w/'steps.json').write_text(json.dumps(steps,indent=2)+'\n')
    if native:
        # A: uses the reserved-track system format; configured B: uses the
        # standard 800K DATA format (OFF=0 and a different sector order).
        # A system-format clone in B: is not readable by that drive's DPB.
        raw=extract_raw(original)
        directory=FILESYSTEM_FIRST_SECTOR*SECTOR_SIZE
        for i in range(DIRECTORY_ENTRIES):
            at=directory+i*32
            if raw[at]==0 and raw[at+1:at+12]==b'STARTUP SUB':raw[at]=0xe5
        # Neither startup prompts nor previous A0> text establish readiness.
        # Let the established SUBMIT path sequence all shell commands, with a
        # blocking completion program after each returned operation.
        script,markers,actions=native_schedule(steps)
        system_files={'UIQUAL.SUB':script,**markers,
                      'STARTUP.SUB':b'RSX LOAD M4SCRN\r\nRSX LOAD ADM3A\r\nSUBMIT UIQUAL\r\n\x1a'}
        for name,data in system_files.items():add_file(raw,name,data)
        (w/'UIQUAL.SUB').write_bytes(script)
        (w/'a.dmk').write_bytes(make_dmk(raw))
        data_format=select_fdf(ROOT/'third_party/montezuma/DISK-INT.FDF','Montezuma Micro 80T DS DATA (80T, DS, DD, 800K)')
        definitions=disk_definition(select_fdf(ROOT/'third_party/montezuma/DISK.FDF',DEFAULT_FORMAT))
        definitions+='diskdef ui-system\n libdsk:format pcw800\n seclen 512\n tracks 160\n sectrk 10\n blocksize 2048\n maxdir 128\n skew 1\n boottrk 4\n os 2.2\nend\n'
        (w/'diskdefs').write_text(definitions)
        system_preflight=w/'a-preflight.raw';system_preflight.write_bytes(extract_raw((w/'a.dmk').read_bytes()))
        for name,data in system_files.items():
            dest=w/('PRE-'+name)
            subprocess.run(['cpmcp','-T','raw','-f','ui-system',str(system_preflight),'0:'+name,str(dest)],cwd=w,check=True,capture_output=True)
            assert dest.read_bytes()[:len(data)]==data,('prepared system script/marker',name)
        subprocess.run(['fsck.cpm','-T','raw','-f','ui-system','-n',str(system_preflight)],cwd=w,check=True,capture_output=True)
        disk=w/'work.raw';disk.write_bytes(bytes([0xe5])*data_format.image_bytes)
        subprocess.run(['mkfs.cpm','-f','bettercpm-mm-80t-ds-data',str(disk)],cwd=w,check=True,capture_output=True)
        for name,data in files.items():
            path=w/name;path.write_bytes(data)
            subprocess.run(['cpmcp','-T','raw','-f','bettercpm-mm-80t-ds-data',str(disk),str(path),'0:'+name],cwd=w,check=True,capture_output=True)
        image=raw_to_dmk(disk.read_bytes(),data_format)
        assert dmk_to_raw(image,data_format)==disk.read_bytes()
        (w/'b.dmk').write_bytes(image)
        # Validate the converted media using the actual B: format before launch.
        preflight=w/'preflight.raw';preflight.write_bytes(dmk_to_raw(image,data_format))
        for name,data in files.items():
            dest=w/('PRE-'+name)
            subprocess.run(['cpmcp','-T','raw','-f','bettercpm-mm-80t-ds-data',str(preflight),'0:'+name,str(dest)],cwd=w,check=True,capture_output=True)
            assert dest.read_bytes()[:len(data)]==data,('prepared media',name)
        subprocess.run(['fsck.cpm','-T','raw','-f','bettercpm-mm-80t-ds-data','-n',str(preflight)],cwd=w,check=True,capture_output=True)
        invocation=[str(a.emulator),'-m4','-batch','-turbo','-sx','-sfmute','-ktx','-d0',str(w/'a.dmk'),'-d1',str(w/'b.dmk'),'-itime','60000']
        for key,marker,complete in actions:
            for part in key.split('\x1b')[:-1]:
                invocation+=key_args(part,delay=25)+['-ik','6','2','-id','25','-ik','6','0','-id','25']
            invocation+=key_args(key.split('\x1b')[-1],delay=25)+['-iw',marker,'-id','60','-it']
            if complete:invocation+=key_args('\r',delay=25)+['-id','120']
        invocation+=['-ix'];(w/'invocation.json').write_text(json.dumps(invocation,indent=2)+'\n')
        # Terminal command is generated as argv, avoiding shell escaping entirely.
        runner='import json,subprocess\nfrom pathlib import Path\nw=Path(__file__).resolve().parent\nsubprocess.run(json.loads((w/"invocation.json").read_text()),cwd=w,check=True)\n'
        (w/'run_model4.py').write_text(runner)
    else:
        definitions=disk_definition(select_fdf(ROOT/'third_party/montezuma/DISK.FDF',DEFAULT_FORMAT))
        disks=w/'disks';disks.mkdir();(disks/'drivea.dsk').write_bytes(original)
        (disks/'driveb.dsk').write_bytes(original)
    (w/'diskdefs').write_text(definitions)
    if not native:
        disk=w/'disks/driveb.dsk'
        subprocess.run(['mkfs.cpm','-f','bettercpm-default',str(disk)],cwd=w,check=True,capture_output=True)
        for name,data in files.items():
            path=w/name;path.write_bytes(data)
            subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(disk),str(path),'0:'+name],cwd=w,check=True,capture_output=True)
    receipt={'status':'PREPARED','platform':a.platform,'system_sha256':sha(original),'binaries':{n:{'bytes':len(b),'sha256':sha(b)} for n,b in artifacts.items()},'steps':len(steps),'scope':'queries, checksum creation/repeated help/invalid bytes/No/Ctrl-C, DASM restart refusal, cpmsim BYE cancellation; independently read back preserved files and new lists'}
    if native:receipt.update(work_format=data_format.name,media_preflight='PASS',command_transport='SUBMIT UIQUAL with unique blocking completion markers',command_script_sha256=sha(script))
    (w/'result.json').write_text(json.dumps(receipt,indent=2)+'\n')
    if a.prepare_only:print('PREPARED; execution and readback pending:',w);return
    if native:
        try:
            launch(invocation,cwd=w,timeout=600)
            captures=sorted(w.glob('trs80-text-*.bin'),key=lambda path:int(path.stem.rsplit('-',1)[1]))
            assert len(captures)==len(steps),('missing native captures',len(captures),len(steps))
            screens=[bytes(value&127 for value in path.read_bytes()[:1920]) for path in captures]
            (w/'console.bin').write_bytes(b'\n'.join(screens))
            for index,(_,marker,_) in enumerate(actions):
                assert marker.encode() in screens[index],('missing completion/prompt',index,marker)
            for index,name in enumerate(artifacts):
                assert b'Usage:' in screens[2*index],('help did not execute',name)
                assert (name+' 1.0 (').encode() in screens[2*index+1],('version did not execute',name)
        except BaseException as error:
            count=len(list(w.glob('trs80-text-*.bin')))
            expected=actions[count][1] if count<len(actions) else 'capture validation'
            reason=(f'timed out after {error.timeout}s' if isinstance(error,subprocess.TimeoutExpired)
                    else 'interrupted' if isinstance(error,KeyboardInterrupt) else f'{type(error).__name__}: {error}')
            receipt.update(status='FAIL',stage='native execution/capture',error=reason,completed_captures=count,next_expected=expected)
            (w/'result.json').write_text(json.dumps(receipt,indent=2)+'\n')
            raise SystemExit(f'FAIL: {reason}; captures {count}/{len(steps)}; next expected {expected!r}. Results: {w}') from None
    else:session(a.simulator,w/'disks',[(key.encode(),(marker+'_ ' if marker=='A0>' else marker).encode(),30) for key,marker in steps],w/'transcript.bin')
    if native:
        raw=dmk_to_raw((w/'b.dmk').read_bytes(),data_format);disk=w/'readback.raw';disk.write_bytes(raw);fmt='bettercpm-mm-80t-ds-data'
    else:disk=w/'disks/driveb.dsk';fmt='bettercpm-default'
    for name,data in files.items():
        dest=w/('READ-'+name)
        subprocess.run(['cpmcp','-T','raw','-f',fmt,str(disk),'0:'+name,str(dest)],cwd=w,check=True,capture_output=True)
        actual=dest.read_bytes();assert actual[:len(data)]==data,name
    for name in ('NEWCRC.LST','NEWMD5.LST'):
        dest=w/('READ-'+name)
        subprocess.run(['cpmcp','-T','raw','-f',fmt,str(disk),'0:'+name,str(dest)],cwd=w,check=True,capture_output=True)
        assert (b'FIX      DAT' if name=='NEWCRC.LST' else b'FIX.DAT') in dest.read_bytes(),name
    result=subprocess.run(['fsck.cpm','-T','raw','-f',fmt,'-n',str(disk)],cwd=w,capture_output=True)
    (w/'filesystem.log').write_bytes(result.stdout+result.stderr);assert result.returncode==0
    assert base.read_bytes()==original
    private_system=(w/('a.dmk' if native else 'disks/drivea.dsk')).read_bytes()
    if native:
        boundary=FILESYSTEM_FIRST_SECTOR*SECTOR_SIZE
        assert extract_raw(private_system)[:boundary]==extract_raw(original)[:boundary]
    else:
        fmt=select_fdf(ROOT/'third_party/montezuma/DISK.FDF',DEFAULT_FORMAT)
        boundary=fmt.reserved_records*128
        assert private_system[:boundary]==original[:boundary]
    receipt.update(status='PASS',unchanged_inputs=True,unchanged_system_area=True,filesystem='PASS',new_lists='PASS')
    (w/'result.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
