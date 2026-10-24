#!/usr/bin/env python3
"""Independently audit shipped System files after packaged tool execution."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from add_cpm_file_to_dmk import extract_raw


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--system', type=Path, required=True)
    p.add_argument('--campaign', type=Path, required=True)
    a = p.parse_args()
    a.system = a.system.expanduser().resolve()
    a.campaign = a.campaign.expanduser().resolve()
    result = {}
    campaign = json.loads((a.campaign / 'report.json').read_text())
    for platform, receipt in campaign['platforms'].items():
        report = json.loads((a.system / platform / 'report.json').read_text())
        for case in receipt['cases']:
            w = a.campaign / platform / case
            native = platform == 'trs80gp'
            raw = w / 'audit.raw'
            raw.write_bytes(extract_raw((w / 'a.dmk').read_bytes()) if native
                            else (w / 'disks/drivea.dsk').read_bytes())
            definition = 'toolchain-system' if native else 'bettercpm-default'
            checked = []
            for file in report['included']:
                # The native startup script is an explicit test fixture.
                if native and file['name'] == 'STARTUP.SUB':
                    continue
                output = w / ('audit-' + file['name'])
                subprocess.run(['cpmcp','-T','raw','-f',definition,str(raw),
                                str(file['user'])+':'+file['name'],str(output)],
                               cwd=w, check=True, capture_output=True)
                data = output.read_bytes()
                assert hashlib.sha256(data[:file['bytes']]).hexdigest() == file['sha256'], (platform, case, file['name'])
                assert file['bytes'] <= len(data) <= (file['bytes']+127)//128*128
                assert set(data[file['bytes']:]) <= {0, 0x1a}
                checked.append(file['name'])
            listing = subprocess.run(['cpmls','-f',definition,str(raw)], cwd=w,
                                     check=True, capture_output=True).stdout
            assert b'$$$' not in listing, (platform,case,'batch queue not cleaned')
            result[platform+'/'+case] = {'status':'PASS','shipped_files_unchanged':checked,
                                         'batch_queue_cleanup':'PASS'}
    (a.campaign / 'system-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(f'PASS: shipped System file bytes and batch cleanup in {len(result)} native-tool work disks')


if __name__ == '__main__':
    main()
