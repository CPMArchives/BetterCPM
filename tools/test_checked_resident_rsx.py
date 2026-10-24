#!/usr/bin/env python3
"""Execute native resident gates/restore and the checked RSX pack reader."""
from pathlib import Path
import argparse
import binascii
import copy
import hashlib
import json
import struct
import types

from build_checked_resident_rsx import build_rsx_components
from checked_build_contract import load_contract
from checked_rsx_reader_fixture import run_reader_cases
from system_layout import LAYOUT as L
from test_bios import Z80

ROOT = Path(__file__).resolve().parents[1]


def native_cases():
    out = ROOT/'build/z80pack';meta = json.loads((out/'checked-load.json').read_text())
    sy = meta['symbols'];cases = []
    def cpu():
        c = Z80((out/'bios.bin').read_bytes());disk = (out/'disk.bin').read_bytes()
        c.mem[L['DISK']:L['DISK']+len(disk)] = disk;c.sp = 0x5F00;c.ix = 0x1234
        return c
    for data in [b'123456789']+[bytes((i*37+11)&255 for i in range(n)) for n in (1,127,128,511,512,1024)]:
        c = cpu();c.mem[0x4001:0x4001+len(data)] = data;c.de = 0x4001;c.bc = len(data)
        before = bytes(c.mem[L['BIOS']:L['FILE']]);c.run(sy['Z_CRC'],limit=500000)
        assert c.hl == binascii.crc_hqx(data,0xFFFF)
        assert (c.sp,c.ix)==(0x5F00,0x1234) and c.mem[0x4001:0x4001+len(data)]==data
        assert c.mem[L['BIOS']:L['FILE']]==before
        cases.append({'case':'native-crc','bytes':len(data),'crc16':c.hl})
    identity = (out/'disk.bin').read_bytes()[L['BIOS']-16-L['DISK']:L['BIOS']-L['DISK']]
    for mutation in [None,*range(16)]:
        c = cpu();probe = bytearray(identity)
        if mutation is not None:probe[mutation]^=1
        c.mem[0x4000:0x4010] = probe;c.hl = 0x4000;c.de = L['BIOS']-16
        c.run(L['BIOS']-26,limit=10000)
        assert c.z == (mutation is None) and c.mem[0x4000:0x4010]==probe
        assert (c.sp,c.ix)==(0x5F00,0x1234)
        cases.append({'case':'native-id-compare','mutation':mutation,'accepted':c.z})
    payloads = [('reloader',(out/'command-loader/stage1.carrier').read_bytes(),'Z_EREL'),
                ('control',(out/'control.carrier').read_bytes(),'Z_ECTL'),
                ('entry',(ROOT/'build/system/R3ENTRY.RSX').read_bytes(),'Z_EENT')]
    for kind,payload,label in payloads:
        expected = meta['checksums'][label]
        assert binascii.crc_hqx(payload,0xFFFF)==expected
        for offset in [None,0,511,999,1000,1015,1023]:
            damaged = bytearray(payload)
            if offset is not None:damaged[offset]^=1
            c = cpu();c.mem[0x4000:0x4400]=damaged;c.de=0x4000;c.hl=expected
            c.run(sy['Z_VERIFY'],limit=250000)
            assert (c.a==0)==(offset is None) and (c.sp,c.ix)==(0x5F00,0x1234)
            cases.append({'case':'native-carrier-gate','kind':kind,'mutation':offset,'accepted':c.a==0})
        for byte in range(16):
            damaged = bytearray(payload);damaged[1000+byte]^=1
            c=cpu();c.mem[0x4000:0x4400]=damaged;c.de=0x4000;c.hl=binascii.crc_hqx(damaged,0xFFFF)
            c.run(sy['Z_VERIFY'],limit=250000);assert c.a!=0
            cases.append({'case':'foreign-id-with-matching-crc','kind':kind,'byte':byte,'accepted':False})
    for kind,payload,_ in payloads:
        entry = {'entry':'PL_RSXLOAD','control':'PL_OVLOAD','reloader':'PL_RELOAD'}[kind]
        for count,status in [(0,1),(128,1),(896,1),(1023,1),(1024,0)]:
            c=cpu();c.mem[0x5000:0x5004]=bytes((0xDB,254,0xB7,0xC9))
            c.mem[L['DISK']+15:L['DISK']+18]=bytes((0xC3,0,0x50))
            c.mem[L['RSX']:L['RSX']+1024]=bytes([0xA5])*1024
            def read(port):
                assert port&255==254
                c.mem[c.hl:c.hl+count]=payload[:count]
                return status
            output=[];c.port_read=read;c.port_write=lambda port,value:output.append(value);c.a=0
            if kind=='reloader':
                run=types.FunctionType(Z80.run.__code__,dict(Z80.run.__globals__,SENTINEL=L['RELOADER']))
                try:run(c,sy[entry],250000);accepted=c.pc==L['RELOADER']
                except AssertionError:
                    assert c.mem[c.pc-1]==0x76 and output==[ord('!')]
                    accepted=False
            else:
                c.run(sy[entry],limit=250000);accepted=c.a==0
                assert c.mem[L['RSX']:L['RSX']+1021]==bytes([0xA5])*1021
                assert (c.sp,c.ix)==(0x5F00,0x1234)
            assert accepted==(status==0)
            cases.append({'case':'partial-raw-read','kind':kind,'bytes':count,'accepted':accepted})
    c=cpu();backup=bytes(i%256 for i in range(1012));c.mem[0x6000:0x63F4]=backup
    c.setword(L['FILE']-2,0x6000);c.mem[L['DISK']+15:L['DISK']+18]=b'\x76'*3
    c.mem[L['RSX']:L['RSX']+1024]=bytes([0xA5])*1024;c.a=3
    c.run(sy['PL_RSXLOAD'],limit=20000)
    assert c.a==0 and c.mem[L['RSX']:L['RSX']+1012]==backup
    assert c.mem[L['RSX']+1012:L['RSX']+1024]==bytes([0xA5])*12
    assert (c.sp,c.ix)==(0x5F00,0x1234)
    cases.append({'case':'disk-free-resolver-restore','bytes':1012,'gateway_and_frame_preserved':True})
    return cases


def carrier_cases(identity):
    """Independent BRSX3 fixtures exercise emitted carrier/metadata validators."""
    import test_rsxcarrier as fixture
    from build_rsx_module import make_module
    original_cpu=fixture.Z80
    class ResidentCPU(Z80):
        def __init__(self,_):
            super().__init__((ROOT/'build/z80pack/bios.bin').read_bytes())
            disk=(ROOT/'build/z80pack/disk.bin').read_bytes()
            self.mem[L['DISK']:L['DISK']+len(disk)]=disk
        def run(self,address,limit=1000):super().run(address,max(limit,500000))
    fixture.Z80=ResidentCPU
    try:
        def make(public):
            payload=bytearray(32);payload[10:12]=(0x8010).to_bytes(2,'little')
            data=bytearray(make_module(name='PROBE',version=(1,0),services=[],linked_base=0x8000,
                code=bytes(payload),relocations=[10],reconstruction_class='STATELESS' if public else 'STATEFUL',
                callable_services=[] if public else [(b'TEST',1,0,8,0)],runtime_pointers=[] if public else [12]))
            off=int.from_bytes(data[30:32],'little');length=int.from_bytes(data[off+8:off+10],'little')
            data[4]=3;data[off+4]=2;data[off+7]+=1
            data[off+8:off+10]=(length+20).to_bytes(2,'little')
            data[off+12:off+12]=bytes((4,18,1,int(not public)))+(bytes(16) if public else identity)
            return data
        results=[]
        def check(label,data,accepted=False,metadata=False):
            c,before=fixture.phase_one(bytes(data),name=b'PROBE   ')
            phase=1
            if c.a==0 and (accepted or metadata):
                before=fixture.phase_two(c,len(data));phase=2
            assert (c.a==0)==accepted,(label,phase,c.a)
            if not accepted:assert c.mem[fixture.FACTS:fixture.FACTS+26]==before,label
            results.append({'case':label,'phase':phase,'accepted':accepted,'facts_preserved_on_failure':True})
        private=make(False);public=make(True)
        check('private-stateful',private,True);check('public-stateless',public,True)
        off=int.from_bytes(private[30:32],'little');record=off+12
        for i in range(16):
            bad=bytearray(private);bad[record+4+i]^=1;check('foreign-private-id-'+str(i),bad)
            bad=bytearray(public);bad[record+4+i]=1;check('nonzero-public-id-'+str(i),bad)
        for end in range(record,record+20):check('truncated-binding-'+str(end-record),private[:end])
        for at,value in [(4,2),(record,5),(record+1,17),(record+2,0),(record+2,2),(record+3,2)]:
            bad=bytearray(private);bad[at]=value;check('binding-field-'+str(at)+'-'+str(value),bad)
        bad=bytearray(private);bad[512]^=1;check('bad-payload-checksum',bad)
        bad=bytearray(private);bad[off+4]=1;check('old-metadata-schema',bad,metadata=True)
        bad=bytearray(private);bad[record:record]=bad[record:record+20];bad[off+7]+=1
        struct.pack_into('<H',bad,off+8,int.from_bytes(bad[off+8:off+10],'little')+20)
        check('duplicate-binding',bad,metadata=True)
        return results
    finally:fixture.Z80=original_cpu


def reference_comparison(reference, contract, output):
    fixture = copy.deepcopy(contract)
    fixture['compatibility_id']=json.loads((reference/'assessment-profile.json').read_text())['compatibility_id']
    result=build_rsx_components(fixture,Path.home()/'bin/z80asm',output)
    identical=[]
    for name in result['artifacts']:
        assert (output/name).read_bytes()==(reference/'build/system'/name).read_bytes(),name
        identical.append(name)
    for name in ('rsxio.bin','rsxloader.bin'):
        assert (output/name).read_bytes()==(reference/'build/system'/name).read_bytes(),name
        identical.append(name)
    root=ROOT/'build/z80pack';old=reference/'build/z80pack'
    symbols=json.loads((root/'checked-load.json').read_text())['symbols']
    new=bytearray((root/'bios.bin').read_bytes());previous=bytearray((old/'bios.bin').read_bytes())
    for label in ('Z_EREL','Z_ECTL','Z_EENT'):
        at=symbols[label]+1-L['BIOS'];new[at:at+2]=previous[at:at+2]=bytes(2)
    assert new==previous,'BIOS code differs beyond the three checked checksum operands'
    new=bytearray((root/'disk.bin').read_bytes());previous=bytearray((old/'disk.bin').read_bytes())
    at=L['BIOS']-16-L['DISK'];new[at:at+16]=previous[at:at+16]=bytes(16)
    assert new==previous,'disk code differs beyond the private identity'
    for name in ('extensions.bin','gateway.bin','tables.bin','config.bin'):
        assert (root/name).read_bytes()==(old/name).read_bytes(),name
        identical.append(name)
    return {'exact_artifacts':identical,'bios_only_differences':'three checksum immediates',
            'disk_only_difference':'16-byte private identity'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reference',type=Path,required=True)
    p.add_argument('--foreign-pack',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();contract=load_contract(ROOT,Path.home()/'bin/z80asm')
    comparison=reference_comparison(a.reference,contract,a.output.parent/'reference-rsx')
    native=native_cases();reader=run_reader_cases(a.foreign_pack)
    carriers=carrier_cases(bytes.fromhex(contract['compatibility_id']))
    assert load_contract(ROOT,Path.home()/'bin/z80asm')==contract
    result={'profile':contract['contract']['profile'],'compatibility_id':contract['compatibility_id'],
            'reference_comparison':comparison,'native_cases':native,'reader':reader,'carrier_cases':carriers,'status':'PASS',
            'scope':'native resident helpers and copied pack reader; no new live checked OS/transaction campaign'}
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(f'PASS {len(native)} native resident cases; {len(reader["cases"])} reader cases; {len(carriers)} carrier cases; {len(comparison["exact_artifacts"])} reference artifacts identical')


if __name__=='__main__':main()
