#!/usr/bin/env python3
"""Part 8 bounded RSX migration and candidate CCP/CPX binding experiments."""
from __future__ import annotations
import json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PUBLIC_RSX={'HELLO','ECHO'}
EXCLUDED_RSX={'M4SCRN','FREHDCLK'}
# Conservative private admission for known in-tree modules; no unknown import.
PRIVATE_RSX={'STATEFUL','TEST','ANSISCRN','ADM3A','VT52','ANSI','BATCHIO','FDF','P2DOS','ZPRTC','T104Z8','T104C3'}

def binding(name,identity,kind='rsx'):
    public=name in (PUBLIC_RSX if kind=='rsx' else {'HELLO'})
    if kind=='rsx' and name not in PUBLIC_RSX|PRIVATE_RSX:raise ValueError('unreviewed RSX '+name)
    return bytes((1,0 if public else 1))+(bytes(16) if public else bytes.fromhex(identity))

def migrate_rsx(data,identity):
    assert data[:5]==b'BRSX\x02'
    b=bytearray(data);name=b[32:40].decode().strip();off=struct.unpack_from('<H',b,30)[0]
    assert b[off:off+7]==b'BMET\x01\x00\x0c'
    length=struct.unpack_from('<H',b,off+8)[0];assert off+length==len(b) and length+20<512
    b[4]=3;b[off+4]=2;b[off+7]+=1;struct.pack_into('<H',b,off+8,length+20)
    b[off+12:off+12]=bytes((4,18))+binding(name,identity)
    return bytes(b)

def bind_generated(data):
    return migrate_rsx(data,json.loads((ROOT/'assessment-profile.json').read_text())['compatibility_id'])

def finish(root):
    ident=json.loads((root/'assessment-profile.json').read_text())['compatibility_id'];changes=[]
    for p in sorted((root/'build/rsx').glob('*.RSX')):
        old=p.read_bytes()
        if p.stem in EXCLUDED_RSX:
            changes.append({'name':p.name,'status':'not migrated; unsupported cpmsim hardware'})
            continue
        if old[:5]==b'BRSX\x02':new=migrate_rsx(old,ident);p.write_bytes(new)
        else:assert old[:5]==b'BRSX\x03';new=old
        changes.append({'name':p.name,'bytes':len(new),'allocation':int.from_bytes(new[14:16],'little'),'binding_class':0 if p.stem in PUBLIC_RSX else 1})
    (root/'assessment-build-logs/rsx-migration.json').write_text(json.dumps(changes,indent=2)+'\n')

def apply(root):
    from assessment_checked_profiles import replace
    def read(p):return (root/p).read_text()
    def write(p,s):(root/p).write_text(s)
    p='tools/build_rsx_module.py';s=read(p)
    s=replace(s,'    return bytes(header) + code + metadata','    from assessment_carrier_binding import bind_generated\n    return bind_generated(bytes(header) + code + metadata)');write(p,s)
    p='src/system/r3carr.mac';s='        INCLUDE layout.inc\n'+read(p)
    s=replace(s,'        CP      2\n        JP      NZ,RX_BAD\n        LD      (RX_FMT),A','        CP      3\n        JP      NZ,RX_BAD\n        DEC     A                       ; internal normalized facts retain format 2\n        LD      (RX_FMT),A')
    s=replace(s,'RX_SIZEOK:\n','RX_SIZEOK:\n        CALL    RX_BIND\n        JP      NZ,RX_BAD\n')
    gate='''; Binding record must fit completely before any facts are published.
RX_BIND:
        LD HL,(RX_METAOFF)
        LD DE,32
        ADD HL,DE
        JP C,RX_BAD
        LD DE,(RX_LENGTH)
        OR A
        SBC HL,DE
        JR C,RX_BFIT
        JP NZ,RX_BAD
RX_BFIT:
        LD HL,(RX_CARRIER)
        LD DE,(RX_METAOFF)
        ADD HL,DE
        JP C,RX_BAD
        LD DE,12
        ADD HL,DE
        JP C,RX_BAD
        LD A,(HL)
        CP 4
        RET NZ
        INC HL
        LD A,(HL)
        CP 18
        RET NZ
        INC HL
        JP PB_CHECK
'''
    s=replace(s,'RX_MAG:      DB',gate+read('src/system/part8-binding.inc')+'\nRX_MAG:      DB');write(p,s)
    p='src/system/r3meta.mac';s=read(p)
    s=replace(s,'        CP      1\n        JP      NZ,RXM_BAD\n        INC     HL','        CP      2\n        JP      NZ,RXM_BAD\n        INC     HL')
    s=replace(s,'        LD      A,(HL)\n        LD      (RXM_NREC),A','        LD      A,(HL)\n        OR      A\n        JP      Z,RXM_BAD\n        DEC     A                       ; mandatory first binding was checked by R3CARR\n        LD      (RXM_NREC),A')
    s=replace(s,'        CP      12\n        JP      C,RXM_BAD','        CP      32\n        JP      C,RXM_BAD')
    s=replace(s,'        INC     HL\n        LD      (RXM_RECPTR),HL','        INC     HL\n        LD      DE,20\n        ADD     HL,DE\n        LD      (RXM_RECPTR),HL')
    write(p,s)
    for p,old,new in [
     ('src/system/r3coord.mac','        CP      2\n        JP      NZ,RC_BAD\n        LD      (RC_FMT),A','        CP      3\n        JP      NZ,RC_BAD\n        LD      (RC_FMT),A'),
     ('src/system/r3keep.mac','        CP      2\n        JP      NZ,KE_BAD','        CP      3\n        JP      NZ,KE_BAD'),
     ('src/system/r3prof.mac','        CP      2\n        JP      NZ,PF_BAD\n\nPF_ABI','        CP      3\n        JP      NZ,PF_BAD\n\nPF_ABI'),
     ('src/system/r3drop.mac','        CP      2\n        JP      NZ,RD_BAD\nRD_ABI','        CP      3\n        JP      NZ,RD_BAD\nRD_ABI')]:write(p,replace(read(p),old,new))
