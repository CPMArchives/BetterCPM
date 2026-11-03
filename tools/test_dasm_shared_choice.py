#!/usr/bin/env python3
"""Compare all DASM approval bytes using the existing full z80pack test core."""
import ctypes as C
import hashlib,json,re,shutil,subprocess,tempfile
from pathlib import Path
from test_usq import SHIM
from test_utility_versions import address
ROOT=Path(__file__).resolve().parents[1]


def main():
    image=(ROOT/'build/utilities/DASM.COM').read_bytes()
    listing=(ROOT/'build/utilities/dasm.lst').read_text()
    z=Path.home()/'projects/git/z80pack';core=z/'z80core'
    with tempfile.TemporaryDirectory(prefix='dasm-choice-') as tmp:
        w=Path(tmp);(w/'sim.h').write_text('#define DEF_CPU Z80\n#define EXCLUDE_I8080\n')
        for name in ('simmem.h','simport.h'):shutil.copy2(z/'z80sim/srcsim'/name,w/name)
        shim=SHIM.replace('static WORD readpc, writepc;', 'static WORD readpc, writepc; WORD minimum_sp;')
        shim=shim.replace('PC=address; SP-=2;', 'minimum_sp=SP; PC=address; SP-=2;')
        shim=shim.replace('if(PC==65535)', 'if(SP<minimum_sp) minimum_sp=SP; if(PC==65535)')
        (w/'shim.c').write_text(shim)
        subprocess.run(['cc','-shared','-fPIC','-O2',f'-I{w}',f'-I{core}',str(w/'shim.c'),str(core/'simglb.c'),*map(str,sorted(core.glob('simz80*.c'))),'-o',str(w/'core.so')],check=True)
        lib=C.CDLL(str(w/'core.so'));mem=(C.c_ubyte*65536).in_dll(lib,'memory')
        regs={n:C.c_ubyte.in_dll(lib,n) for n in ('A','B','C','D','E','H','L')}
        words={n:C.c_ushort.in_dll(lib,n) for n in ('SP','IX','IY','minimum_sp')}
        state={};maximum=0
        @C.CFUNCTYPE(None,C.c_int)
        def hook(kind):
            try:
                assert kind==0
                fn=regs['C'].value
                if fn==6 and regs['E'].value==255:
                    assert state['keys']
                    value=state['keys'].pop(0);state['reads'].append(value)
                elif fn in (2,6):state['text'].append(regs['E'].value);value=0
                else:raise AssertionError(fn)
                regs['A'].value=value
                for n in ('B','C','D','E','H','L'):regs[n].value=0xdd
                words['IX'].value=0xaaaa;words['IY'].value=0xbbbb
            except BaseException as e:
                state['error']=e;regs['A'].value=ord('N')
        lib.set_hooks.argtypes=[C.c_ushort,C.c_ushort,C.CFUNCTYPE(None,C.c_int)]
        lib.test_run.argtypes=[C.c_ushort,C.c_int];lib.set_hooks(5,0xfffe,hook)
        def run(entry,key):
            nonlocal maximum
            C.memset(mem,0,65536);mem[256:256+len(image)]=image;mem[5]=0xc9
            for n in ('HUSH','FOPEN','CNTENAB','D_CAPTURE'):mem[address(listing,n)]=0
            words['SP'].value=0xf000;words['IX'].value=0x1234;words['IY'].value=0x5678
            state.update(keys=[key,ord('N'),ord('!')],text=bytearray(),reads=[],error=None)
            result=lib.test_run(address(listing,entry),100000)
            assert result>=0 and state['error'] is None,(result,state)
            assert words['SP'].value==0xf000
            assert words['IX'].value==0x1234 and words['IY'].value==0x5678
            maximum=max(maximum,0xf000-words['minimum_sp'].value)
            return regs['A'].value==ord('Y'),bytes(state['text']),state['keys'],state['reads']
        for key in range(256):assert run('CHIN',key)==run('D_ASK_KEY',key),key
    for label in ('EDITNEW','UE_INIT','UP_RUN','UR_DRAW'):assert not re.search(r'\b'+label+':',listing),label
    out=ROOT/'build/dasm-shared-choice';out.mkdir(parents=True,exist_ok=True)
    report={'status':'PASS','raw_byte_cases':256,'maximum_prompt_stack_bytes':maximum,'bytes':len(image),'sha256':hashlib.sha256(image).hexdigest(),'scope':'Y approval, echo, one-key consumption, hostile BDOS clobbers, caller SP/IX/IY; file operations covered by test_dasm'}
    (out/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(report)

if __name__=='__main__':main()
