#!/usr/bin/env python3
"""Exercise DDT commands and shared input on disposable CP/M/BetterCP/M images."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,sys,tempfile
from build_ddt import ROOT,BUILD,version_text
# Shared existing PTY harness; imports resolve inside the installed repository.
from test_z80pack_sysgen_install import session


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline',type=Path)
    p.add_argument('--output',type=Path,default=BUILD/'live')
    p.add_argument('--simulator',type=Path,default=Path.home()/'projects/git/z80pack/cpmsim/cpmsim')
    a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    stock=a.baseline is None
    original=(a.simulator.parent/'disks/library/cpm22-62khd.dsk') if stock else a.baseline
    before=hashlib.sha256(original.read_bytes()).hexdigest()
    work=Path(tempfile.mkdtemp(prefix='session-',dir=out));disks=work/'disks';disks.mkdir();image=disks/'drivea.dsk';shutil.copyfile(original,image)
    if stock:fmt='ibm-3740'
    else:
        fmt='bettercpm-default'
        defs=Path.home()/'projects/git/BetterCPM/build/z80pack-daily/diskdefs';shutil.copyfile(defs,work/'diskdefs')
    def run(*args):
        r=subprocess.run([str(x) for x in args],cwd=work,capture_output=True)
        if r.returncode:raise RuntimeError(f'{args}: {r.stderr!r}')
        return r
    # Tiny 8080 fixture performs memory work then returns to the warm-boot frame.
    fixture=work/'TINY.COM';fixture.write_bytes(bytes.fromhex('3e05320003c9'))
    hexfile=work/'TINY.HEX';hexfile.write_bytes(b':030300003E07C9EC\r\n:0000000000\r\n\x1a')
    # Correct checksum derives solely from the controlled fixture record.
    data=bytes([3,3,0,0,0x3e,7,0xc9]);hexfile.write_bytes(b':'+(data+bytes([(-sum(data))&255])).hex().upper().encode()+b'\r\n:0000000000\r\n\x1a')
    for src,name in [(ROOT/'build/utilities/DDT.COM','DDT.COM'),(fixture,'TINY.COM'),(hexfile,'TINY.HEX')]:
        # Baseline disks need not contain DDT; remove an existing copy only on this disposable disk.
        subprocess.run(['cpmrm','-f',fmt,str(image),'0:'+name],cwd=work,capture_output=True)
        run('cpmcp','-f',fmt,image,src,'0:'+name)
    prompt=b'A>' if stock else b'A0>_ '
    commands=[(b'DDT /VER\r',prompt,10),(b'DDT /VER X\r',prompt,10),(b'DDT\r',b'\r\n-',10)]
    commands += [(b'H100,2X\x7f0\r',b'0120 00E0',10),(b'',b'\r\n-',10)]
    commands += [(b'F300,30F,41\r',b'\r\n-',10),(b'D300,30F\r',b'AAAAAAAAAAAAAAAA',10),(b'',b'\r\n-',10),
                 (b'M300,30F,320\r',b'\r\n-',10),(b'D320,32F\r',b'AAAAAAAAAAAAAAAA',10),(b'',b'\r\n-',10)]
    # Interactive subcommands preserve prefixes, dot and empty response semantics.
    commands += [(b'A400\r',b'0400 ',10),(b'MVI A,5\r',b'0402 ',10),(b'RET\r',b'0403 ',10),(b'.\r',b'\r\n-',10),
                 (b'A500\r',b'0500 ',10),(b'\r',b'\r\n-',10),*([] if stock else [(b'A600\rMVI A,1\rRET\r.\r',b'\r\n-',10),(b'L600,602\r',b'  0602  RET',10),(b'',b'\r\n-',10)]),(b'L400,402\r',b'  0402  RET',10),(b'',b'\r\n-',10),
                 (b'S300\r',b'0300 41 ',10),(b'42\r',b'0301 41 ',10),(b'.\r',b'\r\n-',10),
                 (b'XA\r',b'A=00 ',10),(b'7\r',b'\r\n-',10),(b'X\r',b'A=07',10),(b'',b'\r\n-',10),
                 (b'S300\r',b'0300 42 ',10),(b'99\x1b',b'\r\n-',10),(b'D300,300\r',b'0300 42',10),(b'',b'\r\n-',10),
                 (b'bad\x15H100,20\r',b'0120 00E0',10),(b'',b'\r\n-',10),
                 (b'ITINY.HEX\r',b'\r\n-',10),(b'R\r',b'\r\n-',10),(b'L300,302\r',b'  0302  RET',10),(b'',b'\r\n-',10),
                 (b'Z\r',b'\r\n?',10),(b'',b'\r\n-',10),(b'G0\r',prompt,10),
                 (b'DDT TINY.COM\r',b'\r\n-',10),(b'L100,105\r',b'  0105  RET',10),(b'',b'\r\n-',10),
                 (b'G100,102\r',b'*0102',10),(b'',b'\r\n-',10),(b'D102,104\r',b'0102 32 00 03',10),(b'',b'\r\n-',10),
                 (b'T1\r',b'\r\n-',10),(b'XP\r',b'P=0105 ',10),(b'100\r',b'\r\n-',10),(b'U1\r',b'\r\n-',10),(b'G0\r',prompt,10),(b'DDT\r',b'\r\n-',10),(b'\x03',prompt,10)]
    raw=session(a.simulator,disks,commands,transcript_path=work/'transcript.bin',initial_prompt=prompt)
    assert raw.count(version_text().encode())>=4
    assert b'Invalid /VER usage.' not in raw
    assert hashlib.sha256(original.read_bytes()).hexdigest()==before
    readback=work/'TINY-after.COM';run('cpmcp','-f',fmt,image,'0:TINY.COM',readback)
    assert readback.read_bytes()[:6]==fixture.read_bytes()
    run('fsck.cpm','-f',fmt,'-n',image)
    report={'status':'PASS','platform':'CP/M 2.2' if stock else 'BetterCP/M','baseline_sha256':before,'program_sha256':hashlib.sha256((ROOT/'build/utilities/DDT.COM').read_bytes()).hexdigest(),'transcript_sha256':hashlib.sha256(raw).hexdigest(),'interactions':len(commands),'scope':'Identity, edited arithmetic, F/D/M, A/L, S/X, ESC operand cancellation, COM/HEX input, G breakpoint/restoration, T step and G0/Ctrl-C warm boot; immutable disk fixtures.'}
    (work/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(work)


if __name__=='__main__':main()
