#!/usr/bin/env python3
"""Validate reconstructed manifests and execute geometry/ROM guard primitives."""
import argparse
import json
from pathlib import Path
from build_qualified_cpmsim import sha, build, command
from test_cpmsim_rom_guard import prove_guard_primitives, run_probe


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True,help='Git object source for poisoned-working-tree reconstruction test')
    p.add_argument('--runtime',type=Path,required=True)
    p.add_argument('--qualification',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    for folder,profile in ((a.runtime,'runtime'),(a.qualification,'qualification')):
        manifest=json.loads((folder/'environment.json').read_text())
        assert manifest['profile']==profile and manifest['status']=='BUILT'
        for name,h in manifest['executables'].items():assert sha(folder/'z80pack'/name)==h,name
        for name,h in manifest['patched_input_sha256'].items():assert sha(folder/'z80pack'/name)==h,name
        assert '#define FDC_GEOM_PORT_VERSION\t2' in (folder/'z80pack/cpmsim/srcsim/simio.c').read_text()
    # Deliberately supply a different checked-out revision and poisoned source
    # and object files. Only pinned committed Git objects may reach the build.
    poison=a.output/'poisoned-checkout'
    command(['git','clone','--shared','--no-checkout',a.source,poison])
    source=poison/'cpmsim/srcsim';source.mkdir(parents=True)
    (source/'simio.c').write_text('#error working tree must never be copied\n')
    (source/'simio.o').write_bytes(b'NOT AN OBJECT FILE')
    rebuilt=build(poison,a.output/'isolated-runtime','runtime')
    expected=json.loads((a.runtime/'environment.json').read_text())
    actual=json.loads((a.output/'isolated-runtime/environment.json').read_text())
    assert actual['source_archive_sha256']==expected['source_archive_sha256']
    assert actual['patched_input_sha256']==expected['patched_input_sha256']
    assert actual['executables']==expected['executables']
    guard=a.output/'guard';guard.mkdir()
    prove_guard_primitives(a.qualification/'z80pack/cpmsim/cpmsim',guard)
    # Print G followed by the actual runtime geometry-interface version.
    code=bytes.fromhex('3e47d3013e7fd312db13c630d3013eaad3a03e80d3a0')
    run_probe(a.runtime/'z80pack/cpmsim/cpmsim',guard,'geometry-v2',code,0,('G2',),protect=False)
    (a.output/'report.json').write_text(json.dumps({'status':'PASS','poisoned_working_tree_reconstruction':'PASS','guard_cases':7,'geometry_version':2,
        'runtime_manifest_sha256':sha(a.runtime/'environment.json'),
        'qualification_manifest_sha256':sha(a.qualification/'environment.json')},indent=2)+'\n')


if __name__=='__main__':main()
