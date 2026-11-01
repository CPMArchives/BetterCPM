#!/usr/bin/env python3
"""Automated packaged PATCH success/rejection and DSYM conversion on private media."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from diagnose_trs80gp_context import probe_service
from trs80gp_launch import run
from run_trs80_command import key_args, DEFAULT_EMULATOR
from fdf_format import select_fdf
from build_z80pack_image import disk_definition
from convert_fdf_image import raw_to_dmk, dmk_to_raw
from dsym_reference import convert_log


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def padded(b):return b+b'\x1a'*((-len(b))%128)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--images',type=Path,default=Path.home()/'projects/git/BetterCPM/Releases/model4')
    p.add_argument('--emulator',type=Path,default=DEFAULT_EMULATOR)
    p.add_argument('--prepare-only',action='store_true')
    p.add_argument('--only',choices=['all','dsym'],default='all')
    a=p.parse_args();w=a.output.resolve();w.mkdir(parents=True,exist_ok=False)
    result={'status':'PREPARING','scope':'PATCH small success, mismatch preserves destination, DSYM valid LINK report; no full qualification'}
    def save():(w/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    save()
    try:
        originals=[a.images.resolve()/n for n in ['BetterCPM-Distribution-trs80gp-80T-DS-System.dmk','BetterCPM-Utilities-trs80gp-80T-DS-800K.dmk','BetterCPM-NOAH-trs80gp-80T-DS-800K.dmk','BetterCPM-Work-800K.dmk']]
        result['images']=[{'source':str(f),'sha256':sha(f)} for f in originals]
        drives=[]
        for i,f in enumerate(originals):
            dest=w/('drive'+str(i)+'.dmk');shutil.copyfile(f,dest);drives.append(dest)
        root=Path(__file__).resolve().parents[1]
        fmt=select_fdf(root/'third_party/montezuma/DISK-INT.FDF','Montezuma Micro 80T DS DATA (80T, DS, DD, 800K)')
        (w/'diskdefs').write_text(disk_definition(fmt))
        disk=w/'work.raw';disk.write_bytes(b'\xe5'*fmt.image_bytes)
        def cpm(*args):return subprocess.run(['cpmcp','-T','raw','-f','bettercpm-mm-80t-ds-data',str(disk),*map(str,args)],cwd=w,check=True,capture_output=True)
        data=bytes(range(128));old=b'PRESERVE THIS OUTPUT'+bytes(108)
        # Match the complete LINK report fixture already used by test_dsym.py.
        log=(b'LINK 1.3 \n\r\r\nSTART    0100   HELLO    0104   \r\n\r\n'
             b'ABSOLUTE     0000\r\nCODE SIZE    0004 (0100-0103)\r\n'
             b'DATA SIZE    0001 (0104-0104)\r\nCOMMON SIZE  0000\r\n'
             b'USE FACTOR     00\r\nDLINK END\r\n')
        log += b'\x1a'
        files={'IN.DAT':data,'GOOD.PAT':b'INPUT D0:IN.DAT\r\nOUTPUT D0:GOOD.DAT\r\n00: 00 01 02 -> FF FE FD\r\n\x1a',
               'BAD.PAT':b'INPUT D0:IN.DAT\r\nOUTPUT D0:KEEP.DAT\r\n00: 99 -> FF\r\n\x1a','KEEP.DAT':old,'SAMPLE.LOG':log}
        baseline={}
        for n,b in files.items():
            f=w/('fixture-'+n);f.write_bytes(padded(b));cpm(f,'0:'+n)
            copied=w/('baseline-'+n);cpm('0:'+n,copied);baseline[n]=copied.read_bytes()
        drives[3].write_bytes(raw_to_dmk(disk.read_bytes(),fmt))
        result['prepared_work_sha256']=sha(drives[3]);result['emulator_sha256']=sha(a.emulator)
        cases=[('patch-good','C:PATCH D:GOOD.PAT\r','full verification passed.'),
               ('patch-bad','C:PATCH D:BAD.PAT\r','Expected-byte mismatch at '),
               ('dsym','B:DSYM D:SAMPLE.LOG D:\r','; rejected 0; complete.')]
        if a.only=='dsym':cases=[c for c in cases if c[0]=='dsym']
        result['selected_cases']=[c[0] for c in cases]
        result['commands']=[]
        for name,text,expected in cases:
            cmd=[str(a.emulator),'-m4','-batch','-turbo','-ktx','-itime','18000']
            for i,f in enumerate(drives):cmd+=['-d'+str(i),str(f)]
            cmd+=['-iw','Type TYPE README.TXT for more','-id','6000','-it']
            cmd+=key_args(text,delay=25)+['-id','30000','-it','-ix']
            result['commands'].append({'name':name,'command':cmd,'expected':expected})
        save()
        if a.prepare_only:
            result['status']='PREPARED_NOT_RUN';save();print('PREPARED: '+str(w));return 0
        result['services']={n:probe_service(n) for n in ['com.apple.coreservices.launchservicesd','com.apple.windowserver.active']};save()
        if any(x['code'] for x in result['services'].values()):raise RuntimeError('Host service access denied; emulator not launched')
        # Each command gets a fresh boot, so input cannot race the previous
        # command's disk-based warm boot. Preserve the shared private work disk.
        for case in result['commands']:
            folder=w/case['name'];folder.mkdir()
            print('Running '+case['name'],flush=True)
            run(case['command'],cwd=folder,timeout=600)
            captures=[]
            for f in sorted(folder.glob('trs80-text-*.bin')):
                raw=f.read_bytes()[:1920];text='\n'.join(bytes(c&127 for c in raw[i:i+80]).decode('ascii').rstrip() for i in range(0,len(raw),80))
                f.with_suffix('.txt').write_text(text);captures.append(text)
            assert len(captures)==2,case['name']+': expected boot and result captures'
            case['observed']=captures[-1]
            case['output_check']=case['expected'] in captures[-1]
            save()
        # Export bytes even when an output-text check fails, for diagnosis.
        disk.write_bytes(dmk_to_raw(drives[3].read_bytes(),fmt))
        def exported(n):
            f=w/('export-'+n);cpm('0:'+n,f)
            if not f.is_file():raise RuntimeError('Expected output absent from work disk: '+n)
            return f.read_bytes()
        for n,b in baseline.items():assert exported(n)==b,(n,'input or protected output changed')
        if a.only=='all':
            assert exported('GOOD.DAT')==bytes([255,254,253])+data[3:],'PATCH output differs'
        actual=exported('SAMPLE.DSY');expected=convert_log(log)
        assert actual[:len(expected)]==expected and not actual[len(expected):].strip(b'\x1a\x00 '),'DSYM symbols differ'
        assert all(sha(f)==r['sha256'] for f,r in zip(originals,result['images'])),'Original image changed'
        assert sha(drives[1])==result['images'][1]['sha256'] and sha(drives[2])==result['images'][2]['sha256'],'Utility disks changed'
        assert all(c['output_check'] for c in result['commands']),'One or more command output checks failed; inspect case captures'
        result['status']='PASS'
    except Exception as e:result['status']='FAIL';result['error']=str(e)
    save();print(result['status']+': '+str(w/'result.json'),flush=True)
    if result['status']=='FAIL':print(result['error'])
    return 0 if result['status']=='PASS' else 1

if __name__=='__main__':raise SystemExit(main())
