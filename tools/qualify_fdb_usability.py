"""Run the 1.01 interactive workflows on private complete System media."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil
import subprocess
from add_cpm_file_to_dmk import extract_raw
from build_montezuma_extended_790k import build as make_dmk
from fdb_qualification_media import audit
from qualify_fdb_editor import state_probe
from run_trs80_command import DEFAULT_EMULATOR,key_args
from test_sysgen_install import screen
from test_z80pack_sysgen_install import session
from trs80gp_launch import run


def workflows():
    return [
        ('STATE','ENDSTATE'),
        ('FDB','Choice:'),('F','Open catalogue filename:'),
        ('A1:DISK.FDB','current DU:'),('A0:DISK.FDB','Choice:'),
        ('S','Return uses name above'),('','Replace entire file (Y/N)?'),
        ('Y','Recovery file already exists.'),
        ('L','Find ID or description'),('X'*33+'\x08\x7f','No matching formats.'),
        ('D','Source: catalogue ID,'),('MMI012','Q or BREAK Return:'),
        ('2','1-8/10'),('.','9-10/10'),('>','9-10/10'),
        (',','1-8/10'),('<','1-8/10'),('Z','Invalid choice; try again.'),
        ('Q','Choice:'),('P','Source: catalogue ID,'),
        ('MMI012','Source: catalogue ID,'),('MISSING','ID not found; select a source again.'),
        ('MMI012','Q or BREAK Return:'),('2','No map differences in this range.'),
        ('.','9-10/10'),('Q','Choice:'),('N','Entries: 0'),
        ('S','Filename required'),('','Filename required'),('\x03','Choice:'),
        ('F','Open catalogue filename:'),('A0:DISK.FDB','Choice:'),
        ('B','Source filename'),('','Catalogue ID:'),('MMI012','Q Back:'),
        ('A','Value 0-255'),('BOGUS','Value 0-255'),('G','Value 0 or 1'),
        ('1','Q Back:'),('V','DSM / allowed maximum: 394/389'),
        ('3','Q Back:'),('A','Value 0-65535'),('80','Q Back:'),('E','Value 0-65535'),('389','Q Back:'),
        ('V','Format validates.'),('Q','Choice:'),('Q','S Catalogue+write'),('D','A0>'),
        ('FDB','Choice:'),('A','Logical drive B, C or D:'),('B','Q Back:'),
        ('3','Q Back:'),('E','Value 0-65535'),('100','Q Back:'),
        ('S','D Apply active drive'),('D','Logical drive B, C or D:'),
        ('C','Active binding only'),('N','Q Back:'),
        ('Q','Choice:'),('Q','S Catalogue+write'),('D','A0>'),('STATE','ENDSTATE'),
        ('FDB','Choice:'),('A','Logical drive B, C or D:'),('B','Q Back:'),
        ('3','Q Back:'),('E','Value 0-65535'),('100','Q Back:'),
        ('S','D Apply active drive'),('D','Logical drive B, C or D:'),
        ('B','Active binding only'),('Y','Active drive binding updated.'),
        ('S','D Apply active drive'),('D','Logical drive B, C or D:'),
        ('C','Active binding only'),('Y','Active drive binding updated.'),
        ('S','D Apply active drive'),('D','Logical drive B, C or D:'),
        ('D','Active binding only'),('Y','Active drive binding updated.'),
        ('1','Q Back:'),('I','Text (ID <=8'),('CAP101','Q Back:'),('N','Text (ID <=8'),
        ('NATIVE CAPTURE','Q Back:'),('S','D Apply active drive'),
        ('K','1 added, 0 replaced.'),('S','D Apply active drive'),
        ('W','Return uses name above'),('OUT101.FDB','Create (Y/N)?'),
        ('Y','Catalogue saved and verified.'),
        ('O','Export ID'),('CAP101','Export destination'),('ONE101.FDF','Create (Y/N)?'),
        ('Y','exported and verified.'),('O','Export ID'),('CAP101','Export destination'),
        ('ONE101.FDB','Create (Y/N)?'),('Y','exported and verified.'),('Q','A0>'),
        ('STATE','ENDSTATE'),('TYPE POST.TXT','FDB101 UI COMPLETED')]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--target',choices=['z80pack','trs80gp'],required=True)
    p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--simulator',type=Path)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True)
    baseline=a.baseline.resolve();report=json.loads((baseline/'report.json').read_text())
    original=baseline/report['image'];assert hashlib.sha256(original.read_bytes()).hexdigest()==report['sha256']
    shutil.copy2(baseline/'diskdefs',out/'diskdefs')
    raw=out/'staged.raw';raw.write_bytes(extract_raw(original.read_bytes()) if a.target=='trs80gp' else original.read_bytes())
    probe=state_probe(out,clear=True)
    fixtures={'DISK.BAK':b'KEEP PREEXISTING BACKUP\r\n\x1a','STATE.COM':probe,'POST.TXT':b'FDB101 UI COMPLETED\r\n\x1a',
        'FREE.TXT':b'FDB101 UNLOADED READY\r\n\x1a',
        'UNLOAD.SUB':b'CLS\r\nRSX UNLOAD ADM3A\r\nRSX UNLOAD M4SCRN\r\nRSX LIST\r\nTYPE FREE.TXT\r\n\x1a'}
    for name,data in fixtures.items():
        source=out/('fixture-'+name);source.write_bytes(data)
        subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(raw),str(source),'0:'+name],cwd=out,check=True,capture_output=True)
    steps=workflows();(out/'steps.json').write_text(json.dumps(steps,indent=2)+'\n')
    if a.target=='z80pack':
        disks=out/'disks';disks.mkdir();after=disks/'drivea.dsk';shutil.copy2(raw,after)
        trace=session(a.simulator.resolve(),disks,[(k.encode() if k in ('\x03','\x1b') else (k+'\r').encode(), b'A0>_ ' if w=='A0>' else b'Filename required (.FDB/.FDF): \r\n' if w=='Filename required' else w.encode(),60) for k,w in steps]+[(b'BYE /Y\r',b'System halted',30)],out/'transcript.bin')
        states=re.findall(rb'STATE ([0-9A-F]{560}) ENDSTATE',trace)
        text=trace.decode('ascii','replace')
        assert all(w in text for _,w in steps)
    else:
        disk=out/'ui.dmk';disk.write_bytes(make_dmk(raw.read_bytes()))
        cmd=[str(DEFAULT_EMULATOR),'-m4','-batch','-turbo','-ktx','-d0',str(disk),
             '-id','4000','-it','-itime','15000','-iw','Type TYPE README.TXT for more','-id','4000']
        cmd+=key_args('SUBMIT UNLOAD\r')+['-id','600','-it','-iw','FDB101 UNLOADED READY','-iw','A0> ','-id','300','-it']
        diagnostic_indices=[0,1];capture_count=3
        for k,w in steps:
            cmd+=key_args(k if k in ('\x03','\x1b') else k+'\r')
            if k=='FDB':
                cmd+=['-id','600','-it']
                diagnostic_indices.append(capture_count);capture_count+=1
            cmd+=['-iw','A0> ' if w=='A0>' else w]
            if k=='STATE' or k.startswith('TYPE '):
                # ENDSTATE/file text precedes warm-boot completion. Wait for
                # the empty CCP prompt before typing the next command.
                cmd+=['-iw','A0> ']
            # The shipped CCP can display its prompt before command-extension
            # reload/keyboard flush completes. Use the established native
            # qualification settling interval before sending another command.
            settling='3000' if k=='STATE' or k.startswith('TYPE ') or w=='A0>' else '180'
            cmd+=['-id',settling,'-it'];capture_count+=1
        cmd+=key_args('SUBMIT STARTUP\r')+['-iw','Type TYPE README.TXT for more','-iw','A0> ','-id','300','-it']
        cmd+=key_args('RSX LIST\r')+['-iw','TPA available: 50K','-iw','A0> ','-id','300','-it']
        cmd+=key_args('TYPE POST.TXT\r')+['-iw','FDB101 UI COMPLETED','-iw','A0> ','-id','300','-it','-ix']
        (out/'invocation.json').write_text(json.dumps(cmd,indent=2)+'\n')
        run(cmd,cwd=out,check=True,timeout=2400)
        frames=[screen(f) for f in sorted(out.glob('trs80-text*.bin'),key=lambda f:int(f.stem.rsplit('-',1)[1]))]
        assert len(frames)==len(steps)+4+len(diagnostic_indices)
        frames=[f for i,f in enumerate(frames) if i not in diagnostic_indices]
        (out/'diagnostic-frame-indices.json').write_text(json.dumps(diagnostic_indices)+'\n')
        assert 'TPA available: 53K' in frames[0]
        for i,(_,want) in enumerate(steps):assert want in frames[i+1],(i,want,frames[i+1])
        assert 'M4SCRN : BDOS 255' in frames[-2] and 'ADM3A : BDOS 255' in frames[-2]
        assert 'TPA available: 50K' in frames[-2] and 'FDB101 UI COMPLETED' in frames[-1]
        states=[m[1].encode() for i,(command,_) in enumerate(steps) if command=='STATE'
            for m in re.finditer(r'STATE ([0-9A-F]{560}) ENDSTATE',frames[i+1].replace('\n',''))]
        after=out/'after.raw';after.write_bytes(extract_raw(disk.read_bytes()))
    assert len(states)==3,('public snapshots',len(states))
    before,cancel,applied=[bytes.fromhex(s.decode()) for s in states]
    assert before==cancel,'cancelled apply changed a binding'
    expected=bytearray(before)
    for drive in (1,2,3):expected[24+drive*64+6:24+drive*64+8]=(100).to_bytes(2,'little')
    assert applied==expected,'unexpected binding/physical-selector/cold configuration change'
    audit(a.target,original,after,out)
    recovered={}
    for name in ['OUT101.FDB','ONE101.FDB','ONE101.FDF','DISK.BAK']:
        dest=out/name;subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(after),'0:'+name,str(dest)],cwd=out,check=True,capture_output=True);recovered[name]=dest.read_bytes()
    assert recovered['DISK.BAK']==fixtures['DISK.BAK']
    from fdf_v1 import parse,serialize
    from fdfdecomp import decompile
    from build_fdf_catalog import catalogue_payload
    stock=parse(decompile(catalogue_payload()));all_entries=parse(decompile(recovered['OUT101.FDB']))
    assert all_entries[:108]==stock and len(all_entries)==109
    single=parse(decompile(recovered['ONE101.FDB']));assert len(single)==1 and single[0].ident=='CAP101' and single[0].dsm==100
    assert serialize(parse(recovered['ONE101.FDF'].split(b'\x1a')[0].decode()))==recovered['ONE101.FDB']
    (out/'result.json').write_text(json.dumps({'status':'PASS','target':a.target,'steps':len(steps),
        'com_sha256':next(i['sha256'] for i in report['included'] if i['name']=='FDB.COM'),
        'binding_before':before.hex(),'binding_cancel':cancel.hex(),'binding_applied':applied.hex(),
        'scope':'new UI flows, cancellation, actual B-D apply, named109 save, single exports both encodings, all shipped files/reserved tracks preserved; Model4 unload53K/queuedrestore50K/file-read'},indent=2)+'\n')
    print('PASS',a.target,'1.01 interactive usability, bindings, save/export and preservation')


if __name__=='__main__':main()
