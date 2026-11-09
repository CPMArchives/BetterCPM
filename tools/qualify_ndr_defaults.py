#!/usr/bin/env python3
"""Boot private checked cpmsim media and qualify embedded NDR startup defaults."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from build_ccp import ROOT as BUILD_ROOT
from build_z80pack_image import DEFAULT_FORMAT, disk_definition
from fdf_format import select_fdf
from startup_record import build as startup_record
from system_layout import LAYOUT
from test_z80pack_sysgen_install import session
from build_stateful_test_rsx import symbols


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--simulator',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    root=BUILD_ROOT;fmt=select_fdf(root/'metadata/DISK.FDF',DEFAULT_FORMAT)
    payload=bytearray((root/'build/z80pack/system-package/system-tracks.bin').read_bytes())
    payload[128:384]=startup_record('',system_base=LAYOUT['SYSTEM'])
    raw=bytearray(b'\xe5'*fmt.image_bytes)
    for record in range(160):
        track,within=divmod(record,fmt.spt)
        at=track*fmt.raw_track_bytes+fmt.raw_record_map()[within]*128
        raw[at:at+128]=payload[128*record:128*(record+1)]
    (out/'diskdefs').write_text(disk_definition(fmt))
    disks=out/'disks';disks.mkdir()
    for drive in 'abcd':(disks/f'drive{drive}.dsk').write_bytes(raw)
    def tool(name,*arguments):
        return subprocess.check_output([name,'-f','bettercpm-default',*map(str,arguments)],cwd=out)
    files={name:root/path for name,path in {
        'NDR.COM':'build/utilities/NDR.COM','NDR.RSX':'build/rsx/NDR.RSX',
        'RSX.COM':'build/utilities/RSX.COM','RCP.CPX':'build/cpx/RCP.CPX',
        'R3PACK.RSX':'build/system/R3PACK.RSX','R3CACHE.RSX':'build/system/R3CACHE.RSX'
    }.items()}
    # Install complete CP/M records, avoiding cpmtools' optional byte-count
    # extension when comparing record data before and after sequential writes.
    data=files['NDR.RSX'].read_bytes()
    carrier=out/'input-NDR.RSX'
    carrier.write_bytes(data.ljust((len(data)+127)//128*128,b'\x1a'))
    files['NDR.RSX']=carrier
    for name,path in files.items():tool('cpmcp',disks/'drivea.dsk',path,'0:'+name)
    tool('cpmcp',disks/'driveb.dsk',files['NDR.RSX'],'2:NDR.RSX')
    tool('cpmchattr',disks/'driveb.dsk','13sa','2:NDR.RSX')
    tool('cpmcp',disks/'driveb.dsk',files['NDR.RSX'],'3:READONLY.RSX')
    tool('cpmchattr',disks/'driveb.dsk','r','3:READONLY.RSX')
    originals={}
    for drive,user,stem in [('a',0,'NDR'),('b',2,'NDR'),('b',3,'READONLY')]:
        dest=out/f'before-{drive}{user}-{stem}.RSX'
        tool('cpmcp',disks/f'drive{drive}.dsk',f'{user}:{stem}.RSX',dest)
        originals[drive,user]=dest.read_bytes()
    steps=[]
    def step(command,expected=None,prompt='A0 [COMMANDS]> _ '):
        steps.append((command,expected,prompt))
    step('RSX LOAD NDR',prompt='A0> _ ')
    step('NDR COMMANDS A0:','updated')
    step('NDR UTILS B31:','updated')
    step('NDR /SAVE SNAPSHOT','set saved.')
    step('NDR /DEFAULT B3:READONLY.RSX','read-only; defaults unchanged.')
    step('NDR /DEFAULT B2:NDR.RSX','defaults saved; effective on next provider load.')
    step('NDR /DEL UTILS','updated')
    step('NDR','NDR: 1 of 32 names in use.')
    step('RSX UNLOAD NDR',prompt='A0> _ ')
    step('RSX LOAD B2:NDR')
    step('NDR','NDR: 2 of 32 names in use.')
    step('NDR /DEL COMMANDS','updated',prompt='A0> _ ')
    step('NDR ROOT A0:','updated',prompt='A0 [ROOT]> _ ')
    step('NDR /DEFAULT B2:NDR.RSX','defaults saved;',prompt='A0 [ROOT]> _ ')
    step('RSX UNLOAD NDR',prompt='A0> _ ')
    step('RSX LOAD B2:NDR',prompt='A0 [ROOT]> _ ')
    step('NDR','NDR: 2 of 32 names in use.',prompt='A0 [ROOT]> _ ')
    step('NDR /CLEAR','updated',prompt='A0> _ ')
    step('NDR /DEFAULT B2:NDR.RSX','defaults saved;',prompt='A0> _ ')
    step('RSX UNLOAD NDR',prompt='A0> _ ')
    step('RSX LOAD B2:NDR',prompt='A0> _ ')
    step('NDR','NDR: 0 of 32 names in use.',prompt='A0> _ ')
    step('NDR /LOAD SNAPSHOT','set loaded.')
    step('NDR /DEFAULT A0:NDR.RSX','defaults saved;')
    commands=[]
    for command,expected,prompt in steps:
        commands.append(((command+'\r').encode(),(expected or prompt).encode(),30))
        if expected:commands.append((b'',prompt.encode(),30))
    session(a.simulator.resolve(),disks,commands,out/'session.txt',initial_prompt=b'A0> _ ')
    exports={}
    for drive,user,stem in [('a',0,'NDR'),('b',2,'NDR'),('b',3,'READONLY')]:
        dest=out/f'{drive}{user}-{stem}.RSX'
        tool('cpmcp',disks/f'drive{drive}.dsk',f'{user}:{stem}.RSX',dest)
        exports[drive,user]=dest.read_bytes()
    original=originals['a',0]
    table_offset=512+symbols(root/'build/rsx/ndr.lst')['NR_TABLE']-0x8000
    expected=bytearray(original)
    table=(b'COMMANDS'+bytes((1,0))+b'UTILS   '+bytes((2,31))).ljust(320,b'\0')
    expected[table_offset:table_offset+320]=table
    expected[44:46]=(sum(expected[512:512+int.from_bytes(expected[12:14],'little')])&65535).to_bytes(2,'little')
    assert exports['a',0]==expected
    assert exports['b',2]==originals['b',2]
    assert exports['b',3]==originals['b',3]
    listing=tool('cpmls','-l',disks/'driveb.dsk','2:*').decode()
    assert '$nd' not in listing.lower() and '$nb' not in listing.lower()
    # Verify attributes in the actual directory, independently of the guest.
    disk=(disks/'driveb.dsk').read_bytes()
    attrs=[]
    for i in range(fmt.drm+1):
        track,within=divmod(fmt.off*fmt.spt+i//4,fmt.spt)
        at=track*fmt.raw_track_bytes+fmt.raw_record_map()[within]*128+(i%4)*32
        entry=disk[at:at+32]
        if entry[0]==2 and bytes(v&127 for v in entry[1:12])==b'NDR     RSX':
            attrs.append([v&128 for v in entry[1:12]])
    assert attrs and all(value==[128,0,128,0,0,0,0,0,0,128,128] for value in attrs),attrs
    # The ordinary saved set is removed before a fresh boot: only RSX LOAD is used.
    tool('cpmrm',disks/'drivea.dsk','0:SNAPSHOT.NDR')
    cold=session(a.simulator.resolve(),disks,[(b'RSX LOAD NDR\r',b'A0 [COMMANDS]> _ ',30),
        (b'NDR\r',b'NDR: 2 of 32 names in use.',30),(b'',b'A0 [COMMANDS]> _ ',30)],
        out/'cold.txt',initial_prompt=b'A0> _ ')
    assert b'COMMANDS A0:' in cold and b'UTILS    B31:' in cold
    result={'status':'PASS','scope':'private booted checked cpmsim development media',
        'steps':len(steps),'cold_load_without_ndr_file':True,'repeat_update':True,
        'empty_defaults':True,'read_only_rejected':True,'caller_du_restored':True,
        'carrier_unrelated_bytes_preserved':True,'file_attributes_preserved':True,
        'input_sha256':{name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in files.items()},
        'embedded_carrier_sha256':hashlib.sha256(exports['a',0]).hexdigest()}
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
