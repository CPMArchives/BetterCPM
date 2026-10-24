#!/usr/bin/env python3
"""Audit rename return handling with an isolated, one-shot BDOS fault gate."""
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from build_ccp import assemble
from test_z80pack_sysgen_install import session
ROOT=Path(__file__).resolve().parents[1]


def instrument(image,work,fail):
    # Reserve the gate above the TPA ceiling; neither editor may allocate it.
    # The input binary is never changed on disk. Restore both vectors at exit.
    source='''        ASEG
        ORG 0C000H
GATE:
        LD A,C
        CP 23
        JP NZ,CHAIN
        LD A,(COUNT)
        DEC A
        LD (COUNT),A
        JP NZ,CHAIN
        LD A,255
        RET
CHAIN:  JP 0
COUNT:  DB FAIL
        ORG 0C080H
CLEAN:
        LD HL,(WCHAIN+1)
        LD (1),HL
        LD HL,(CHAIN+1)
        LD (6),HL
WCHAIN: JP 0
        ORG 0C100H
INIT:
        LD HL,(6)
        LD (CHAIN+1),HL
        LD HL,0C000H
        LD (6),HL
        LD HL,(1)
        LD (WCHAIN+1),HL
        LD HL,0C080H
        LD (1),HL
        LD HL,SAVED
        LD DE,0100H
        LD BC,3
        LDIR
        JP 0100H
SAVED: DB FIRST
        END
'''.replace('DB FAIL',f'DB {fail}').replace('DB FIRST','DB '+','.join(str(b) for b in image[:3]))
    gate=assemble(Path.home()/'bin/z80asm',source,work/'gate.bin',work/'gate.lst',0xc000)
    out=bytearray(image);out.extend(bytes(0xc000-256-len(out)));out.extend(gate)
    out[:3]=bytes((0xc3,0,0xc1))
    path=work/'EDTEST.COM';path.write_bytes(out);return path


def main():
    template=Path.home()/'projects/git/z80pack/cpmsim/disks/library/cpm22-1.dsk'
    assert hashlib.sha256(template.read_bytes()).hexdigest()=='86ac7cb1bdd6bac05fe6299b50f94cb26a047022ce00135fbecf7bbc5d3303d2'
    oracle=ROOT/'third_party/dri-ed/ED-CPM22-reference.COM'
    assert hashlib.sha256(oracle.read_bytes()).hexdigest()=='adeeb92c897bd6a07579f06d163bd6ded549842203a5459c88a93d26c65fe85f'
    parent=ROOT/'build/ed-development/rename';parent.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix='run-',dir=parent));results=[]
    for kind,image in [('dri',oracle.read_bytes()),('better',(ROOT/'build/ed-development/EDDEV.COM').read_bytes())]:
        cases=[('E',0),('E',1),('E',2)]
        if kind=='better':cases += [('H',1),('H',2)]
        for command,fail in cases:
            here=work/f'{kind}-{command}-{fail}';here.mkdir();disks=here/'disks';disks.mkdir()
            disk=disks/'drivea.dsk';shutil.copy2(template,disk)
            binary=instrument(image,here,fail)
            seed=here/'seed.txt';seed.write_bytes(b'OLD\r\n\x1a')
            def tool(*args):return subprocess.run(args,cwd=here,check=True,stdout=subprocess.PIPE).stdout
            bye=here/'BYE.COM'
            tool('cpmcp','-f','ibm-3740',str(disk),'0:bye.com',str(bye))
            tool('cpmrm','-f','ibm-3740',str(disk),'0:*')
            for host,name in [(bye,'BYE.COM'),(binary,'EDTEST.COM'),(seed,'CASE.TXT')]:tool('cpmcp','-f','ibm-3740',str(disk),str(host),'0:'+name)
            trace=session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',disks,[
                (b'EDTEST CASE.TXT\r',b'*',10),(b'iNEW\x1a\r',b'*',10),
                (command.encode()+b'\r',b'A>',10),(b'BYE /Y\r',b'System halted',10)],here/'transcript.bin',initial_prompt=b'A>')
            listing=tool('cpmls','-f','ibm-3740',str(disk)).decode()
            # This one-record fixture deliberately inspects directory entries:
            # DRI can create duplicate names, which cpmcp refuses to extract.
            # IBM 3740: two reserved 26-sector tracks, 1K blocks, 64 entries.
            raw=disk.read_bytes();base=2*26*128;files={}
            for slot in range(64):
                entry=raw[base+slot*32:base+(slot+1)*32]
                if entry[0]!=0 or entry[1:9]!=b'CASE    ':continue
                assert entry[12]==0 and entry[14]==0 and entry[15]<=8
                name='case.'+bytes(b&127 for b in entry[9:12]).decode().lower()
                # Sector skew is cpmtools' responsibility. Rename this entry
                # uniquely on a disposable extraction copy, preserving every
                # allocation/record field and the original audit disk.
                unique=f'R{slot:07d}'
                copy=bytearray(raw);copy[base+slot*32+1:base+slot*32+9]=unique.encode()
                extract_disk=here/f'extract-{slot}.dsk';extract_disk.write_bytes(copy)
                target=here/f'entry-{slot}.bin'
                ext=bytes(b&127 for b in entry[9:12]).decode()
                tool('cpmcp','-f','ibm-3740',str(extract_disk),'0:'+unique+'.'+ext,str(target))
                files.setdefault(name,[]).append(target.read_bytes().hex())
            results.append({'editor':kind,'command':command,'fail_rename':fail,'listing':listing,'files':files,'trace_hex':trace.hex()})
    # The control confirms the gate does not change ordinary output. Keep
    # duplicate directory names visible rather than accepting cpmcp's first hit.
    controls={r['editor']:r['files'] for r in results if r['fail_rename']==0}
    assert controls['dri']==controls['better']
    old=controls['dri']['case.bak'][0];new=controls['dri']['case.txt'][0]
    assert bytes.fromhex(old).split(b'\x1a')[0]==b'OLD\r\n'
    assert bytes.fromhex(new).split(b'\x1a')[0]==b'NEWOLD\r\n'
    expected={
        ('dri',0):{'case.bak':[old],'case.txt':[new]},
        ('dri',1):{'case.txt':[old,new]},
        ('dri',2):{'case.bak':[old],'case.$$$':[new]},
        ('better',0):{'case.bak':[old],'case.txt':[new]},
        ('better',1):{'case.txt':[old],'case.$$$':[new]},
        ('better',2):{'case.bak':[old],'case.$$$':[new]},
    }
    message=b'Rename failed. Edited text retained in work file.'
    for row in results:
        assert (message in bytes.fromhex(row['trace_hex']))==(row['editor']=='better' and row['fail_rename']!=0)
        assert row['files']==expected[row['editor'],row['fail_rename']],row
        for name,entries in row['files'].items():
            assert row['listing'].lower().split().count(name)==len(entries)
    (work/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    for row in results:
        print(row['editor'],row['command'],row['fail_rename'],{k:[bytes.fromhex(v).split(b'\x1a')[0] for v in values] for k,values in row['files'].items()})
    print(f'PASS: eight E/H rename control/fault cases, exact records and directory-entry counts; {work}')


if __name__=='__main__':main()
