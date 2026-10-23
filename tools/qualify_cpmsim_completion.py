#!/usr/bin/env python3
"""Trace remaining cpmsim stack paths and final-BIOS error recovery.

Runs intact qualified system tracks. Fault probes temporarily replace one BIOS
vector with a self-restoring final-error leaf; this tests BDOS response after
driver retries, not the controller's retry policy. Host SP tracing is separate
from the guest and must be corroborated with the ordinary simulator.
"""
from pathlib import Path
import argparse,hashlib,json,os,re,sys

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('root',type=Path);p.add_argument('--output',type=Path,required=True)
p.add_argument('--simulator',type=Path,required=True)
p.add_argument('--campaign',choices=('observer','smoke','faults','console','lifecycle','rollback','all'),default='all')
p.add_argument('--untraced',action='store_true')
p.add_argument('--match',default='.',help='case-name regex for focused development runs')
a=p.parse_args();root=a.root.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(root/'tools'))
import part7_probe_support as h
from build_z80pack_image import symbols
h.out=out;h.sim=a.simulator.resolve()
g=symbols(root/'build/z80pack/gateway.lst');b=symbols(root/'build/bdos/bdos.lst');c=symbols(root/'build/ccp/ccp.lst')
L=h.L
bands=[('bdos',b['UB_STACK'],b['UB_STKTOP'],0),('system',g['SYS_STACK'],g['SYS_STKTOP'],0),
 ('ccp',c['CCP_STACK']-c['CCP_ENTRY'],c['CCP_STKTOP']-c['CCP_ENTRY'],g['ECB_CCPBASE']),
 ('stage1',0x4c0,0x500,0),('raw_reload',0x80,0x100,0),('stream',0xd00,0x1000,0),
 ('early_manager',L['RSX']+len((root/'build/system/rsxresolver.bin').read_bytes()),L['RSX']+0x3fd,0),
 ('reader',0x6615,0x6700,0),('manager',0x6f00,0x7000,0),
 ('config',0x3e00,0x4000,0),('sysgen',0x3d00,0x3f00,0)]
cfg=out/'stack-bands.cfg';cfg.write_text(''.join(f'{n} {lo:x} {hi:x} {ptr:x}\n' for n,lo,hi,ptr in bands))
ex=symbols(root/'build/z80pack/extensions.lst')
commit_cfg=out/'commit-watch.cfg'
commit_cfg.write_text(f"{L['RSX']:x} {ex['EX_RETURN']:x} "+' '.join(f'{x:x}' for x in (root/'build/system/R3COMIT.RSX').read_bytes()[:16])+'\n')
results={};last_commit_windows=None
def run(w,commands,stem='transcript'):
    global last_commit_windows
    last_commit_windows=None
    if a.untraced:
        os.environ.pop('BCPM_STACK_CONFIG',None);os.environ.pop('BCPM_STACK_TRACE',None)
        os.environ.pop('BCPM_COMMIT_CONFIG',None)
    else:
        os.environ['BCPM_STACK_CONFIG']=str(cfg);os.environ['BCPM_STACK_TRACE']=str(w/(stem+'-stacks.txt'))
        os.environ['BCPM_COMMIT_CONFIG']=str(commit_cfg)
    t=h.run(w,commands,stem=stem)
    rows={}
    if not a.untraced:
        trace=(w/(stem+'-stacks.txt')).read_text()
        assert 'OVERFLOW' not in trace,trace[-5000:]
        assert 'DISK_IO_DURING_COMMIT' not in trace,trace[-5000:]
        assert trace.count('COMMIT_BEGIN')==trace.count('COMMIT_END'),trace[-5000:]
        last_commit_windows=trace.count('COMMIT_BEGIN')
        for name,used,low,top,sp,pc in re.findall(r'^MIN (\w+) (\d+) ([0-9a-f]+) ([0-9a-f]+) ([0-9a-f]+) ([0-9a-f]+)$',trace,re.M):
            rows[name]={'used':int(used),'low':int(low,16),'top':int(top,16),'sp':int(sp,16),'pc':int(pc,16)}
        assert {'bdos','system','ccp','stage1','raw_reload','stream'}<=set(rows),rows
    return t,rows
def save(name,rows,**extra):
    results[name]={'stacks':rows,'disk_free_commit_windows':last_commit_windows,**extra}
    (out/'results.json').write_text(json.dumps({'profile':json.loads((root/'assessment-profile.json').read_text())['compatibility_id'],'untraced':a.untraced,'system_raw_sha256':hashlib.sha256((root/'assessment-media/system.raw').read_bytes()).hexdigest(),'results':results},indent=2)+'\n')
    print('PASS '+name+' '+json.dumps({n:r['used'] for n,r in rows.items()}),flush=True)

PRINT='''
PRINT: LD A,(HL)
 INC HL
 OR A
 RET Z
 OUT (1),A
 JR PRINT
'''

if a.campaign in ('observer','all') and not a.untraced:
    # Deliberate probe-only violations prove that neither observer can silently
    # report success when the property it checks is violated.
    for label in ('overflow','commit-io'):
        w=h.case('observer-'+label)
        if label=='overflow':
            src=f' LD SP,{b["UB_STKTOP"]}\n'+(' PUSH HL\n'*21)+' HALT\n'
            expected='OVERFLOW bdos';watch=commit_cfg
        else:
            src=' NOP\n'*16+' LD A,0\n OUT (13),A\n HALT\n'
            expected='DISK_IO_DURING_COMMIT';watch=w/'commit-watch.cfg'
            watch.write_text('100 ffff '+'00 '*16+'\n')
        h.put(w,'CHECK.COM',h.asm(w,'check',src))
        os.environ['BCPM_STACK_CONFIG']=str(cfg)
        os.environ['BCPM_STACK_TRACE']=str(w/'observer.txt')
        os.environ['BCPM_COMMIT_CONFIG']=str(watch)
        try:h.run(w,['CHECK'])
        except (AssertionError,OSError):pass
        else:raise AssertionError('observer did not reject '+label)
        trace=(w/'observer.txt').read_text();assert expected in trace,trace[-3000:]
        save('observer-'+label,{},intentional_probe_violation_detected=True)

def fault_source(operation,kind):
    # A fresh file is opened before arming. Make has a separate unused stem;
    # zero-fill targets a new block; close follows a successful new write.
    setup=''
    if operation=='close':setup=' LD DE,FCB\n LD C,21\n CALL 5\n'
    if operation=='select':setup=' LD DE,2\n LD C,37\n CALL 5\n'
    if operation=='make':setup=" LD A,'N'\n LD (FCB+1),A\n"
    if operation=='zero':setup=' LD A,16\n LD (FCB+33),A\n'
    if operation=='extent':setup=' LD A,128\n LD (FCB+33),A\n'
    fn={'select':14,'open':15,'close':16,'find':17,'delete':19,'read':20,'write':21,'make':22,'random':33,'zero':40,'extent':40}[operation]
    parameter='1' if operation=='select' else 'FCB'
    vector=39 if kind=='read' else 42
    return f''' LD SP,03000H
 LD DE,FCB
 LD C,15
 CALL 5
 CP 0FFH
 JP Z,BAD
 LD DE,BUFFER
 LD C,26
 CALL 5
{setup}
 LD DE,SCREENSET
 LD C,9
 CALL 5
 LD HL,READY
 CALL PRINT
 LD HL,(1)
 LD DE,{vector-3+1}
 ADD HL,DE
 LD (VECPTR),HL
 LD E,(HL)
 INC HL
 LD D,(HL)
 LD (OLDVEC),DE
 DEC HL
 LD DE,FAILONCE
 LD (HL),E
 INC HL
 LD (HL),D
 LD DE,{parameter}
 LD C,{fn}
 CALL 5
 LD A,(HIT)
 CP 1
 JP NZ,BAD
 LD HL,DONE
 CALL PRINT
 JP 0
FAILONCE:
 LD HL,(VECPTR)
 LD DE,(OLDVEC)
 LD (HL),E
 INC HL
 LD (HL),D
 LD A,1
 LD (HIT),A
 RET
BAD: LD HL,FAILMSG
 CALL PRINT
 JP 0
{PRINT}
VECPTR: DW 0
OLDVEC: DW 0
HIT: DB 0
FCB: DB 0,'STACK   DAT'
 REPT 24
 DB 0
 ENDM
BUFFER: DS 128
READY: DB 'FAULT ARMED',13,10,0
DONE: DB 'CALLER RESUMED',13,10,0
FAILMSG: DB 'PROBE FAILED',13,10,0
'''

if a.campaign in ('smoke','all'):
    w=h.case('normal')
    t,rows=run(w,['DIR','CONFIG /SHOW','SYSGEN A: B:STACK.SYS','STAT MEM'])
    assert 'Package exported and verified.' in t
    assert h.maps(t)[-1]['maximum']==(L['TPA']-256)//128*128
    save('normal',rows,tpa=h.maps(t)[-1]['maximum'])

if a.campaign in ('faults','all'):
    cases=[('select','read'),('open','read'),('find','read'),('read','read'),('random','read'),('make','read'),('make','write'),('write','write'),('close','write'),('delete','write'),('zero','write'),('extent','write')]
    modes=[(None,'',()),('ADM3A','screen',()),
        ('ADM3A','ADM3A-lower-row',(27,61,52,32)),
        ('ADM3A','ADM3A-reverse',(27,61,52,32,15)),
        ('ADM3A','ADM3A-scroll-reverse',(27,61,55,32,15)),
        ('VT52','VT52-scroll',(27,89,55,32)),
        ('ANSI','ANSI-reverse',tuple(b'\x1b[21;1H\x1b[7m')),
        ('ANSI','ANSI-region-reverse',tuple(b'\x1b[5;24r\x1b[24;1H\x1b[1;7m'))]
    for personality,label,screen_setup in modes:
        screens=personality is not None
        for operation,kind in (cases if label in ('','screen') else [('select','read')]):
            for action in ('ignore','abort'):
                name=f'{operation}-{kind}-{action}'+('-'+label if label else '')
                if not re.search(a.match,name):continue
                w=h.case(name);h.put(w,'STACK.DAT',bytes(range(128)))
                source=fault_source(operation,kind)+'\nSCREENSET: DB '+','.join(map(str,(*screen_setup,36)))+'\n'
                h.put(w,'FAULT.COM',h.asm(w,'fault',source))
                commands=['RSX LOAD ANSISCRN','RSX LOAD '+personality] if screens else []
                prompt=b'\x1b[7m \x1b[0m ' if personality in ('ADM3A','VT52') else b'>_ '
                # All screen output goes through the admitted real screen pair.
                if screens:commands=[commands[0],(commands[1].encode()+b'\r',prompt,25)]
                # Reverse state legitimately survives warm boot and can elide
                # the ADM3A cursor's SGR transitions. Still wait for the cursor,
                # not an earlier textual prefix of the editor's redraw.
                recovery_prompt=b'>  ' if personality=='ADM3A' and 'reverse' in label else prompt
                commands += [(b'FAULT\r',b'Bad Sector',25),(b'I' if action=='ignore' else b'\x03',recovery_prompt,25)]
                if operation=='select':commands += [(b'A:\r',recovery_prompt,25)]
                if screens:commands += [((f'RSX UNLOAD {personality}\r').encode(),b'A0>_ ',25),'RSX UNLOAD ANSISCRN']
                expected=(L['TPA']-256)//128*128
                commands += [(b'STAT MEM\r',f'Maximum loadable COM: {expected} bytes'.encode(),25),(b'',b'A0>_ ',25)]
                t,rows=run(w,commands)
                assert t.count('Bad Sector')==1 and 'PROBE FAILED' not in t,t
                # Ignoring a failed directory read does not certify its stale
                # bytes. MAKE subsequently detects the checksum change and
                # correctly takes the independent read-only warm-boot exit.
                read_only_exit=(operation=='make' and kind=='read' and action=='ignore')
                assert ('CALLER RESUMED' in t)==(action=='ignore' and not read_only_exit),t
                if read_only_exit:assert 'Disk R/O' in t,t
                assert h.maps(t)[-1]['maximum']==(L['TPA']-256)//128*128
                save(name,rows,error_seen=True,caller_resumed='CALLER RESUMED' in t,read_only_exit=read_only_exit,recovery=True)

if a.campaign in ('console','all'):
    for personality in (None,'ADM3A','VT52','ANSI'):
        screens=personality is not None
        name='console-'+(personality or 'basic')
        if not re.search(a.match,name):continue
        w=h.case(name)
        src=''' LD SP,03000H
 LD A,(3)
 LD (OLDIO),A
 LD A,015H
 LD (3),A
 LD B,26
LOOP: PUSH BC
 LD DE,LINE
 LD C,9
 CALL 5
 POP BC
 DJNZ LOOP
 LD HL,READY
 CALL PRINT
 LD DE,INPUT
 LD C,10
 CALL 5
 LD A,(INPUT+1)
 CP 2
 JR NZ,BAD
 LD HL,(INPUT+2)
 LD DE,04847H
 OR A
 SBC HL,DE
 JR NZ,BAD
 LD HL,DONE
 JR FINISH
BAD: LD HL,FAILMSG
FINISH: CALL PRINT
 LD A,(OLDIO)
 LD (3),A
 JP 0
'''+PRINT+'''
OLDIO: DB 0
INPUT: DB 40,0
 REPT 40
 DB 0
 ENDM
READY: DB 'INPUT READY',13,10,0
DONE: DB 'CONSOLE PASS',13,10,0
FAILMSG: DB 'CONSOLE FAILED',13,10,0
LINE: DB '''+repr('X'*77)+''',9,'B',8,'C',13,10,'$'
'''
        h.put(w,'CHAR.COM',h.asm(w,'char',src))
        prompt=b'\x1b[7m \x1b[0m ' if personality in ('ADM3A','VT52') else b'>_ '
        commands=['RSX LOAD ANSISCRN',(('RSX LOAD '+personality+'\r').encode(),prompt,25)] if screens else []
        commands += [(b'CHAR\r',b'INPUT READY',25),(b'\x10A\tB\x08C\x12\x05D\x18EF\x15\x10GH\r',b'CONSOLE PASS',25),(b'',prompt,25)]
        if screens:commands += [(('RSX UNLOAD '+personality+'\r').encode(),b'A0>_ ',25),'RSX UNLOAD ANSISCRN']
        commands+=['STAT MEM']
        t,rows=run(w,commands)
        assert 'CONSOLE FAILED' not in t and h.maps(t)[-1]['maximum']==(L['TPA']-256)//128*128
        save(name,rows,edited_line='GH',wrap_scroll_tab_backspace=True,printer_echo_CRT=True)

if a.campaign in ('lifecycle','all'):
    w=h.case('lifecycle')
    for name,path in [('STATEFUL.RSX','build/rsx/STATEFUL.RSX'),('ECHO.RSX','build/rsx/ECHO.RSX'),('STATTST.COM','build/utilities/STATTST.COM')]:h.put(w,name,(root/path).read_bytes())
    t,rows=run(w,['RSX LIST','RSX LOAD STATEFUL','STATTST INIT','STATTST MUTATE','RSX LOAD ECHO','STATTST CHECK','RSX LOAD ECHO','RSX LIST','RSX UNLOAD ECHO','RSX UNLOAD ECHO','STATTST CHECK','RSX UNLOAD STATEFUL','STAT MEM'])
    assert t.count('STATEFUL CHECK PASS')==2 and 'FAILED' not in t and 'RSX module or profile error' not in t
    assert a.untraced or last_commit_windows==4,last_commit_windows
    save('lifecycle',rows,state_preserved=True,tpa=h.maps(t)[-1]['maximum'])
    w=h.case('early-refusals')
    for name,path in [('STATEFUL.RSX','build/rsx/STATEFUL.RSX'),('STATTST.COM','build/utilities/STATTST.COM')]:h.put(w,name,(root/path).read_bytes())
    commands=['RSX LOAD STATEFUL','STATTST INIT','STATTST MUTATE']
    for i,(version,op,low,high) in enumerate([(3,1,0x1000,0x7000),(2,99,0x1000,0x7000),(2,1,0x100,0x7000),(2,1,0x6500,0x7000),(2,1,0x1000,0xffff)]):
        src=f''' LD SP,03000H
 LD DE,REQ
 LD C,177
 CALL 5
 CP 0FFH
 LD HL,GOOD
 JR Z,SHOW
 LD HL,BAD
SHOW: CALL PRINT
 JP 0
{PRINT}
REQ: DB {version},{op},0,0,'MISSING ',0,0
 DW {low},{high}
GOOD: DB 'REFUSAL PASS',13,10,0
BAD: DB 'REFUSAL FAILED',13,10,0
'''
        name=f'REF{i}';h.put(w,name+'.COM',h.asm(w,name,src));commands += [name,'STATTST CHECK']
    commands+=['RSX UNLOAD STATEFUL','STAT MEM']
    t,rows=run(w,commands)
    assert t.count('REFUSAL PASS')==5 and t.count('STATEFUL CHECK PASS')==5 and 'FAILED' not in t
    assert a.untraced or last_commit_windows==2,last_commit_windows
    save('early-refusals',rows,refusals=5,state_checks=5,tpa=h.maps(t)[-1]['maximum'])

if a.campaign in ('rollback','all'):
    pack=(root/'build/system/R3PACK.RSX').read_bytes()
    bads={'missing':b'', 'truncated':pack[:-128], 'header':bytes([pack[0]^1])+pack[1:]}
    for slot in (5,10,12,13,14):
        bad=bytearray(pack);bad[512+slot*1024+511]^=1;bads['slot'+str(slot)]=bytes(bad)
    for label,bad in bads.items():
        name='rollback-'+label
        if not re.search(a.match,name):continue
        w=h.case(name)
        for n,path in [('STATEFUL.RSX','build/rsx/STATEFUL.RSX'),('ECHO.RSX','build/rsx/ECHO.RSX'),('STATTST.COM','build/utilities/STATTST.COM')]:h.put(w,n,(root/path).read_bytes())
        h.put(w,'BAD.RSX',bad,'b');h.put(w,'GOOD.RSX',pack,'b')
        replacement='ERA R3PACK.RSX' if label=='missing' else 'PIP R3PACK.RSX=B:BAD.RSX'
        t,rows=run(w,['RSX LOAD STATEFUL','STATTST INIT','STATTST MUTATE','STAT MEM',replacement,'RSX LOAD ECHO','STATTST CHECK','RSX LIST','STAT MEM','PIP R3PACK.RSX=B:GOOD.RSX','RSX LOAD ECHO','STATTST CHECK','RSX UNLOAD ECHO','RSX UNLOAD STATEFUL','STAT MEM'])
        maps=h.maps(t)
        assert t.count('STATEFUL CHECK PASS')==2 and 'FAILED' not in t and t.count('RSX module or profile error')==1
        assert maps[0]['maximum']==maps[1]['maximum'] and maps[-1]['maximum']==(L['TPA']-256)//128*128
        assert a.untraced or last_commit_windows==4,last_commit_windows
        save(name,rows,state_checks=2,rejected_without_profile_change=True,recovery=True)
