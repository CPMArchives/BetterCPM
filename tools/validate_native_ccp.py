#!/usr/bin/env python3
"""Assemble prepared packed inputs with native ZSM4/LINK, then run RLMBUILD."""
import argparse
from pathlib import Path
import shutil
import tempfile
from build_native_trs80 import blank, run
from build_source_disk import build_source, extract_files

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cpmsim', type=Path, required=True)
    p.add_argument('--system-disk', type=Path, required=True)
    p.add_argument('--disk-template', type=Path, required=True)
    p.add_argument('--tools', type=Path, required=True)
    p.add_argument('--build-disk', type=Path, help='validate exported logical build-disk inputs')
    args = p.parse_args()
    exported = extract_files(args.build_disk.read_bytes()) if args.build_disk else None
    folder = ROOT/'build/ccp'
    with tempfile.TemporaryDirectory(prefix='native-packed-ccp-') as tmp:
        work = Path(tmp); disks = work/'disks'; disks.mkdir()
        shutil.copy2(args.system_disk, disks/'drivea.dsk')
        for drive in 'bcd': blank(args.disk_template, disks/f'drive{drive}.dsk')
        for tool in ('ZSM4.COM','LINK.COM'):
            run('cpmcp','-f','ibm-3740',str(disks/'drived.dsk'),str(args.tools/tool),'0:'+tool)
        builder = work/'RLMBUILD.COM'
        builder.write_bytes(exported[(0,'RLMBUILD.COM')] if exported else
                            (ROOT/'build/utilities/RLMBUILD.COM').read_bytes())
        run('cpmcp','-f','ibm-3740',str(disks/'driveb.dsk'),str(builder),'0:RLMBUILD.COM')
        commands = [f'set timeout 60', f'spawn {args.cpmsim.resolve()} -z -d {disks}',
                    'expect_after {timeout {exit 124}}',
                    'expect "A>"', 'send -- "B:\\r"', 'expect "B>"']
        variants = [('CCP','packed','CCPBASE'),('CCPALT','packed-alt','CCPALT'),
                    ('CCPCHK','packed-check','CCPCHK')]
        for stem, packed, output in variants:
            source = work/(stem+'.MAC')
            source.write_bytes(exported[(0,stem+'.MAC')] if exported else
                               build_source((folder/(packed+'.mac')).read_bytes(),stem+'.MAC'))
            run('cpmcp','-f','ibm-3740',str(disks/'drivec.dsk'),str(source),'0:'+source.name)
            commands += [f'send -- "D:ZSM4 B:{stem}=C:{stem}\\r"',
                         'expect -re {Errors: +0}', 'expect "B>"',
                         f'send -- "D:LINK {stem}\\[A\\]\\r"',
                         'expect "CODE SIZE"','expect "B>"',
                         f'send -- "REN {output}.BIN={stem}.COM\\r"','expect "B>"']
        commands += ['send -- "RLMBUILD\\r"','expect "CCP.RLM created and verified."',
                     'expect "B>"','send "\\034"','expect eof']
        result = run('expect','-c','\n'.join(commands),check=False)
        transcript = result.stdout+result.stderr
        (folder/'NATIVE-PACKED-BUILD.LOG').write_text(transcript)
        if result.returncode or 'CCP.RLM created and verified.' not in transcript:
            raise SystemExit('native packed rebuild failed\n'+transcript)
        for stem, packed, output in variants:
            target = work/(output+'.BIN')
            run('cpmcp','-f','ibm-3740',str(disks/'driveb.dsk'),'0:'+target.name,str(target))
            expected = (folder/(packed+'.bin')).read_bytes()
            actual = target.read_bytes()
            if actual[:len(expected)] != expected:
                raise SystemExit('native prepared-input mismatch: '+stem)
            print(f'{stem}: {len(expected)} byte-identical native bytes')
        target = work/'CCP.RLM'
        run('cpmcp','-f','ibm-3740',str(disks/'driveb.dsk'),'0:CCP.RLM',str(target))
        expected = (folder/'ccp.rlm').read_bytes(); actual = target.read_bytes()
        if actual[:len(expected)] != expected or any(actual[len(expected):]):
            raise SystemExit('native RLMBUILD carrier mismatch')
        print(f'CCP.RLM: {len(expected)} byte-identical bytes, zero record padding')


if __name__ == '__main__': main()
