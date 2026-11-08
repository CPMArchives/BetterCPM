#!/usr/bin/env python3
"""Reaccept shipped /VER paths on both platforms using private System/Utilities."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
from add_cpm_file_to_dmk import extract_raw,add_file,FILESYSTEM_FIRST_SECTOR,SECTOR_SIZE,DIRECTORY_ENTRIES
from build_montezuma_extended_790k import build as dmk
from build_z80pack_image import disk_definition,DEFAULT_FORMAT
from fdf_format import select_fdf
from run_trs80_command import DEFAULT_EMULATOR
from trs80gp_launch import run as launch
from test_z80pack_sysgen_install import session
from utility_versions import identities,banner
from utility_help import resident_identification
ROOT=Path(__file__).resolve().parents[1]
sha=lambda b:hashlib.sha256(b).hexdigest()

def resident_marker(work):
    """A single private checkpoint: show tail/TPA, block, reclaim CPX RAM, WBOOT."""
    from build_ccp import assemble
    source='''        ASEG
        ORG 100H
        LD SP,3000H
        LD DE,HEAD
        LD C,9
        CALL 5
        LD HL,81H
        LD A,(80H)
        LD B,A
MTAIL:  LD E,(HL)
        PUSH BC
        PUSH HL
        LD C,2
        CALL 5
        POP HL
        POP BC
        INC HL
        DJNZ MTAIL
        LD DE,TPATXT
        LD C,9
        CALL 5
        LD HL,(6)
        LD A,H
        CALL HEX
        LD A,L
        CALL HEX
        LD DE,NL
        LD C,9
        CALL 5
        LD C,1
        CALL 5
        LD DE,CLEAR
        LD C,9
        CALL 5
        LD HL,(6)
        LD DE,3000H
        OR A
        SBC HL,DE
        LD D,H
        LD E,L
        INC DE
        LD BC,2FFFH
        LD (HL),0A5H
        LDIR
        JP 0
HEX:    PUSH AF
        RRCA
        RRCA
        RRCA
        RRCA
        CALL NIB
        POP AF
NIB:    AND 15
        ADD A,'0'
        CP '9'+1
        JR C,DIGIT
        ADD A,7
DIGIT:  LD E,A
        PUSH HL
        LD C,2
        CALL 5
        POP HL
        RET
HEAD:   DB 'RCP CHECK','$'
TPATXT: DB ' TPA=','$'
NL:     DB 13,10,'$'
CLEAR:  REPT 24
        DB 13,10
        ENDM
        DB '$'
'''
    return assemble(Path.home()/'bin/z80asm',source,work/'UICHECK.COM',work/'uicheck.lst',256)

def resident(a):
    import re
    from utility_help import RESIDENT_SCREENS,text
    from build_montezuma_extended_790k import build as make_dmk
    from run_trs80_command import key_args
    a.output.mkdir(parents=True,exist_ok=False);w=a.output.resolve()
    native=a.platform=='model4';target='trs80gp' if native else 'z80pack'
    r=json.loads((a.system/target/'report.json').read_text())
    base=a.system/target/r['image'];original=base.read_bytes()
    definitions=(a.system/target/'diskdefs').read_text();(w/'diskdefs').write_text(definitions)
    if native:disk=w/'a.raw';disk.write_bytes(extract_raw(original))
    else:
        (w/'disks').mkdir();disk=w/'disks/drivea.dsk';disk.write_bytes(original)
        for letter in 'bcd':(w/f'disks/drive{letter}.dsk').write_bytes(original)
    def cpm(tool,*args,check=True):
        return subprocess.run([tool,'-T','raw','-f','bettercpm-default',str(disk),*map(str,args)],cwd=w,check=check,capture_output=True)
    def put(name,data,user=0):
        p=w/name;p.write_bytes(data);cpm('cpmrm',f'{user}:'+name,check=False)
        result=cpm('cpmcp',p,f'{user}:'+name);assert result.returncode==0,(name,result.stderr)
    removed=[]
    for name in RESIDENT_SCREENS:
        before=w/('BEFORE-'+name+'.COM')
        cpm('cpmcp','0:'+name+'.COM',before,check=False)
        if before.exists():removed.append(name+'.COM')
        cpm('cpmrm','0:'+name+'.COM',check=False)
    module=(ROOT/'build/cpx/RCP.CPX').read_bytes();put('RCP.CPX',module)
    fixture=b'RESIDENT QUERY FILE\r\n\x1a';put('UIFILE.TXT',fixture)
    different=b'PRESERVE DIFFERENT CONTENT\r\n\x1a'
    if a.operations:
        for name in ('UIDIFF.TXT','UIOVR.TXT','UIMOVE.TXT'):put(name,different)
        put('UIKEEP.TXT',fixture,5);put('UIKEEP2.TXT',different,5)
    marker=resident_marker(w);put('UICHECK.COM',marker)
    # Every checkpoint overwrites the upper 12 KiB of transient RAM before
    # WBOOT. Subsequent help proves reconstruction; the printed TPA is audited.
    cases=[]
    for name in RESIDENT_SCREENS:
        cases.extend([(name+' /H',text(name,identity=banner(name,True),resident=True)),
                      (name+' /VER',resident_identification(name)),
                      (name+' /HELPER','Invalid usage.')])
    cases += [('ERA A0:UIFILE.TXT /VER /HELP /BOGUS',text('ERA',identity=banner('ERA',True),resident=True)),
              ('COPY A0:UIFILE.TXT A0:BAD.TXT /VER /H',text('COPY',identity=banner('COPY',True),resident=True)),
              ('TYPE A0:UIFILE.TXT','RESIDENT QUERY FILE'),('USER 32','Invalid usage.'),
              ('CLS EXTRA','Invalid usage.'),('VER FILE','Invalid usage.')]
    responses={}
    if a.operations:
        cases += [('COPY A0:UIFILE.TXT A0:UICOPY.TXT',''),
                  ('REN UICOPY2.TXT=A0:UICOPY.TXT',''),('ERA A0:UICOPY2.TXT',''),
                  ('MOVE A0:UIMOVE.TXT A0:UIMOVED.TXT',''),
                  ('COPY A0:UIDIFF.TXT A0:UIFILE.TXT','FILE EXISTS'),
                  ('COPY A0:UIFILE.TXT A0:UIOVR.TXT /O',''),('ERA A5:*.*','')]
        responses[len(cases)-1]=('ALL (Y/N)? ','N\r')
    script=[]
    for i,(command,_) in enumerate(cases):script+=['CLS',command,f'UICHECK {i:02d}']
    body=('\r\n'.join(script)+'\r\n\x1a').encode();put('UIQUAL.SUB',body)
    if native:put('STARTUP.SUB',b'RSX LOAD M4SCRN\r\nRSX LOAD ADM3A\r\nSUBMIT UIQUAL\r\n\x1a')
    else:cpm('cpmrm','0:STARTUP.SUB',check=False)  # isolate queries from cold-start SUBMIT writes
    # Verify the executed module and absent transients before any launch.
    for name,data in [('RCP.CPX',module),('UIFILE.TXT',fixture)]:
        p=w/('PRE-'+name);assert cpm('cpmcp','0:'+name,p).returncode==0
        assert p.read_bytes()[:len(data)]==data
    for name in RESIDENT_SCREENS:
        unexpected=w/'UNEXPECTED.COM';unexpected.unlink(missing_ok=True)
        cpm('cpmcp','0:'+name+'.COM',unexpected,check=False)
        assert not unexpected.exists(),name
    initial=disk.read_bytes();boundary=FILESYSTEM_FIRST_SECTOR*SECTOR_SIZE if native else 0
    receipt={'status':'PREPARED','platform':a.platform,'steps':len(cases),'system_sha256':sha(original),
             'rcp_sha256':sha(module),'removed_transients':removed,
             'verified_absent_transients':[n+'.COM' for n in RESIDENT_SCREENS],'resident_only':True,
             'scope':'resident queries/errors, exact help, preserved files, WBOOT reconstruction and transient TPA observations',
             'operations':a.operations}
    if native:
        image=w/'a.dmk';image.write_bytes(make_dmk(initial))
        invocation=[str(a.emulator),'-m4','-batch','-turbo','-sx','-sfmute','-ktx','-d0',str(image),'-itime','60000']
        for i in range(len(cases)):
            if i in responses:
                prompt,response=responses[i]
                invocation+=['-iw',prompt]+key_args(response,delay=25)
            invocation+=['-iw',f'RCP CHECK {i:02d}','-id','60','-it']+key_args('\r',delay=25)+['-id','120']
        invocation+=['-ix'];(w/'invocation.json').write_text(json.dumps(invocation,indent=2)+'\n')
    (w/'cases.json').write_text(json.dumps(cases,indent=2)+'\n');(w/'report.json').write_text(json.dumps(receipt,indent=2)+'\n')
    if a.prepare_only:print('PREPARED:',w);return
    if native:
        launch(invocation,cwd=w,timeout=600)
        captures=sorted(w.glob('trs80-text-*.bin'),key=lambda p:int(p.stem.rsplit('-',1)[1]))
        assert len(captures)==len(cases)
        screens=[bytes(x&127 for x in p.read_bytes()[:1920]).decode() for p in captures]
        for (command,wanted),screen in zip(cases,screens):
            # Native screen snapshots contain fixed-width rows.
            for line in wanted.splitlines():assert line in screen,(command,line,screen)
        disk.write_bytes(extract_raw((w/'a.dmk').read_bytes()))
        assert disk.read_bytes()[:boundary]==initial[:boundary]
    else:
        steps=[]
        for i,(command,_) in enumerate(cases):
            steps += [(b'CLS\r',b'A0>_ ',30)]
            if i in responses:
                prompt,response=responses[i]
                steps += [(command.encode()+b'\r',prompt.encode(),30),(response.encode(),b'A0>_ ',30)]
            else:steps += [(command.encode()+b'\r',b'A0>_ ',30)]
            steps += [(f'UICHECK {i:02d}\r'.encode(),f'RCP CHECK {i:02d}'.encode(),30),
                      (b'',b'TPA=',30),(b'\r',b'A0>_ ',30)]
        output=session(a.simulator,w/'disks',steps,w/'transcript.bin').decode(errors='replace')
        screens=output.split('RCP CHECK ')
        assert len(screens)==len(cases)+1
        for (command,wanted),screen in zip(cases,screens):assert wanted in screen,(command,wanted,screen)
        if not a.operations:assert disk.read_bytes()==initial,'read-only resident campaign changed the filesystem'
    expected=[(0,'UIFILE.TXT',fixture),(0,'RCP.CPX',module)]
    absent=['BAD.TXT']
    if a.operations:
        expected += [(0,'UIDIFF.TXT',different),(0,'UIOVR.TXT',fixture),(0,'UIMOVED.TXT',different),
                     (5,'UIKEEP.TXT',fixture),(5,'UIKEEP2.TXT',different)]
        absent+=['UIMOVE.TXT','UICOPY.TXT','UICOPY2.TXT']
    for user,name,data in expected:
        p=w/('READ-'+name);assert cpm('cpmcp',f'{user}:'+name,p).returncode==0
        assert p.read_bytes()[:len(data)]==data
    for name in absent:
        unexpected=w/('ABSENT-'+name);unexpected.unlink(missing_ok=True)
        cpm('cpmcp','0:'+name,unexpected,check=False);assert not unexpected.exists(),name
    tpas=re.findall(r'TPA=([0-9A-F]{4})','\n'.join(screens));assert tpas and len(set(tpas))==1,tpas
    result=subprocess.run(['fsck.cpm','-T','raw','-f','bettercpm-default','-n',str(disk)],cwd=w,capture_output=True)
    (w/'filesystem.log').write_bytes(result.stdout+result.stderr)
    assert result.returncode==0,result.stdout+result.stderr
    assert base.read_bytes()==original
    receipt.update(status='PASS',tpa_ceiling=tpas[0],filesystem='PASS',unchanged_inputs=True)
    (w/'report.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('system','output','simulator'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--utilities',type=Path)
    p.add_argument('--resident',action='store_true')
    p.add_argument('--operations',action='store_true',help='Include file operations and ERA refusal in the resident campaign')
    p.add_argument('--platform',choices=('cpmsim','model4'),default='cpmsim')
    p.add_argument('--prepare-only',action='store_true')
    p.add_argument('--emulator',type=Path,default=DEFAULT_EMULATOR)
    a=p.parse_args()
    if a.resident:return resident(a)
    if a.utilities is None:p.error('--utilities is required without --resident')
    a.output.mkdir(parents=True,exist_ok=False);metadata=identities();result={'status':'IN_PROGRESS','platforms':{}}
    for platform in ('z80pack','trs80gp'):
        w=a.output/platform;w.mkdir();r=json.loads((a.system/platform/'report.json').read_text());system=a.system/platform/r['image'];source=system.read_bytes()
        utilities=next(a.utilities.glob('*'+platform+('*.dsk' if platform=='z80pack' else '*.dmk')));ub=utilities.read_bytes()
        names=[x['name'][:-4] for x in r['included'] if x['name'].endswith('.COM') and x['name'][:-4] in metadata]
        cases=[('A:'+n,'BetterCP/M '+n if n not in ('DDT','DUMP','SQ','USQ','CR','UNCR','LZH','UNLZH') else n,n) for n in names]
        cases += [('B:'+n,n if n!='XSUB' else 'BetterCP/M XSUB',n) for n in ('DDT','DUMP','XSUB','SQ','USQ','CR','UNCR','LZH','UNLZH')]
        if platform=='z80pack':
            disks=w/'disks';disks.mkdir();(disks/'drivea.dsk').write_bytes(source)
            for letter in 'bcd':(disks/f'drive{letter}.dsk').write_bytes(ub)
            steps=[]
            for command,title,name in cases:
                version,build=metadata[name];expected=f'{title} {version} (Build {build:03d})'.encode()
                steps.extend([((command+' /VER ignored').encode()+b'\r',expected,30),(b'',b'A0>_ ',30)])
            transcript=session(a.simulator,disks,steps,w/'transcript.bin')
            assert b'Invalid /VER usage' not in transcript
            assert (disks/'driveb.dsk').read_bytes()==ub
            (w/'diskdefs').write_text(disk_definition(select_fdf(ROOT/'metadata/DISK.FDF',DEFAULT_FORMAT)))
            assert subprocess.run(['fsck.cpm','-T','raw','-f','bettercpm-default','-n',str(disks/'drivea.dsk')],cwd=w,capture_output=True).returncode==0
        else:
            raw=extract_raw(source);directory=FILESYSTEM_FIRST_SECTOR*SECTOR_SIZE
            for i in range(DIRECTORY_ENTRIES):
                at=directory+i*32
                if raw[at]==0 and raw[at+1:at+12]==b'STARTUP SUB':raw[at]=0xe5
            script=['RSX LOAD M4SCRN','RSX LOAD ADM3A']
            for i,(command,title,name) in enumerate(cases):
                mark=f'QUERY CASE {i:02d} DONE';program=f'Q{i:02d}'
                add_file(raw,program+'.COM',bytes.fromhex('110b010e09cd0500c30000')+(mark+'\r\n$').encode())
                script += [command+' /VER ignored',program]
            add_file(raw,'STARTUP.SUB',('\r\n'.join(script)+'\r\n\x1a').encode());disk=w/'a.dmk';disk.write_bytes(dmk(raw));(w/'b.dmk').write_bytes(ub)
            invocation=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-ktx','-d0',str(disk),'-d1',str(w/'b.dmk'),'-itime','60000']
            for i in range(len(cases)):invocation+=['-iw',f'QUERY CASE {i:02d} DONE','-id','120','-it']
            invocation+=['-ix'];(w/'invocation.json').write_text(json.dumps(invocation,indent=2)+'\n');launch(invocation,cwd=w,timeout=1200)
            captures=sorted(w.glob('trs80-text-*'),key=lambda p:int(p.stem.rsplit('-',1)[1]));assert len(captures)==len(cases)
            for (command,title,name),capture in zip(cases,captures):
                screen=bytes(x&127 for x in capture.read_bytes()[:1920]);version,build=metadata[name]
                assert f'{title} {version} (Build {build:03d})'.encode() in screen,(command,screen)
            assert (w/'b.dmk').read_bytes()==ub
        assert system.read_bytes()==source and utilities.read_bytes()==ub
        result['platforms'][platform]={'status':'PASS','cases':len(cases),'commands':[x[0] for x in cases],'system_sha256':sha(source),'utilities_sha256':sha(ub),'utilities_unchanged':True}
        (a.output/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    result['status']='PASS';(a.output/'report.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS shipped utility /VER queries on both platforms')


if __name__=='__main__':main()
