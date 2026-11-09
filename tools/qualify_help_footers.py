#!/usr/bin/env python3
"""Exercise the shipped cpmsim quick references with the optional library removed."""
import argparse
import json
import re
from pathlib import Path
import shutil
import subprocess
import tempfile

from build_distribution import MANIFEST
from build_utilities_disk import COMPONENTS as UTILITIES
from noah_distribution import COMPONENTS as COMPANION
from build_z80pack_image import DEFAULT_FORMAT, disk_definition
from fdf_format import select_fdf
from test_z80pack_sysgen_install import session
from utility_help import RESIDENT_SCREENS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for volume in ('system', 'utilities', 'companion', 'simulator'):
        parser.add_argument('--'+volume, type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text())
    system = [item['name'] for item in manifest['system_disk']
              if item['status'] == 'implemented' and 'z80pack' in item['targets']]
    packaged = {name[:-4]: drive for drive, files in
                [('A', system), ('B', UTILITIES), ('C', COMPANION)]
                for name in files if name.endswith('.COM')}
    queries = [(drive+'0:'+name, name) for name, drive in sorted(packaged.items())
               if name not in ('ZSM4', 'LINK', 'HELP')]
    queries += [(name, name) for name in RESIDENT_SCREENS]

    with tempfile.TemporaryDirectory(prefix='help-footers-') as temporary:
        work = Path(temporary)
        disks = work/'disks'
        disks.mkdir()
        (work/'diskdefs').write_text(disk_definition(select_fdf(MANIFEST.parent/'DISK.FDF', DEFAULT_FORMAT)))
        for letter, image in zip('abc', (args.system, args.utilities, args.companion)):
            shutil.copyfile(image, disks/f'drive{letter}.dsk')
        def remove(letter, name):
            subprocess.run(['cpmrm','-T','raw','-f','bettercpm-default',
                            str(disks/f'drive{letter}.dsk'),'0:'+name],cwd=work,check=True)
        remove('c','HELP.LBR')
        prompt = b'A0>_ '
        def verify(commands):
            steps = []
            for command, topic in commands:
                for switch in ('/H', '/HELP'):
                    line = ('For detailed help, see HELP '+topic+'\r\n').encode()
                    steps += [((command+' '+switch+'\r').encode(), line, 12), (b'',prompt,12)]
            output = session(args.simulator.resolve(), disks, steps)
            final_lines = re.findall(rb'For detailed help, see HELP ([A-Z0-9]+)\r*\n(?:\r*\n)*A0>', output)
            assert final_lines == [topic.encode() for _, topic in commands for _ in range(2)], final_lines
        verify([('HELP','HELP')])
        remove('a','HELP.COM')
        verify(queries)
    print(f'PASS: HELP with no library, {len(queries)} external and resident quick references '
          'with HELP removed, both /H and /HELP.')


if __name__ == '__main__':
    main()
