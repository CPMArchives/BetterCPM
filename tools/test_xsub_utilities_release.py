#!/usr/bin/env python3
"""Run packaged XSUB on both platforms with its exact BATCHIO companion."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
from add_cpm_file_to_dmk import extract_raw,add_file,FILESYSTEM_FIRST_SECTOR,SECTOR_SIZE,DIRECTORY_ENTRIES
from build_montezuma_extended_790k import build as system_dmk
from build_z80pack_image import disk_definition,DEFAULT_FORMAT
from fdf_format import select_fdf
from test_z80pack_sysgen_install import session
from test_z80pack_submit_xsub import input_probe
from test_submit_xsub import marker
from run_trs80_command import DEFAULT_EMULATOR,key_args
from trs80gp_launch import run as launch
ROOT=Path(__file__).resolve().parents[1]
sha=lambda b:hashlib.sha256(b).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('system','images','artifacts','output','simulator'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    fixtures={'INPUT.COM':input_probe(a.output),'MARK.COM':marker(a.output),
              'UBATCH.SUB':b'B:XSUB\r\nA:INPUT\r\nBATCHFULL\r\nA:MARK AFTER\r\n\x1a',
              # The documented provider placement is A0; use the exact packaged companion.
              'BATCHIO.RSX':(a.artifacts/'build/rsx/BATCHIO.RSX').read_bytes()}
    result={'status':'PASS','xsub_sha256':sha((a.artifacts/'build/utilities/XSUB.COM').read_bytes()),'batchio_sha256':sha(fixtures['BATCHIO.RSX']),'platforms':{}}
    for target in ('z80pack','trs80gp'):
        w=a.output/target;w.mkdir();report=json.loads((a.system/target/'report.json').read_text());source=a.system/target/report['image'];before=source.read_bytes()
        utility=next(a.images.glob('*'+target+('*.dsk' if target=='z80pack' else '*.dmk')));utility_before=utility.read_bytes()
        defs=disk_definition(select_fdf(ROOT/'third_party/montezuma/DISK.FDF',DEFAULT_FORMAT))+'''diskdef xsub-system
 libdsk:format pcw800
 seclen 512
 tracks 160
 sectrk 10
 blocksize 2048
 maxdir 128
 skew 1
 boottrk 4
 os 2.2
end
'''
        (w/'diskdefs').write_text(defs);native=target=='trs80gp';definition='xsub-system' if native else 'bettercpm-default'
        raw=w/'system.raw';raw.write_bytes(extract_raw(before) if native else before)
        def command(*args):return subprocess.run(list(map(str,args)),cwd=w,check=True,capture_output=True)
        for name,data in fixtures.items():
            path=w/name;path.write_bytes(data)
            # The System disk may already include the companion.
            command('cpmcp','-T','raw','-f',definition,raw,path,'0:'+name)
        if not native:
            disks=w/'disks';disks.mkdir();shutil.copy2(raw,disks/'drivea.dsk');shutil.copy2(utility,disks/'driveb.dsk')
            for letter in 'cd':shutil.copy2(utility,disks/f'drive{letter}.dsk')
            transcript=session(a.simulator,disks,[(b'B:XSUB /VER ignored\r',b'A0>_ ',30),
                (b'SUBMIT UBATCH\r',b'MARK: AFTER',60),(b'',b'A0>_ ',30)],w/'transcript.bin')
            assert b'INPUT OK' in transcript and b'INPUT FAILED' not in transcript
            assert (disks/'driveb.dsk').read_bytes()==utility_before
            shutil.copy2(disks/'drivea.dsk',raw)
        else:
            native_raw=bytearray(raw.read_bytes())
            directory=FILESYSTEM_FIRST_SECTOR*SECTOR_SIZE
            for i in range(DIRECTORY_ENTRIES):
                at=directory+i*32
                if native_raw[at]==0 and native_raw[at+1:at+12]==b'STARTUP SUB':native_raw[at]=0xe5
            add_file(native_raw,'STARTUP.SUB',b'RSX LOAD M4SCRN\r\nRSX LOAD ADM3A\r\n:VER /BANNER\r\nB:XSUB /VER ignored\r\nSUBMIT UBATCH\r\n\x1a')
            disk=w/'system.dmk';disk.write_bytes(system_dmk(native_raw));shutil.copy2(utility,w/'utilities.dmk')
            args=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-ktx','-d0',str(disk),'-d1',str(w/'utilities.dmk'),'-itime','60000',
                  '-iw','BetterCP/M XSUB 1.0','-id','120','-it','-iw','INPUT OK','-id','120','-it','-iw','MARK: AFTER','-id','1000','-it','-ix']
            (w/'invocation.json').write_text(json.dumps(args,indent=2)+'\n');launch(args,cwd=w,timeout=600)
            screens=b'\n'.join(bytes(c&127 for c in p.read_bytes()[:1920]) for p in sorted(w.glob('trs80-text*')))
            assert b'INPUT OK' in screens and b'MARK: AFTER' in screens and b'INPUT FAILED' not in screens
            assert (w/'utilities.dmk').read_bytes()==utility_before
            raw.write_bytes(extract_raw(disk.read_bytes()))
        for name,data in fixtures.items():
            output=w/('after-'+name);command('cpmcp','-T','raw','-f',definition,raw,'0:'+name,output)
            assert output.read_bytes()[:len(data)]==data,('fixture changed',name)
        listing=command('cpmls','-f',definition,raw).stdout.upper();assert b'$$$' not in listing
        command('fsck.cpm','-T','raw','-f',definition,'-n',raw)
        assert source.read_bytes()==before and utility.read_bytes()==utility_before
        result['platforms'][target]={'status':'PASS','system_sha256':sha(before),'utilities_sha256':sha(utility_before),'utilities_unchanged':True,'input_and_companion_unchanged':True,'queue_cleanup':'PASS','filesystem':'PASS'}
        (a.output/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS packaged XSUB /VER and protected Function-10 batch input on both platforms; exact BATCHIO installed on private A0, queues cleaned, Utilities unchanged')


if __name__=='__main__':main()
