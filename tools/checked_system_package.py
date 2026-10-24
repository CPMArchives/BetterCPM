"""Checked cpmsim package v2 and its build-owned installer admission gate.

Integrity/binding, not authentication. Normalized editable fields stay owned by
CONFIG/SYSGEN; every other byte of the 160-record payload is build-bound.
"""
from pathlib import Path
import argparse,binascii,hashlib,json,struct
SIZE=160*128

def crc(data):return binascii.crc_hqx(data,0xffff)
def normalize(payload,masks):
    b=bytearray(payload)
    if len(b)!=SIZE:raise ValueError('payload length')
    for start,n in masks:
        if not 0<=start<=len(b)-n:raise ValueError('mask outside payload')
        b[start:start+n]=bytes(n)
    return bytes(b)

def make(payload,contract):
    if crc(normalize(payload,contract['masks']))!=contract['normalized_crc']:raise ValueError('mixed/corrupt system payload')
    h=bytearray(128);h[:10]=b'BCSY\2\2'+struct.pack('<HH',160,contract['system_base'])
    pos=contract['a_binding_offset'];h[16:80]=payload[pos:pos+64]
    h[80:96]=bytes.fromhex(contract['compatibility_id']);struct.pack_into('<H',h,96,crc(payload))
    struct.pack_into('<H',h,126,crc(h[:126]));return bytes(h)+payload

def validate(package,contract):
    if len(package)!=SIZE+128:raise ValueError('package length')
    h,p=package[:128],package[128:]
    if h[:10]!=b'BCSY\2\2'+struct.pack('<HH',160,contract['system_base']):raise ValueError('package format/profile')
    if h[80:96]!=bytes.fromhex(contract['compatibility_id']):raise ValueError('package identity')
    if crc(h[:126])!=int.from_bytes(h[126:128],'little'):raise ValueError('header CRC')
    if crc(p)!=int.from_bytes(h[96:98],'little'):raise ValueError('payload CRC')
    if crc(normalize(p,contract['masks']))!=contract['normalized_crc']:raise ValueError('mixed/corrupt system payload')
    if h[16:80]!=p[contract['a_binding_offset']:contract['a_binding_offset']+64]:raise ValueError('header binding mismatch')
    return True

def raw_payload(root,path):
    from fdf_format import select_fdf
    from build_z80pack_image import DEFAULT_FORMAT
    f=select_fdf(root/'third_party/montezuma/DISK.FDF',DEFAULT_FORMAT);b=path.read_bytes();p=bytearray()
    for rec in range(160):
        track,within=divmod(rec,f.spt);at=track*f.raw_track_bytes+f.raw_record_map()[within]*128;p+=b[at:at+128]
    return bytes(p)

def prepare(root,out,payload,symbols):
    from system_layout import LAYOUT as L
    from checked_carriers import selected_contract
    profile=selected_contract()
    if not profile:raise ValueError('checked package requires a prepared profile')
    resident=payload[1024:7680];at=resident.index(b'BDCF'+bytes((5,4,4,64)))
    physical,logical=struct.unpack_from('<HH',resident,at+8)
    masks=[(128,256),(1024+physical-L['SYSTEM'],24)]+[(1024+logical-L['SYSTEM']+i*80+16,64) for i in range(4)]+[(1024+symbols['IO_COLD']+1-L['SYSTEM'],1)]
    cid=1024+L['BIOS']-16-L['SYSTEM']
    assert payload[cid:cid+16]==bytes.fromhex(profile['compatibility_id'])
    contract={'schema':2,'profile':profile['contract']['profile'],'compatibility_id':profile['compatibility_id'],'system_base':L['SYSTEM'],'masks':masks,'normalized_crc':crc(normalize(payload,masks)),'a_binding_offset':1024+logical-L['SYSTEM']+16,'resident_id_offset':cid,'required_files':{}}
    for name,rel in [('RCP.CPX','build/cpx/RCP.CPX'),('R3PACK.RSX','build/system/R3PACK.RSX')]:
        b=(root/rel).read_bytes();contract['required_files'][name]={'bytes':len(b),'crc16':crc(b)}
    (out/'checked-package.json').write_text(json.dumps(contract,indent=2)+'\n')
    (out/'package-guard.inc').write_text(assembly(contract))
    state={'build_contract':profile,'payload_sha256':hashlib.sha256(payload).hexdigest(),
           'contract_sha256':hashlib.sha256((out/'checked-package.json').read_bytes()).hexdigest(),
           'guard_sha256':hashlib.sha256((out/'package-guard.inc').read_bytes()).hexdigest()}
    (out/'package-inputs.json').write_text(json.dumps(state,indent=2)+'\n')

def guard_source(root):
    from checked_carriers import selected_contract
    contract=selected_contract()
    if not contract:raise ValueError('checked package guard requires a prepared profile')
    out=root/'build/z80pack'
    state=json.loads((out/'package-inputs.json').read_text())
    if state['build_contract']!=contract:raise ValueError('foreign/stale package guard')
    for name,key in [('checked-package.json','contract_sha256'),('package-guard.inc','guard_sha256')]:
        if hashlib.sha256((out/name).read_bytes()).hexdigest()!=state[key]:
            raise ValueError('changed package guard input: '+name)
    return (out/'package-guard.inc').read_text()

def assembly(c):
    ident=','.join(str(x) for x in bytes.fromhex(c['compatibility_id']))
    text=f'''P11HCHK:
        LD HL,PKGHEADER+80
        LD DE,P11ID
        LD B,16
        CALL XCMP
        RET NZ
        LD DE,PKGHEADER
        LD BC,126
        CALL P11CRC
        LD DE,(PKGHEADER+126)
        OR A
        SBC HL,DE
        RET
P11FCRC:
        LD DE,IMAGE
        LD BC,20480
        CALL P11CRC
        LD DE,(PKGHEADER+96)
        OR A
        SBC HL,DE
        RET NZ
        LD HL,PKGHEADER+16
        LD DE,IMAGE+{c['a_binding_offset']}
        LD B,64
        JP XCMP
P11HEAD:
        LD HL,P11ID
        LD DE,PKGHEADER+80
        LD BC,16
        LDIR
        LD DE,IMAGE
        LD BC,20480
        CALL P11CRC
        LD (PKGHEADER+96),HL
        LD DE,PKGHEADER
        LD BC,126
        CALL P11CRC
        LD (PKGHEADER+126),HL
        RET
P11CHECK:
        LD HL,LY_CID
        LD DE,P11ID
        LD B,16
        CALL XCMP
        RET NZ
        LD HL,IMAGE+{c['resident_id_offset']}
        LD DE,P11ID
        LD B,16
        CALL XCMP
        RET NZ
'''
    scratch=0x3200
    for i,(off,n) in enumerate(c['masks']):
        text+=f'''        LD HL,IMAGE+{off}
        LD DE,{scratch}
        LD BC,{n}
        LDIR
        LD HL,IMAGE+{off}
        LD BC,{n}
        CALL P11ZERO
''';scratch+=n
    assert scratch<0x3E00
    text+='''        LD DE,IMAGE
        LD BC,20480
        CALL P11CRC
        PUSH HL
'''
    scratch=0x3200
    for off,n in c['masks']:
        text+=f'        LD HL,{scratch}\n        LD DE,IMAGE+{off}\n        LD BC,{n}\n        LDIR\n';scratch+=n
    text+=f'''        POP HL
        LD DE,{c['normalized_crc']}
        OR A
        SBC HL,DE
        RET
P11ZERO:
        LD (HL),0
        INC HL
        DEC BC
        LD A,B
        OR C
        JR NZ,P11ZERO
        RET
P11CRC: LD HL,65535
P11UPD: LD A,(DE)
        XOR H
        LD H,A
        PUSH BC
        LD B,8
P11BIT: ADD HL,HL
        JR NC,P11BNXT
        LD A,H
        XOR 16
        LD H,A
        LD A,L
        XOR 33
        LD L,A
P11BNXT:DJNZ P11BIT
        POP BC
        INC DE
        DEC BC
        LD A,B
        OR C
        JR NZ,P11UPD
        RET
P11FILES:
        LD E,255
        LD C,32
        CALL BDOS
        LD (P11USER),A
        LD E,0
        LD C,32
        CALL BDOS
        CALL P11FSUB
        PUSH AF
        LD A,(P11USER)
        LD E,A
        LD C,32
        CALL BDOS
        POP AF
        RET
P11FSUB:
'''
    for i,(name,item) in enumerate(c['required_files'].items()):
        text+=f"        LD HL,P11NAME{i}\n        LD DE,{item['bytes']}\n        LD BC,{item['crc16']}\n        CALL P11FILE\n        RET NZ\n"
    text+='''        XOR A
        RET
P11FILE:
        LD (P11LEFT),DE
        LD (P11EXP),BC
        LD DE,P11FCB+1
        LD BC,11
        LDIR
        LD HL,P11FCB+12
        LD B,24
        XOR A
P11CLR: LD (HL),A
        INC HL
        DJNZ P11CLR
        LD A,(DEST)
        INC A
        LD (P11FCB),A
        LD DE,P11FCB
        LD C,15
        CALL BDOS
        INC A
        JP Z,XBAD
        LD HL,65535
        LD (P11SUM),HL
P11READ:
        LD DE,BUFFER
        LD C,26
        CALL BDOS
        LD DE,P11FCB
        LD C,20
        CALL BDOS
        OR A
        JR NZ,P11CLOS
        LD HL,(P11LEFT)
        LD DE,128
        OR A
        SBC HL,DE
        JR NC,P11FULL
        LD BC,(P11LEFT)
        LD HL,0
        JR P11CHNK
P11FULL:LD BC,128
P11CHNK:LD (P11LEFT),HL
        LD HL,(P11SUM)
        LD DE,BUFFER
        CALL P11UPD
        LD (P11SUM),HL
        LD HL,(P11LEFT)
        LD A,H
        OR L
        JR NZ,P11READ
        LD DE,P11FCB
        LD C,20
        CALL BDOS
        CP 1
        JR NZ,P11CLOS
        LD DE,P11FCB
        LD C,16
        CALL BDOS
        INC A
        JP Z,XBAD
        LD HL,(P11SUM)
        LD DE,(P11EXP)
        OR A
        SBC HL,DE
        RET
P11CLOS:
        LD DE,P11FCB
        LD C,16
        CALL BDOS
        JP XBAD
P11FBAD:LD HL,P11MSG
        JP REPORT
P11MSG: DB 'Matching RCP.CPX and R3PACK.RSX required on destination.',13,10,0
P11USER:DB 0
P11FCB: DS 36
P11LEFT:DW 0
P11EXP: DW 0
P11SUM: DW 0
'''
    for i,name in enumerate(c['required_files']):
        stem,ext=name.split('.');text+=f"P11NAME{i}: DB '{stem:<8}{ext:<3}'\n"
    text+='P11ID: DB '+ident+'\n';return text

def main():
    from build_checked_package import main as build
    build()

if __name__=='__main__':main()
