#!/usr/bin/env python3
"""Check PATCH's paired package, corresponding source and acceptance refusals."""
from pathlib import Path
import argparse
import copy
import io
import json
import tarfile
import zipfile
from patch_distribution import sha, validate_acceptance


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--package', type=Path, required=True)
    a = p.parse_args()
    with zipfile.ZipFile(a.package/'BetterCPM-Utilities-package.zip') as package:
        native = package.read('PATCH-NATIVE.MAC')
        provenance = json.loads(package.read('PATCH-Build-Provenance.json'))
        binary = (Path(__file__).resolve().parents[1]/'build/utilities/PATCH.COM').read_bytes()
        assert provenance['artifact']['sha256'] == sha(binary)
        with tarfile.open(fileobj=io.BytesIO(package.read('BetterCPM-TED-SOURCE.tar.gz')),mode='r:gz') as source:
            for name,wanted in provenance['input_record']['inputs']['files'].items():
                assert sha(source.extractfile('BetterCPM-source/'+name).read()) == wanted,name
        for target,filename in (('z80pack','BetterCPM-NOAH-z80pack-332K.dsk'),
                                ('trs80gp','BetterCPM-NOAH-trs80gp-80T-DS-800K.dmk')):
            image = package.read(filename)
            report = json.loads(package.read(filename+'.json'))
            assert report['sha256'] == sha(image)
            row = next(x for x in report['included'] if x['name']=='PATCH.COM')
            assert row['sha256'] == sha(binary) and row['bytes'] == len(binary)
            assert report['patch_companions']['PATCH-NATIVE.MAC'] == sha(native)
            assert report['component_acceptance']['PATCH.COM']['status'] == 'PENDING_RELEASE_ACCEPTANCE'
            assert any(x.startswith('PATCH ') for x in report['pending'])
            # An otherwise complete receipt cannot qualify another image,
            # another COM, or a run lacking the native/source/immutability checks.
            good = {'patch_acceptance':'PASS','binary':{'sha256':sha(binary)},
                    'platforms':{target:{'status':'PASS','utilities_sha256':sha(image),
                        'system_sha256':'1'*64,'utilities_unchanged':True,
                        'fixtures_unchanged':True,'native_cross_parity':True}}}
            validate_acceptance(good,{'PATCH.COM':binary},target,image)
            for field in ('status','utilities_sha256','system_sha256','utilities_unchanged',
                          'fixtures_unchanged','native_cross_parity'):
                bad = copy.deepcopy(good)
                bad['platforms'][target][field] = 'FAIL' if field=='status' else False
                try:
                    validate_acceptance(bad,{'PATCH.COM':binary},target,image)
                except ValueError:
                    pass
                else:
                    raise AssertionError('accepted incomplete proof: '+field)
            try:
                validate_acceptance(good,{'PATCH.COM':binary+b'X'},target,image)
            except ValueError:
                pass
            else:
                raise AssertionError('accepted a different binary')
    print('PATCH paired packaging, source closure and acceptance refusals: PASS')


if __name__ == '__main__':
    main()
