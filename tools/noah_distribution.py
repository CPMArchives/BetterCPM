"""Build matching NOAH companion Utilities volumes without changing primary media."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from fdf_format import select_fdf
from build_z80pack_image import disk_definition, DEFAULT_FORMAT
from convert_fdf_image import raw_to_dmk, dmk_to_raw

COMPONENTS = {'NOAH.COM':'build/utilities/NOAH.COM',
              'NOAH.OVL':'build/utilities/NOAH.OVL',
              'NOAH.TXT':'src/distribution/NOAH.TXT',
              'PATCH.COM':'build/utilities/PATCH.COM',
              'PATCH.TXT':'src/distribution/PATCH.TXT'}
COMPONENTS.update({'COMPARE.COM':'build/utilities/COMPARE.COM',
                   'COMPARE.TXT':'src/distribution/COMPARE.TXT'})
COMPONENTS.update({'SUPPDISK.FDF':'metadata/supplemental/1.0.1/SUPPDISK.FDF',
                   'SUPPDISK.FDB':'metadata/supplemental/1.0.1/SUPPDISK.FDB',
                   'SUPPDISK.TXT':'src/distribution/SUPPDISK.TXT'})
sha = lambda data: hashlib.sha256(data).hexdigest()


def image_name(target):
    return 'BetterCPM-NOAH-'+target+('-332K.dsk' if target=='z80pack' else '-80T-DS-800K.dmk')


def acceptance_proof(target, files, image, receipt, acceptance, system_sha256=None):
    proof = {'status':'PENDING_RELEASE_ACCEPTANCE', 'sha256':sha(files['NOAH.COM']),
             'overlay_sha256':sha(files['NOAH.OVL'])}
    if receipt is not None:
        observed = receipt.get('platforms', {}).get(target, {})
        if (receipt.get('noah_acceptance')!='PASS' or observed.get('status')!='PASS'
                or observed.get('utilities_sha256')!=sha(image) or not observed.get('system_sha256')
                or (system_sha256 is not None and observed['system_sha256'] != system_sha256)
                or any(receipt['binaries'][n]['sha256']!=sha(files[n]) for n in ('NOAH.COM','NOAH.OVL'))):
            raise ValueError('NOAH acceptance differs from companion media: '+target)
        proof.update(status='PASS', evidence_sha256=sha(acceptance.read_bytes()),
                     paired_system_sha256=observed['system_sha256'])
    return proof


def companion_components(target):
    if target == 'z80pack':
        return {**COMPONENTS, 'HELP.LBR': 'build/help/HELP.LBR'}
    return COMPONENTS


def media(artifacts, acceptance=None):
    root = Path(artifacts)
    receipt = json.loads(acceptance.read_text()) if acceptance else None
    reports = []
    for target in ('z80pack','trs80gp'):
        files = {name:(root/path).read_bytes() for name,path in companion_components(target).items()}
        if not all(files.values()):
            raise ValueError('empty companion artifact')
        native = target=='trs80gp'
        fmt = select_fdf(root/'metadata/DISK.FDF',
                        'Montezuma Micro 80T DS DATA (80T, DS, DD, 800K)' if native else DEFAULT_FORMAT)
        definition = 'bettercpm-mm-80t-ds-data' if native else 'bettercpm-default'
        with tempfile.TemporaryDirectory(prefix='bettercpm-noah-media-') as temp:
            work = Path(temp)
            (work/'diskdefs').write_text(disk_definition(select_fdf(root/'metadata/DISK.FDF',DEFAULT_FORMAT)))
            raw = work/'noah.raw'
            raw.write_bytes(bytes([0xe5])*fmt.image_bytes)
            def run(*args):
                return subprocess.run(list(map(str,args)),cwd=work,check=True,capture_output=True)
            run('mkfs.cpm','-f',definition,raw)
            for name,data in files.items():
                source = work/name
                source.write_bytes(data)
                run('cpmcp','-T','raw','-f',definition,raw,source,'0:'+name)
                extracted = work/('after-'+name)
                run('cpmcp','-T','raw','-f',definition,raw,'0:'+name,extracted)
                actual = extracted.read_bytes()
                if (actual[:len(data)]!=data or not len(data)<=len(actual)<=(len(data)+127)//128*128
                        or not set(actual[len(data):])<={0,26}):
                    raise ValueError(f'NOAH media readback differs: {target} {name}, expected {len(data)}, actual {len(actual)}, prefix {actual[:len(data)]==data}, padding {set(actual[len(data):])}')
            run('fsck.cpm','-T','raw','-f',definition,'-n',raw)
            data = raw.read_bytes()
            image = raw_to_dmk(data,fmt) if native else data
            if native and dmk_to_raw(image,fmt)!=data:
                raise ValueError('NOAH DMK/raw round trip differs')
        proof = acceptance_proof(target, files, image, receipt, acceptance)
        report = {'target':target,'image':image_name(target),'sha256':sha(image),
                  'format':fmt.name,'status':'PROVISIONAL','volume':'NOAH companion Utilities Disk',
                  'included':[{'name':n,'bytes':len(b),'sha256':sha(b)} for n,b in files.items()],
                  'component_acceptance':{'NOAH.COM':proof,'PATCH.COM':{'status':'PENDING_RELEASE_ACCEPTANCE','sha256':sha(files['PATCH.COM'])}},
                  'pending':(['NOAH paired-media qualification pending'] if not receipt else [])+['PATCH paired-media qualification pending'],
                  'deferred':['interactive browser','ZIP','LZH/CrLZH selectors'],
                  'validation':'exact file readback, filesystem and DMK/raw round trip PASS; whole release acceptance separate'}
        report['component_acceptance']['COMPARE.COM']={'status':'PENDING_RELEASE_ACCEPTANCE','sha256':sha(files['COMPARE.COM'])}
        report['pending'].append('COMPARE paired-media qualification pending')
        reports.append((image_name(target),image,report))
    return reports
