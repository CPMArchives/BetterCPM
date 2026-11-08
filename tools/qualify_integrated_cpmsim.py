"""Qualify integrated TCAP 2.0 with the ordinary cpmsim loader and SYSGEN."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

from build_integrated_display import build
from integrated_display_qualification import fixtures,commands,collection,audit
from tcap_test_support import ROOT,sha
from build_z80pack_image import DEFAULT_FORMAT
from fdf_format import select_fdf

from tcap_test_support import Guest


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('workspace',type=Path)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--personality',choices=('ADM3A','VT52','ANSI'),default='ADM3A')
    p.add_argument('--inline-cache',action='store_true')
    p.add_argument('--all-personalities',action='store_true')
    p.add_argument('--simulator',type=Path,default=ROOT/'build/tcap-cpmsim-emulator/z80pack/cpmsim/cpmsim')
    a=p.parse_args();workspace=a.workspace.resolve();out=a.output.resolve()
    out.mkdir(parents=True,exist_ok=False)
    platform=workspace/'build/z80pack'
    context=json.loads((workspace/'build/profile/context.json').read_text())
    assert context['profile']=='cpmsim-fullram' and not context.get('public_tcap',False)
    baseline=context['symbols']['LY_TPA'];maximum=(baseline-256)//128*128
    if a.all_personalities:
        files,budgets,sequence=collection(workspace,out,'cpmsim',maximum,('ADM3A','VT52','ANSI'),a.inline_cache)
        budget=budgets['ADM3A']
    else:
        carrier,budget=build(workspace,out/'profile','cpmsim',a.personality,inline_cache=a.inline_cache)
        files=fixtures(out/'fixtures',maximum,personality=a.personality);files[a.personality+'.RSX']=carrier
        budgets={a.personality:budget};sequence=commands(a.personality)
    for name,relative in [('RCP.CPX','build/cpx/RCP.CPX'),('R3PACK.RSX','build/system/R3PACK.RSX'),
        ('R3CACHE.RSX','build/system/R3CACHE.RSX'),('HELLO.RSX','build/rsx/HELLO.RSX'),
        ('SYSTEM.SYS','build/z80pack/system-package/SYSTEM.SYS')]:files[name]=(workspace/relative).read_bytes()
    for name in ('RSX','SYSGEN'):files[name+'.COM']=(workspace/'build/utilities'/(name+'.COM')).read_bytes()
    source=out/'source';source.mkdir();shutil.copytree(platform/'disks',source/'disks')
    shutil.copy2(platform/'diskdefs',source/'diskdefs')
    def put(folder,name,data,drive='a'):
        path=folder/name;path.write_bytes(data)
        subprocess.run(['cpmcp','-f','bettercpm-default',str(folder/'disks'/('drive'+drive+'.dsk')),
            str(path),'0:'+name],cwd=folder,check=True,capture_output=True)
    for name,data in files.items():put(source,name,data)
    report={'status':'RUNNING','platform':'cpmsim','service':'TCAP 2.0','budget':budget,
        'budgets':budgets,
        'baseline_boundary':baseline,'maximum_com_bytes':maximum,'checks':{},
        'simulator_sha256':sha(a.simulator),'core_package_sha256':sha(source/'SYSTEM.SYS')}
    def save():(out/'qualification.json').write_text(json.dumps(report,indent=2)+'\n')
    def plain(data):return re.sub(rb'\x1b\[[0-?]*[ -/]*[@-~]',b'',data).decode('ascii',errors='replace')
    def lifecycle(label,image):
        case=out/label;case.mkdir();shutil.copytree(source/'disks',case/'disks')
        shutil.copy2(image,case/'disks/drivea.dsk')
        guest=Guest(a.simulator.resolve(),case/'disks',case)
        boundaries=[];records=[];frames=[];active=None
        try:
            guest.prompt()
            for command in sequence:
                if command.startswith('RSX LOAD ') and command.split()[-1] in budgets:active=command.split()[-1]
                if command.startswith('RSX UNLOAD ') and command.split()[-1] in budgets:active=None
                if command.startswith('DEMO '):
                    guest.pending.clear();os.write(guest.terminal,command.encode()+b'\r')
                    before=guest.expect(('INTEGRATED READY '+command[-1]).encode(),rendered=True)
                    cells=[guest.screen.buffer[4][col] for col in range(9,18)]
                    reverse=active!='VT52'
                    assert ''.join(c.data for c in cells)=='TCAP TEXT' and all(c.reverse==reverse for c in cells),cells
                    os.write(guest.terminal,b' ');data=before+guest.prompt()
                else:data=guest.prompt(command)
                text=plain(data)
                assert 'FAIL' not in text and 'error' not in text.lower(),(command,text[-2000:])
                item={'command':command}
                if command=='BOUND':
                    boundary=int(re.findall(r'BOUNDARY ([0-9A-F]{4})',text)[-1],16)
                    boundaries.append(boundary);item['boundary']=boundary
                for cmd,caption in [('MAXCOM','MAXIMUM COM PASS'),('ABSENT','INTEGRATED ABSENT PASS'),
                    ('DEMO','INTEGRATED DEMO PASS'),('LEGACY','INTEGRATED LEGACY PASS')]:
                    if command==cmd or (cmd=='DEMO' and command.startswith('DEMO ')):assert caption in text,(command,text[-2000:])
                frames.append(text);records.append(item);print('PASS',label,command,flush=True)
            audit(sequence,frames,budgets,baseline)
            report['checks'][label]={'commands':records,'boundaries':boundaries,
                'cold_boot':True,'warm_returns':True,'exact_unload_restoration':True,
                'transcript_sha256':sha(case/'transcript.bin')};save()
        finally:guest.close()
    try:
        save();original=source/'disks/drivea.dsk';lifecycle('source-lifecycle',original)
        install=out/'installation';install.mkdir();shutil.copytree(source/'disks',install/'disks')
        shutil.copy2(source/'diskdefs',install/'diskdefs');dest=install/'disks/driveb.dsk'
        shutil.copy2(original,dest);put(install,'KEEP.TXT',b'KEEP THROUGH INSTALLATION\r\n','b')
        fmt=select_fdf(workspace/'metadata/DISK.FDF',DEFAULT_FORMAT)
        reserved=fmt.reserved_records*128
        before=bytearray(dest.read_bytes());before[:reserved]=b'\xe5'*reserved;dest.write_bytes(before)
        before=bytes(before);bad=bytearray(files['SYSTEM.SYS']);bad[80]^=1;put(install,'BAD.SYS',bad)
        guest=Guest(a.simulator.resolve(),install/'disks',install)
        try:
            guest.prompt();rejected=guest.prompt('SYSGEN BAD.SYS B:')
            assert b'system package is invalid' in rejected and dest.read_bytes()==before
            guest.command('SYSGEN SYSTEM.SYS B:',b'Proceed (Y/N)?');os.write(guest.terminal,b'N');guest.prompt()
            assert dest.read_bytes()==before
            guest.pending.clear();guest.command('SYSGEN SYSTEM.SYS B:',b'Proceed (Y/N)?')
            os.write(guest.terminal,b'Y');message=guest.prompt()
            assert b'System installed and verified' in message,plain(message)
        finally:guest.close()
        installed=dest.read_bytes();assert installed[reserved:]==before[reserved:]
        from checked_system_package import normalize
        definition=json.loads((platform/'checked-package.json').read_text())
        def payload(raw):
            result=bytearray()
            for n in range(160):
                track,within=divmod(n,fmt.spt)
                at=track*fmt.raw_track_bytes+fmt.raw_record_map()[within]*128
                result.extend(raw[at:at+128])
            return bytes(result)
        assert normalize(payload(installed),definition['masks'])==normalize(payload(original.read_bytes()),definition['masks'])
        report['checks']['installation']={'invalid_package_rejected_before_write':True,
            'decline_unchanged':True,'filesystem_unchanged':True,'installed_core_matches_source':True,
            'installed_image_sha256':sha(dest)};save()
        lifecycle('installed-lifecycle',dest)
        report.update(status='PASS integrated TCAP 2.0 source/install/cold/warm/load/run/unload',permanent_memory_loss_bytes=0)
    except BaseException as error:
        report.update(status='FAIL',detail=str(error));raise
    finally:save()
    print(report['status'],out,flush=True)


if __name__=='__main__':main()
