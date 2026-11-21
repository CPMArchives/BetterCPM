"""Short final-System smoke on private copies; does not promote acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--simulator',type=Path)
    args=parser.parse_args();folder=args.system.resolve();out=args.output.resolve()
    out.mkdir(parents=True,exist_ok=False)
    receipt=json.loads((folder/'report.json').read_text())
    image=folder/receipt['image'];target=receipt['target'];original=sha(image)
    assert original==receipt['sha256']
    result={'source_commit':receipt['source']['revision'],'target':target,
            'system_sha256':original,'status':'RUNNING','scope':'boot/identity, default memory, CONFIG F, NDR/PATH, HELP VAR and ordinary COM; no broad qualification'}
    def save():(out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    save()
    try:
        if target=='z80pack':
            from test_z80pack_sysgen_install import session
            assert args.simulator
            disks=out/'disks';disks.mkdir()
            root=Path(receipt['build_root'])
            shutil.copyfile(image,disks/'drivea.dsk')
            for letter in 'bcd':shutil.copyfile(root/f'build/z80pack/disks/drive{letter}.dsk',disks/f'drive{letter}.dsk')
            # The 332K System intentionally keeps HELP.LBR on Companion C:.
            # Stage only that matching-built archive as a disposable fixture;
            # this does not qualify a final Companion Utilities package.
            shutil.copyfile(folder/'diskdefs',disks/'diskdefs')
            library=root/'build/help/HELP.LBR'
            subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(disks/'drivec.dsk'),str(library),'0:HELP.LBR'],cwd=disks,check=True)
            result['supplemental_help_fixture_sha256']=sha(library)
            commands=[(b'VER\r',b'A0> _ ',60),(b'STAT MEM\r',b'A0> _ ',60),
                      (b'CONFIG\r',b'Your choice:',60),(b'F',b'Active H/M/V bytes: 192 0 0',60),
                      (b'\x03\x03',b'A0> _ ',60),(b'RSX LOAD NDR\r',b'A0> _ ',60),
                      (b'NDR WORK A0:\r',b'A0 [WORK]> _ ',60),(b'PATH\r',b'A0 [WORK]> _ ',60),
                      (b'RSX UNLOAD NDR\r',b'A0> _ ',60),(b'HELP VAR\r',b'Enable variables',60),
                      (b'Q',b'A0> _ ',60),(b'STAT /VER\r',b'A0> _ ',60)]
            text=session(args.simulator.resolve(),disks,commands,out/'transcript.txt').decode(errors='replace')
            texts=[text]
        else:
            from run_trs80_command import DEFAULT_EMULATOR,key_args
            from trs80gp_launch import run
            from test_config_startup_read import screen
            disk=out/('a.imd' if target=='trs80m2' else 'a.dmk');shutil.copyfile(image,disk)
            command=[str(DEFAULT_EMULATOR),'-m2' if target=='trs80m2' else '-m4']
            if target=='trs80m2':
                from run_model2_qualification import EMU,EMU_SHA
                assert sha(EMU)==EMU_SHA,'Model II emulator differs from qualified baseline'
                command[0]=str(EMU);command+=['-mem','64','-itime','45000']
            command+=['-batch','-turbo','-d0',str(disk),'-iw','Type TYPE README.TXT','-id','3000','-it']
            steps=['VER\r']
            if target=='trs80gp':steps+=['RSX UNLOAD ADM3A\r']
            steps+=['STAT MEM\r','CONFIG\r','F','\x03\x03','RSX LOAD NDR\r',
                    'NDR WORK A0:\r','PATH\r','HELP VAR\r','Q','STAT /VER\r']
            for step in steps:
                command+=(['-i',step] if target=='trs80m2' else key_args(step))
                command+=['-id','25000' if step.startswith('RSX ') else '8000','-it']
            command+=['-ix'];run(command,cwd=out,timeout=480,check=True)
            texts=[screen(path) for path in sorted(out.glob('trs80-text-*.bin'))]
            for index,text in enumerate(texts):(out/f'screen-{index}.txt').write_text(text)
        text='\n'.join(texts)
        expected=['1.3','candidate','Active H/M/V bytes: 192 0 0','WORK',
                  'Enable variables','STAT 1.0','54272 bytes' if target=='trs80gp' else '57344 bytes']
        for phrase in expected:assert phrase in text,('missing smoke result',phrase,text[-5000:])
        assert sha(image)==original,'source System image changed'
        result.update(status='PASS_FOCUSED_SYSTEM_SMOKE',observed=expected,
                      source_image_unchanged=True,final_release_acceptance='PENDING')
    except Exception as error:
        result.update(status='FAIL',error=str(error));save();raise
    save();print(target,result['status'],original,flush=True)


if __name__=='__main__':main()
