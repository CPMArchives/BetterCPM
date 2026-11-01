#!/usr/bin/env python3
"""Compare macOS service access and optionally execute a private Model 4 smoke test."""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import sys
from datetime import datetime
from trs80gp_launch import run
from run_trs80_command import key_args, DEFAULT_EMULATOR


def probe_service(name):
    lib = ctypes.CDLL('/usr/lib/libSystem.B.dylib')
    bootstrap = ctypes.c_uint.in_dll(lib, 'bootstrap_port').value
    task = ctypes.c_uint.in_dll(lib, 'mach_task_self_').value
    lib.bootstrap_look_up.argtypes = [ctypes.c_uint, ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint)]
    lib.bootstrap_look_up.restype = ctypes.c_int
    lib.mach_port_deallocate.argtypes = [ctypes.c_uint, ctypes.c_uint]
    port = ctypes.c_uint()
    code = lib.bootstrap_look_up(bootstrap, name.encode(), ctypes.byref(port))
    if code == 0:
        lib.mach_port_deallocate(task, port.value)
    return {'code':code, 'meaning':{0:'accessible',1100:'BOOTSTRAP_NOT_PRIVILEGED',1102:'BOOTSTRAP_UNKNOWN_SERVICE'}.get(code,'other error')}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--probe-only', action='store_true')
    p.add_argument('--emulator', type=Path, default=DEFAULT_EMULATOR)
    p.add_argument('--images', type=Path, default=Path.home()/'projects/git/BetterCPM/Releases/model4')
    p.add_argument('--output', type=Path, required=True)
    a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    report={'host':platform.platform(),'uid':os.getuid(),'time':datetime.now().astimezone().isoformat(),
            'probe_only':a.probe_only,'status':'PROBED','services':{}}
    if sys.platform=='darwin':
        for name in ['com.apple.coreservices.launchservicesd','com.apple.windowserver.active']:
            report['services'][name]=probe_service(name)
    path=out/'result.json'
    def save():
        path.write_text(json.dumps(report,indent=2)+'\n')
    save();print(json.dumps(report,indent=2),flush=True)
    if a.probe_only:return 0
    if any(r['code'] for r in report['services'].values()):
        report['status']='BLOCKED_HOST_SERVICES';save()
        print('No emulator launched: required macOS service access failed.',flush=True);return 2
    try:
        emulator=a.emulator.resolve();assert emulator.is_file(),str(emulator)
        names=['BetterCPM-Distribution-trs80gp-80T-DS-System.dmk','BetterCPM-Utilities-trs80gp-80T-DS-800K.dmk',
               'BetterCPM-NOAH-trs80gp-80T-DS-800K.dmk','BetterCPM-Work-800K.dmk']
        originals=[a.images.resolve()/n for n in names]
        assert all(f.is_file() for f in originals),'Missing release images'
        report['emulator_sha256']=sha(emulator)
        report['images']=[{'source':str(f),'sha256':sha(f)} for f in originals]
        copies=[]
        for i,f in enumerate(originals):
            copy=out/('drive'+str(i)+'.dmk');shutil.copyfile(f,copy);copies.append(copy)
        cmd=[str(emulator),'-m4','-batch','-turbo','-ktx','-itime','15000']
        for i,f in enumerate(copies):cmd.extend(['-d'+str(i),str(f)])
        cmd+=['-iw','Type TYPE README.TXT for more','-id','6000','-it']
        cmd+=key_args('B:CRCKSUM /VER\r',delay=25)
        cmd+=['-iw','CRCKSUM 1.0','-id','6000','-it','-ix']
        report['command']=cmd;save()
        run(cmd,cwd=out,timeout=180)
        screens=[]
        for f in sorted(out.glob('trs80-text-*.bin')):
            raw=f.read_bytes();text='\n'.join(bytes(c&127 for c in raw[i:i+80]).decode('ascii').rstrip() for i in range(0,min(len(raw),1920),80))
            f.with_suffix('.txt').write_text(text);screens.append(text)
        assert len(screens)>=2,'Expected boot and version captures'
        assert 'BetterCP/M' in screens[0],'Boot banner missing'
        assert 'CRCKSUM 1.0 (008-dev)' in screens[-1],'Expected candidate CRCKSUM version missing'
        assert 'A0>' in screens[-1].split('CRCKSUM 1.0 (008-dev)',1)[1],'No returned prompt captured after version banner'
        assert all(sha(f)==r['sha256'] for f,r in zip(originals,report['images'])),'Original image changed'
        report['status']='PASS';report['scope']='Model 4 boot, injected version query, screen capture, prompt return; not full qualification'
    except Exception as e:
        report['status']='FAIL';report['error']=str(e)
    save();print(report['status']+': '+str(path),flush=True)
    return 0 if report['status']=='PASS' else 1


if __name__=='__main__':
    sys.exit(main())
