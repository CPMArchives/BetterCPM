#!/usr/bin/env python3
"""Archive bounded TED foundation evidence without asserting editor acceptance."""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile

from build_ted import ROOT, source, verify_reference, native_source
from dasm_native import compact_source, cpm_text


def sha(data):
    return hashlib.sha256(data).hexdigest()


def collect(native, host, destination):
    native = native.resolve()
    report = json.loads((native/'report.json').read_text())
    unit = json.loads(host.read_text())
    assert report['status'] == unit['status'] == 'PASS'
    assert report['editor_qualified'] is unit['editor_qualified'] is False
    assert set(report['platforms']) == {'z80pack', 'trs80gp'}
    prepared, _ = source()
    assert (native/'cross/TEDDEV.MAC').read_bytes() == prepared.encode('ascii')
    binary = (native/'cross/TEDDEV.COM').read_bytes()
    assert sha(binary) == unit['executable_sha256'] == report['cross_sha256']
    assert sha(prepared.encode('ascii')) == unit['prepared_source_sha256']
    expected_native = cpm_text(compact_source(native_source(prepared)))
    for platform, result in report['platforms'].items():
        assert result['status'] == 'PASS' and result['native_cross_parity']
        assert result['editor_qualified'] is False
        assert (native/platform/'TEDNAT.MAC').read_bytes() == expected_native
        actual = (native/platform/'after-TEDDEV.COM').read_bytes()
        assert actual[:len(binary)] == binary
        assert len(actual) == (len(binary)+127)//128*128
        assert set(actual[len(binary):]) <= {26}
        execution = json.loads((native/platform/'execution.json').read_text())
        assert execution['original_media_unchanged']
        assert execution['outputs']['TEDDEV.COM'] == sha(actual)
        assert execution['console_sha256'] == sha((native/platform/'console.bin').read_bytes())
    reference = verify_reference()
    inputs = sorted((ROOT/'src/utilities/ted').glob('*'))
    inputs += [ROOT/path for path in (
        'tools/build_ted.py', 'tools/build_native_ted.py', 'tools/test_ted_foundation.py',
        'tools/collect_ted_foundation.py', 'tools/dasm_native.py',
        'tools/test_usq.py', 'tools/test_usq_com.py',
        'tools/run_trs80_command.py', 'tools/trs80gp_launch.py',
        'tools/test_z80pack_sysgen_install.py', 'third_party/ted/provenance.json')]
    entries = {'host/test-report.json': host.read_bytes()}
    for path in sorted(native.rglob('*')):
        if path.is_file() and not path.is_symlink():
            entries['native/'+str(path.relative_to(native))] = path.read_bytes()
    for path in inputs:
        entries['inputs/'+str(path.relative_to(ROOT))] = path.read_bytes()
    manifest = {name: {'bytes': len(data), 'sha256': sha(data)} for name, data in sorted(entries.items())}
    entries['MANIFEST.json'] = (json.dumps(manifest, indent=2)+'\n').encode()
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode='wb', filename='', mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode='w') as archive:
            for name, data in sorted(entries.items()):
                info = tarfile.TarInfo(name)
                info.size, info.mode, info.mtime = len(data), 0o644, 0
                archive.addfile(info, io.BytesIO(data))
    destination.mkdir(parents=True, exist_ok=True)
    archive = destination/'TED-Foundation-Evidence.tar.gz'
    archive.write_bytes(buffer.getvalue())
    current = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
    receipt = {'schema': 1, 'status': 'PARTIAL_IMPLEMENTATION', 'editor_qualified': False,
               'scope': 'startup, workspace/cache foundation, native build/parity and legacy prompt exit only',
               'upstream_commit': reference['commit'], 'upstream_archive_sha256': reference['archive_sha256'],
               'base_repository_commit': current,
               'source_binding': 'actual input hashes; base commit does not assert a clean source tree',
               'source_inputs': {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in inputs},
               'payload': {'bytes': len(binary), 'sha256': sha(binary)},
               'host_gate': unit, 'native_gate': report,
               'archive': {'name': archive.name, 'bytes': archive.stat().st_size,
                           'sha256': sha(archive.read_bytes()), 'manifest_entries': len(manifest)},
               'not_qualified': ['WordStar commands/oracle', 'text preservation', '4095-byte lines',
                                 'DU/attributes/aliases', 'transactional publisher and recovery',
                                 'real full-media failures', 'native stack bounds', 'ANSI full-screen editing',
                                 'final Utilities membership/source companions', 'physical hardware']}
    (destination/'TED-Foundation.json').write_text(json.dumps(receipt, indent=2)+'\n')
    return receipt


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--native', type=Path, required=True)
    p.add_argument('--host', type=Path, required=True)
    p.add_argument('--destination', type=Path, default=ROOT/'docs/engineering')
    a = p.parse_args()
    result = collect(a.native, a.host, a.destination)
    print(result['status'], result['archive']['sha256'])
