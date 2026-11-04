#!/usr/bin/env python3
"""Reconstruct cpmsim from pinned Git objects, never a caller's working tree."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]
PIN = ROOT/'third_party/z80pack/upstream.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(args, **kw):
    return subprocess.run(list(map(str,args)),check=True,capture_output=True,**kw).stdout


def project_revision(root=ROOT):
    """Use this checkout's identity, or the explicit identity of a source ZIP."""
    root=Path(root).resolve()
    top=subprocess.run(['git','rev-parse','--show-toplevel'],cwd=root,
                       capture_output=True,text=True)
    if top.returncode==0 and Path(top.stdout.strip()).resolve()==root:
        return command(['git','rev-parse','HEAD'],cwd=root).decode().strip()
    record=json.loads((root/'SOURCE-IDENTITY.json').read_text())
    revision=record.get('source_commit')
    if not isinstance(revision,str) or not re.fullmatch(r'[0-9a-f]{40}',revision):
        raise ValueError('source archive requires a full source_commit in SOURCE-IDENTITY.json')
    return revision


def offline_inputs(commit):
    manifest = json.loads((PIN.parent/'offline-inputs.json').read_text())
    if manifest['commit'] != commit:
        raise ValueError('offline inventory does not match upstream pin')
    return manifest['files']


def source_archive(repository, commit, files):
    """Archive only approved paths from committed objects at the full pin."""
    resolved = command(['git', '-C', repository, 'rev-parse', commit + '^{commit}']).decode().strip()
    if resolved != commit:
        raise ValueError('pinned commit unavailable')
    return command(['git', '-C', repository, 'archive', '--format=tar', commit, '--', *sorted(files)])


def verified_sources(payload, expected):
    sources = {}
    with tarfile.open(fileobj=io.BytesIO(payload), mode='r:') as archive:
        for member in archive:
            if member.isdir():
                continue
            path = PurePosixPath(member.name)
            if (not member.isfile() or path.is_absolute() or '..' in path.parts
                    or member.name not in expected or member.name in sources):
                raise ValueError('unexpected offline source entry: ' + member.name)
            data = archive.extractfile(member).read()
            if hashlib.sha256(data).hexdigest() != expected[member.name]:
                raise ValueError('offline source checksum differs: ' + member.name)
            sources[member.name] = data
    if sources.keys() != expected.keys():
        raise ValueError('offline source archive is incomplete')
    return sources


def build(repository, output, profile):
    pin=json.loads(PIN.read_text());output=output.resolve();output.mkdir(parents=True,exist_ok=False)
    source=output/'z80pack';source.mkdir()
    expected = offline_inputs(pin['commit'])
    repository = Path(repository)
    payload = (repository.read_bytes() if repository.is_file()
               else source_archive(repository, pin['commit'], expected))
    archive_hash = hashlib.sha256(payload).hexdigest()
    for name, data in verified_sources(payload, expected).items():
        path = source/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    # git apply otherwise discovers a surrounding BetterCP/M checkout when
    # output is under build/, and silently skips paths outside that prefix.
    # Apply to this standalone archive, independent of caller Git state.
    patch_env=dict(os.environ)
    for name in ('GIT_DIR','GIT_WORK_TREE','GIT_INDEX_FILE'):
        patch_env.pop(name,None)
    patch_env['GIT_CEILING_DIRECTORIES']=str(output)
    applied=[]
    for name in pin['profiles'][profile]:
        patch=PIN.parent/'patches'/name;entry=next(x for x in pin['patches'] if x['file']==name)
        if sha(patch)!=entry['sha256']:raise ValueError('patch digest mismatch: '+name)
        command(['git','apply','--check',patch],cwd=source,env=patch_env)
        command(['git','apply',patch],cwd=source,env=patch_env);applied.append(entry)
    compiler=shutil.which('cc');make=shutil.which('make')
    guest_env=dict(os.environ)
    for name in ('CFLAGS','CPPFLAGS','LDFLAGS','MAKEFLAGS','CPMSIM_ROM_START','CPMSIM_STACK_TRACE'):
        guest_env.pop(name,None)
    # Prepare project-owned guest banners with the actual pinned cross assembler.
    # No release-display override is used; baselines select assigned vs -dev.
    with (output/'guest-assembler-build.log').open('wb') as log:
        subprocess.run([make,'CC='+compiler,'all'],cwd=source/'z80asm',env=guest_env,
                       stdout=log,stderr=subprocess.STDOUT,check=True)
    from guest_utility_identity import prepare, finish
    guest_assembler=source/'z80asm/z80asm'
    guest_records=prepare(source,guest_assembler)
    source_hashes={str(p.relative_to(source)):sha(p) for p in sorted(source.rglob('*'))
                   if p.is_file() and p.suffix not in ('.o',) and p != guest_assembler}
    flags=['CC='+compiler,'INFOPANEL=NO','WANT_SDL=NO','MODE=RELEASE','DEBUG=',
           'SIM='+str(source/'cpmsim/cpmsim'),'ROM_QUALIFY='+('YES' if profile=='qualification' else 'NO')]
    env=dict(os.environ)
    for name in ('CFLAGS','CPPFLAGS','LDFLAGS','MAKEFLAGS','CPMSIM_ROM_START','CPMSIM_STACK_TRACE'):
        env.pop(name,None)
    builds=[[make,'-j4',*flags,'all'],[make,'CC='+compiler,'all']]
    for args,folder in zip(builds,('srcsim','srctools')):
        with (output/(folder+'-build.log')).open('wb') as log:
            subprocess.run(args,cwd=source/'cpmsim'/folder,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    guest_build=[make,'CC='+compiler,'r.com','w.com','mount.com']
    with (output/'cpmtools-build.log').open('wb') as log:
        subprocess.run(guest_build,cwd=source/'cpmtools',env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    guest_records=finish(guest_records,source,guest_assembler)
    (output/'guest-component-records.json').write_text(json.dumps(guest_records,indent=2,sort_keys=True)+'\n')
    builds.append(guest_build)
    guest_binaries=[source/'cpmtools'/n for n in ('r.com','w.com','mount.com')]
    binaries=[source/'cpmsim/cpmsim',*(source/'cpmsim/srctools'/n for n in ('cpmrecv','cpmsend','mkdskimg','bin2hex','ptp2bin'))]
    if platform.system()=='Darwin':
        for path in binaries:command(['codesign','--force','--sign','-',path])
    manifest={'status':'BUILT','profile':profile,'upstream':pin,'source_archive_sha256':archive_hash,
              'patches':applied,'patch_set_sha256':hashlib.sha256(json.dumps(applied,sort_keys=True).encode()).hexdigest(),
              'bettercpm_revision':project_revision(),
              'builder_sha256':sha(Path(__file__)),'host':platform.platform(),'architecture':platform.machine(),
              'compiler':command([compiler,'--version']).decode(),'make':command([make,'--version']).decode(),
              'build_commands':builds,'patched_input_sha256':source_hashes,
              'executables':{str(p.relative_to(source)):sha(p) for p in binaries},
              'guest_utilities':{str(p.relative_to(source)):sha(p) for p in guest_binaries},
              'build_log_sha256':{p.name:sha(p) for p in output.glob('*-build.log')}}
    (output/'environment.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(source/'cpmsim/cpmsim')
    return source


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True,help='packaged source tar or local Git repository containing the pinned commit')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--profile',choices=('runtime','qualification'),required=True)
    a=p.parse_args();build(a.source,a.output,a.profile)
