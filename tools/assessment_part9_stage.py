#!/usr/bin/env python3
"""Build the Part 9 second-stage experiment against a pinned Part 8 resident.

Produces private probe artifacts only; no production image builder is changed.
"""
from pathlib import Path
import argparse,binascii,json,struct,sys
from assessment_part9_compact import compact
ROOT=Path(__file__).resolve().parents[1]

def carrier(old,identity):
    # Keep the Part 8 candidate format numbers; schema 2 adds whole-carrier CRC.
    b=bytearray(old)
    if b[:4]==b'BCPX':
        assert b[4]==1;b[4]=2;public=b[32:40].decode().strip()=='HELLO'
    else:
        assert b[:6]==b'BCM1\1\2';b[:5]=b'BCM2\2';public=False
    b+=b'BP'+bytes((2,0 if public else 1))+(bytes(16) if public else bytes.fromhex(identity))
    b+=struct.pack('<H',binascii.crc_hqx(b,0xffff))
    return bytes(b)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('baseline',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    root=a.baseline.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    sys.path.insert(0,str(root/'tools'))
    from build_ccp import assemble
    from build_z80pack_rom_boot import z80pack_reloader_source,normalized
    from build_z80pack_image import symbols
    from system_layout import LAYOUT as L
    identity=json.loads((root/'assessment-profile.json').read_text())['compatibility_id']
    source=compact(normalized(z80pack_reloader_source((root/'src/platform/trs80m4/ccprelod.mac').read_text())))
    source=source.replace('RELOADBASE      EQU     LY_LOAD','RELOADBASE      EQU     00500H').replace('CRSTKTOP        EQU     LY_STKT','CRSTKTOP        EQU     01000H')
    first=source.index('CRLOAD:');last=source.index('CRENTRY:',first)
    source=source[:first]+(ROOT/'src/system/part9-stage-load.inc').read_text()+'\n'+source[last:]
    first=source.index('CRRESET:');last=source.index('CRFAIL:',first)
    source=source[:first]+source[last:]
    source=source.replace('        LD      (CRSLOT),A\n        LD      HL,CRCCPMAG','        LD      A,108\n        LD      (CRSLOT),A\n        LD      HL,CRCCPMAG')
    source=source.replace("'B','C','M','1',1,2","'B','C','M','2',2,2").replace("'B','C','P','X',1,1","'B','C','P','X',2,1")
    source=source.replace('        JR      CRFAIL',"        LD A,'!'\n        OUT (1),A\n        HALT\n        JR CRFAIL")
    (out/'stage2.mac').write_text(source)
    stage=assemble(Path.home()/'bin/z80asm',source,out/'stage2.bin',out/'stage2.lst',0x500)
    assert len(stage)<=2024,('second-stage overflow',len(stage))
    stagecarrier=stage.ljust(2024,b'\0')+bytes.fromhex(identity)+bytes(8)
    (out/'stage2.carrier').write_bytes(stagecarrier)
    bootstrap=(ROOT/'src/system/part9-stage1.mac').read_text().replace('P9_EXPECT: LD DE,0',f'P9_EXPECT: LD DE,{binascii.crc_hqx(stagecarrier,0xffff)}')
    (out/'stage1.mac').write_text(bootstrap)
    first=assemble(Path.home()/'bin/z80asm',bootstrap,out/'stage1.bin',out/'stage1.lst',0x100)
    assert len(first)<=932
    firstcarrier=first.ljust(1000,b'\0')+bytes.fromhex(identity)+bytes(8)
    (out/'stage1.carrier').write_bytes(firstcarrier)
    rows=[]
    for rel in ('build/ccp/ccp.rlm','build/cpx/RCP.CPX','build/cpx/HELLO.CPX'):
        old=(root/rel).read_bytes();new=carrier(old,identity);(out/Path(rel).name).write_bytes(new)
        allocation=int.from_bytes(old[14:16] if old[:4]==b'BCPX' else old[10:12],'little')
        rows.append({'name':Path(rel).name,'old_bytes':len(old),'new_bytes':len(new),'records':(len(new)+127)//128,'staging_record_bytes':(len(new)+127)//128*128,'allocation':allocation,'required_upper_boundary':4096+(len(new)+127)//128*128+allocation})
    report={'baseline':str(root),'resident_contract_id':identity,'stage1_bytes':len(first),'stage2_bytes':len(stage),'stage2_carrier_bytes':len(stagecarrier),'stage1_origin':256,'stage2_origin':1280,'stack_top':4096,'stack_reserved_low':3328,'carrier_origin':4096,'stage2_raw_records':[84,99],'carriers':rows,'scope':'private probe images bound to the Part 8 resident; not a newly qualified profile or production package'}
    (out/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

if __name__=='__main__':main()
