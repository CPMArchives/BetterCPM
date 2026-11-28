#!/usr/bin/env python3
"""Run unmodified pinned CP/M compatibility binaries on four-drive RomWBW."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
from qualify_cromemco_compatibility import GROUPS, REVISION
from romwbw_media import image
from test_romwbw_system import Terminal


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('suite','image-dir','simulator','rom','output'): p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--only',action='append')
    a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    src=a.image_dir.resolve();suite=a.suite.resolve()
    def blob(path): return subprocess.check_output(['git','-C',str(suite),'show',REVISION+':suite/'+path])
    hashes={n:h for h,n in (line.split() for line in blob('build/SHA256SUMS.txt').decode().splitlines() if line.strip())}
    names=subprocess.check_output(['git','-C',str(suite),'ls-tree','--name-only',REVISION+':suite/runtime-payload'],text=True).splitlines()
    payload=[(n,blob('runtime-payload/'+n)) for n in names if n.endswith(('.DAT','.CFG'))]
    report={'status':'RUNNING','suite_revision':REVISION,
            'system_sha256':hashlib.sha256((src/'system.img').read_bytes()).hexdigest(),
            'scope':'Unmodified automatic groups on A:/B:/C:/D:, including distinct C: and full-allocation/full-directory D: fixtures; manual and external cards remain separate.',
            'groups':{}}
    def save(): (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    save()
    for name,selector,reference in GROUPS:
        if a.only and name.lower() not in a.only: continue
        work=out/name.lower();work.mkdir()
        shutil.copy2(src/'system.img',work/'system.img')
        program=blob('build/'+name+'.COM')
        assert hashlib.sha256(program).hexdigest()==hashes[name+'.COM']
        files=[(name+'.COM',program),*payload]
        if name=='BDOSTEST': files += [('BDSA.TMP',b''),('BDSB.TMP',b'')]
        raw=bytearray(image(bytes(20480),b'\0',files))
        # The independent fixture explicitly requires the CP/M read-only bit.
        for at in range(131072,147456,32):
            if raw[at+1:at+12]==b'BTRO    DAT': raw[at+9]|=128
        (work/'fixtures.img').write_bytes(raw)
        shutil.copy2(src/'diskdefs',work/'diskdefs')
        (work/'BTUSR.DAT').write_bytes(blob('runtime-payload/BTUSR.DAT'))
        subprocess.run(['cpmcp','-T','raw','-f','bettercpm-romwbw',str(work/'fixtures.img'),str(work/'BTUSR.DAT'),'1:BTUSR.DAT'],cwd=work,check=True)
        cross=image(bytes(20480),b'\0',[('BTBFILE.DAT',(b'BFILE-000 '*15)[:128])])
        full=[('BTFULL.DAT',bytes(127*128)+b'FULL-127'+bytes(120)),
              ('BTREL.DAT',bytes(128)),('BTFILL.DAT',bytes((2048-4-4-1)*4096))]
        entries=sum(max(1,(len(data)+32767)//32768) for _,data in full)
        full.extend((f'F{i:07}.DAT',b'') for i in range(512-entries))
        filled=image(bytes(20480),b'\0',full)
        directory=filled[131072:147456]
        allocated={0,1,2,3}
        for at in range(0,16384,32):
            assert directory[at]!=229
            for i in range(16,32,2):
                block=int.from_bytes(directory[at+i:at+i+2],'little')
                if block: allocated.add(block)
        assert allocated==set(range(2048)), 'D: fixture is not allocation-full'
        (work/'cross.img').write_bytes(cross);(work/'full.img').write_bytes(filled)
        row={'status':'RUNNING','command':name+' '+selector,
             'expected_passes':reference,
             'cross_sha256':hashlib.sha256(cross).hexdigest(),
             'full_sha256':hashlib.sha256(filled).hexdigest(),'program_sha256':hashes[name+'.COM']}
        report['groups'][name]=row;save();print('Running',name,selector,flush=True)
        command=[str(a.simulator.resolve()),'--romwbw='+str(a.rom.resolve()),
                 '--disk0='+str(work/'system.img'),'--disk1='+str(work/'fixtures.img'),
                 '--disk2='+str(work/'cross.img'),'--disk3='+str(work/'full.img'),
                 '--boot=2','--no-config','--strict-io','--escape=none','--max-instructions=40000000000']
        t=Terminal(a.simulator.resolve(),work,command=command)
        try:
            t.prompt();t.send('CONFIG /LOGICAL=B /UNIT=3','B: binding updated.')
            t.send('CONFIG /LOGICAL=C /UNIT=4','C: binding updated.')
            t.send('CONFIG /LOGICAL=D /UNIT=5','D: binding updated.')
            t.send('B:',drive='B');t.type_command(name+' '+selector)
            t.expect(r'Summary:\s*\d+ pass,\s*\d+ fail,\s*\d+ error',timeout=180)
            t.prompt('B');text=t.data.decode('latin1')
            summary=re.search(r'Summary:\s*(\d+) pass,\s*(\d+) fail,\s*(\d+) error',text)
            actual=tuple(map(int,summary.groups()))
            row.update(summary=list(actual),rows={m[1]:[m[2],m[3],m[4].strip()] for m in
                re.finditer(r'(?:^|\n)(\d{4})\s+([PFEOS?\-])\s+([RNXS])\s+([^\r\n]*)',text)})
            row['qualified_passes']=actual[0]
            row['status']='PASS' if actual==(reference,0,0) else 'FAIL'
            print(name,actual,flush=True)
        except Exception as error:
            row.update(status='FAIL',error=str(error));report['status']='FAIL';save();raise
        finally:
            t.close();row['transcript_sha256']=hashlib.sha256(t.data).hexdigest();save()
    states={row['status'] for row in report['groups'].values()}
    report.update(status='FAIL' if 'FAIL' in states else 'PASS',
                  raw_passes=sum(row['summary'][0] for row in report['groups'].values()),
                  qualified_passes=sum(row['qualified_passes'] for row in report['groups'].values()))
    save();print(report['status']+':',report['qualified_passes'],'qualified automatic assertions',flush=True)
    if report['status']!='PASS': raise SystemExit(1)



if __name__=='__main__': main()
