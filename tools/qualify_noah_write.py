#!/usr/bin/env python3
"""Native build parity and bounded LBR-write qualification on both platforms."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from build_noah import build, ROOT
from dasm_native import campaign
from qualify_noah_proof import verify_system
from test_lbr import archive, entry, with_crcs
from test_lbr_write import members


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--system',type=Path,required=True)
    p.add_argument('--utilities',type=Path,default=ROOT/'build/ted-qualified-utilities')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--platforms',nargs='+',default=['z80pack','trs80gp'])
    p.add_argument('--extent-only',action='store_true')
    p.add_argument('--reuse-native',type=Path)
    a=p.parse_args()
    if a.extent_only and not a.reuse_native: p.error('--extent-only requires --reuse-native')
    a.output=a.output.resolve();a.system=a.system.resolve();a.utilities=a.utilities.resolve()
    systems=verify_system(a.system,a.platforms)
    a.output.mkdir(parents=True,exist_ok=False)
    image=build(Path.home()/'bin/z80asm',a.output/'cross')
    binary=bytes(range(256))
    original=with_crcs(archive([entry(b'BINARY  DAT')],b'X'*128))
    files={'NOAHNAT.MAC':(a.output/'cross/NOAHNAT.MAC').read_bytes(),
           'BINARY.DAT':binary,'EMPTY.DAT':b'','LARGE.BIN':bytes(range(256))*80,
           'REPLACE.LBR':original,'REMOVE.LBR':original,'COMPACT.LBR':original}
    operations=['NOAHNAT /VER','NOAHNAT /ADD CREATED.LBR *.DAT',
        'NOAHNAT /ADD /Y REPLACE.LBR BINARY.DAT',
        'NOAHNAT /REMOVE /Y REMOVE.LBR BINARY.DAT',
        'NOAHNAT /REMOVE /COMPACT /Y COMPACT.LBR BINARY.DAT',
        'NOAHNAT /ADD /CAPACITY=1 LIMITED.LBR BINARY.DAT',
        'NOAHNAT /TEST CREATED.LBR','NOAHNAT /TEST REPLACE.LBR',
        'NOAHNAT /ADD LARGE.LBR LARGE.BIN','NOAHNAT /TEST LARGE.LBR']
    report={'scope':'LBR writes only; no browser, ARK or codecs','binary_sha256':sha(image),
            'image_bytes':len(image),'exclusive_memory_ceiling':256+len(image),
            'record_rounded_load_ceiling':256+(len(image)+127)//128*128,
            'verified_systems':systems,'platforms':{}}
    extract=['NOAHNAT.COM','CREATED.LBR','REPLACE.LBR','REMOVE.LBR','COMPACT.LBR','LIMITED.LBR','LARGE.LBR']
    if a.extent_only:
        operations=['NOAHNAT /ADD LARGE.LBR LARGE.BIN','NOAHNAT /TEST LARGE.LBR']
        extract=['NOAHNAT.COM','LARGE.LBR']
    for platform in a.platforms:
        prefix=['RSX UNLOAD ADM3A','RSX UNLOAD M4SCRN'] if platform=='trs80gp' else []
        inputs=dict(files)
        builds=['B:ZSM4 NOAHNAT=NOAHNAT','B:LINK NOAHNAT[A]']
        if a.reuse_native:
            prior=(a.reuse_native/platform/'after-NOAHNAT.COM').read_bytes()
            assert prior[:len(image)]==image, 'reused native output differs from current build'
            inputs['NOAHNAT.COM']=prior
            builds=[]
        if a.extent_only:
            inputs={'NOAHNAT.COM':prior,'LARGE.BIN':bytes(range(256))*80}
        commands=prefix+builds+operations
        log,outputs=campaign(platform,inputs,commands,a.output/platform,system=a.system,
            utilities=a.utilities,extract=extract,timeout=600)
        errors=re.findall(rb'Errors: +([0-9]+)',log)
        assert errors==([] if a.reuse_native else [b'0']),log[-4000:]
        native=outputs['NOAHNAT.COM']
        assert native[:len(image)]==image and len(native)==(len(image)+127)//128*128,'native parity'
        assert set(native[len(image):])<={26}
        if a.extent_only:
            large=outputs['LARGE.LBR']
            assert large[int.from_bytes(large[14:16],'little')*128:]==inputs['LARGE.BIN']
            from test_lbr_write import check_crc
            check_crc(large)
            assert b'Integrity checks complete' in log and b'update failed' not in log
            report['platforms'][platform]={'status':'PASS','cross_extent_bytes':20480,
                'native_build_reused_from':str(a.reuse_native/platform),
                'console_sha256':sha(log),'outputs':{n:sha(v) for n,v in outputs.items()}}
            (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
            print('PASS',platform,'cross-extent write and integrity audit',flush=True)
            continue
        created=outputs['CREATED.LBR'];rows=members(created)
        assert [r[1:12] for r in rows]==[b'BINARY  DAT',b'EMPTY   DAT']
        assert created[int.from_bytes(created[14:16],'little')*128:]==binary
        replaced=outputs['REPLACE.LBR']
        assert [r[0] for r in members(replaced)]==[254,0]
        assert replaced[128:256]==b'X'*128 and replaced[256:]==binary
        removed=outputs['REMOVE.LBR']
        assert members(removed)[0][0]==254 and removed[128:]==original[128:]
        assert len(outputs['COMPACT.LBR'])==128 and not members(outputs['COMPACT.LBR'])
        assert int.from_bytes(outputs['LIMITED.LBR'][14:16],'little')==1
        large=outputs['LARGE.LBR']
        assert large[int.from_bytes(large[14:16],'little')*128:]==files['LARGE.BIN']
        from test_lbr_write import check_crc
        check_crc(large)
        assert log.count(b'verified and published')==6,log[-6000:]
        assert b'Archive/read error' not in log and b'update failed' not in log
        report['platforms'][platform]={'status':'PASS','native_cross_parity':True,'cross_extent_bytes':20480,
            'console_sha256':sha(log),'outputs':{n:sha(v) for n,v in outputs.items()}}
        (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        print('PASS',platform,'native parity, creation/replacement/removal/compaction/capacity',flush=True)


if __name__=='__main__':main()
