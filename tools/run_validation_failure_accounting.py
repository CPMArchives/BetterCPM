#!/usr/bin/env python3
"""Production BDOS RO mutation and complete selected Function-37 profile oracles."""
import argparse,contextlib,hashlib,io,json,shutil,sys
from pathlib import Path


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('build-root','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False);sys.path.insert(0,str(a.build_root/'tools'))
    import test_unified_bdos as f
    original=f.Z80;captured=[]
    def capture(*args,**kw):c=original(*args,**kw);captured.append(c);return c
    f.Z80=capture;log=io.StringIO()
    try:
        with contextlib.redirect_stdout(log):f.main()
    finally:f.Z80=original
    (a.output/'foundation.txt').write_text(log.getvalue());cpu,=captured;s=f.symbols();sp=cpu.sp
    # The foundation's legacy mutation fixtures disable entry cache invalidation.
    # Restore every emitted instruction before these independent public calls.
    emitted=f.IMAGE.read_bytes();end=s['UB_OLDSP']-f.BASE
    cpu.mem[f.BASE:s['UB_OLDSP']]=emitted[:end]
    assert bytes(cpu.mem[f.BASE:s['UB_OLDSP']])==emitted[:end]
    memory=bytes(cpu.mem)
    def call(fn,arg=0):
        cpu.ix=0xA55A;cpu.c,cpu.de=fn,arg;cpu.run(f.BASE,limit=100000);assert cpu.sp==sp and cpu.ix==0xA55A;return cpu.a
    protection=[]
    for fn in (19,23):
        cpu.mem[:]=memory;cpu.mem[f.FIXTURE+9]|=128;call(32,0);assert call(13)==0
        cpu.mem[f.FCB:f.FCB+36]=bytes(36);cpu.mem[f.FCB+1:f.FCB+12]=b'OWNER   DAT'
        if fn==23:cpu.mem[f.FCB+17:f.FCB+28]=b'NEW     DAT'
        before=bytes(cpu.mem[f.FIXTURE:f.FIXTURE+512]);writes=cpu.mem[0x7304]
        assert call(fn,f.FCB)==255;assert bytes(cpu.mem[f.FIXTURE:f.FIXTURE+512])==before and cpu.mem[0x7304]==writes
        protection.append({'function':fn,'status':255,'directory_unchanged':True,'no_write':True})
    resets=[]
    for mask in (0,1,2,6,15,0x8000,0xFFFF):
        cpu.mem[:]=memory;call(32,0);assert call(13)==0
        for drive in range(4):assert call(14,drive)==0 and call(28)==0
        assert call(14,1)==0;call(32,7);call(26,0x9000)
        call(24);assert cpu.hl==15;call(29);assert cpu.hl==15
        media=bytes(cpu.mem[f.FIXTURE:f.FIXTURE+512]);reads,writes=cpu.mem[0x7303],cpu.mem[0x7304]
        assert call(37,mask)==0;call(24);login=cpu.hl;call(29);ro=cpu.hl
        assert login==ro==(15&~mask);assert call(25)==1 and call(32,255)==7 and cpu.word(s['UB_DMA'])==0x9000
        assert cpu.mem[0x7303]==reads and cpu.mem[0x7304]==writes and bytes(cpu.mem[f.FIXTURE:f.FIXTURE+512])==media
        call(31);call(24);assert cpu.hl==((15&~mask)|2)
        resets.append({'mask':mask,'login_after':login,'ro_after':ro,'caller_drive':1,'caller_user':7,'dma':0x9000,'no_immediate_io':True,'selected_drive_relogs_on_query':True})
    # Capture write-type C at the actual BIOS boundary while metadata writes
    # persist the first private directory record. Data bytes are not qualified
    # by this provider; only public lifecycle ordering/type codes are asserted.
    from build_ccp import assemble
    from system_layout import LAYOUT
    cpu.mem[:]=memory;call(32,0);call(31);dpb=cpu.hl
    cpu.mem[dpb+2:dpb+5]=bytes((3,7,0));cpu.setword(dpb+5,31);cpu.setword(dpb+7,15)
    cpu.mem[dpb+9:dpb+11]=bytes((0x80,0));cpu.setword(dpb+11,0)
    cpu.mem[f.FIXTURE:f.FIXTURE+512]=b'\xE5'*512
    assert call(13)==0
    source=f""" ORG 9A00H
 LD A,C
 OUT (44H),A
 CP 1
 JR NZ,DONE
 PUSH HL
 PUSH DE
 PUSH BC
 LD HL,({s['UB_DIRBUF']})
 LD DE,{f.FIXTURE}
 LD BC,128
 LDIR
 POP BC
 POP DE
 POP HL
DONE: XOR A
 RET
 END
"""
    (a.output/'write-provider.asm').write_text(source)
    data=assemble(Path.home()/'bin/z80asm',source,a.output/'write-provider.bin',a.output/'write-provider.lst',0x9A00)
    cpu.mem[0x9A00:0x9A00+len(data)]=data;cpu.mem[LAYOUT['BIOS']+42:LAYOUT['BIOS']+45]=bytes((0xC3,0,0x9A))
    types=[]
    def output(port,value):assert port&255==0x44;types.append(value)
    cpu.port_write=output
    cpu.mem[f.FCB:f.FCB+36]=bytes(36);cpu.mem[f.FCB+1:f.FCB+12]=b'NEW     DAT'
    assert call(22,f.FCB)!=255;call(26,0x9000);cpu.mem[0x9000:0x9080]=b'X'*128
    assert call(21,f.FCB)==0 and call(21,f.FCB)==0 and call(16,f.FCB)!=255
    assert types==[1,1,2,0,1],types
    assert cpu.mem[f.FIXTURE+15]==2
    image=a.build_root/'build/bdos/bdos.bin';shutil.copy2(__file__,a.output/'executed-runner.py')
    result={'status':'PASS','bdos_sha256':hashlib.sha256(image.read_bytes()).hexdigest(),'instruction_prefix_sha256':hashlib.sha256(emitted[:end]).hexdigest(),'foundation_cache_patch_restored':True,'protection':protection,'function37':resets,'public_lifecycle_write_types':types,'cards':['0370','0371','0435','0523','0458'],'scope':'Production BDOS instructions with declared private directory/DPB providers. Function 37 is selected and fully checked for inactive/current/multiple/read-only reset effects; no physical media-change claim.'};(a.output/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS protected Delete/Rename and seven selected Function-37 state profiles')


if __name__=='__main__':main()
