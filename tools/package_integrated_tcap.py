"""Package qualified engineering media without changing any release assignment."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

from build_montezuma_extended_790k import RAW_SIZE,build as dmk
from build_trs80_boot import install_files
from add_cpm_file_to_dmk import extract_raw
from model2_media import image as imd,geometry
from test_model2_release_media import decoded

ROOT=Path(__file__).resolve().parents[1]


def digest(data):return hashlib.sha256(data).hexdigest()


def native_files(path,platform):
    raw=extract_raw(path.read_bytes()) if platform=='model4' else decoded(path.read_bytes())[2]
    reserved=20480 if platform=='model4' else 3328+(geometry().off-1)*geometry().raw_track_bytes
    result={}
    for i in range(128):
        entry=raw[reserved+i*32:reserved+(i+1)*32]
        if entry[0]!=0:continue
        stem=bytes(v&127 for v in entry[1:9]).decode('ascii').rstrip()
        suffix=bytes(v&127 for v in entry[9:12]).decode('ascii').rstrip()
        name=stem+('.'+suffix if suffix else '')
        extent=(entry[14]&63)*32+(entry[12]&31)
        data=bytearray()
        for at in range(16,32,2):
            block=int.from_bytes(entry[at:at+2],'little')
            if block:data.extend(raw[reserved+block*2048:reserved+(block+1)*2048])
        result.setdefault(name,[]).append((extent,bytes(data[:entry[15]*128])))
    return {name:b''.join(data for _,data in sorted(parts)) for name,parts in result.items()}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cores',type=Path,required=True)
    p.add_argument('--platform',choices=('cpmsim','model4','model2'),action='append',help='package selected platforms; default is all three')
    for platform in ('cpmsim','model4','model2'):p.add_argument('--'+platform,type=Path,help='passing qualification directory')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    selected=a.platform or ['cpmsim','model4','model2']
    for name in selected:
        if getattr(a,name) is None:p.error('--'+name+' passing qualification directory is required')
    reports={name:json.loads((getattr(a,name)/'qualification.json').read_text()) for name in selected}
    for name,r in reports.items():
        assert r['status'].startswith('PASS') and r['service']=='TCAP 2.0',name
        assert r['permanent_memory_loss_bytes']==0 and set(r['budgets'])=={'ADM3A','VT52','ANSI'},name
        assert all(b['inline_cache_ownership'] and b['full_budgeted_path_bytes']<=(1792 if b['personality']=='ANSI' else 1280) for b in r['budgets'].values()),name
    manifest={'status':'qualified engineering candidate; no release assignment',
        'service':'TCAP 2.0','utility_migrations':'deferred','release_assignment':'deferred','platforms':{}}
    corepaths={'cpmsim':'profiles/cpmsim-fullram/z80pack','model4':'trs80gp','model2':'profiles/model2-fullram/trs80m2'}
    for platform,r in reports.items():
        folder=out/platform;folder.mkdir();q=getattr(a,platform).resolve();work=a.cores.resolve()/corepaths[platform]
        native=platform!='cpmsim'
        tested=native_files(q/'source-lifecycle'/('workflow.imd' if platform=='model2' else 'workflow.dmk'),platform) if native else None
        verified=[]
        def verify(name,data):
            if native:observed=tested[name]
            else:
                dest=folder/'verify.tmp'
                subprocess.run(['cpmcp','-f','bettercpm-default',str(q/'source-lifecycle/disks/drivea.dsk'),
                    '0:'+name,str(dest)],cwd=q/'source',check=True,capture_output=True)
                observed=dest.read_bytes();dest.unlink()
            assert observed in (data,data.ljust((len(data)+127)//128*128,b'\x1a')),(platform,name)
            verified.append(name)
        assets={}
        core=[('SYSTEM.SYS','build/trs80m2/SYSTEM.SYS' if platform=='model2' else
               'build/trs80/system-package/SYSTEM.SYS' if platform=='model4' else 'build/z80pack/system-package/SYSTEM.SYS'),
              ('RCP.CPX','build/cpx/RCP.CPX'),('R3PACK.RSX','build/system/R3PACK.RSX'),('R3CACHE.RSX','build/system/R3CACHE.RSX')]
        core += [(name+'.COM','build/utilities/'+name+'.COM') for name in (('RSX','SYSGEN','CONFIG','STAT') if native else ('RSX','SYSGEN'))]
        for name,relative in core:
            data=(work/relative).read_bytes();verify(name,data);assets[name]=data
        for name,budget in r['budgets'].items():
            data=(q/'profiles'/name/(name+'.RSX')).read_bytes()
            assert digest(data)==budget['carrier_sha256'];verify(name+'.RSX',data);assets[name+'.RSX']=data
        consumer=(q/'fixtures/ANSI/DEMO.bin').read_bytes()
        verify('DEMO.COM',consumer);assets['DEMO.COM']=consumer
        # Existing ordinary utilities only. No TYPE, TED or HELP migration.
        for name in (('CPX','SUBMIT','VER') if native else ('CPX','SUBMIT','VER','CONFIG','STAT')):
            path=work/'build/utilities'/(name+'.COM')
            if path.exists():assets[name+'.COM']=path.read_bytes()
        if 'SUBMIT.COM' in assets:
            assert 'VER.COM' in assets,'compile the existing transient VER before creating its startup script'
            assets['STARTUP.SUB']=b':VER /BANNER\r\n\x1a'
        assets['README.TXT']=('TCAP 2.0 ENGINEERING CANDIDATE\r\n'
            'Supported compact personalities: ADM3A, VT52 and ANSI.\r\n'
            'RSX LOAD ADM3A, run an ADM3A app, RSX UNLOAD ADM3A.\r\n'
            'Then RSX LOAD VT52, run a VT52 app, RSX UNLOAD VT52.\r\n'
            'No separate screen backend is required for these modules.\r\n'
            'After loading a personality, run DEMO 1 and press 1 at READY.\r\n'
            'Use the matching SYSTEM.SYS, R3PACK.RSX and R3CACHE.RSX.\r\n'
            'Select ANSI with RSX LOAD ANSI; finish with RSX UNLOAD ANSI.\r\n'
            'Utility migrations and release assignment remain deferred.\r\n').encode('ascii')
        for name,data in assets.items():(folder/name).write_bytes(data)
        if platform=='model4':
            raw=bytearray(b'\xe5'*RAW_SIZE);raw[:len(assets['SYSTEM.SYS'])-128]=assets['SYSTEM.SYS'][128:]
            install_files(raw,list(assets.items()),directory=20480,block_count=(RAW_SIZE-20480)//2048)
            disk=folder/'TCAP-Model4-Engineering.dmk';disk.write_bytes(dmk(raw))
        elif platform=='model2':
            disk=folder/'TCAP-ModelII-Engineering.imd';disk.write_bytes(imd(assets['SYSTEM.SYS'][128:],list(assets.items())))
        else:
            disks=folder/'disks';shutil.copytree(work/'build/z80pack/disks',disks)
            shutil.copy2(work/'build/z80pack/diskdefs',folder/'diskdefs')
            disk=disks/'drivea.dsk'
            protected=disk.read_bytes()[:6*18*256]
            # The engineering image contains the declared assets, not the
            # prepared workspace's unrelated development utilities. Keep the
            # already-qualified protected boot surface byte-identical.
            subprocess.run(['cpmrm','-f','bettercpm-default',str(disk),'0:*'],
                cwd=folder,check=True,capture_output=True)
            assert disk.read_bytes()[:len(protected)]==protected
            for name in assets:
                subprocess.run(['cpmcp','-f','bettercpm-default',str(disk),str(folder/name),'0:'+name],cwd=folder,check=True,capture_output=True)
        manifest['platforms'][platform]={'budgets':r['budgets'],'permanent_memory_loss_bytes':0,
            'qualification_sha256':digest((q/'qualification.json').read_bytes()),
            'core_and_modules_verified_against_tested_media':True,'verified_asset_names':verified,
            'boot_image':str(disk.relative_to(out)),'boot_image_sha256':digest(disk.read_bytes()),
            'files':{name:digest(data) for name,data in assets.items()}}
        shutil.copy2(q/'qualification.json',folder/'qualification.json')
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (out/'README.md').write_text('# TCAP engineering package\n\nPlatforms in this package: '+', '.join(selected)+'.\n'+'''

This is an engineering candidate for the combined ADM3A, VT52 and ANSI modules on
cpmsim, Model 4 and Model II. It is not a release assignment. TYPE, TED and HELP have not been migrated.

Boot the appropriate image, then use `RSX LOAD ADM3A`, run an ADM3A application,
and `RSX UNLOAD ADM3A`. Select VT52 or ANSI in the same way. These modules require no
separate SCRN load. Keep each platform's SYSTEM.SYS, R3PACK.RSX, R3CACHE.RSX and
personality files together. The bundled `DEMO 1` consumer displays TCAP TEXT;
press `1` at its READY message. Its bytes are verified against the qualified
source media, including the native checkpoint form. The checked platforms enforce matching private builds;
older managers reject the new inline-cache permission flag.

The manifest counts personality, renderer, facts, descriptors, cache footer,
rounding, caller helper, shared display state and disclosed call/stack allowances.
Only the separate 1,024-byte generic RSX machinery is excluded. Exact original
TPA and maximum COM capacity were restored after complete unload on every tested
platform. The bundled ordinary startup does not load a personality automatically.

The qualification files describe the tested cold boot, installation, warm returns,
relocation and unload. Packaged disk filesystem contents differ by removal of test
fixtures and addition of this README and ordinary startup utilities. Their core and
module bytes are verified against the actual tested media; packaged-boot smoke
checks are recorded separately.
''')
    sdk=out/'sdk';sdk.mkdir()
    shutil.copy2(ROOT/'src/utilities/common/tcap2.inc',sdk/'tcap2.inc')
    shutil.copy2(ROOT/'docs/engineering/contracts/tcap-2.0.json',sdk/'tcap-2.0.json')
    (sdk/'README.txt').write_text('TCAP 2.0 caller interface: T2_OPEN discovers the selected same-owner provider.\n'
        'T2_EMIT accepts A=operation, B=row and C=column for position. Text uses normal BDOS output.\n'
        'A=0 is success; 1 unavailable, 2 unsupported, 3 invalid arguments, 255 unknown selector.\n'
        'Rediscover after every RSX layout mutation; retain no pointer across a warm return.\n'
        'Operations: 0 facts, 1 clear, 2 position, 3 erase line, 4/5 strong on/off, 6/7 normal baseline.\n'
        'Utility migrations and release assignment are deferred. See the source-tree TCAP-Direct-ABI.md.\n')
    archive=out.with_suffix('.zip')
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for file in sorted(out.rglob('*')):
            if file.is_file():z.write(file,str(Path(out.name)/file.relative_to(out)))
    print('BUILT engineering package',archive)


if __name__=='__main__':main()
