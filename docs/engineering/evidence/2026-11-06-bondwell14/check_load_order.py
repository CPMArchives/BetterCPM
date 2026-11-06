"""Reproduce the private FDF HL-input limitation with a prior chaining RSX."""
from argparse import ArgumentParser
from pathlib import Path
import json
import qualify as q
from test_z80pack_sysgen_install import session

class ObservedFailure(Exception):pass

def main():
    p=ArgumentParser(description=__doc__)
    for name in ('images','system','simulator','cpmtools','dsktrans','mapper','output'):p.add_argument('--'+name,type=Path,required=True)
    args=p.parse_args()
    if not __debug__:p.error('run without -O')
    for name in vars(args):setattr(args,name,getattr(args,name).resolve())
    args.catalogue=q.HERE/'qualification-catalogue.FDF'
    root=args.output;root.mkdir(parents=True)
    spec=next(s for s in json.loads((q.HERE/'sources.json').read_text())['images'] if s['filename']=='SYSTEM1.IMG')
    results={}
    for before in (True,False):
        label='p2dos-before-fdf' if before else 'fdf-before-p2dos'
        args.output=root/label;args.output.mkdir()
        def ordered(simulator,disks,commands,transcript):
            commands=list(commands);commands.insert(0 if before else 1,(b'RSX LOAD P2DOS\r',b'A0>_ ',30))
            if before:
                at=next(i for i,x in enumerate(commands) if x[0]==b'DIR B:\r')
                trace=session(simulator,disks,commands[:at]+[(b'DIR B:\r',b'Bad Sector',30)],transcript)
                assert trace.count(b'Disk configuration changed')==6
                raise ObservedFailure()
            return session(simulator,disks,commands,transcript)
        q.session=ordered
        try:result=q.run_one(spec,args)
        except ObservedFailure:results[label]=dict(status='expected Bad Sector reproduced')
        else:
            assert not before
            result['guest_commands'].insert(1,'RSX LOAD P2DOS')
            (args.output/'SYSTEM1/result.json').write_text(json.dumps(result,indent=2)+'\n')
            results[label]=result
        results[label]['console_sha256']=q.digest((args.output/'SYSTEM1/console.bin').read_bytes())
    (root/'results.json').write_text(json.dumps(dict(status='pass',scope='cpmsim controlled RSX load order; Model 4 rerun pending',samples=results),indent=2)+'\n')
    print('PASS: prior P2DOS reproduces Bad Sector; FDF first passes full interchange')
if __name__=='__main__':main()
