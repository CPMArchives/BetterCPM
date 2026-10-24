"""Reproducible complete source companion for the maintained DASM tool set."""
import gzip
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile


def companions(root):
    root=Path(root)
    provenance=json.loads((root/'third_party/dasm/provenance.json').read_text())
    for name,row in provenance['files'].items():
        data=(root/'third_party/dasm'/name).read_bytes()
        if len(data)!=row['bytes'] or hashlib.sha256(data).hexdigest()!=row['sha256']:
            raise ValueError('original DASM provenance mismatch: '+name)
    names=subprocess.run(['git','-C',str(root),'ls-files','-z'],check=True,capture_output=True).stdout.split(b'\0')
    files={name.decode(): (root/name.decode()).read_bytes() for name in names if name}
    required={'src/utilities/dasm.mac','src/utilities/dsym.mac','src/utilities/dlink.mac',
        'src/utilities/common/dasmsession.inc','src/utilities/common/dsymlog.inc',
        'tools/build_dasm.py','tools/build_dsym.py','tools/build_dlink.py','tools/dasm_distribution.py',
        'third_party/dasm/dasm.mac','third_party/dasm/provenance.json'}
    if not required<=files.keys():raise ValueError('DASM source companion requires tracked implementation files')
    revision=subprocess.run(['git','-C',str(root),'rev-parse','HEAD'],check=True,capture_output=True,text=True).stdout.strip()
    manifest={'schema':1,'repository_commit':revision,'files':{n:hashlib.sha256(v).hexdigest() for n,v in sorted(files.items())}}
    files['DASM-SOURCE-MANIFEST.json']=(json.dumps(manifest,indent=2)+'\n').encode()
    content=io.BytesIO()
    with tarfile.open(fileobj=content,mode='w') as archive:
        for name,data in sorted(files.items()):
            info=tarfile.TarInfo('BetterCPM-source/'+name);info.size=len(data);info.mode=0o644
            info.mtime=info.uid=info.gid=0;info.uname=info.gname=''
            archive.addfile(info,io.BytesIO(data))
    return {'BetterCPM-DASM-SOURCE.tar.gz':gzip.compress(content.getvalue(),mtime=0),
        'DASM-Provenance.json':(root/'third_party/dasm/provenance.json').read_bytes(),
        'DASM-SOURCE-README.txt':(
            'Maintained BetterCP/M DASM, DSYM and DLINK source companion\n\n'
            'Extract BetterCPM-DASM-SOURCE.tar.gz. It contains the complete tracked\n'
            'repository source, build helpers, metadata, tests, documentation and\n'
            'unaltered historical imports, with a per-file SHA-256 manifest.\n'
            'See docs/engineering/DASM Implementation Status.md for build/test\n'
            'commands and the exact qualification limits. Do not interpret this\n'
            'source package or the provisional images as full release acceptance.\n'
            'Original DASM credits/provenance remain under third_party/dasm.\n'
            'The SIG/M submission file is an unsigned generic template.\n'
            'ZSM4 4.7 and DRI LINK 1.3 retain their upstream versions/notices.\n'
        ).encode()}
