#!/usr/bin/env python3
"""Run focused Altair release gates against exact manifest-selected media."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from prepare_altair_release_session import prepare

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build-root',type=Path,required=True,help='prepared profile root')
    p.add_argument('--simulator',type=Path,required=True)
    p.add_argument('--suite',type=Path,required=True,help='pinned independent compatibility-suite checkout')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    root=a.build_root.resolve();images=root/'build/altair';session=prepare(images,out/'mounts')
    sim=a.simulator.resolve();suite=a.suite.resolve()
    gates=[('loader','qualify_altair_loader',['--build-root',root,'--simulator',sim]),
           ('install','qualify_altair_install',['--image-dir',session,'--simulator',sim]),
           ('media','qualify_altair_media',['--image-dir',session,'--simulator',sim]),
           ('utilities','qualify_altair_utilities',['--image-dir',images,'--simulator',sim]),
           ('compatibility','qualify_altair_compatibility',['--image-dir',session,'--simulator',sim,'--suite',suite]),
           ('shared-core','qualify_altair_shared_core',['--altair-root',root]),
           ('hardware','test_altair_hardware',['--simulator',sim])]
    collection=json.loads((images/'release/collection.json').read_text())
    summary={'status':'RUNNING','system_sha256':collection['volumes'][0]['sha256'],
             'emulator_sha256':hashlib.sha256(sim.read_bytes()).hexdigest(),'gates':{}}
    def save():(out/'result.json').write_text(json.dumps(summary,indent=2)+'\n')
    save()
    for name,script,options in gates:
        print('Qualifying',name,flush=True)
        with (out/(name+'.log')).open('w') as log:
            result=subprocess.run([sys.executable,'-B',str(ROOT/'tools'/(script+'.py')),
                                   *map(str,options),'--output',str(out/name)],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        summary['gates'][name]={'status':'PASS' if result.returncode==0 else 'FAIL',
                              'result':name+'/result.json','log':name+'.log'}
        save()
        if result.returncode:
            summary['status']='FAIL';save();raise SystemExit('failed '+name+'; see '+str(out/(name+'.log')))
    summary['status']='PASS';save();print('PASS: all focused Altair release gates',flush=True)


if __name__=='__main__':main()
