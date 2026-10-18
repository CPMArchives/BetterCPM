#!/usr/bin/env python3
"""Run controlled ED/CONFIG recovery fixtures against manifest-matched binaries."""
import argparse,json,shutil,subprocess,sys
from pathlib import Path
from run_validation_returning import sha
ROOT=Path(__file__).resolve().parents[1]
TESTS=('test_ed_files','test_ed_recovery','test_ed_stream_recovery','test_ed_publish','test_ed_finish','test_ed_transfer',
       'test_config_startup_save','test_config_iobyte','test_config_saved_inspection')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('build-root','baseline','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();build=a.build_root.resolve();w=a.output.resolve();w.mkdir(parents=True,exist_ok=False)
    manifest=json.loads((a.baseline/'report.json').read_text());matched={}
    for name in ('ED.COM','CONFIG.COM'):
        actual=sha(build/'build/utilities'/name)
        assert actual==next(x['sha256'] for x in manifest['included'] if x['name']==name),name
        matched[name]=actual
    assert (build/'build/ed-development/EDDEV.COM').read_bytes()==(build/'build/utilities/ED.COM').read_bytes()
    shutil.copy2(__file__,w/'executed-runner.py');results={}
    for name in TESTS:
        shutil.copy2(ROOT/'tools'/(name+'.py'),w/(name+'.py'))
        code=("import sys;sys.path.insert(0,"+repr(str(ROOT/'tools'))+");from pathlib import Path;"
              "import test_ed_buffer;test_ed_buffer.OUT=Path("+repr(str(build/'build/ed-development'))+");"
              "import "+name+" as t;t.ROOT=Path("+repr(str(build))+");t.main()")
        r=subprocess.run([sys.executable,'-c',code],cwd=ROOT,capture_output=True,text=True,timeout=180)
        (w/(name+'.txt')).write_text(r.stdout+r.stderr)
        results[name]={'exit_code':r.returncode,'test_sha256':sha(w/(name+'.py'))}
        print(name,r.returncode,r.stdout.strip(),flush=True)
    assert sha(a.baseline/manifest['image'])==manifest['sha256']
    helpers={}
    for name in ('test_ed_buffer.py','test_bios.py','test_utility_versions.py'):
        shutil.copy2(ROOT/'tools'/name,w/name);helpers[name]=sha(w/name)
    passed=all(r['exit_code']==0 for r in results.values())
    (w/'result.json').write_text(json.dumps({'status':'PASS' if passed else 'FAIL','tests':results,'matched_binaries':matched,
        'baseline_sha256':manifest['sha256'],'runner_sha256':sha(Path(__file__)),'helper_hashes':helpers,
        'scope':'controlled assembled-code BDOS/BIOS fixtures; not native emulator or physical-media fault injection'},indent=2)+'\n')
    assert passed,'see retained failure logs'


if __name__=='__main__':main()
