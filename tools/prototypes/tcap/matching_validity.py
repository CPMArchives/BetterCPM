#!/usr/bin/env python3
"""Private matched-system admission and permanent validity allocation campaign."""
import argparse
import binascii
import hashlib
import json
import re
import struct
import sys
from pathlib import Path
import campaign as base
import placement as placed
import system_paths as paths
import system_layout as layout

ROOT=base.ROOT
OUT=ROOT/'build/tcap-matching-validity'
ROLES=('bios','ccp','model4-reloader','stage2','metadata','finalizer','commit','publisher')


def sha(data):return hashlib.sha256(data).hexdigest()

def closure(assembler):
    names=set(json.loads((ROOT/'docs/engineering/evidence/tcap-system-paths/report.json').read_text())['source_sha256'])
    names.update(('tools/prototypes/tcap/matching_validity.py','tools/prototypes/tcap/validity-root.inc',
                  'src/system/gateway.mac','src/system/r3pst.mac','tools/build_system.py',
                  'tools/checked_build_contract.py','tools/checked_carriers.py'))
    names.update(str(path.relative_to(ROOT)) for folder in ('src/bdos','src/bios','src/system','src/platform','src/ccp','src/rsx') for path in (ROOT/folder).rglob('*') if path.is_file())
    inputs={name:sha((ROOT/name).read_bytes()) for name in sorted(names)}
    contract={'private_epoch':4,'permanent_bytes':512,'roles':ROLES,'inputs':inputs,'assembler_sha256':sha(assembler.read_bytes())}
    identity=hashlib.sha256(json.dumps(contract,sort_keys=True,separators=(',',':')).encode()).digest()[:16]
    return contract,identity


def root_text(identity,pins):
    text=(base.HERE/'validity-root.inc').read_text()
    text=text.replace('; @validity-build-id@','        DB '+','.join(str(b) for b in identity))
    text=text.replace('; @validity-artifact-pins@','        DB '+','.join(str(b) for b in pins))
    publisher=base.normalized((ROOT/'src/system/r3pst.mac').read_text())
    publisher=publisher[publisher.index('RT_ENTRY:'):publisher.index('        DS      RTBASE+0050H-$')]
    # Extended experimental commit record: +41 prepared-value pointer, +43 final
    # owner-validity pointer (zero for no TCAP owner). Both prepared before move.
    prefix='''        PUSH DE
        EX DE,HL
        LD BC,41
        ADD HL,BC
        LD E,(HL)
        INC HL
        LD D,(HL)
        PUSH DE
        INC HL
        LD E,(HL)
        INC HL
        LD D,(HL)
        POP HL
        LD A,D
        OR E
        JR Z,VG_NOVAL
        CALL VG_COPY
VG_NOVAL:
        POP DE
'''
    publisher=publisher.replace('RT_ENTRY:', 'VG_RPUB:',1)
    at=publisher.index('\n')+1
    publisher=publisher[:at]+prefix+publisher[at:]
    text=text.replace('; @validity-publisher@',publisher)
    return 'VG_IDOFF EQU 2257\nRT_REQ EQU LY_CFG+03F8H\n'+text


def gateway(assembler,stage,identity,pins):
    source=(ROOT/'src/system/gateway.mac').read_text()
    source,n=re.subn(r'(SYS_COLD:[^\n]*\n)        LD      SP,SYS_STKTOP',r'\1        JP      VG_CBOOT',source)
    assert n==1
    source=source.replace('        .DEPHASE\n',root_text(identity,pins)+'\n        .DEPHASE\n')
    (stage/'src/system/gateway.mac').write_text(source)
    return source


def rebuild_core(assembler,stage):
    import build_system as bs
    import build_bios as bb
    saved_bs={k:getattr(bs,k) for k in ('ROOT','SOURCE','BUILD','RESIDENT_BASE','COMPONENTS')}
    saved_bb={k:getattr(bb,k) for k in ('ROOT','SOURCE','PLATFORM','BUILD')}
    argv=sys.argv
    try:
        bs.ROOT=stage;bs.SOURCE=stage/'src/system/gateway.mac';bs.BUILD=stage/'build/system'
        bs.RESIDENT_BASE=base.L['SYSTEM'];bs.COMPONENTS=((base.L['SYSTEM'],'gateway.bin'),)+bs.COMPONENTS[1:]
        bb.ROOT=stage;bb.SOURCE=stage/'src/bios';bb.PLATFORM=stage/'src/platform/trs80m4';bb.BUILD=stage/'build/bios'
        sys.argv=['build_system.py','--assembler',str(assembler)]
        bs.main()
    finally:
        sys.argv=argv
        for name,value in saved_bs.items():setattr(bs,name,value)
        for name,value in saved_bb.items():setattr(bb,name,value)
    return (stage/'build/bios/bios.bin').read_bytes(),base.symbols(stage/'build/bios/bios.lst')


def owner(assembler,images,identity,root):
    # Reuse the reviewed source transforms, capturing only its assembled text.
    # The old campaign stays byte-for-byte unchanged and remains reproducible.
    original=placed.relax;captured=[]
    def capture(a,text):captured.append(text);return original(a,text)
    placed.relax=capture
    try:paths.owner(assembler,images)
    finally:placed.relax=original
    text=captured[0]
    marker='TX_ENTRY:\n        PUSH IX\n        LD IX,TX_STATE\n'
    assert text.count(marker)==1
    gate='''        PUSH AF
        PUSH DE
        LD DE,TX_BUILD
        CALL VG_CHECK
        POP DE
        OR A
        JR NZ,TX_DENY
        LD A,(IX+(TX_VALID-TX_STATE))
        OR (IX+(TX_VALID-TX_STATE+1))
        OR (IX+(TX_VALID-TX_STATE+2))
        OR (IX+(TX_VALID-TX_STATE+3))
        JR Z,TX_DENY
        POP AF
        JR TX_OPEN
TX_DENY:
        POP AF
        POP IX
        LD A,10
        OR A
        RET
TX_OPEN:
'''
    text=text.replace(marker,marker+gate)
    text=text.replace('TX_VALID: DB 1,0,0,0','TX_VALID: DB 0,0,0,0')
    text=text.replace('        END\n','TX_BUILD: DB '+','.join(map(str,identity))+'\n        END\n')
    text=f'VG_CHECK EQU 0{root["VG_CHECK"]:04X}H\n'+text
    text,count=placed.relax(assembler,text)
    (OUT/'matched-owner.mac').write_text(text)
    code,labels=placed.emit(assembler,'matched-owner',text,0x8000)
    alt,_=placed.emit(assembler,'matched-owner-alt',text.replace('08000H','08101H'),0x8101)
    slots=base.relocation_offsets(code,alt,0x101)
    third,_=placed.emit(assembler,'matched-owner-third',text.replace('08000H','08427H'),0x8427)
    assert base.relocated(code,slots,0x8427)==third
    assert code[labels['TX_VALID']-0x8000:labels['TX_VALID']-0x8000+4]==bytes(4)
    return (code,labels),slots,count


def metadata(assembler,images,root,identity_offset):
    text=(ROOT/'src/system/r3meta.mac').read_text()
    # Relax only MCON 1.3, after a positive matched-root/owner-build check.
    # Existing 1.0/1.1/1.2 and SCRN 1.1 rules remain unchanged.
    old='        CP      3\n        JR      NC,RXM_MBAD'
    new='''        CP      3
        JR      C,VM_OLD
        JR      NZ,RXM_MBAD
        PUSH HL
        LD HL,(RXM_DATA)
        LD A,(HL)
        CP 'M'
        JR NZ,VM_NO
        POP HL
        DEC HL
        PUSH HL
        LD DE,(RXM_PAYLOAD)
        LD BC,(RXM_CODE)
        CALL VG_META
        OR A
        JR NZ,VM_NO
        POP HL
        LD A,2
        JR VM_OLD
VM_NO:
        POP HL
        JP RXM_MBAD
VM_OLD:
'''
    assert text.count(old)==1
    text=text.replace(old,new)
    text=text.replace('RXM_MONITOR:\n','RXM_MONITOR:\n        LD HL,(RXM_DATA)\n        LD DE,(RXM_PAYLOAD)\n        LD BC,(RXM_CODE)\n        CALL VG_XTEST\n        RET NC\n',1)
    active=True;lines=[]
    for line in text.splitlines():
        if line.strip()=='IF BP_CHECKED EQ 1':active=False
        elif line.strip()=='ELSE':active=not active
        elif line.strip()=='ENDIF':active=True
        elif active:lines.append(line)
    text='\n'.join(lines)+'\n'
    text=re.sub(r'\bJR(\s+(?:NZ|Z|NC|C),RXM_M(?:BAD|OK))',r'JP\1',text)
    assert identity_offset==2257
    text=f'VG_META EQU 0{root["VG_META"]:04X}H\nVG_XTEST EQU 0{root["VG_XTEST"]:04X}H\n'+text
    text=re.sub(r'^RMBASE\s+EQU[^\n]*',f'RMBASE EQU 0{base.L["CONFIG"]:04X}H',text,flags=re.M)
    text,_=placed.relax(assembler,base.normalized(text))
    (OUT/'metadata.mac').write_text(text)
    data,labels=placed.emit(assembler,'metadata',text,base.L['CONFIG'])
    assert len(data)<=1024,('metadata budget',len(data))
    return data,labels


def envelope(role,data,identity):
    return bytes((role,))+identity+struct.pack('<HH',len(data),binascii.crc_hqx(data,0xffff))+data


def seal(artifacts,identity,core,resident):
    assert set(artifacts)==set(ROLES)
    return {'schema':1,'private_epoch':4,'identity':identity.hex(),'root_sha256':sha(core),'resident_sha256':sha(resident),
            'artifacts':{name:{'sha256':sha(data),'length':len(data),'crc16':binascii.crc_hqx(data,0xffff)} for name,data in artifacts.items()}}


def admit(manifest,artifacts,core,resident):
    if sha(resident)!=manifest['resident_sha256']:raise ValueError('unmatched resident image')
    if sha(core)!=manifest['root_sha256']:raise ValueError('unmatched permanent root')
    if set(artifacts)!=set(ROLES):raise ValueError('missing or unrecognized matching-system role')
    for name,data in artifacts.items():
        if sha(data)!=manifest['artifacts'][name]['sha256']:raise ValueError('unmatched artifact: '+name)
    return True


def load_root(f,core,root,artifacts,identity):
    c=f.cpu;c.mem[base.L['SYSTEM']:base.L['SYSTEM']+len(core)]=core
    c._stack_bounds['system']=(root['SYS_STKTOP']-32,root['SYS_STKTOP'])
    for role,name in enumerate(ROLES):
        data=envelope(role,artifacts[name],identity);c.mem[0x1000:0x1000+len(data)]=data
        c.hl=0x1000;c.de=0x1000+len(data)
        assert f.run(root['VG_LOAD'],role)==0,(name,'root admission')
    assert c.mem[root['VG_MASK']]==255


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--assembler',type=Path,default=Path.home()/'bin/z80asm')
    a=p.parse_args();OUT.mkdir(parents=True,exist_ok=True);base.OUT=placed.OUT=paths.OUT=OUT
    (OUT/'report.json').unlink(missing_ok=True)
    contract,identity=closure(a.assembler)
    images,_,backends,_=base.build(a.assembler)
    images['bios'],stage=placed.packed_core(a.assembler,images)
    old_layout=dict(base.L);old_text=layout.LAYOUT_TEXT
    # Permanent allocator/admission root is charged even with no RSX profile.
    changes={'LY_SYS':old_layout['SYSTEM']-512,'LY_HIST':old_layout['HISTORY']-512,
             'LY_TPA':old_layout['TPA']-512,'LY_RSX':old_layout['RSX']-512,'LY_SECTS':14}
    newtext=old_text
    for name,value in changes.items():newtext=re.sub(r'^'+name+r'\s+EQU[^\n]*',f'{name} EQU 0{value:04X}H',newtext,flags=re.M)
    (stage/'src/system/layout.inc').write_text(newtext);layout.LAYOUT_TEXT=newtext
    for alias,name in layout.ALIASES.items():
        if name in changes:base.L[alias]=changes[name]
    base.L.update(PDS_DESCRIPTOR=base.L['SYSTEM']+0x80,PDS_TOP=base.L['SYSTEM'],PDS_LOW=base.L['HISTORY'])
    tables=stage/'src/bios/tables.mac'
    table_text=tables.read_text();assert table_text.count('        DW 389,127')==1 and table_text.count('        DW 32,2')==1
    tables.write_text(table_text.replace('        DW 389,127','        DW 384,127').replace('        DW 32,2','        DW 32,3'))
    # 14 resident sectors plus existing loaders and 13 command sectors end at
    # sector 41. Reserve three tracks (60 sectors), not the old 40-sector area.
    assert 14+14+13==41 and 41<=3*20
    try:
        gateway(a.assembler,stage,identity,bytes(32))
        images['bios']=rebuild_core(a.assembler,stage)
        root=base.symbols(stage/'build/system/gateway.lst')
        matched,slots,branches=owner(a.assembler,images,identity,root)
        built,_=paths.sources(a.assembler,stage)
        # The infallible publisher body moves into the fixed root. Its old slot
        # remains the same size and retains the prefetched-resolver continuation.
        text=base.normalized((ROOT/'src/system/r3pst.mac').read_text())
        start=text.index('RT_ENTRY:');end=text.index('        DS      RTBASE+0050H-$')
        text=text[:start]+f'RT_ENTRY: JP 0{root["VG_RPUB"]:04X}H\n'+text[end:]
        (stage/'src/system/r3pst.mac').write_text(text)
        publisher,_=placed.emit(a.assembler,'publisher',text,base.L['CONFIG']+0x38f)
        meta=metadata(a.assembler,images,root,matched[1]['TX_BUILD']-0x8000)
        artifacts={'bios':images['bios'][0],**{name:built[name][0] for name in ('ccp','model4-reloader','stage2','finalizer','commit')},'metadata':meta[0],'publisher':publisher}
        pins=b''.join(struct.pack('<HH',len(artifacts[name]),binascii.crc_hqx(artifacts[name],0xffff)) for name in ROLES)
        gateway(a.assembler,stage,identity,pins)
        images['bios']=rebuild_core(a.assembler,stage)
        root=base.symbols(stage/'build/system/gateway.lst');core=(stage/'build/system/gateway.bin').read_bytes()
        assert len(core)<=base.L['BDOS']-base.L['SYSTEM']
        assert root['VG_END']<=base.L['BDOS']
        images['owner']=matched;images['commit']=built['commit'][:2]
        backends=placed.placed_backends(a.assembler,images,backends)
        resident=(stage/'build/system/resident.bin').read_bytes()
        manifest=seal(artifacts,identity,core,resident);assert admit(manifest,artifacts,core,resident)
        (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        carrier=base.make_module(name='XTCAP',version=(0,4),services=[],linked_base=0x8000,code=matched[0],relocations=slots,reconstruction_class='STATEFUL',callable_services=[(b'MCON',1,3,matched[1]['AN_ENTRY']-0x8000,4),(b'XTCP',0,4,matched[1]['TX_ENTRY']-0x8000,0)])
        print('BUILT MATCHED',len(core),len(matched[0]),len(slots),len(meta[0]),flush=True)
        report=qualify(a.assembler,images,slots,backends,built,core,root,artifacts,identity,manifest,carrier)
        import difflib
        patch=''.join(line for path in ('src/system/layout.inc','src/system/gateway.mac','src/bios/tables.mac','src/system/r3pst.mac') for line in difflib.unified_diff((ROOT/path).read_text().splitlines(True),(stage/path).read_text().splitlines(True),fromfile='a/'+path,tofile='b/'+path,n=0))
        (OUT/'permanent-root.patch').write_text(patch)
        from importlib.metadata import version
        report.update(date='2026-11-07',python_version=sys.version.split()[0],dependencies={name:version(name) for name in ('pyte','wcwidth')},patch_sha256=sha(patch.encode()),manifest_sha256=sha((OUT/'manifest.json').read_bytes()),status='PASS',source_baseline='a65cc772116c91c743ff61c8b89b0bb2ed6f3c75',identity=identity.hex(),contract=contract,
            placement={'permanent_added_bytes':512,'gateway_bytes':len(core),'root_bytes':root['VG_END']-root['VG_CHECK'],
                       'resident_span_bytes':(stage/'build/system/resident.bin').stat().st_size,'boot_sectors':14,'boot_volume_reserved_tracks':3,'boot_volume_dsm':384,'boot_volume_capacity_loss_bytes':10240,
                       'tpa_exclusive':hex(base.L['TPA']),'unloaded_tpa_record_bytes':((base.L['TPA']-0x100)//128)*128,
                       'owner_payload_bytes':len(matched[0]),'owner_relocations':len(slots),'owner_allocation_bytes':int.from_bytes(carrier[14:16],'little'),
                       'metadata_overlay_bytes':len(meta[0]),'publisher_overlay_bytes':len(publisher)},
            limits=['private reference build only; no production sources or distribution media changed',
                    'reference stage2 fixture bindings; not a full checked cpmsim profile or live/native qualification',
                    'prepared validity record supplied explicitly by campaign; full finalizer/context-producer record construction not implemented',
                    'CPU load gate validates bound buffers; file-reader copy/execute front doors are not yet wired to it',
                    'private boot-volume DPB uses OFF=3/DSM=384; existing OFF=2 disks are incompatible; no distribution disk created',
                    'full public request ABI, utility migrations and release assignment deferred'])
        (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report['placement'],indent=2))
    finally:base.L.clear();base.L.update(old_layout);layout.LAYOUT_TEXT=old_text


def qualify(assembler,images,slots,backends,built,core,root,artifacts,identity,manifest,carrier):
    runs=[]
    for name in ('M4SCRN','ANSISCRN'):
        for origin in (0x9000,0xa101):
            f=placed.PlacedFixture(assembler,images,slots,backends,name,origin)
            c=f.cpu
            # Zero validity and an unadmitted cold root cannot create a session.
            c.mem[base.L['SYSTEM']:base.L['SYSTEM']+len(core)]=core
            before=bytes(c.mem[origin:origin+len(images['owner'][0])])
            assert f.owner(2,bytes(16))[0]==10 and before==bytes(c.mem[origin:origin+len(images['owner'][0])])
            load_root(f,core,root,artifacts,identity)
            assert f.owner(2,bytes(16))[0]==10
            c.hl=f.labels['TX_VALID'];assert f.run(root['VG_ALLOC'])==0
            assert bytes(c.mem[f.labels['TX_VALID']:f.labels['TX_VALID']+4])==b'\x01\0\0\0'
            prior=base.exercise(f)
            # Exercise the reviewed real return entries/guard cases, but the
            # fixture-only fake-state tests bypass public Begin, not validity.
            cases=paths.checks(f,images,built)
            extra=allocator_checks(f,images,slots,core,root,artifacts,identity,carrier)
            stack={label:high-c._min_sp.get(label,high) for label,(_,high) in c._stack_bounds.items()}
            runs.append({'backend':name,'origin':hex(origin),'prior_case_count':len(prior)+len(cases),'new_cases':extra,'observed_stack_bytes':stack})
            print('PASS MATCHED',name,hex(origin),len(extra),stack,flush=True)
    binding=binding_checks(assembler,images,slots,core,root,artifacts,identity,manifest,carrier)
    regression=full_regressions(assembler,images,built,backends)
    return {'runs':runs,'binding':binding,'regressions':regression}


def full_regressions(assembler,images,built,backends):
    # The extra system sector crosses a cylinder boundary. The historical test
    # reader keys only side/sector, so qualify with an explicit three-coordinate
    # service instead. Carrier parsing/movement/recovery assertions are unchanged.
    import test_ccpreload as regression
    original=regression.Z80
    class TrackAware(original):
        def run(self,address,limit=1000):
            if address==regression.BASE:
                module=bytearray(regression.MODULE.read_bytes())
                code,labels,origin,_=built['model4-reloader'];at=labels['CRSECTS']-origin
                sectors=[tuple(code[at+3*i:at+3*i+3]) for i in range(13)]
                _,side,physical=sectors[0]
                first=regression.MODULE_SOURCE+(side*16+physical-6)*512
                # Preserve the unit test's required-CCP corruption injection.
                module[:512]=self.mem[first:first+512]
                padded=module+bytes((-len(module))%512)
                blocks={key:padded[i*512:(i+1)*512] for i,key in enumerate(sectors)}
                assert len(blocks)==13
                self.mem[0x5800:0x5804]=bytes((0xd3,200,0xaf,0xc9))
                def output(port,value):
                    assert port&255==200
                    key=(value,self.b,self.c);data=blocks[key];assert len(data)==512
                    self.mem[self.hl:self.hl+512]=data;self.hl=(self.hl+512)&65535
                self.port_write=output
            return super().run(address,limit)
    regression.Z80=TrackAware
    try:result=paths.regressions(assembler,images,built,backends)
    finally:regression.Z80=original
    result['physical_read_fixture']='track/side/sector service; crosses cylinder boundary without aliases'
    return result


def allocator_checks(f,images,slots,core,root,artifacts,identity,carrier):
    c=f.cpu;cases=[]
    def check(name,value):assert value,name;cases.append(name)
    # Range/carry/exhaustion use private preparation memory, never caller tokens.
    for value in (1,0xff,0xffff,0xffffff,0xfffffffe):
        c.setword(root['VG_NEXT'],value&65535);c.setword(root['VG_NEXT']+2,value>>16)
        c.mem[0x6580:0x6584]=b'ABCD';c.hl=0x6580
        check('global allocation carry '+hex(value),f.run(root['VG_ALLOC'])==0 and int.from_bytes(c.mem[0x6580:0x6584],'little')==value+1)
    before=bytes(c.mem[root['VG_NEXT']:root['VG_NEXT']+4]);c.mem[0x6580:0x6584]=b'ABCD';c.hl=0x6580
    check('global exhaustion refuses without writes',f.run(root['VG_ALLOC'])==20 and bytes(c.mem[0x6580:0x6584])==b'ABCD' and bytes(c.mem[root['VG_NEXT']:root['VG_NEXT']+4])==before)
    # Fresh isolated boot for lifecycle tests. Only true cold entry clears the
    # allocator. SYS_ENTER is the explicit next-phase boundary, not mocked reset.
    saved=bytes(c.mem[root['SYS_ENTER']:root['SYS_ENTER']+3])
    c.mem[root['SYS_ENTER']:root['SYS_ENTER']+3]=b'\xc3\xff\xff'
    c.run(root['SYS_COLD'],limit=500000)
    check('actual cold entry resets admission and global counter',bytes(c.mem[root['VG_NEXT']:root['VG_NEXT']+4])==bytes(4) and c.mem[root['VG_MASK']]==0)
    c.mem[root['SYS_ENTER']:root['SYS_ENTER']+3]=saved;c.sp=0x5f00
    load_root(f,core,root,artifacts,identity)
    c.hl=f.labels['TX_VALID'];assert f.run(root['VG_ALLOC'])==0
    # Reset local serials only as a fresh experimental allocation would.
    for field in ('TX_SESS','TX_SSEQ','TX_SCOPE'):c.mem[f.labels[field]:f.labels[field]+4]=bytes(4)
    _,retired=f.owner(2,bytes(16));assert f.owner(4,retired)[0]==0
    check('first activation uses root-issued validity',retired[:4]==b'\x01\0\0\0')
    # Warm entry must retain the root even though it discards/rebuilds commands.
    # Stop at SYS_ENTER before filesystem work; the protected reset adapter is
    # a controlled RET here, unrelated to allocator state.
    cleanup=base.L['EXTENSIONS']+15;old_cleanup=bytes(c.mem[cleanup:cleanup+3]);c.mem[cleanup:cleanup+3]=b'\xc9\0\0'
    c.mem[root['SYS_ENTER']:root['SYS_ENTER']+3]=b'\xc3\xff\xff'
    c.run(root['SYS_WARM'],limit=500000)
    check('actual warm entry preserves validity namespace',int.from_bytes(c.mem[root['VG_NEXT']:root['VG_NEXT']+4],'little')==1 and c.mem[root['VG_MASK']]==255)
    c.mem[cleanup:cleanup+3]=old_cleanup;c.mem[root['SYS_ENTER']:root['SYS_ENTER']+3]=saved;c.sp=0x5f00
    # A failed preparation burns an identity without invalidating the old one.
    c.hl=0x6580;assert f.run(root['VG_ALLOC'])==0
    current=bytes(c.mem[f.labels['TX_VALID']:f.labels['TX_VALID']+4])
    check('aborted preparation leaves live validity unchanged',current==retired[:4] and int.from_bytes(c.mem[0x6580:0x6584],'little')==2)
    for image,address in (('mover',0x7000),('scheduler',0x7800),('commit',0x7c00)):
        c.mem[address:address+len(images[image][0])]=images[image][0]
    c.mem[base.L['CONFIG']+0x38f:base.L['CONFIG']+0x38f+len(artifacts['publisher'])]=artifacts['publisher']
    old=f.base;new=0xa101 if old==0x9000 else 0x9000;allocation=int.from_bytes(carrier[14:16],'little')
    def request(source,destination,fresh=False,empty=False):
        count=0 if empty else 1;top=destination+allocation
        c.mem[0x6100:0x6108]=struct.pack('<HHHBB',0 if fresh else source,destination,allocation,1,0)
        c.mem[0x6200:0x6203]=struct.pack('<HB',0x3400,len(slots))
        c.mem[0x3400:0x3400+2*len(slots)]=struct.pack('<'+'H'*len(slots),*slots)
        c.mem[0x6240:0x6246]=struct.pack('<HHH',0x3600 if fresh else 0,allocation if fresh else 0,f.labels['AN_ENTRY']-f.base)
        c.mem[0x6460:0x646a]=struct.pack('<5H',0x6600,0x6602,0x6604,0x6606,0x6608)
        c.mem[0x6500:0x6529]=bytes(41);c.mem[0x6500]=count
        c.setword(0x6606,7)
        data=struct.pack('<HHHBBHHHHHHHHB',0x6100,0x6200,0x6240,count,1,0x6400,0x7800,0x6800,512,0x7000,top,base.L['BDOS'],0x6460,1)
        data+=struct.pack('<8H',base.L['CONFIG']+0x38f,0x6500,base.L['RSX_STATE'],0x6540,0xffff,
                         f.bios['MC_RAW'] if empty else destination+f.labels['AN_ENTRY']-f.base,0,0)
        data+=struct.pack('<HH',0x6580,0 if empty else destination+f.labels['TX_VALID']-f.base)
        assert len(data)==45
        c.mem[0x6000:0x6000+len(data)]=data;c.de=0x6000
    # Reserve #3; malformed commit must not publish it, nor mutate the owner.
    c.hl=0x6580;assert f.run(root['VG_ALLOC'])==0
    request(old,new);c.mem[0x6006]=5
    check('failed real commit does not publish reserved validity',f.run(0x7c00)==255 and bytes(c.mem[f.labels['TX_VALID']:f.labels['TX_VALID']+4])==current and c.word(0x6606)==7)
    # Reserve #4, perform real STATEFUL move and persistent publication.
    c.hl=0x6580;assert f.run(root['VG_ALLOC'])==0
    request(old,new)
    before_root=bytes(c.mem[root['VG_NEXT']:root['VG_NEXT']+4])
    events=[];valid_target=new+f.labels['TX_VALID']-f.base
    watched=set(range(valid_target,valid_target+4))|{0x6606,0x6607,f.bios['MP_MON'],f.bios['MP_MON']+1}
    class PublicationOrder(base.WatchedMemory):
        def __setitem__(self,key,value):
            if isinstance(key,int):addresses=[key]
            else:addresses=range(*key.indices(len(self)))
            events.extend(address for address in addresses if address in watched)
            return super().__setitem__(key,value)
    c.mem=PublicationOrder(c,c.mem,f.bdos)
    assert f.run(0x7c00)==0
    generation=events.index(0x6606)
    check('validity and dispatch publish before generation marker',all(events.index(address)<generation for address in watched-{0x6606,0x6607}))
    delta=new-old;f.base=new;f.labels={key:value+delta for key,value in f.labels.items()};f.gx={key:value+delta for key,value in f.gx.items()}
    check('real commit moves owner and publishes new validity',c.word(f.bios['MP_MON'])==f.labels['AN_ENTRY'] and c.word(0x6606)==8 and bytes(c.mem[f.labels['TX_VALID']:f.labels['TX_VALID']+4])==b'\x04\0\0\0')
    check('owner movement cannot move/reset root allocator',bytes(c.mem[root['VG_NEXT']:root['VG_NEXT']+4])==before_root)
    c.mem[old:old+allocation]=b'\xdd'*allocation
    # Actual empty publication retires the Monitor while root state remains.
    request(new,new,empty=True);assert f.run(0x7c00)==0
    check('real unload preserves boot-global allocator',c.word(f.bios['MP_MON'])==f.bios['MC_RAW'] and bytes(c.mem[root['VG_NEXT']:root['VG_NEXT']+4])==before_root)
    # Reinstall cold bytes at the old address with local counters zero. Snapshot
    # construction is explicit; real commit copies/links/publishes it.
    fresh=base.relocated(images['owner'][0],slots,old)+bytes(allocation-len(images['owner'][0]))
    c.mem[0x3600:0x3600+allocation]=fresh
    c.setword(0x3600+f.labels['AN_BACKEND']-f.base,0x5000+f.backend_labels['S_ENTRY']-0x5000 if f.name=='M4SCRN' else f.backend_labels['SB_ENTRY'])
    c.hl=0x6580;assert f.run(root['VG_ALLOC'])==0
    request(0,old,fresh=True);assert f.run(0x7c00)==0
    delta=old-f.base;f.base=old;f.labels={key:value+delta for key,value in f.labels.items()};f.gx={key:value+delta for key,value in f.gx.items()}
    result,active=f.owner(2,bytes(16))
    check('same-address reload cannot recreate old session identity',result==0 and active[:4]==b'\x05\0\0\0' and active[4:]==retired[4:])
    check('old token cannot end reloaded active session',f.owner(4,retired)[0]==13 and f.state()==1)
    check('current token still ends session',f.owner(4,active)[0]==0)
    # Exhausted root never authorizes a zero-validity cold owner.
    c.mem[f.labels['TX_VALID']:f.labels['TX_VALID']+4]=bytes(4)
    c.mem[root['VG_NEXT']:root['VG_NEXT']+4]=b'\xff'*4;c.hl=0x6580
    before=bytes(c.mem[f.labels['AP_VALUE']:f.labels['AP_VALUE']+9])
    check('exhaustion cannot activate unissued owner',f.run(root['VG_ALLOC'])==20 and f.owner(2,bytes(16))[0]==10 and f.state()==0 and before==bytes(c.mem[f.labels['AP_VALUE']:f.labels['AP_VALUE']+9]))
    return cases


def binding_checks(assembler,images,slots,core,root,artifacts,identity,manifest,carrier):
    import test_rsxcarrier as validation
    cases=[]
    resident=(OUT/'packed-core/build/system/resident.bin').read_bytes()
    # Build-sealed SHA256 closure rejects stale bytes even with recomputed CRC.
    for name in ROLES:
        bad=dict(artifacts);data=bytearray(bad[name]);data[-1]^=1;bad[name]=bytes(data)
        try:admit(manifest,bad,core,resident)
        except ValueError:cases.append('SHA closure rejects altered '+name)
        else:raise AssertionError(name)
        missing=dict(artifacts);del missing[name]
        try:admit(manifest,missing,core,resident)
        except ValueError:cases.append('SHA closure rejects missing '+name)
        else:raise AssertionError(name)
    # CPU load gate tests each role, each identity byte, pinned size/CRC and data.
    cpu=base.Z80(b'');cpu.mem[base.L['SYSTEM']:base.L['SYSTEM']+len(core)]=core;cpu.sp=0x5f00
    total=0
    for role,name in enumerate(ROLES):
        original=envelope(role,artifacts[name],identity)
        for offset in list(range(1,17))+[0,17,19,21,len(original)-1]:
            data=bytearray(original);data[offset]^=1
            cpu.mem[0x1000:0x1000+len(data)]=data;cpu.hl=0x1000;cpu.de=0x1000+len(data);cpu.a=role
            before=cpu.mem[root['VG_MASK']];cpu.run(root['VG_LOAD'],limit=500000)
            assert cpu.a!=0 and cpu.mem[root['VG_MASK']]==before,(name,offset)
            total+=1
        cpu.mem[0x1000:0x1000+len(original)]=original;cpu.hl=0x1000;cpu.de=0x1000+len(original);cpu.a=role;cpu.run(root['VG_LOAD'],limit=500000);assert cpu.a==0
        # Positive metadata admission remains unavailable with any required role
        # missing, including command carriers and the infallible publisher.
        cpu.mem[root['VG_MASK']]=255^(1<<role);cpu.mem[0x1000:0x1010]=identity;cpu.de=0x1000;cpu.run(root['VG_CHECK'],limit=5000)
        assert cpu.a==255
        cpu.mem[0x6580:0x6584]=b'ABCD';cpu.hl=0x6580;cpu.run(root['VG_ALLOC'],limit=5000)
        assert cpu.a==255 and bytes(cpu.mem[0x6580:0x6584])==b'ABCD'
        cpu.mem[root['VG_MASK']]=0
        for available in (0,20,len(original)-1,len(original)+1):
            cpu.mem[0x1000:0x1000+len(original)]=original;cpu.hl=0x1000;cpu.de=0x1000+available;cpu.a=role
            cpu.run(root['VG_LOAD'],limit=500000)
            assert cpu.a!=0 and cpu.mem[root['VG_MASK']]==0
            total+=1
    for which in ('root','resident'):
        bad=bytearray(core if which=='root' else resident);bad[-1]^=1
        try:admit(manifest,artifacts,bytes(bad) if which=='root' else core,bytes(bad) if which=='resident' else resident)
        except ValueError:cases.append('SHA closure rejects altered '+which)
        else:raise AssertionError(which)
    # Execute the real carrier and modified metadata validators on independent
    # CPUs, retaining facts atomically on every failure.
    folder=OUT/'metadata-validation/build/system';folder.mkdir(parents=True,exist_ok=True)
    for filename,symbol,out in [('r3carr.mac','RXBASE','R3CARR.RSX')]:
        text=(ROOT/'src/system'/filename).read_text();text=re.sub(r'^'+symbol+r'\s+EQU[^\n]*',f'{symbol} EQU 0{base.L["CONFIG"]:04X}H',text,flags=re.M)
        data=base.assemble(assembler,base.normalized(text),folder/out,folder/(out+'.lst'),base.L['CONFIG']);assert len(data)<=1024
    (folder/'R3META.RSX').write_bytes(artifacts['metadata'])
    previous=validation.ROOT,validation.CARRIER
    try:
        validation.ROOT=folder.parents[1];validation.CARRIER=0x3000
        admitted_root=None
        for missing in [None]+list(range(8)):
            c,_=validation.phase_one(carrier,b'XTCAP   ');assert c.a==0
            c.mem[base.L['SYSTEM']:base.L['SYSTEM']+len(core)]=core
            # Populate admission using actual root byte/CRC checks.
            for role,name in enumerate(ROLES):
                if role==missing:continue
                data=envelope(role,artifacts[name],identity);c.mem[0x1000:0x1000+len(data)]=data;c.hl=0x1000;c.de=0x1000+len(data);c.a=role;c.run(root['VG_LOAD'],limit=500000);assert c.a==0
            if missing is None:admitted_root=bytes(c.mem[base.L['SYSTEM']:base.L['SYSTEM']+len(core)])
            before=validation.phase_two(c,len(carrier))
            assert c.a==(0 if missing is None else 255)
            if missing is not None:assert bytes(c.mem[validation.FACTS:validation.FACTS+26])==before
            cases.append('real metadata '+('accepts complete matched system' if missing is None else 'rejects absent '+ROLES[missing]))
        assert admitted_root is not None
        variants=[]
        for minor in (1,2,3):
            old=base.make_module(name='XTCAP',version=(0,minor),services=[],linked_base=0x8000,code=images['owner'][0],relocations=slots,reconstruction_class='STATEFUL',callable_services=[(b'MCON',1,2,images['owner'][1]['AN_ENTRY']-0x8000,4),(b'XTCP',0,minor,images['owner'][1]['TX_ENTRY']-0x8000,0)])
            variants.append(('rejects old experimental XTCP 0.'+str(minor),old,False))
        bad=bytearray(carrier);offset=512+images['owner'][1]['TX_BUILD']-0x8000;bad[offset]^=1
        struct.pack_into('<H',bad,44,sum(bad[512:512+len(images['owner'][0])])&65535)
        variants.append(('rejects foreign owner identity after valid carrier checksum',bytes(bad),False))
        ansi=images['ansi-base'];repairs=base.relocation_offsets(ansi[0],images['ansi-base-alt'][0],0x101)
        legacy=base.make_module(name='XTCAP',version=(0,1),services=[],linked_base=0x8000,code=ansi[0],relocations=repairs,reconstruction_class='STATEFUL',callable_services=[(b'MCON',1,2,ansi[1]['AN_ENTRY']-0x8000,4)])
        variants.append(('accepts ordinary legacy MCON without TCAP admission',legacy,True))
        for label,candidate,accepted in variants:
            c,_=validation.phase_one(candidate,b'XTCAP   ');assert c.a==0,label
            c.mem[base.L['SYSTEM']:base.L['SYSTEM']+len(core)]=admitted_root if not accepted else core
            before=validation.phase_two(c,len(candidate))
            assert c.a==(0 if accepted else 255),label
            if not accepted:assert before==bytes(c.mem[validation.FACTS:validation.FACTS+26])
            cases.append('real metadata '+label)
    finally:validation.ROOT,validation.CARRIER=previous
    return {'named_cases':cases,'cpu_foreign_or_corrupt_envelope_cases':total,'all_eight_roles_required':True}

if __name__=='__main__':main()
