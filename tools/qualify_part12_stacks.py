#!/usr/bin/env python3
"""Live changed-byte stack watermarks on disposable checked cpmsim media.

These are observed workloads, not exhaustive high-water or interrupt proofs.
No instrumented resident code or altered system-track image is used.
"""
from pathlib import Path
import argparse,json,re,sys
p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--output',type=Path,required=True)
a=p.parse_args();root=a.root.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True);sys.path.insert(0,str(root/'tools'))
import part7_probe_support as h
from build_z80pack_image import symbols
h.out=out;g=symbols(root/'build/z80pack/gateway.lst');b=symbols(root/'build/bdos/bdos.lst')
bands={'system':(g['SYS_STACK'],g['SYS_STKTOP']),'bdos':(b['UB_STACK'],b['UB_STKTOP']),
       'stream':(0xd00,0x1000),'reader':(0x6615,0x6700),'manager':(0x6f00,0x7000),'config':(0x3e00,0x4000),'sysgen':(0x3e00,0x3f00)}
results={}
# Output goes directly to the host console so the measuring routine cannot
# deepen the BDOS/system/transaction stacks it is inspecting.
common='''
FILL: LD (HL),A
 INC HL
 DEC BC
 LD D,A
 LD A,B
 OR C
 LD A,D
 JR NZ,FILL
 RET
PRINT: LD A,(HL)
 INC HL
 OR A
 RET Z
 OUT (1),A
 JR PRINT
MEASURE:
 LD E,0
SCAN: LD A,(HL)
 CP MARK
 JR NZ,FOUND
 INC HL
 DEC BC
 LD A,B
 OR C
 JR NZ,SCAN
FOUND:
 LD A,B
 CALL HEX
 LD A,C
 CALL HEX
 LD A,13
 OUT (1),A
 LD A,10
 OUT (1),A
 RET
HEX: PUSH AF
 RRCA
 RRCA
 RRCA
 RRCA
 CALL DIGIT
 POP AF
DIGIT: AND 15
 ADD A,'0'
 CP ':'
 JR C,PUT
 ADD A,7
PUT: OUT (1),A
 RET
'''
def fill(names):
    return ''.join(f' LD HL,{bands[n][0]}\n LD BC,{bands[n][1]-bands[n][0]}\n LD A,MARK\n CALL FILL\n' for n in names)
def measure(names):
    return ''.join(f' LD HL,M{i}\n CALL PRINT\n LD HL,{bands[n][0]}\n LD BC,{bands[n][1]-bands[n][0]}\n CALL MEASURE\n' for i,n in enumerate(names))
def labels(names):return ''.join(f"M{i}: DB 'P12 {n} ',0\n" for i,n in enumerate(names))
def observe(t,names):
    found={n:int(v,16) for n,v in re.findall(r'P12 (\w+) ([0-9A-F]{4})',t)}
    assert set(found)==set(names),(names,t)
    for n,v in found.items():assert v<bands[n][1]-bands[n][0],(n,v,'stack band exhausted')
    return found
for mark in (0xa5,0x5a):
    w=h.case('watermark-'+hex(mark));h.put(w,'STATEFUL.RSX',(root/'build/rsx/STATEFUL.RSX').read_bytes())
    prefix=f'MARK EQU {mark}\n LD SP,03000H\n'
    names=['system','bdos','stream']
    init=prefix+fill(names)+' JP 0\n'+common
    read=prefix+measure(names)+' JP 0\n'+common+labels(names)
    for name,src in [('MARK',init),('READ',read)]:
        data=h.asm(w,name,src);assert len(data)<0x300;h.put(w,name+'.COM',data)
    t=h.run(w,['MARK','READ']);results[f'warm-{mark}']=observe(t,names)
    for operation in (1,2):
        names=['bdos','reader','manager']
        src=prefix+fill(names)+''' LD DE,REQ
 LD C,177
 CALL 5
 LD (STATUS),A
 LD HL,STATUSMSG
 CALL PRINT
 LD A,(STATUS)
 CALL HEX
 LD A,13
 OUT (1),A
 LD A,10
 OUT (1),A
'''+measure(names)+' JP 0\n'+common+labels(names)+f'''
STATUS: DB 0
STATUSMSG: DB 'P12 status ',0
REQ: DB 2,{operation},0,0,'STATEFUL',0,0
 DW ENDPROG,07000H
ENDPROG:
'''
        name='TX'+str(operation)
        data=h.asm(w,name,src);assert len(data)<0x600;h.put(w,name+'.COM',data)
        t=h.run(w,['RSX LOAD STATEFUL',name] if operation==2 else [name],stem='transaction-'+str(operation))
        assert 'P12 status 00' in t,t
        results[f'transaction-{operation}-{mark}']=observe(t,names)
    for label,command in [('config','CONFIG /SHOW'),('sysgen','SYSGEN A: B:STACK.SYS')]:
        u=h.case(label+'-'+hex(mark));names=[label,'bdos']
        init=prefix+fill(names)+' JP 0\n'+common
        read=prefix+measure(names)+' JP 0\n'+common+labels(names)
        for name,src in [('MARK',init),('READ',read)]:
            data=h.asm(u,name,src);assert len(data)<0x300;h.put(u,name+'.COM',data)
        t=h.run(u,['MARK',command,'READ'])
        if label=='sysgen':assert 'Package exported and verified.' in t,t
        else:assert 'does not match' not in t and 'Requires matching' not in t,t
        results[f'{label}-{mark}']=observe(t,names)
    (out/'results.json').write_text(json.dumps({'bands':bands,'observations':results,'method':'live changed-byte watermarks, two fill patterns; no interrupt or exhaustive bound claim'},indent=2)+'\n')
print(json.dumps(results,indent=2),flush=True)
