"""Private, OFF=3 native-reference media; called with the integration build live.

No default system layout, production utility, or public TCAP ABI is changed.
"""
import binascii
import hashlib
import json
import struct
from pathlib import Path
import campaign as base
import manager_integration as manager
import placement as placed
from rsx_container import NAMES

ROOT=base.ROOT

def build_package(assembler,stage,images,root,artifacts,matched,slots,backends,identity,reloadlabels):
    import build_trs80_boot as media
    import system_layout as layout
    import build_ccp
    from startup_record import build as startup
    from build_montezuma_extended_790k import build as dmk,RAW_SIZE
    from shared_ui import expand_sysgen_ui
    out=manager.OUT/'native-package';out.mkdir(exist_ok=True)
    (out/'qualification.json').unlink(missing_ok=True)
    def emit(name,text,origin):
        (out/(name+'.mac')).write_text(text)
        return base.assemble(assembler,text,out/(name+'.bin'),out/(name+'.lst'),origin)
    resident=(stage/'build/system/resident.bin').read_bytes()
    assert len(resident)==7612
    padded=resident.ljust(15*512,b'\0')
    crc=binascii.crc_hqx(padded,65535)
    # The ROM-loaded boot sector is the trust root. It verifies all of stage one
    # (including the resident CRC pin); stage one verifies the full resident load.
    # Keep the startup record at boot-sector bytes 128..383 intact. The shared
    # checksum routine is in the otherwise unused final 128 bytes of that sector.
    stage1=(ROOT/'src/platform/trs80m4/stage1.mac').read_text()
    stage1=stage1.replace('        JP      SYSBOOT',f'''        LD HL,SYSIMAGE
        LD BC,7680
        LD DE,{crc}
        CALL 04492H
        JP NZ,SYSERROR
        JP SYSBOOT''')
    platform=ROOT/'src/platform/trs80m4'
    def platform_source(text):
        for name in ('hardware.inc','m4disk.inc','hal.inc','m4cons.inc'):
            text=text.replace('        INCLUDE '+name,(platform/name).read_text())
        return base.normalized(text)
    s1=emit('stage1',platform_source(stage1),0x5000)
    assert len(s1)<=512,('stage1 overflow',len(s1))
    boot=(platform/'boot.mac').read_text().replace('        JP      STAGE1BASE','        JP BC_VERIFY',1)
    # Tail has an 18-byte verification entry followed by the reusable CRC16.
    tail=f'''        DS 04480H-$,0
BC_VERIFY:
        LD HL,05000H
        LD BC,512
        LD DE,{binascii.crc_hqx(s1.ljust(512,bytes(1)),65535)}
        CALL BC_CRC
        JP NZ,BOOTERROR
        JP 05000H
BC_CRC:
        PUSH DE
        LD DE,0FFFFH
BC_BYTE:
        LD A,(HL)
        XOR D
        LD D,A
        INC HL
        PUSH BC
        LD B,8
BC_BIT:
        SLA E
        RL D
        JR NC,BC_NEXT
        LD A,D
        XOR 010H
        LD D,A
        LD A,E
        XOR 021H
        LD E,A
BC_NEXT:
        DJNZ BC_BIT
        POP BC
        DEC BC
        LD A,B
        OR C
        JR NZ,BC_BYTE
        POP HL
        OR A
        SBC HL,DE
        RET
'''
    message=boot[boot.index('ERRORMSG:'):boot.index('        .DEPHASE')]
    boot=boot.replace(message,'')
    boot=boot.replace('        .DEPHASE',tail+'\n'+message+'\n        .DEPHASE')
    b0=emit('boot',platform_source(boot),0x4300)
    bootlabels=base.symbols(out/'boot.lst')
    assert bootlabels['BC_CRC']==0x4492,(hex(bootlabels['BC_CRC']))
    assert len(b0)<=512 and not any(b0[128:384]),'boot overlaps startup record'
    # Form the linked/relocatable command carrier from the exact gated payload.
    text=(manager.OUT/'ccp.mac').read_text()
    alternatives=[]
    for origin in (0xbc01,0xbd37):
        data=emit('ccp-'+hex(origin),text.replace('0BB00H',f'0{origin:04X}H'),origin)
        alternatives.append((data,origin))
    repairs=build_ccp.relocation_offsets(artifacts['ccp'],alternatives)
    header=bytearray(1024)
    struct.pack_into('<4sBBHHHHH',header,0,b'BCM1',1,2,0xbb00,len(artifacts['ccp']),5632,0,len(repairs))
    for i,at in enumerate(repairs):struct.pack_into('<H',header,16+2*i,at)
    command=bytes(header)+artifacts['ccp']
    assert len(command)<=13*512
    payload=bytearray(60*512)
    def put(sector,data,capacity):
        assert 0<len(data)<=capacity
        payload[sector*512:sector*512+capacity]=data.ljust(capacity,b'\0')
    put(0,b0,512);put(1,s1,512);put(2,resident,15*512)
    # No obsolete transient-selector tail: selector is in the sealed resident.
    put(17,artifacts['model4-reloader'],1024)
    put(19,(stage/'build/system/config.bin').read_bytes(),1024)
    for sector,name in ((21,'entry'),(23,'R3CARR'),(25,'R3MOVE'),(27,'R3RESOL')):
        put(sector,artifacts[name],1024)
    put(29,command,13*512)
    payload[128:384]=startup('',system_base=base.L['SYSTEM'])
    # Private magic prevents ordinary OFF=2 SYSGEN/SYSBUILD accepting this layout.
    signature=b'BDCF'+bytes((5,4,4,64));at=resident.index(signature)
    logical=struct.unpack_from('<H',resident,at+10)[0]
    bind=logical-base.L['SYSTEM']+16
    assert 0<=bind<=len(resident)-64
    package_header=bytearray(128);package_header[:8]=b'XTNP'+bytes((1,1,240,0))
    struct.pack_into('<H',package_header,8,base.L['SYSTEM'])
    package_header[16:80]=resident[bind:bind+64]
    package=bytes(package_header)+payload
    (out/'SYSTEM.SYS').write_bytes(package)
    (out/'system-tracks.bin').write_bytes(payload)
    # Build the existing installer with private layout constants and package magic.
    # No TCAP-facing utility migration occurs. Installation still validates media,
    # reserves, writes, and reads back every record through the ordinary BIOS.
    installer=(ROOT/'src/utilities/sysgen.mac').read_text()
    for name in ('sysgen-parse.inc','sysgen-export.inc'):
        installer=installer.replace('        INCLUDE '+name,(ROOT/'src/utilities'/name).read_text())
    installer=installer.replace('SYSRECS EQU 160','SYSRECS EQU 240').replace('52*128','60*128')
    installer=installer.replace("'BCSY',1,1,160,0","'XTNP',1,1,240,0")
    installer=installer.replace('160 records required','240 records required')
    installer=installer.replace('; @monitor-console@',(ROOT/'src/utilities/common/monitorconsole.inc').read_text())
    installer=expand_sysgen_ui(installer)
    installer=installer.replace('        JP WRIMAGE', '        CALL PK_VERIFY\n        JP NZ,PKGBAD\n        JP WRIMAGE',1)
    # Reject damaged or differently patched private system tracks before writing.
    # This is corruption detection, not authentication against hostile media.
    checksum=tail[tail.index('BC_CRC:'):].replace('BC_','PK_')
    verify=f'PK_VERIFY:\n        LD HL,IMAGE\n        LD BC,30720\n        LD DE,{binascii.crc_hqx(payload,65535)}\n        JP PK_CRC\n'
    installer=installer.replace('; @checked-package-guard@',verify+checksum)
    inst=emit('install',installer,0x100)
    assert len(inst)<0x2f00
    # Use the existing RSX command interface, rebuilt against this private layout.
    rsx=(ROOT/'src/utilities/rsx.mac').read_text().replace('        INCLUDE rsxvers.inc',(ROOT/'src/utilities/rsxvers.inc').read_text())
    utility=b'\xc3\x03\x01'+emit('rsx',base.normalized(rsx),0x103)
    files=[('INSTALL.COM',inst),('SYSTEM.SYS',package),('RSX.COM',utility),
           ('R3PACK.RSX',(stage/'build/system/R3PACK.RSX').read_bytes()),
           ('R3CACHE.RSX',artifacts['cache'])]
    actual_backends=placed.placed_backends(assembler,images,backends)
    code,labels,relocs,entry=actual_backends['M4SCRN']
    files.append(('M4SCRN.RSX',base.make_module(name='M4SCRN',version=(1,1),services=[],linked_base=0x8000,code=code,relocations=relocs,reconstruction_class='STATEFUL',callable_services=[(b'SCRN',1,1,labels[entry]-0x8000,1)])))
    files.append(('XTCAP.RSX',base.make_module(name='XTCAP',version=(0,5),services=[],linked_base=0x8000,code=matched[0],relocations=slots,reconstruction_class='STATEFUL',callable_services=[(b'MCON',1,3,matched[1]['AN_ENTRY']-0x8000,4),(b'XTCP',0,4,matched[1]['TX_ENTRY']-0x8000,0)])))
    for name,entry in (('ADM3A','AM_ENTRY'),('ANSI','AN_ENTRY')):
        source=base.normalized((ROOT/f'src/rsx/{name.lower()}.mac').read_text())
        for inc in ('ansi-dispatch.inc','screen/rendition.inc'):
            source=source.replace('        INCLUDE '+inc,(ROOT/'src/rsx'/inc).read_text())
        code=emit(name.lower(),source,0x8000);labels=base.symbols(out/(name.lower()+'.lst'))
        alt=emit(name.lower()+'-alt',source.replace('08000H','08101H'),0x8101)
        relocs=base.relocation_offsets(code,alt,0x101)
        files.append((name+'.RSX',base.make_module(name=name,version=(0,1),services=[],linked_base=0x8000,code=code,relocations=relocs,reconstruction_class='STATEFUL',callable_services=[(b'MCON',1,1 if name=='ADM3A' else 2,labels[entry]-0x8000,4)])))
    # Small protocol fixtures are applications configured for one personality;
    # they use only normal console BDOS calls and return through real WBOOT.
    for name,control in (('ADMAPP',bytes((27,61,36,41))),('ANSIAPP',b'\x1b[5;10H')):
        message=name.encode()+b' NORMAL CONSOLE PASS'
        text="""        ASEG
        ORG 0100H
        LD HL,STREAM
        LD B,STREAM_END-STREAM
APP_NEXT:
        LD E,(HL)
        PUSH HL
        PUSH BC
        LD C,2
        CALL 5
        POP BC
        POP HL
        INC HL
        DJNZ APP_NEXT
        JP 0
STREAM: DB """+','.join(map(str,control+message))+"\nSTREAM_END:\n        END\n"
        files.append((name+'.COM',emit(name.lower(),text,0x100)))
    # These private probes deliberately bind the private reference entry offset.
    # They do not claim discovery or implement the proposed public request ABI.
    for name,operations in (('TCHECK',(7,)),('TSCOPE',(2,4)),('TBEGIN',(2,))):
        text=f"""        ASEG
        ORG 0100H
"""
        for op in operations:
            text+=f"""        LD HL,({images['bios'][1]['MP_MON']})
        LD DE,{matched[1]['TX_ENTRY']-matched[1]['AN_ENTRY']}
        ADD HL,DE
        LD DE,TOKEN
        LD A,{op}
        CALL INVOKE
        OR A
        JP NZ,FAIL
"""
        # TBEGIN must not emit ordinary output after Begin: go straight to WBOOT.
        if name=='TBEGIN':text+='        JP 0\n'
        else:
            text+=f"""        LD HL,({root['VG_NEXT']})
        DEC HL
        LD A,H
        OR L
        JR NZ,FAIL
        LD DE,OK
        JR PRINT
"""
        text+="""FAIL: LD DE,BAD
PRINT: LD C,9
        CALL 5
        JP 0
INVOKE: JP (HL)
TOKEN: DS 16,0
"""+f"OK: DB '{name} PASS',13,10,'$'\nBAD: DB '{name} FAIL',13,10,'$'\n        END\n"
        files.append((name+'.COM',emit(name.lower(),text,0x100)))
    import test_sysgen_install as install_test
    old_out=install_test.OUT
    try:
        install_test.OUT=out
        files.append(('SETBSYS.COM',install_test.setup_program()))
    finally:install_test.OUT=old_out
    for name,data in files:(out/name).write_bytes(data)
    raw=bytearray(b'\xe5'*RAW_SIZE);raw[:len(payload)]=payload
    media.install_files(raw,files,directory=60*512,block_count=385)
    (out/'reference.raw').write_bytes(raw)
    (out/'reference.dmk').write_bytes(dmk(bytes(raw)))
    result={'status':'BUILT; full-machine qualification is a separate command','identity':identity.hex(),'system_records':240,'boot_volume_off':3,
            'resident_bytes':len(resident),'stage1_bytes':len(s1),'boot_bytes':len(b0),
            'files':{name:hashlib.sha256(data).hexdigest() for name,data in files},
            'package_sha256':hashlib.sha256(package).hexdigest(),
            'raw_sha256':hashlib.sha256(raw).hexdigest(),
            'scope':'private Model 4 native reference; utility migrations and release assignment deferred'}
    (out/'package-manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print('BUILT native-reference package',out,flush=True)
    return result
