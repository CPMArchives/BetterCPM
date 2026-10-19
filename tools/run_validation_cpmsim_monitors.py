#!/usr/bin/env python3
"""Regress shipped cpmsim monitor/backend pairs without replacing release files."""
import argparse,json,shutil,subprocess,tempfile
from pathlib import Path
from run_validation_returning import sha
from test_z80pack_sysgen_install import session


def audit(baseline,report,work,image):
    results=[]
    for item in report['included']:
        outputs=[]
        for label,disk in [('before',baseline/report['image']),('after',image)]:
            path=work/(label+'-'+item['name'])
            subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(disk),f"{item.get('user',0)}:{item['name']}",str(path)],cwd=work,check=True,capture_output=True)
            outputs.append(path)
        assert sha(outputs[0])==item['sha256'] and outputs[0].read_bytes()==outputs[1].read_bytes(),item['name']
        results.append(item['name'])
    check=subprocess.run(['fsck.cpm','-T','raw','-f','bettercpm-default','-n',str(image)],cwd=work,capture_output=True,text=True)
    (work/'filesystem.txt').write_text(check.stdout+check.stderr);assert check.returncode==0
    assert sha(baseline/report['image'])==report['sha256']
    return results


def main():
    import pyte
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('baseline','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--simulator',type=Path,default=Path.home()/'projects/git/z80pack/cpmsim/cpmsim')
    a=p.parse_args();report=json.loads((a.baseline/'report.json').read_text())
    assert report['target']=='z80pack' and sha(a.baseline/report['image'])==report['sha256']
    a.output.mkdir(parents=True,exist_ok=True)
    for name,program in [('ADM3A','ADMTST'),('VT52','VT52TST'),('ANSI','ANSITST')]:
        work=Path(tempfile.mkdtemp(prefix=name.lower()+'-',dir=a.output.resolve()));disks=work/'disks';disks.mkdir()
        image=disks/'drivea.dsk';shutil.copy2(a.baseline/report['image'],image);shutil.copy2(a.baseline/'diskdefs',work/'diskdefs')
        shutil.copy2(__file__,work/'executed-runner.py');prompt=b'A0>'
        steps=[(b'RSX LOAD ANSISCRN\r',prompt,30),(f'RSX LOAD {name}\r'.encode(),prompt,30),
               (b'RSX LIST\r',prompt,30),(program.encode()+b'\r',b'Press a key to continue.',30)]
        pauses=3 if name=='ADM3A' else 2 if name=='VT52' else 1
        steps += [(b' ',b'Press a key to continue.',30)]*pauses
        if name=='ADM3A':
            steps += [(b' ',b'No ENTER is required.',30),(b'A:[]',b'ADMTST keyboard checks passed.',30)]
        else:steps += [(b' ',name.encode()+b' monitor exercise complete.',30)]
        steps += [(b'',prompt,30),(f'RSX UNLOAD {name}\r'.encode(),prompt,30),
                  (b'RSX UNLOAD ANSISCRN\r',prompt,30),(b'RSX LIST\r',b'TPA available: 53K',30),
                  (b'',prompt,30),(b'BYE\r',b'System halted',30)]
        trace=session(a.simulator,disks,steps,work/'transcript.bin')
        assert name.encode()+b' : BDOS 255' in trace and b'ANSISCRN : BDOS 255' in trace
        assert b'No RSXs loaded' in trace and b'TPA available: 53K' in trace
        assert b'No MCON provider loaded' not in trace
        prefix=trace.split(b'Press a key to continue.',1)[0]
        screen=pyte.Screen(80,24);stream=pyte.Stream(screen);stream.feed(prefix.decode('ascii',errors='replace'))
        assert screen.display[5][10:34]=='Marker: row 5, column 10'
        if name=='ANSI':
            assert screen.display[7].startswith('Normal Reverse Normal')
            assert all(screen.buffer[7][c].reverse for c in range(7,14)) and not screen.buffer[7][0].reverse
            assert screen.display[9].rstrip()=='Erase KEEP'
            assert b'Parser reset: readable text' in trace
        elif name=='VT52':
            assert b'identification reply ESC / K passed.' in trace and b'identification reply failed' not in trace
            assert b'\x1b[0K' in trace and b'\x1b[0J' in trace and b'\x1bY' not in trace
        else:
            assert b'Cursor OFF/ON query passed.' in trace and b'Keyboard mismatch.' not in trace
            assert b'\x1b[?25l' in trace and b'\x1b[?25h' in trace and b'\x1b[7m' in trace
        (work/'first-page.txt').write_text('\n'.join(screen.display)+'\n')
        shipped=audit(a.baseline,report,work,image)
        (work/'result.json').write_text(json.dumps({'status':'PASS','monitor':name,'baseline_sha256':report['sha256'],
            'simulator_sha256':sha(a.simulator),'runner_sha256':sha(Path(__file__)),'pyte_module':pyte.__file__,
            'unchanged_shipped_files':shipped,'scope':'selected shipped RAM-profile cpmsim personality/ANSI-host backend controls, rendered first page, utility completion and unload/53K; no physical-terminal or ROM claim'},indent=2)+'\n')
        print(name,'PASS',work,flush=True)


if __name__=='__main__':main()
