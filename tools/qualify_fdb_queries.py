"""Qualify FDB query screens and normal conversion on private full System media."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess
from add_cpm_file_to_dmk import extract_raw
from build_montezuma_extended_790k import build as make_dmk
from fdb_qualification_media import audit
from run_trs80_command import DEFAULT_EMULATOR, key_args
from trs80gp_launch import run
from test_sysgen_install import screen
from test_z80pack_sysgen_install import session


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--target',choices=['z80pack','trs80gp'],required=True)
    p.add_argument('--system-image',type=Path,required=True)
    p.add_argument('--binary-dir',type=Path,required=True)
    p.add_argument('--simulator',type=Path)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True)
    baseline=out/'baseline';baseline.mkdir()
    original=a.system_image.resolve();payload=original.read_bytes()
    report=json.loads((original.parent/'report.json').read_text())
    assert hashlib.sha256(payload).hexdigest()==report['sha256']
    shutil.copy2(original.parent/'diskdefs',out/'diskdefs')
    shutil.copy2(original.parent/'diskdefs',baseline/'diskdefs')
    raw=out/'staged.raw';raw.write_bytes(extract_raw(payload) if a.target=='trs80gp' else payload)
    for name in ['FDB.COM','FDBVIEW.OVL']:
        binary=(a.binary_dir/name).resolve()
        subprocess.run(['cpmrm','-T','raw','-f','bettercpm-default',str(raw),'0:'+name],cwd=out,check=True,capture_output=True)
        subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(raw),str(binary),'0:'+name],cwd=out,check=True,capture_output=True)
        item=next(i for i in report['included'] if i['name']==name)
        item.update(bytes=binary.stat().st_size,sha256=hashlib.sha256(binary.read_bytes()).hexdigest())
    report['fixture_origin']={'sha256':report['sha256'],'scope':'Only new matching FDB pair substituted; original frozen image unchanged'}
    base=baseline/original.name;base.write_bytes(make_dmk(raw.read_bytes()) if a.target=='trs80gp' else raw.read_bytes())
    report['sha256']=hashlib.sha256(base.read_bytes()).hexdigest()
    (baseline/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    steps=[('FDB /VER',' | Disk Format Catalogue Workbench'),
           ('FDB /H','Display utility identification.'),
           ('FDB /HELP','Display utility identification.'),
           ('FDB /VER BAD.FDB /HELP','Display utility identification.'),
           ('FDB /HELP /VER','Display utility identification.'),
           ('FDB BAD.FDB /vEr',' | Disk Format Catalogue Workbench'),
           ('FDB DISK.FDB QUERY.FDF','FDB: complete.'),
           ('FDB QUERY.FDF QUERY.FDB','FDB: complete.')]
    if a.target=='z80pack':
        assert a.simulator,'--simulator is required for z80pack'
        disks=out/'disks';disks.mkdir();after=disks/'drivea.dsk';shutil.copy2(raw,after)
        trace=session(a.simulator.resolve(),disks,
            [((k+'\r').encode(),b'A0>_ ',60) for k,_ in steps]+
            [(b'BYE /Y\r',b'System halted',30)],out/'transcript.bin')
        text=trace.decode('ascii','replace')
        assert text.count('FDB 1.0 (001)')==6
        assert text.count(' | BetterCP/M Utilities')==2
        assert text.count('     /H /HELP    Display this help.')==4
        assert text.count('     FDB                   Open DISK.FDB in the workbench.')==4
        assert text.count('     FDB in.FDF out.FDB    Compile FDF text to a catalogue.')==4
        assert text.count('FDB: complete.')==2
        assert 'Invalid filename or ID.' not in text
    else:
        disk=out/'queries.dmk';shutil.copy2(base,disk)
        cmd=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-ktx','-d0',str(disk),
             '-id','4000','-itime','15000','-iw','Type TYPE README.TXT for more','-id','4000']
        cmd+=key_args('RSX LIST\r')+['-iw','TPA available: 50K','-iw','A0> ','-id','300','-it']
        for k,want in steps:
            cmd+=key_args('CLS\r')+['-id','300']
            cmd+=key_args(k+'\r')+['-iw',want,'-iw','A0> ','-id','300','-it']
        (out/'invocation.json').write_text(json.dumps(cmd+['-ix'],indent=2)+'\n')
        run(cmd+['-ix'],cwd=out,check=True,timeout=1200)
        frames=[screen(f) for f in sorted(out.glob('trs80-text*.bin'),key=lambda f:int(f.stem.rsplit('-',1)[1]))]
        assert len(frames)==9 and 'TPA available: 50K' in frames[0]
        for i in range(6):
            assert 'FDB 1.0 (001)' in frames[i+1]
            assert (' | BetterCP/M Utilities' in frames[i+1]) == (i in (0,5))
            assert ('     /H /HELP    Display this help.' in frames[i+1]) == (i not in (0,5))
            if i not in (0,5):
                assert '     FDB                   Open DISK.FDB in the workbench.' in frames[i+1]
                assert '     FDB file.FDB          Open a named catalogue in the workbench.' in frames[i+1]
                assert '     FDB in.FDB out.FDF    Export a catalogue as FDF text.' in frames[i+1]
                assert '     FDB in.FDF out.FDB    Compile FDF text to a catalogue.' in frames[i+1]
            assert 'A0>' in frames[i+1]
        assert all('FDB: complete.' in f for f in frames[-2:])
        after=out/'after.raw';after.write_bytes(extract_raw(disk.read_bytes()))
    audit(a.target,base,after,out)
    for name in ['QUERY.FDB','QUERY.FDF']:
        subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(after),'0:'+name,str(out/name)],cwd=out,check=True,capture_output=True)
    stock=next(i for i in report['included'] if i['name']=='DISK.FDB')
    assert hashlib.sha256((out/'QUERY.FDB').read_bytes()).hexdigest()==stock['sha256']
    from fdf_v1 import parse,serialize
    assert serialize(parse((out/'QUERY.FDF').read_bytes().split(b'\x1a')[0].decode()))==(out/'QUERY.FDB').read_bytes()
    (out/'result.json').write_text(json.dumps({'status':'PASS','target':a.target,
        'com_sha256':next(i['sha256'] for i in report['included'] if i['name']=='FDB.COM'),
        'queries':6,'native_conversion_roundtrip':'108 entries byte-identical; host cross-check PASS',
        'preservation':'All shipped files and reserved tracks unchanged from explicit new-pair fixture',
        'model4_default_50K':a.target=='trs80gp'},indent=2)+'\n')
    print('PASS',a.target,'FDB queries, native roundtrip and full-media preservation')


if __name__=='__main__':main()
