#!/usr/bin/env python3
"""Real backend qualification of scalar CONFIG workbench commands."""
import argparse,json,re,shutil,subprocess,tempfile
from pathlib import Path
from qualify_config_physical_cli import state_probe
from fdf_format import select_fdf
from build_z80pack_image import DEFAULT_FORMAT
from startup_record import build as startup
from system_layout import LAYOUT
from test_z80pack_sysgen_install import session
ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser();p.add_argument('--diskdefs',type=Path,required=True);a=p.parse_args()
    parent=ROOT/'build/config-edit-cli';parent.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix='run-',dir=parent));probe=state_probe(work)
    fmt=select_fdf(ROOT/'third_party/montezuma/DISK.FDF',DEFAULT_FORMAT)
    def offset(n):
        track,i=divmod(n,fmt.spt);return track*fmt.raw_track_bytes+fmt.raw_record_map()[i]*128
    template=ROOT/'build/z80pack/disks/library/BetterCPM-Distribution-z80pack-332K.dsk'
    results=[]
    for name in ('edit','invalid','backend-reject','boot-protected'):
        here=work/name;here.mkdir();disks=here/'disks';disks.mkdir();image=disks/'drivea.dsk';shutil.copy2(template,image)
        shutil.copy2(a.diskdefs,here/'diskdefs')
        for label in ('CONFIG.COM','DISK.FDB'):
            subprocess.run(['cpmrm','-T','raw','-f','bettercpm-default',str(image),'0:'+label],cwd=here,check=True)
        files=[('CONFIG.COM',(ROOT/'build/utilities/CONFIG.COM').read_bytes()),('STATE.COM',probe)]
        for label,data in files:
            path=here/label;path.write_bytes(data)
            subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(image),str(path),'0:'+label],cwd=here,check=True)
        data=bytearray(image.read_bytes());bcst=startup('',system_base=LAYOUT['SYSTEM'])
        for i,n in enumerate((1,2)):data[offset(n):offset(n)+128]=bcst[i*128:(i+1)*128]
        image.write_bytes(data);before=bytes(data)
        command=b'CONFIG /EDIT=B /CKS=16\r'
        if name=='invalid':command=b'CONFIG /EDIT=B /CKS=16 /BSH=256\r'
        if name=='backend-reject':command=b'CONFIG /EDIT=B /SPT=0\r'
        if name=='boot-protected':command=b'CONFIG /EDIT=A /CKS=16\r'
        commands=[(b'STATE\r',b'A0>_ ',20),(command,b'A0>_ ',20),
                  (b'STATE\r',b'A0>_ ',20),(b'BYE\r',b'System halted',10)]
        trace=session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',disks,commands,here/'transcript.bin')
        states=[bytes.fromhex(s.decode()) for s in re.findall(rb'STATE ([0-9A-F]{560})',trace)]
        assert len(states)==2,trace
        old,new=states;expected=bytearray(old);at=24+64
        if name=='edit':expected[at+12:at+14]=(16).to_bytes(2,'little')
        elif name=='backend-reject':assert b'Nothing changed.' in trace,trace
        else:assert b'Invalid CONFIG usage.' in trace,trace
        assert new==bytes(expected),(name,new.hex(),bytes(expected).hex(),trace)
        assert image.read_bytes()==before,(name,'CLI saved disk bytes')
        assert b'Push ENTER' not in trace and b'(Y/N)?' not in trace,trace
        if name=='edit':
            assert b'until cold boot' in trace,trace
            cold=session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',disks,
                         [(b'STATE\r',b'A0>_ ',20),(b'BYE\r',b'System halted',10)],here/'cold.bin')
            state=bytes.fromhex(re.findall(rb'STATE ([0-9A-F]{560})',cold)[0].decode())
            assert state==old,'workbench edit persisted across cold boot'
        results.append({'case':name,'result':'PASS'})
    (work/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    print('PASS: scalar workbench edit, invalid/boot/backend rejection, no disk writes and cold reset;',work)


if __name__=='__main__':main()
