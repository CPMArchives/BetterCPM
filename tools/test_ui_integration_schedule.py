#!/usr/bin/env python3
"""Execute native completion stubs and check the focused media-test schedule."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
from test_bios import Z80
from test_ui_integration_media import ROOT,native_marker,native_schedule
from test_z80pack_sysgen_install import session


def check_queries(transcript):
    for index,name in enumerate(('CRCKSUM','MD5SUM','DASM')):
        for offset,query in enumerate(('/HELP /VER /BOGUS','/VER /BOGUS')):
            start=transcript.index(f'A0>B:{name} {query}\r'.encode())
            end=transcript.index(f'UI STEP {index*2+offset:02} DONE'.encode(),start)
            section=transcript[start:end]
            assert (name+' 1.0 (').encode() in section,('identification',name,query)
            if offset==0:assert b'Usage:' in section,('help did not execute',name)


def media_test(system,output):
    """Exercise the same SUBMIT/marker protocol on real BetterCP/M cpmsim."""
    work=output.resolve()
    subprocess.run([sys.executable,str(ROOT/'tools/test_ui_integration_media.py'),
                    '--system',str(system.resolve()),'--platform','cpmsim',
                    '--prepare-only','--output',str(work)],check=True)
    # Exercise the twenty Model 4 phases on cpmsim. BYE is cpmsim-only and its
    # queued Escape cancellation intentionally leaves a following key unread,
    # which cancels a SUBMIT stream under the documented CCP convention.
    steps=[];skip_response=False
    for key,prompt in json.loads((work/'steps.json').read_text()):
        if key.startswith('B:BYE'):
            skip_response=prompt!='A0>';continue
        if skip_response:skip_response=False;continue
        steps.append(('??-[\x1bn' if key=='??#-\x1bn' else key,prompt))
    assert len(steps)==20
    script,markers,actions=native_schedule(steps)
    def cpm(tool,disk,*args):
        return subprocess.run([tool,'-T','raw','-f','bettercpm-default',str(disk),*map(str,args)],
                              cwd=work,check=True,capture_output=True)
    system_disk=work/'disks/drivea.dsk';disk=work/'disks/driveb.dsk'
    before=system_disk.read_bytes()
    for name,data in {'UIQUAL.SUB':script,**markers}.items():
        host=work/name;host.write_bytes(data);cpm('cpmcp',system_disk,host,'0:'+name)
    # Preserve each original input for independent readback after the campaign.
    inputs={path.name:path.read_bytes() for path in work.iterdir()
            if path.name in ('CRCKSUM.COM','MD5SUM.COM','DASM.COM','BYE.COM','FIX.DAT','CRC.LST','MD5.LST')}
    commands=[(b'SUBMIT UIQUAL\r',actions[0][1].encode(),120)]
    for index,(key,prompt,_) in enumerate(actions[1:],1):
        release='\r' if actions[index-1][2] else ''
        assert not (release and key),('overlapping marker release and modal input',index)
        commands.append(((release+key).encode(),prompt.encode(),120))
    commands.append((b'\r',b'A0>_ ',120))
    transcript=session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',work/'disks',commands,work/'submit-transcript.bin')
    check_queries(transcript)
    for name,data in inputs.items():
        dest=work/('AFTER-'+name);cpm('cpmcp',disk,'0:'+name,dest)
        assert dest.read_bytes()[:len(data)]==data,name
    for name,token in [('NEWCRC.LST',b'FIX      DAT'),('NEWMD5.LST',b'FIX.DAT')]:
        dest=work/('AFTER-'+name);cpm('cpmcp',disk,'0:'+name,dest)
        assert token in dest.read_bytes(),name
    from fdf_format import select_fdf
    from build_z80pack_image import DEFAULT_FORMAT
    boundary=select_fdf(ROOT/'metadata/DISK.FDF',DEFAULT_FORMAT).reserved_records*128
    assert system_disk.read_bytes()[:boundary]==before[:boundary]
    for name,volume in [('system',system_disk),('work',disk)]:
        result=subprocess.run(['fsck.cpm','-T','raw','-f','bettercpm-default','-n',str(volume)],cwd=work,capture_output=True)
        (work/(name+'-filesystem.log')).write_bytes(result.stdout+result.stderr)
        assert result.returncode==0,(name,result.stdout,result.stderr)
    receipt={'status':'PASS','platform':'cpmsim','steps':len(actions),'markers':len(markers),
             'command_script_sha256':hashlib.sha256(script).hexdigest(),
             'unchanged_inputs':True,'new_lists':'PASS','filesystem':'PASS','unchanged_system_area':True,
             'model4_qualification':False}
    (work/'submit-result.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print('PASS: actual cpmsim SUBMIT/marker campaign, 20 Model 4 phases, preserved input files, new checksum lists and filesystems')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system',type=Path)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if bool(args.system)!=bool(args.output):parser.error('--system and --output must be supplied together')
    steps=[('B:CRCKSUM /HELP /VER /BOGUS\r','A0>'),
           ('B:CRCKSUM /VER /BOGUS\r','A0>'),
           ('B:CRCKSUM B:FIX.DAT /FILE=B:NEWCRC.LST\r','A0>'),
           ('B:CRCKSUM B:FIX.DAT /FILE=B:CRC.LST\r','Overwrite?'),
           ('??-[\x1bn','A0>'),
           ('B:CRCKSUM B:FIX.DAT /FILE=B:CRC.LST\r','Overwrite?'),
           ('\x03','A0>'),('B:DASM\r','*'),
           ('X\r','Restart DASM (Y/N)? '),('n','*'),('G\r','A0>'),('A:RSX LIST\r','A0>')]
    script,markers,actions=native_schedule(steps)
    lines=script.rstrip(b'\x1a').decode().splitlines()
    commands=[key[:-1] for key,_ in steps if key.startswith(('A:','B:'))]
    assert [line for line in lines if line.startswith(('A:','B:'))]==commands
    assert [key for key,_,_ in actions if key]==['??-[\x1bn','\x03','X\r','n','G\r']
    completions=[prompt for _,prompt,complete in actions if complete]
    assert len(completions)==len(set(completions))==len(markers)==7
    assert all(prompt!='A0>' for _,prompt,_ in actions)
    assert lines[lines.index(commands[3])+1]=='UI04'
    assert lines[lines.index('B:DASM')+1]=='UI10'
    assert lines[lines.index('A:RSX LIST')+1]=='UI11'
    for index,(_,prompt,complete) in enumerate(actions):
        if complete:assert markers[f'UI{index:02}.COM']==native_marker(prompt)
    for message in completions:
        cpu=Z80(b'');image=native_marker(message)
        cpu.mem[256:256+len(image)]=image
        cpu.mem[5:8]=bytes.fromhex('db71c9')
        cpu.mem[:3]=bytes.fromhex('db72c9')
        calls=[]
        def io(port):
            if port&255==114:
                assert calls==[('print',(message+'\r\n').encode()),('read',13),('print',b'\r\n'*24)]
                calls.append(('warmboot',));return 0
            assert port&255==113
            if cpu.c==9:
                text=bytes(cpu.mem[cpu.de:cpu.mem.index(36,cpu.de)])
                calls.append(('print',text))
            else:
                assert cpu.c==1 and calls==[('print',(message+'\r\n').encode())]
                calls.append(('read',13))
            cpu.bc=0xbcbc;cpu.de=0xdede;cpu.hl=0xeeee
            return 13
        cpu.port_read=io;sp=cpu.sp;cpu.run(256)
        assert cpu.sp==sp and calls[-1]==('warmboot',)
    print('PASS: SUBMIT owns every shell command; unique completion markers; seven Z80 marker executions block before clearing stale prompts and warm booting')
    if args.system:media_test(args.system,args.output)


if __name__=='__main__':main()
