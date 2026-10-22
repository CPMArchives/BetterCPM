#!/usr/bin/env python3
"""Exercise shared CONFIG prompts under cpmsim on a private accepted System Disk."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
from test_z80pack_sysgen_install import session
ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=False);w=a.output.resolve();disks=w/'disks';disks.mkdir()
    shutil.copy2(a.baseline/'diskdefs',w/'diskdefs')
    source=a.baseline/'BetterCPM-Distribution-z80pack-332K.dsk';image=disks/'drivea.dsk';shutil.copy2(source,image)
    def run(*args):subprocess.run(args,cwd=w,check=True,capture_output=True)
    run('cpmrm','-T','raw','-f','bettercpm-default',str(image),'0:CONFIG.COM')
    run('cpmcp','-T','raw','-f','bettercpm-default',str(image),str(ROOT/'build/utilities/CONFIG.COM'),'0:CONFIG.COM')
    # Suppress startup SUBMIT: preserve this intentional fixture change in 'before'.
    from startup_record import build
    from fdf_format import select_fdf
    from build_z80pack_image import DEFAULT_FORMAT
    from system_layout import LAYOUT
    fmt=select_fdf(ROOT/'third_party/montezuma/DISK.FDF',DEFAULT_FORMAT)
    data=bytearray(image.read_bytes());record=build('',system_base=LAYOUT['SYSTEM'])
    for i in range(2):
        track,within=divmod(i+1,fmt.spt);at=track*fmt.raw_track_bytes+fmt.raw_record_map()[within]*128
        data[at:at+128]=record[i*128:(i+1)*128]
    image.write_bytes(data);before=bytes(data)
    commands=[(b'CONFIG /DEFAULT\r',b'Push ENTER for menu.',30),
              (b'\r',b'Your choice: [',20),(b'E',b'Command:',20),
              (b'Abc\x13\x07\x08Z\x04!\r',b'Your choice: [',20),
              (b'E',b'Command:',20),(b'Cancelled\x1b',b'Your choice: [',20),
              (b'\x03',b'Your choice: [',20),
              (b'B',b'Disk-boot IOBYTE (decimal):',30),
              (b'12X\r',b'Invalid decimal value.',20),
              (b'\x08\x03',b'Your choice: [',20),
              (b'\x03',b'A0>_ ',30),(b'BYE\r',b'System halted',20)]
    trace=session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',disks,commands,w/'transcript.bin')
    assert trace.count(b'Pending startup command: AZ!')>=2
    assert image.read_bytes()==before,'editing/cancellation wrote disk'
    run('fsck.cpm','-T','raw','-f','bettercpm-default','-n',str(image))
    report={'status':'PASS','platform':'cpmsim','bytes':(ROOT/'build/utilities/CONFIG.COM').stat().st_size,
            'program_sha256':hashlib.sha256((ROOT/'build/utilities/CONFIG.COM').read_bytes()).hexdigest(),
            'cases':['startup insertion/deletion and retained pending value','ESC cancellation','numeric invalid-input correction and Ctrl-C cancellation','exit without saving and unchanged disk','filesystem check'],
            'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
    (w/'results.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS: cpmsim CONFIG shared input and unchanged private disk;',w)


if __name__=='__main__':main()
