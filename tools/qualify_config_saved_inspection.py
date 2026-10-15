#!/usr/bin/env python3
"""Inspect saved CONFIG defaults without writes, including differing active state."""
import argparse
import json
import re
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path
from fdf_format import select_fdf
from build_z80pack_image import DEFAULT_FORMAT
from startup_record import build
from config_validation import validation_record
from system_layout import LAYOUT
from test_config_sysgen import probe
from test_z80pack_sysgen_install import session
ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser();p.add_argument('--diskdefs',type=Path,required=True);a=p.parse_args()
    parent=ROOT/'build/config-saved-inspection';parent.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix='run-',dir=parent))
    fmt=select_fdf(ROOT/'third_party/montezuma/DISK.FDF',DEFAULT_FORMAT)
    def offset(record):
        track,within=divmod(record,fmt.spt)
        return track*fmt.raw_track_bytes+fmt.raw_record_map()[within]*128
    original=(ROOT/'build/z80pack/disks/library/BetterCPM-Distribution-z80pack-332K.dsk').read_bytes()
    carrier=b''.join(original[offset(r):offset(r)+128] for r in range(8,60))
    record=validation_record(carrier,LAYOUT['SYSTEM'],52,8,fmt.spt)
    config=(ROOT/'build/utilities/CONFIG.COM').read_bytes()
    assert config.count(record)==1,'build CONFIG with matching cpmsim fingerprint first'
    signature=carrier.index(b'BDCF'+bytes((5,4,4,64)))
    physical=struct.unpack_from('<H',carrier,signature+8)[0]-LAYOUT['SYSTEM']
    saved_delay=carrier[physical+6+5]
    results=[]
    for name in ('different','wrong-crc','wrong-layout'):
        here=work/name;here.mkdir();disks=here/'disks';disks.mkdir()
        shutil.copy2(a.diskdefs,here/'diskdefs');image=disks/'drivea.dsk';image.write_bytes(original)
        subprocess.run(['cpmrm','-T','raw','-f','bettercpm-default',str(image),'0:CONFIG.COM'],cwd=here,check=True)
        def install(label,data):
            path=here/label;path.write_bytes(data)
            subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(image),str(path),'0:'+label],cwd=here,check=True)
        # Prove inspection is independent of the old reference, even when the
        # template is a pre-CRC disk which still carries that file.
        listing=subprocess.run(['cpmls','-T','raw','-f','bettercpm-default',str(image)],cwd=here,check=True,capture_output=True).stdout.lower().split()
        if b'sysgen.dat' in listing:
            subprocess.run(['cpmrm','-T','raw','-f','bettercpm-default',str(image),'0:SYSGEN.DAT'],cwd=here,check=True)
        data=bytearray(config);at=config.index(record)
        if name=='wrong-crc':data[at+16]^=1
        if name=='wrong-layout':data[at+10]^=1
        install('CONFIG.COM',data)
        setup=probe(here,fault=False)
        install('SETUP.COM',setup)
        data=bytearray(image.read_bytes());startup=build('',system_base=LAYOUT['SYSTEM'])
        for i,r in enumerate((1,2)):data[offset(r):offset(r)+128]=startup[i*128:(i+1)*128]
        image.write_bytes(data);before=bytes(data)
        trace=session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',disks,
                      [(b'SETUP\r',b'SYSGEN PROBE PASS',20),(b'\r',b'A0>_ ',20),
                       (b'CONFIG /SHOW\r',b'A0>_ ',30),(b'BYE\r',b'System halted',10)],here/'transcript.bin')
        assert image.read_bytes()==before,(name,'inspection changed image')
        assert b'Push ENTER' not in trace and b'(Y/N)?' not in trace,trace
        if name=='different':
            assert b'Saved physical-drive profiles:' in trace and b'Saved logical-drive bindings:' in trace,trace
            active=trace.split(b'Active physical-drive profiles:',1)[1].split(b'Active logical-drive bindings:',1)[0]
            saved=trace.split(b'Saved physical-drive profiles:',1)[1].split(b'Saved logical-drive bindings:',1)[0]
            delays=lambda text:[int(n) for n in re.findall(rb'Head settling time \(ms\): +([0-9]+)',text)]
            assert delays(active)[1]==20 and delays(saved)[1]==saved_delay,(active,saved)
            assert b'B: 2:' in trace.split(b'Active logical-drive bindings:',1)[1].split(b'Saved cold-start',1)[0]
            assert b'B: 1:' in trace.split(b'Saved logical-drive bindings:',1)[1]
        else:
            assert b'Saved physical-drive profiles:' not in trace,trace
            assert b'Boot disk does not match' in trace,trace
        results.append({'case':name,'result':'PASS'})
    (work/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    print('PASS: saved/active distinction, no reference file, wrong CRC/layout rejection, image unchanged;',work)


if __name__=='__main__':main()
