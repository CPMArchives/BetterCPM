"""One guarded build/provenance entry point for every registered component.

Run the existing builder after --; no revision is assigned automatically.
Native mode records the real ZSM4/LINK binaries and exports the same prepared
identity context to source-generation code, without requiring Git on CP/M.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
from component_inputs import ROOT, capture, digest
from component_development import select


def record_collection(root, target, source, assembler=None):
    """Record actual build products once; identical cached artifacts keep provenance."""
    root=Path(root);assembler=Path(assembler or Path.home()/'bin/z80asm')
    from component_registry import load
    registry=load(root/'metadata/component-registry.json')['components']
    template=json.loads((root/'metadata/component-artifacts.json').read_text())
    records={}
    for key,products in template['components'].items():
        try:
            context=root/'build/profile/context.json'
            context=context if context.is_file() else None
            inputs=capture(key,assembler,root=root,target=target,checked_context=context)
            display=select(key,assembler,root=root,target=target,checked_context=context)
        except ValueError:continue  # Component is not available on this target.
        for product in products:
            path=root/product
            if not path.is_file():continue
            data=path.read_bytes();sha=digest(data)
            sidecar=path.parent/(key.split(':')[1]+'-build-report.json')
            if sidecar.is_file():
                cached=json.loads(sidecar.read_text())
                if cached.get('component')==key and cached.get('artifact',{}).get('sha256')==sha:
                    records[key]=cached;continue
            row=registry[key]
            if key.startswith('utility:') and path.suffix.upper()=='.COM':
                name=key.split(':')[1]
                expected=f"{name} {row['version']} ({row['revision']:03d}".encode()
                if expected not in data:raise ValueError('stale component identity: '+name)
            record={'schema':1,'component':key,'identity':inputs['assigned_identity'],
                    'input_record':inputs,'display_selection':display,'artifact':{'name':path.name,'bytes':len(data),'sha256':sha},
                    'provenance':{'repository_commit':source.get('revision'),'source_inputs':source.get('inputs')},
                    'status':'collection build record; execution qualification not asserted'}
            sidecar.write_text(json.dumps(record,indent=2,sort_keys=True)+'\n');records[key]=record
    return records


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('component');p.add_argument('--assembler',type=Path,required=True)
    p.add_argument('--linker',type=Path);p.add_argument('--native',action='store_true')
    p.add_argument('--target',default='z80pack');p.add_argument('--profile',default='default')
    p.add_argument('--artifact',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--identity-state',choices=('auto','assigned','development'),default='auto')
    # argparse REMAINDER after the component would consume options; split the
    # builder command at the explicit delimiter before normal option parsing.
    import sys
    argsv=sys.argv[1:];cut=argsv.index('--') if '--' in argsv else len(argsv)
    args=p.parse_args(argsv[:cut]);command=argsv[cut+1:]
    if not command:p.error('supply the builder command after --')
    if args.native and not args.linker:p.error('native mode requires --linker')
    kwargs={'target':args.target,'profile':args.profile,'build_mode':'native' if args.native else 'cross',
            'toolchain':{'linker':args.linker} if args.native else {},'configuration':{'command':command}}
    args.output.unlink(missing_ok=True)
    before=capture(args.component,args.assembler,**kwargs)
    environment=dict(os.environ)
    environment.update(BETTERCPM_IDENTITY_TARGET=args.target,BETTERCPM_IDENTITY_STATE=args.identity_state,
                       BETTERCPM_BUILD_ASSEMBLER=str(args.assembler.resolve()),
                       BETTERCPM_BUILD_CONFIGURATION=json.dumps(kwargs['configuration'],sort_keys=True))
    if args.native:environment['BETTERCPM_NATIVE_LINKER']=str(args.linker.resolve())
    selected=select(args.component,args.assembler,target=args.target,mode=args.identity_state,
                    build_mode=kwargs['build_mode'],toolchain=kwargs['toolchain'],configuration=kwargs['configuration'])
    subprocess.run(command,check=True,env=environment,cwd=ROOT)
    after=capture(args.component,args.assembler,**kwargs)
    after_display=select(args.component,args.assembler,target=args.target,mode=args.identity_state,
                         build_mode=kwargs['build_mode'],toolchain=kwargs['toolchain'],configuration=kwargs['configuration'])
    if before!=after or selected!=after_display:raise ValueError('component inputs/display changed during build')
    data=args.artifact.read_bytes()
    git=subprocess.run(['git','-C',str(ROOT),'rev-parse','HEAD'],capture_output=True,text=True)
    result={'schema':1,'component':args.component,'identity':after['assigned_identity'],
            'input_record':after,'display_selection':selected,
            'artifact':{'name':args.artifact.name,'bytes':len(data),'sha256':digest(data)},
            'provenance':{'repository_commit':git.stdout.strip() if git.returncode==0 else None},
            'status':'guarded build record; execution qualification not asserted'}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')


if __name__=='__main__':main()
