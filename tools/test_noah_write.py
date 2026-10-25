#!/usr/bin/env python3
"""Focused NOAH LBR-write CLI and transaction qualification on the real Z80 core."""
import ctypes as C
from pathlib import Path
import shutil
import subprocess
from build_noah import build
from test_noah import Noah
from test_usq import SHIM
from test_usq_com import diskkey
from test_lbr import archive, entry, with_crcs
from test_lbr_write import members

ROOT = Path(__file__).resolve().parents[1]


def machine():
    work = ROOT / 'build/noah-lbr-writes/cli'
    work.mkdir(parents=True, exist_ok=True)
    image = build(Path.home() / 'bin/z80asm', work)
    core = Path.home() / 'projects/git/z80pack/z80core'
    if not (work / 'core.so').exists():
        (work / 'sim.h').write_text('#define DEF_CPU Z80\n#define EXCLUDE_I8080\n')
        for name in ('simmem.h','simport.h'):
            shutil.copy2(core.parent / 'z80sim/srcsim' / name, work / name)
        shim = SHIM.replace('int test_run(', 'WORD minimum_sp;\nint test_run(')
        shim = shim.replace(' PC=address;', ' minimum_sp=SP; PC=address;')
        shim = shim.replace('  if(PC==65535)', '  if(SP<minimum_sp) minimum_sp=SP;\n  if(PC==65535)')
        (work / 'shim.c').write_text(shim)
        subprocess.run(['cc','-shared','-fPIC','-O2',f'-I{work}',f'-I{core}',str(work/'shim.c'),str(core/'simglb.c'),*map(str,sorted(core.glob('simz80*.c'))),'-o',str(work/'core.so')],check=True)
    m = Noah(C.CDLL(str(work/'core.so')),image,(work/'noah.lst').read_text(errors='replace'))
    m.instruction_budget = 30000000
    return m


def tests(m):
    lib = diskkey(1,'TEST.LBR')
    src = diskkey(2,'BINARY.DAT',7)
    binary = bytes(range(256))
    output=m.run('/ADD TEST.LBR B7:BINARY.DAT',{src:binary})
    assert 'published' in output, output
    raw=m.files[lib]
    assert raw[int.from_bytes(raw[14:16],"little")*128:]==binary and members(raw)[0][1:12]==b'BINARY  DAT'
    assert m.files[src]==binary and not m.opened
    output=m.run('/TEST TEST.LBR',{lib:raw})
    assert 'Integrity checks complete' in output,output
    original=with_crcs(archive([entry(b'BINARY  DAT')],b'X'*128))
    output=m.run('/ADD /Y TEST.LBR B7:BINARY.DAT',{lib:original,src:binary})
    assert 'published' in output,output
    replaced=m.files[lib]
    assert replaced[128:256]==b'X'*128 and replaced[256:]==binary
    assert [r[0] for r in members(replaced)]==[254,0]
    output=m.run('/REMOVE /Y TEST.LBR BINARY.DAT',{lib:replaced})
    assert 'published' in output,output
    removed=m.files[lib]
    assert removed[128:]==replaced[128:] and all(r[0]==254 for r in members(removed))
    output=m.run('/COMPACT /Y TEST.LBR',{lib:removed})
    assert 'published' in output,output
    assert len(m.files[lib])==128 and not members(m.files[lib])
    for opts in ('','/COMPACT','/CAPACITY=8'):
        output=m.run(f'/ADD /Y {opts} TEST.LBR B7:NONE.*',{lib:original,src:binary})
        assert not m.created and m.files[lib]==original,output
    for tamper in (True,'append','truncate'):
        output=m.run('/ADD /Y TEST.LBR B7:BINARY.DAT',{lib:original,src:binary},tamper=tamper)
        assert 'published' not in output and m.files[lib]==original,output
    for fail in ('write','make','rename','close_output','read'):
        output=m.run('/ADD /Y TEST.LBR B7:BINARY.DAT',{lib:original,src:binary},failures={fail:1})
        assert 'published' not in output and m.files[lib]==original,(fail,output)
    output=m.run('/ADD /Y TEST.LBR B7:BINARY.DAT',{lib:original,src:binary},failures={'read':4})
    assert 'published' not in output and m.files[lib]==original and not m.created,output
    output=m.run('/ADD /Y TEST.LBR B7:BINARY.DAT',{lib:b'bad archive',src:binary})
    assert not m.opened and not m.created and m.files[lib]==b'bad archive',output
    output=m.run('/ADD /Y TEST.LBR TEST.LBR',{lib:original})
    assert 'target excluded' in output and m.files[lib]==original and not m.created,output
    # Decisions and explicit limits are resolved before staging.
    output=m.run('/ADD TEST.LBR B7:BINARY.DAT',{lib:original,src:binary},keys='N')
    assert m.files[lib]==original and not m.created and not m.opened,output
    output=m.run('/ADD /COMPACT /Y NEW.LBR B7:BINARY.DAT',{src:binary})
    assert 'published' in output,output
    output=m.run('/ADD /CAPACITY=1 /Y NEW.LBR B7:BINARY.DAT',{src:binary})
    assert 'published' in output and int.from_bytes(m.files[diskkey(1,'NEW.LBR')][14:16],'little')==1,output
    more={src:binary,diskkey(2,'OTHER.DAT',7):b'Z'*128}
    output=m.run('/ADD /CAPACITY=1 /Y NEW.LBR B7:*.DAT',more)
    assert 'published' not in output and not m.created,output
    for tail in ('/ADD /REMOVE TEST.LBR B7:*.DAT','/ADD /CAPACITY=262140 TEST.LBR B7:*.DAT',
                 '/ADD /CAPACITY=1 /CAPACITY=2 TEST.LBR B7:*.DAT',
                 '/CAPACITY=7 /REMOVE TEST.LBR *.*','/ADD [A0,B0]:TEST.LBR B7:*.DAT',
                 '/COMPACT /FORMAT=LBR TEST.LBR','/ADD /FORMAT=ARK NEW.LBR B7:*.DAT'):
        output=m.run(tail,{lib:original,src:binary})
        assert 'Usage:' in output and not m.created and not m.renamed,output
    output=m.run('/REMOVE /COMPACT /Y TEST.LBR NONE.*',{lib:original})
    assert 'No members matched' in output and m.files[lib]==original and not m.created,output
    output=m.run('/ADD /Y /R TEST.LBR B7:BINARY.DAT',{lib:original,src:binary},attributes={lib:1})
    assert m.files[lib]==original and not m.created,output
    output=m.run('/ADD /R TEST.LBR B7:BINARY.DAT',{lib:original,src:binary},attributes={lib:1},keys='YY')
    assert 'published' in output and m.attrs[lib]&1 and not m.opened,output
    output=m.run('/ADD /Y TEST.LBR B7:BINARY.DAT',{lib:original,src:binary},keys='C',cancel_poll=6)
    assert m.files[lib]==original and 'published' not in output,output
    output=m.run('/ADD /Y TEST.LBR B7:BINARY.DAT',{src:binary},tpa=0x7000)
    assert 'Insufficient transient memory' in output and not m.created,output
    for ceiling in (0xc501,0xca01):
        output=m.run('/ADD NEW.LBR B7:BINARY.DAT',{src:binary},tpa=ceiling)
        assert 'published' in output,output
    # Same member name from different users: latest accepted candidate wins;
    # the earlier accepted version remains as a deleted entry without rebuild.
    duplicate={diskkey(2,'SAME.DAT',0):b'A'*128,diskkey(2,'SAME.DAT',1):b'B'*128}
    output=m.run('/ADD /Y NEW.LBR B[0,1]:SAME.DAT',{**duplicate,diskkey(1,'NEW.LBR'):with_crcs(archive([],b'',sectors=2))})
    assert 'published' in output,output
    rows=members(m.files[diskkey(1,'NEW.LBR')])
    assert [r[0] for r in rows]==[254,0],rows
    print(f'PASS: {m.cases} LBR-write CLI cases; max intercepted stack {m.max_stack} bytes')


if __name__=='__main__':
    tests(machine())
