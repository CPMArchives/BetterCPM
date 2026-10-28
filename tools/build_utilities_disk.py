#!/usr/bin/env python3
"""Assemble provisional Utilities media from selected owned and third-party components.

No third-party candidate is silently selected. The report lists remaining
manifest entries; these development images are not a completed release disk.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile
ROOT=Path(os.environ.get("BCPM_REPO",Path(__file__).resolve().parents[1])).resolve()
sys.path.insert(0,str(ROOT/"tools"))
from fdf_format import select_fdf
from build_z80pack_image import disk_definition, DEFAULT_FORMAT
from convert_fdf_image import raw_to_dmk, dmk_to_raw
COMPONENTS={'DDT.COM':'build/utilities/DDT.COM','DUMP.COM':'build/utilities/DUMP.COM','XSUB.COM':'build/utilities/XSUB.COM','BATCHIO.RSX':'build/rsx/BATCHIO.RSX','SQ.COM':'build/utilities/SQ.COM','USQ.COM':'build/utilities/USQ.COM','UNCR.COM':'build/utilities/UNCR.COM','CR.COM':'build/utilities/CR.COM','UNLZH.COM':'build/utilities/UNLZH.COM','LZH.COM':'build/utilities/LZH.COM'}
COMPONENTS.update({'ZSM4.COM':'third_party/zsm4/ZSM4.COM','LINK.COM':'third_party/dri-link/LINK.COM',
                   'TOOLINFO.TXT':'src/distribution/TOOLINFO.TXT',
                   'ZSM4COPY.TXT':'src/distribution/ZSM4COPY.TXT',
                   'LINKCOPY.TXT':'src/distribution/LINKCOPY.TXT'})
COMPONENTS.update({name+'.COM':'build/utilities/'+name+'.COM' for name in ('DASM','DSYM','DLINK')})
COMPONENTS.update({'DASM.TXT':'src/distribution/DASM.TXT','DASMCOPY.TXT':'src/distribution/DASMCOPY.TXT'})
COMPONENTS.update({'TED.COM':'build/utilities/TED.COM','TED.TXT':'src/distribution/TED.TXT','TEDCOPY.TXT':'src/distribution/TEDCOPY.TXT'})
COMPONENTS['SEARCH.COM']='build/utilities/SEARCH.COM'
COMPONENTS['CRCKSUM.COM']='build/utilities/CRCKSUM.COM'
COMPONENTS['MD5SUM.COM']='build/utilities/MD5SUM.COM'
PENDING=['TED final paired-media qualification pending','DASM tool set final release qualification pending','SEARCH final paired-media qualification pending','CRCKSUM final paired-media qualification pending','MD5SUM final paired-media qualification pending']
sha=lambda data:hashlib.sha256(data).hexdigest()


def validate_dasm_acceptance(receipt,files,target,image):
    proof=receipt['platforms'][target]
    if (receipt.get('dasm_acceptance')!='PASS' or proof.get('status')!='PASS'
        or proof['utilities_sha256']!=sha(image)
        or not proof.get('system_sha256')
        or any(receipt['binaries'][name]['sha256']!=sha(files[name])
               for name in ('DASM.COM','DSYM.COM','DLINK.COM'))):
        raise ValueError('DASM acceptance does not match packaged '+target)
    return proof


def validate_ted_acceptance(receipt,files,target,image):
    proof=receipt['platforms'][target]
    if (receipt.get('ted_acceptance')!='PASS' or proof.get('status')!='PASS'
        or proof['utilities_sha256']!=sha(image)
        or receipt['binary']['sha256']!=sha(files['TED.COM'])
        or not proof.get('system_sha256')):
        raise ValueError('TED acceptance does not match packaged '+target)
    return proof


def validate_search_acceptance(receipt,files,target,image):
    proof=receipt['platforms'][target]
    if (receipt.get('search_acceptance')!='PASS' or proof.get('status')!='PASS'
        or proof['utilities_sha256']!=sha(image)
        or receipt['binary']['sha256']!=sha(files['SEARCH.COM'])
        or not proof.get('system_sha256') or not proof.get('utilities_unchanged')
        or not proof.get('fixtures_unchanged') or not proof.get('native_cross_parity')):
        raise ValueError('SEARCH acceptance does not match packaged '+target)
    return proof


def build(output, artifacts=ROOT, ddt_acceptance=None, toolchain_acceptance=None, dasm_acceptance=None, ted_acceptance=None, noah_acceptance=None, search_acceptance=None, crc_acceptance=None, md5sum_acceptance=None):
    from toolchain_distribution import companions, validate_acceptance
    accompanying = companions(artifacts)
    from dasm_distribution import companions as dasm_companions
    analysis_companions=dasm_companions(artifacts)
    from ted_distribution import companions as ted_companions
    editor_companions=ted_companions(artifacts)
    from search_distribution import companions as search_companions
    search_source_companions=search_companions(artifacts,editor_companions,search_acceptance)
    from crc_distribution import companions as crc_companions, validate_acceptance as validate_crc_acceptance
    crc_source_companions=crc_companions(artifacts,editor_companions,crc_acceptance)
    from md5sum_distribution import companions as md5sum_companions, validate_acceptance as validate_md5sum_acceptance
    md5sum_source_companions=md5sum_companions(artifacts,editor_companions,md5sum_acceptance)
    from patch_distribution import companions as patch_companions
    patch_source_companions=patch_companions(artifacts,editor_companions)
    from compare_distribution import companions as compare_companions
    compare_source_companions=compare_companions(artifacts,editor_companions)
    files={name:(artifacts/path).read_bytes() for name,path in COMPONENTS.items()}
    if not all(files.values()):raise ValueError('empty Utilities artifact')
    accepted=json.loads(ddt_acceptance.read_text()) if ddt_acceptance else None
    tools_accepted=json.loads(toolchain_acceptance.read_text()) if toolchain_acceptance else None
    if accepted is not None:
        if accepted.get('ddt_utilities_acceptance')!='PASS' or accepted.get('ddt_sha256')!=sha(files['DDT.COM']):
            raise ValueError('DDT acceptance does not match current artifact')
    dasm_accepted=json.loads(dasm_acceptance.read_text()) if dasm_acceptance else None
    ted_accepted=json.loads(ted_acceptance.read_text()) if ted_acceptance else None
    search_accepted=json.loads(search_acceptance.read_text()) if search_acceptance else None
    crc_accepted=json.loads(crc_acceptance.read_text()) if crc_acceptance else None
    md5sum_accepted=json.loads(md5sum_acceptance.read_text()) if md5sum_acceptance else None
    reports=[]
    output.mkdir(parents=True,exist_ok=True)
    for target in ['z80pack','trs80gp']:
        native=target=='trs80gp'
        fmt=select_fdf(ROOT/'third_party/montezuma'/('DISK-INT.FDF' if native else 'DISK.FDF'), 'Montezuma Micro 80T DS DATA (80T, DS, DD, 800K)' if native else DEFAULT_FORMAT)
        definition='bettercpm-mm-80t-ds-data' if native else 'bettercpm-default'
        with tempfile.TemporaryDirectory(prefix='bettercpm-utilities-',dir='/private/tmp') as temp:
            work=Path(temp);(work/'diskdefs').write_text(disk_definition(select_fdf(ROOT/'third_party/montezuma/DISK.FDF',DEFAULT_FORMAT)))
            raw=work/'utilities.dsk';raw.write_bytes(bytes([0xE5])*fmt.image_bytes)
            def run(*args):
                result=subprocess.run(args,cwd=work,capture_output=True)
                if result.returncode:raise RuntimeError(f'{args}: {result.stdout!r} {result.stderr!r}')
                return result
            run('mkfs.cpm','-f',definition,str(raw))
            for name,data in files.items():
                source=work/name;source.write_bytes(data);run('cpmcp','-T','raw','-f',definition,str(raw),str(source),'0:'+name)
                extracted=work/('readback-'+name);run('cpmcp','-T','raw','-f',definition,str(raw),'0:'+name,str(extracted))
                actual=extracted.read_bytes();assert actual[:len(data)]==data and len(actual)<=((len(data)+127)//128)*128,name
            run('fsck.cpm','-T','raw','-f',definition,'-n',str(raw))
            data=raw.read_bytes()
            if native:
                image=raw_to_dmk(data,fmt);assert dmk_to_raw(image,fmt)==data
            else:image=data
            name=f'BetterCPM-Utilities-{target}-'+('80T-DS-800K.dmk' if native else '332K.dsk')
            reports.append((name,image,{'target':target,'image':name,'sha256':sha(image),'format':fmt.name,'status':'PROVISIONAL','included':[{'name':n,'sha256':sha(d),'bytes':len(d)} for n,d in files.items()],'pending':PENDING,'deferred':['NOAH interactive browser; command-line utility supplied on companion volume'],'validation':'file readback and filesystem PASS; native DMK/raw round trip PASS; no whole Utilities release acceptance claimed'}))
    # Component evidence is valid only for these exact packaged images.
    for name,data,report in reports:
        verdict={'status':'PENDING_RELEASE_ACCEPTANCE','sha256':sha(files['DDT.COM'])}
        if accepted:
            proof=accepted['platforms'][report['target']]
            if proof['status']!='PASS' or proof['utilities_sha256']!=sha(data) or proof['ddt_sha256']!=sha(files['DDT.COM']):
                raise ValueError('DDT acceptance does not match packaged '+name)
            verdict={'status':'PASS','sha256':sha(files['DDT.COM']),'evidence_sha256':sha(ddt_acceptance.read_bytes())}
        report['component_acceptance']={'DDT.COM':verdict}
        if tools_accepted is not None:
            validate_acceptance(tools_accepted,files,report['target'],data,accompanying)
        for tool in ('ZSM4.COM','LINK.COM'):
            report['component_acceptance'][tool]={'status':'PASS' if tools_accepted else 'PENDING_RELEASE_ACCEPTANCE','sha256':sha(files[tool])}
            if tools_accepted:
                report['component_acceptance'][tool]['evidence_sha256']=sha(toolchain_acceptance.read_bytes())
                report['component_acceptance'][tool]['paired_system_sha256']=tools_accepted['platforms'][report['target']]['system_sha256']
        report['toolchain_companions']={n:sha(d) for n,d in accompanying.items()}
        report['third_party_versions']={'ZSM4.COM':'4.7','LINK.COM':'1.3'}
        report['dasm_companions']={n:sha(d) for n,d in analysis_companions.items()}
        for name in ('DASM.COM','DSYM.COM','DLINK.COM'):
            verdict={'status':'PENDING_RELEASE_ACCEPTANCE','sha256':sha(files[name])}
            if dasm_accepted is not None:
                proof=validate_dasm_acceptance(dasm_accepted,files,report['target'],data)
                verdict.update(status='PASS',evidence_sha256=sha(dasm_acceptance.read_bytes()),
                               paired_system_sha256=proof['system_sha256'])
            report['component_acceptance'][name]=verdict
        report['ted_companions']={n:sha(d) for n,d in editor_companions.items()}
        verdict={'status':'PENDING_RELEASE_ACCEPTANCE','sha256':sha(files['TED.COM'])}
        if ted_accepted is not None:
            proof=validate_ted_acceptance(ted_accepted,files,report['target'],data)
            verdict.update(status='PASS',evidence_sha256=sha(ted_acceptance.read_bytes()),paired_system_sha256=proof['system_sha256'])
        report['component_acceptance']['TED.COM']=verdict
        verdict={'status':'PENDING_RELEASE_ACCEPTANCE','sha256':sha(files['SEARCH.COM'])}
        if search_accepted is not None:
            proof=validate_search_acceptance(search_accepted,files,report['target'],data)
            verdict.update(status='PASS',evidence_sha256=sha(search_acceptance.read_bytes()),paired_system_sha256=proof['system_sha256'])
            report['pending']=[x for x in report['pending'] if not x.startswith('SEARCH ')]
        report['component_acceptance']['SEARCH.COM']=verdict
        report['search_companions']={n:sha(d) for n,d in search_source_companions.items()}
        verdict={'status':'PENDING_RELEASE_ACCEPTANCE','sha256':sha(files['CRCKSUM.COM'])}
        if crc_accepted is not None:
            proof=validate_crc_acceptance(crc_accepted,files,report['target'],data)
            verdict.update(status='PASS',evidence_sha256=sha(crc_acceptance.read_bytes()),paired_system_sha256=proof['system_sha256'])
            report['pending']=[x for x in report['pending'] if not x.startswith('CRCKSUM ')]
        report['component_acceptance']['CRCKSUM.COM']=verdict
        report['crc_companions']={n:sha(d) for n,d in crc_source_companions.items()}
        verdict={'status':'PENDING_RELEASE_ACCEPTANCE','sha256':sha(files['MD5SUM.COM'])}
        if md5sum_accepted is not None:
            proof=validate_md5sum_acceptance(md5sum_accepted,files,report['target'],data)
            verdict.update(status='PASS',evidence_sha256=sha(md5sum_acceptance.read_bytes()),paired_system_sha256=proof['system_sha256'])
            report['pending']=[x for x in report['pending'] if not x.startswith('MD5SUM ')]
        report['component_acceptance']['MD5SUM.COM']=verdict
        report['md5sum_companions']={n:sha(d) for n,d in md5sum_source_companions.items()}
        if dasm_accepted is not None:
            report['pending']=[x for x in report['pending'] if not x.startswith('DASM ')]
        if ted_accepted is not None:
            report['pending']=[x for x in report['pending'] if not x.startswith('TED ')]
    # NOAH's matching COM/OVL and notes travel on a companion volume. The
    # 332K primary cannot hold these files alongside the selected tool set.
    from noah_distribution import media as noah_media
    companion_reports=noah_media(artifacts, noah_acceptance)
    for _,_,report in companion_reports:
        report['patch_companions']={n:sha(d) for n,d in patch_source_companions.items()}
        report['compare_companions']={n:sha(d) for n,d in compare_source_companions.items()}
    reports.extend(companion_reports)
    # The complete source companion travels with both images (GPL section 3a).
    for name,data in {**accompanying,**analysis_companions,**editor_companions,**search_source_companions,**crc_source_companions,**md5sum_source_companions,**patch_source_companions,**compare_source_companions}.items():
        staged=output/(name+'.tmp');staged.write_bytes(data);staged.replace(output/name)
    acceptance_files={}
    for label,path in [('DDT',ddt_acceptance),('Toolchain',toolchain_acceptance),('DASM',dasm_acceptance),('TED',ted_acceptance)]:
        if path:
            payload=path.read_bytes();receipt=json.loads(payload)
            acceptance_files[label+'-Utilities-Acceptance.json']=payload
            proof=receipt.get('evidence_archive')
            if proof:
                name=proof['name']
                if Path(name).name!=name:
                    raise ValueError('acceptance evidence requires a simple filename')
                data=(path.parent/name).read_bytes()
                if sha(data)!=proof['sha256']:
                    raise ValueError('acceptance evidence checksum differs: '+label)
                acceptance_files[name]=data
    # Construct and validate both before publishing either named image.
    for name,data,report in reports:
        from release_metadata import disk_record
        source_state=artifacts/'build-state.json'
        if source_state.is_file():report['source']=json.loads(source_state.read_text())['source']
        else:
            provenance=subprocess.run(['git','-C',str(artifacts),'rev-parse','HEAD'],capture_output=True,text=True)
            report['source']={'revision':provenance.stdout.strip() if provenance.returncode==0 else None}
        report['release_record']=disk_record(report,data,root=artifacts)
    for name,data,report in reports:
        staged=output/(name+'.tmp');staged.write_bytes(data);staged.replace(output/name)
        (output/(name+'.json')).write_text(json.dumps(report,indent=2)+'\n')
        print(f"{output/name}: PROVISIONAL, {len(report['included'])} files; {len(report['pending'])} pending selections/implementations")
    package={**accompanying,**analysis_companions,**editor_companions,**search_source_companions,**crc_source_companions,**md5sum_source_companions,**patch_source_companions,**compare_source_companions,**acceptance_files}
    for name,data,report in reports:
        package[name]=data
        package[name+'.json']=(output/(name+'.json')).read_bytes()
    sums=''.join(f'{sha(d)}  {n}\n' for n,d in sorted(package.items())).encode()
    (output/'Utilities-SHA256SUMS.txt').write_bytes(sums)
    package['Utilities-SHA256SUMS.txt']=sums
    # A complete host package keeps GPL corresponding source with both images.
    archive=output/'BetterCPM-Utilities-package.zip.tmp'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as zipped:
        for name,data in sorted(package.items()):
            info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o100644<<16
            zipped.writestr(info,data)
    archive.replace(output/'BetterCPM-Utilities-package.zip')
    return reports


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=ROOT/'build/utilities-disks')
    p.add_argument('--artifacts',type=Path,default=ROOT)
    p.add_argument('--build',action='store_true',help='freshly build owned Utilities components first')
    p.add_argument('--ddt-acceptance',type=Path,help='bind a passing DDT campaign to these exact image hashes')
    p.add_argument('--toolchain-acceptance',type=Path,help='bind passing native tool campaigns to both exact images and source companions')
    p.add_argument('--dasm-acceptance',type=Path,help='bind both-platform DASM qualification to exact binaries and disk images')
    p.add_argument('--ted-acceptance',type=Path,help='bind TED acceptance to both exact disk images')
    p.add_argument('--noah-acceptance',type=Path,help='bind NOAH companion-volume qualification to exact images')
    p.add_argument('--search-acceptance',type=Path,help='bind SEARCH native parity and execution to both exact disk images')
    p.add_argument('--crc-acceptance',type=Path,help='bind CRC native parity and execution to both exact disk images')
    p.add_argument('--md5sum-acceptance',type=Path,help='bind MD5SUM execution to exact paired images')
    a=p.parse_args()
    if a.build:
        for name in ['dump','ddt','batch','sq','usq','uncr','cr','unlzh','lzh','dasm','dsym','dlink','ted','noah','search','crc','md5sum']:
            command=[sys.executable,str(a.artifacts.resolve()/'tools'/f'build_{name}.py')]
            # TED defaults to its development directory; packaging consumes the
            # binary, native source and build records together in utilities.
            if name=='ted':command+=['--output',str(a.artifacts.resolve()/'build/utilities')]
            subprocess.run(command,cwd=a.artifacts.resolve(),check=True)
    build(a.output.resolve(),a.artifacts.resolve(),a.ddt_acceptance,a.toolchain_acceptance,a.dasm_acceptance,a.ted_acceptance,a.noah_acceptance,a.search_acceptance,a.crc_acceptance,a.md5sum_acceptance)


if __name__=='__main__':main()
