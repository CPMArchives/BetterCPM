#!/usr/bin/env python3
"""Second isolated campaign: normal carrier packaging and packed BIOS placement."""
import argparse
import hashlib
import json
import re
import struct
import sys
from pathlib import Path
import campaign as base

ROOT=base.ROOT
OUT=ROOT/'build/tcap-placement'


def emit(assembler,name,text,origin):
    code=base.assemble(assembler,text,OUT/(name+'.bin'),OUT/(name+'.lst'),origin)
    return code,base.symbols(OUT/(name+'.lst'))


def relax(assembler,text):
    """Only convert supported JP conditions when assembled displacement fits JR.

    Labels carry no bytes. Every iteration is assembled; distances only shrink.
    Original code is retained separately for differential execution.
    """
    lines=text.splitlines();marked=[];sites=[]
    pattern=re.compile(r'^\s*JP\s+(?:(NZ|Z|NC|C),)?([A-Z][A-Z0-9_]*)\s*(?:;.*)?$')
    for line in lines:
        match=pattern.match(line)
        if match:
            name=f'XP{len(sites):04d}';marked.append(name+':')
            sites.append((len(marked),name,match[2]))
        marked.append(line)
    count=0
    for iteration in range(20):
        code,labels=emit(assembler,f'relax-{iteration}','\n'.join(marked)+'\n',0x8000)
        changed=0
        for index,name,target in sites:
            if re.match(r'^\s*JP\s+',marked[index]) and target in labels:
                distance=labels[target]-(labels[name]+2)
                if -128<=distance<=127:
                    marked[index]=re.sub(r'\bJP\b','JR',marked[index],count=1)
                    changed+=1
        count+=changed
        if not changed:return '\n'.join(marked)+'\n',count
    raise AssertionError('relative branch relaxation did not converge')


def indexed_owner(text, labels):
    """Specialize this owner's data addressing to a preserved IX.

    Address helpers use DE/BC and ADD flags only at sites where owner.inc resets
    or does not consume them. This is not a general instruction optimizer.
    The source-hash gate below makes changing that premise an explicit review.
    """
    recorded=json.loads((ROOT/'docs/engineering/evidence/tcap-feasibility/report.json').read_text())
    actual=hashlib.sha256(text.encode()).hexdigest()
    assert actual==recorded['source_sha256']['tools/prototypes/tcap/owner.inc'],'owner transformation premise changed; review addressing helpers'
    fields={name for name,value in labels.items() if labels['TX_STATE']<=value<labels['TX_IMAGE']}
    assert labels['TX_IMAGE']-labels['TX_STATE']<=128
    def field(expr):
        match=re.fullmatch(r'(TX_[A-Z]+)(\+\d+)?',expr)
        return match and match[1] in fields
    def offset(expr):return f'({expr}-TX_STATE)'
    result=[]
    for line in text.splitlines():
        m=re.match(r'\s*LD (A|HL|DE),\((TX_[A-Z]+(?:\+\d+)?)\)\s*(?:;.*)?$',line)
        if m and field(m[2]):
            reg,expr=m.groups();off=offset(expr)
            if reg=='A':result.append(f'        LD A,(IX+{off})')
            else:
                lo,hi=('L','H') if reg=='HL' else ('E','D')
                result.extend([f'        LD {lo},(IX+{off})',f'        LD {hi},(IX+{off}+1)'])
            continue
        m=re.match(r'\s*LD \((TX_[A-Z]+(?:\+\d+)?)\),(A|HL|DE)\s*(?:;.*)?$',line)
        if m and field(m[1]):
            expr,reg=m.groups();off=offset(expr)
            if reg=='A':result.append(f'        LD (IX+{off}),A')
            elif reg=='HL':result.extend([f'        LD (IX+{off}),L',f'        LD (IX+{off}+1),H'])
            else:
                result.extend(['        PUSH DE','        POP HL',f'        LD (IX+{off}),L',f'        LD (IX+{off}+1),H'])
            continue
        m=re.match(r'\s*LD (HL|DE),(TX_[A-Z]+(?:\+\d+)?)\s*(?:;.*)?$',line)
        if m and field(m[2]):
            reg,expr=m.groups()
            if reg=='HL':
                result.extend(['        PUSH IX','        POP HL',f'        LD DE,{expr}-TX_STATE','        ADD HL,DE'])
            else:
                result.extend(['        PUSH HL','        PUSH IX','        POP HL',f'        LD BC,{expr}-TX_STATE','        ADD HL,BC','        EX DE,HL','        POP HL'])
            continue
        result.append(line)
    text='\n'.join(result)+'\n'
    text=text.replace('TX_ENTRY:\n','TX_ENTRY:\n        PUSH IX\n        LD IX,TX_STATE\n')
    text=text.replace('        POP DE\n        RET','        POP DE\n        POP IX\n        RET',1)
    text=text.replace('TX_FIX:\n','TX_FIX:\n        PUSH IX\n        LD IX,TX_STATE\n        CALL TF_BODY\n        POP IX\n        RET\nTF_BODY:\n')
    return text


def owner(assembler,images):
    ansi=base.normalized((ROOT/'src/rsx/ansi.mac').read_text())
    ansi=ansi.replace('        INCLUDE ansi-dispatch.inc',(ROOT/'src/rsx/ansi-dispatch.inc').read_text())
    ansi=ansi.replace('        INCLUDE screen/rendition.inc',(ROOT/'src/rsx/screen/rendition.inc').read_text())
    # Private opcode, not an allocation/change to public MCON/SCRN contracts.
    ansi=ansi.replace('AN_ENTRY:\n','AN_ENTRY:\n        CP 25\n        JP Z,GX_ROUTE\n')
    bridge=(base.HERE/'coordinator.mac').read_text()
    bridge=bridge.replace('        ASEG\n        ORG 04000H\n','')
    bridge=bridge.replace('        JP RCONOUT','        RET')
    # The fixed caller saves BC. MCON scratch DE/HL need not be saved twice.
    saved='GX_ROUTE:\n        PUSH BC\n        PUSH DE\n        PUSH HL'
    assert bridge.count(saved)==1
    bridge=bridge.replace(saved,'GX_ROUTE:')
    saved='GR_GO:\n        POP HL\n        POP DE\n        POP BC\n        RET'
    assert bridge.count(saved)==1
    bridge=bridge.replace(saved,'GR_GO:\n        RET')
    bridge='BDOSCALL EQU 0'+f'{base.L["BDOS"]:04X}'+'H\nRCOMMIT EQU 07C00H\n'+bridge
    tail=indexed_owner((base.HERE/'owner.inc').read_text(),images['owner'][1])+'\n'+bridge
    original=ansi.replace('        END\n',tail+'\n        END\n')
    original_code,original_labels=emit(assembler,'placed-unoptimized',original,0x8000)
    text,count=relax(assembler,original)
    code,labels=emit(assembler,'placed-owner',text,0x8000)
    other,_=emit(assembler,'placed-owner-alt',text.replace('08000H','08101H'),0x8101)
    slots=base.relocation_offsets(code,other,0x101)
    check,_=emit(assembler,'placed-owner-check',text.replace('08000H','08427H'),0x8427)
    assert base.relocated(code,slots,0x8427)==check,'third-origin relocation mismatch'
    return (code,labels),slots,(original_code,original_labels),count


def packed_core(assembler, images):
    """Seven equivalent saved bytes pay for a seven-byte private route hook."""
    import shutil
    import build_bios as bb
    import build_system as bs
    stage=OUT/'packed-core'
    shutil.copytree(ROOT/'src',stage/'src',dirs_exist_ok=True)
    bios=stage/'src/bios/bios.mac'
    text=bios.read_text()
    old='        CALL MC_CALL\n        OR A\n        RET Z\nIO_READY:\n        LD A,0FFH\n        RET'
    new='        CALL MC_CALL\n        ADD A,255\n        SBC A,A\n        RET'
    assert text.count(old)==1
    text=text.replace(old,new)
    decoder='IO_CON:\n        LD A,(0003H)\n        AND 3\n        DEC A\n        RET\n'
    assert text.count(decoder)==1
    text=text.replace(decoder,'')
    assert text.count('        JR BIOLIST\n')==1
    text=text.replace('        JR BIOLIST\n','')
    text=text.replace("BIOPUNCH:                               ; output sink shares the reader's RET only\n        RET",
                      "BIOPUNCH:                               ; output sink shares the reader's RET only\n        RET\n"+decoder)
    # Use the exact public-entry definition without disturbing its vector.
    line=next(line for line in text.splitlines() if line.startswith('BIOCONOT:'))
    text=text.replace(line+'\n',line+'\n        PUSH BC\n        LD A,25\n        CALL MC_CALL\n        POP BC\n',1)
    bios.write_text(text)
    scroll=stage/'src/platform/trs80m4/m4scroll.inc'
    text=scroll.read_text()
    old='        LD      HL,VIDEOEND-VIDEOCOLS\n        LD      DE,VIDEOEND-VIDEOCOLS+1\n        LD      BC,VIDEOCOLS-1\n        LD      (HL),020H\n        LDIR'
    new='        EX      DE,HL                   ; completed LDIR: DE=last-row, HL=VIDEOEND\n        LD      E,(VIDEOEND-VIDEOCOLS+1) AND 255\n        LD      C,VIDEOCOLS-1            ; B is zero after completed LDIR\n        LD      (HL),020H\n        LDIR'
    assert text.count(old)==1
    scroll.write_text(text.replace(old,new))
    system=stage/'build/system';system.mkdir(parents=True,exist_ok=True)
    bdos=stage/'build/bdos';bdos.mkdir(parents=True,exist_ok=True)
    (bdos/'bdos.bin').write_bytes(images['bdos'][0])
    shutil.copy2(OUT/'bdos.lst',bdos/'bdos.lst')
    base.assemble(assembler,base.normalized((stage/'src/system/fileload.mac').read_text()),system/'fileloader.bin',system/'fileloader.lst',base.L['FILE'])
    saved_bb={k:getattr(bb,k) for k in ('ROOT','SOURCE','PLATFORM','BUILD')}
    saved_bs={k:getattr(bs,k) for k in ('ROOT','SOURCE','BUILD')}
    argv=sys.argv
    try:
        bb.ROOT=stage;bb.SOURCE=stage/'src/bios';bb.PLATFORM=stage/'src/platform/trs80m4';bb.BUILD=stage/'build/bios'
        bs.ROOT=stage;bs.SOURCE=stage/'src/system/gateway.mac';bs.BUILD=system
        sys.argv=['build_system.py','--assembler',str(assembler)]
        bs.main()                       # actual packed-image overlap/reservation checks
    finally:
        sys.argv=argv
        for key,value in saved_bb.items():setattr(bb,key,value)
        for key,value in saved_bs.items():setattr(bs,key,value)
    code=(stage/'build/bios/bios.bin').read_bytes()
    labels=base.symbols(stage/'build/bios/bios.lst')
    assert len(code)==len(images['bios'][0])==base.L['FILE']-base.L['BIOS']
    for name in ('MONCALL','MONRAW','MONBASE','MP_MON'):
        assert labels[name]==images['bios'][1][name],name
    return (code,labels),stage


def placed_backends(assembler, images, backends):
    result=dict(backends)
    bindings='\n'.join(f'{key} EQU 0{images["bios"][1][key]:04X}H' for key in ('M4CURSOR','M4COLUMN'))
    text=(ROOT/'src/rsx/screen/model4.mac').read_text().replace('        INCLUDE backend.inc',bindings)
    code,labels=emit(assembler,'placed-M4SCRN',text,0x8000)
    alt,_=emit(assembler,'placed-M4SCRN-alt',text.replace('08000H','08101H'),0x8101)
    result['M4SCRN']=(code,labels,base.relocation_offsets(code,alt,0x101),'S_ENTRY')
    return result


class PlacedFixture(base.Fixture):
    def __init__(self,assembler,images,slots,backends,name,origin):
        super().__init__(assembler,images,slots,backends,name,origin)
        cpu=self.cpu
        start=base.L['BIOS']+12
        cpu.mem[start:start+3]=images['bios'][0][12:15]
        cpu.mem[0x4000:0x4000+len(self.bridge)]=bytes(len(self.bridge))
        self.gx={name:self.labels[name] for name in self.gx}
        self.bridge=bytes(cpu.mem[self.gx['GX_RECV']:self.gx['GX_IMAGE']])
        cpu.setword(self.io['IO_WARM']+4,self.gx['GX_RECV'])
        cpu.ix=0x2468


def move_owner(fixture, images, slots, allocation):
    """Execute the real STATEFUL mover; fixture performs explicit rebinding."""
    c=fixture.cpu;old=fixture.base;new=0xa101 if old==0x9000 else 0x9000
    assert fixture.state()==0 and len(slots)<=255
    request=struct.pack('<HHHBB',old,new,allocation,len(slots),0)+struct.pack('<'+'H'*len(slots),*slots)
    c.mem[0x6000:0x6000+len(request)]=request
    mover=images['mover'][0];c.mem[0x7000:0x7000+len(mover)]=mover
    c.de=0x6000
    assert fixture.run(0x7000)==0
    delta=new-old
    expected=base.relocated(images['owner'][0],slots,new)
    # Mutable fields differ from a cold image; check all repaired static words.
    for slot in slots:
        assert c.word(new+slot)==int.from_bytes(expected[slot:slot+2],'little'),slot
    assert c.word(new+fixture.labels['AN_BACKEND']-old)==c.word(fixture.labels['AN_BACKEND'])
    fixture.labels={key:value+delta for key,value in fixture.labels.items()}
    fixture.gx={key:value+delta for key,value in fixture.gx.items()}
    fixture.base=new
    c.setword(fixture.bios['MP_MON'],fixture.labels['AN_ENTRY'])
    c.setword(fixture.io['IO_WARM']+4,fixture.gx['GX_RECV'])
    # Simulate a committed idle validity transition; no global allocator claimed.
    c.mem[fixture.labels['TX_VALID']]=2
    c.mem[old:old+allocation]=bytes([0xdd])*allocation
    result,token=fixture.owner(2,bytes(16))
    assert result==0 and token[0]==2
    fixture.text(b'M')
    assert fixture.owner(4,token)[0]==0 and fixture.state()==0
    assert fixture.run(fixture.gx['GX_RECV'])==2
    return {'old':hex(old),'new':hex(new),'repair_words':len(slots),'result':'PASS','rebinding':'explicit fixture publication'}


def parser_parity(assembler, reference, oldslots, oldbackends, images, slots, backends):
    import random
    rng=random.Random(0x54434150)
    corpus=[b'\x1b[2J\x1b[H',b'A'*80+b'\r\n',b'\x1b[3;10r',b'B'*800,
            b'\x1b7\x1b[24;80HXY\x1b8Z',b'\x1b[?25l\x1b[?25h',
            b'\x1b[38;2;10;128;250mCOLOR\x1b[0m',b'\x1b[',b'12;',b'15H',
            b'\x1b]ignored\x1b\\',b'\x1b[999999999999999999999H',b'\x18\x1a']
    choices=[b'\x1b[1;7m',b'\x1b[22;27m',b'\x1b[0m',b'\x1b[38;5;195m',b'\x1b[38;6;1m',
             b'\x1b7',b'\x1b8',b'\x1b[s',b'\x1b[u',b'\x1b[2K',b'\x1b[1J',
             b'\x1bD',b'\x1bM',b'\x1bE',b'\r\n',b'\t',b'\b',b'\x1b[r']
    for _ in range(384):
        if rng.randrange(3)==0:corpus.append(bytes(rng.randrange(32,127) for _ in range(rng.randrange(1,24))))
        elif rng.randrange(2):corpus.append(rng.choice(choices))
        else:corpus.append(f'\x1b[{rng.randrange(0,30)};{rng.randrange(0,90)}H'.encode())
    runs=[]
    for name in ('M4SCRN','ANSISCRN'):
        for origin in (0x9000,0xa101):
            old=base.Fixture(assembler,reference,oldslots,oldbackends,name,origin)
            new=PlacedFixture(assembler,images,slots,backends,name,origin)
            for index,data in enumerate(corpus):
                old.text(data);new.text(data)
                for label,size in [('AN_STATE',1),('AN_COUNT',1),('AN_BUFFER',32),('AP_VALUE',9),('AN_VISIBLE',1)]:
                    a=old.labels[label];b=new.labels[label]
                    assert bytes(old.cpu.mem[a:a+size])==bytes(new.cpu.mem[b:b+size]),(name,index,label)
                assert old.cpu.mem[old.bdos['UB_COLUMN']]==new.cpu.mem[new.bdos['UB_COLUMN']]
                if name=='ANSISCRN':
                    assert old.wire==new.wire,(index,'wire parity')
                    assert old.screen.display==new.screen.display
                    assert tuple(getattr(old.screen.cursor,k) for k in ('x','y','attrs','hidden'))==tuple(getattr(new.screen.cursor,k) for k in ('x','y','attrs','hidden'))
                else:
                    assert old.cpu.mem[0xf800:0xff80]==new.cpu.mem[0xf800:0xff80],index
                    assert old.cpu.word(old.bios['M4CURSOR'])==new.cpu.word(new.bios['M4CURSOR'])
                    assert old.cpu.mem[old.bios['M4COLUMN']]==new.cpu.mem[new.bios['M4COLUMN']]
            runs.append({'backend':name,'origin':hex(origin),'trace_checkpoints':len(corpus),'result':'PASS'})
    return runs


def core_regressions(assembler, old_bios, new_bios, stage):
    from test_bios import Z80
    results={}
    # Legacy-style callback: unknown operations return FF without effects.
    provider='        ASEG\n        ORG 09000H\nLP_ENTRY: CP 6\n        JR C,LP_VALID\n        LD BC,0DEADH\n        LD DE,0ABCDH\n        LD HL,01234H\n        LD A,255\n        RET\nLP_VALID: LD (09100H),A\n        LD A,(09101H)\n        RET\n        END\n'
    stub,_=emit(assembler,'legacy-provider',provider,0x9000)
    cpu=Z80(b'');cpu.mem[base.L['BIOS']:base.L['BIOS']+len(new_bios[0])]=new_bios[0]
    labels=new_bios[1];cpu.mem[0x9000:0x9000+len(stub)]=stub;cpu.setword(labels['MP_MON'],0x9000)
    cases=0
    for io in range(256):
        cpu.mem[3]=io;con=io&3;lst=io>>6
        for status in (0,1,0x7e,0xff):
            cpu.mem[0x9101]=status
            for label,expected,op in [('BIOCONST',255 if con==1 and status else 0,1 if con==1 else 0xcc),
                                      ('BIOCONIN',status&127 if con==1 else 26,2 if con==1 else 0xcc),
                                      ('BIOLSTST',255 if lst==1 else 0,0xcc),
                                      ('BIOCONOT',None,0 if con==1 or con==2 and lst==1 else 0xcc),
                                      ('BIOLIST',None,0 if lst==1 else 0xcc)]:
                cpu.mem[0x9100]=0xcc;cpu.c=ord('X');sp=cpu.sp
                cpu.run(labels[label],limit=2000)
                assert cpu.mem[0x9100]==op,(io,label,cpu.mem[0x9100],op)
                assert expected is None or cpu.a==expected,(io,label,cpu.a,expected)
                assert cpu.sp==sp and cpu.c==ord('X')
                cases+=1
    # Status normalization independent of sampled characters.
    cpu.mem[3]=1
    for status in range(256):
        cpu.mem[0x9101]=status;cpu.run(labels['BIOCONST'])
        assert cpu.a==(255 if status else 0)
    results['legacy_iobyte_cases']=cases;results['all_status_values']=256
    # Basic fallback keeps ordinary public console/list behavior on every route.
    basic=[]
    for data,table in (old_bios,new_bios):
        c=Z80(b'');c.mem[base.L['BIOS']:base.L['BIOS']+len(data)]=data;c.port_write=lambda *args:None
        c.run(table['MONBASE']);c.run(table['M4_INIT'],limit=10000);basic.append((c,table))
    for io in range(256):
        for c,table in basic:c.mem[3]=io
        for label in ('BIOCONOT','BIOLIST'):
            for c,table in basic:c.c=ord('B');c.run(table[label],limit=15000)
            assert basic[0][0].mem[0xf800:0xff80]==basic[1][0].mem[0xf800:0xff80],(io,label)
            assert basic[0][0].word(basic[0][1]['M4CURSOR'])==basic[1][0].word(basic[1][1]['M4CURSOR'])
    results['basic_fallback_route_comparisons']=512
    # Independent normal-console video model, plus original/private comparison.
    import random
    rng=random.Random(0x5343524e)
    chars=list(b'A'*(80*30))+[rng.choice([8,10,13,28]+list(range(32,127))) for _ in range(2048)]
    cpus=[]
    for data,table in (old_bios,new_bios):
        c=Z80(b'');c.mem[base.L['BIOS']:base.L['BIOS']+len(data)]=data;c.port_write=lambda *args:None
        c.run(table['MONBASE']);c.run(table['M4_INIT'],limit=10000)
        cpus.append((c,table))
    video=bytearray(b' '*1920);position=column=0
    for char in chars:
        if char==28:video[:]=b' '*1920;position=column=0
        elif char==8:
            if column:position-=1;column-=1
        else:
            if char==13:position-=column;column=0
            elif char==10:position+=80
            else:video[position]=char;position+=1;column=(column+1)%80
            if position>=1920:video[:]=video[80:]+b' '*80;position=1840+column
        for c,table in cpus:
            c.c=char;c.run(table['M4_SCROLL_OUT'],limit=15000)
            assert bytes(c.mem[0xf800:0xff80])==video,char
            assert c.word(table['M4CURSOR'])==0xf800+position
            assert c.mem[table['M4COLUMN']]==column
    results['independent_video_characters']=len(chars)
    import test_model4_keyboard_case as keyboard
    prior=keyboard.FOLDER
    try:
        keyboard.FOLDER=stage/'build/bios'
        keyboard.caps_checks();keyboard.compaction_checks()
    finally:keyboard.FOLDER=prior
    results['existing_caps_and_compaction_regressions']='PASS'
    return results


def old_provider_probes(assembler, images, backends):
    cases=0
    modules=[('ANSI',images['ansi-base'],'AN_ENTRY','AN_STATE')]
    for name,source,entry,state in [('ADM3A','adm3a.mac','AM_ENTRY','AM_STATE'),('VT52','vt52.mac','VT_ENTRY','VT_STATE')]:
        modules.append((name,emit(assembler,'legacy-'+name,base.normalized((ROOT/'src/rsx'/source).read_text()),0x8000),entry,state))
    for name,(data,labels),entry,state in modules:
        for backend,(code,table,repairs,callback) in backends.items():
            for pending in range(6):
                c=base.Z80(b'');c.mem[0x8000:0x8000+len(data)]=data
                c.mem[0x5000:0x5000+len(code)]=base.relocated(code,repairs,0x5000)
                c.setword(0x800c,table[callback]-0x8000+0x5000)
                c.mem[labels[state]]=pending
                writes=[];c.port_write=lambda *args:writes.append(args)
                before=(bytes(c.mem[0x8000:0x8000+len(data)]),bytes(c.mem[0x5000:0x5000+len(code)]))
                c.a=25;c.c=ord('X');c.run(labels[entry],limit=2000)
                assert c.a==255 and not writes,(name,backend,pending)
                assert before==(bytes(c.mem[0x8000:0x8000+len(data)]),bytes(c.mem[0x5000:0x5000+len(code)]))
                cases+=1
    return {'actual_legacy_personalities':['ADM3A','VT52','ANSI'],'unknown_probe_cases':cases,'result':'PASS'}


def carrier_validation(assembler, carrier, slots):
    import test_rsxcarrier as validation
    root=OUT/'carrier-validation';folder=root/'build/system';folder.mkdir(parents=True,exist_ok=True)
    for filename,symbol,out in [('r3carr.mac','RXBASE','R3CARR.RSX'),('r3meta.mac','RMBASE','R3META.RSX'),('r3snap.mac','RNBASE','R3SNAP.RSX')]:
        text=(ROOT/'src/system'/filename).read_text()
        text,n=re.subn(r'^'+symbol+r'\s+EQU[^\n]*',f'{symbol} EQU 0{base.L["CONFIG"]:04X}H',text,flags=re.M)
        assert n==1
        data=base.assemble(assembler,base.normalized(text),folder/out,folder/(out+'.lst'),base.L['CONFIG'])
        assert len(data)<=1024
    prior=(validation.ROOT,validation.CARRIER)
    try:
        validation.ROOT=root;validation.CARRIER=0x3000
        cpu,_=validation.phase_one(carrier,b'XTCAP   ')
        assert cpu.a==0 and cpu.word(validation.FACTS+12)==len(slots)
        validation.phase_two(cpu,len(carrier))
        assert cpu.a==0 and cpu.mem[validation.FACTS+17]==2
        scratch=validation.SCRATCH
        assert bytes(cpu.mem[scratch:scratch+4])==b'MCON'
        assert bytes(cpu.mem[scratch+10:scratch+14])==b'XTCP'
        facts=validation.FACTS
        request=struct.pack('<8HBBHHB',cpu.word(facts),cpu.word(facts+2),cpu.word(facts+4),
            cpu.word(facts+6),0x9000,cpu.word(facts+10),cpu.word(facts+12),cpu.word(facts+18),
            cpu.mem[facts+17],cpu.mem[facts+21],0x7000,cpu.word(facts+8),0xcc)
        validation.run_phase(cpu,'R3SNAP.RSX',request)
        assert cpu.a==0 and cpu.mem[validation.REQUEST+22]==1
        assert cpu.word(0x7000)==cpu.word(0x7002)==0
        assert cpu.word(0x7004)==2 and cpu.word(0x7006)==int.from_bytes(carrier[14:16],'little')-20
        for slot in slots:
            if slot<8:continue  # snapshot rewrites loader-owned header deliberately
            linked=int.from_bytes(carrier[512+slot:514+slot],'little')
            assert cpu.word(0x7000+slot)==linked+0x1000,(slot,hex(cpu.word(0x7000+slot)),hex(linked+0x1000))
        broken=bytearray(carrier);broken[512+100]^=1
        cpu,before=validation.phase_one(bytes(broken),b'XTCAP   ')
        assert cpu.a!=0 and bytes(cpu.mem[facts:facts+26])==before
    finally:
        validation.ROOT,validation.CARRIER=prior
    return {'production_carrier_validator':'PASS','production_metadata_validator':'PASS',
            'production_snapshot_constructor':'PASS','bad_checksum_rejection':'PASS',
            'callable_services':['MCON 1.2','XTCP 0.2'],'static_relocation_words':len(slots)}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--assembler',type=Path,default=Path.home()/'bin/z80asm')
    args=p.parse_args();OUT.mkdir(parents=True,exist_ok=True);base.OUT=OUT
    (OUT/'placement-report.json').unlink(missing_ok=True)
    (OUT/'XTCAP.RSX').unlink(missing_ok=True)
    images,oldslots,backends,metrics=base.build(args.assembler)
    placed,slots,unoptimized,count=owner(args.assembler,images)
    print('placed payload',len(placed[0]),'relocations',len(slots),'branches relaxed',count)
    print('unoptimized placed payload',len(unoptimized[0]))
    carrier=base.make_module(name='XTCAP',version=(0,2),services=[],linked_base=0x8000,
        code=placed[0],relocations=slots,reconstruction_class='STATEFUL',
        callable_services=[(b'MCON',1,2,placed[1]['AN_ENTRY']-0x8000,4),
                           (b'XTCP',0,2,placed[1]['TX_ENTRY']-0x8000,0)])
    (OUT/'XTCAP.RSX').write_bytes(carrier)
    print('PACKAGED',len(slots),'relocations, allocation',int.from_bytes(carrier[14:16],'little'))
    reference=dict(images);oldbackends=dict(backends)
    images['bios'],stage=packed_core(args.assembler,images)
    images['owner']=placed
    backends=placed_backends(args.assembler,images,backends)
    runs=[]
    for name in ('M4SCRN','ANSISCRN'):
        for origin in (0x9000,0xa101):
            fixture=PlacedFixture(args.assembler,images,slots,backends,name,origin)
            cases=base.exercise(fixture)+base.transactions(fixture,images)
            movement=move_owner(fixture,images,slots,int.from_bytes(carrier[14:16],'little'))
            stack={label:high-fixture.cpu._min_sp.get(label,high) for label,high in [('client',0x5f00),('warm',0x5d00),('bdos',fixture.bdos['UB_STKTOP'])]}
            runs.append({'backend':name,'origin':hex(origin),'cases':cases,'idle_movement':movement,'stack_observed_bytes':stack})
            print('PASS PLACED',name,hex(origin),len(cases),'cases',stack)
    parity=parser_parity(args.assembler,reference,oldslots,oldbackends,images,slots,backends)
    print('PASS parser parity',parity)
    regressions=core_regressions(args.assembler,reference['bios'],images['bios'],stage)
    print('PASS packed core regressions',regressions)
    probes=old_provider_probes(args.assembler,images,backends)
    print('PASS actual legacy unknown-probe behavior',probes)
    validation=carrier_validation(args.assembler,carrier,slots)
    print('PASS actual carrier/metadata/snapshot validation',validation)
    assert carrier[:5]==b'BRSX\x02'
    assert int.from_bytes(carrier[24:26],'little')==512
    assert [int.from_bytes(carrier[48+2*i:50+2*i],'little') for i in range(len(slots))]==slots
    import difflib
    changes=[]
    for relative in ('src/bios/bios.mac','src/platform/trs80m4/m4scroll.inc'):
        changes.extend(difflib.unified_diff((ROOT/relative).read_text().splitlines(True),(stage/relative).read_text().splitlines(True),fromfile='a/'+relative,tofile='b/'+relative,n=0))
    patch=''.join(changes)
    (OUT/'packed-core.patch').write_text(patch)
    from importlib.metadata import version
    report={
        'date':'2026-11-07','status':'PASS',
        'disposition':'CARRIER_AND_REFERENCE_MODEL4_PLACEMENT_GATES_RESOLVED_IN_PRIVATE_BUILD',
        'experimental_interface':'XTCP 0.2 subset; private MCON probe 25; no public allocation',
        'source_baseline':'d1c493c537a85ecef4ea88ffb78265af00982eb1',
        'python_version':sys.version.split()[0],
        'dependencies':{name:version(name) for name in ('pyte','wcwidth')},
        'carrier':{'format':2,'header_bytes':512,'relocation_capacity':232,
                   'relocations':len(slots),'spare_relocations':232-len(slots),
                   'relative_branches':count,'payload_bytes':len(placed[0]),
                   'allocation_bytes':int.from_bytes(carrier[14:16],'little'),
                   'baseline_personality_allocation_bytes':metrics['baseline_ansi_allocation_bytes'],
                   'loaded_allocation_delta_bytes':int.from_bytes(carrier[14:16],'little')-metrics['baseline_ansi_allocation_bytes'],
                   'optional_resident_bridge_bytes':placed[1]['GX_IMAGE']-placed[1]['GX_RECV'],
                   'sha256':hashlib.sha256(carrier).hexdigest()},
        'core':{'baseline_bios_bytes':len(reference['bios'][0]),'private_bios_bytes':len(images['bios'][0]),
                'hook_bytes':7,'saved_bytes':{'status_normalization':1,'routing_fallthrough':2,'scroll_fill':4},
                'fixed_image_growth_bytes':0,'tpa_exclusive':hex(base.L['TPA']),
                'unloaded_tpa_record_aligned_bytes':((base.L['TPA']-0x100)//128)*128,
                'monitor_binding':hex(images['bios'][1]['MP_MON']),
                'resident_span_bytes':(stage/'build/system/resident.bin').stat().st_size,
                'packed_image_checks':'PASS',
                'sha256':hashlib.sha256((stage/'build/system/resident.bin').read_bytes()).hexdigest()},
        'behavioral_cases':runs[0]['cases'],
        'runs':[{key:value for key,value in run.items() if key!='cases'}|{'case_count':len(run['cases'])} for run in runs],
        'parser_differential':parity,'core_regressions':regressions,
        'old_provider_probes':probes,'carrier_validation':validation,
        'source_sha256':{str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in (
            Path(__file__),base.HERE/'campaign.py',base.HERE/'owner.inc',base.HERE/'coordinator.mac',
            ROOT/'src/system/layout.inc',ROOT/'src/bios/bios.mac',ROOT/'src/platform/trs80m4/m4scroll.inc',
            ROOT/'src/rsx/ansi.mac',ROOT/'src/rsx/ansi-dispatch.inc',ROOT/'src/rsx/screen/rendition.inc',
            ROOT/'src/rsx/screen/model4.mac',ROOT/'src/rsx/screen/ansi-host.mac')},
        'private_core_patch_sha256':hashlib.sha256(patch.encode()).hexdigest(),
        'assembler_sha256':hashlib.sha256(args.assembler.read_bytes()).hexdigest(),
        'limits':['private staged Model 4 reference layout, not installed production source',
                  'host backend exercised with shared BIOS/router and host leaf, not a complete cpmsim image',
                  'fixture keyboard/warm entry and explicit idle publication rebinding',
                  'private MCON probe has no public allocation or compatibility handshake',
                  'boot-global identity allocator, full request ABI and finalizer/return-path admission deferred',
                  'no live/native/protected-ROM or media qualification',
                  'no utility migration or release assignment']}
    (OUT/'placement-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'carrier':report['carrier'],'core':report['core']},indent=2))





if __name__=='__main__':main()
