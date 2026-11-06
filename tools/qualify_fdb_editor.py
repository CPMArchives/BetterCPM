"""Exercise capture, editing and confirmed active binding apply on private media."""
from fdb_qualification_media import stage, startup, audit
import argparse
import re
import shutil
from pathlib import Path
from build_distribution import construct, geometry
from build_fdb import build
from build_fdf_catalog import catalogue_payload
from build_montezuma_extended_790k import build as make_dmk
from build_ccp import assemble
from run_trs80_command import DEFAULT_EMULATOR, key_args
from test_sysgen_install import screen
from test_z80pack_sysgen_install import session
from trs80gp_launch import run

def state_probe(out, *, clear=False):
    """Snapshot only through the public API, then return on the CCP stack."""
    source = """        ASEG
        ORG 100H
        LD HL,BUFFER
        LD (POS),HL
        LD B,1
OPLOOP: LD C,0
DRLOOP: PUSH BC
        LD A,C
        LD (REQUEST),A
        LD DE,REQUEST
        LD C,181
        CALL 5
        LD A,L
        OR A
        JR NZ,FAILED
        POP BC
        PUSH BC
        LD A,B
        CP 1
        LD B,6
        JR Z,BYTES
        LD B,64
BYTES:  LD HL,REQUEST+1
        LD DE,(POS)
NEXT:   LD A,(HL)
        RRCA
        RRCA
        RRCA
        RRCA
        CALL HEX
        LD A,(HL)
        CALL HEX
        INC HL
        DJNZ NEXT
        LD (POS),DE
        POP BC
        INC C
        LD A,C
        CP 4
        JR NZ,DRLOOP
        LD A,B
        CP 3
        LD B,3
        JR NZ,OPLOOP
        LD DE,REPORT
        LD C,9
        JP 5
FAILED: POP BC
        RET
HEX:    AND 15
        ADD A,48
        CP 58
        JR C,PUT
        ADD A,7
PUT:    LD (DE),A
        INC DE
        RET
POS:    DW 0
REQUEST:DS 80
REPORT: DB 'STATE '
BUFFER: DS 560
        DB ' ENDSTATE',13,10,'$'
        END
"""
    if clear:
        source=source.replace('        ORG 100H\n', '        ORG 100H\n'
            '        LD HL,(1)\n        LD DE,63\n        ADD HL,DE\n'
            '        LD A,4\n        CALL CLEARJUMP\n')
        source=source.replace('        END\n', 'CLEARJUMP:JP (HL)\n        END\n')
    return assemble(Path.home()/'bin/z80asm',source,out/'STATE.COM',out/'state.lst',0x100)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system-image',type=Path)
    parser.add_argument('--target', choices=('z80pack','trs80gp'), required=True)
    parser.add_argument('--build-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--simulator', type=Path)
    a = parser.parse_args()
    root, out = a.build_root.resolve(), a.output.resolve()
    out.mkdir(parents=True)
    names = [('FDB.COM',build(destination=out)), ('DISK.FDB',catalogue_payload()),
             ('RCP.CPX',(root/'build/cpx/RCP.CPX').read_bytes()), ('STATE.COM',state_probe(out))]
    if a.target == 'z80pack':
        names.append(('BYE.COM',(root/'build/z80pack-tools/BYE.COM').read_bytes()))
    raw = construct(a.target, root, out, [({'name':n,'user':0},d) for n,d in names],
                    geometry(a.target,root),'')
    stage(a.target,raw,a.system_image,names,out)
    steps = [('STATE','A0>'), ('FDB','Your choice: [ ]'), ('A','Logical drive B, C or D:'),
             ('B','Q Back:'), ('3','Q Back:'), ('E','Value:'),
             ('100','Q Back:'), ('V','Format validates.')]
    for drive in 'DCB':
        steps += [('S','other Cancel:'), ('D','Logical drive B, C or D:'),
                  (drive,'(Y/N)?'), ('Y','Active drive binding updated.')]
    steps += [('Q','Your choice: [ ]'), ('Q','C Cancel:'), ('D','A0>'), ('STATE','A0>')]
    if a.target == 'z80pack':
        disks=out/'disks';disks.mkdir()
        image=disks/'drivea.dsk';shutil.copy2(raw,image)
        trace=session(a.simulator.resolve(), disks,
                      [((k+'\r').encode(), (b'A0>_ ' if msg=='A0>' else msg.encode()), 40)
                       for k,msg in steps]+[(b'BYE /Y\r',b'System halted',15)],out/'trace')
        states=re.findall(rb'STATE ([0-9A-F]{560})',trace)
        if a.system_image:
            audit(a.target,a.system_image,image,out)
        else:
            assert image.read_bytes()==raw.read_bytes()
    else:
        image=out/'test.dmk';original=make_dmk(raw.read_bytes());image.write_bytes(original)
        states=[]
        for label, commands in [('before',steps[:1]), ('edited',steps[1:])]:
            here=out/label
            here.mkdir()
            cmd=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-d0',str(image),'-id','3000','-itime','0']
            if a.system_image:
                cmd=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-ktx','-d0',str(image),
                     '-id','4000','-itime','15000','-iw','Type TYPE README.TXT for more','-id','4000']
            for k,msg in startup(a.target,a.system_image)+commands:
                wait_for='ENDSTATE' if k=='STATE' else ('A0> ' if msg=='A0>' else msg)
                cmd+=key_args(k+'\r')+['-iw',wait_for,'-id','3000' if msg=='A0>' else '200'] + (['-it'] if a.system_image else [])
            run(cmd+['-it','-ix'],cwd=here,check=True,timeout=900 if a.system_image else 300)
            captures=sorted(here.glob('trs80-text-*.bin'),key=lambda p:int(p.stem.rsplit('-',1)[1]))
            matches=[m[1] for p in captures for m in re.finditer(r'STATE ([0-9A-F]{560}) ENDSTATE',screen(p).replace('\n',''))]
            assert matches,'missing complete public API snapshot'
            states.append(matches[-1])
        if a.system_image:
            after=out/'after.raw';after.write_bytes(__import__('add_cpm_file_to_dmk').extract_raw(image.read_bytes()))
            audit(a.target,a.system_image,after,out)
        else:
            assert image.read_bytes()==original
    assert len(states)==2
    before, after=[bytes.fromhex(s.decode() if isinstance(s,bytes) else s) for s in states]
    expected=bytearray(before)
    for drive in range(1, 4):
        offset=24+drive*64
        expected[offset+1:offset+64]=before[24+64+1:24+128]
        expected[offset+6:offset+8]=(100).to_bytes(2,'little')
    assert before != expected
    assert after==bytes(expected)
    import json,hashlib
    (out/'result.json').write_text(json.dumps({'status':'PASS','target':a.target,
        'com_sha256':hashlib.sha256(names[0][1]).hexdigest(),
        'scope':'B capture,DSM edit,confirmedB-D apply,physical selectors,A andcold defaults preserved',
        'before_state':before.hex(),'after_state':after.hex()},indent=2)+'\n')
    print('PASS',a.target,'B capture, DSM edit, confirmed B-D apply, physical mappings, A and cold media preserved')

if __name__=='__main__':
    main()
