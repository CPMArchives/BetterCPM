#!/usr/bin/env python3
"""Execute production RSX disk-cache transactions with returning-error injection."""
import hashlib
import json
import re
import struct
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from test_rsx_offline import Machine, L
from test_rsx_stage3 import service_offset
OUT=ROOT/'build/system'

class DiskMachine(Machine):
    def __init__(self):
        self.fault=None;self.hits=0;self.trace=[];self.stage_fault=None;self.runtime_name=None
        super().__init__()
        self.mem[L['RSX_STATE']:L['RSX_STATE']+41]=bytes(41)
        self.word(L['SYSTEM']+0x84,L['BDOS'])
        self.word(L['SYSTEM']+0x88,L['HISTORY'])
        self.bootstrap=(OUT/'r3entry.bin').read_bytes()
        self.files[0,0,'R3PACK.RSX']=(OUT/'R3PACK.RSX').read_bytes()
        self.files[0,0,'R3CACHE.RSX']=(OUT/'R3CACHE.RSX').read_bytes()
        self.mem[self.symbol['UB_DRIVE']]=2;self.mem[self.symbol['UB_USERNO']]=17
        self.word(self.symbol['UB_DMA'],0x1600)
    def callback(self,kind):
        if kind==0:
            at=self.pair('HL');self.runtime_name=bytes(self.mem[at:at+8]).decode().rstrip()
        if kind==2 and self.runtime_name=='R3CACHE' and self.stage_fault is not None and self.position==self.stage_fault*512:
            self.reg['A'].value=255;self.reg['F'].value=0
            return
        if kind!=1:return super().callback(kind)
        try:
            fn=self.reg['C'].value;fcb=self.pair('DE')
            raw=bytes(self.mem[fcb+1:fcb+12]);name=raw[:8].decode().rstrip()+'.'+raw[8:].decode().rstrip()
            key=(self.mem[fcb]-1,self.mem[self.symbol['UB_USERNO']],name)
            cache=name.endswith('.RSC')
            fail=False
            if cache and self.fault and fn==self.fault[0]:
                self.hits+=1;fail=self.hits==self.fault[1]
            self.trace.append((fn,key,fail))
            if fail:value=2 if fn in (20,21) else 255
            elif fn==15:
                value=3 if key in self.files else 255
                if value!=255:self.opened=key;self.diskpos=0
            elif fn==22:
                assert key not in self.files,('overwrite',key)
                self.files[key]=b'';self.opened=key;self.diskpos=0;value=2
            elif fn==16:value=1
            elif fn==19:
                del self.files[key];value=0
            elif fn==20:
                assert self.opened==key,(self.opened,key)
                data=self.files[key][self.diskpos:self.diskpos+128]
                value=0 if data else 1
                if data:
                    at=self.word(self.symbol['UB_DMA']);self.mem[at:at+128]=data.ljust(128,b'\0');self.diskpos+=128
            elif fn==21:
                assert self.opened==key
                at=self.word(self.symbol['UB_DMA']);data=bytes(self.mem[at:at+128])
                old=self.files[key];self.files[key]=old[:self.diskpos]+data+old[self.diskpos+128:]
                self.diskpos+=128;value=0
            else:raise AssertionError(fn)
            self.reg['A'].value=value;self.reg['F'].value=0x40 if value==0 else 0
        except BaseException as e:self.error=e;self.reg['A'].value=255;self.reg['F'].value=0
    def change(self,op,name,location=None,high=None):
        return super().change(op,name,location,high)
    def chain(self):
        low=self.word(L['SYSTEM']+0x88)
        return (bytes(self.mem[L['RSX_STATE']:L['RSX_STATE']+41]),self.word(L['SYSTEM']+0x84),low,self.word(6),self.word(L['SYSTEM']+0x92),bytes(self.mem[low:L['RSX']]))
    def context(self):return (self.mem[self.symbol['UB_DRIVE']],self.mem[self.symbol['UB_USERNO']],self.word(self.symbol['UB_DMA']))

def setup():
    m=DiskMachine()
    for name,du in (('HELLO',(1,0)),('STATEFUL',(1,3)),('BATCHIO',(1,0))):m.files[du+(name+'.RSX',)]=(ROOT/f'build/rsx/{name}.RSX').read_bytes()
    return m

def state(m,op):
    carrier=(ROOT/'build/rsx/STATEFUL.RSX').read_bytes()
    base=m.word(L['SYSTEM']+0x84)
    for i in range(m.mem[L['RSX_STATE']]):
        if bytes(m.mem[L['RSX_STATE']+1+i*8:L['RSX_STATE']+9+i*8])==b'STATEFUL':break
        base=m.word(base)-8
    m.mem[0x3600:0x3610]=bytes((1,16,op))+bytes(13)
    m.pair('DE',0x3600)
    assert m.run(base+service_offset(carrier))==(0xA4 if op==2 else 0)
    result=bytearray(m.mem[0x3600:0x3610])
    if op==2:
        for at in (6,8):
            value=struct.unpack_from('<H',result,at)[0]
            struct.pack_into('<H',result,at,(value-base)&65535)
    return bytes(result)

def main():
    m=setup()
    assert m.change(1,b'HELLO',(1,0))==0, m.trace
    print('HELLO loaded')
    assert m.change(1,b'STATEFUL',(1,3))==0,m.trace
    print('STATEFUL loaded')
    stateful=(ROOT/'build/rsx/STATEFUL.RSX').read_bytes()
    def stat(op):
        base=m.word(L['SYSTEM']+0x84)
        for i in range(m.mem[L['RSX_STATE']]):
            if bytes(m.mem[L['RSX_STATE']+1+i*8:L['RSX_STATE']+9+i*8])==b'STATEFUL':break
            base=m.word(base)-8
        m.mem[0x3600:0x3610]=bytes((1,16,op))+bytes(13)
        m.pair('DE',0x3600)
        assert m.run(base+service_offset(stateful))==(0xA4 if op==2 else 0)
        result=bytearray(m.mem[0x3600:0x3610])
        if op==2:
            for at in (6,8):
                value=struct.unpack_from('<H',result,at)[0]
                struct.pack_into('<H',result,at,(value-base)&65535)
        return bytes(result)
    stat(0)
    for _ in range(3):stat(1)
    expected=stat(2)
    del m.files[1,0,'HELLO.RSX'];del m.files[1,3,'STATEFUL.RSX']
    assert m.change(2,b'HELLO',(0,0))==0,m.trace
    actual=stat(2)
    assert actual==expected,(expected.hex(),actual.hex())
    assert m.change(2,b'STATEFUL',(0,0))==0
    print('offline relocation/unload passed')
    b=setup();old_tpa=b.word(6)
    assert b.change(1,b'BATCHIO',(1,0))==0,b.trace
    low=b.word(L['SYSTEM']+0x88)
    allocation=L['RSX']-low
    assert b.change(2,b'BATCHIO',(0,0))==0
    assert b.word(6)==old_tpa
    print('BATCHIO provider allocation',allocation)
    checks=[]
    # Returning disk errors during actual preparation must not publish changes.
    faults=[(22,1,'load')]+[(21,i,'load') for i in range(1,11)]+[(16,1,'load')]
    faults += [(20,i,'load-retained') for i in range(1,8)]+[(16,2,'load-retained')]
    faults += [(15,4,'unload')]+[(20,i,'unload') for i in range(1,8)]+[(16,1,'unload')]
    for fn,nth,operation in faults:
        x=setup()
        assert x.change(1,b'STATEFUL',(1,3))==0
        if operation=='unload':assert x.change(1,b'HELLO',(1,0))==0
        state(x,0)
        for _ in range(3):state(x,1)
        expected_state=state(x,2)
        before=x.chain();context=x.context()
        x.fault=(fn,nth)
        result=x.change(1,b'BATCHIO',(1,0)) if operation.startswith('load') else x.change(2,b'HELLO',(0,0))
        assert x.hits>=nth,(fn,nth,operation,x.hits)
        assert result==255,(fn,nth,operation,result,x.trace)
        assert x.chain()==before,(fn,nth,operation,'live chain changed')
        assert x.context()==context
        assert state(x,2)==expected_state
        x.fault=None
        # A subsequent successful change must still be possible; failed new
        # cache files are skipped, existing installed cache files are untouched.
        retry=x.change(1,b'BATCHIO',(1,0)) if operation.startswith('load') else x.change(2,b'HELLO',(0,0))
        assert retry==0,(fn,nth,operation,'retry',retry,x.trace)
        checks.append({'function':fn,'occurrence':nth,'operation':operation,'chain_unchanged':True,'retry_pass':True,'stateful_service_pass':True})
    # CRC/prefix/count errors in an installed cache reject before commit.
    corrupt_checks=[]
    for offset in (0,8,128,700):
        x=setup();assert x.change(1,b'STATEFUL',(1,3))==0;assert x.change(1,b'HELLO',(1,0))==0
        key=next(k for k in x.files if k[2].endswith('.RSC') and x.files[k][18:26]==b'STATEFUL')
        original=x.files[key];bad=bytearray(original);bad[offset]^=1;x.files[key]=bytes(bad)
        before=x.chain()
        assert x.change(2,b'HELLO',(0,0))==255,(offset,x.trace)
        assert x.chain()==before
        x.files[key]=original
        assert x.change(2,b'HELLO',(0,0))==0
        corrupt_checks.append(offset)
    # Query provenance needs no cache disk and cannot depend on staged helper.
    x=setup();assert x.change(1,b'STATEFUL',(1,3))==0
    saved=dict(x.files)
    for key in list(x.files):
        if key[2].endswith('.RSC') or key[2]=='R3CACHE.RSX':del x.files[key]
    x.mem[0x1000:0x1800]=bytes(2048);x.trace.clear()
    assert x.change(3,b'STATEFUL',(0,0))==1
    assert bytes(x.mem[0x312:0x314])==bytes((1,3)) and not x.trace
    # Prototype removal still opens the removed carrier during planning.
    # Missing cache must fail safely, then recover after restoring the file.
    x.files[0,0,'R3CACHE.RSX']=(OUT/'R3CACHE.RSX').read_bytes()
    before=x.chain()
    assert x.change(2,b'STATEFUL',(0,0))==255
    assert x.chain()==before
    x.files.update(saved)
    assert x.change(2,b'STATEFUL',(0,0))==0
    # Foreign collisions are never deleted or overwritten; all five occupied
    # slots reject a new installation without affecting the live profile.
    x=setup();assert x.change(1,b'STATEFUL',(1,3))==0
    for i in range(1,5):x.files[0,0,f'$$RSX0{i}.RSC']=b'user file'.ljust(128,b'!')
    before=x.chain()
    assert x.change(1,b'HELLO',(1,0))==255
    assert x.chain()==before
    stage_checks=[]
    for chunk in range(5):
        x=setup();assert x.change(1,b'STATEFUL',(1,3))==0
        before=x.chain();context=x.context();x.stage_fault=chunk
        assert x.change(1,b'HELLO',(1,0))==255
        assert x.chain()==before and x.context()==context
        x.stage_fault=None
        assert x.change(1,b'HELLO',(1,0))==0
        stage_checks.append(chunk)
    # STATELESS retained code is reconstructed from its cache, not live bytes.
    x=setup();assert x.change(1,b'HELLO',(1,0))==0
    base=x.word(L['SYSTEM']+0x84);original_byte=x.mem[base+40];x.mem[base+40]^=1
    del x.files[1,0,'HELLO.RSX']
    assert x.change(1,b'STATEFUL',(1,3))==0
    assert x.mem[x.word(L['SYSTEM']+0x84)+40]==original_byte
    # Force overlapping upward STATEFUL movement, protect provider padding,
    # and leave an external pointer numerically inside the loader-owned page.
    x=setup()
    small=bytearray(x.files[1,0,'HELLO.RSX']);struct.pack_into('<H',small,14,256)
    large=bytearray(x.files[1,3,'STATEFUL.RSX']);struct.pack_into('<H',large,14,1024)
    x.files[1,0,'HELLO.RSX']=bytes(small);x.files[1,3,'STATEFUL.RSX']=bytes(large)
    assert x.change(1,b'HELLO',(1,0))==0
    assert x.change(1,b'STATEFUL',(1,3))==0
    state(x,0)
    for _ in range(3):state(x,1)
    old=x.word(L['SYSTEM']+0x88)
    x.mem[old+1023]=0xA7
    listing=(ROOT/'build/rsx/stateful.lst').read_text()
    fixed=int(re.search(r'^([0-9a-f]{4}).*\bSR_FIXED:',listing,re.M|re.I)[1],16)-0x8000
    external=old+1026;x.word(old+fixed,external)
    expected_state=state(x,2)
    del x.files[1,0,'HELLO.RSX'];del x.files[1,3,'STATEFUL.RSX']
    assert x.change(2,b'HELLO',(0,0))==0
    new=x.word(L['SYSTEM']+0x88)
    assert 0<new-old<1280
    assert x.mem[new+1023]==0xA7 and x.word(new+fixed)==external
    assert state(x,2)==expected_state
    # Relocated callers may supply any sufficient disposable workspace.
    for low in (0x405,0x1234,0x2011):
        x=setup();x.workspace_low=low
        assert x.change(1,b'HELLO',(1,0))==0
        assert x.word(L['FILE']+109+34)==((low+255)&~255)+512+33
        assert x.change(2,b'HELLO',(0,0))==0
        assert not any(k[2].endswith('.RSC') for k in x.files)
    # Repeated successful changes reclaim cache files immediately at commit.
    x=setup()
    for _ in range(8):
        assert x.change(1,b'HELLO',(1,0))==0
        assert sum(k[2].endswith('.RSC') for k in x.files)==1
        assert x.change(2,b'HELLO',(0,0))==0
        assert not any(k[2].endswith('.RSC') for k in x.files)
    # Retrying cleanup after a returning delete error protects the new chain.
    x=setup();assert x.change(1,b'STATEFUL',(1,3))==0
    assert x.change(1,b'HELLO',(1,0))==0
    x.fault=(19,1)
    assert x.change(2,b'HELLO',(0,0))==0
    assert x.mem[L['RSX_STATE']]==1
    assert sum(k[2].endswith('.RSC') for k in x.files)==2
    x.fault=None
    assert x.change(1,b'HELLO',(1,0))==0
    assert sum(k[2].endswith('.RSC') for k in x.files)==2
    # Bad signatures and foreign reserved-name collisions are left intact.
    x=setup();foreign=b'foreign reserved-name collision'.ljust(128,b'!')
    x.files[0,0,'$$RSX00.RSC']=foreign
    assert x.change(1,b'HELLO',(1,0))==0
    assert x.files[0,0,'$$RSX00.RSC']==foreign
    assert x.change(2,b'HELLO',(0,0))==0
    assert x.files[0,0,'$$RSX00.RSC']==foreign
    # A removed member's header must be authenticated before its allocation
    # is used, even though that member does not need full reconstruction.
    x=setup();assert x.change(1,b'STATEFUL',(1,3))==0
    assert x.change(1,b'HELLO',(1,0))==0
    key=next(k for k in x.files if k[2].endswith('.RSC') and x.files[k][18:26]==b'HELLO   ')
    original=x.files[key];bad=bytearray(original);bad[128+14]^=1;x.files[key]=bytes(bad)
    before=x.chain()
    assert x.change(2,b'HELLO',(0,0))==255
    assert x.chain()==before
    x.files[key]=original;assert x.change(2,b'HELLO',(0,0))==0
    # Returning housekeeping errors before publication preserve the old chain.
    cleanup_checks=[]
    for fn in (20,16,19):
        x=setup();assert x.change(1,b'STATEFUL',(1,3))==0
        active=next(v for k,v in x.files.items() if k[2].endswith('.RSC'))
        stale=bytearray(active);stale[6]=1;x.files[0,0,'$$RSX01.RSC']=bytes(stale)
        before=x.chain();x.fault=(fn,1)
        assert x.change(1,b'HELLO',(1,0))==255
        assert x.chain()==before
        x.fault=None;assert x.change(1,b'HELLO',(1,0))==0
        cleanup_checks.append(fn)
    # Legacy A0 API and no-I/O idempotence remain compatible.
    x=setup();x.files[0,0,'HELLO.RSX']=x.files[1,0,'HELLO.RSX']
    assert x.change(1,b'HELLO')==0
    del x.files[0,0,'R3CACHE.RSX'];x.trace.clear()
    assert x.change(1,b'HELLO',(15,31))==0 and not x.trace
    assert x.change(2,b'ABSENT',(0,0))==0 and not x.trace
    sizes={p.name:p.stat().st_size for p in OUT.glob('r3*.bin') if not p.stem.endswith('-alt')}
    sizes['rsxio.bin']=(OUT/'rsxio.bin').stat().st_size
    sizes['rsxresolver.bin']=(OUT/'rsxresolver.bin').stat().st_size

    report={'scope':'integrated RAM-profile Z80 manager with record-filesystem hooks; not native disk qualification',
            'status':'PASS','removed_header_corruption_rejected':True,'precommit_cleanup_error_functions':cleanup_checks,'postcommit_cleanup_failure_deferred':True,'cleanup_reuse_cycles':8,'relocated_workspace_bases':[0x405,0x1234,0x2011],'overlapping_stateful_move_preserves_padding_and_external_pointer':True,'helper_staging_read_failures':stage_checks,'stateless_pristine_reconstruction':True,'returning_disk_error_cases':checks,'corrupt_cache_offsets_rejected':corrupt_checks,
            'batchio_provider_allocation':allocation,'batchio_shared_manager':1024,
            'batchio_total_resident':allocation+1024,'batchio_saving_vs_merged':3328-allocation-1024,
            'provider_footer_bytes':10,'extra_batchio_allocation_for_footer':allocation-512,
            'provider_owned_padding_preserved':True,
            'extra_shared_resident_bytes':0,'unloaded_tpa_change':0,'total_emitted_image_bytes':sum(sizes.values()),
            'helper_file_bytes':2560,'helper_actual_bytes':sizes['r3cache.bin'],
            'temporary_reserved_helper_bytes':2560,'temporary_workspace':'page-aligned caller-supplied bounds',
            'emitted_code_sizes':sizes,
            'disk_free_query_provenance':True,'cache_namespace_exhaustion_safe':True,
            'limitations':[
              'CRC16 detects accidental mismatch, not malicious replacement',
              'unchecked RAM profile only; no ROM/checked profile qualification',
              'filesystem hooks do not establish physical-media crash atomicity or fatal BDOS error recovery']}
    report['executable_sha256']={n:hashlib.sha256((OUT/n).read_bytes()).hexdigest() for n in ('R3PACK.RSX','R3CACHE.RSX','r3entry.bin')}
    (ROOT/'build/rsx-disk-cache-results.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS',len(checks),'returning-error cases; cache corruption, retry, provenance, exhaustion and reclamation')
    print('helper',sizes['r3cache.bin'],'entry',sizes['r3entry.bin'])

if __name__=='__main__':main()
