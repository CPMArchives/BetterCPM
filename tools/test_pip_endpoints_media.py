#!/usr/bin/env python3
"""Compare actual host LPT/PTP/PTR routes with DRI and preserve live IOBYTE."""
from pathlib import Path
import argparse,shutil,subprocess,tempfile,threading,os
from build_ccp import assemble
from test_z80pack_sysgen_install import session
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('--image-dir',type=Path,required=True)
    p.add_argument('--simulator',type=Path,default=Path.home()/'projects/git/z80pack/cpmsim/cpmsim');a=p.parse_args()
    report=ROOT/'build/test-results/pip-endpoints';report.mkdir(parents=True,exist_ok=True)
    results=[]
    for name,binary in [('OUR',ROOT/'build/utilities/PIP.COM'),('DRI',ROOT/'third_party/dri-pip/PIP-1.5-reference.COM')]:
        with tempfile.TemporaryDirectory(prefix='pip-endpoints-',dir='/private/tmp') as t:
            w=Path(t);shutil.copytree(a.image_dir/'disks',w/'disks');shutil.copy2(a.image_dir/'diskdefs',w/'diskdefs')
            disk=w/'disks/drivea.dsk'
            def put(path,filename):
                subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(disk),str(path),'0:'+filename],cwd=w,check=True)
            put(binary,'PIO.COM')
            src=w/'SRC.TXT';src.write_bytes(b'alpha\r\nbeta\x1a');put(src,'SRC.TXT')
            (w/'auxiliaryin.txt').write_bytes(b'INPUT\nEND\x1a')
            setup='''        ASEG
        ORG 100H
        LD E,055H
        LD C,8
        CALL 5
        JP 0
'''
            code=assemble(Path.home()/'bin/z80asm',setup,w/'IOS.COM',w/'ios.lst',256);put(w/'IOS.COM','IOS.COM')
            check='''        ASEG
        ORG 100H
        LD C,7
        CALL 5
        CP 055H
        LD DE,GOOD
        JR Z,SHOW
        LD DE,BAD
SHOW:   LD C,9
        CALL 5
        JP 0
GOOD: DB 'IOBYTE PRESERVED',13,10,'$'
BAD: DB 'IOBYTE LEAKED',13,10,'$'
'''
            assemble(Path.home()/'bin/z80asm',check,w/'IOC.COM',w/'ioc.lst',256);put(w/'IOC.COM','IOC.COM')
            commands=[(b'IOS\r',b'A0>_ ',30)]
            for command in [b'PIO PRN:=SRC.TXT\r',b'PIO PTP:=SRC.TXT\r',b'PIO B:READ.TXT=PTR:\r',b'PIO CRT:=SRC.TXT\r']:
                commands += [(command,b'A0>_ ',30),(b'IOC\r',b'A0>_ ',30)]
            commands += [(b'BYE\r',b'System halted',30)]
            # This cpmsim build uses named pipes, not auxiliaryin.txt.
            # Queue a complete bounded stream after the emulator opens its reader.
            def feed():
                fd=os.open('/tmp/.z80pack/cpmsim.auxin',os.O_WRONLY)
                try:os.write(fd,b'INPUT\r\nEND\x1a')
                finally:os.close(fd)
            writer=threading.Thread(target=feed,daemon=True);writer.start()
            transcript=session(a.simulator,w/'disks',commands,report/(name+'.txt'))
            writer.join(timeout=5)
            assert not writer.is_alive(),'reader feeder did not complete'
            assert transcript.count(b'IOBYTE PRESERVED')==4 and b'IOBYTE LEAKED' not in transcript,transcript[-1000:]
            assert (w/'disks/driveb.dsk').exists(),str(list((w/'disks').iterdir()))
            dest=w/'read.txt';subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(w/'disks/driveb.dsk'),'0:READ.TXT',str(dest)],cwd=w,check=True)
            result=((w/'printer.txt').read_bytes(),(w/'auxiliaryout.txt').read_bytes(),dest.read_bytes())
            assert result[0]==b'\x0c     1: alpha\n     2: beta' and result[1]==b'alpha\nbeta',result[:2]
            (report/(name+'-reader.bin')).write_bytes(result[2])
            results.append(result)
    assert results[0]==results[1], [(r[0],r[1],r[2][:40]) for r in results]
    assert results[0][2].startswith(b'INPUT\r\nEND\x1a')
    print('PASS: physical PRN/PTP/PTR and CRT host endpoints match DRI; IOBYTE preserved')
if __name__=='__main__':main()
