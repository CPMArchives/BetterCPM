#!/usr/bin/env python3
"""Live CCP documentary predicates, exact lookup profile and damaged gateways."""
import argparse,hashlib,json,re,shutil,subprocess
from pathlib import Path
from build_ccp import assemble
from run_validation_returning import sha
from run_validation_cpmsim_monitors import audit
from test_z80pack_attributes import directory
from test_z80pack_sysgen_install import session

ROOT=Path(__file__).resolve().parents[1]
GSTATE=''' ORG 100H
 LD C,25
 CALL 5
 ADD A,'0'
 LD (DRIVE),A
 LD A,(3)
 LD (IOVAL),A
 LD E,0
 LD C,32
 CALL 5
 XOR A
 LD (80H),A
 LD A,0A5H
 LD (9200H),A
 LD DE,FCB
 LD C,15
 CALL 5
 CP 255
 JR Z,BAD
 LD DE,FCB
 LD C,20
 CALL 5
 OR A
 JR NZ,BAD
 LD A,(80H)
 CP 'Z'
 JR NZ,BAD
 LD A,(9200H)
 CP 0A5H
 JR NZ,BAD
 LD A,(0)
 CP 0C3H
 JR NZ,BAD
 LD A,(5)
 CP 0C3H
 JR NZ,BAD
 LD HL,(6)
 LD DE,0D501H
 OR A
 SBC HL,DE
 JR NZ,BAD
 LD DE,GOOD
 LD C,9
 CALL 5
 LD A,(DRIVE)
 LD E,A
 LD C,2
 CALL 5
 LD DE,IOMSG
 LD C,9
 CALL 5
 LD A,(IOVAL)
 CALL HEX
 LD DE,NL
 LD C,9
 CALL 5
 RET
BAD: LD DE,ERROR
 LD C,9
 CALL 5
 RET
HEX: PUSH AF
 RRCA
 RRCA
 RRCA
 RRCA
 CALL NIB
 POP AF
NIB: AND 15
 ADD A,'0'
 CP ':'
 JR C,PUT
 ADD A,7
PUT: LD E,A
 LD C,2
 JP 5
FCB: DB 1,'GDATA   DAT'
 DEFS 24,0
GOOD: DB 'GATE DMA OK DRIVE=','$'
IOMSG: DB ' IO=','$'
NL: DB 13,10,'$'
ERROR: DB 'GATE DMA FAILED',13,10,'$'
DRIVE: DB 0
IOVAL: DB 0
 END
'''


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('baseline','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();w=a.output.resolve();w.mkdir(parents=True,exist_ok=False);disks=w/'disks';disks.mkdir();report=json.loads((a.baseline/'report.json').read_text());image=a.baseline/report['image'];assert report['target']=='z80pack' and sha(image)==report['sha256'];shutil.copy2(a.baseline/'diskdefs',w/'diskdefs');shutil.copy2(__file__,w/'executed-runner.py')
    for d in 'ab':shutil.copy2(image,disks/f'drive{d}.dsk')
    def cpm(tool,d,*args):return subprocess.run([tool,'-T','raw','-f','bettercpm-default',str(disks/f'drive{d}.dsk'),*map(str,args)],cwd=w,check=True,capture_output=True)
    cpm('cpmrm','b','0:*.*')
    def put(d,u,name,data):
        file=w/f'{d}-{u}-{name}';file.write_bytes(data);cpm('cpmcp',d,file,f'{u}:{name}')
    def code(name,source):
        (w/(name+'.asm')).write_text(source);f=w/(name+'.COM');assemble(Path.home()/'bin/z80asm',source,f,w/(name+'.lst'),0x100);return f.read_bytes()
    marker=(ROOT/'tests/fixtures/conformance/ccpmark.mac').read_text()
    marker=marker.replace("        RET\nHEX:","""        LD DE,FM
        LD C,9
        CALL 5
        LD HL,5CH
        LD B,12
FDUMP: LD A,(HL)
        PUSH HL
        PUSH BC
        CALL HEX
        POP BC
        POP HL
        INC HL
        DJNZ FDUMP
        LD DE,NL
        LD C,9
        CALL 5
        RET
FM: DB 'FCB1 ','$'
HEX:""",1)
    for d,u,name,identity in [('a',0,'NAME','A0'),('a',0,'ONLYA','ONLYA'),('b',0,'NAME','B0'),('b',1,'NAME','B1'),('b',15,'NAME','B15')]+[('b',0,n,'COLLIDE-'+n) for n in ('DIR','ERA','REN','SAVE','TYPE','USER','DI','DIRX')]:put(d,u,name+'.COM',code(identity,marker.replace('@ID@',identity)))
    probe=(ROOT/'tests/fixtures/conformance/bdos-manual-probes.mac').read_text()
    put('a',0,'BDOPROBE.COM',code('BDOPROBE',probe))
    put('a',0,'ANCHOR.DAT',b'PUBLIC RESOURCE PROBE ANCHOR\x1A')
    put('a',0,'GSTATE.COM',code('GSTATE',GSTATE));put('a',0,'GDATA.DAT',b'Z'*128)
    io=" ORG 100H\n LD C,7\n CALL 5\n LD (VALUE),A\n LD DE,MSG\n LD C,9\n CALL 5\n LD A,(VALUE)\n CALL HEX\n LD DE,NL\n LD C,9\n CALL 5\n RET\n"+'HEX:'+GSTATE.split('HEX:',1)[1].split('FCB:',1)[0]+"MSG: DB 'IOBYTE=','$'\nNL: DB 13,10,'$'\nVALUE: DB 0\n END\n"
    put('a',0,'IOBYTE.COM',code('IOBYTE',io))
    for name,mode in (('WOP','opcode'),('WFLD','fields'),('CBOOT','cold')):
        source=" ORG 100H\n LD HL,(1)\n"+(' DEC HL\n DEC HL\n DEC HL\n' if mode=='cold' else '')+" LD (SAVED),HL\n LD DE,9200H\n LD C,26\n CALL 5\n LD E,041H\n LD C,8\n CALL 5\n XOR A\n LD (0),A\n LD (5),A\n"+(' LD HL,0DEADH\n LD (1),HL\n LD HL,0BEEFH\n LD (6),HL\n' if mode!='opcode' else '')+" LD HL,(SAVED)\n JP (HL)\nSAVED: DW 0\n END\n"
        put('a',0,name+'.COM',code(name,source))
    for name,route in (('RETCHECK','RET'),('JP0CHECK','JP 0')):
        source=" ORG 100H\n LD HL,(1)\n LD (SAVED),HL\n LD HL,HOOK\n LD (1),HL\n "+route+"\nHOOK: LD DE,MSG\n LD C,9\n CALL 5\n LD HL,(SAVED)\n JP (HL)\nMSG: DB 'PUBLIC WBOOT HOOK SEEN',13,10,'$'\nSAVED: DW 0\n END\n"
        put('a',0,name+'.COM',code(name,source))
    private=" ORG 100H\n LD HL,(0D650H)\n LD A,H\n CP 80H\n JR C,BAD\n CP 0D5H\n JR NC,BAD\n LD SP,8000H\n LD B,16\nLOOP: LD (HL),0A5H\n INC HL\n DJNZ LOOP\n JP 0\nBAD: JP 0\n END\n"
    put('a',0,'PRIVCCP.COM',code('PRIVCCP',private))
    for name,content in [('ONE.TXT',b'FIRST\r\n\x1a'),('TWO.TXT',b'SECOND\r\n\x1a'),('SYSFILE.TXT',b'SYSTEM\x1a'),('DROP.DAT',b'DROP'),('ERASE1.TMP',b'ERASE1'),('ERASE2.TMP',b'ERASE2')]:put('b',0,name,content)
    put('b',1,'KEEP.TMP',b'OTHER USER KEEP');cpm('cpmchattr','b','s','0:SYSFILE.TXT')
    trace=w/'transcript.bin';checks=[];observations=[];prompt=b'A0>_ '
    def commands():
        nonlocal prompt
        def do(command,required=(),forbidden=()):
            start=len(trace.read_bytes());yield(command.encode()+b'\r',prompt,60);delta=trace.read_bytes()[start:]
            response=delta.split(b'\n',1)[1] if b'\n' in delta else b''
            for text in required:assert text in response,(command,text,delta[-1000:])
            for text in forbidden:assert text not in response,(command,text,delta[-1000:])
            if command=='DIR SYSFILE.TXT':assert b'B0: SYSFILE' not in response
            observations.append({'command':command,'required':[x.decode() for x in required],'forbidden':[x.decode() for x in forbidden]})
        yield(b'nAmX\x08E mIxEd.TxT',b'nAmE mIxEd.TxT_ ',30)
        # The CCP redraws its cursor while waiting; raw PTY silence is not its contract.
        yield(b'',b'\rA0>nAmE mIxEd.TxT',30)
        yield(b'',None,0.25)
        assert b'MARK A0' not in trace.read_bytes(), 'dispatch occurred before Enter'
        yield(b'\r',prompt,30)
        text=trace.read_bytes();assert b'MARK A0 DU A/00 TAIL[ MIXED.TXT]' in text and b'FCB1 004D49584544202020545854' in text;checks.append('Edited mixed-case command waits for CR; tail and padded FCB uppercase')
        for command in ('',' ','   '):yield from do(command,forbidden=(b'?',b'MARK '))
        yield from do('NAME\tMIXED',forbidden=(b'MARK ',));yield from do('NAME MIXED',required=(b'MARK A0',b'TAIL[ MIXED]'))
        yield from do('NAME.COM',forbidden=(b'MARK ',));yield from do('NAME.TXT',forbidden=(b'MARK ',));checks.append('Empty/SPACE commands, TAB distinction and primary-name COM syntax')
        prompt=b'B0>_ ';yield from do('B:');yield from do('NAME',required=(b'MARK B0 DU B/00',));yield from do('ONLYA',required=(b'MARK ONLYA DU B/00',));yield from do('B:ONLYA',forbidden=(b'MARK ONLYA',));yield from do('A:NAME',required=(b'MARK A0 DU B/00',));yield from do('A:MISSING',forbidden=(b'MARK ',));yield from do('NAME',required=(b'MARK B0 DU B/00',));checks.append('Current DU wins; fixed A0 fallback; qualified lookup exact; caller DU retained after miss')
        for user in range(16):
            prompt=f'B{user}>_ '.encode();yield from do('USER '+str(user));yield from do('A0:NAME',required=(f'MARK A0 DU B/{user:02X}'.encode(),))
            if user in (1,15):yield from do('NAME',required=(f'MARK B{user} DU B/{user:02X}'.encode(),))
        prompt=b'B0>_ ';yield from do('USER 0');checks.append('USER 0..15 shares BDOS user state; local user copies take precedence over A0')
        yield from do('DI',required=(b'MARK COLLIDE-DI',));yield from do('DIRX',required=(b'MARK COLLIDE-DIRX',))
        for command,expected in [('DIR ONE.TXT',b'ONE'),('DIR SYSFILE.TXT',b''),('TYPE ONE.TXT',b'FIRST'),('ERA DROP.DAT',b''),('REN NEW.TXT=ONE.TXT',b''),('REN NEW.TXT=TWO.TXT',b'FILE EXISTS'),('REN X.TXT=MISSING.TXT',b'NO FILE'),('REN B:X.TXT=A:README.TXT',b'Invalid filespec.'),('SAVE X BAD.DAT',b'?')]:yield from do(command,required=(expected,) if expected else (),forbidden=(b'MARK COLLIDE-',))
        yield from do('DIR *.TXT',required=(b'NEW',b'TWO'),forbidden=(b'SYSFILE',b'MARK COLLIDE-'));yield from do('DIR',required=(b'NAME',),forbidden=(b'SYSFILE',b'MARK COLLIDE-'));yield from do('ERA *.TMP',forbidden=(b'ALL (Y/N)',b'MARK COLLIDE-'))
        yield from do('DIR DROP.DAT',required=(b'NO FILE',))
        yield from do('TYPE NEW.TXT',required=(b'FIRST',))
        yield from do('TYPE TWO.TXT',required=(b'SECOND',))
        yield from do('DIR ONE.TXT',required=(b'NO FILE',))
        yield from do('A0:IOBYTE',required=(b'IOBYTE=95',))
        yield from do('STAT DEV:',required=(b'CON',b'CRT'))
        yield from do('STAT LST:=CRT:')
        yield from do('A0:IOBYTE',required=(b'IOBYTE=55',))
        yield from do('STAT CON:=ZZZ:',required=(b'Invalid Assignment',))
        yield from do('A0:IOBYTE',required=(b'IOBYTE=55',))
        yield from do('STAT LST:=LPT:')
        yield from do('A0:IOBYTE',required=(b'IOBYTE=95',))
        checks.append('STAT device display, valid assignment, invalid-name preservation and restoration')
        checks.append('Exact resident names precede colliding COMs; DIR visibility, ERA exact/partial wildcard, REN outcomes and invalid SAVE')
        before=sha(disks/'driveb.dsk');yield(b'ERA *.*\r',b'ALL (Y/N)? ',30);yield(b'N\r',prompt,30);assert sha(disks/'driveb.dsk')==before
        yield(b'ERA *.*\r',b'ALL (Y/N)? ',30);yield(b'Y\r',prompt,30);yield from do('DIR',forbidden=(b'B0: ',b'MARK COLLIDE-',));checks.append('All-wildcard ERA N preserves disk and Y erases admitted files; other users/SYS preserved')
        prompt=b'B7>_ ';yield from do('B7:')
        yield from do('A0:RETCHECK',forbidden=(b'PUBLIC WBOOT HOOK SEEN',))
        yield from do('A0:JP0CHECK',required=(b'PUBLIC WBOOT HOOK SEEN',))
        yield from do('A0:PRIVCCP')
        yield from do('A0:NAME',required=(b'MARK A0 DU B/07',))
        checks.append('RET bypasses public WBOOT interception; JP0 uses it; private-stack CCP overwrite reconstructs')
        for program in ('WOP','WFLD','CBOOT'):
            prompt=b'B7>_ ';yield from do('B7:');yield(f'A0:{program}\r'.encode(),b'>_ ',60)
            start=len(trace.read_bytes());yield(b'A0:GSTATE\r',b'>_ ',60);delta=trace.read_bytes()[start:];assert b'GATE DMA FAILED' not in delta and b'GATE DMA OK DRIVE='+ (b'0' if program=='CBOOT' else b'1') in delta,delta[-1200:];assert (b'IO=95' if program=='CBOOT' else b'IO=41') in delta
            observations.append({'program':program,'gateways_reconstructed':True,'dma_at_next_transient':128,'cold_drive_A':program=='CBOOT','scope':'saved configured BIOS entry; corrupt public gateways/nondefault DMA; cold user value not prescribed'})
            prompt=b'A0>_ ';yield from do('A0:')
        checks.append('Saved WBOOT restores damaged opcodes/operands and DMA; configured BOOT restores A drive and saved cold IOBYTE')
        yield(b'A0:BDOPROBE\r',b'0420 INPUT READY: type BUFFER42 then ENTER\r\n',30)
        yield(b'BUFFER42\r',b'OR-0519 PASS: BIOS DPH matches BDOS DPB and ALV for A B A',30)
        yield(b'',prompt,30)
        assert b'OR-0420 PASS:' in trace.read_bytes() and b'OR-0420 FAIL' not in trace.read_bytes() and b'OR-0519 FAIL' not in trace.read_bytes()
        checks.append('Actual buffered-input/DMA guard and A/B/A BIOS-DPH versus BDOS resource pointers')
        yield(b'BYE\r',b'System halted',10)
    simulator=Path.home()/'projects/git/z80pack/cpmsim/cpmsim'
    try:session(simulator,disks,commands(),trace)
    except Exception as e:(w/'incomplete.json').write_text(json.dumps({'error':str(e),'checks':checks,'observations':observations},indent=2)+'\n');raise
    raw_directory=directory(disks/'driveb.dsk',w/'diskdefs')
    visible=[r for n in range(0,len(raw_directory),32) if (r:=raw_directory[n:n+32])[0]==0]
    assert len(visible)==1 and bytes(v&127 for v in visible[0][1:12])==b'SYSFILE TXT' and visible[0][10]&128, 'all-wildcard erase left incorrect user-zero inventory'
    listed=cpm('cpmls','b').stdout.decode();(w/'directory.txt').write_text(listed)
    for user,name,expected in ((0,'SYSFILE.TXT',b'SYSTEM\x1a'),(1,'KEEP.TMP',b'OTHER USER KEEP')):
        file=w/f'after-{user}-{name}';cpm('cpmcp','b',f'{user}:{name}',file);assert file.read_bytes()==expected
    fs=subprocess.run(['fsck.cpm','-T','raw','-f','bettercpm-default','-n',str(disks/'driveb.dsk')],cwd=w,check=True,capture_output=True)
    (w/'b-filesystem.txt').write_bytes(fs.stdout+fs.stderr)
    shipped=audit(a.baseline,report,w,disks/'drivea.dsk');assert sha(image)==report['sha256']
    result={'status':'PASS','baseline_sha256':report['sha256'],'simulator_sha256':sha(simulator),'checks':checks,'observations':observations,'unchanged_shipped_files':shipped,'cards':['0015','0020','0027','0464','0465','0466','0475','0477','0479','0480','0481','0482','0483','0484','0485','0486','0487','0488','0489','0493','0494','0495','0567','0570','0572','0574','0578','0509','0590','0593','0595','0612','0420','0519'],'lookup_profile':'BetterCP/M fixed A0 fallback: 0493/0494 are explicitly an extension of generic single-DU lookup, not generic suite PASS rows.'};(w/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS live CCP accounting and boot/gateway oracles',w)


if __name__=='__main__':main()
