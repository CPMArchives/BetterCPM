#!/usr/bin/env python3
"""Check explicit media selection with a dummy launcher and no real emulator."""
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix='bcpm-usecurrent-') as temp:
        work=Path(temp);repo=work/'private repo';daily=repo/'build/z80pack-daily'
        disks=daily/'disks';disks.mkdir(parents=True)
        source=(ROOT/'tools/bcpm').read_text()
        assignment='repo="$HOME/projects/git/BetterCPM"'
        assert source.count(assignment)==1
        script=work/'bcpm';script.write_text(source.replace(assignment,'repo='+shlex.quote(str(repo)),1))
        launch_log=work/'launch.log'
        launcher=daily/'launch-z80pack.command'
        launcher.write_text('#!/bin/sh\nprintf "launched\\n" >> '+shlex.quote(str(launch_log))+'\n')
        launcher.chmod(0o755)
        def run(*args):
            return subprocess.run([shutil.which('bash'),str(script),*map(str,args)],
                                  cwd=work,capture_output=True)
        def count():return len(launch_log.read_text().splitlines()) if launch_log.exists() else 0
        def snapshot():
            return {p.name:(os.readlink(p) if p.is_symlink() else None,
                            p.lstat().st_mtime_ns,p.read_bytes()) for p in disks.iterdir() if p.is_file()}
        selected={}
        for letter in 'abcd':
            image=work/('selected '+letter+' image.dsk');image.write_bytes(('candidate-'+letter).encode());selected[letter]=image
            for token in (letter,letter.upper(),letter+':',letter.upper()+':'):
                result=run('mount',token,image)
                assert result.returncode==0,result.stderr
                assert (disks/('drive'+letter+'.dsk')).resolve()==image.resolve()
        before=snapshot()
        assert run('z','/usecurrent').returncode==0 and count()==1
        assert snapshot()==before
        # No development System/Utilities images exist: /usecurrent bypasses them.
        for args in [('z','/bogus'),('z','/usecurrent','extra'),('mount','e',selected['a']),
                     ('mount','a',work/'missing.dsk')]:
            assert run(*args).returncode!=0 and count()==1
            assert snapshot()==before
        for args in [('-h',),('z','-h'),('mount','-h')]:
            result=run(*args);assert result.returncode==0 and b'/usecurrent' in result.stdout
            assert snapshot()==before and count()==1
        a=disks/'drivea.dsk';a.unlink()
        assert run('z','/usecurrent').returncode!=0 and count()==1
        assert run('mount','a:',selected['a']).returncode==0
        held=work/'held.dsk';selected['b'].rename(held)
        assert run('z','/usecurrent').returncode!=0 and count()==1
        held.rename(selected['b'])
        # Existing regular image files can be used, but mount never deletes one.
        for letter in 'abcd':
            path=disks/('drive'+letter+'.dsk');path.unlink();path.write_bytes(b'personal image')
            assert run('mount',letter,selected[letter]).returncode!=0
            assert path.read_bytes()==b'personal image'
            before=snapshot();assert run('z','/usecurrent').returncode==0
            assert snapshot()==before
            path.unlink();assert run('mount',letter,selected[letter]).returncode==0
        # Default behavior still mounts built A/B/C, retaining D exactly.
        system=repo/'build/z80pack/disks/library/BetterCPM-Distribution-z80pack-332K.dsk'
        system.parent.mkdir(parents=True);system.write_bytes(b'built system')
        utils=repo/'build/utilities-disks';utils.mkdir()
        primary=utils/'BetterCPM-Utilities-z80pack-332K.dsk';primary.write_bytes(b'built primary')
        companion=utils/'BetterCPM-NOAH-z80pack-332K.dsk';companion.write_bytes(b'built companion')
        d_before=snapshot()['drived.dsk'];assert run('z').returncode==0
        assert (disks/'drivea.dsk').resolve()==system.resolve()
        assert (disks/'driveb.dsk').resolve()==primary.resolve()
        assert (disks/'drivec.dsk').resolve()==companion.resolve()
        assert snapshot()['drived.dsk']==d_before
        for letter,image in selected.items():assert image.read_bytes()==('candidate-'+letter).encode()
        print('PASS: 16 drive forms, unchanged /usecurrent mounts without built media, default A/B/C mounts, D retention, help, missing media/argument errors and regular-file preservation; dummy launches only')


if __name__=='__main__':main()
