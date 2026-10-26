#!/usr/bin/env python3
"""Bind SEARCH qualification to its exact program, selected inputs and paired media."""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile
from search_source import ROOT
from component_development import select

sha=lambda data:hashlib.sha256(data).hexdigest()


def collect(campaign,inventory,output):
    evidence=json.loads((campaign/'evidence.json').read_text())
    audit=json.loads(inventory.read_text())
    image=(ROOT/'build/utilities/SEARCH.COM').read_bytes()
    record=json.loads((ROOT/'build/utilities/SEARCH-build-report.json').read_text())
    assert record['artifact']['sha256']==evidence['binary_sha256']==sha(image)
    assert audit['status']=='PASS'
    assert not record['display_selection']['development']
    for target in ('z80pack','trs80gp'):
        state=select('utility:SEARCH',Path.home()/'bin/z80asm',target=target)
        assert state['input_state']=='unchanged' and not state['development']
    for name,wanted in record['input_record']['inputs']['files'].items():
        assert sha((ROOT/name).read_bytes())==wanted,('source changed',name)
    native_source=(ROOT/'build/utilities/SEARCH-NATIVE.MAC').read_bytes()
    assert (campaign/'cpmsim/SEARCH.MAC').read_bytes()==native_source
    assert (campaign/'model4/SEARCH.MAC').read_bytes()==native_source
    platforms={}
    for target,key in [('z80pack','cpmsim'),('trs80gp','model4')]:
        proof=evidence[key]
        assert proof['result']=='PASS' and proof['native_cross_parity'] and proof['utilities_unchanged']
        assert proof['fixture_contents_unchanged']
        assert audit['platforms'][target]['image_sha256']==proof['utilities_sha256']
        assert audit['platforms'][target]['files_sha256']['SEARCH.COM']==sha(image)
        resources=evidence[key+'_resources']
        assert resources['advertised_tpa_payload_bytes']==8192 and resources['stack_watermark_bytes']<=512
        native=(campaign/('cpmsim/NATIVE.COM' if key=='cpmsim' else 'model4/native/NATIVE.COM')).read_bytes()
        assert native[:len(image)]==image and set(native[len(image):])<={0,26}
        platforms[target]={'status':'PASS','system_sha256':evidence[key+'_system_input_sha256'],
            'utilities_sha256':proof['utilities_sha256'],'utilities_unchanged':True,
            'fixtures_unchanged':True,'native_cross_parity':True,'native_file_sha256':sha(native),
            **resources,'directory_inventory':audit['platforms'][target]['exact_membership']}
    files={}
    for p in sorted(campaign.rglob('*')):
        if p.is_file():files['campaign/'+str(p.relative_to(campaign))]=p.read_bytes()
    files['inventory.json']=inventory.read_bytes()
    files['SEARCH-build-report.json']=(ROOT/'build/utilities/SEARCH-build-report.json').read_bytes()
    files['source-inputs.json']=json.dumps(record['input_record'],indent=2).encode()+b'\n'
    files['EVIDENCE-MANIFEST.json']=json.dumps({name:sha(data) for name,data in sorted(files.items())},indent=2).encode()+b'\n'
    content=io.BytesIO()
    with tarfile.open(fileobj=content,mode='w') as archive:
        for name,data in sorted(files.items()):
            entry=tarfile.TarInfo(name);entry.size=len(data);entry.mode=0o644;entry.mtime=0
            archive.addfile(entry,io.BytesIO(data))
    packed=gzip.compress(content.getvalue(),mtime=0)
    output.mkdir(parents=True,exist_ok=True)
    archive_name='SEARCH-Utilities-Evidence.tar.gz'
    (output/archive_name).write_bytes(packed)
    receipt={'schema':1,'search_acceptance':'PASS','scope':'SEARCH 1.0 revision 001 on exact paired RAM emulator media; whole Utilities release separate',
        'binary':record['artifact'],'identity':record['identity'],'input_fingerprint':record['input_record']['fingerprint'],
        'native_source_sha256':sha(native_source),
        'platforms':platforms,'evidence':{'name':archive_name,'sha256':sha(packed),'bytes':len(packed)},
        'limits':['Physical hardware and arbitrary third-party BIOS/interrupt stack depth not qualified',
            '80x24 console; Model 4 command text supplied by SUBMIT; physical Ctrl-C pager suppression verified',
            'BDOS Bad Sector Ctrl-C can warm boot without returning totals; directory replay remains quadratic']}
    (output/'SEARCH-Utilities-Acceptance.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('campaign','inventory','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    result=collect(args.campaign,args.inventory,args.output)
    print('PASS SEARCH exact-artifact paired Utilities acceptance:',result['binary']['sha256'])
