#!/usr/bin/env python3
"""Isolated real-source TCAP return entries and transaction admission experiment.

No production source, public ABI, checked build identity, or utility is changed.
"""
import argparse
import difflib
import hashlib
import json
import re
import struct
from pathlib import Path
import campaign as base
import placement as placed

ROOT=base.ROOT
OUT=ROOT/'build/tcap-system-paths'

# Both calls preserve the incoming request pointer even when a legacy MCON
# uses all permitted scratch registers. Nothing may be published before this.
GUARD='''        PUSH    DE
        LD      A,26
        CALL    LY_BIOS+66
        POP     DE
        CP      16
        RET     Z
'''
# An unknown operation is the ordinary legacy case. All other failures stop
# before the next disk operation, diagnostic, or prompt. Operation 5 retains its
# existing parser-only meaning and still executes after this private check.
RECOVER='''        LD      A,27
        CALL    LY_BIOS+66
'''


def owner(assembler, images):
    ansi=base.normalized((ROOT/'src/rsx/ansi.mac').read_text())
    ansi=ansi.replace('        INCLUDE ansi-dispatch.inc',(ROOT/'src/rsx/ansi-dispatch.inc').read_text())
    ansi=ansi.replace('        INCLUDE screen/rendition.inc',(ROOT/'src/rsx/screen/rendition.inc').read_text())
    ansi=ansi.replace('AN_ENTRY:\n','AN_ENTRY:\n        CP 25\n        JP Z,GX_ROUTE\n        CP 26\n        JP Z,GX_BUSY\n        CP 27\n        JP Z,GX_SAFE\n')
    bridge=(base.HERE/'coordinator.mac').read_text().replace('        ASEG\n        ORG 04000H\n','')
    bridge=bridge.replace('        JP RCONOUT','        RET')
    bridge=bridge.replace('GX_ROUTE:\n        PUSH BC\n        PUSH DE\n        PUSH HL','GX_ROUTE:')
    bridge=bridge.replace('GR_GO:\n        POP HL\n        POP DE\n        POP BC\n        RET','GR_GO:\n        RET')
    begin=bridge.index('GX_COMIT:');end=bridge.index('GX_ROUTE:',begin)
    bridge=bridge[:begin]+bridge[end:]
    bridge=bridge.replace('GX_IMAGE:', 'GX_SAFE:\n        CALL GX_RECV\n        CP 2\n        RET Z\n        OR A\n        RET Z\n        JP GX_HALT\nGX_IMAGE:')
    bridge=bridge.replace('GX_IMAGE:', 'GC_IDLE:\nGX_COMIT:\nGX_BUSY:\n        LD A,(TX_STATE)\n        OR A\n        RET Z\n        LD A,16\n        RET\nGX_IMAGE:')
    tail=placed.indexed_owner((base.HERE/'owner.inc').read_text(),images['owner'][1])+'\n'+bridge
    text='BDOSCALL EQU 0'+f'{base.L["BDOS"]:04X}'+'H\nRCOMMIT EQU 07C00H\n'+ansi.replace('        END\n',tail+'\n        END\n')
    text,count=placed.relax(assembler,text)
    code,labels=placed.emit(assembler,'system-owner',text,0x8000)
    alt,_=placed.emit(assembler,'system-owner-alt',text.replace('08000H','08101H'),0x8101)
    slots=base.relocation_offsets(code,alt,0x101)
    third,_=placed.emit(assembler,'system-owner-third',text.replace('08000H','08427H'),0x8427)
    assert base.relocated(code,slots,0x8427)==third
    return (code,labels),slots,count


def sources(assembler, stage):
    result={};patch=[]
    paths={'finalizer':('src/system/r3final.mac','RF_ENTRY:',base.L['RSX']),
           'commit':('src/system/r3comit.mac','RC_ENTRY:',0x7c00),
           'ccp':('src/ccp/ccp.mac','CCP_ENTRY:',0xbb00),
           'model4-reloader':('src/platform/trs80m4/ccprelod.mac','CRBODY:',base.L['RELOADER']),
           'stage2':('src/system/command-stage2.mac','CRBODY:',0x500)}
    for name,(path,entry,origin) in paths.items():
        original=(ROOT/path).read_text();text=original
        if name in ('finalizer','commit'):
            # Match the actual entry's comment without changing its label.
            line=next(line for line in text.splitlines() if line.startswith(entry))
            text=text.replace(line+'\n',line+'\n'+GUARD,1)
        elif name=='ccp':
            text=text.replace('        CALL    CPX_INITIALIZE','        CALL    XP_CHECK\n        CALL    CPX_INITIALIZE',1)
            old='        LD      A,5\n        CALL    LY_BIOS+66              ; resident-command returns bypass warm boot'
            assert text.count(old)==1
            text=text.replace(old,'        CALL    XP_CHECK',1)
            text=text.replace('CCP_STACK:', 'XP_CHECK:\n'+RECOVER+'        LD      A,5\n        JP      LY_BIOS+66\n\nCCP_STACK:',1)
        else:
            anchor='        LD      SP,CRSTKTOP\n'
            assert text.count(anchor)==1
            text=text.replace(anchor,anchor+RECOVER,1)
        if name=='model4-reloader':
            # Preserve CRBAD's exact A=1/NZ, share the known zero in A after
            # the alignment test, and reuse BC=0 after completed LDIR.
            text=text.replace('        LD      A,1\n        OR      A\n        RET','        XOR     A\n        INC     A\n        RET')
            text=text.replace('        LD      A,H\n        OR      A\n        JP      Z,CRBAD','        OR      H\n        JP      Z,CRBAD')
            text=text.replace('        LDIR\n        LD      HL,0\n        LD      (CRLEFT),HL','        LDIR\n        LD      H,B\n        LD      L,C\n        LD      (CRLEFT),HL')
            text=text.replace('        LD      HL,(CRMPAYLOAD)\n        LD      DE,0200H\n        OR      A','        LD      HL,(CRMPAYLOAD)\n        LD      DE,0200H')
        if name=='commit':
            assert text.count('        OR      A\n        ADD     HL,DE')==2
            text=text.replace('        OR      A\n        ADD     HL,DE','        ADD     HL,DE')
            text=text.replace('RC_BAD:\n        LD      A,0FFH\n        OR      A','RC_BAD:\n        OR      0FFH')
        target=stage/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text)
        bindings=f'LY_CCRC EQU 0{base.L["FILE"]-32:04X}H\nLY_CID EQU 0{base.L["BIOS"]-16:04X}H\nLY_CCMP EQU 0{base.L["BIOS"]-26:04X}H\n' if name=='stage2' else ''
        source=bindings+base.normalized(text)
        if name=='finalizer':
            # Use the same container-slot expansion as the real overlay builder.
            from system_layout import expand_layout
            source=expand_layout(source)
        if name=='commit':source='        INCLUDE layout.inc\n'+source
        if name in ('commit','finalizer','model4-reloader','stage2'):
            source,_=placed.relax(assembler,source)
            target.write_text(source)
        patch.extend(difflib.unified_diff(original.splitlines(True),target.read_text().splitlines(True),fromfile='a/'+path,tofile='b/'+path,n=0))
        code,labels=placed.emit(assembler,name,source,origin)
        baseline,_=placed.emit(assembler,name+'-baseline',bindings+base.normalized(original),origin)
        result[name]=(code,labels,origin,len(baseline))
        if name in ('commit','finalizer'):assert len(code)<=1012,(name,len(code))
        if name=='model4-reloader':assert len(code)<=base.L['RELOADER_CAPACITY']
        if name=='stage2':assert len(code)<=2024
        if name=='ccp':
            import build_ccp
            alternatives=[]
            for other in (0xbc01,0xbd37):
                alternate,_=placed.emit(assembler,name+f'-{other:x}',source.replace('0BB00H',f'0{other:04X}H'),other)
                alternatives.append((alternate,other))
            repairs=build_ccp.relocation_offsets(code,alternatives)
            assert len(repairs)<= (1024-16)//2
            result['ccp_repairs']=len(repairs)
            result['ccp_offsets']=repairs
    return result,''.join(patch)


def checks(f, images, built):
    c=f.cpu;zero=bytes(16);cases=[]
    def check(name, condition):
        assert condition,name
        cases.append(name)
    # The real entry guard must return before even its private context/request
    # bookkeeping, for every currently defined non-idle owner state.
    for name in ('commit','finalizer'):
        code,labels,origin,_=built[name];c.mem[origin:origin+len(code)]=code
        for state in (1,2,3,5):
            c.mem[f.labels['TX_STATE']]=state;c.de=0x6000
            before=bytes(c.mem[0x6000:0x8400]);private=bytes(c.mem[origin:origin+len(code)])
            check(f'{name} rejects state {state}',f.run(origin)==16 and c.de==0x6000 and bytes(c.mem[0x6000:0x8400])==before and bytes(c.mem[origin:origin+len(code)])==private)
    c.mem[f.labels['TX_STATE']]=0
    # Legacy MCON scratch registers must not become a corrupted request pointer.
    fake=0x4a00
    c.mem[fake:fake+12]=bytes.fromhex('0100001100002100003effc9')
    c.setword(f.bios['MP_MON'],fake)
    c.mem[0x6006]=5;c.mem[0x6016]=0xcc
    for name,field in (('commit','RC_REQ'),('finalizer','RF_CTX')):
        code,labels,origin,_=built[name];c.de=0x6000
        check(name+' legacy scratch preserves request',f.run(origin)==255 and c.word(labels[field])==0x6000)
    c.setword(f.bios['MP_MON'],f.labels['AN_ENTRY'])
    # Reuse real scheduler/publication regression through the guarded entry,
    # bypassing the old fixture-owned GX_COMIT wrapper entirely.
    direct=dict(f.gx);f.gx['GX_COMIT']=0x7c00
    cases+=base.transactions(f,images)
    check('empty-profile commit retires Monitor binding',c.word(f.bios['MP_MON'])==f.bios['MC_RAW'])
    # Independent return-entry scenarios explicitly reinstall the fixture owner.
    c.setword(f.bios['MP_MON'],f.labels['AN_ENTRY'])
    f.gx=direct
    for name in ('ccp','model4-reloader','stage2'):
        code,labels,origin,_=built[name]
        c.mem[origin:origin+len(code)]=code
        if name=='ccp':
            c.setword(base.L['SYSTEM']+0x8c,origin)
            # Stop at the first real following phase, not inside recovery.
            boundaries=[('entry',labels['CCP_ENTRY'],labels['CPX_INITIALIZE']),
                        ('loop',labels['CCP_LOOP'],labels['CCP_PROMPT'])]
            c.mem[labels['CPX_INITIALIZE']:labels['CPX_INITIALIZE']+3]=b'\xc3\xff\xff'
            # Prompt data is never executed. Trap at the BDOS string call instead.
            loop=labels['CCP_LOOP'];boundary=loop+3
            assert c.mem[boundary]==0x11
            c.mem[boundary:boundary+3]=b'\xc3\xff\xff'
            c._stack_bounds['ccp']=(labels['CCP_STACK'],labels['CCP_STKTOP'])
        else:
            entry=labels['CRBODY'];boundary=next(address for address in range(entry,entry+80) if bytes(c.mem[address:address+3])==b'\x11\xff\xff')
            c.mem[boundary:boundary+3]=b'\xc3\xff\xff'
            boundaries=[('warm',entry,boundary)]
            c._stack_bounds[name]=(0xd00,0x1000) if name=='stage2' else (0x4c0,0x500)
        for kind,entry,boundary in boundaries:
            for state in (0,1,2,3,5):
                c.sp=0x5f00
                c.mem[f.labels['TX_STATE']]=0
                if state in (1,3):
                    _,token=f.owner(2,zero)
                if state in (2,3):
                    # Starting takeover after emphasis is illegal; construct in order.
                    f.run(f.gx['GX_RECV']);_,token=f.owner(3,zero)
                    if state==3:f.owner(2,token)
                if state==5:
                    f.owner(2,zero);c.mem[f.labels['TX_STATE']]=5
                c.mem[f.bdos['UB_COLUMN']]=37
                before=len(f.wire)
                c.run(entry,limit=500000)
                check(f'{name}/{kind} state {state} reaches next phase idle',f.state()==0)
                check(f'{name}/{kind} state {state} column',c.mem[f.bdos['UB_COLUMN']]==(37 if state==0 else 0))
                if state==0:check(f'{name}/{kind} idle emits nothing',len(f.wire)==before)
                c.sp=0x5f00
            # Fault in rendering repair must not reach the following phase.
            f.owner(2,zero);target=c.word(f.labels['AN_BACKEND']);saved=bytes(c.mem[target:target+3]);c.mem[target:target+3]=b'\x3e\xff\xc9'
            try:c.run(entry,limit=500000)
            except AssertionError as error:
                assert str(error)==f"unsupported opcode 76 at {f.gx['GX_HALT']:04X}",error
            else:raise AssertionError('recovery failure escaped into command execution')
            check(f'{name}/{kind} failed recovery stops before next phase',f.state()==5)
            c.mem[target:target+3]=saved;c.sp=0x5f00;f.run(f.gx['GX_RECV'])
        # ^C abandons the real BDOS frame through BIOS WBOOT to real reloader.
        if name!='ccp':
            f.owner(2,zero);c.mem[f.io['IO_WARM']:f.io['IO_WARM']+3]=b'\xc3'+struct.pack('<H',labels['CRBODY'])
            c.mem[f.io['IO_KEY']]=3;c.c=2;c.de=ord('X');c.sp=0x5f00
            c.run(base.L['BDOS'],limit=500000)
            check(name+' cooked control-C reaches real return entry',f.state()==0 and c.mem[f.bdos['UB_COLUMN']]==0)
            c.sp=0x5f00
    return cases


def regressions(assembler, images, built, backends):
    import shutil
    import test_rsxcommit as commit
    import test_ccpreload as reload
    from build_cpx_module import make_module
    stage=OUT/'regression'
    bios=bytearray(images['bios'][0])
    struct.pack_into('<H',bios,images['bios'][1]['MP_MON']-base.L['BIOS'],images['bios'][1]['MC_RAW'])
    for relative,data in [('build/bios/bios.bin',bios),
            ('build/system/rsxmover.bin',images['mover'][0]),
            ('build/system/rsxschedule.bin',images['scheduler'][0]),
            ('build/system/rsxcommit.bin',images['commit'][0])]:
        path=stage/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    previous=commit.ROOT
    try:
        commit.ROOT=stage
        commit.main()
    finally:commit.ROOT=previous
    data=built['ccp'][0];header=bytearray(1024);allocation=(len(data)+255)&~255
    struct.pack_into('<4sBBHHHHH',header,0,b'BCM1',1,2,0xbb00,len(data),allocation,0,len(built['ccp_offsets']))
    for i,offset in enumerate(built['ccp_offsets']):struct.pack_into('<H',header,16+2*i,offset)
    for relative,content in [('build/ccp/ccp.bin',data),('build/ccp/ccp.rlm',bytes(header)+data),
                             ('build/trs80/ccpreload.bin',built['model4-reloader'][0])]:
        path=stage/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(content)
    shutil.copy2(OUT/'model4-reloader.lst',stage/'build/trs80/ccpreload.lst')
    for name in ('RCP','HELLO'):
        target=stage/'build/cpx'/f'{name}.CPX';target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(make_module(name=name,version=(0,0),commands=[],linked_base=0x8000,
            code=bytes((0,0,8,0x80,9,0x80,10,0x80,0xc9,0xc9,0xc9)),relocations=[2,4,6],init_offset=9,shutdown_offset=10))
    previous={key:getattr(reload,key) for key in ('ROOT','RELOADER','MODULE','CCP','BASIC_MODULE','HELLO_MODULE')}
    reload.ROOT=stage;reload.RELOADER=stage/'build/trs80/ccpreload.bin'
    reload.MODULE=stage/'build/ccp/ccp.rlm';reload.CCP=stage/'build/ccp/ccp.bin'
    reload.BASIC_MODULE=stage/'build/cpx/RCP.CPX';reload.HELLO_MODULE=stage/'build/cpx/HELLO.CPX'
    count=0
    try:
        target=base.L['TPA']-allocation
        # Actual full reloader, independently generated command/CPX carriers,
        # controlled successful/error physical reads and file operations.
        cases=[(target,{}),(target-0x100,{}),(target-0x100,{'with_cpx':True}),
               (target-0x200,{'with_two_cpx':True}),
               (target-0x100,{'with_cpx':True,'cpx_module':b'INVALID HEADER'.ljust(128,b'\0'),'expect_reject':True}),
               (target,{'bad_ccp':True})]
        for failure in (1,2,3):cases.append((target-0x100,{'with_cpx':True,'read_failure':failure,'expect_reject':True}))
        cases.append((target-0x100,{'with_cpx':True,'reset_failure':True,'expect_reject':True}))
        for address,kwargs in cases:
            reload.run_at(address,**kwargs);count+=1
    finally:
        for key,value in previous.items():setattr(reload,key,value)
    # Same real legacy personality probes as placement, independently for every
    # newly used private operation. The helper's source is intentionally local
    # so the historical campaign is unchanged.
    modules=[('ANSI',images['ansi-base'],'AN_ENTRY','AN_STATE')]
    for name,source,entry,state in [('ADM3A','adm3a.mac','AM_ENTRY','AM_STATE'),('VT52','vt52.mac','VT_ENTRY','VT_STATE')]:
        modules.append((name,placed.emit(assembler,'legacy-'+name,base.normalized((ROOT/'src/rsx'/source).read_text()),0x8000),entry,state))
    probes=0
    for name,(data,labels),entry,state in modules:
        for _,(backend,table,repairs,callback) in backends.items():
            for pending in range(6):
                for operation in (25,26,27):
                    c=base.Z80(b'');c.mem[0x8000:0x8000+len(data)]=data;c.mem[labels[state]]=pending
                    c.mem[0x5000:0x5000+len(backend)]=base.relocated(backend,repairs,0x5000)
                    c.setword(0x800c,table[callback]-0x8000+0x5000)
                    before=(bytes(c.mem[0x8000:0x8000+len(data)]),bytes(c.mem[0x5000:0x5000+len(backend)]))
                    writes=[];c.port_write=lambda *args:writes.append(args)
                    c.a=operation;c.run(labels[entry],limit=2000)
                    assert c.a==255 and not writes and before==(bytes(c.mem[0x8000:0x8000+len(data)]),bytes(c.mem[0x5000:0x5000+len(backend)]))
                    probes+=1
    return {'existing_full_commit_scheduler_mover_regression':'PASS',
            'full_model4_reloader_cases':count,'reloader_services':'controlled read/file/reset doubles; synthetic CPXs; actual experimental CCP carrier',
            'legacy_unknown_control_cases':probes}


def admission(assembler, carrier, slots):
    """Fail closed on the existing manager; do not silently claim MCON 1.2."""
    import test_rsxcarrier as validation
    root=OUT/'admission';folder=root/'build/system';folder.mkdir(parents=True,exist_ok=True)
    for filename,symbol,out in [('r3carr.mac','RXBASE','R3CARR.RSX'),('r3meta.mac','RMBASE','R3META.RSX')]:
        text=(ROOT/'src/system'/filename).read_text()
        text,n=re.subn(r'^'+symbol+r'\s+EQU[^\n]*',f'{symbol} EQU 0{base.L["CONFIG"]:04X}H',text,flags=re.M)
        assert n==1
        data=base.assemble(assembler,base.normalized(text),folder/out,folder/(out+'.lst'),base.L['CONFIG'])
        assert len(data)<=1024
    previous=validation.ROOT,validation.CARRIER
    try:
        validation.ROOT=root;validation.CARRIER=0x3000
        cpu,_=validation.phase_one(carrier,b'XTCAP   ')
        assert cpu.a==0 and cpu.word(validation.FACTS+12)==len(slots)
        before=validation.phase_two(cpu,len(carrier))
        assert cpu.a==255 and bytes(cpu.mem[validation.FACTS:validation.FACTS+26])==before
    finally:validation.ROOT,validation.CARRIER=previous
    return {'carrier_structure':'accepted','existing_manager_metadata':'rejected without facts publication',
            'private_mcon_requirement':'1.3 experimental/unallocated; deliberately not accepted by shipped manager',
            'production_activation':'BLOCKED until a versioned matching coordinator/carrier contract is implemented'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assembler',type=Path,default=Path.home()/'bin/z80asm')
    args=parser.parse_args();OUT.mkdir(parents=True,exist_ok=True)
    base.OUT=placed.OUT=OUT
    (OUT/'report.json').unlink(missing_ok=True)
    historical=json.loads((ROOT/'docs/engineering/evidence/tcap-placement/report.json').read_text())
    for path,digest in historical['source_sha256'].items():
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,('placement baseline changed',path)
    images,_,backends,_=base.build(args.assembler)
    newowner,slots,count=owner(args.assembler,images)
    carrier=base.make_module(name='XTCAP',version=(0,3),services=[],linked_base=0x8000,code=newowner[0],relocations=slots,reconstruction_class='STATEFUL',callable_services=[(b'MCON',1,3,newowner[1]['AN_ENTRY']-0x8000,4),(b'XTCP',0,3,newowner[1]['TX_ENTRY']-0x8000,0)])
    admission_result=admission(args.assembler,carrier,slots)
    images['bios'],stage=placed.packed_core(args.assembler,images)
    built,patch=sources(args.assembler,stage)
    images['owner']=newowner
    images['commit']=built['commit'][:2]
    backends=placed.placed_backends(args.assembler,images,backends)
    runs=[]
    for name in ('M4SCRN','ANSISCRN'):
        for origin in (0x9000,0xa101):
            f=placed.PlacedFixture(args.assembler,images,slots,backends,name,origin)
            # Previous behavioral campaign still passes with the two new private controls.
            prior=base.exercise(f)
            cases=checks(f,images,built)
            stack={label:high-f.cpu._min_sp.get(label,high) for label,(_,high) in f.cpu._stack_bounds.items()}
            runs.append({'backend':name,'origin':hex(origin),'prior_cases':len(prior),'cases':cases,'stack_observed_bytes':stack})
            print('PASS SYSTEM PATHS',name,hex(origin),len(cases),stack)
    regression=regressions(args.assembler,images,built,backends)
    (OUT/'system-paths.patch').write_text(patch)
    report={'status':'PASS','source_baseline':'62acda7391767505cedb1549688b72354542d092','scope':'isolated real-source return-entry and transaction-guard execution; not production admission',
            'private_controls':{'25':'BIOS output route guard','26':'non-mutating transaction busy query','27':'safe-stack recovery; stops at owner fatal loop on rendering failure'},
            'carrier':{'payload_bytes':len(newowner[0]),'relocations':len(slots),'capacity':232,'allocation_bytes':int.from_bytes(carrier[14:16],'little'),'relative_branches':count,'installed':False},
            'sizes':{name:{'baseline_bytes':value[3],'experimental_bytes':len(value[0]),'delta_bytes':len(value[0])-value[3]} for name,value in built.items() if name not in ('ccp_repairs','ccp_offsets')},
            'ccp_relocation_words':built['ccp_repairs'],'runs':runs,'regressions':regression,'admission':admission_result,
            'source_sha256':{str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in [Path(__file__),base.HERE/'placement.py',base.HERE/'campaign.py',base.HERE/'coordinator.mac',base.HERE/'owner.inc']+[ROOT/path for path in ('src/system/r3comit.mac','src/system/r3final.mac','src/system/r3carr.mac','src/system/r3meta.mac','src/ccp/ccp.mac','src/system/command-stage2.mac','src/platform/trs80m4/ccprelod.mac')]+[ROOT/path for path in historical['source_sha256']]},
            'patch_sha256':hashlib.sha256(patch.encode()).hexdigest(),
            'assembler_sha256':hashlib.sha256(args.assembler.read_bytes()).hexdigest(),
            'stage2_bindings':'fixture-only checked CRC/identity helper addresses in reference layout; helpers not executed; no checked profile claim',
            'remaining':['versioned coordinator/core/command-carrier admission and boot-global non-reusing identity allocator',
                         'full candidate request ABI, live/native/media and full checked cpmsim qualification',
                         'utility migrations and release assignment deferred'],
            'execution_boundaries':'CCP initialization/prompt and reloader first disk operation replaced with explicit stop traps; no filesystem or complete command-loop claim'}
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({key:report[key] for key in ('carrier','sizes','ccp_relocation_words')},indent=2))

if __name__=='__main__':main()
