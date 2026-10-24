#!/usr/bin/env python3
"""Real catalogue/backend qualification of named logical CONFIG commands."""
import argparse,json,re,shutil,struct,subprocess,tempfile
from pathlib import Path
from qualify_config_physical_cli import state_probe
from fdf_format import select_fdf
from build_z80pack_image import DEFAULT_FORMAT
from fdf_v1 import crc16
from startup_record import build as startup
from system_layout import LAYOUT
from test_z80pack_sysgen_install import session
ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser();p.add_argument('--diskdefs',type=Path,required=True);a=p.parse_args()
    parent=ROOT/'build/config-logical-cli';parent.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix='run-',dir=parent));probe=state_probe(work)
    fmt=select_fdf(ROOT/'third_party/montezuma/DISK.FDF',DEFAULT_FORMAT)
    def offset(n):
        track,i=divmod(n,fmt.spt);return track*fmt.raw_track_bytes+fmt.raw_record_map()[i]*128
    template=ROOT/'build/z80pack/disks/library/BetterCPM-Distribution-z80pack-332K.dsk'
    catalogue=(ROOT/'build/catalog/DISK.FDB').read_bytes()
    definitions=json.loads((ROOT/'metadata/mm-builtin-formats.json').read_text())['formats']
    definition=next(d for d in definitions if d['name']=='Montezuma Micro 80T DS DATA (80T, DS, DD, 800K)');v=definition['parameters']
    expected_binding=b'\1'+struct.pack('<HBBBHHBBHH',*v[:10])+bytes((v[12],v[10],v[11],v[13]))+bytes(definition['sector_ids']).ljust(32,b'\0')+bytes(12)
    results=[]
    for name in ('bind','unbind','unknown','ambiguous','incompatible','missing','bad-crc'):
        here=work/name;here.mkdir();disks=here/'disks';disks.mkdir();image=disks/'drivea.dsk';shutil.copy2(template,image)
        shutil.copy2(a.diskdefs,here/'diskdefs')
        for label in ('CONFIG.COM','DISK.FDB'):
            subprocess.run(['cpmrm','-T','raw','-f','bettercpm-default',str(image),'0:'+label],cwd=here,check=True)
        files=[('CONFIG.COM',(ROOT/'build/utilities/CONFIG.COM').read_bytes()),('STATE.COM',probe)]
        if name not in ('missing','unbind'):
            data=bytearray(catalogue)
            if name=='bad-crc':data[-1]^=1
            if name=='ambiguous':
                stride=data[7];data[128+stride+8:128+stride+40]=b'MM 80T DS DATA'.ljust(32,b' ')
                data[128+8:128+40]=b'MM 80T DS DATA'.ljust(32,b' ')
                data[14:16]=b'\0\0';data[14:16]=crc16(data).to_bytes(2,'little')
            files.append(('DISK.FDB',data))
        for label,data in files:
            path=here/label;path.write_bytes(data)
            subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(image),str(path),'0:'+label],cwd=here,check=True)
        data=bytearray(image.read_bytes());bcst=startup('',system_base=LAYOUT['SYSTEM'])
        for i,n in enumerate((1,2)):data[offset(n):offset(n)+128]=bcst[i*128:(i+1)*128]
        image.write_bytes(data);before=bytes(data)
        command=b'CONFIG /LOGICAL=C /PHYSICAL=1 /FORMAT="mm 80t ds data"\r'
        if name=='unbind':command=b'CONFIG /LOGICAL=C /UNBIND\r'
        if name=='unknown':command=b'CONFIG /LOGICAL=C /PHYSICAL=1 /FORMAT="No such format"\r'
        commands=[]
        if name=='bind':commands.append((b'CONFIG /PHYSICAL=1 /TRACKS=80\r',b'A0>_ ',20))
        commands += [(b'STATE\r',b'A0>_ ',20),(command,b'A0>_ ',20),
                     (b'STATE\r',b'A0>_ ',20),(b'BYE /Y\r',b'System halted',10)]
        trace=session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',disks,commands,here/'transcript.bin')
        states=[bytes.fromhex(s.decode()) for s in re.findall(rb'STATE ([0-9A-F]{560})',trace)]
        assert len(states)==2,trace
        old,new=states;expected=bytearray(old);at=24+2*64
        if name=='bind':expected[at:at+64]=expected_binding
        elif name=='unbind':expected[at]=255
        else:assert b'Nothing changed.' in trace or b'DISK.FDB' in trace,trace
        assert new==bytes(expected),(name,new.hex(),bytes(expected).hex(),trace)
        assert image.read_bytes()==before,(name,'CLI saved disk bytes')
        assert b'Push ENTER' not in trace and b'(Y/N)?' not in trace,trace
        if name in ('bind','unbind'):assert b'until cold boot' in trace,trace
        if name=='ambiguous':assert b'ambiguous' in trace,trace
        if name=='bad-crc':assert b'invalid framing or CRC' in trace,trace
        if name=='missing':assert b'Cannot open DISK.FDB' in trace,trace
        if name=='bind':
            cold=session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',disks,
                         [(b'STATE\r',b'A0>_ ',20),(b'BYE /Y\r',b'System halted',10)],here/'cold.bin')
            state=bytes.fromhex(re.findall(rb'STATE ([0-9A-F]{560})',cold)[0].decode())
            assert state[24:]==old[24:],'logical binding persisted across cold boot'
        results.append({'case':name,'result':'PASS'})
    (work/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    print('PASS: named logical bind/unbind, catalogue unknown/duplicate/missing/CRC errors, incompatible geometry, no disk writes and cold reset;',work)


if __name__=='__main__':main()
