#!/usr/bin/env python3
"""Part 7 isolated build/loader prototype; not a supported release builder.

Stages complete source trees. The checked transformations never modify the
source checkout. Unselected Model 4/ROM products are not deliverables.
"""
from __future__ import annotations
import argparse, binascii, hashlib, json, re, shutil, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PROFILES={'cpmsim-legacy':(0,False),'cpmsim-legacy-checked':(0,True),
          'cpmsim-fullram':(0xC00,True),'model4-legacy':(0,False)}

def replace(text,old,new,count=1):
    if text.count(old)!=count:raise ValueError('source drift: '+old[:90])
    return text.replace(old,new)

def apply_checked(root, identity):
    def read(p):return (root/p).read_text()
    def write(p,s):(root/p).write_text(s)
    layout=read('src/system/layout.inc')
    vals={n:int(v,16) for n,v in re.findall(r'^(LY_\w+)\s+EQU\s+0([0-9A-F]+)H',layout,re.M)}
    # A fixed entry for the CRC and rollback pointer in the existing BIOS tail.
    layout+=f"\nLY_CCRC EQU 0{vals['LY_FILE']-32:04X}H\nLY_CBACK EQU 0{vals['LY_FILE']-2:04X}H\nLY_CCMP EQU 0{vals['LY_BIOS']-26:04X}H\nLY_CID EQU 0{vals['LY_BIOS']-16:04X}H\n"
    write('src/system/layout.inc',layout)
    text=read('src/system/extens.mac')
    text=replace(text,'        CALL    RSXCONTROL\n        POP     DE','        CALL    LY_CFG\n        POP     DE')
    write('src/system/extens.mac',text)
    entry=read('src/system/r3entry.mac')
    entry=replace(entry,'RVBASE          EQU     LY_RSX','RVBASE          EQU     LY_CFG')
    entry=replace(entry,'LD      BC,0F00H','LD      BC,1000H')
    marker='        LD      HL,(RV_HREQ+2)\n        LD      BC,0400H'
    backup='''        LD      A,(RSTCOUNT)
        OR      A
        JR      Z,RV_NOBACK
        LD      HL,(RV_HREQ+2)
        LD      DE,0B00H
        ADD     HL,DE
        LD      (LY_CBACK),HL
        EX      DE,HL
        LD      HL,LY_RSX
        LD      BC,03F4H
        LDIR
RV_NOBACK:
'''
    entry=replace(entry,marker,backup+marker)
    before,reader=entry.split('RI_ENTRY:',1)
    # Only the initial state pointer moves: later +100h is saved-CFG placement.
    reader=reader.replace('LD      DE,0100H','LD      DE,0200H',1)
    reader=replace(reader,'RI_PACK-RI_ENTRY-0100H','RI_PACK-RI_ENTRY-0200H')
    reader=replace(reader,'CP      120','CP      124')
    old='''        LD      A,(IX+18)
        LD      (LY_FCB+32),A
        PUSH    IX
        POP     HL
        LD      DE,0500H
        OR      A
        SBC     HL,DE
        PUSH    HL
        CALL    LY_FILE+3'''
    new='''        PUSH    IX
        POP     HL
        LD      DE,0600H
        OR      A
        SBC     HL,DE
        PUSH    HL
        CALL    LY_FILE+3
        JR      NZ,RI_READFAIL
        LD      A,(LY_FCB+32)
        CP      4
        JR      NZ,RI_READFAIL
        POP     DE
        PUSH    DE
        LD      BC,0200H
        CALL    LY_CCRC
RI_EXPECT: LD DE,0
        OR      A
        SBC     HL,DE
        JR      NZ,RI_READFAIL
        POP     HL
        PUSH    HL
        LD      DE,8
        ADD     HL,DE
        PUSH    IX
        POP     DE
        EX      DE,HL
        LD      BC,RI_ID-RI_ENTRY-0200H
        ADD     HL,BC
        EX      DE,HL
        LD      B,16
RI_IDENT:
        LD      A,(DE)
        CP      (HL)
        JR      NZ,RI_READFAIL
        INC     DE
        INC     HL
        DJNZ    RI_IDENT
        POP     HL
        PUSH    HL
        LD      A,(IX+18)
        ADD     A,40
        LD      E,A
        LD      D,0
        ADD     HL,DE
        LD      A,(HL)
        LD      (IX+19),A
        INC     HL
        LD      A,(HL)
        LD      (IX+20),A
        LD      A,(IX+18)
        ADD     A,4
        LD      (LY_FCB+32),A
        POP     HL
        PUSH    HL
        CALL    LY_FILE+3'''
    reader=replace(reader,old,new)
    reader=replace(reader,'ADD     A,8','ADD     A,12')
    marker='''        POP     HL
        LD      A,(IX+0)
        OR      A
        LD      DE,LY_CFG'''
    validation='''        POP     DE
        PUSH    DE
        LD      BC,0400H
        CALL    LY_CCRC
        LD      E,(IX+19)
        LD      D,(IX+20)
        OR      A
        SBC     HL,DE
        JR      NZ,RI_READFAIL
'''
    reader=replace(reader,marker,validation+marker)
    reader=replace(reader,"RI_PACK: DB 'R3PACK  '","RI_PACK: DB 'R3PACK  '\nRI_ID: DB "+','.join(str(b) for b in bytes.fromhex(identity)))
    # Long exits remain position independent: compute the target from IX,
    # whose value is the copied entry + 200h. Conditional fallthrough is local.
    serial=[0]
    def far_failure(m):
        serial[0]+=1; label='RIX'+str(serial[0])
        inverse={'NZ':'Z','NC':'C'}[m[1]]
        return (f'        JR {inverse},{label}\n'
                f'        LD HL,{m[2]}-RI_ENTRY-0200H\n'
                '        PUSH IX\n        POP DE\n        ADD HL,DE\n        JP (HL)\n'+label+':')
    reader=re.sub(r'^        JR\s+(NZ|NC),(RI_FAIL|RI_READFAIL)\b[^\n]*',far_failure,reader,flags=re.M)
    write('src/system/r3entry.mac',before+'RI_ENTRY:'+reader)
    for p in ['src/system/r3coord.mac','src/system/r3drop.mac']:
        write(p,replace(read(p),'LD      DE,0F00H','LD      DE,1000H'))
    write('src/system/r3final.mac',replace(read('src/system/r3final.mac'),'0A00H','0B00H',2))
    write('tools/build_rsxloader.py',replace(read('tools/build_rsxloader.py'),'BASE = LAYOUT["RSX"]','BASE = LAYOUT["CONFIG"]'))
    builder=read('tools/build_rsx_runtime_overlays.py')
    builder=replace(builder,'"RVBASE", rsx','"RVBASE", cfg')
    builder=replace(builder,'len(io) > 256','len(io) > 512')
    extra='''
    from assessment_checked_profiles import checked_pack, bound
    outputs[PACK_NAME] = checked_pack(outputs, ROOT)
    # The pack excludes R3ENTRY, so its final checksum can be embedded without
    # a circular build dependency. Reassemble the entry and copied reader.
    import binascii, re
    entry_path = ROOT / 'src/system/r3entry.mac'
    text = entry_path.read_text()
    checksum = binascii.crc_hqx(outputs[PACK_NAME][:512], 0xffff)
    text = re.sub(r'RI_EXPECT: LD DE,[^\\n]+', f'RI_EXPECT: LD DE,0{checksum:04X}H', text)
    entry_path.write_text(text)
    entry = build(args.assembler, 'r3entry', 'r3entry.mac', 'RVBASE', cfg)
    helper = text[text.index('RI_ENTRY:'):text.index('RI_END:')]
    io = assemble(args.assembler, '        INCLUDE layout.inc\\n        ASEG\\n        ORG 0\\n'+helper+'        END\\n', BUILD/'rsxio.bin', BUILD/'rsxio.lst', 0)
    if len(io)>512 or len(entry)>1000: raise ValueError('checked entry/reader/binding overflow')
    (BUILD/'rsxloader.bin').write_bytes(entry)
    outputs['R3ENTRY.RSX'] = bound(entry.ljust(1021,b'\\0') + gateway, ROOT)
'''
    builder=replace(builder,'    outputs[PACK_NAME] = pack(outputs)','    outputs[PACK_NAME] = pack(outputs)'+extra)
    write('tools/build_rsx_runtime_overlays.py',builder)
    bios=read('src/platform/z80pack/biosplat.inc')
    bios=bios[:bios.index('PL_RELOAD:')]+read('src/platform/z80pack/checked-load.inc')
    write('src/platform/z80pack/biosplat.inc',bios)
    builder=read('tools/build_z80pack_image.py')
    marker=" bios=asm('bios',"
    pre=" bios_source=bios_source.replace('        .DEPHASE', '        DS LY_CCRC-$\\n'+read('src/platform/z80pack/checked-crc.inc')+'\\n        .DEPHASE')\n"
    builder=replace(builder,marker,pre+marker)
    builder=replace(builder," bioslinks=equ(bs,", " assert bs['MP_MON_END'] <= L['FILE']-32, 'BIOS code overlaps verification tail'\n bioslinks=equ(bs,")
    marker=" disk=asm('disk',"
    cmp_code='        DS LY_CCMP-$\nZ_CMP: LD B,16\nZ_CMLP: LD A,(DE)\n        SUB (HL)\n        RET NZ\n        INC DE\n        INC HL\n        DJNZ Z_CMLP\n        RET\nZ_ID: DB '+','.join(str(x) for x in bytes.fromhex(identity))+'\n'
    builder=replace(builder,marker," disk_source=disk_source.replace('        END\\n',"+repr(cmp_code+"        END\n")+")\n"+marker)
    builder=replace(builder," ds=symbols(out/'disk.lst')", " ds=symbols(out/'disk.lst')\n assert ds['ZP_END'] <= L['BIOS']-26, 'disk state overlaps private contract'")
    marker=" resident=bytearray(L['DIRBUF']-L['SYSTEM'])"
    patch=''' import binascii
 from assessment_checked_profiles import bound
 assert L['RELOADER_CAPACITY']+len(selector)<=1000 and len(ctl)<=1000
 padded_loader=bound(loader.ljust(L['RELOADER_CAPACITY'],b'\\0')+selector.ljust(1024-L['RELOADER_CAPACITY'],b'\\0'), ROOT)
 ctl=bound(ctl.ljust(1024,b'\\0'), ROOT)
 checked_entry=(ROOT/'build/system/R3ENTRY.RSX').read_bytes()
 bios=bytearray(bios)
 checks={}
 for label,payload in [('Z_EREL',padded_loader),('Z_ECTL',ctl.ljust(1024,b'\\0')),('Z_EENT',checked_entry)]:
  value=binascii.crc_hqx(payload,0xffff); at=bs[label]+1-L['BIOS']
  assert bios[at-1]==0x21 and len(payload)==1024
  bios[at:at+2]=value.to_bytes(2,'little'); checks[label]=value
 bios=bytes(bios);(out/'bios.bin').write_bytes(bios)
 (out/'checked-load.json').write_text(json.dumps({'checksums':checks,'symbols':bs,'bios_bytes':len(bios),'bios_capacity':L['FILE']-L['BIOS']},indent=2)+'\\n')
'''
    builder=replace(builder,marker,patch+marker)
    builder=replace(builder," loader_carrier=loader.ljust(L['RELOADER_CAPACITY'],b'\\0')+selector.ljust(1024-L['RELOADER_CAPACITY'],b'\\0')",' loader_carrier=padded_loader')
    builder=replace(builder," def rsx_overlay(path):return path.read_bytes().ljust(1021,b'\\0')+gateway_tail"," def rsx_overlay(path):return bound(path.read_bytes().ljust(1021,b'\\0')+gateway_tail, ROOT)")
    write('tools/build_z80pack_image.py',builder)

def bound(data, root):
    assert len(data)==1024 and data[1000:1016]==bytes(16), 'private binding overlaps executable code'
    b=bytearray(data);b[1000:1016]=bytes.fromhex(json.loads((root/'assessment-profile.json').read_text())['compatibility_id'])
    return bytes(b)

def checked_pack(images, root):
    import struct
    from rsx_container import NAMES
    profile=json.loads((root/'assessment-profile.json').read_text())
    h=bytearray(512);h[:4]=b'BCPH';h[4:6]=bytes((1,1));struct.pack_into('<H',h,6,512)
    h[8:24]=bytes.fromhex(profile['compatibility_id'])
    for p,v in ((24,15),(26,1024),(28,124)):struct.pack_into('<H',h,p,v)
    payload=b''
    for i,n in enumerate(NAMES):
        data=images[n+'.RSX'];assert len(data)==1024
        struct.pack_into('<BBHHH',h,34+8*i,i,0 if i<5 or i==12 else 1,4+8*i,1024,binascii.crc_hqx(data,0xffff));payload+=data
    struct.pack_into('<H',h,32,binascii.crc_hqx(h,0xffff))
    return bytes(h)+payload

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('profile',choices=PROFILES)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--prepare-only',action='store_true')
    args=p.parse_args();out=args.output.resolve()
    if out.exists():p.error('output must be new; no cached cross-profile products are admitted')
    if args.profile=='model4-legacy' and not args.prepare_only:p.error('Model 4 build/qualification is outside this cpmsim prototype; use --prepare-only')
    paths=subprocess.check_output(['git','ls-files','-co','--exclude-standard','-z'],cwd=ROOT).decode().split('\0')
    paths=sorted(set(x for x in paths if x and x.split('/')[0] in ('src','tools','metadata','third_party','docs')))
    for rel in paths:
        src=ROOT/rel
        if not src.is_file() or '__pycache__' in src.parts:continue
        dst=out/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
    delta,checked=PROFILES[args.profile]
    layout=(out/'src/system/layout.inc').read_text()
    def moved(m):
        n,v=m[1],int(m[2],16)
        if n=='LY_TOPRSV':v=0xC00-delta
        elif v>=0xC000:v+=delta
        return f'{n:<16}EQU     0{v:04X}H'
    layout=re.sub(r'^(LY_\w+)\s+EQU\s+0([0-9A-F]+)H',moved,layout,flags=re.M)
    (out/'src/system/layout.inc').write_text(layout)
    private_paths=list((ROOT/'src').rglob('*'))+list((ROOT/'tools').glob('build_*.py'))+[ROOT/'tools'/n for n in ('assessment_checked_profiles.py','assessment_fullram_cpmsim.py','system_layout.py','rsx_container.py')]
    inputs={str(x.relative_to(ROOT)):hashlib.sha256(x.read_bytes()).hexdigest() for x in sorted(private_paths) if x.is_file() and '__pycache__' not in x.parts}
    contract={'schema':1,'private_epoch':1,'profile':args.profile,'layout_sha256':hashlib.sha256(layout.encode()).hexdigest(),'private_inputs':inputs,'checked':checked,'scratch_bytes':4096 if checked else 3840}
    identity=hashlib.sha256(json.dumps(contract,sort_keys=True,separators=(',',':')).encode()).hexdigest()[:32]
    profile={'contract':contract,'compatibility_id':identity,'source_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),'status':'assessment prototype; not release qualified'}
    (out/'assessment-profile.json').write_text(json.dumps(profile,indent=2)+'\n')
    if args.prepare_only:print(out);return
    logs=out/'assessment-build-logs';logs.mkdir(exist_ok=True)
    def run(name,argv):
        with (logs/(name+'.log')).open('wb') as f:r=subprocess.run(argv,cwd=out,stdout=f,stderr=subprocess.STDOUT)
        if r.returncode:raise SystemExit((logs/(name+'.log')).read_text(errors='replace')[-6000:])
        print(name+' PASS',flush=True)
    run('base',[sys.executable,str(out/'tools/assessment_fullram_cpmsim.py')])
    if checked:
        (out/'assessment-media').rename(out/'unchecked-control-media')
        apply_checked(out,identity)
        shutil.rmtree(out/'build/z80pack')
        run('checked',[sys.executable,str(out/'tools/build_z80pack_image.py'),'--system-tracks-only','--ram-only'])
        sys.path.insert(0,str(out/'tools'))
        from build_distribution import geometry,selected_files,construct,capacity,validate_config_fingerprint,validate_config_cold_patch,validate_files
        manifest=json.loads((out/'metadata/distribution.json').read_text())
        files,omitted=selected_files(manifest,'z80pack',out);g=geometry('z80pack',out)
        media=out/'assessment-media';media.mkdir()
        raw=construct('z80pack',out,media,files,g,manifest['cold_start_command'])
        validate_config_fingerprint('z80pack',raw,files,out);validate_config_cold_patch('z80pack',raw,files,out);validate_files(raw,media,files,g)
    print('PROTOTYPE MEDIA: '+str(out/'assessment-media/system.raw'),flush=True)

if __name__=='__main__':main()
