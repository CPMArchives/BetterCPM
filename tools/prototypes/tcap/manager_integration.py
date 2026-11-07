#!/usr/bin/env python3
"""Private manager construction and loading integration; no utility migrations."""
import argparse
import binascii
import hashlib
import json
import re
import struct
import subprocess
import shutil
import sys
from pathlib import Path
import matching_validity as previous
import campaign as base
import placement as placed
import system_paths as paths
import system_layout as layout
from rsx_container import NAMES

ROOT=base.ROOT
OUT=ROOT/'build/tcap-manager-integration'
ROLES=('bios','ccp','model4-reloader','stage2','entry','cache','reader')+NAMES
REQUIRED=((1<<len(ROLES))-1) ^ (1<<3)  # native reference: stage 2 is not executable


def choose_reference(text):
    """Resolve only the explicit reference-build conditionals before relaxation."""
    frames=[];active=True;result=[]
    for line in text.splitlines():
        match=re.fullmatch(r'\s*IF\s+(0|BP_CHECKED EQ 1|PL_M2 EQ 1)\s*(?:;.*)?',line)
        if match:frames.append((active,False));active=False
        elif line.strip()=='ELSE' and frames:
            parent,branch=frames[-1];frames[-1]=(parent,not branch);active=parent and not branch
        elif line.strip()=='ENDIF' and frames:active=frames.pop()[0]
        elif active:result.append(line)
    assert not frames
    return '\n'.join(result)+'\n'


def produce_sources(stage,valid_offset):
    """Extend every durable context producer, and fail closed on old markers."""
    changed={}
    for name in ('r3prof.mac','r3kctx.mac','r3drop.mac','r3keep.mac','r3kpre.mac','r3final.mac'):
        text=(ROOT/'src/system'/name).read_text()
        if name in ('r3prof.mac','r3kctx.mac','r3drop.mac'):
            assert text.count('        LD      DE,31')==1
            text=text.replace('        LD      DE,31','        LD      DE,33')
        if name=='r3drop.mac':
            text=text.replace('        LD      B,8\nRD_ZMON:', '        LD      B,10\nRD_ZMON:')
        if name=='r3kctx.mac':
            text=text.replace('        LD      B,8\nKC_ZMON:', '        LD      B,10\nKC_ZMON:')
        # Distinct context marker prevents an old producer being mistaken for
        # the larger representation. All consumers/producers change together.
        text=text.replace('05AH','05CH').replace('05BH','05DH')
        if name=='r3final.mac':
            text=text.replace('0A00H','0B00H').replace('0E03H','0F03H')
            entry=next(line for line in text.splitlines() if line.startswith('RF_ENTRY:'))
            text=text.replace(entry+'\n',entry+'\n'+paths.GUARD,1)
            anchor='        LD      (RF_CREQ),HL\n        LD      DE,41'
            assert text.count(anchor)==1
            text=text.replace(anchor,'        LD      (RF_CREQ),HL\n        LD      DE,49')
            anchor='        LD      HL,RF_NCOMIT\n'
            assert text.count(anchor)==1
            text=text.replace(anchor,'''        LD HL,(RF_CREQ)
        LD DE,(RF_CTX)
        CALL LY_CFG+0392H
        OR A
        JP NZ,RF_BAD
'''+anchor)
        (stage/'src/system'/name).write_text(text);changed[name]=text
    text=(ROOT/'src/system/rsxslots.mac').read_text()
    text=text.replace('        LD (MS_SLOT),HL','        LD (MS_SLOT),HL\n        LD (MS_VSLOT),HL',1)
    anchor='        DEC A                          ; 1.1 requires SCRN 1.0, 1.2 requires 1.1'
    assert text.count(anchor)==1
    text=text.replace(anchor,'''        CP 3
        JR NZ,VM_MINOR
        LD HL,(MS_PLAN)
        INC HL
        INC HL
        LD E,(HL)
        INC HL
        LD D,(HL)
        LD HL,VM_VALID
        ADD HL,DE
        JP C,MS_BAD
        LD (MS_VSLOT),HL
        LD HL,(MS_SOURCE)
        LD DE,5
        ADD HL,DE
        LD A,2                         ; private MCON 1.3 still requires SCRN 1.1
VM_MINOR:
'''+anchor)
    anchor='MS_FINISH:\n'
    assert text.count(anchor)==1
    text=text.replace(anchor,anchor+'''        LD DE,(MS_VSLOT)
        LD A,D
        OR E
        JR Z,VM_NONE
        LD HL,(MS_TARGET)
        LD BC,8
        ADD HL,BC
        LD (HL),E
        INC HL
        LD (HL),D
VM_NONE:
''')
    text=text.replace('MS_SLOT: DW 0','MS_SLOT: DW 0\nMS_VSLOT: DW 0')
    text=f'VM_VALID EQU {valid_offset}\n'+text
    (stage/'src/system/rsxslots.mac').write_text(text);changed['rsxslots.mac']=text
    return changed


def overlay(assembler,name,text,symbol,origin):
    text=re.sub(r'^'+symbol+r'\s+EQU[^\n]*',f'{symbol} EQU 0{origin:04X}H',text,flags=re.M)
    text=text.replace('0F00H','01000H')
    text=text.replace('; @resident-capsule-snapshot@','LD DE,(RN_REQ)\n        CALL LY_FCB+33\n        DB 12\n        OR A\n        JP NZ,RN_BAD')
    if name=='mover':
        old='        LD      DE,(RM_SIZE)\n        OR      A\n        SBC     HL,DE\n        JR      NC,RM_RSKIP'
        new='        LD      BC,(RM_NEW)\n        CALL LY_FCB+33\n        DB 18\n        JR      NC,RM_RSKIP'
        assert text.count(old)==1
        text='        INCLUDE layout.inc\n'+text.replace(old,new)
    text=base.normalized(choose_reference(text))
    text=re.sub(r'\bJR(\s+(?:(?:NZ|Z|NC|C),)?(?:MS_ADDRESS|RV_UNLOAD|RV_RETIRE))',r'JP\1',text)
    text,_=placed.relax(assembler,text)
    (OUT/(name+'.mac')).write_text(text)
    data,labels=placed.emit(assembler,name,text,origin)
    limit=1024 if origin==base.L['CONFIG'] else 1012
    assert len(data)<=limit,(name,len(data),limit)
    return data,labels


def publisher(assembler,root):
    text=base.normalized((ROOT/'src/system/r3pst.mac').read_text())
    start=text.index('RT_ENTRY:');end=text.index('        DS      RTBASE+0050H-$')
    helper=(base.HERE/'manager-prepare.inc').read_text()
    text=text[:start]+f'RT_ENTRY: JP 0{root["VG_RPUB"]:04X}H\n'+helper+text[end:]
    text=f'VG_ALLOC EQU 0{root["VG_ALLOC"]:04X}H\n'+text
    (OUT/'publisher.mac').write_text(text)
    data,labels=placed.emit(assembler,'publisher',text,base.L['CONFIG']+0x38f)
    assert labels['VP_PREP']==base.L['CONFIG']+0x392 and len(data)==107
    return data,labels



def integrated_root(identity,pins,ccp_size_address=0):
    text=previous.root_text(identity,pins)
    text=text.replace('        DB '+','.join(map(str,pins)), '\n'.join('        DB '+','.join(map(str,pins[i:i+16])) for i in range(0,len(pins),16)))
    text=text.replace('VG_PUBL: JP VG_COPY','VG_PUBL: JP VG_SELECT')
    text=text.replace('VG_COLD: JP VG_CLEAR','VG_COLD: JP VG_CLEAR\nVG_RAW: JP VR_RAW\nVG_BOOT: JP VR_BOOT\nVG_CCP: JP VR_CCP')
    start=text.index('VG_READY:');end=text.index('VG_IDENT:',start)
    text=text[:start]+'''VG_READY:
        PUSH DE
        CALL VR_BITS
        POP DE
        RET NZ
        JP VG_IDENT
VR_BITS:
        LD HL,VG_MASK
        LD DE,VR_NEED
        LD B,4
VR_BLOOP:
        LD A,(DE)
        AND (HL)
        LD C,A
        LD A,(DE)
        CP C
        JP NZ,VG_BAD
        INC DE
        INC HL
        DJNZ VR_BLOOP
        XOR A
        RET
'''+text[end:]
    text=text.replace('        LD (VG_MASK),A','        LD (VG_MASK),A\n        LD (VG_MASK+1),A\n        LD (VG_MASK+2),A\n        LD (VG_MASK+3),A',1)
    # BIOS belongs to the sealed resident image; native doesn't execute stage2.
    text=text.replace('VG_ISSUE:\n        LD A,(VG_MASK)\n        INC A\n        JP NZ,VG_BAD','VG_ISSUE:\n        PUSH HL\n        CALL VR_BITS\n        POP HL\n        RET NZ')
    text=text.replace('        CP 8\n',f'        CP {len(ROLES)}\n',1)
    begin=text.index('        LD A,(VG_ROLE)\n        LD B,A\n');end=text.index('VG_RBAD:',begin)
    text=text[:begin]+'''VR_MARK:
        LD A,(VG_ROLE)
        LD E,A
        AND 7
        LD B,A
        INC B
        LD A,E
        RRCA
        RRCA
        RRCA
        AND 3
        LD E,A
        LD D,0
        LD HL,VG_MASK
        ADD HL,DE
        LD A,080H
VG_BIT: RLCA
        DJNZ VG_BIT
        OR (HL)
        LD (HL),A
        XOR A
        RET
'''+text[end:]
    text=text.replace('VG_MASK: DB 0','VG_MASK: DB 1,0,0,0')
    # True cold entry marks only its trusted, sealed BIOS role.
    text=text.replace('        DJNZ VG_ZLOOP\n        RET','        DJNZ VG_ZLOOP\n        LD A,1\n        LD (VG_MASK),A\n        RET',1)
    at=text.index('VG_BUILD:')
    raw='''; Raw pinned objects have no caller-selected checksum or executable prefix.
; HL=quarantine buffer; DE=exclusive available end; A=role. Accept a bounded
; prefix of a padded physical block, hashing exactly the pinned logical length.
VR_RAW:
        LD (VG_LIMIT),DE
        CP VR_NROLE
        JP NC,VG_BAD
        LD (VG_ROLE),A
        ADD A,A
        ADD A,A
        LD E,A
        LD D,0
        PUSH HL
        LD HL,VG_PINS
        ADD HL,DE
        LD C,(HL)
        INC HL
        LD B,(HL)
        INC HL
        LD E,(HL)
        INC HL
        LD D,(HL)
        LD (VG_WANT),DE
        POP HL
        PUSH HL
        ADD HL,BC
        JR C,VR_RANGE
        LD DE,(VG_LIMIT)
        OR A
        SBC HL,DE
        JR C,VR_SIZE
        JR Z,VR_SIZE
VR_RANGE:
        POP HL
        JP VG_BAD
VR_SIZE:
        POP DE
        CALL VG_CRC
        LD DE,(VG_WANT)
        OR A
        SBC HL,DE
        JP NZ,VG_BAD
        JP VR_MARK
VR_BOOT:
        LD HL,LY_LOAD
        LD DE,LY_LOAD+1024
        LD A,2
        CALL VR_RAW
        OR A
        JR NZ,VR_STOP
        LD SP,LY_STKT
        JP LY_LOAD
VR_CCP:
        PUSH HL
        LD DE,(VR_CSIZE)
        ADD HL,DE
        EX DE,HL
        POP HL
        LD A,1
        CALL VR_RAW
        OR A
        RET Z
VR_STOP: HALT
        JR VR_STOP
; Native selector executes from permanent, already trusted core. Both physical
; sectors are quarantined in BUF and checked before touching the manager slot.
VG_SELECT:
        CP 4
        JP NC,VG_BAD
        LD E,A
        LD D,0
        PUSH DE
        LD HL,VR_RMAP
        ADD HL,DE
        LD A,(HL)
        LD (VR_SEL),A
        POP DE
        LD H,D
        LD L,E
        ADD HL,HL
        ADD HL,DE
        ADD HL,HL
        LD DE,VR_TABLE
        ADD HL,DE
        EX DE,HL
        LD HL,LY_BUF
        CALL VR_READ
        RET NZ
        INC DE
        INC DE
        INC DE
        CALL VR_READ
        RET NZ
        LD HL,LY_BUF
        LD DE,LY_BUF+1024
        LD A,(VR_SEL)
        CALL VR_RAW
        OR A
        RET NZ
        LD HL,LY_BUF
        LD DE,LY_RSX
        LD BC,03F4H
        LDIR
        LD HL,LY_BUF+03FDH
        LD DE,LY_RSX+03FDH
        LD BC,3
        LDIR
        XOR A
        RET
VR_READ:
        PUSH DE
        EX DE,HL
        LD A,(HL)
        INC HL
        LD B,(HL)
        INC HL
        LD C,(HL)
        EX DE,HL
        CALL LY_BIOS+51
        POP DE
        RET
VR_SEL: DB 0
VR_RMAP: DB 4,10,19,21
VR_TABLE:
; @rsx-sector-table@
; @rsx-validator-sector-table@
; @rsx-publisher-sector-table@
; @rsx-resolver-sector-table@
VR_NEED: DB VR_N0,VR_N1,VR_N2,VR_N3
'''
    text=text[:at]+raw+text[at:]
    constants=f'VR_NROLE EQU {len(ROLES)}\nVR_CSIZE EQU 0{ccp_size_address:04X}H\n'
    constants+=''.join(f'VR_N{i} EQU {(REQUIRED>>(8*i))&255}\n' for i in range(4))
    text=re.sub(r'\bJR(\s+(?:NZ|NC),VG_BAD)',r'JP\1',text)
    return constants+text


def reader_and_entry(assembler,root):
    text=(ROOT/'src/system/r3entry.mac').read_text()
    reader=text[text.index('RI_ENTRY:'):text.index('RI_PACK:')]
    reader=choose_reference(reader)+'RI_PACK: DB \'R3PACK  \'\n'
    # Preflight every immutable slot. Later reads are checked again before copy,
    # so changing the file after this pass cannot bypass admission.
    at='        LD      A,(IX+18)\n        CP      113'
    assert reader.count(at)==1
    preflight='''        CALL VG_BITS
        OR A
        JR Z,VI_GO
        XOR A
        LD (LY_FCB+32),A
        LD (IX+21),A
VI_SCAN:
        PUSH IX
        POP HL
        LD DE,0500H
        OR A
        SBC HL,DE
        PUSH HL
        CALL LY_FILE+3
        OR A
        JR NZ,VI_READBAD
        CALL LY_FILE+3
        OR A
        JR NZ,VI_READBAD
        POP HL
        PUSH HL
        LD DE,0400H
        ADD HL,DE
        EX DE,HL
        POP HL
        LD A,(IX+21)
        ADD A,7
        CALL VG_RAW
        OR A
        JP NZ,VI_BAD
        INC (IX+21)
        LD A,(IX+21)
        CP 15
        JR C,VI_SCAN
        JR VI_GO
VI_READBAD:
        POP HL
VI_BAD:
        LD HL,RI_FAIL-RI_ENTRY-0100H
        PUSH IX
        POP DE
        ADD HL,DE
        JP (HL)
VI_GO:
'''
    # JP to local error would break position independence; the trampoline above
    # is relative to runtime IX, as in the existing staged reader.
    preflight=preflight.replace('        JP NZ,VI_BAD','        JR NZ,VI_BAD')
    reader=reader.replace(at,preflight+at)
    at='        POP     HL\n        LD      A,(IX+0)\n        OR      A\n        LD      DE,LY_CFG'
    assert reader.count(at)==1
    # Gate before the destination/length registers and flags are selected.
    gate_at='VI_CHECK:\n'
    reader=reader.replace(at,'        POP     HL\n'+gate_at+'        LD      A,(IX+0)\n        OR      A\n        LD      DE,LY_CFG',1)
    at=gate_at
    gate='''        PUSH HL
        PUSH DE
        PUSH BC
        PUSH AF
        PUSH HL
        LD DE,0400H
        ADD HL,DE
        EX DE,HL
        POP HL
        LD A,(IX+18)
        RRCA
        RRCA
        RRCA
        ADD A,7
        CALL VG_RAW
        OR A
        JR NZ,VI_COPYBAD
        POP AF
        POP BC
        POP DE
        POP HL
        JR VI_COPYOK
VI_COPYBAD:
        LD HL,RI_FAIL-RI_ENTRY-0100H
        PUSH IX
        POP DE
        ADD HL,DE
        JP (HL)
VI_COPYOK:
'''
    reader=reader.replace(at,at+gate)
    # Long legacy jumps may now exceed JR reach. Use position-independent error
    # trampolines; every failure restores the saved SP through RI_RETURN.
    for label in ('RI_FAIL','RI_READFAIL'):
        pattern=re.compile(r'^\s*JR\s+(NZ|NC),'+label+r'[^\n]*$',re.M)
        inverse={'NZ':'Z','NC':'C'}
        serial=[0]
        def far(match):
            name=f'VI{serial[0]:04d}';serial[0]+=1
            return f'        JR {inverse[match[1]]},{name}\n        LD HL,{label}-RI_ENTRY-0100H\n        PUSH IX\n        POP DE\n        ADD HL,DE\n        JP (HL)\n{name}:'
        # Distinct prefix per target avoids generated duplicate labels.
        if label=='RI_READFAIL':serial[0]=50
        reader=pattern.sub(far,reader)
    reader=reader.replace('        LD      DE,0100H','        LD      DE,0200H',1).replace('-0100H','-0200H').replace('DE,0500H','DE,0600H')
    constants=f'VG_BITS EQU 0{root["VR_BITS"]:04X}H\nVG_RAW EQU 0{root["VG_RAW"]:04X}H\n'
    source=constants+'        INCLUDE layout.inc\n        ASEG\n        ORG 0\n'+reader+'        END\n'
    (OUT/'reader.mac').write_text(source)
    io=base.assemble(assembler,source,OUT/'reader.bin',OUT/'reader.lst',0)
    assert len(io)<=512,('reader',len(io))
    # Bind the worker before reading its relocation metadata; its trailing reader
    # is separately checked before being installed as the executable front door.
    original=choose_reference(text)
    anchor='        LD HL,(PX_HEADER)\n        LD DE,PX_MAGIC\n'
    assert original.count(anchor)==1
    gate='''        LD HL,(PX_HEADER)
        PUSH HL
        LD DE,2560
        ADD HL,DE
        EX DE,HL
        POP HL
        LD A,5
        CALL VG_RAW
        OR A
        JP NZ,PX_BAD
'''
    original=original.replace(anchor,gate+anchor)
    anchor='        LD      BC,0200H\n        LDIR\n        POP     HL\n        LD      DE,RV_HREQ'
    assert original.count(anchor)==1
    gate='''        PUSH HL
        PUSH DE
        PUSH HL
        LD DE,0200H
        ADD HL,DE
        EX DE,HL
        POP HL
        LD A,6
        CALL VG_RAW
        OR A
        POP DE
        POP HL
        JP NZ,RV_BAD
'''
    original=original.replace(anchor,gate+anchor)
    for index,label in enumerate(('RV_LOAD','RV_UNLOAD','RV_RETIRE')):
        line=next(line for line in original.splitlines() if line.startswith(label+':'))
        guard=f'        PUSH DE\n        LD A,26\n        CALL LY_BIOS+66\n        POP DE\n        CP 16\n        JR NZ,VI_BUSY{index}\n        LD A,255\n        OR A\n        RET\nVI_BUSY{index}:\n'
        original=original.replace(line+'\n',line+'\n'+guard,1)
    entry=overlay(assembler,'r3entry',constants+original,'RVBASE',base.L['RSX'])
    return entry,io

def build_all(assembler,stage,images,root,identity,matched):
    changed=produce_sources(stage,matched[1]['TX_VALID']-0x8000)
    built,_=paths.sources(assembler,stage)
    for name,text in changed.items():(stage/'src/system'/name).write_text(text)
    for name,text in changed.items():
        symbol={'r3prof.mac':'PFBASE','r3kctx.mac':'KCBASE','r3drop.mac':'RDBASE','r3keep.mac':'KEBASE','r3kpre.mac':'KPBASE','rsxslots.mac':'SUBASE','r3final.mac':'RFBASE'}[name]
        origin=base.L['CONFIG'] if name=='rsxslots.mac' else base.L['RSX']
        code,labels=overlay(assembler,name[:-4],text,symbol,origin)
        built[name[:-4]]=(code,labels,origin)
    entry,io=reader_and_entry(assembler,root)
    pub=publisher(assembler,root)
    meta_source=(stage/'src/system/r3meta.mac');meta_source.write_text(choose_reference((ROOT/'src/system/r3meta.mac').read_text()))
    old_previous_root=previous.ROOT;previous.ROOT=stage
    try:meta=previous.metadata(assembler,images,root,matched[1]['TX_BUILD']-0x8000)
    finally:previous.ROOT=old_previous_root
    gateway=bytes((0xc3,base.L['BDOS']&255,base.L['BDOS']>>8))
    resident={'R3COORD','R3PROF','R3KCTX','R3KEEP','R3KPRE','R3FINAL','R3DROP','R3COMIT','R3RESOL'}
    specs={'R3PLAN':('rsxplan.mac','RPBASE'),'R3SLOTS':('rsxslots.mac','SUBASE'),'R3SNAP':('r3snap.mac','RNBASE'),
           'R3CARR':('r3carr.mac','RXBASE'),'R3COORD':('r3coord.mac','RCBASE'),'R3PROF':('r3prof.mac','PFBASE'),
           'R3KCTX':('r3kctx.mac','KCBASE'),'R3KEEP':('r3keep.mac','KEBASE'),'R3KPRE':('r3kpre.mac','KPBASE'),
           'R3FINAL':('r3final.mac','RFBASE'),'R3DROP':('r3drop.mac','RDBASE'),'R3RESOL':('rsxresol.mac','RRBASE')}
    outputs={}
    for name,(filename,symbol) in specs.items():
        if name=='R3FINAL':code=built['r3final'][0]
        elif filename in changed:code=built[filename[:-4]][0]
        else:
            source=(ROOT/'src/system'/filename).read_text()
            code,_=overlay(assembler,name,source,symbol,base.L['RSX'] if name in resident else base.L['CONFIG'])
        outputs[name]=code.ljust(1021,b'\0')+gateway if name in resident else code.ljust(1024,b'\0')
    outputs['R3META']=meta[0].ljust(1024,b'\0')
    commit_text=(stage/'src/system/r3comit.mac').read_text()
    commit_text=re.sub(r'^XP[0-9]+:[^\n]*\n','',commit_text,flags=re.M)
    live_commit=overlay(assembler,'live-commit',commit_text,'RCBASE',base.L['RSX'])
    built['live-commit']=live_commit
    outputs['R3COMIT']=live_commit[0].ljust(1021,b'\0')+gateway
    move=bytearray(1024)
    for name,filename,symbol,offset in [('mover','rsxmover.mac','RMBASE',0),('scheduler','rsxsched.mac','RSBASE',0x120),('handoff','r3ovload.mac','ROBASE',0x310)]:
        text=(ROOT/'src/system'/filename).read_text()
        code,_=overlay(assembler,name,text,symbol,base.L['CONFIG']+offset)
        end=offset+len(code);assert end<= {'mover':0x120,'scheduler':0x310,'handoff':0x38f}[name]
        move[offset:end]=code
    move[0x38f:0x38f+len(pub[0])]=pub[0];outputs['R3MOVE']=bytes(move)
    outputs['entry']=entry[0].ljust(1021,b'\0')+gateway
    outputs['reader']=io.ljust(512,b'\0')
    import build_rsx_runtime_overlays as overlays
    old=overlays.ROOT;overlays.ROOT=stage
    # r3cache needs matching core symbols; all other sources remain controlled.
    try:
        text=overlays.source('r3cache.mac','CBBASE',0x1000)
        code,labels=placed.emit(assembler,'cache',text,0x1000)
        alttext=overlays.source('r3cache.mac','CBBASE',0x1101)
        alt,_=placed.emit(assembler,'cache-alt',alttext,0x1101)
    finally:overlays.ROOT=old
    repairs=base.relocation_offsets(code,alt,0x101)
    assert len(code)<=1536 and len(repairs)<=240
    header=bytearray(512);header[:4]=b'R3DC';header[4]=len(repairs);struct.pack_into('<H',header,6,len(code))
    for n,value in enumerate(repairs):struct.pack_into('<H',header,32+2*n,value)
    outputs['cache']=bytes(header)+code.ljust(1536,b'\0')+outputs['reader']
    # Bound code bytes include their immutable build identity in reconstructible
    # command images; never hash after relocation or stack use.
    ccp_text=(stage/'src/ccp/ccp.mac').read_text().replace('CCP_STACK:','VI_BUILD: DB '+','.join(map(str,identity))+'\nCCP_STACK:') if (stage/'src/ccp/ccp.mac').exists() else None
    assert ccp_text is not None
    (OUT/'ccp.mac').write_text(base.normalized(ccp_text))
    ccp=base.assemble(assembler,base.normalized(ccp_text),OUT/'ccp.bin',OUT/'ccp.lst',0xbb00)
    ccp_labels=base.symbols(OUT/'ccp.lst');assert len(ccp)<=5632
    reload_text=(stage/'src/platform/trs80m4/ccprelod.mac').read_text()
    line=next(line for line in reload_text.splitlines() if line.startswith('CRRELOC:'))
    reload_text=reload_text.replace(line+'\n',line+'''
        LD A,(CRFILE)
        OR A
        JR NZ,VI_RELOC
        LD HL,(CRBASE)
        CALL VG_CCP
VI_RELOC:
''',1)
    reload_text=reload_text.replace('        END\n','VI_BUILD: DB '+','.join(map(str,identity))+'\n        END\n')
    reload_text=f'VG_CCP EQU 0{root["VG_CCP"]:04X}H\n'+reload_text
    (OUT/'native-reloader.mac').write_text(reload_text)
    reloadcode=base.assemble(assembler,reload_text,OUT/'native-reloader.bin',OUT/'native-reloader.lst',base.L['RELOADER'])
    reloadlabels=base.symbols(OUT/'native-reloader.lst');assert len(reloadcode)<=960,('native reloader',len(reloadcode))
    artifacts={'bios':images['bios'][0],'ccp':ccp,'model4-reloader':reloadcode,'stage2':built['stage2'][0],**outputs}
    assert set(artifacts)==set(ROLES),(set(artifacts)-set(ROLES),set(ROLES)-set(artifacts))
    for name,data in artifacts.items():(OUT/(name+'.artifact')).write_bytes(data)
    return artifacts,built,reloadlabels,outputs


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--assembler',type=Path,default=Path.home()/'bin/z80asm')
    p.add_argument('--native-package',action='store_true',help='build private Model 4 reference media after the integration checks')
    args=p.parse_args()
    if layout.CONTEXT:p.error('use the unprepared native-reference checkout; checked/Model II profiles are not qualified by this campaign')
    assert len(NAMES)==15,'private reader format requires the reviewed fifteen-slot pack'
    OUT.mkdir(parents=True,exist_ok=True)
    base.OUT=placed.OUT=paths.OUT=OUT
    previous.OUT=OUT
    (OUT/'report.json').unlink(missing_ok=True)
    names=set(json.loads((ROOT/'docs/engineering/evidence/tcap-system-paths/report.json').read_text())['source_sha256'])
    names.discard('src/rsx/screen/model4.mac');names.add('src/rsx/screen/crt80x24.mac')
    names.update(str(path.relative_to(ROOT)) for folder in ('src/bdos','src/bios','src/system','src/platform','src/ccp','src/rsx') for path in (ROOT/folder).rglob('*') if path.is_file())
    names.update(str(path.relative_to(ROOT)) for path in (ROOT/'tools').glob('build*.py'))
    names.update(('tools/prototypes/tcap/matching_validity.py','tools/prototypes/tcap/validity-root.inc','tools/system_layout.py','tools/checked_build_contract.py','tools/checked_carriers.py','tools/rsx_disk_cache.py','tools/rsx_container.py'))
    if args.native_package:
        # Native utility expansion also reads registry/display metadata and
        # helper modules. Conservatively freeze the complete local source/tool
        # trees so a matching identity cannot hide changed expansion inputs.
        names.update(str(path.relative_to(ROOT)) for folder in ('src','metadata','tools') for path in (ROOT/folder).rglob('*') if path.is_file() and (folder!='tools' or path.suffix in ('.py','.inc','.mac')))
        names.update(('tools/startup_record.py','tools/shared_ui.py','tools/test_sysgen_install.py','tools/add_cpm_file_to_dmk.py','tools/trs80gp_launch.py','tools/run_trs80_command.py'))
    contract={'inputs':{name:previous.sha((ROOT/name).read_bytes()) for name in sorted(names)},'assembler_sha256':previous.sha(args.assembler.read_bytes())}
    for path in (Path(__file__),base.HERE/'manager-prepare.inc'):
        contract['inputs'][str(path.relative_to(ROOT))]=previous.sha(path.read_bytes())
    if args.native_package:
        for path in (base.HERE/'native_package.py',):contract['inputs'][str(path.relative_to(ROOT))]=previous.sha(path.read_bytes())
    if args.native_package:
        import utility_versions
        contract['development_display']={name:utility_versions.display_development('utility:'+name) for name in ('RCP','RSX','SYSGEN')}
    contract.update(private_epoch=5,permanent_bytes=1024,roles=ROLES,required_mask=REQUIRED)
    identity=hashlib.sha256(json.dumps(contract,sort_keys=True,separators=(',',':')).encode()).digest()[:16]
    # Preserve historical campaign code while using today's shared CRT source.
    # Only this private read view supplies its former filename and Model 4 flag.
    view=OUT/'reference-inputs';view.mkdir(exist_ok=True)
    if (view/'src').exists():shutil.rmtree(view/'src')
    shutil.copytree(ROOT/'src',view/'src')
    alias=view/'src/rsx/screen/model4.mac'
    alias.write_text((ROOT/'src/rsx/screen/crt80x24.mac').read_text().replace('        INCLUDE backend.inc','        INCLUDE backend.inc\nCRT_POS EQU M4CURSOR\nCRT_COL EQU M4COLUMN\nM2BANK EQU 0'))
    for name in ('tools','docs','metadata','build'):
        link=view/name
        if not link.exists():link.symlink_to(ROOT/name,target_is_directory=True)
    old_base_root,old_placed_root=base.ROOT,placed.ROOT
    base.ROOT=placed.ROOT=view
    try:images,_,backends,_=base.build(args.assembler)
    finally:base.ROOT=old_base_root
    images['bios'],stage=placed.packed_core(args.assembler,images)
    old_layout=dict(base.L);old_text=layout.LAYOUT_TEXT
    changes={'LY_SYS':old_layout['SYSTEM']-1024,'LY_HIST':old_layout['HISTORY']-1024,'LY_TPA':old_layout['TPA']-1024,'LY_RSX':old_layout['RSX']-1024,'LY_SECTS':15,'LY_RLCAP':960}
    newtext=old_text
    for name,value in changes.items():newtext=re.sub(r'^'+name+r'\s+EQU[^\n]*',f'{name} EQU 0{value:04X}H',newtext,flags=re.M)
    layout.LAYOUT_TEXT=newtext;(stage/'src/system/layout.inc').write_text(newtext)
    for alias,name in layout.ALIASES.items():
        if name in changes:base.L[alias]=changes[name]
    base.L.update(PDS_DESCRIPTOR=base.L['SYSTEM']+0x80,PDS_TOP=base.L['SYSTEM'],PDS_LOW=base.L['HISTORY'])
    tables=stage/'src/bios/tables.mac';tables.write_text(tables.read_text().replace('DW 389,127','DW 384,127').replace('DW 32,2','DW 32,3'))
    if args.native_package:
        # Canonical cold binding: installer normalization must not change sealed bytes.
        tables.write_text(tables.read_text().replace('DB 80,10,2,0E0H','DB 80,10,2,0A0H'))
    # New native selector is permanent. No executable tail remains in the raw
    # reloader block, allowing 960 code/data bytes below the original stack low.
    rootbase=base.L['SYSTEM']+0xf8
    reload=stage/'src/platform/trs80m4/reload.inc'
    rt=reload.read_text().replace('        JP LY_LOAD',f'        JP 0{rootbase+24:04X}H').replace('        JP LY_RSSEL',f'        JP 0{rootbase+6:04X}H')
    reload.write_text(rt)
    def build_gateway(pins,csize=0):
        source=(ROOT/'src/system/gateway.mac').read_text()
        source,n=re.subn(r'(SYS_COLD:[^\n]*\n)        LD      SP,SYS_STKTOP',r'\1        JP      VG_CBOOT',source);assert n==1
        source=source.replace('        .DEPHASE\n',integrated_root(identity,pins,csize)+'\n        .DEPHASE\n')
        (stage/'src/system/gateway.mac').write_text(source)
        return previous.rebuild_core(args.assembler,stage)
    try:
        images['bios']=build_gateway(bytes(4*len(ROLES)))
        root=base.symbols(stage/'build/system/gateway.lst')
        matched,slots,_=previous.owner(args.assembler,images,identity,root)
        artifacts,built,reloadlabels,outputs=build_all(args.assembler,stage,images,root,identity,matched)
        pins=b''.join(struct.pack('<HH',len(artifacts[name]),binascii.crc_hqx(artifacts[name],0xffff)) for name in ROLES)
        images['bios']=build_gateway(pins,reloadlabels['CRMSIZE'])
        root=base.symbols(stage/'build/system/gateway.lst')
        assert root['VG_MASK']-root['VG_PINS']==4*len(ROLES)
        assert root['VG_NEXT']-root['VG_MASK']==4 and root['VG_ROLE']-root['VG_NEXT']==4
        core=(stage/'build/system/gateway.bin').read_bytes();assert root['VG_END']<=base.L['BDOS']
        images['owner']=matched
        pack=b''.join(outputs[name] for name in NAMES)
        system=stage/'build/system'
        (system/'r3entry.bin').write_bytes(outputs['entry'][:1012])
        (system/'R3PACK.RSX').write_bytes(pack);(system/'R3CACHE.RSX').write_bytes(outputs['cache'])
        for name in NAMES:(system/(name+'.RSX')).write_bytes(outputs[name])
        print('BUILT',len(core),'root',root['VG_END']-root['VG_CHECK'],'pack',len(pack),'entry',len((OUT/'r3entry.bin').read_bytes()),flush=True)
        report=qualify(args.assembler,stage,images,root,core,artifacts,built,outputs,matched,slots,backends,identity,reloadlabels)
        if args.native_package:
            import native_package
            report['native_package']=native_package.build_package(args.assembler,stage,images,root,artifacts,matched,slots,backends,identity,reloadlabels)
        report.update(status='PASS',source_baseline='895b8e46',contract=contract,identity=identity.hex(),roles=ROLES,required_mask=REQUIRED,
                      sizes={name:len(data) for name,data in artifacts.items()},root_bytes=root['VG_END']-root['VG_CHECK'],gateway_bytes=len(core),
                      permanent_bytes=1024,resident_span_bytes=(system/'resident.bin').stat().st_size,tpa_record_bytes=((base.L['TPA']-256)//128)*128,
                      boot_sectors=15,boot_volume_off=3,boot_volume_dsm=384,
                      limits=['private native reference integration; no production source/media changes',
                              'controlled disk/physical services; no native machine or whole checked cpmsim qualification',
                              'native profile does not execute optional stage2; separate checked profile integration deferred',
                              'utility migrations and release assignment deferred; public request ABI remains a proposal'])
        import difflib
        files=('src/system/layout.inc','src/platform/trs80m4/reload.inc','src/system/gateway.mac','src/bios/tables.mac')
        patch=''.join(line for path in files for line in difflib.unified_diff((ROOT/path).read_text().splitlines(True),(stage/path).read_text().splitlines(True),fromfile='a/'+path,tofile='b/'+path,n=0))
        (OUT/'integrated-core.patch').write_text(patch)
        contexts=('r3prof.mac','r3kctx.mac','r3drop.mac','r3keep.mac','r3kpre.mac','r3final.mac','rsxslots.mac')
        context_patch=''.join(line for name in contexts for line in difflib.unified_diff((ROOT/'src/system'/name).read_text().splitlines(True),(stage/'src/system'/name).read_text().splitlines(True),fromfile='a/src/system/'+name,tofile='b/src/system/'+name,n=0))
        (OUT/'manager-context.patch').write_text(context_patch)
        resident=(stage/'build/system/resident.bin').read_bytes()
        manifest={'schema':1,'private_epoch':5,'identity':identity.hex(),'required_native_mask':REQUIRED,
                  'resident_sha256':previous.sha(resident),'artifacts':{name:{'bytes':len(data),'sha256':previous.sha(data),'crc16':binascii.crc_hqx(data,65535)} for name,data in artifacts.items()}}
        (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        report.update(date='2026-11-07',source_baseline=subprocess.check_output(['git','rev-parse','e366bf9e' if args.native_package else '895b8e46'],cwd=ROOT).decode().strip(),
                      python_version=sys.version.split()[0],assembler_sha256=previous.sha(args.assembler.read_bytes()),
                      patch_sha256=previous.sha(patch.encode()),context_patch_sha256=previous.sha(context_patch.encode()),manifest_sha256=previous.sha((OUT/'manifest.json').read_bytes()),
                      shim_sha256=previous.sha((stage/'build/rsx-offline-test/shim.c').read_bytes()),
                      test_source_sha256={name:previous.sha((ROOT/name).read_bytes()) for name in ('tools/test_rsx_offline.py','tools/test_rsx_disk_cache.py','tools/test_usq.py')})
        engine=Path.home()/'projects/git/z80pack/z80core'
        engine_files=sorted(set(engine.glob('simz80*.c'))|{engine/'simglb.c'}|set(engine.glob('*.h')))
        report['emulator_source_sha256']={path.name:previous.sha(path.read_bytes()) for path in engine_files}
        if args.native_package:
            assert all(previous.sha((ROOT/name).read_bytes())==digest for name,digest in contract['inputs'].items()),'package inputs changed during build'
            assert contract['development_display']=={name:utility_versions.display_development('utility:'+name) for name in ('RCP','RSX','SYSGEN')},'package display inputs changed during build'
        (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({key:report[key] for key in ('root_bytes','gateway_bytes','sizes','permanent_bytes','tpa_record_bytes')},indent=2))
    finally:base.L.clear();base.L.update(old_layout);layout.LAYOUT_TEXT=old_text;placed.ROOT=old_placed_root


def qualify(assembler,stage,images,root,core,artifacts,built,outputs,matched,slots,backends,identity,reloadlabels):
    import test_rsx_offline as offline
    import test_rsx_disk_cache as disk
    old_offline,old_disk,old_out,old_shim=offline.ROOT,disk.ROOT,disk.OUT,offline.SHIM
    gen_pc=built['live-commit'][1]['RC_GENWRITE']
    offline.SHIM=offline.SHIM.replace('cpu_state=ST_SINGLE_STEP; cpu_z80();',f'if(hook && (PC=={root["VG_RPUB"]} || PC=={gen_pc})) hook(4); cpu_state=ST_SINGLE_STEP; cpu_z80();')
    offline.ROOT=disk.ROOT=stage;disk.OUT=stage/'build/system'
    ccp_text=(OUT/'ccp.mac').read_text()
    import build_ccp
    alternatives=[]
    for origin in (0xbc01,0xbd37):
        data=base.assemble(assembler,ccp_text.replace('0BB00H',f'0{origin:04X}H'),OUT/f'ccp-{origin:x}.bin',OUT/f'ccp-{origin:x}.lst',origin)
        alternatives.append((data,origin))
    repairs=build_ccp.relocation_offsets(artifacts['ccp'],alternatives)
    assert len(repairs)<=504
    header=bytearray(1024);struct.pack_into('<4sBBHHHHH',header,0,b'BCM1',1,2,0xbb00,len(artifacts['ccp']),5632,0,len(repairs))
    for i,offset in enumerate(repairs):struct.pack_into('<H',header,16+2*i,offset)
    ccp_carrier=bytes(header)+artifacts['ccp']
    assert len(ccp_carrier)<=13*512
    bios=images['bios'][1]
    root_data=(stage/'build/system/gateway.bin').read_bytes()
    def triples(data,address,count,origin):return [tuple(data[address-origin+3*i:address-origin+3*i+3]) for i in range(count)]
    reload_sectors=triples(images['bios'][0],bios['M4_RLTAB'],2,base.L['BIOS'])
    command_sectors=triples(artifacts['model4-reloader'],reloadlabels['CRSECTS'],13,base.L['RELOADER'])
    selector_sectors=triples(core,root['VR_TABLE'],8,base.L['SYSTEM'])
    carrier=base.make_module(name='XTCAP',version=(0,5),services=[],linked_base=0x8000,code=matched[0],relocations=slots,reconstruction_class='STATEFUL',callable_services=[(b'MCON',1,3,matched[1]['AN_ENTRY']-0x8000,4),(b'XTCP',0,4,matched[1]['TX_ENTRY']-0x8000,0)])
    backends=placed.placed_backends(assembler,images,backends)
    bcode,blabels,brepairs,bentry=backends['M4SCRN']
    backend=base.make_module(name='M4SCRN',version=(1,1),services=[],linked_base=0x8000,code=bcode,relocations=brepairs,reconstruction_class='STATEFUL',callable_services=[(b'SCRN',1,1,blabels[bentry]-0x8000,1)])
    class IntegratedMachine(disk.DiskMachine):
        def __init__(self):
            self.physical=False;self.phys_fault=None;self.preads=[];self.read_fault=None;self.publication=[];self.pending=None;self.steps=[];self.console=[]
            super().__init__()
            self.mem[base.L['BIOS']:base.L['BIOS']+len(images['bios'][0])]=images['bios'][0]
            self.mem[base.L['SYSTEM']:base.L['SYSTEM']+len(root_data)]=root_data
            self.word(bios['MP_MON'],bios['MC_RAW']);self.word(bios['M4CURSOR'],0xf800)
            self.mem[base.L['SYSTEM']+0x94]=0
            self.mem[base.L['EXTENSIONS']+3:base.L['EXTENSIONS']+5]=b'\xaf\xc9'
            self.mem[base.L['BIOS']+51:base.L['BIOS']+54]=b'\xc3'+struct.pack('<H',base.L['FILE']+6)
            self.blocks={}
            def store(keys,data):
                padded=data.ljust(len(keys)*512,b'\0')
                for i,key in enumerate(keys):self.blocks[key]=padded[i*512:i*512+512]
            store(reload_sectors,artifacts['model4-reloader'])
            store(command_sectors,ccp_carrier)
            for i,name in enumerate(('entry','R3CARR','R3MOVE','R3RESOL')):store(selector_sectors[2*i:2*i+2],artifacts[name])
            self.files[0,0,'M4SCRN.RSX']=backend;self.files[0,0,'XTCAP.RSX']=carrier
        def callback(self,kind):
            if kind==4:
                if self.pc.value==gen_pc and (self.mem[root['VG_ROLE']]!=ROLES.index('R3COMIT') or bytes(self.mem[gen_pc:gen_pc+3])!=outputs['R3COMIT'][gen_pc-base.L['RSX']:gen_pc-base.L['RSX']+3]):return
                if self.pc.value==root['VG_RPUB']:self.pending=self.pair('DE')
                request=self.pending
                if request is not None:
                    target=self.word(request+43);expected=bytes(self.mem[self.word(request+41):self.word(request+41)+4])
                    self.publication.append({'phase':'publish' if self.pc.value==root['VG_RPUB'] else 'generation',
                        'target':target,'value':None if not target else bytes(self.mem[target:target+4]).hex(),
                        'expected':expected.hex(),'generation':self.word(base.L['SYSTEM']+0x92),
                        'binding':self.word(bios['MP_MON']),'expected_binding':self.word(request+35)})
                return
            if kind==2 and self.runtime_name=='R3PACK' and self.read_fault==self.mem[base.L['FILE']+109+32]*128:
                self.reg['A'].value=255;self.reg['F'].value=0;return
            if kind==1 and self.reg['C'].value==2:
                self.console.append(self.reg['E'].value);self.reg['A'].value=0;self.reg['F'].value=0x40;return
            if kind==1 and self.reg['C'].value==37:
                self.reg['A'].value=0;self.reg['F'].value=0x40;return
            if self.physical and kind==3:
                try:
                    key=(self.reg['A'].value,self.reg['B'].value,self.reg['C'].value)
                    self.preads.append(key);data=self.blocks[key]
                    if self.phys_fault==key:data=bytes((data[0]^1,))+data[1:]
                    at=self.pair('HL');self.mem[at:at+512]=data;self.pair('HL',at+512)
                    self.reg['A'].value=0;self.reg['F'].value=0x40
                except BaseException as error:self.error=error;self.reg['A'].value=255;self.reg['F'].value=0
                return
            return super().callback(kind)
        def run(self,address,budget=60000000):
            self.sp.value=0x3f00
            steps=self.lib.test_run(address,budget)
            assert steps>=0,(steps,hex(self.pc.value))
            assert self.error is None,self.error
            self.steps.append(steps)
            return self.reg['A'].value
        def native_boot(self):
            self.physical=True
            stop=base.L['SYSTEM']+0x23;saved=bytes(self.mem[stop:stop+3]);self.mem[stop:stop+3]=b'\xc3\xff\xff'
            try:result=self.run(bios['M4_RELOAD'],12000000)
            finally:self.physical=False;self.mem[stop:stop+3]=saved
            return result
        def change(self,op,name,location=None,high=None):
            self.pending=None
            self.physical=True;self.reg['A'].value=0
            try:result=self.run(base.L['BIOS']+60,12000000)
            finally:self.physical=False
            if result:return result
            return super().change(op,name,location,high)
        def invoke(self,address,operation,token=None):
            if token is not None:self.mem[0x7600:0x7610]=token
            self.pair('DE',0x7600);self.reg['A'].value=operation
            result=self.run(address,12000000)
            return result,bytes(self.mem[0x7600:0x7610])
    try:
        m=IntegratedMachine();checks=[]
        def check(name,value):assert value,name;checks.append(name)
        def snapshot():return bytes(m.mem),dict(m.files),dict(m.blocks)
        def restore(saved):
            memory,files,blocks=saved;m.mem[:]=memory;m.files=dict(files);m.blocks=dict(blocks)
            m.physical=False;m.phys_fault=None;m.read_fault=None;m.stage_fault=None;m.fault=None;m.hits=0;m.error=None
            m.events.clear();m.trace.clear();m.publication.clear();m.pending=None;m.preads.clear()
        initial=snapshot()
        m.native_boot()
        check('native fetch verifies reloader and CCP before publication',m.word(base.L['SYSTEM']+0x8c)==base.L['TPA']-5632 and int.from_bytes(bytes(m.mem[root['VG_MASK']:root['VG_MASK']+4]),'little')&7==7)
        boot=snapshot()
        check('backend installed by complete manager',m.change(1,b'M4SCRN',(0,0))==0)
        check('backend-only commit does not reserve validity',m.word(root['VG_NEXT'])==0)
        check('owner installed by complete manager',m.change(1,b'XTCAP',(0,0))==0)
        def owner_base():return m.word(bios['MP_MON'])-(matched[1]['AN_ENTRY']-0x8000)
        def owner_entry():return owner_base()+matched[1]['TX_ENTRY']-0x8000
        def current_validity():return int.from_bytes(bytes(m.mem[owner_base()+matched[1]['TX_VALID']-0x8000:owner_base()+matched[1]['TX_VALID']-0x8000+4]),'little')
        check('manager constructed and published first validity',current_validity()==1)
        check('MCON 1.3 depends on SCRN 1.1',m.mem[base.L['RSX_STATE']]==2)
        result,token=m.invoke(owner_entry(),2,bytes(16));check('installed owner begins scope',result==0)
        before=m.chain();events=len(m.events)
        check('active session refuses mutation before filesystem work',m.change(2,b'XTCAP',(0,0))==255 and m.chain()==before and len(m.events)==events)
        check('active session refuses load before filesystem work',m.change(1,b'EXTRA',(0,0))==255 and m.chain()==before and len(m.events)==events)
        check('active session refuses self-retirement',m.change(4,b'XTCAP',(0,0))==255 and m.chain()==before and len(m.events)==events)
        check('active session still permits read-only query',m.change(3,b'XTCAP',(0,0))==1 and m.chain()==before and len(m.events)==events)
        check('current token ends installed scope',m.invoke(owner_entry(),4,token)[0]==0)
        first_base=owner_base()
        check('complete manager unloads owner',m.change(2,b'XTCAP',(0,0))==0)
        check('removal context clears absent validity target',int.from_bytes(bytes(m.mem[root['VG_NEXT']:root['VG_NEXT']+4]),'little')==1 and m.word(bios['MP_MON'])==bios['MC_RAW'])
        check('complete manager reloads owner',m.change(1,b'XTCAP',(0,0))==0)
        backend_base=m.word(base.L['SYSTEM']+0x84)
        loaded_owner_bytes=backend_base-owner_base()
        assert loaded_owner_bytes==2560
        check('same address has newly issued validity',owner_base()==first_base and current_validity()==2)
        result,newtoken=m.invoke(owner_entry(),2,bytes(16))
        check('local serial equality cannot recreate retired token',result==0 and newtoken[4:]==token[4:] and newtoken[:4]!=token[:4])
        check('retired token cannot end current scope',m.invoke(owner_entry(),4,token)[0]==13)
        check('reloaded current token remains usable',m.invoke(owner_entry(),4,newtoken)[0]==0)
        for publication in m.publication:
            if publication['phase']=='generation':
                check('publication precedes generation '+str(len(checks)),publication['binding']==publication['expected_binding'] and (not publication['target'] or publication['value']==publication['expected']))
        result,warm_token=m.invoke(owner_entry(),2,bytes(16));assert result==0
        m.native_boot()
        check('native warm reconstruction retires owned scope',m.mem[owner_base()+matched[1]['TX_STATE']-0x8000]==0 and m.console[-2:]==[13,10])
        check('native warm reconstruction preserves global namespace',m.word(root['VG_NEXT'])==2 and current_validity()==2)
        check('warm command allocation stays below resident owner',m.word(base.L['SYSTEM']+0x8c)+5632<=m.word(base.L['SYSTEM']+0x90))
        publication_evidence=list(m.publication)
        extra=base.make_module(name='EXTRA',version=(0,1),services=[],linked_base=0x8000,code=bytes(8)+b'\x2a\x00\x80\xe9',relocations=[9])
        m.files[0,0,'EXTRA.RSX']=extra
        ready=snapshot();failure_cases=[]
        def refused(name,operation):
            before=m.chain();counter=bytes(m.mem[root['VG_NEXT']:root['VG_NEXT']+4]);context=m.context()
            result=operation()
            assert result==255,(name,result)
            assert m.chain()==before and bytes(m.mem[root['VG_NEXT']:root['VG_NEXT']+4])==counter,(name,'changed live state')
            assert m.context()==context,(name,'changed caller disk context')
            failure_cases.append(name)
        # Missing/corrupt code is rejected by native and file-backed front doors.
        for index in range(15):
            restore(boot)
            data=bytearray(m.files[0,0,'R3PACK.RSX']);data[1024*index]^=1;m.files[0,0,'R3PACK.RSX']=bytes(data)
            refused('initial preflight corrupt '+NAMES[index],lambda:m.change(1,b'M4SCRN',(0,0)))
        for length in (15360-128,15360+128):
            restore(boot);m.files[0,0,'R3PACK.RSX']=m.files[0,0,'R3PACK.RSX'][:length].ljust(length,b'\0')
            refused('pack length '+str(length),lambda:m.change(1,b'M4SCRN',(0,0)))
        for offset in (0,31,512,2048,2559):
            restore(ready);data=bytearray(m.files[0,0,'R3CACHE.RSX']);data[offset]^=1;m.files[0,0,'R3CACHE.RSX']=bytes(data)
            refused('worker/header/reader corruption '+str(offset),lambda:m.change(1,b'EXTRA',(0,0)))
        for chunk in range(5):
            restore(ready);m.stage_fault=chunk
            refused('worker read failure '+str(chunk),lambda:m.change(1,b'EXTRA',(0,0)))
        for index in range(15):
            restore(boot);m.read_fault=index*1024
            refused('preflight read failure '+NAMES[index],lambda:m.change(1,b'M4SCRN',(0,0)))
        for index in range(15):
            restore(ready)
            data=bytearray(m.files[0,0,'R3PACK.RSX']);data[index*1024+7]^=1;m.files[0,0,'R3PACK.RSX']=bytes(data)
            m.mem[0x8400:0x8600]=artifacts['reader'];m.mem[0x7400]=index*8
            m.pair('HL',0x8400);m.pair('DE',0x7400);m.reg['A'].value=0
            refused('per-copy rejects changed '+NAMES[index],lambda:m.run(0x8400))
        restore(ready);m.phys_fault=selector_sectors[0]
        refused('native selector rejects changed entry before install',lambda:m.change(1,b'EXTRA',(0,0)))
        # The actual finalizer rejects old context markers, even if code from a
        # previous epoch somehow supplies a shorter preparation record.
        for marker in (0x5a,0x5b):
            restore(ready);m.mem[base.L['RSX']:base.L['RSX']+1024]=outputs['R3FINAL']
            m.mem[0x7400:0x7421]=bytes(33);m.mem[0x7416]=marker;m.pair('DE',0x7400)
            refused('old finalizer context '+hex(marker),lambda:m.run(base.L['RSX']))
        restore(ready)
        refused('insufficient manager workspace',lambda:m.change(1,b'EXTRA',(0,0),high=0x1800))
        restore(ready);m.mem[root['VG_NEXT']:root['VG_NEXT']+4]=b'\xff'*4
        refused('allocator exhaustion aborts real finalizer',lambda:m.change(1,b'EXTRA',(0,0)))
        # Fail after reservation, while the actual handoff is fetching commit.
        restore(ready);before=m.chain();m.read_fault=13*1024
        check('late commit read failure returns without publication',m.change(1,b'EXTRA',(0,0))==255 and m.chain()==before and not m.publication)
        check('late failure burns reservation without changing owner',m.word(root['VG_NEXT'])==3 and current_validity()==2)
        m.read_fault=None
        check('retry uses a fresh reservation',m.change(1,b'EXTRA',(0,0))==0 and current_validity()==4)
        # Retained snapshots and context reconstruction work without originals.
        del m.files[0,0,'M4SCRN.RSX'];del m.files[0,0,'XTCAP.RSX']
        check('offline removal reconstructs retained owner from cache',m.change(2,b'EXTRA',(0,0))==0 and current_validity()==5)
        check('disk context survives manager publication',m.context()==(2,17,0x1600))
        for publication in m.publication:
            if publication['phase']=='generation':check('retry/offline publication ordering '+str(len(checks)),publication['binding']==publication['expected_binding'] and (not publication['target'] or publication['value']==publication['expected']))
        publication_evidence+=m.publication
        ansi=images['ansi-base'];repairs_ansi=base.relocation_offsets(ansi[0],images['ansi-base-alt'][0],0x101)
        m.files[0,0,'ANSI.RSX']=base.make_module(name='ANSI',version=(0,1),services=[],linked_base=0x8000,code=ansi[0],relocations=repairs_ansi,reconstruction_class='STATEFUL',callable_services=[(b'MCON',1,2,ansi[1]['AN_ENTRY']-0x8000,4)])
        check('offline TCAP removal preserves namespace',m.change(2,b'XTCAP',(0,0))==0 and m.word(root['VG_NEXT'])==5)
        check('ordinary ANSI installs without TCAP validity',m.change(1,b'ANSI',(0,0))==0 and m.word(root['VG_NEXT'])==5)
        cursor=m.word(bios['M4CURSOR']);m.reg['A'].value=0;m.reg['C'].value=ord('Z')
        m.run(m.word(bios['MP_MON']))
        check('legacy personality writes through its normal backend',m.mem[cursor]==ord('Z'))
        m.native_boot();check('ordinary ANSI survives native warm reconstruction',m.word(root['VG_NEXT'])==5)
        check('ordinary ANSI unload preserves namespace',m.change(2,b'ANSI',(0,0))==0 and m.word(root['VG_NEXT'])==5)
        check('last provider removal restores unloaded TPA',m.change(2,b'M4SCRN',(0,0))==0 and m.word(6)==base.L['TPA'] and m.mem[base.L['RSX_STATE']]==0 and m.word(root['VG_NEXT'])==5)
        m.run(root['VG_COLD'])
        check('cold helper clears all admission words and allocator',bytes(m.mem[root['VG_MASK']:root['VG_MASK']+4])==b'\x01\0\0\0' and bytes(m.mem[root['VG_NEXT']:root['VG_NEXT']+4])==bytes(4))
        for label,key in [('native reloader CRC failure',reload_sectors[0]),('native CCP CRC failure',command_sectors[-1])]:
            restore(initial);m.phys_fault=key;before=m.word(base.L['SYSTEM']+0x8c);generation=m.word(base.L['SYSTEM']+0x92)
            try:m.native_boot()
            except AssertionError as error:
                assert m.error is None and m.pc.value in (root['VR_STOP'],root['VR_STOP']+1),(label,error,hex(m.pc.value))
            else:raise AssertionError(label+' unexpectedly returned')
            check(label+' stops before command publication',m.word(base.L['SYSTEM']+0x8c)==before and m.word(base.L['SYSTEM']+0x92)==generation)
        print('PASS integrated manager/native cases',len(checks),len(failure_cases),flush=True)
        components=component_checks(assembler,images,root,core,artifacts,built,slots,backends,identity)
        return {'component_regressions':components,'loaded_owner_allocation_bytes':loaded_owner_bytes,'manager_native_checks':checks,'front_door_failure_checks':failure_cases,'ccp_relocations':len(repairs),
                'maximum_emulator_steps_per_invocation':max(m.steps),'disk_services':'existing drive/user-aware RSC fixture; controlled login/reset and physical reads',
                'publication_checkpoints':publication_evidence,'publication_trace':'CPU checkpoints at permanent publisher entry and actual RC_GENWRITE',
                'emulator':'existing z80pack C CPU shim through test_rsx_offline.Machine'}
    finally:offline.ROOT,disk.ROOT,disk.OUT,offline.SHIM=old_offline,old_disk,old_out,old_shim

def component_checks(assembler,images,root,core,artifacts,built,slots,backends,identity):
    images=dict(images);images['commit']=built['commit'][:2]
    built=dict(built);built['finalizer']=(*built['r3final'][:2],base.L['RSX'],982)
    old_roles=previous.ROLES;previous.ROLES=ROLES
    result=[]
    try:
        for name in ('M4SCRN','ANSISCRN'):
            for origin in (0x9000,0xa101):
                f=placed.PlacedFixture(assembler,images,slots,backends,name,origin)
                previous.load_root(f,core,root,artifacts,identity)
                f.cpu.hl=f.labels['TX_VALID'];assert f.run(root['VG_ALLOC'])==0
                cases=base.exercise(f)+paths.checks(f,images,built)
                depths={label:high-f.cpu._min_sp.get(label,high) for label,(_,high) in f.cpu._stack_bounds.items()}
                assert depths['bdos']<=40
                result.append({'backend':name,'origin':hex(origin),'checks':len(cases),'observed_stack_bytes':depths})
    finally:previous.ROLES=old_roles
    print('PASS real BDOS/owner/entry regressions',sum(run['checks'] for run in result),flush=True)
    return result

if __name__=='__main__':main()
